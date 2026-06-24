# DreamControl Policy Interaction Evaluation

This repository is a compact handoff package for evaluating released DreamControl policies on MuJoCo object-interaction tasks.

Current focus:

> Run existing DreamControl policies and log contact-aware / object-aware metrics without retraining.

Included code:

- `Sim2Real/`: DreamControl Sim2Real/MuJoCo deployment code, policies, robot XML, and G1+InspireHand assets.
- `Sim2Real/deploy/deploy_mujoco/deploy_mujoco_metrics.py`: new interaction metric logger.
- root `*.md`: handoff notes, experiment plan, and Sunday report outline.

Primary runnable scripts:

```bash
cd Sim2Real/deploy/deploy_mujoco
mjpython deploy_mujoco_Pick_UB_inspirehand.py g1_ih.yaml
mjpython deploy_mujoco_Pick_Top_UB_inspirehand.py g1_ih.yaml
mjpython deploy_mujoco_Open_Drawer_UB_inspirehand.py g1_ih.yaml
mjpython deploy_mujoco_Button_Press_UB_inspirehand.py g1_ih.yaml
```

Each InspireHand common-runner script now writes CSV metrics under:

```text
Sim2Real/deploy/deploy_mujoco/metrics/
```

Logged metrics include:

- fingertip-object distance
- hand-object contact flag
- contact duration
- object displacement
- object height delta
- drawer slide progress
- simple success flags

Near-term Sunday report claim:

> DreamControl already contains task-level object-aware rewards, but released policies do not directly report finger-level contact quality. This repository adds evaluation metrics to quantify whether task demonstrations produce stable hand-object contact.

