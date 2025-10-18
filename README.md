# 🧠 Face Tracking Semi-Immersive VR
**A20586593 — Seonghwan Lim (IIT CS539 Project)**  

> Realtime head-pose tracking using only a webcam and Unity — no headset, no markers, no extra sensors.

---

## 🎯 Project Overview
This project turns an **ordinary webcam** into a **head-pose controller** for Unity scenes.  
It enables a semi-immersive VR “window” experience — letting the user look around a 3D world naturally by moving their head.  

Key idea:
- Detect **facial landmarks** in realtime using *MediaPipe Face Landmarker*  
- Predict **Euler angles (Roll, Pitch, Yaw)** via a Transformer model trained on the *BIWI Kinect Head Pose Database*  
- Smooth signals using the *One-Euro Filter*  
- Send the smoothed angles to Unity via UDP to rotate the main camera in real time.

---

## ⚙️ System Overview

| Stage | Component | Description |
|--------|------------|-------------|
| **Capture** | Webcam | 720p @ 30 FPS |
| **Landmark Extraction** | MediaPipe Face Mesh | 478 3D facial landmarks per frame |
| **Angle Estimation** | Transformer (3-layer encoder) | 4 heads, 64-d embeddings, CPU-realtime |
| **Signal Smoothing** | One-Euro Filter | Adaptive low-pass to remove jitter |
| **Transport** | UDP | Sends `"rollZ,pitchX,yawY"` |
| **Rendering** | Unity C# | Rotates Main Camera; ±30° triggers soft auto-spin |

---

## 🧠 Face Landmark Detection (MediaPipe Face Landmarker)

This project uses **Google MediaPipe’s Face Landmarker Task** to extract  
**478 3D facial landmarks** in real time from a live webcam feed.

### 🔍 Summary

| Item | Details |
|------|----------|
| **Input Types** | Still images / Video frames / Live stream |
| **Outputs** | Face bounding boxes, 478 3D landmarks, optional 52 blendshape scores + facial transformation matrix |
| **Models** | BlazeFace (Detection) → Face Mesh V2 (Landmarks) → Blendshape Predictor |
| **Python Config** | `num_faces=1`, `refine_landmarks=True`, `min_face_detection_confidence=0.5`, `min_tracking_confidence=0.5` |
| **Mode Used** | `LIVE_STREAM` |
| **Performance** | ≈ 30 FPS (720p webcam) |

```python
import mediapipe as mp
mp_face_mesh = mp.solutions.face_mesh.FaceMesh(
    static_image_mode=False,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)
