import csv
import os
import time
from dataclasses import dataclass

import mujoco
import numpy as np


FINGERTIP_SITE_NAMES = (
    "left_thumb_tip",
    "left_index_tip",
    "left_middle_tip",
    "left_ring_tip",
    "left_pinky_tip",
    "right_thumb_tip",
    "right_index_tip",
    "right_middle_tip",
    "right_ring_tip",
    "right_pinky_tip",
)

HAND_BODY_KEYWORDS = ("wrist", "inspire_hand", "thumb", "index", "middle", "ring", "pinky")
OBJECT_BODY_NAMES = ("object", "drawer_visual", "platform")
OBJECT_BODY_KEYWORDS = ("object", "drawer", "button", "handle")


@dataclass
class InteractionMetrics:
    task_name: str
    output_dir: str = "metrics"
    log_every_steps: int = 20


class InteractionMetricLogger:
    """Evaluation-only contact/object metrics for MuJoCo DreamControl rollouts."""

    def __init__(self, model, data, cfg: InteractionMetrics):
        self.model = model
        self.data = data
        self.cfg = cfg
        self.step_count = 0
        self.episode_index = 0
        self.contact_duration = 0.0
        self.max_object_displacement = 0.0
        self.max_object_height_delta = 0.0
        self.max_drawer_slide_abs = 0.0

        self.fingertip_site_ids = self._find_sites(FINGERTIP_SITE_NAMES)
        self.object_body_id = self._find_first_body(OBJECT_BODY_NAMES)
        self.drawer_joint_id = self._find_joint("object_slide_x")
        self.hand_geom_ids = self._collect_hand_geom_ids()
        self.object_geom_ids = self._collect_object_geom_ids()

        os.makedirs(cfg.output_dir, exist_ok=True)
        stamp = time.strftime("%Y%m%d_%H%M%S")
        safe_task = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in cfg.task_name)
        self.csv_path = os.path.join(cfg.output_dir, f"{safe_task}_{stamp}.csv")
        self.csv_file = open(self.csv_path, "w", newline="", encoding="utf-8")
        self.writer = csv.DictWriter(
            self.csv_file,
            fieldnames=[
                "episode",
                "time_s",
                "min_fingertip_object_distance",
                "mean_fingertip_object_distance",
                "contact_flag",
                "contact_duration_s",
                "object_displacement",
                "object_height_delta",
                "drawer_slide",
                "max_object_displacement",
                "max_object_height_delta",
                "max_drawer_slide_abs",
                "lift_success",
                "drawer_success",
                "contact_success",
            ],
        )
        self.writer.writeheader()
        self.reset_episode()
        print(f"[metrics] logging interaction metrics to {self.csv_path}")
        print(
            "[metrics] fingertips=%d hand_geoms=%d object_geoms=%d object_body=%s drawer_joint=%s"
            % (
                len(self.fingertip_site_ids),
                len(self.hand_geom_ids),
                len(self.object_geom_ids),
                self._name(mujoco.mjtObj.mjOBJ_BODY, self.object_body_id),
                self._name(mujoco.mjtObj.mjOBJ_JOINT, self.drawer_joint_id),
            )
        )

    def close(self):
        self.csv_file.flush()
        self.csv_file.close()

    def reset_episode(self):
        mujoco.mj_forward(self.model, self.data)
        self.episode_index += 1
        self.contact_duration = 0.0
        self.max_object_displacement = 0.0
        self.max_object_height_delta = 0.0
        self.max_drawer_slide_abs = 0.0
        self.initial_object_pos = self._object_pos()
        self.initial_drawer_slide = self._drawer_slide()

    def update(self, time_s: float, dt: float):
        self.step_count += 1
        contact_flag = self._contact_flag()
        if contact_flag:
            self.contact_duration += dt

        object_pos = self._object_pos()
        object_displacement = float(np.linalg.norm(object_pos - self.initial_object_pos)) if object_pos is not None else np.nan
        object_height_delta = float(object_pos[2] - self.initial_object_pos[2]) if object_pos is not None else np.nan
        drawer_slide = self._drawer_slide()
        drawer_slide_delta = drawer_slide - self.initial_drawer_slide if drawer_slide is not None else np.nan

        if not np.isnan(object_displacement):
            self.max_object_displacement = max(self.max_object_displacement, object_displacement)
        if not np.isnan(object_height_delta):
            self.max_object_height_delta = max(self.max_object_height_delta, object_height_delta)
        if not np.isnan(drawer_slide_delta):
            self.max_drawer_slide_abs = max(self.max_drawer_slide_abs, abs(float(drawer_slide_delta)))

        if self.step_count % self.cfg.log_every_steps != 0:
            return

        min_dist, mean_dist = self._fingertip_object_distances(object_pos)
        self.writer.writerow(
            {
                "episode": self.episode_index,
                "time_s": f"{time_s:.4f}",
                "min_fingertip_object_distance": self._fmt(min_dist),
                "mean_fingertip_object_distance": self._fmt(mean_dist),
                "contact_flag": int(contact_flag),
                "contact_duration_s": f"{self.contact_duration:.4f}",
                "object_displacement": self._fmt(object_displacement),
                "object_height_delta": self._fmt(object_height_delta),
                "drawer_slide": self._fmt(drawer_slide_delta),
                "max_object_displacement": f"{self.max_object_displacement:.6f}",
                "max_object_height_delta": f"{self.max_object_height_delta:.6f}",
                "max_drawer_slide_abs": f"{self.max_drawer_slide_abs:.6f}",
                "lift_success": int(self.max_object_height_delta > 0.05),
                "drawer_success": int(self.max_drawer_slide_abs > 0.03),
                "contact_success": int(self.contact_duration > 0.10),
            }
        )
        self.csv_file.flush()

    def _find_sites(self, names):
        ids = []
        for name in names:
            idx = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_SITE, name)
            if idx >= 0:
                ids.append(idx)
        return ids

    def _find_first_body(self, names):
        for name in names:
            idx = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, name)
            if idx >= 0:
                return idx
        return -1

    def _find_joint(self, name):
        return mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, name)

    def _name(self, obj_type, idx):
        if idx is None or idx < 0:
            return "none"
        name = mujoco.mj_id2name(self.model, obj_type, idx)
        return name if name is not None else f"id:{idx}"

    def _body_name_for_geom(self, geom_id):
        body_id = int(self.model.geom_bodyid[geom_id])
        return self._name(mujoco.mjtObj.mjOBJ_BODY, body_id)

    def _is_descendant_body(self, body_id, ancestor_id):
        if ancestor_id < 0:
            return False
        current = body_id
        while current >= 0:
            if current == ancestor_id:
                return True
            if current == 0:
                return False
            current = int(self.model.body_parentid[current])
        return False

    def _collect_hand_geom_ids(self):
        ids = set()
        for geom_id in range(self.model.ngeom):
            body_name = self._body_name_for_geom(geom_id)
            if body_name and any(key in body_name for key in HAND_BODY_KEYWORDS):
                ids.add(geom_id)
        return ids

    def _collect_object_geom_ids(self):
        ids = set()
        for geom_id in range(self.model.ngeom):
            body_id = int(self.model.geom_bodyid[geom_id])
            geom_name = self._name(mujoco.mjtObj.mjOBJ_GEOM, geom_id)
            body_name = self._name(mujoco.mjtObj.mjOBJ_BODY, body_id)
            if self._is_descendant_body(body_id, self.object_body_id):
                ids.add(geom_id)
            elif any(key in (geom_name or "") for key in OBJECT_BODY_KEYWORDS):
                ids.add(geom_id)
            elif any(key in (body_name or "") for key in OBJECT_BODY_KEYWORDS):
                ids.add(geom_id)
        return ids

    def _object_pos(self):
        if self.object_body_id < 0:
            return None
        return self.data.xpos[self.object_body_id].copy()

    def _drawer_slide(self):
        if self.drawer_joint_id < 0:
            return None
        return float(self.data.qpos[self.model.jnt_qposadr[self.drawer_joint_id]])

    def _fingertip_object_distances(self, object_pos):
        if object_pos is None or not self.fingertip_site_ids:
            return np.nan, np.nan
        tip_positions = self.data.site_xpos[self.fingertip_site_ids]
        distances = np.linalg.norm(tip_positions - object_pos[None, :], axis=1)
        return float(np.min(distances)), float(np.mean(distances))

    def _contact_flag(self):
        if not self.hand_geom_ids or not self.object_geom_ids:
            return False
        for i in range(self.data.ncon):
            contact = self.data.contact[i]
            geom1 = int(contact.geom1)
            geom2 = int(contact.geom2)
            if (geom1 in self.hand_geom_ids and geom2 in self.object_geom_ids) or (
                geom2 in self.hand_geom_ids and geom1 in self.object_geom_ids
            ):
                return True
        return False

    @staticmethod
    def _fmt(value):
        if value is None or np.isnan(value):
            return "nan"
        return f"{float(value):.6f}"
