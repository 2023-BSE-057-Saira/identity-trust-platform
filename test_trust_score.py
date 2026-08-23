from app.modules.trust_scoring.engine import compute_trust_score
import json

# Using your REAL results from Week 1 + Week 2 testing
result = compute_trust_score(
    face_match_score=0.7389,        # your real face match (Photo A vs Photo B)
    face_match_passed=True,
    liveness_passed=True,            # your real liveness test (9 blinks)
    document_is_forged=False,        # your real document check
    document_forgery_score=0.089,
    deepfake_score=0.2435,           # your real recalibrated deepfake score
    voice_match_score=0.996,         # your real voice match
    voice_match_passed=True,
    voice_spoof_score=0.5588,        # your real spoof check score
)

print(json.dumps(result, indent=2))