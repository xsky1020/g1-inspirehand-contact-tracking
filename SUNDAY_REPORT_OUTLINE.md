# Sunday Report Outline

## Title

Contact/Object-Aware Evaluation of DreamControl Policies with G1+InspireHand

## Main Message

DreamControl already includes task-level interaction rewards, but the released deployment does not directly quantify finger-level hand-object contact. We add metrics to evaluate contact quality of existing policies before attempting retraining.

## Slides

### 1. Background

- DreamControl: whole-body humanoid scene interaction.
- Existing policy can run Pick, Button Press, Open Drawer.
- Question: does task demonstration imply stable hand-object contact?

### 2. Existing Reward Understanding

- Stability rewards: alive, termination, torque, action rate, foot slide.
- Motion rewards: pose, orientation, joint/keypoint tracking.
- Task rewards: hand/object approach, goal approach, object height threshold.

### 3. Gap

- Task-level rewards do not directly report fine contact quality.
- Released deployment uses task-specific hand schedules/postures in some scripts.
- Need measurable contact/object interaction metrics.

### 4. Implementation

- Added `deploy_mujoco_metrics.py`.
- Integrated it into InspireHand MuJoCo common runner.
- Replaced Button Press InspireHand script with common runner path.

### 5. Metrics

- fingertip-object distance
- contact flag
- contact duration
- object displacement
- lift height
- drawer slide
- thresholded success flags

### 6. Next Step

- Run released policies.
- Export CSV and videos.
- Analyze whether visual success matches contact metrics.
- Future: convert metrics to auxiliary reward if full Training code is available.

