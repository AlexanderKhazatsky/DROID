import argparse
from r2d2.user_interface.eval_gui import EvalGUI
from r2d2.evaluation.rt1_wrapper import RT1Policy

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint_path", type=str, required=True)
    args = parser.parse_args()

    policy = RT1Policy(args.checkpoint_path, camera_obs_keys=["16291792_left", "16291792_right"])
    EvalGUI(policy=policy)

if __name__ == "__main__":
    # main()
    import multiprocessing
    process_eval = multiprocessing.Process(target=main)
    process_eval.start()
    process_eval.join()