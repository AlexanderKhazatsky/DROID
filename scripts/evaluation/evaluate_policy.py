from r2d2.evaluation.eval_launcher_robomimic import eval_launcher, get_goal_im
import matplotlib.pyplot as plt
import os
import argparse
import cv2

# CKPT_PATH = "/home/ashwinbalakrishna/Desktop/data/expdata_1101_fulldata/r2d2/im/diffusion_policy/11-01-None/ds_full_cams_3cams_goal_mode_None_truncated_geom_factor_0.3_ldkeys_proprio-cam_visenc_DeFiNeVisualCore_fuser_None/20231101215633/models/model_epoch_1000.pth"
# CKPT_PATH = "/home/ashwinbalakrishna/Desktop/data/expdata_1101_fulldata/r2d2/im/diffusion_policy/11-01-None/ds_full_cams_3cams_goal_mode_geom_truncated_geom_factor_0.3_ldkeys_proprio-cam_visenc_DeFiNeVisualCore_fuser_None/20231101215635/models/model_epoch_1000.pth"
# CKPT_PATH = "/home/ashwinbalakrishna/Desktop/data/expdata_1101_fulldata/r2d2/im/diffusion_policy/11-01-None/ds_full_cams_3cams_goal_mode_None_truncated_geom_factor_0.3_ldkeys_proprio-cam_visenc_DeFiNeVisualCore_fuser_None/20231101215633/models/model_epoch_1000.pth"
# CKPT_PATH = "/home/ashwinbalakrishna/Desktop/data/expdata_1101_fulldata/ds_full_cams_3cams_goal_mode_None_truncated_geom_factor_0.3_ldkeys_proprio-cam_backbone_ResNet50Conv_visdim_512/20231101215939/models/model_epoch_650.pth"
# CKPT_PATH = "/home/ashwinbalakrishna/Desktop/data/expdata_1101_fulldata/ds_full_cams_3cams_goal_mode_geom_truncated_geom_factor_0.3_ldkeys_proprio-cam_backbone_ResNet50Conv_visdim_512/20231101215953/models/model_epoch_400.pth"
# CKPT_PATH = "/home/ashwinbalakrishna/Desktop/data/expdata_1127/r2d2/im/diffusion_policy/11-24-None/ds_narrow_cams_wrist_goal_mode_geom_truncated_geom_factor_0.3_ldkeys_proprio-cam_backbone_ResNet50Conv_visdim_512/20231124222735/models/model_epoch_650.pth"

# Goal conditioned narrow
# CKPT_PATH = "/home/ashwinbalakrishna/Desktop/data/expdata_1127/r2d2/im/diffusion_policy/11-24-None/ds_narrow_cams_wrist_goal_mode_geom_truncated_geom_factor_0.3_ldkeys_proprio-cam_backbone_ResNet50Conv_visdim_512/20231124222735/models/model_epoch_650.pth"
# CKPT_PATH = "/home/ashwinbalakrishna/Desktop/data/expdata_1127/r2d2/im/diffusion_policy/11-24-None/ds_eval_cams_wrist_goal_mode_geom_truncated_geom_factor_0.3_ldkeys_proprio-cam_visenc_DeFiNeVisualCore_fuser_None/20231124200552/models/model_epoch_550.pth"
# CKPT_PATH = "/home/ashwinbalakrishna/Desktop/data/expdata_1127/r2d2/im/diffusion_policy/11-24-None/ds_narrow_cams_3cams_goal_mode_geom_truncated_geom_factor_0.3_ldkeys_proprio-cam_backbone_ResNet50Conv_visdim_512/20231124222748/models/model_epoch_250.pth"
# CKPT_PATH = "/home/ashwinbalakrishna/Desktop/data/expdata_1127/r2d2/im/diffusion_policy/11-24-None/ds_eval_cams_3cams_goal_mode_geom_truncated_geom_factor_0.3_ldkeys_proprio-cam_visenc_DeFiNeVisualCore_fuser_None/20231124200627/models/model_epoch_200.pth"


# Goal conditioned easy narrow
# CKPT_PATH = "/home/ashwinbalakrishna/Desktop/data/expdata_1127/r2d2/im/act/11-29-None/ds_eval_cams_3cams_goal_mode_geom_truncated_geom_factor_0.3_ldkeys_proprio-cam_backbone_ResNet50Conv_visdim_512/20231129070624/models/model_epoch_50.pth" # ACT 3 cam
# CKPT_PATH = "/home/ashwinbalakrishna/Desktop/data/expdata_1127/r2d2/im/act/11-29-None/ds_eval_cams_wrist_goal_mode_geom_truncated_geom_factor_0.3_ldkeys_proprio-cam_backbone_ResNet50Conv_visdim_512/20231129070528/models/model_epoch_50.pth" # ACT wrist
# CKPT_PATH = "/home/ashwinbalakrishna/Desktop/data/expdata_1127/r2d2/im/diffusion_policy/11-29-None/ds_eval_cams_wrist_goal_mode_geom_truncated_geom_factor_0.3_ldkeys_proprio-cam_visenc_DeFiNeVisualCore_fuser_None/20231129062342/models/model_epoch_300.pth" # Diffusion wrist define encoding
# CKPT_PATH = "/home/ashwinbalakrishna/Desktop/data/expdata_1127/r2d2/im/diffusion_policy/11-29-None/ds_eval_cams_3cams_goal_mode_geom_truncated_geom_factor_0.3_ldkeys_proprio-cam_visenc_DeFiNeVisualCore_fuser_None/20231129062347/models/model_epoch_300.pth" # Diffusion 3 cam define encoding

# CKPT_PATH = "/home/ashwinbalakrishna/Desktop/data/r2d2-multitask/r2d2/im/diffusion_policy/12-26-None/ds_eval_multi_cams_3cams_goal_mode_None_truncated_geom_factor_0.3_ldkeys_proprio-cam_visenc_DeFiNeVisualCore_fuser_None/20231226191919/models/model_epoch_100.pth"
# CKPT_PATH = "/home/ashwinbalakrishna/Desktop/data/r2d2-multitask/r2d2/im/diffusion_policy/12-26-None/ds_eval_multi_cams_3cams_goal_mode_geom_truncated_geom_factor_0.3_ldkeys_proprio-cam_visenc_DeFiNeVisualCore_fuser_None/20231226191925/models/model_epoch_100.pth"

# Large sweep evals

# Goal conditioned

# 3 Cam, food in bowl: Worked 2x times with apple
# CKPT_PATH = "/home/ashwinbalakrishna/Desktop/data/r2d2-multitask/r2d2/im/diffusion_policy/12-29-None/cams_3cams_goal_mode_geom_truncated_geom_factor_0.3_ldkeys_proprio-cam_visenc_DeFiNeVisualCore_fuser_None_ds_eval_foodinbowl/20231229054907/models/model_epoch_400.pth"

# Wrist, food in bowl: does nonsense
# CKPT_PATH = "/home/ashwinbalakrishna/Desktop/data/r2d2-multitask/r2d2/im/diffusion_policy/12-29-None/cams_wrist_goal_mode_geom_truncated_geom_factor_0.3_ldkeys_proprio-cam_visenc_DeFiNeVisualCore_fuser_None_ds_eval_foodinbowl/20231229060939/models/model_epoch_1100.pth"


# Tried both ckpt 550 and 1100, both are quite bad
# CKPT_PATH = "/home/ashwinbalakrishna/Desktop/data/r2d2-multitask/r2d2/im/diffusion_policy/12-29-None/cams_wrist_goal_mode_None_truncated_geom_factor_0.3_ldkeys_proprio-cam-lang_visenc_DeFiNeVisualCore_fuser_None_ds_eval_foodinbowl/20231229053941/models/model_epoch_1100.pth"

# 3 cam, food in bowl: behavior is pretty reasonable, but does not actually successfully grasp apple
# CKPT_PATH = "/home/ashwinbalakrishna/Desktop/data/r2d2-multitask/r2d2/im/diffusion_policy/12-30-None/cams_3cams_goal_mode_None_truncated_geom_factor_0.3_ldkeys_proprio-cam-lang_visenc_DeFiNeVisualCore_fuser_None_ds_eval_foodinbowl/20231230065508/models/model_epoch_400.pth"





############################ EXPERIMENTS 1/9 ########################

# 3 Cam, Goal Conditioned, Food in Bowl, Narrow

# Apple: 
    # Trial 1: didn't grasp apple but close, didn't re-open gripper to retry
    # Trial 2: worked perfectly
    # Trial 3: didn't grasp apple but close, didn't re-open gripper to retry
# CKPT_PATH = "/home/ashwinbalakrishna/Desktop/data/r2d2-multitask/r2d2/im/diffusion_policy/12-29-None/cams_3cams_goal_mode_geom_truncated_geom_factor_0.3_ldkeys_proprio-cam_visenc_DeFiNeVisualCore_fuser_None_ds_eval_foodinbowl/20231229054907/models/model_epoch_400.pth"

# 3 Cam, Goal Conditioned, Food in Bowl, Co-Train

# Apple:
    # Trial 1: randomly jumped up and down in free space nowhere near the apple
    # Trial 2: same as trial 1
    # Trial 3: 
# CKPT_PATH = "/home/ashwinbalakrishna/Desktop/data/r2d2-multitask/r2d2/im/diffusion_policy/12-29-None/cams_3cams_goal_mode_geom_truncated_geom_factor_0.3_ldkeys_proprio-cam_visenc_DeFiNeVisualCore_fuser_None_ds_balanced_broad_eval_foodinbowl/20231229054914/models/model_epoch_400.pth"

# Wrist, Goal Conditioned, Food in Bowl, Co-Train

# Apple:
    # Trial 1: random nonsense
    # Trial 2: picked up the bowl lol
    # Trial 3: 

# CKPT_PATH = "/home/ashwinbalakrishna/Desktop/data/r2d2-multitask/r2d2/im/diffusion_policy/12-29-None/cams_wrist_goal_mode_geom_truncated_geom_factor_0.3_ldkeys_proprio-cam_visenc_DeFiNeVisualCore_fuser_None_ds_balanced_broad_eval_foodinbowl/20231229060959/models/model_epoch_1100.pth"

# 3 Cam, FiLM, Food in Bowl, Narrow

# Doritos:
    # Trial 1: worked kinda eventually
# CKPT_PATH = "/home/ashwinbalakrishna/Desktop/data/r2d2-multitask/r2d2/im/diffusion_policy/12-29-None/ds_eval_foodinbowl_cams_3cams_goal_mode_None_truncated_geom_factor_0.3_ldkeys_proprio-cam-lang_visenc_DeFiNeVisualCore_fuser_None/20231229054729/models/model_epoch_200.pth"

# 3 Cam, Naive Language, Food in Bowl, Narrow

# Orange:
    # Trial 1: failed
    # Trial 2: failed

# CKPT_PATH = "/home/ashwinbalakrishna/Desktop/data/r2d2-multitask/r2d2/im/diffusion_policy/12-30-None/cams_3cams_goal_mode_None_truncated_geom_factor_0.3_ldkeys_proprio-cam-lang_visenc_DeFiNeVisualCore_fuser_None_ds_eval_foodinbowl/20231230065508/models/model_epoch_1100.pth"
# CKPT_PATH = "/home/ashwinbalakrishna/Desktop/data/r2d2-multitask/r2d2/im/diffusion_policy/12-30-None/cams_3cams_goal_mode_None_truncated_geom_factor_0.3_ldkeys_proprio-cam-lang_visenc_DeFiNeVisualCore_fuser_None_ds_balanced_broad_eval_foodinbowl/20231230065556/models/model_epoch_1100.pth"

# CKPT_PATH = "/home/ashwinbalakrishna/Desktop/data/r2d2-multitask/r2d2/im/diffusion_policy/12-29-None/cams_wrist_goal_mode_None_truncated_geom_factor_0.3_ldkeys_proprio-cam-lang_visenc_DeFiNeVisualCore_fuser_None_ds_balanced_broad_eval_foodinbowl/20231229053947/models/model_epoch_1500.pth"



# aws s3 sync s3://r2d2-multitask/r2d2/im/diffusion_policy/12-30-None/ /home/ashwinbalakrishna/Desktop/data/r2d2-multitask/r2d2/im/diffusion_policy/12-30-None/ --exclude "*" --include "*100.pth"

# CKPT_PATH = "/home/ashwinbalakrishna/Desktop/data/r2d2-multitask/r2d2/im/diffusion_policy/12-29-None/cams_wrist_goal_mode_None_truncated_geom_factor_0.3_ldkeys_proprio-cam-lang_visenc_DeFiNeVisualCore_fuser_None_ds_eval_closemicro/20231229053941/models/model_epoch_1500.pth"
# CKPT_PATH = "/home/ashwinbalakrishna/Desktop/data/r2d2-multitask/r2d2/im/diffusion_policy/12-29-None/cams_wrist_goal_mode_None_truncated_geom_factor_0.3_ldkeys_proprio-cam-lang_visenc_DeFiNeVisualCore_fuser_None_ds_balanced_broad_eval_closemicro/20231229053956/models/model_epoch_1500.pth"
# CKPT_PATH = "/home/ashwinbalakrishna/Desktop/data/r2d2-multitask/r2d2/im/diffusion_policy/12-30-None/cams_3cams_goal_mode_None_truncated_geom_factor_0.3_ldkeys_proprio-cam-lang_visenc_DeFiNeVisualCore_fuser_None_ds_eval_closemicro/20231230065525/models/model_epoch_1100.pth"

# CKPT_PATH = "/home/ashwinbalakrishna/Desktop/data/r2d2-multitask/r2d2/im/diffusion_policy/12-29-None/cams_wrist_goal_mode_None_truncated_geom_factor_0.3_ldkeys_proprio-cam-lang_visenc_DeFiNeVisualCore_fuser_None_ds_balanced_broad_eval_closemicro/20231229053956/models/model_epoch_500.pth"


############################## EVAL 1/14 ############################
# CKPT_PATH = "/home/ashwinbalakrishna/Desktop/data/r2d2-multitask/r2d2/im/diffusion_policy/01-12-None/cams_3cams_goal_mode_geom_truncated_geom_factor_0.3_ldkeys_proprio-cam_inpmap_define_visenc_DeFiNeVisualCore_fuser_None_ds_eval_multi/20240112175039/models/model_epoch_50.pth"

# CKPT_PATH = "/home/ashwinbalakrishna/Desktop/data/r2d2-multitask/r2d2/im/diffusion_policy/01-12-None/cams_wrist_goal_mode_geom_truncated_geom_factor_0.3_ldkeys_proprio-cam_inpmap_define_visenc_DeFiNeVisualCore_fuser_None_ds_eval_multi/20240112174742/models/model_epoch_200.pth"

# CKPT_PATH = "/home/ashwinbalakrishna/Desktop/data/r2d2-multitask/r2d2/im/diffusion_policy/01-12-None/cams_3cams_goal_mode_None_truncated_geom_factor_0.3_ldkeys_proprio-cam-lang_inpmap_define_visenc_DeFiNeVisualCore_fuser_None_ds_eval_multi/20240112175349/models/model_epoch_100.pth"
# CKPT_PATH = "/home/ashwinbalakrishna/Desktop/data/r2d2-multitask/r2d2/im/diffusion_policy/01-12-None/cams_3cams_goal_mode_None_truncated_geom_factor_0.3_ldkeys_proprio-cam-lang_inpmap_define_visenc_DeFiNeVisualCore_fuser_None_ds_balanced_broad_eval_multi/20240112074228/models/model_epoch_150.pth"

# CKPT_PATH = "/home/ashwinbalakrishna/Desktop/data/r2d2-multitask/r2d2/im/diffusion_policy/01-12-None/cams_wrist_goal_mode_None_truncated_geom_factor_0.3_ldkeys_proprio-cam-lang_inpmap_define-film-lang_visenc_DeFiNeVisualCore_fuser_None_ds_eval_multi/20240112175048/models/model_epoch_300.pth"




########################################### 1/21 #################################################
# CKPT_PATH = "/home/ashwinbalakrishna/Desktop/data/r2d2-multitask/r2d2/im/bc_xfmr/01-18-None/bz_128_cams_3cams_goal_mode_None_truncated_geom_factor_0.3_ldkeys_proprio-cam-lang_inpmap_define_visenc_DeFiNeVisualCore_fuser_None_ds_eval_apple_H_2/20240118083638/models/model_epoch_100.pth"

# CKPT_PATH="/home/ashwinbalakrishna/Desktop/data/r2d2-multitask/r2d2/im/diffusion_policy/01-18-None/bz_128_noise_samples_8_cams_wrist_goal_mode_None_truncated_geom_factor_0.3_ldkeys_proprio-cam-lang_inpmap_define_visenc_DeFiNeVisualCore_fuser_None_ds_eval_apple/20240118084053/models/model_epoch_400.pth"

# CKPT_PATH="/home/ashwinbalakrishna/Desktop/data/r2d2-multitask/r2d2/im/bc_xfmr/01-18-None/bz_128_cams_3cams_goal_mode_None_truncated_geom_factor_0.3_ldkeys_proprio-cam-lang_inpmap_define_visenc_DeFiNeVisualCore_fuser_None_ds_eval_apple_H_2/20240118083638/models/model_epoch_100.pth"

# CKPT_PATH="/home/ashwinbalakrishna/Desktop/data/r2d2-multitask/r2d2/im/diffusion_policy/01-18-None/bz_128_noise_samples_8_cams_3cams_goal_mode_None_truncated_geom_factor_0.3_ldkeys_proprio-cam-lang_inpmap_define_visenc_DeFiNeVisualCore_fuser_None_ds_eval_apple/20240118084433/models/model_epoch_100.pth"

# CKPT_PATH="/home/ashwinbalakrishna/Desktop/data/r2d2-multitask/r2d2/im/diffusion_policy/01-18-None/bz_128_noise_samples_8_cams_3cams_goal_mode_None_truncated_geom_factor_0.3_ldkeys_proprio-cam-lang_inpmap_define_visenc_DeFiNeVisualCore_fuser_None_ds_balanced_apple/20240118084447/models/model_epoch_100.pth"

# CKPT_PATH="/home/ashwinbalakrishna/Desktop/data/r2d2-multitask/r2d2/im/bc_xfmr/01-18-None/bz_128_cams_3cams_goal_mode_None_truncated_geom_factor_0.3_ldkeys_proprio-cam-lang_inpmap_define_visenc_DeFiNeVisualCore_fuser_None_ds_balanced_apple_H_2/20240118083653/models/model_epoch_100.pth"

# CKPT_PATH="/home/ashwinbalakrishna/Desktop/data/r2d2-multitask/r2d2/im/diffusion_policy/01-18-None/bz_128_noise_samples_8_cams_wrist_goal_mode_None_truncated_geom_factor_0.3_ldkeys_proprio-cam-lang_inpmap_define_visenc_DeFiNeVisualCore_fuser_None_ds_balanced_apple/20240118084108/models/model_epoch_400.pth"




# Chips, single task 3 cam diffusion, lang
# CKPT_PATH = "/home/ashwinbalakrishna/Desktop/data/r2d2-multitask/r2d2/im/diffusion_policy/01-18-None/bz_128_noise_samples_8_cams_3cams_goal_mode_None_truncated_geom_factor_0.3_ldkeys_proprio-cam-lang_inpmap_define_visenc_DeFiNeVisualCore_fuser_None_ds_eval_chips/20240118084429/models/model_epoch_100.pth"

# Chips, single task wrist diffusion lang
# CKPT_PATH = "/home/ashwinbalakrishna/Desktop/data/r2d2-multitask/r2d2/im/diffusion_policy/01-18-None/bz_128_noise_samples_8_cams_wrist_goal_mode_None_truncated_geom_factor_0.3_ldkeys_proprio-cam-lang_inpmap_define_visenc_DeFiNeVisualCore_fuser_None_ds_eval_chips/20240118084052/models/model_epoch_400.pth"

# Chips, co-train, wrist diffusion lang
# CKPT_PATH = "/home/ashwinbalakrishna/Desktop/data/r2d2-multitask/r2d2/im/diffusion_policy/01-18-None/bz_128_noise_samples_8_cams_wrist_goal_mode_None_truncated_geom_factor_0.3_ldkeys_proprio-cam-lang_inpmap_define_visenc_DeFiNeVisualCore_fuser_None_ds_balanced_chips/20240118084103/models/model_epoch_400.pth"

# chips, single task, wrist diffusion goal cond
# CKPT_PATH = "/home/ashwinbalakrishna/Desktop/data/r2d2-multitask/r2d2/im/diffusion_policy/01-18-None/bz_128_noise_samples_8_cams_wrist_goal_mode_geom_truncated_geom_factor_0.3_ldkeys_proprio-cam_inpmap_define_visenc_DeFiNeVisualCore_fuser_None_ds_eval_chips/20240118083415/models/model_epoch_300.pth"



# Chips, single task 3 cam bc transformer, lang
# CKPT_PATH = "/home/ashwinbalakrishna/Desktop/data/r2d2-multitask/r2d2/im/bc_xfmr/01-18-None/bz_128_cams_3cams_goal_mode_None_truncated_geom_factor_0.3_ldkeys_proprio-cam-lang_inpmap_define_visenc_DeFiNeVisualCore_fuser_None_ds_eval_chips_H_2/20240118083636/models/model_epoch_100.pth"

# Chips, single task wrist bc transformer lang
# CKPT_PATH = "/home/ashwinbalakrishna/Desktop/data/r2d2-multitask/r2d2/im/bc_xfmr/01-18-None/bz_128_cams_wrist_goal_mode_None_truncated_geom_factor_0.3_ldkeys_proprio-cam-lang_inpmap_define_visenc_DeFiNeVisualCore_fuser_None_ds_eval_chips_H_2/20240118083252/models/model_epoch_400.pth"

# Chips, co-train, wrist bc transformer lang
# CKPT_PATH = "/home/ashwinbalakrishna/Desktop/data/r2d2-multitask/r2d2/im/bc_xfmr/01-18-None/bz_128_cams_wrist_goal_mode_None_truncated_geom_factor_0.3_ldkeys_proprio-cam-lang_inpmap_define_visenc_DeFiNeVisualCore_fuser_None_ds_balanced_chips_H_2/20240118083307/models/model_epoch_400.pth"


# 01/22 --> Chips Narrow Evals --------------------

# CKPT_PATH = "/home/ashwinbalakrishna/Desktop/data/r2d2-multitask/r2d2/im/diffusion_policy/01-22-None/bz_128_noise_samples_8_cams_2cams_goal_mode_None_truncated_geom_factor_0.3_ldkeys_proprio-lang_visenc_VisualCore_fuser_None_ds_eval_chips/20240122062832/models/model_epoch_50.pth"
# 
# CKPT_PATH = "/home/ashwinbalakrishna/Desktop/data/r2d2-multitask/r2d2/im/diffusion_policy/01-22-None/bz_128_noise_samples_8_cams_wrist_goal_mode_None_truncated_geom_factor_0.3_ldkeys_proprio-lang_visenc_VisualCore_fuser_None_ds_eval_chips/20240122062659/models/model_epoch_150.pth"

# CKPT_PATH = "/home/ashwinbalakrishna/Desktop/data/r2d2-multitask/r2d2/im/bc_xfmr/01-22-None/bz_128_cams_2cams_goal_mode_None_truncated_geom_factor_0.3_ldkeys_proprio-lang_visenc_VisualCore_fuser_None_ds_eval_chips_H_2/20240122062629/models/model_epoch_100.pth"

# CKPT_PATH = "/home/ashwinbalakrishna/Desktop/data/r2d2-multitask/r2d2/im/bc_xfmr/01-22-None/bz_128_cams_wrist_goal_mode_None_truncated_geom_factor_0.3_ldkeys_proprio-lang_visenc_VisualCore_fuser_None_ds_eval_chips_H_2/20240122062436/models/model_epoch_150.pth"








# -------------------- -------------------- 01/22 --> Chips Cotrain filtered Evals -------------------- --------------------

# Narrow, language conditioned 2 cam

# CKPT_PATH = "/home/ashwinbalakrishna/Desktop/data/r2d2-multitask/r2d2/im/diffusion_policy/01-22-None/bz_128_noise_samples_8_cams_2cams_goal_mode_None_truncated_geom_factor_0.3_ldkeys_proprio-lang_visenc_VisualCore_fuser_None_ds_eval_chips/20240122062832/models/model_epoch_50.pth"

# Co-Train Filtered, language conditioned 2 cam

# CKPT_PATH="/home/ashwinbalakrishna/Desktop/data/r2d2-multitask/r2d2/im/diffusion_policy/01-22-None/bz_128_noise_samples_8_cams_2cams_goal_mode_None_truncated_geom_factor_0.3_ldkeys_proprio-lang_visenc_VisualCore_fuser_None_ds_balanced_chips/20240122062837/models/model_epoch_50.pth"

# Co-Train full R2D2 language conditioned 2 cam

# CKPT_PATH="/home/ashwinbalakrishna/Desktop/data/r2d2-multitask/r2d2/im/diffusion_policy/01-22-None/bz_128_noise_samples_8_cams_2cams_goal_mode_None_truncated_geom_factor_0.3_ldkeys_proprio-lang_visenc_VisualCore_fuser_None_ds_full_balanced_chips/20240122062843/models/model_epoch_50.pth"


### GC
# CKPT_PATH = "/home/ashwinbalakrishna/Desktop/data/r2d2-multitask/r2d2/im/diffusion_policy/01-22-None/bz_128_noise_samples_8_cams_wrist_goal_mode_geom_truncated_geom_factor_0.3_ldkeys_proprio_visenc_VisualCore_fuser_None_ds_full_balanced_chips/20240122062654/models/model_epoch_50.pth"

variant = dict(
    exp_name="policy_test",
    save_data=False,
    use_gpu=True,
    seed=0,
    policy_logdir="test",
    task="",
    layout_id=None,
    model_id=50,
    camera_kwargs=dict(),
    data_processing_kwargs=dict(
        timestep_filtering_kwargs=dict(),
        image_transform_kwargs=dict(),
    ),
    ckpt_path=CKPT_PATH,
)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-g', '--capture_goal', action='store_true')
    parser.add_argument('-l', '--lang_cond', action='store_true')
    args = parser.parse_args()
    if args.capture_goal:
        valid_values = ["yes", "no"]
        goal_im_ok = False

        while goal_im_ok is not True:
            program_mode = input("Move the robot into programming mode, adjust the scene as needed, and then press Enter to acknowledge: ")
            exec_mode = input("Now move the robot into execution mode, press Enter to acknowledge: ")
            print("Capturing Goal Image")
            goal_ims = get_goal_im(variant, run_id=1, exp_id=0)
            # Sort the goal_ims by key and display in a 3 x 2 grid
            sort_goal_ims = [cv2.cvtColor(image[1][:, :, :3], cv2.COLOR_BGR2RGB) for image in sorted(goal_ims.items(), key=lambda x: x[0])]
            fig, axes = plt.subplots(3, 2, figsize=(8,10))
            axes = axes.flatten()
            for i in range(len(sort_goal_ims)):
                axes[i].imshow(sort_goal_ims[i])
                axes[i].axis('off')
            plt.tight_layout()
            plt.show()

            user_input = input("Do these goal images look reasonable? Enter Yes or No: ").lower()
            while user_input not in valid_values:
                print("Invalid input, Please enter Yes or No")
            goal_im_ok = user_input == "yes"
        input("Now reset the scene for the policy to execute, press Enter to acknowledge: ")
    if args.lang_cond:
        user_input = input("Provide a language command for the robot to complete: ").lower()
        with open('eval_params/lang_command.txt', 'w') as file:
            file.write(user_input)
    
    print("Evaluating Policy")
    eval_launcher(variant, run_id=1, exp_id=0)
