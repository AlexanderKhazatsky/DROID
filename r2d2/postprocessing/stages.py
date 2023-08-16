"""
stages.py

Encapsulates logic for the various postprocessing stages:
    - Stage 1 :: "Indexing"  -->  Quickly iterate through all data, identifying formatting errors & naively counting
                                  total number of demonstrations to process/convert/upload.

                                  Note :: Raises hard exceptions on any unexpected directory/file formatting!

    - Stage 2 :: "Processing" --> Walk through data, extract & validate metadata (writing a JSON record for each unique
                                  demonstration). Additionally, runs conversion from SVO --> MP4.

                                  Note :: Logs corrupt HDF5/SVO files & raises warning at end of stage.

    - Stage 3 :: "Uploading" -->  Iterates through individual processed demonstration directories, and uploads them
                                  sequentially to the AWS S3 Bucket (via `boto`).

The outputs/failures of each stage are logged to a special cache data structure that prevents redundant work where
possible. Note that to emphasize readability, some of the following code is intentionally redundant.
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Tuple

from tqdm import tqdm

from r2d2.postprocessing.parse import parse_datetime, parse_timestamp, parse_trajectory, parse_user
from r2d2.postprocessing.util.svo2mp4 import convert_mp4s
from r2d2.postprocessing.util.validate import validate_day_dir, validate_metadata_record, validate_svo_existence


# === Stage 1 :: Indexing ===
def run_indexing(
    data_dir: Path,
    lab: str,
    start_datetime: datetime,
    aliases: Dict[str, Tuple[str, str]],
    members: Dict[str, Dict[str, str]],
    indexed_uuids: Dict[str, Dict[str, str]],
    errored_paths: Dict[str, Dict[str, str]],
) -> Tuple[Dict[str, Dict[str, str]], Dict[str, Dict[str, str]]]:
    """Index data by iterating through each "success/ | failure/" --> <DAY>/ --> <TIMESTAMP>/ (specified trajectory)."""
    progress = tqdm(desc="[*] Stage 1 =>> Indexing")
    for outcome_dir, outcome in [(p, p.name) for p in [data_dir / "success", data_dir / "failure"]]:
        if outcome == "failure" and not outcome_dir.exists():
            # Note: Some labs don't have failure trajectories...
            continue

        day_dirs = sorted([p for p in outcome_dir.iterdir() if p.is_dir() and validate_day_dir(p)])
        for day_dir, day in [(p, p.name) for p in day_dirs]:
            if parse_datetime(day) < start_datetime:
                continue

            for trajectory_dir, _trajectory in [(p, p.name) for p in day_dir.iterdir() if p.is_dir()]:
                # Extract Timestamp (from `trajectory_dir`) and User, User ID (from `trajectory.h5`)
                timestamp = parse_timestamp(trajectory_dir)
                user, user_id = parse_user(trajectory_dir, aliases, members)
                if user is None or user_id is None:
                    errored_paths[outcome][str(trajectory_dir.relative_to(data_dir))] = "Missing/Invalid HDF5"
                    progress.update()
                    continue

                # Create Trajectory UUID --> <LAB>+<USER_ID>+YYYY-MM-DD-{24 Hour}h-{Min}m-{Sec}s
                uuid = f"{lab}+{user_id}+{timestamp}"

                # Verify SVO Files
                if not validate_svo_existence(trajectory_dir):
                    errored_paths[outcome][str(trajectory_dir.relative_to(data_dir))] = "Missing SVO Files"
                    progress.update()
                    continue

                # Otherwise -- we're good for indexing!
                indexed_uuids[outcome][uuid] = str(trajectory_dir.relative_to(data_dir))
                errored_paths[outcome].pop(str(trajectory_dir.relative_to(data_dir)), None)
                progress.update()

    return indexed_uuids, errored_paths


# === Stage 2 :: Processing ===
def run_processing(
    data_dir: Path,
    lab: str,
    aliases: Dict[str, Tuple[str, str]],
    members: Dict[str, Dict[str, str]],
    indexed_uuids: Dict[str, Dict[str, str]],
    processed_uuids: Dict[str, Dict[str, str]],
    errored_paths: Dict[str, Dict[str, str]],
) -> Tuple[Dict[str, Dict[str, str]], Dict[str, Dict[str, str]]]:
    """Iterate through each trajectory in `indexed_uuids` and 1) extract JSON metadata and 2) convert SVO -> MP4."""
    for outcome in indexed_uuids:
        for uuid, rel_trajectory_dir in tqdm(
            indexed_uuids[outcome].items(), desc=f"[*] Stage 2 =>> `{outcome}/` Processing"
        ):
            if uuid in processed_uuids[outcome]:
                continue

            trajectory_dir = data_dir / rel_trajectory_dir
            timestamp = parse_timestamp(trajectory_dir)
            user, user_id = parse_user(trajectory_dir, aliases, members)

            # Run Metadata Extraction --> JSON-serializable Data Record + Validation
            valid_parse, metadata_record = parse_trajectory(
                data_dir, trajectory_dir, uuid, lab, user, user_id, timestamp
            )
            if not valid_parse:
                errored_paths[outcome][rel_trajectory_dir] = "JSON Metadata Parse Error"

            # Convert SVOs --> MP4s
            valid_convert, vid_paths = convert_mp4s(
                data_dir,
                trajectory_dir,
                metadata_record["wrist_cam_serial"],
                metadata_record["ext1_cam_serial"],
                metadata_record["ext2_cam_serial"],
                metadata_record["ext1_cam_extrinsics"],
                metadata_record["ext2_cam_extrinsics"],
            )
            if not valid_convert:
                errored_paths[outcome][rel_trajectory_dir] = "Corrupted SVO / Failed Conversion"
                continue

            # Finalize Metadata Record
            for key, vid_path in vid_paths.items():
                metadata_record[key] = vid_path

            # Validate
            if not validate_metadata_record(metadata_record):
                errored_paths[outcome][rel_trajectory_dir] = "Incomplete Metadata Record!"
                continue

            # Write JSON
            with open(trajectory_dir / "metadata.json", "w") as f:
                json.dump(metadata_record, f)

            # Otherwise --> we're good for processing!
            processed_uuids[outcome][uuid] = rel_trajectory_dir
            errored_paths[outcome].pop(rel_trajectory_dir, None)

    return processed_uuids, errored_paths
