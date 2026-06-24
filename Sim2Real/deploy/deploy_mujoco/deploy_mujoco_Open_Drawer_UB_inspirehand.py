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
            policy_name="Open_Drawer_UB.pt",
            scene_name="scene_fixed_base_drawer_inspirehand.xml",
            initial_object_pose=[0.39, -0.15, 0.0, 1.0, 0.0, 0.0, 0.0],
            reset_after=10.0,
            reset_low=[0.37, -0.2, -0.033],
            reset_high=[0.42, -0.1, 0.027],
            object_pose_offset=[0.2, 0.0, 0.753, 0.0, 0.0, 0.0, 0.0],
            event_time=3.0,
            hand_mapping="open_closed_cross",
            metrics_name="open_drawer_inspirehand",
            headless=args.headless,
            max_time_s=args.max_time_s,
        ),
    )
