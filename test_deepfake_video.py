from app.modules.deepfake_detection.detector import analyze_video_frames, check_blink_rate_plausibility
import cv2

# Point this to your actual blink video from Week 1 testing
video_path = "WIN_20260822_12_22_19_Pro.mp4"  # <-- update to your real filename/path

result = analyze_video_frames(video_path)
print("Deepfake analysis:", result)

# Get real video duration for the blink-rate check
cap = cv2.VideoCapture(video_path)
fps = cap.get(cv2.CAP_PROP_FPS)
frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
duration = frame_count / fps if fps > 0 else 0
cap.release()

print(f"Video duration: {duration:.1f} seconds")

# Using the blinks_detected value from your earlier liveness test (9 blinks)
blink_check = check_blink_rate_plausibility(blinks_detected=9, video_duration_seconds=duration, is_deliberate_challenge=True)
print("Blink rate plausibility:", blink_check)