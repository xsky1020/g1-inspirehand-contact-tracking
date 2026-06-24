"""
可视化 G1 机器人在 MuJoCo 中的姿态。
从 YAML 配置读取关节名和默认角度，设置到 XML 模型中并可视化。

用法:
    mjpython visualize_pose.py [yaml_config]
    
    默认使用 configs/g1 copy.yaml
"""

import sys
import faulthandler
import traceback
import yaml
import numpy as np
import mujoco
import mujoco.viewer

# 启用 faulthandler，捕获 C 层 segfault 等崩溃的堆栈
faulthandler.enable()

# ─── 配置路径 ─── 

DEFAULT_XML = "../../resources/robots/g1_description/g1_inspirehands/g1_inspirehands copy.xml"
DEFAULT_YAML = "configs/g1 copy.yaml"

# DEFAULT_XML="../../resources/robots/g1_description/g1_27dof_with_hand_rev_1_0_fixed.xml"
# DEFAULT_YAML = "configs/g1.yaml"


def load_config(yaml_path):
    with open(yaml_path, "r") as f:
        return yaml.safe_load(f)


def main():
    yaml_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_YAML
    
    # 加载配置
    cfg = load_config(yaml_path)
    joint_names = cfg["joint_names"]
    default_angles = cfg["default_angles"]
    
    print(f"加载 YAML: {yaml_path}")
    print(f"关节数: {len(joint_names)}")
    print(f"默认角度数: {len(default_angles)}")

    # 加载 MuJoCo 模型
    xml_path = cfg.get("xml_path", DEFAULT_XML)
    # 如果 yaml 里的路径带占位符，用默认路径
    if "{" in xml_path:
        xml_path = DEFAULT_XML

    print(f"加载 XML: {xml_path}")
    model = mujoco.MjModel.from_xml_path(xml_path)
    data = mujoco.MjData(model)

    # 打印模型信息
    print(f"\n模型关节总数 (model.njnt): {model.njnt}")
    print(f"qpos 维度: {model.nq}")
    print(f"actuator 数量: {model.nu}")
    
    # 检测是否有 freejoint（前 7 个 qpos 是 base 的 pos + quat）
    has_freejoint = False
    for i in range(model.njnt):
        jnt_name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, i)
        if model.jnt_type[i] == mujoco.mjtJoint.mjJNT_FREE:
            has_freejoint = True
            print(f"\n检测到 freejoint: {jnt_name}")
            break

    # 辅助函数：查找关节 ID，自动处理 _link/_joint 命名差异
    def find_joint_id(model, name):
        """查找关节 ID，若 name 以 _link 结尾但找不到，自动尝试替换为 _joint"""
        jid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, name)
        if jid == -1 and name.endswith("_link"):
            alt_name = name[:-5] + "_joint"
            jid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, alt_name)
            if jid != -1:
                print(f"  [名称修正] '{name}' -> '{alt_name}'")
        return jid

    # 设置关节角度
    print("\n─── 设置关节角度 ───")
    set_count = 0
    for name, angle in zip(joint_names, default_angles):
        jid = find_joint_id(model, name)
        if jid == -1:
            print(f"  [跳过] 关节 '{name}' 在 XML 中未找到")
            continue
        qpos_addr = model.jnt_qposadr[jid]
        data.qpos[qpos_addr] = angle
        set_count += 1

    print(f"\n成功设置 {set_count}/{len(joint_names)} 个关节")

    # ─── 设置右手为握拳姿态 ───
    right_hand_names = cfg.get("right_hand_joint_names", [])
    right_hand_angles = cfg.get("right_hand_closed_joint_angles", [])
    print("\n─── 设置右手握拳 ───")
    for name, angle in zip(right_hand_names, right_hand_angles):
        jid = find_joint_id(model, name)
        if jid == -1:
            print(f"  [跳过] 关节 '{name}' 在 XML 中未找到")
            continue
        qpos_addr = model.jnt_qposadr[jid]
        data.qpos[qpos_addr] = angle
        print(f"  {name:40s} -> {angle:+.4f} rad ({np.degrees(angle):+.2f}°)")

    # ─── 设置左手为握拳姿态 ───
    left_hand_names = cfg.get("left_hand_joint_names", [])
    left_hand_angles = cfg.get("left_hand_closed_joint_angles", [])
    print("\n─── 设置左手握拳 ───")
    for name, angle in zip(left_hand_names, left_hand_angles):
        jid = find_joint_id(model, name)
        if jid == -1:
            print(f"  [跳过] 关节 '{name}' 在 XML 中未找到")
            continue
        qpos_addr = model.jnt_qposadr[jid]
        data.qpos[qpos_addr] = angle
        print(f"  {name:40s} -> {angle:+.4f} rad ({np.degrees(angle):+.2f}°)")
    
    # 如果有 freejoint，确保 base 位置合理
    if has_freejoint:
        # qpos[0:3] = position, qpos[3:7] = quaternion (w,x,y,z)
        data.qpos[2] = 0.793  # 站立高度
        data.qpos[3] = 1.0    # quat w
        data.qpos[4] = 0.0    # quat x
        data.qpos[5] = 0.0    # quat y
        data.qpos[6] = 0.0    # quat z

    # 前向运动学
    mujoco.mj_forward(model, data)

    # ─── 处理 equality 约束（手指耦合关节） ───
    # equality 中的 joint 约束形式: joint1 = polycoef[0] + polycoef[1]*joint2
    # 需要根据 proximal 关节角度计算 intermediate 关节角度
    print("\n─── 处理 equality 耦合关节 ───")
    for i in range(model.neq):
        eq_type = model.eq_type[i]
        if eq_type != mujoco.mjtEq.mjEQ_JOINT:
            continue
        # eq_obj1id = joint1 (从属关节), eq_obj2id = joint2 (主关节)
        jid1 = model.eq_obj1id[i]
        jid2 = model.eq_obj2id[i]
        name1 = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, jid1)
        name2 = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, jid2)
        polycoef = model.eq_data[i]  # [c0, c1, c2, c3, c4, ...]
        c0, c1 = polycoef[0], polycoef[1]
        
        addr1 = model.jnt_qposadr[jid1]
        addr2 = model.jnt_qposadr[jid2]
        q2 = data.qpos[addr2]
        # joint1 = c0 + c1 * joint2 (线性近似，忽略高阶项)
        q1 = c0 + c1 * q2
        data.qpos[addr1] = q1
        print(f"  {name1:40s} = {c0:.5f} + {c1:.5f} * {name2}({q2:+.4f}) -> {q1:+.4f} rad")

    # 重新计算前向运动学
    mujoco.mj_forward(model, data)

    # 打印当前所有关节角度
    print("\n─── 当前关节状态 ───")
    for i in range(model.njnt):
        jnt_name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, i)
        if model.jnt_type[i] == mujoco.mjtJoint.mjJNT_FREE:
            continue
        qpos_addr = model.jnt_qposadr[i]
        angle_rad = data.qpos[qpos_addr]
        angle_deg = np.degrees(angle_rad)
        print(f"  {jnt_name:40s}  {angle_rad:+8.4f} rad  ({angle_deg:+8.2f}°)")

    # 启动可视化（只刷新显示，不运行物理仿真，姿态保持不变）
    print("\n启动 MuJoCo Viewer... (关闭窗口或 Ctrl+C 退出)")
    import time
    with mujoco.viewer.launch_passive(model, data) as v:
        while v.is_running():
            time.sleep(0.02)  # 不调用 mj_step，姿态冻结不变
            v.sync()

if __name__ == "__main__":
    main()
