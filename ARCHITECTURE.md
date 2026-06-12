# System Architecture — Smart Driver Monitoring System

## Table of Contents

1. [High-Level Architecture](#1-high-level-architecture)
2. [Module Descriptions](#2-module-descriptions)
3. [Data Flow](#3-data-flow)
4. [Database Schema](#4-database-schema)
5. [Decision Engine Logic](#5-decision-engine-logic)
6. [Alert Escalation Flow](#6-alert-escalation-flow)
7. [Hardware Requirements](#7-hardware-requirements)
8. [Software Requirements](#8-software-requirements)
9. [Scalability Roadmap](#9-scalability-roadmap)

---

## 1. High-Level Architecture

```
                        ┌─────────────────┐
                        │   Webcam Input  │
                        └────────┬────────┘
                                 │  Raw Video Frames
                        ┌────────▼────────┐
                        │ Video Acquisition│
                        │    (OpenCV)      │
                        └────────┬────────┘
                                 │
                   ┌─────────────▼─────────────┐
                   │      Frame Processing      │
                   │  Resize · Denoise · Convert│
                   └──────┬────────────┬────────┘
                          │            │
          ┌───────────────▼──┐    ┌────▼──────────────┐
          │ Drowsiness Module│    │  Phone Detection   │
          │ MediaPipe + EAR  │    │     YOLOv8         │
          └───────────┬──────┘    └──────┬─────────────┘
                      │  State           │  State
                 ┌────▼──────────────────▼────┐
                 │       Decision Engine       │
                 │  Normal · Sleepy · Drowsy   │
                 │       · Using Phone         │
                 └──────────────┬─────────────┘
                                │
                 ┌──────────────▼──────────────┐
                 │         Alert Module         │
                 │  Audio Warning · Status HUD  │
                 └──────────────┬──────────────┘
                                │
                 ┌──────────────▼──────────────┐
                 │        Database Layer        │
                 │    SQLite via SQLAlchemy      │
                 └────────┬─────────────────────┘
                          │
          ┌───────────────┴──────────────┐
          │                              │
   ┌──────▼────────┐           ┌─────────▼──────────┐
   │    Reports    │           │  Email Notification │
   │   Dashboard   │           │    (SMTP / MIME)    │
   └───────────────┘           └────────────────────┘
```

---

## 2. Module Descriptions

### Module 1 — Video Acquisition

Captures real-time video from the connected webcam and provides a continuous frame stream to the processing pipeline.

| Property | Value |
|---|---|
| Technology | OpenCV (`cv2.VideoCapture`) |
| Output | Raw BGR video frames |
| Frame Rate | Configurable (default: 30 FPS) |

---

### Module 2 — Frame Processing

Pre-processes each incoming frame before it is passed to the detection modules.

**Operations:**

- Frame capture from buffer
- Resizing to target resolution
- BGR → RGB color space conversion (for MediaPipe)
- Optional noise reduction

| Property | Value |
|---|---|
| Technology | OpenCV |
| Input | Raw BGR frame |
| Output | Processed frame (BGR + RGB copy) |

---

### Module 3 — Face and Eye Detection

Uses MediaPipe Face Mesh to extract 468 3D facial landmarks. The 12 landmarks corresponding to both eyes are selected for EAR computation.

```
Left Eye Landmarks:  [362, 385, 387, 263, 373, 380]
Right Eye Landmarks: [33,  160, 158, 133, 153, 144]
```

| Property | Value |
|---|---|
| Technology | MediaPipe Face Mesh |
| Landmark Count | 468 (full face) |
| Eye Points Used | 6 per eye × 2 = 12 |

---

### Module 4 — Drowsiness Detection

Calculates the Eye Aspect Ratio (EAR) to determine whether the driver's eyes are open, partially closed, or fully closed over a sustained period.

**EAR Formula:**

```
       ||p2 - p6|| + ||p3 - p5||
EAR = ─────────────────────────────
            2 × ||p1 - p4||
```

Where p1–p6 are the 6 eye landmark coordinates.

**Thresholds:**

| EAR Value | State | Action |
|---|---|---|
| ≥ 0.25 (default) | Awake | No action |
| < 0.25 (1–15 frames) | Sleepy | Visual warning |
| < 0.25 (> 15 frames) | Drowsy | Audio alert + DB log + Email |

> Threshold values are configurable.

---

### Module 5 — Phone Detection

Runs YOLOv8 inference on each frame to detect whether the driver is holding or using a mobile phone.

**Pipeline:**

```
Frame → YOLOv8 Inference → Detected Bounding Boxes
                                    │
                          Filter class: 'cell phone'
                                    │
                          Confidence > threshold?
                                    │
                          Yes → PHONE DETECTED → Alert
```

| Property | Value |
|---|---|
| Model | YOLOv8n (nano, optimized for speed) |
| Detection Class | `cell phone` (COCO class 67) |
| Confidence Threshold | 0.5 (configurable) |
| Technology | Ultralytics YOLOv8 |

---

### Module 6 — Decision Engine

Aggregates the outputs of the drowsiness and phone detection modules and determines the overall driver state for the current frame.

**State Table:**

| Drowsiness State | Phone Detected | Final State | Alert |
|---|---|---|---|
| Awake | No | `NORMAL` | None |
| Sleepy | No | `SLEEPY` | Visual |
| Drowsy | No | `DROWSY` | Audio + Email |
| Any | Yes | `USING PHONE` | Audio + Email |

---

### Module 7 — Alert Module

Provides immediate, real-time feedback to the driver upon detecting unsafe behavior.

| Alert Type | Trigger | Technology |
|---|---|---|
| Audio warning | Drowsy / Phone | Pygame mixer |
| Visual HUD overlay | All unsafe states | OpenCV draw |
| Status display | All states | Flask frontend |

---

### Module 8 — Database Module

Stores all driver, session, and event data using SQLite with SQLAlchemy ORM.

**Schema:**

```
┌──────────────────┐     ┌───────────────────────┐     ┌──────────────────────┐
│      Driver       │     │        Session         │     │        Event          │
├──────────────────┤     ├───────────────────────┤     ├──────────────────────┤
│ driver_id (PK)   │────►│ session_id (PK)        │────►│ event_id (PK)         │
│ name             │     │ driver_id (FK)          │     │ session_id (FK)       │
│ age              │     │ start_time              │     │ event_type            │
│ vehicle_number   │     │ end_time                │     │ timestamp             │
└──────────────────┘     │ drowsy_event_count      │     └──────────────────────┘
                         │ phone_event_count        │
                         └───────────────────────┘
```

| Property | Value |
|---|---|
| Database | SQLite |
| ORM | SQLAlchemy |
| Tables | Driver, Session, Event |

---

### Module 9 — Reporting Module

Reads aggregated session and event data from the database and presents visual analytics on the Flask dashboard.

**Features:**

- Session history timeline
- Event frequency charts (drowsy vs phone)
- Per-driver behavioral analysis
- Exportable graphical reports

---

### Module 10 — Email Notification Module

Sends automated email alerts to pre-registered emergency contacts when unsafe driving behavior is detected.

| Property | Value |
|---|---|
| Protocol | SMTP |
| Library | Python `smtplib` + `email.mime` |
| Trigger | Drowsy state OR Phone detected |
| Content | Driver info, event type, timestamp |

---

## 3. Data Flow

```
Step 1   Webcam captures driver video stream
           │
Step 2   OpenCV reads and pre-processes each frame
           │
Step 3   Processed frame → MediaPipe Face Mesh
           │
Step 4   68 facial landmarks extracted → 12 eye landmarks selected
           │
Step 5   EAR calculated per frame → compared against threshold
           │
Step 6   Same frame → YOLOv8 inference → phone class detection
           │
Step 7   Decision Engine evaluates both outputs → assigns driver state
           │
Step 8   Alert Module triggers audio/visual feedback if unsafe
           │
Step 9   Event logged to SQLite (type, timestamp, session ID)
           │
Step 10  Reports dashboard updated with latest session data
           │
Step 11  Email notification dispatched to emergency contact (if configured)
```

---

## 4. Database Schema

### Table: Driver

| Column | Type | Description |
|---|---|---|
| `driver_id` | INTEGER (PK) | Auto-incremented unique driver identifier |
| `name` | TEXT | Driver full name |
| `age` | INTEGER | Driver age |
| `vehicle_number` | TEXT | Vehicle registration number |

### Table: Session

| Column | Type | Description |
|---|---|---|
| `session_id` | INTEGER (PK) | Auto-incremented session identifier |
| `driver_id` | INTEGER (FK) | Reference to Driver |
| `start_time` | DATETIME | Session start timestamp |
| `end_time` | DATETIME | Session end timestamp |
| `drowsy_event_count` | INTEGER | Total drowsiness events in session |
| `phone_event_count` | INTEGER | Total phone usage events in session |

### Table: Event

| Column | Type | Description |
|---|---|---|
| `event_id` | INTEGER (PK) | Auto-incremented event identifier |
| `session_id` | INTEGER (FK) | Reference to Session |
| `event_type` | TEXT | `DROWSY` or `PHONE_DETECTED` |
| `timestamp` | DATETIME | Exact event timestamp |

---

## 5. Decision Engine Logic

```python
# Pseudocode

def get_driver_state(ear, ear_threshold, ear_counter, ear_limit, phone_detected):

    if phone_detected:
        return "USING PHONE"

    if ear < ear_threshold:
        ear_counter += 1
        if ear_counter >= ear_limit:
            return "DROWSY"      # Sustained closure
        else:
            return "SLEEPY"     # Brief closure
    else:
        ear_counter = 0
        return "NORMAL"
```

---

## 6. Alert Escalation Flow

```
Driver State
     │
     ├─── NORMAL      ──────────────────────► No action
     │
     ├─── SLEEPY      ──────────────────────► Visual overlay (yellow)
     │
     ├─── DROWSY      ──── Audio alert
     │                ──── Visual overlay (red)
     │                ──── Log event to DB
     │                ──── Send email notification
     │
     └─── USING PHONE ──── Audio alert
                      ──── Visual overlay (red)
                      ──── Log event to DB
                      ──── Send email notification
```

---

## 7. Hardware Requirements

| Component | Minimum | Recommended |
|---|---|---|
| Processor | Intel Core i3 | Intel Core i5/i7 |
| RAM | 4 GB | 8 GB+ |
| GPU | — | NVIDIA (CUDA for YOLOv8) |
| Camera | Standard Webcam | HD Webcam 720p+ |
| Storage | 500 MB | SSD |

> **Note:** YOLOv8 inference runs on CPU by default. NVIDIA GPU with CUDA significantly improves real-time performance.

---

## 8. Software Requirements

| Package | Purpose |
|---|---|
| Python 3.10+ | Runtime |
| Flask | Web framework + dashboard |
| OpenCV (`cv2`) | Video capture + frame processing |
| MediaPipe | Face Mesh + landmark extraction |
| Ultralytics YOLOv8 | Phone object detection |
| SQLAlchemy | ORM for SQLite |
| Pygame | Audio alert playback |
| smtplib | Email notification |
| HTML/CSS/Bootstrap | Frontend UI |

---

## 9. Scalability Roadmap

| Enhancement | Description | Status |
|---|---|---|
| Cloud deployment | Move database and API to cloud (AWS/GCP) | Planned |
| Multi-camera monitoring | Support for multiple simultaneous webcam streams | Planned |
| Driver recognition | Face recognition to auto-identify drivers | Planned |
| Mobile application | Flutter/React Native companion app | Planned |
| IoT vehicle integration | CAN bus interface for in-vehicle alerts | Planned |
| Edge AI deployment | Optimized models for Jetson Nano / Raspberry Pi | Planned |
| Night vision support | IR camera support for low-light environments | Planned |
| GPS tracking | Location logging at event time | Planned |

---

*Architecture documented by Abdul Haris H — M.Tech CSE, Government Engineering College Thrissur*