<div align="center">

<h1>🚗 Smart Driver Monitoring System</h1>

<p><strong>Real-time computer vision pipeline for driver drowsiness and phone usage detection</strong></p>

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-Web%20Framework-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![OpenCV](https://img.shields.io/badge/OpenCV-Computer%20Vision-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)](https://opencv.org)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-Object%20Detection-00FFFF?style=for-the-badge&logo=ultralytics&logoColor=black)](https://ultralytics.com)
[![MediaPipe](https://img.shields.io/badge/MediaPipe-Face%20Mesh-0097A7?style=for-the-badge&logo=google&logoColor=white)](https://mediapipe.dev)
[![SQLite](https://img.shields.io/badge/SQLite-Database-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org)
[![License](https://img.shields.io/badge/License-Academic-green?style=for-the-badge)](LICENSE)

<br/>

> Road accidents due to driver fatigue and phone distraction are among the leading causes of death globally. This system uses real-time computer vision to keep drivers alert — before it's too late.

</div>

---

## 📌 Overview

The **Smart Driver Monitoring System** is a real-time safety application that continuously monitors a driver through a webcam, detects drowsiness and mobile phone usage using state-of-the-art computer vision models, and immediately triggers audio/visual alerts. All events are logged to a database, and a Flask web dashboard provides session history, behavioral analytics, and automated email notifications to emergency contacts.

Built as an M.Tech capstone project at **Government Engineering College Thrissur**, this system demonstrates the integration of:
- **Facial landmark analysis** (MediaPipe Face Mesh + Eye Aspect Ratio)
- **Deep learning object detection** (YOLOv8)
- **Full-stack web application** (Flask + SQLite + Bootstrap)

---

## 🎯 Key Features

| Feature | Description |
|---|---|
| 👁️ **Drowsiness Detection** | Calculates Eye Aspect Ratio (EAR) in real-time; detects prolonged eye closure indicating fatigue |
| 📱 **Phone Usage Detection** | YOLOv8-powered object detection flags mobile phone usage while driving |
| 🔊 **Instant Audio Alerts** | Pygame-driven audio warnings trigger immediately on unsafe behavior |
| 📊 **Web Dashboard** | Flask-powered UI for session monitoring, event logs, and driver profiles |
| 🗄️ **Persistent Event Logging** | All events stored in SQLite via SQLAlchemy ORM |
| 📈 **Graphical Reports** | Visual analytics of driver behavior across sessions |
| 📧 **Email Notifications** | SMTP-based alerts sent to emergency contacts upon detection |
| 👤 **Driver Management** | Register and manage multiple driver profiles |

---

## 🏗️ System Architecture

```
                        ┌─────────────────┐
                        │   Webcam Input  │
                        └────────┬────────┘
                                 │
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
          │                  │    │                    │
          │  EAR Threshold   │    │  Bounding Box +    │
          │  Comparison      │    │  Confidence Score  │
          └───────────┬──────┘    └──────┬─────────────┘
                      │                  │
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

### Driver State Machine

```
         ┌──────────┐
    ─────►  NORMAL  ◄─────────────────────────┐
         └────┬─────┘                          │
              │ EAR drops below threshold      │ Eyes re-open
         ┌────▼─────┐                          │
         │  SLEEPY  ├──────────────────────────┘
         └────┬─────┘
              │ Sustained closure (> N frames)
         ┌────▼──────┐
         │  DROWSY   │──► 🔊 Audio Alert + 📧 Email
         └───────────┘

         ┌────────────────┐
    ─────► PHONE DETECTED │──► 🔊 Audio Alert + 📧 Email
         └────────────────┘
```

---

## 🔬 How It Works

### Eye Aspect Ratio (EAR) — Drowsiness Detection

The EAR is calculated from 6 facial landmarks per eye using MediaPipe Face Mesh:

```
       p2   p3
        \   /
    p1───────p4
        /   \
       p6   p5

       ||p2-p6|| + ||p3-p5||
EAR = ─────────────────────────
          2 × ||p1-p4||
```

- **EAR ≥ threshold** → Eyes open → `NORMAL`
- **EAR < threshold** (brief) → `SLEEPY`
- **EAR < threshold** (sustained, N frames) → `DROWSY` → Alert triggered

### YOLOv8 — Phone Detection

- Each frame is passed through a YOLOv8 model
- Bounding boxes are evaluated for the `cell phone` class
- Confidence score above threshold → `PHONE DETECTED` → Alert triggered

---

## 🗂️ Project Structure

```
Smart-Driver-Monitoring-System/
│
├── app.py                  # Flask application entrypoint
├── detector.py             # Core CV pipeline (EAR + YOLOv8)
├── models.py               # SQLAlchemy ORM models
├── database.db             # SQLite database
│
├── static/
│   ├── style.css           # Custom frontend styles
│   ├── alert.wav           # Audio alert file
│   └── reports/            # Generated report charts
│
├── templates/
│   ├── base.html           # Base layout template
│   ├── index.html          # Home / monitoring page
│   ├── add_driver.html     # Driver registration form
│   ├── drivers.html        # Driver list
│   ├── dashboard.html      # Session dashboard
│   └── reports.html        # Analytics and reports
│
├── screenshots/            # Demo screenshots
├── requirements.txt        # Python dependencies
├── README.md
└── ARCHITECTURE.md
```

---

## 🗄️ Database Schema

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

---

## ⚙️ Installation

### Prerequisites

- Python 3.10+
- Webcam
- pip

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/your-username/smart-driver-monitoring-system.git
cd smart-driver-monitoring-system

# 2. (Recommended) Create a virtual environment
python -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
python app.py
```

Open your browser and navigate to:

```
http://127.0.0.1:5000
```

### requirements.txt (core dependencies)

```
flask
opencv-python
mediapipe
ultralytics
sqlalchemy
pygame
```

---

## 🖥️ Hardware Requirements

| Component | Minimum | Recommended |
|---|---|---|
| Processor | Intel Core i3 | Intel Core i5/i7 |
| RAM | 4 GB | 8 GB+ |
| GPU | — | NVIDIA (for faster YOLOv8 inference) |
| Camera | Standard Webcam | HD Webcam (720p+) |
| Storage | 500 MB | SSD |

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| **Language** | Python 3.10+ |
| **Web Framework** | Flask |
| **Computer Vision** | OpenCV |
| **Face Landmark Detection** | MediaPipe Face Mesh |
| **Object Detection** | YOLOv8 (Ultralytics) |
| **Database** | SQLite + SQLAlchemy ORM |
| **Frontend** | HTML5, CSS3, Bootstrap |
| **Audio Alerts** | Pygame |
| **Email Notifications** | SMTP (smtplib) |

---

## 📊 Detection Pipeline Summary

```
Frame (from Webcam)
       │
       ├──── MediaPipe Face Mesh ──────────► Facial Landmarks (468 points)
       │                                             │
       │                                    Eye Coordinates (12 points)
       │                                             │
       │                                    EAR Calculation
       │                                             │
       │                               EAR < threshold? ──► DROWSY
       │
       └──── YOLOv8 Inference ────────────► Detected Objects
                                                     │
                                          'cell phone' class? ──► PHONE DETECTED
```

---

## 🔮 Future Enhancements

- [ ] Night vision support (IR camera integration)
- [ ] Driver identity recognition (Face Recognition)
- [ ] Cloud database integration (PostgreSQL / Firebase)
- [ ] Mobile application (Flutter / React Native)
- [ ] GPS location tracking for incident reporting
- [ ] IoT vehicle integration (CAN bus)
- [ ] Edge AI deployment (Jetson Nano / Raspberry Pi)
- [ ] Multi-driver / multi-camera support
- [ ] Advanced gaze estimation (head pose detection)

---

## 👨‍💻 Author

**Abdul Haris H**
M.Tech — Computer Science and Engineering
Government Engineering College Thrissur

---

## 📄 License

This project is developed for academic and educational purposes.

---

<div align="center">
  <sub>Built with ❤️ using OpenCV, MediaPipe, and YOLOv8</sub>
</div>