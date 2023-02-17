from r2d2.evaluation.eval_launcher import eval_launcher

variant = dict(
    exp_name='policy_test',
    save_data=False,
    use_gpu=True,
    seed=0,

    policy_logdir='simple_bc/run6/id0/',
    model_id=0,

    camera_kwargs=dict(),
    data_processing_kwargs=dict(
        timestep_filtering_kwargs=dict(),
        image_transform_kwargs=dict(),
    ),

)

if __name__ == "__main__":
    eval_launcher(variant, run_id=1, exp_id=0)
