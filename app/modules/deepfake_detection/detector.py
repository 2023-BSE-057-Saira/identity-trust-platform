"""
Deepfake detection.

Two real, complementary signals, neither requiring a downloaded model:

1. FREQUENCY-DOMAIN ARTIFACT DETECTION
   GAN-generated and face-swapped images leave a statistically detectable
   "fingerprint" in their frequency spectrum - upsampling layers in GAN
   decoders create periodic checkerboard-like patterns invisible to the
   eye but visible as anomalous peaks in the FFT magnitude spectrum. This
   is a real, published technique (see Zhang et al. 2019, "Detecting and
   Simulating Artifacts in GAN Fake Images" and Durall et al. 2020).

   CALIBRATION NOTE (important - read before trusting this in your report):
   The scaling below was originally tuned against synthetic test images
   (a smooth gradient vs. a hand-drawn checkerboard pattern), which
   produced ring-energy ratios around 0.017-0.072. Real compressed webcam
   video turned out to sit MUCH higher - around 0.18-0.19 for genuine,
   unedited footage - because real video naturally carries more
   high-frequency energy from compression artifacts and sensor noise than
   a clean synthetic image does. The scaling was recalibrated using one
   real genuine-video sample (mean ratio 0.183, max 0.191) as the "should
   score low" anchor point. This is ONE real sample, not a validated
   dataset - before presenting exact numbers in your report, test against
   at least one genuine deepfake/face-swap sample too, since the upper
   end of this scale is still an estimate, not measured against real
   manipulated footage. State this limitation explicitly if asked.

2. TEMPORAL BLINK-RATE CONSISTENCY
   Reuses the liveness module's blink detection. This check is meaningful
   for PASSIVE footage (natural resting blink rate, ~15-20/min). It is
   NOT meaningful for a short, deliberate liveness-challenge clip where
   the subject is intentionally blinking rapidly on request - that's a
   different behavior entirely and will produce a much higher rate
   without being suspicious. Use passive/longer footage for this specific
   check, or skip it for challenge-response liveness clips.
"""

from typing import Dict, List

import cv2
import numpy as np


def _fft_artifact_score(frame: np.ndarray) -> float:
    """
    Computes a GAN-artifact score from a single frame's frequency spectrum.

    Recalibrated linear mapping (see module docstring for why):
    - ratio <= 0.10  -> score 0.0 (very clean/low high-freq energy)
    - ratio >= 0.45  -> score 1.0 (very high high-freq energy - estimated
      upper bound, not yet validated against a real deepfake sample)
    - real genuine webcam video (ratio ~0.18-0.19) lands around 0.18-0.20,
      comfortably below the 0.5 flag threshold, as it should.
    """
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

    high_freq_energy = magnitude[high_freq_mask].sum()
    total_energy = magnitude.sum() + 1e-8
    ratio = float(high_freq_energy / total_energy)

    RATIO_FLOOR = 0.10
    RATIO_CEILING = 0.45
    score = (ratio - RATIO_FLOOR) / (RATIO_CEILING - RATIO_FLOOR)
    return float(min(max(score, 0.0), 1.0))


def analyze_video_frames(video_path: str, sample_every_n_frames: int = 10) -> Dict:
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return {"deepfake_score": None, "reason": f"Could not open video: {video_path}"}

    frame_scores: List[float] = []
    frame_idx = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx % sample_every_n_frames == 0:
            score = _fft_artifact_score(frame)
            frame_scores.append(score)
        frame_idx += 1

    cap.release()

    if not frame_scores:
        return {"deepfake_score": None, "reason": "No frames could be analyzed"}

    mean_score = float(np.mean(frame_scores))
    max_score = float(np.max(frame_scores))
    deepfake_score = round(0.7 * mean_score + 0.3 * max_score, 4)

    return {
        "deepfake_score": deepfake_score,
        "mean_frame_score": round(mean_score, 4),
        "max_frame_score": round(max_score, 4),
        "frames_analyzed": len(frame_scores),
        "flag": deepfake_score > 0.5,
    }


def check_blink_rate_plausibility(
    blinks_detected: int,
    video_duration_seconds: float,
    is_deliberate_challenge: bool = False,
) -> Dict:
    """
    Cross-checks blink rate against known human norms.

    is_deliberate_challenge: set True for short liveness-challenge clips
    where the subject is deliberately asked to blink (much higher rates
    are normal and NOT suspicious in that context). Set False (default)
    only for longer passive footage where natural resting blink rate
    (~4-30/min) is the right comparison.
    """
    if video_duration_seconds <= 0:
        return {"plausible": None, "reason": "Invalid video duration"}

    blink_rate_per_minute = (blinks_detected / video_duration_seconds) * 60

    if is_deliberate_challenge:
        plausible = blink_rate_per_minute > 0
        reason = None if plausible else "No blinking detected during challenge clip"
    else:
        plausible = 4 <= blink_rate_per_minute <= 30
        reason = None if plausible else f"Blink rate ({blink_rate_per_minute:.1f}/min) outside normal passive human range"

    return {
        "blink_rate_per_minute": round(blink_rate_per_minute, 2),
        "plausible": plausible,
        "reason": reason,
    }