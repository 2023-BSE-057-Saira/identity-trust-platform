"""
Active liveness detection via blink counting using Eye Aspect Ratio (EAR).

This is a well-established, real technique (Soukupova & Cech, 2016) - not a
toy heuristic. It won't catch a sophisticated video replay attack, but it
does defeat the simplest attack (a static printed photo held up to the
camera), and it's honest to say so in your documentation rather than
overselling it as "3D liveness."

Input: a short video (or sequence of frames) of the user's face, ideally
captured during the verification session asking them to blink naturally.
"""

from typing import List

import cv2
import numpy as np
import mediapipe as mp

from app.core.config import settings

mp_face_mesh = mp.solutions.face_mesh

# MediaPipe FaceMesh landmark indices for eyes (6 points each, standard EAR set)
LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]


def _eye_aspect_ratio(landmarks, eye_indices, frame_w, frame_h) -> float:
    pts = np.array([
        (landmarks[i].x * frame_w, landmarks[i].y * frame_h) for i in eye_indices
    ])
    # Vertical distances
    a = np.linalg.norm(pts[1] - pts[5])
    b = np.linalg.norm(pts[2] - pts[4])
    # Horizontal distance
    c = np.linalg.norm(pts[0] - pts[3])
    return (a + b) / (2.0 * c) if c > 0 else 0.0


def run_blink_liveness(video_path: str) -> dict:
    """
    Reads frames from a video file, tracks EAR per frame, counts blinks.

    Returns:
        {
            "liveness_passed": bool,
            "blinks_detected": int,
            "ear_min": float,
            "frames_analyzed": int,
            "reason": str | None
        }
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return {"liveness_passed": False, "reason": f"Could not open video: {video_path}"}

    ear_values: List[float] = []
    blink_count = 0
    consecutive_low_frames = 0

    with mp_face_mesh.FaceMesh(
        max_num_faces=1, refine_landmarks=True,
        min_detection_confidence=0.5, min_tracking_confidence=0.5
    ) as face_mesh:

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            h, w = frame.shape[:2]
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_mesh.process(rgb)

            if not results.multi_face_landmarks:
                continue

            landmarks = results.multi_face_landmarks[0].landmark
            left_ear = _eye_aspect_ratio(landmarks, LEFT_EYE, w, h)
            right_ear = _eye_aspect_ratio(landmarks, RIGHT_EYE, w, h)
            avg_ear = (left_ear + right_ear) / 2.0
            ear_values.append(avg_ear)

            if avg_ear < settings.BLINK_EAR_THRESHOLD:
                consecutive_low_frames += 1
            else:
                if consecutive_low_frames >= settings.BLINK_CONSEC_FRAMES:
                    blink_count += 1
                consecutive_low_frames = 0

    cap.release()

    if not ear_values:
        return {"liveness_passed": False, "reason": "No face detected in any frame"}

    # Require at least one genuine blink to pass - defeats a static photo
    # held up to the camera, which will show constant EAR with zero blinks.
    passed = blink_count >= 1

    return {
        "liveness_passed": passed,
        "blinks_detected": blink_count,
        "ear_min": round(float(min(ear_values)), 4),
        "frames_analyzed": len(ear_values),
        "reason": None if passed else "No blink detected - possible static photo/spoof attempt",
    }
