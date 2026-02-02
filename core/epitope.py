from __future__ import annotations
from typing import Any
import numpy as np

def points_repr_from_points(points: np.ndarray, labels: list[str], *, label_prefix: str) -> dict[str, Any]:
    if points is None or len(points) == 0:
        return {
            f"{label_prefix}_size": 0,
            f"{label_prefix}_labels": "",
            f"{label_prefix}_centroid_x": np.nan,
            f"{label_prefix}_centroid_y": np.nan,
            f"{label_prefix}_centroid_z": np.nan,
            f"{label_prefix}_rg": np.nan,
        }

    P = np.asarray(points, dtype=float)
    if P.ndim != 2 or P.shape[1] != 3:
        raise ValueError("points must be (N,3)")

    C = P.mean(axis=0)
    rg = float(np.sqrt(np.mean(np.sum((P - C) ** 2, axis=1))))

    return {
        f"{label_prefix}_size": int(P.shape[0]),
        f"{label_prefix}_labels": ";".join(labels),
        f"{label_prefix}_centroid_x": float(C[0]),
        f"{label_prefix}_centroid_y": float(C[1]),
        f"{label_prefix}_centroid_z": float(C[2]),
        f"{label_prefix}_rg": rg,
    }
