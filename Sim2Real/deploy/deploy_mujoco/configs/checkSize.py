import yaml
import numpy as np
with open("g1_ih.yaml","r") as f:
    config=yaml.load(f, Loader=yaml.FullLoader)
    default_angles = np.array(config["default_angles"])
    joint_names = config["joint_names"]
    kps = np.array(config["kps"])
    kds = np.array(config["kds"])
    print("kps length:", len(kps))
    print("kds length:", len(kds))
    print("joint_names length:", len(joint_names))
    print("default_angles length:", len(default_angles))