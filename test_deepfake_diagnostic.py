import cv2
import numpy as np
from app.modules.deepfake_detection.detector import _fft_artifact_score

video_path = "WIN_20260822_12_22_19_Pro.mp4"
cap = cv2.VideoCapture(video_path)

raw_ratios = []
frame_idx = 0
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    if frame_idx % 10 == 0:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, (256, 256))
        f = np.fft.fft2(gray)
        fshift = np.fft.fftshift(f)
        magnitude = np.abs(fshift)
        h, w = magnitude.shape
        cy, cx = h // 2, w // 2
        y, x = np.ogrid[:h, :w]
        dist = np.sqrt((y - cy) ** 2 + (x - cx) ** 2)
        max_dist = np.sqrt(cy ** 2 + cx ** 2)
        high_freq_mask = dist > (0.6 * max_dist)
        ratio = float(magnitude[high_freq_mask].sum() / (magnitude.sum() + 1e-8))
        raw_ratios.append(ratio)
    frame_idx += 1
cap.release()

print("Raw (unscaled) ratios per sampled frame:", [round(r, 5) for r in raw_ratios])
print("Mean raw ratio:", round(np.mean(raw_ratios), 5))
print("Max raw ratio:", round(np.max(raw_ratios), 5))