# Face Tracking Semi-Immersive VR  
**Seonghwan Lim, Illinois Institute of Technology**  

---

### Abstract

This project transforms a **standard webcam** into a **real-time head-pose controller** for Unity,  
enabling a *semi-immersive VR* experience without requiring head-mounted displays (HMDs), sensors, or markers.  

Using **MediaPipe Face Landmarker**, the system extracts **478 facial landmarks** from live video frames and estimates  
**Euler angles (Roll, Pitch, Yaw)** through a lightweight **Transformer-based regression model** trained on the  
**BIWI Kinect Head Pose Database**.  

To ensure smooth and natural motion, the predicted angles are stabilized using the **One-Euro Filter**  
and transmitted via **UDP** to a Unity scene, where a C# script maps them to camera rotations in real time.  

This low-cost and portable setup demonstrates that **marker-free, webcam-only head tracking**  
can approximate the responsiveness of professional VR hardware with less than **10 ms latency**,  
making it suitable for rapid VR/AR prototyping, educational visualization, and interactive installations.  

> **Keywords:** Head Pose Estimation · MediaPipe Face Landmarker · Transformer Regression ·  
> One-Euro Filter · Realtime Unity Integration · BIWI Kinect Dataset

---

## Project Overview

Most virtual-reality (VR) systems require **head-mounted displays (HMDs)** or specialized sensors,  
making them expensive and impractical for small labs, classrooms, or hobby projects.  
This work demonstrates that a **single, off-the-shelf webcam** is sufficient to deliver  
a *semi-immersive VR experience* — allowing users to look around a 3D world  
simply by turning their head.

The system continuously detects **3D facial landmarks** from live webcam video using  
**MediaPipe Face Landmarker**, predicts the head’s **Euler angles (Roll, Pitch, Yaw)**  
through a lightweight **Transformer network**, and transmits the results to **Unity** in real time.  
Unity’s camera then rotates according to the user’s head motion, creating the feeling  
of peering through a virtual window into another world.

This architecture achieves smooth, low-latency head-pose control (≈10 ms)  
without dedicated hardware — ideal for rapid **VR/AR prototyping**,  
**virtual classrooms**, and **interactive exhibitions**.

---

### System Concept Diagram

<p align="center">
  <img src="figures/overview_concept.png" alt="System Concept Diagram" width="750"/>
  <br>
  <em>Figure 1. Overview of the semi-immersive face-tracking VR system using only a webcam.</em>
</p>

**Workflow Summary**

1. **Webcam Capture** → Live 720p video feed  
2. **MediaPipe Face Mesh** → Extracts 478 facial keypoints  
3. **Transformer Model** → Regresses Euler angles *(Roll, Pitch, Yaw)*  
4. **One-Euro Filter** → Smooths temporal jitter  
5. **UDP Transmission** → Sends three floats to Unity  
6. **Unity C# Receiver** → Rotates Main Camera accordingly  

---

### Why It Matters
- **Low-cost & portable:** Runs on any laptop webcam  
- **Marker-free:** No fiducial markers or external sensors required  
- **Realtime:** < 10 ms total latency with CPU-only inference  
- **Expandable:** Easily integrated with facial animation or avatar control  

---

## System Overview

The full system integrates **Python (MediaPipe + Transformer)** for head-pose estimation  
and **Unity (C#)** for visualization, connected through **UDP streaming**.  
The table below summarizes each functional stage of the pipeline.

| Stage | Component | Description |
|--------|------------|-------------|
| **1. Capture** | Webcam | Captures 720p/30 FPS RGB frames. |
| **2. Face Landmark Extraction** | MediaPipe Face Mesh | Detects 478 3D facial landmarks in each frame. |
| **3. Angle Estimation** | Transformer Model | Predicts Euler angles *(Roll, Pitch, Yaw)* from normalized landmark coordinates. |
| **4. Temporal Filtering** | One-Euro Filter | Removes high-frequency jitter while preserving responsiveness. |
| **5. Communication** | UDP Socket | Streams three floats — `rollZ,pitchX,yawY` — to Unity in real time. |
| **6. Rendering** | Unity (C# Script) | Rotates the Main Camera according to received angles; applies soft auto-spin beyond ±30°. |

---

### End-to-End Data Flow

```mermaid
flowchart LR
    A["Webcam Capture\n(OpenCV)"] --> B["MediaPipe FaceMesh\n478 Landmarks"]
    B --> C["Box Normalize\n(x,y) Coordinates"]
    C --> D["Transformer Model\nPredict Roll / Pitch / Yaw"]
    D --> E["One-Euro Filter\nSmooth Angles"]
    E --> F["UDP Transmission\n127.0.0.1:9999"]
    F --> G["Unity Receiver (C#)\nCamera Rotation"]


