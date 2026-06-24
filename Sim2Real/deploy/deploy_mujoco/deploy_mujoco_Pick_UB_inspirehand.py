import argparse

from deploy_mujoco_inspirehand_common import InspireHandTask, run_inspirehand_ub_task


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("config_file", type=str, help="config file name in the config folder")
    parser.add_argument("--headless", action="store_true", help="run without opening the MuJoCo viewer")
    parser.add_argument("--max_time_s", type=float, default=None, help="stop after this many simulated seconds")
    args = parser.parse_args()

    run_inspirehand_ub_task(
        args.config_file,
        InspireHandTask(
            policy_name="Pick_UB.pt",
            scene_name="scene_fixed_base_pick_inspirehand.xml",
            initial_object_pose=[0.45, -0.2, 0.293, 1.0, 0.0, 0.0, 0.0],
            reset_after=7.0,
            reset_low=[0.42, -0.3, 0.293],
            reset_high=[0.48, 0.0, 0.293],
            object_pose_offset=[0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
            event_time=4.75,
            obs_object_offset=[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            free_object=True,
            hand_mapping="swapped",
            settle_steps=400,
            hand_schedule="event",
            object_obs_z_bias=-0.03,
            metrics_name="pick_inspirehand",
            headless=args.headless,
            max_time_s=args.max_time_s,
        ),
    )
