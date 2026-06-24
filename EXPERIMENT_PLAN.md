# Experiment Plan

## Research Question

Do released DreamControl policies produce stable hand-object contact, or only coarse task-level motion?

## Method

Use existing policies and MuJoCo scenes:

| Task | Script | Policy |
|---|---|---|
| Pick | `deploy_mujoco_Pick_UB_inspirehand.py` | `Pick_UB.pt` |
| Pick Top | `deploy_mujoco_Pick_Top_UB_inspirehand.py` | `Pick_Top_UB.pt` |
| Button Press | `deploy_mujoco_Button_Press_UB_inspirehand.py` | `Button_Press_UB.pt` |
| Open Drawer | `deploy_mujoco_Open_Drawer_UB_inspirehand.py` | `Open_Drawer_UB.pt` |

## Metrics

| Metric | Meaning |
|---|---|
| `min_fingertip_object_distance` | closest fingertip-to-object distance |
| `contact_flag` | whether a hand geom touches an object/drawer/button geom |
| `contact_duration_s` | cumulative hand-object contact time |
| `object_displacement` | object movement from episode start |
| `object_height_delta` | lift progress for pick-like tasks |
| `drawer_slide` | drawer joint displacement |
| `lift_success`, `drawer_success`, `contact_success` | simple thresholded success flags |

## Optional Extra Work

If baseline runs reliably:

1. Run 5-10 randomized resets per task.
2. Compare normal object placement versus perturbed placement.
3. Compare visual success with CSV contact metrics.
4. Summarize failure modes.

## Future Training Direction

If full DreamControl Training code is available later, convert the evaluation metrics into auxiliary rewards:

```text
reward += w_dist * exp(-k * fingertip_object_distance)
reward += w_contact * contact_flag
reward += w_progress * object_progress
```

This is future work, not required for the Sunday report.

