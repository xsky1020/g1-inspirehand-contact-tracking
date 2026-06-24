# AI Agent Tasks

## Objective

Evaluate released DreamControl MuJoCo policies with contact-aware and object-aware metrics.

Do not start by retraining. First run existing policies and save videos/CSV logs.

## First Steps

```bash
cd Sim2Real/deploy/deploy_mujoco
python -c "import ast, pathlib; [ast.parse(pathlib.Path(p).read_text(encoding='utf-8')) for p in ['deploy_mujoco_metrics.py','deploy_mujoco_inspirehand_common.py']]"
```

Then run one task:

```bash
mjpython deploy_mujoco_Pick_UB_inspirehand.py g1_ih.yaml
```

If that works, run:

```bash
mjpython deploy_mujoco_Button_Press_UB_inspirehand.py g1_ih.yaml
mjpython deploy_mujoco_Open_Drawer_UB_inspirehand.py g1_ih.yaml
```

## Outputs

The metric logger writes CSV files to:

```text
Sim2Real/deploy/deploy_mujoco/metrics/
```

Keep:

- command used
- policy name
- scene name
- video/screenshot if possible
- generated CSV
- failure notes

## What To Analyze

For each task, report:

- minimum fingertip-object distance
- contact duration
- whether contact occurred
- object displacement / drawer slide / object height change
- obvious failure cases

## Do Not Claim

Do not claim retraining was completed unless a separate Training codebase is actually run.

Safe claim:

> We added contact/object-aware evaluation for released DreamControl policies and can now quantify whether visual task success corresponds to stable hand-object contact.

