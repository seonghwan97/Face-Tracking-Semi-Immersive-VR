import math
import numpy as np
import cv2

AXIS_LENGTH = 50.0  # length of each axis (pixels)

def box_normalize_xy(pts: np.ndarray) -> np.ndarray:
    """
    Normalize (x, y) landmarks to [0, 1] using their bounding box.
    Returns NaNs if box has zero width or height.
    """
    has_z = pts.shape[1] == 3
    x_min, x_max = pts[:, 0].min(), pts[:, 0].max()
    y_min, y_max = pts[:, 1].min(), pts[:, 1].max()
    w, h = x_max - x_min, y_max - y_min
    if w == 0 or h == 0:
        return np.full_like(pts, np.nan)
    out = pts.copy()
    out[:, 0] = (pts[:, 0] - x_min) / w
    out[:, 1] = (pts[:, 1] - y_min) / h
    if has_z:
        out[:, 2] = pts[:, 2]
    return out

def rotmat_zyx(z_deg, y_deg, x_deg):
    """Convert Z-Y-X Euler angles (deg) to a rotation matrix."""
    z, y, x = map(math.radians, (z_deg, y_deg, x_deg))
    Rz = np.array([[ math.cos(z),  math.sin(z), 0],
                   [-math.sin(z),  math.cos(z), 0],
                   [          0,            0, 1]], np.float32)
    Ry = np.array([[ math.cos(y),  0, -math.sin(y)],
                   [          0,  1,           0],
                   [ math.sin(y),  0,  math.cos(y)]], np.float32)
    Rx = np.array([[1,           0,            0],
                   [0, math.cos(x), -math.sin(x)],
                   [0, math.sin(x),  math.cos(x)]], np.float32)
    return Rz @ Ry @ Rx

def draw_axes(frame, cx, cy,
              z_deg, y_deg, x_deg,
              length: float = AXIS_LENGTH):
    """
    Draw 3D axes on a BGR frame at pixel (cx, cy) using Euler angles.
    """
    R     = rotmat_zyx(z_deg, y_deg, x_deg)
    axes  = np.eye(3, dtype=np.float32)
    colors = [(0, 0, 255),   # X axis (red)
              (0, 255, 0),   # Y axis (green)
              (255, 0, 0)]   # Z axis (blue)
    for vec, col in zip(axes, colors):
        end = (int(cx + length * (R @ vec)[0]),
               int(cy - length * (R @ vec)[1]))
        cv2.line(frame, (cx, cy), end, col, 3)
