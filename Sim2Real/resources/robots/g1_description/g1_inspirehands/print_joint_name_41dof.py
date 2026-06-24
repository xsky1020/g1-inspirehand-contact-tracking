import mujoco
import yaml
with open("/Users/yanmin/Documents/2a-科研归档/DreamControl/Sim2Real/deploy/deploy_mujoco/configs/g1_ih.yaml", "r") as f:
    config = yaml.load(f, Loader=yaml.FullLoader)  
xml_file_path="g1_inspirehands_copy.xml"
xml_file_path2="/Users/yanmin/Documents/2a-科研归档/DreamControl/Sim2Real/resources/robots/g1_description/g1_27dof_with_hand_rev_1_0_fixed.xml"
xml_file_path3="/Users/yanmin/Documents/2a-科研归档/DreamControl/Sim2Real/resources/robots/g1_description/g1_29dof_with_hand.xml"

# # Load model from MJCF (XML)
# model = mujoco.MjModel.from_xml_path(xml_file_path)
# data = mujoco.MjData(model)

# # 1. Print the compiled mjModel structure
# # print(model)

left_hand_joint_names= config["left_hand_joint_names"]

right_hand_joint_names= config["right_hand_joint_names"]

left_hand_mimic_joitn_names= config["left_hand_mimic_joitn_names"]
right_hand_mimic_joitn_names= config["right_hand_mimic_joitn_names"]

model1 = mujoco.MjModel.from_xml_path(xml_file_path)
data1 = mujoco.MjData(model1)
print("Number of joints in model1:", model1.njnt)
print("Actuator names in model1:",model1.nu)
print("qves",data1.qvel.shape)
left_hand_joint_ids=[model1.joint(name).id for name in left_hand_joint_names]
print("Joint IDs for left hand actuator:", left_hand_joint_ids)

right_hand_joint_ids=[model1.joint(name).id for name in right_hand_joint_names]
print("Joint IDs for right hand actuator:", right_hand_joint_ids)

# left_hand_actuators_ids=[model1.actuator(name).id for name in left_hand_joint_names]
# print("Actuator IDs for left hand:", left_hand_actuators_ids)

# right_hand_actuators_ids=[model1.actuator(name).id for name in right_hand_joint_names]
# print("Actuator IDs for right hand:", right_hand_actuators_ids)

left_hand_mimic_joint_ids=[model1.joint(name).id for name in left_hand_mimic_joitn_names]
print("Joint IDs for left hand mimic joints:", left_hand_mimic_joint_ids)

right_hand_mimic_joint_ids=[model1.joint(name).id for name in right_hand_mimic_joitn_names]
print("Joint IDs for right hand mimic joints:", right_hand_mimic_joint_ids)

print("All actuator ids", [model1.joint(model1.actuator(i).name).id for i in range(model1.nu)])


# for i in range(model1.njnt):
#     model1_joints.add(model1.joint(i).name)
    # print(model1.joint(i).name) 
# # 2. To print specific XML-like details (compiled)
# # print("Number of bodies:", model.nbody)
# # print("Body names:", [model.names[model.name_bodyadr[i]:].split(b'\x00')[0].decode('utf-8') for i in range(model.nbody)])
# list_of_joints = [model.names[model.name_jntadr[i]:].split(b'\x00')[0].decode('utf-8') for i in range(model.njnt)]

# model2 = mujoco.MjModel.from_xml_path(xml_file_path2)
# data2 = mujoco.MjData(model2)
# print("Number of joints in model1:", model2.njnt)
# print("Actuator names in model1:",model2.nu)
# model2_joints=set()
# for i in range(model2.njnt):
#     model2_joints.add(model2.joint(i).name)
    # print(model2.joint(i).name) 
    
# print("Different joints between model1 and model2:", sorted(model1_joints - model2_joints))
# print(model2)
# print("Number of bodies in model2:", model2.njnt)
# print(data2.qpos.shape)
# print("Body names in model2:", [model2.names[model2.name_bodyadr[i]:].split(b'\x00')[0].decode('utf-8') for i in range(model2.nbody)])
# list_of_joints2 = [model2.names[model2.name_jntadr[i]:].split(b'\x00')[0].decode('utf-8') for i in range(model2.njnt)]

# model3 = mujoco.MjModel.from_xml_path(xml_file_path3)
# # print(model3)
# # print("Number of bodies in model3:", model3.nbody)
# # print("Body names in model3:", [model3.names[model3.name_bodyadr[i]:].split(b'\x00')[0].decode('utf-8') for i in range(model3.nbody)])
# list_of_joints3=[model3.names[model3.name_jntadr[i]:].split(b'\x00')[0].decode('utf-8') for i in range(model3.njnt)]
# diff_joints = set(list_of_joints) - set(list_of_joints3)
# print("Size of different joints:", len(diff_joints))
# print("Joints in model1 but not in model3:", sorted(diff_joints))
