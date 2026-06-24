import argparse
import math
import time
from pathlib import Path

import mujoco
import mujoco.viewer
import numpy as np
import yaml


SCRIPT_DIR = Path(__file__).resolve().parent
SIM2REAL_DIR = SCRIPT_DIR.parents[1]
DEFAULT_CONFIG = SCRIPT_DIR / "configs" / "g1_ih.yaml"
DEFAULT_SCENE = (
    SIM2REAL_DIR
    / "resources"
    / "robots"
    / "g1_description"
    / "g1_inspirehands"
    / "scene_fixed_base_button_press_inspirehand.xml"
)


def load_yaml(path):
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def set_joint_position(model, data, joint_name, value):
    joint_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, joint_name)
    if joint_id < 0:
        return False
    data.qpos[model.jnt_qposadr[joint_id]] = value
    return True


def actuator_ids(model, names):
    ids = []
    missing = []
    for name in names:
        actuator_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_ACTUATOR, name)
        if actuator_id < 0:
            missing.append(name)
        else:
            ids.append(actuator_id)
    if missing:
        raise RuntimeError("Missing actuators: " + ", ".join(missing))
    return ids


def apply_default_pose(model, data, config):
    joint_names = config["joint_names"]
    default_angles = config["default_angles"]
    if len(joint_names) != len(default_angles):
        raise RuntimeError(
            f"joint_names has {len(joint_names)} entries but default_angles has {len(default_angles)}"
        )

    missing = []
    for name, value in zip(joint_names, default_angles):
        if not set_joint_position(model, data, name, float(value)):
            missing.append(name)

    if missing:
        print("Skipped joints not found in XML:")
        for name in missing:
            print(f"  {name}")

    mujoco.mj_forward(model, data)


def blend(open_angles, closed_angles, alpha):
    return open_angles * (1.0 - alpha) + closed_angles * alpha


def main():
    parser = argparse.ArgumentParser(description="Showcase the G1 Inspire Hand model without a policy file.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--scene", type=Path, default=DEFAULT_SCENE)
    parser.add_argument("--duration", type=float, default=30.0)
    args = parser.parse_args()

    config = load_yaml(args.config)
    model = mujoco.MjModel.from_xml_path(str(args.scene))
    data = mujoco.MjData(model)
    model.opt.timestep = float(config.get("simulation_dt", 0.001))

    apply_default_pose(model, data, config)

    left_hand_names = config["left_hand_joint_names"]
    right_hand_names = config["right_hand_joint_names"]
    left_ids = actuator_ids(model, left_hand_names)
    right_ids = actuator_ids(model, right_hand_names)

    left_open = np.array(config["left_hand_open_joint_angles"], dtype=np.float64)
    left_closed = np.array(config["left_hand_closed_joint_angles"], dtype=np.float64)
    right_open = np.array(config["right_hand_open_joint_angles"], dtype=np.float64)
    right_closed = np.array(config["right_hand_closed_joint_angles"], dtype=np.float64)

    if not (len(left_ids) == len(left_open) == len(left_closed)):
        raise RuntimeError("Left hand actuator count does not match open/closed angle count.")
    if not (len(right_ids) == len(right_open) == len(right_closed)):
        raise RuntimeError("Right hand actuator count does not match open/closed angle count.")

    print(f"Loaded scene: {args.scene}")
    print(f"Model joints={model.njnt}, qpos={model.nq}, actuators={model.nu}")
    print("Demo cycles: both open, right closes, left closes, both close.")

    with mujoco.viewer.launch_passive(model, data) as viewer:
        start = time.time()
        while viewer.is_running():
            elapsed = time.time() - start
            if elapsed > args.duration:
                break

            phase = (elapsed % 8.0) / 8.0
            wave = 0.5 - 0.5 * math.cos(2.0 * math.pi * phase)

            if phase < 0.25:
                left_alpha = 0.0
                right_alpha = 0.0
            elif phase < 0.5:
                left_alpha = 0.0
                right_alpha = wave
            elif phase < 0.75:
                left_alpha = wave
                right_alpha = 1.0
            else:
                left_alpha = 1.0
                right_alpha = 1.0

            data.ctrl[left_ids] = blend(left_open, left_closed, left_alpha)
            data.ctrl[right_ids] = blend(right_open, right_closed, right_alpha)

            mujoco.mj_step(model, data)
            viewer.sync()
            time.sleep(model.opt.timestep)


if __name__ == "__main__":
    main()
