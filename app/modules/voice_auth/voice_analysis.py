"""
Voice authentication: speaker verification + voice clone/spoof detection.

DESIGN DECISION - why MFCC + librosa instead of Whisper/SpeechBrain:
Whisper and SpeechBrain speaker-embedding models are large downloads
(100MB-1GB+) from Hugging Face - given how much trouble large downloads
have caused throughout this project, MFCC-based speaker features are a
well-established, decades-old technique (used in real speaker verification
systems before deep learning took over) - no model download required,
just signal processing math via librosa. It's a weaker signal than a
trained deep speaker-embedding model, but it's real, explainable, and
will actually run without another download risk. State this trade-off
explicitly in your report.
"""

from typing import Dict

import numpy as np
import librosa


def _extract_mfcc_features(audio_path: str, n_mfcc: int = 20) -> np.ndarray:
    """
    Extracts a fixed-length MFCC feature vector representing this speaker's
    voice characteristics (mean + std of MFCCs across the clip - a simple
    but genuinely used "voiceprint" summary).
    """
    y, sr = librosa.load(audio_path, sr=16000, mono=True)
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=n_mfcc)
    feature_vector = np.concatenate([mfcc.mean(axis=1), mfcc.std(axis=1)])
    return feature_vector


def match_speakers(reference_audio_path: str, test_audio_path: str) -> Dict:
    """
    Compares two audio clips' MFCC voiceprints via cosine similarity.
    Returns {"score": float, "passed": bool, "reason": str|None}
    """
    try:
        ref_features = _extract_mfcc_features(reference_audio_path)
        test_features = _extract_mfcc_features(test_audio_path)
    except Exception as e:
        return {"score": None, "passed": False, "reason": f"Could not process audio: {e}"}

    similarity = float(
        np.dot(ref_features, test_features)
        / (np.linalg.norm(ref_features) * np.linalg.norm(test_features) + 1e-8)
    )
  # NOTE (updated after real-voice testing): initial testing with
    # synthetic tones suggested 0.90 was safe, but REAL voice testing
    # showed a genuine match at 0.996 and a real impostor at 0.963 - much
    # closer together than expected. This is a documented, honest
    # limitation of MFCC-based matching vs. deep speaker embeddings
    # (state this trade-off explicitly in your report). Threshold set at
    # the midpoint of these two real measurements as a reasonable
    # starting point, but this genuinely needs testing against more
    # real speaker pairs (3-5+) before the exact number can be trusted -
    # a narrow gap like this means the system may sometimes misclassify
    # borderline cases either direction.
    threshold = 0.98
    passed = similarity >= threshold

    return {
        "score": round(similarity, 4),
        "passed": passed,
        "reason": None if passed else "Voice characteristics do not sufficiently match reference",
    }


def detect_voice_spoof(audio_path: str) -> Dict:
    """
    Heuristic AI-voice / replay-attack detection via spectral analysis.

    Real signal, not a placeholder: synthetic TTS/voice-cloning systems and
    replayed audio (played through a speaker, re-recorded) both tend to
    show characteristic spectral differences from genuine live speech:

    1. SPECTRAL FLATNESS: synthetic vocoders often produce unnaturally
       smooth/flat spectral envelopes vs. the more "textured" spectrum of
       a real human vocal tract + room acoustics.
    2. HIGH-FREQUENCY ROLLOFF: replayed audio typically loses high-frequency
       content due to speaker/mic frequency response limits - a real tell
       used in actual anti-spoofing research (ASVspoof challenge).
    """
    try:
        y, sr = librosa.load(audio_path, sr=16000, mono=True)
    except Exception as e:
        return {"spoof_score": None, "reason": f"Could not process audio: {e}"}

    flatness = librosa.feature.spectral_flatness(y=y)
    mean_flatness = float(np.mean(flatness))

    stft = np.abs(librosa.stft(y))
    freqs = librosa.fft_frequencies(sr=sr)
    high_freq_mask = freqs > 6000
    high_freq_energy = float(stft[high_freq_mask, :].sum())
    total_energy = float(stft.sum()) + 1e-8
    high_freq_ratio = high_freq_energy / total_energy

    spoof_score = round(min(mean_flatness * 3 + (1 - min(high_freq_ratio * 20, 1)) * 0.5, 1.0), 4)

    return {
        "spoof_score": spoof_score,
        "spectral_flatness": round(mean_flatness, 4),
        "high_freq_energy_ratio": round(high_freq_ratio, 4),
        "flag": spoof_score > 0.6,
        "reason": "Spectral characteristics suggest possible synthetic/replayed audio" if spoof_score > 0.6 else None,
    }