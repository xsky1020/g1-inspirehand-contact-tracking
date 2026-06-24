import argparse

from deploy_mujoco_inspirehand_common import InspireHandTask, run_inspirehand_ub_task


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("config_file", type=str, help="config file name in the config folder")
    args = parser.parse_args()

    run_inspirehand_ub_task(
        args.config_file,
        InspireHandTask(
            policy_name="Button_Press_UB.pt",
            scene_name="scene_fixed_base_button_press_inspirehand.xml",
            initial_object_pose=[0.45, -0.04, 0.2, 1.0, 0.0, 0.0, 0.0],
            reset_after=7.0,
            reset_low=[0.43, -0.27, 0.13],
            reset_high=[0.54, -0.04, 0.29],
            object_pose_offset=[0.03, 0.0, 0.793, 0.0, 0.0, 0.0, 0.0],
            event_time=2.9,
            obs_object_offset=[-0.07, 0.0, -0.005, 0.0, 0.0, 0.0, 0.0],
            hand_mapping="closed_only",
            metrics_name="button_press_inspirehand",
        ),
    )
