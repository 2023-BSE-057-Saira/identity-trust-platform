"""
Face matching: compares the face on the ID document photo against the live
selfie using InsightFace embeddings + cosine similarity.

InsightFace's buffalo_l model gives you detection + 512-d embeddings in one
call, which is why it's the standard choice here over building your own
detector+embedder pipeline.
"""

from typing import Optional, Tuple

import numpy as np
import insightface
from insightface.app import FaceAnalysis

from app.core.config import settings

_face_app: Optional[FaceAnalysis] = None


def get_face_app() -> FaceAnalysis:
    global _face_app
    if _face_app is None:
        _face_app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
        _face_app.prepare(ctx_id=0, det_size=(640, 640))
    return _face_app


def get_face_embedding(image_path: str) -> Optional[np.ndarray]:
    """Returns the 512-d embedding of the largest detected face, or None if no face found."""
    import cv2

    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not read image: {image_path}")

    app = get_face_app()
    faces = app.get(img)

    if not faces:
        return None

    # If multiple faces detected, take the largest bounding box (most likely
    # the primary subject rather than a background face).
    largest = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
    return largest.normed_embedding


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def match_faces(document_image_path: str, selfie_image_path: str) -> dict:
    """
    Returns {"score": float, "passed": bool, "reason": str|None}
    score is cosine similarity in [-1, 1], typically [0, 1] for real faces.
    """
    doc_embedding = get_face_embedding(document_image_path)
    selfie_embedding = get_face_embedding(selfie_image_path)

    if doc_embedding is None:
        return {"score": None, "passed": False, "reason": "No face detected on document"}
    if selfie_embedding is None:
        return {"score": None, "passed": False, "reason": "No face detected in selfie"}

    score = cosine_similarity(doc_embedding, selfie_embedding)
    passed = score >= settings.FACE_MATCH_THRESHOLD

    return {
        "score": round(score, 4),
        "passed": passed,
        "reason": None if passed else "Face similarity below threshold",
    }
