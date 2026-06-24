import time
from dataclasses import dataclass

import mujoco
import mujoco.viewer
import numpy as np
import torch
import yaml

from deploy_mujoco_base import LEGGED_GYM_ROOT_DIR, JointNamesOrder_UB, get_gravity_orientation, pd_control
from deploy_mujoco_metrics import InteractionMetricLogger, InteractionMetrics


@dataclass
class InspireHandTask:
    policy_name: str
    scene_name: str
    initial_object_pose: list
    reset_after: float
    reset_low: list
    reset_high: list
    object_pose_offset: list
    event_time: float
    period: float = 10.0
    obs_object_offset: list | None = None
    top_pick_timing: bool = False
    free_object: bool = False
    hand_mapping: str = "normal"
    settle_steps: int = 0
    hand_schedule: str = "policy"
    object_obs_z_bias: float = 0.0
    metrics_name: str | None = None


def _read_config(config_file):
    with open(f"{LEGGED_GYM_ROOT_DIR}/deploy/deploy_mujoco/configs/{config_file}", "r", encoding="utf-8") as f:
        return yaml.load(f, Loader=yaml.FullLoader)


def _ids_by_name(model, obj_type, names):
    ids = []
    missing = []
    for name in names:
        idx = mujoco.mj_name2id(model, obj_type, name)
        if idx < 0:
            missing.append(name)
        else:
            ids.append(idx)
    if missing:
        raise RuntimeError("Missing MuJoCo names: " + ", ".join(missing))
    return ids


def _hand_angles(config, mapping):
    if mapping == "swapped":
        return (
            np.array(config["right_hand_open_joint_angles"]),
            np.array(config["left_hand_open_joint_angles"]),
            np.array(config["right_hand_closed_joint_angles"]),
            np.array(config["left_hand_closed_joint_angles"]),
        )
    if mapping == "open_closed_cross":
        return (
            np.array(config["left_hand_open_joint_angles"]),
            np.array(config["right_hand_closed_joint_angles"]),
            np.array(config["left_hand_closed_joint_angles"]),
            np.array(config["right_hand_open_joint_angles"]),
        )
    if mapping == "closed_only":
        return (
            np.array(config["left_hand_closed_joint_angles"]),
            np.array(config["right_hand_closed_joint_angles"]),
            np.array(config["left_hand_closed_joint_angles"]),
            np.array(config["right_hand_closed_joint_angles"]),
        )
    return (
        np.array(config["left_hand_open_joint_angles"]),
        np.array(config["right_hand_open_joint_angles"]),
        np.array(config["left_hand_closed_joint_angles"]),
        np.array(config["right_hand_closed_joint_angles"]),
    )


def run_inspirehand_ub_task(config_file, task: InspireHandTask):
    config = _read_config(config_file)
    policy_path = config["policy_path"].replace("{LEGGED_GYM_ROOT_DIR}", LEGGED_GYM_ROOT_DIR) + task.policy_name
    xml_path = config["xml_path"].replace("{LEGGED_GYM_ROOT_DIR}", LEGGED_GYM_ROOT_DIR)
    all_joint_names = config["joint_names"]
    simulation_dt = config["simulation_dt"]
    control_decimation = config["control_decimation"]

    kps = np.array(config["kps"], dtype=np.float32)
    kds = np.array(config["kds"], dtype=np.float32)
    default_angles = np.array(config["default_angles"], dtype=np.float32)
    action_scale = config["action_scale"]
    dof_pos_scale = config["dof_pos_scale"]
    dof_vel_scale = config["dof_vel_scale"]
    num_actions = config["num_actions"]
    num_obs = config["num_obs"]

    left_hand_joints = config["left_hand_joint_names"]
    right_hand_joints = config["right_hand_joint_names"]
    left_hand_open_ja, right_hand_open_ja, left_hand_closed_ja, right_hand_closed_ja = _hand_angles(
        config, task.hand_mapping
    )

    model = mujoco.MjModel.from_xml_path(xml_path + "g1_inspirehands/" + task.scene_name)
    data = mujoco.MjData(model)
    model.opt.timestep = simulation_dt
    policy = torch.jit.load(policy_path)

    active_joints = JointNamesOrder_UB
    active_joint_ids = [all_joint_names.index(name) for name in active_joints]
    left_hand_joint_ids = [all_joint_names.index(name) for name in left_hand_joints]
    right_hand_joint_ids = [all_joint_names.index(name) for name in right_hand_joints]
    active_actuator_ids = _ids_by_name(model, mujoco.mjtObj.mjOBJ_ACTUATOR, active_joints)
    left_hand_actuator_ids = _ids_by_name(model, mujoco.mjtObj.mjOBJ_ACTUATOR, left_hand_joints)
    right_hand_actuator_ids = _ids_by_name(model, mujoco.mjtObj.mjOBJ_ACTUATOR, right_hand_joints)

    target_dof_pos = default_angles[active_joint_ids].copy()
    target_dof_left_hand = default_angles[left_hand_joint_ids].copy()
    target_dof_right_hand = default_angles[right_hand_joint_ids].copy()
    action = np.zeros(num_actions, dtype=np.float32)
    obs = np.zeros(num_obs, dtype=np.float32)
    counter = 0

    def set_robot_default():
        data.qpos[:] = 0.0
        data.qvel[:] = 0.0
        data.qpos[: len(default_angles)] = default_angles

    def set_object_pose(rel_pose):
        pose = np.array(rel_pose) + np.array(task.object_pose_offset)
        if task.free_object:
            data.qpos[-7:] = pose
        else:
            body_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "object")
            if body_id < 0:
                raise RuntimeError("Scene has no body named 'object'.")
            model.body_pos[body_id] = pose[:3]
            model.body_quat[body_id] = pose[3:7]
            joint_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, "object_slide_x")
            if joint_id >= 0:
                data.qpos[model.jnt_qposadr[joint_id]] = 0.0
                data.qvel[model.jnt_dofadr[joint_id]] = 0.0

    def set_ctrl():
        tau = pd_control(
            target_dof_pos,
            data.qpos[active_joint_ids],
            kps[active_joint_ids],
            np.zeros_like(kds[active_joint_ids]),
            data.qvel[active_joint_ids],
            kds[active_joint_ids],
        )
        tau_left = pd_control(
            target_dof_left_hand,
            data.qpos[left_hand_joint_ids],
            kps[left_hand_joint_ids],
            np.zeros_like(kds[left_hand_joint_ids]),
            data.qvel[left_hand_joint_ids],
            kds[left_hand_joint_ids],
        )
        tau_right = pd_control(
            target_dof_right_hand,
            data.qpos[right_hand_joint_ids],
            kps[right_hand_joint_ids],
            np.zeros_like(kds[right_hand_joint_ids]),
            data.qvel[right_hand_joint_ids],
            kds[right_hand_joint_ids],
        )
        data.ctrl[active_actuator_ids] = tau
        data.ctrl[left_hand_actuator_ids] = tau_left
        data.ctrl[right_hand_actuator_ids] = tau_right

    def settle_scene():
        for _ in range(task.settle_steps):
            set_ctrl()
            mujoco.mj_step(model, data)

    rel_pose_object = list(task.initial_object_pose)
    set_robot_default()
    set_object_pose(rel_pose_object)
    settle_scene()
    mujoco.mj_forward(model, data)
    metric_logger = InteractionMetricLogger(
        model,
        data,
        InteractionMetrics(task_name=task.metrics_name or task.scene_name.replace(".xml", "")),
    )

    print(f"Loaded {task.scene_name}: joints={model.njnt}, qpos={model.nq}, actuators={model.nu}")
    try:
        with mujoco.viewer.launch_passive(model, data) as viewer:
            while viewer.is_running():
                step_start = time.time()

                if counter * simulation_dt > task.reset_after:
                    counter = 0
                    rel_pose_object = np.random.uniform(task.reset_low, task.reset_high).tolist()
                    rel_pose_object += [1.0, 0.0, 0.0, 0.0]
                    set_robot_default()
                    set_object_pose(rel_pose_object)
                    settle_scene()
                    mujoco.mj_forward(model, data)
                    metric_logger.reset_episode()

                set_ctrl()
                mujoco.mj_step(model, data)
                counter += 1
                metric_logger.update(counter * simulation_dt, simulation_dt)

                if counter % control_decimation == 0:
                    qj = data.qpos[active_joint_ids]
                    dqj = data.qvel[active_joint_ids]
                    qj_normalized = (qj - default_angles[active_joint_ids]) * dof_pos_scale
                    dqj_normalized = dqj * dof_vel_scale
                    gravity_orientation = get_gravity_orientation([1.0, 0.0, 0.0, 0.0])

                    count = counter * simulation_dt
                    phase = min(count, task.period) / task.period
                    sin_phase = np.sin(2 * np.pi * phase)
                    if task.top_pick_timing:
                        right_hand_state = np.exp(-np.abs(count - 0.475))
                        right_hand_state_1 = np.exp(-0.5 * np.abs(count - 0.475))
                    else:
                        right_hand_state = float(count > task.event_time)
                        right_hand_state_1 = float(count < task.event_time + 0.7 and count > task.event_time - 0.7)

                    object_obs = np.array(rel_pose_object)
                    if task.obs_object_offset is not None:
                        object_obs = object_obs + np.array(task.obs_object_offset)
                    object_obs[2] += task.object_obs_z_bias

                    obs[:3] = gravity_orientation
                    obs[3 : 3 + len(active_joint_ids)] = qj_normalized
                    obs[3 + len(active_joint_ids) : 3 + 2 * len(active_joint_ids)] = dqj_normalized
                    obs[3 + 2 * len(active_joint_ids) : 3 + 2 * len(active_joint_ids) + num_actions] = action
                    obs[
                        3 + 2 * len(active_joint_ids) + num_actions : 3 + 2 * len(active_joint_ids) + num_actions + 2
                    ] = np.array([phase, sin_phase])
                    base = 3 + 2 * len(active_joint_ids) + num_actions + 2
                    obs[base : base + 3] = object_obs[:3]
                    obs[base + 3 : base + 4] = np.array([right_hand_state])
                    obs[base + 4 : base + 5] = np.array([right_hand_state_1])

                    action = policy(torch.from_numpy(obs).unsqueeze(0)).detach().numpy().squeeze()
                    target_dof_pos = action[:-2] * action_scale + default_angles[active_joint_ids]
                    if task.hand_schedule == "event":
                        close_alpha = np.clip((count - (task.event_time - 0.6)) / 0.6, 0.0, 1.0)
                        target_dof_left_hand = left_hand_open_ja * (1 - close_alpha) + left_hand_closed_ja * close_alpha
                        target_dof_right_hand = right_hand_open_ja * (1 - close_alpha) + right_hand_closed_ja * close_alpha
                    else:
                        target_dof_left_hand = left_hand_open_ja * (1 - action[-2]) + left_hand_closed_ja * action[-2]
                        target_dof_right_hand = right_hand_open_ja * (1 - action[-1]) + right_hand_closed_ja * action[-1]

                viewer.sync()
                time_until_next_step = model.opt.timestep - (time.time() - step_start)
                if time_until_next_step > 0:
                    time.sleep(time_until_next_step)
    finally:
        metric_logger.close()
