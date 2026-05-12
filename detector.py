import cv2
import mediapipe as mp
import numpy as np
import pygame
import os
from ultralytics import YOLO

# -----------------------------
# Alarm setup
# -----------------------------
pygame.mixer.init()
pygame.mixer.music.load(os.path.join(os.getcwd(), "alarm.wav"))

# -----------------------------
# MediaPipe Face Mesh setup
# -----------------------------
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    refine_landmarks=True,
    max_num_faces=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# -----------------------------
# YOLO model setup
# -----------------------------
model = YOLO("yolov8n.pt")

# -----------------------------
# Eye landmark points
# -----------------------------
LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]

# COCO class id for cell phone = 67
PHONE_CLASS_ID = 67


def calculate_ear(eye_points, landmarks, frame_w, frame_h):
    coords = []
    for point in eye_points:
        x = int(landmarks[point].x * frame_w)
        y = int(landmarks[point].y * frame_h)
        coords.append((x, y))

    A = np.linalg.norm(np.array(coords[1]) - np.array(coords[5]))
    B = np.linalg.norm(np.array(coords[2]) - np.array(coords[4]))
    C = np.linalg.norm(np.array(coords[0]) - np.array(coords[3]))

    if C == 0:
        return 0.0

    ear = (A + B) / (2.0 * C)
    return ear


def detect_phone(frame):
    phone_detected = False

    results = model(frame, verbose=False)

    for result in results:
        if result.boxes is None:
            continue

        for box in result.boxes:
            cls_id = int(box.cls[0].item())
            conf = float(box.conf[0].item())

            if cls_id == PHONE_CLASS_ID and conf > 0.45:
                phone_detected = True

                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 165, 255), 2)
                cv2.putText(
                    frame,
                    f"Phone {conf:.2f}",
                    (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 165, 255),
                    2
                )

    return phone_detected


def start_detection():
    cap = cv2.VideoCapture(0)

    EAR_THRESHOLD = 0.23
    COUNTER = 0

    drowsy_count = 0
    phone_count = 0

    drowsy_logged = False
    phone_logged = False

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        result = face_mesh.process(rgb)

        status = "Awake"
        phone_detected = detect_phone(frame)

        if result.multi_face_landmarks:
            for face_landmarks in result.multi_face_landmarks:
                landmarks = face_landmarks.landmark

                left_ear = calculate_ear(LEFT_EYE, landmarks, w, h)
                right_ear = calculate_ear(RIGHT_EYE, landmarks, w, h)
                ear = (left_ear + right_ear) / 2.0

                cv2.putText(
                    frame,
                    f"EAR: {ear:.2f}",
                    (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (255, 255, 0),
                    2
                )

                if ear < EAR_THRESHOLD:
                    COUNTER += 1

                    if COUNTER > 15:
                        status = "Drowsy"

                        if not drowsy_logged:
                            drowsy_count += 1
                            drowsy_logged = True

                        if not pygame.mixer.music.get_busy():
                            pygame.mixer.music.play()
                    else:
                        status = "Sleepy"
                else:
                    COUNTER = 0
                    drowsy_logged = False

                    if not phone_detected:
                        pygame.mixer.music.stop()

        if phone_detected:
            status = "Using Phone"

            if not phone_logged:
                phone_count += 1
                phone_logged = True

            if not pygame.mixer.music.get_busy():
                pygame.mixer.music.play()
        else:
            phone_logged = False

        if status == "Awake":
            color = (0, 255, 0)
        elif status == "Sleepy":
            color = (0, 255, 255)
        elif status == "Drowsy":
            color = (0, 0, 255)
        else:
            color = (0, 165, 255)

        cv2.putText(
            frame,
            status,
            (180, 100),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.5,
            color,
            3
        )

        cv2.putText(
            frame,
            f"Drowsy Count: {drowsy_count}",
            (20, 80),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 200, 255),
            2
        )

        cv2.putText(
            frame,
            f"Phone Count: {phone_count}",
            (20, 120),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 100, 100),
            2
        )

        cv2.imshow("Driver Monitoring", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESC key
            break

    cap.release()
    cv2.destroyAllWindows()
    pygame.mixer.music.stop()

    return {
        "total_drowsy_events": drowsy_count,
        "total_phone_events": phone_count
    }