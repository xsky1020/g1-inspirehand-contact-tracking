# Reward Redesign Plan

## Current Baseline Metrics (Released Policies, No Retraining)

| Task | min指尖距 | 接触 | 接触时长 | 物体进度 | 成功 |
|---|---|---|---|---|---|
| Button Press | 0.098m | yes | 0.14s | press ✓ | **press yes** |
| Open Drawer | 0.048m | yes | 2.28s | drawer 0.13m | **drawer yes** |
| Punch | 0.163m | yes | 0.59s | — | **contact yes** |
| Pick | 0.135m | no | 0 | height 0.35mm | **全失败** |

## Problem

The existing `G1Rewards` in `motion_tracking_interactive_base.py` uses sparse task rewards:

- `touch_goal` — right hand proximity (sparse, no fingertip-level signal)
- `object_above_threshold` — binary height threshold (no gradient before threshold)
- No contact detection reward at all
- No grasp stability reward

Result: policies produce coarse arm motion but lack finger-level contact awareness. Pick fails completely — hand never reaches object.

## Proposed New Reward Terms

### 1. Fingertip Proximity Reward (replaces `touch_goal`)

```python
fingertip_positions = data.site_xpos[fingertip_site_ids]  # (10, 3)
object_pos = data.xpos[object_body_id]                      # (3,)
distances = np.linalg.norm(fingertip_positions - object_pos[None, :], axis=1)
min_dist = float(np.min(distances))

r_fingertip = np.exp(-8.0 * min_dist)  # range [0, 1], max when touching
```

Why: 10 fingertips give dense gradient signal. Current `touch_goal` only considers hand center.

### 2. Contact Reward (new)

```python
r_contact = float(contact_flag) * 0.5
```

Why: No existing reward punishes missing contact. This directly incentivizes hand-object interaction.

### 3. Grasp Stability Reward (new)

```python
r_grasp_stable = min(contact_duration_s, 1.0) * 0.15
```

Why: Prevents "touch and leave". Encourages sustained grasping.

### 4. Continuous Task Progress (replaces `object_above_threshold`)

```python
# Pick: continuous lift reward
r_lift = np.clip(object_height_delta / 0.15, 0.0, 1.0) * 1.5

# Drawer: continuous slide reward
r_drawer = np.clip(abs(drawer_slide) / 0.15, 0.0, 1.0) * 1.5

# Press: continuous press depth reward
r_press = np.clip(abs(button_depth) / 0.01, 0.0, 1.0) * 1.5
```

Why: Binary threshold gives zero gradient until success. Continuous reward provides dense signal.

### 5. Motion Efficiency Penalty (new)

```python
r_wrist_path = -0.001 * wrist_displacement_per_step
```

Why: Reduces unnecessary oscillation, encourages direct trajectories.

## Total Reward

```python
reward = (+ r_task_progress * 1.5      # lift / drawer / press
          + r_fingertip * 0.3          # fingertip proximity
          + r_contact * 0.5            # contact bonus
          + r_grasp_stable * 0.15      # sustained grasp
          + r_wrist_path               # efficiency penalty
          + base_penalties)            # existing: torque, acc, action rate, etc.
```

Where `base_penalties` = `dof_torques_l2 + dof_acc_l2 + action_rate_l2 + feet_slide + feet_parallel_to_ground`.

## New Evaluation Metrics (Before vs After)

| Metric | Meaning | Before (expected) | After (target) |
|---|---|---|---|
| `contact_onset_time` | Time to first hand-object contact | >3s or never | <1.5s |
| `contact_efficiency` | object_displacement / contact_duration | ~0 | >0.03 |
| `num_fingertips_near_5cm` | Fingertips within 5cm at contact | 0-1 | 4+ |
| `post_contact_lift` | Object height change after first contact | <1cm | >5cm |
| `object_drop_flag` | Object dropped after grasp | — | 0 |
| `wrist_trajectory_length` | Total wrist path length | high | lower |
| `pre_contact_oscillation` | Hand position variance before contact | high | low |

## Implementation Checklist

1. [ ] In `motion_tracking_interactive_base.py`, add new reward methods to `G1Rewards`:
   - `compute_fingertip_proximity_reward()`
   - `compute_contact_reward()`
   - `compute_grasp_stability_reward()`
   - `compute_continuous_task_progress()`
   - `compute_motion_efficiency_penalty()`
2. [ ] Update `compute_reward()` to call new methods with stated weights
3. [ ] In `deploy_mujoco_metrics.py`, add new CSV columns:
   - `contact_onset_time`
   - `num_fingertips_near_5cm`
   - `wrist_displacement_total`
4. [ ] Retrain Pick, Button Press, Open Drawer policies
5. [ ] Run evaluation with `deploy_mujoco_metrics.py` on both old and new policies
6. [ ] Generate comparison table
