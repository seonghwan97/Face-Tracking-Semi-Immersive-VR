import os
import socket
import time

import cv2
import numpy as np
import mediapipe as mp
import torch

# ── internal modules ───────────────────────────────────────────
from transformer import (
    SingleFramePositionalTransformer,
    MODEL_N_LANDMARKS,
    BEST_MODEL_PATH,
)
from help import box_normalize_xy, draw_axes
from filters import OneEuro

# ── runtime options ────────────────────────────────────────────
ANGLE_SCALE = 1.0            # final scale after smoothing
UDP_IP      = "127.0.0.1"    # receiver IP
UDP_PORT    = 9999           # receiver port

# ── device & model ─────────────────────────────────────────────
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

model = SingleFramePositionalTransformer().to(DEVICE)
if not os.path.isfile(BEST_MODEL_PATH):
    raise FileNotFoundError(f"[unity.py] model not found: {BEST_MODEL_PATH}")
model.load_state_dict(torch.load(BEST_MODEL_PATH, map_location=DEVICE))
model.eval()

# ── MediaPipe face mesh ───────────────────────────────────────
mp_face_mesh = mp.solutions.face_mesh.FaceMesh(
    static_image_mode=False,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
)

# ── webcam & UDP sockets ──────────────────────────────────────
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise RuntimeError("[unity.py] Webcam not available")

fps_cam = cap.get(cv2.CAP_PROP_FPS) or 30.0      # estimate FPS
sock    = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
remote  = (UDP_IP, UDP_PORT)

# ── One-Euro filters (roll / yaw / pitch) ─────────────────────
f_roll  = OneEuro(freq=fps_cam, min_cut=1.0, beta=0.005)
f_yaw   = OneEuro(freq=fps_cam, min_cut=1.0, beta=0.005)
f_pitch = OneEuro(freq=fps_cam, min_cut=1.0, beta=0.005)

cv2.namedWindow("Realtime Pose", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Realtime Pose", 1280, 720)

print("[unity.py] running …  (ESC to exit)")
try:
    t_prev = time.time()
    while True:
        ok, frame = cap.read()
        if not ok:
            print("[unity.py] frame grab failed")
            break

        frame = cv2.flip(frame, 1)
        H, W, _ = frame.shape

        # ── face landmarks ─────────────────────────────────────
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = mp_face_mesh.process(rgb)

        if res.multi_face_landmarks:
            lm = res.multi_face_landmarks[0].landmark
            if len(lm) == MODEL_N_LANDMARKS:
                pts = np.array(
                    [[p.x * W, p.y * H, p.z] for p in lm], np.float32
                )
                pts_norm = box_normalize_xy(pts)
                if not np.isnan(pts_norm).any():
                    mask = np.isnan(pts_norm[:, :2]).any(1)
                    x_in = torch.from_numpy(
                        np.nan_to_num(pts_norm[:, :2])
                    ).unsqueeze(0).to(DEVICE)
                    m_in = torch.from_numpy(mask).unsqueeze(0).to(DEVICE)

                    # ── inference ───────────────────────────────
                    with torch.no_grad():
                        roll_z, yaw_y, pitch_x = model(
                            x_in, m_in
                        ).cpu().numpy()[0]

                    # ── smoothing & scaling ─────────────────────
                    roll_z  = ANGLE_SCALE * f_roll( roll_z  )
                    yaw_y   = ANGLE_SCALE * f_yaw ( yaw_y   )
                    pitch_x = ANGLE_SCALE * f_pitch(pitch_x )

                    # ── visualization ──────────────────────────
                    cx, cy = int(pts[4, 0]), int(pts[4, 1])
                    draw_axes(frame, cx, cy, roll_z, yaw_y, pitch_x)

                    for i, txt in enumerate(
                        (f"Roll  : {roll_z:.2f}",
                         f"Yaw   : {yaw_y:.2f}",
                         f"Pitch : {pitch_x:.2f}"),
                        start=2,
                    ):
                        cv2.putText(
                            frame, txt, (30, 30 * i),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2
                        )

                    # ── UDP send to Unity ───────────────────────
                    sock.sendto(
                        f"{roll_z:.2f},{pitch_x:.2f},{yaw_y:.2f}".encode(),
                        remote,
                    )

        # FPS overlay
        t_now = time.time()
        fps_disp = 1.0 / (t_now - t_prev + 1e-8)
        t_prev = t_now
        cv2.putText(
            frame, f"FPS: {fps_disp:4.1f}", (10, H - 20),
            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2
        )

        cv2.putText(
            frame, "Press ESC to exit", (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2
        )
        cv2.imshow("Realtime Pose", frame)
        if cv2.waitKey(1) & 0xFF == 27:      # ESC key
            break

except KeyboardInterrupt:
    print("\n[unity.py] interrupted by user")

finally:
    print("[unity.py] cleaning up …")
    cap.release()
    cv2.destroyAllWindows()
    mp_face_mesh.close()
    sock.close()