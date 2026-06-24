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
            policy_name="Punch_UB.pt",
            scene_name="scene_fixed_base_object_inspirehand.xml",
            initial_object_pose=[0.45, -0.2, 0.2, 1.0, 0.0, 0.0, 0.0],
            reset_after=7.0,
            reset_low=[0.435, -0.27, 0.17],
            reset_high=[0.485, -0.04, 0.44],
            object_pose_offset=[0.13, 0.0, 0.883, 0.0, 0.0, 0.0, 0.0],
            event_time=3.5,
            obs_object_offset=[0.0, 0.0, 0.02, 0.0, 0.0, 0.0, 0.0],
            hand_mapping="closed_only",
            headless=args.headless,
            max_time_s=args.max_time_s,
        ),
    )
