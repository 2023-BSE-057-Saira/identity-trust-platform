# Enterprise Digital Identity, Trust & Deepfake Detection Platform
### AI-236 Case Study — Week 1: Identity Verification Engine

## What's built so far (Week 1 — now complete)
- **Auth**: register/login with JWT (python-jose + passlib/bcrypt), role field (applicant/analyst/admin) for later dashboard access control, ownership checks on documents/sessions
- **Document Intelligence**: OCR extraction (PaddleOCR) + field parsing + passport MRZ checksum validation (real ICAO 9303 algorithm) + image tampering heuristics (ELA + noise-consistency) + **document consistency checks** (expiry/DOB logic, MRZ-vs-OCR date cross-check) + **signature verification** (SSIM-based comparison)
- **Face Verification**: InsightFace embedding-based face matching (document photo vs. selfie)
- **Active Liveness**: Blink detection via MediaPipe FaceMesh + Eye Aspect Ratio (EAR)
- **API**: FastAPI endpoints wiring the above into a full verification flow, all protected behind login
- **DB schema**: Postgres models for User, Document, VerificationSession — already includes columns for deepfake_score, voice_match_score, trust_score, device_fingerprint so Week 2/3 don't require a schema migration

## Auth flow (test this first before anything else)
1. `POST /api/v1/auth/register` — body: `{"email": "...", "password": "...", "full_name": "..."}`
2. `POST /api/v1/auth/login` — form fields `username` (use your email) + `password` → returns `access_token`
3. Click the **"Authorize"** button (top right of `/docs`), paste in your email/password (Swagger handles the OAuth2 form) — this authorizes ALL subsequent requests in that browser session
4. Now every `/api/v1/identity/*` endpoint will work — they all require a valid token now

## Setup

### 1. Start Postgres + Redis
```bash
docker compose up -d
```

### 2. Python environment
```bash
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

> **Windows Tesseract setup (required, not optional):** `pytesseract` is just a
> Python wrapper — it calls the actual Tesseract OCR program, which you must
> install separately (not via pip). Download the Windows installer from
> https://github.com/UB-Mannheim/tesseract/wiki, install it, then add this
> line to your `.env` if it's not automatically on your PATH:
> ```
> TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
> ```
>
> **PaddleOCR was dropped** — it pins an old `protobuf` version that
> conflicts with `mediapipe`/`onnxruntime` (needed for face matching and
> liveness). This is a genuine, unresolvable dependency conflict on Windows,
> not a setup mistake — pytesseract avoids it entirely.

### 3. Environment variables
```bash
cp .env.example .env
```

### 4. Run the API
```bash
uvicorn app.main:app --reload
```
Visit `http://localhost:8000/docs` for interactive Swagger UI — this is the fastest way to test each endpoint by hand before building any frontend.

## API flow (Week 1)
0. Register + login (see Auth flow above) — required before anything else now
1. `POST /api/v1/identity/document/upload` — upload ID/passport image → OCR + forgery check + consistency check
2. `POST /api/v1/identity/face/verify` — upload selfie, matched against step 1's document → face similarity score
3. `POST /api/v1/identity/liveness/check` — upload short video (ask user to blink naturally) → liveness pass/fail
4. `POST /api/v1/identity/document/verify-signature` — compare a signature crop against a reference signature

## SECRET_KEY — add this to your .env before running
Auth needs a JWT signing secret. Add this line to your `.env` file:
```
SECRET_KEY=any-long-random-string-you-make-up-for-dev
```
(Never reuse a dev secret in a real deployment — this is fine for the demo/coursework.)

## Testing without real ID documents
You don't need real government IDs for the demo. For document testing:
- Generate synthetic ID card mockups (Canva/Figma template + fake data) — this also sidesteps any privacy/legal concern with using real IDs
- For passports specifically, you need a **valid MRZ** to test the checksum validator — you can hand-construct one using the ICAO 9303 format, or find publicly documented sample/specimen passport MRZ strings (never use a real person's document)

For face matching/liveness testing: just use your own webcam photos + a short selfie video of yourself blinking. That's realistic enough for a demo.

## Known simplifications (be upfront about these in your report/presentation)
| What the case study asks for | What we built | Why |
|---|---|---|
| 3D Face Validation | 2D landmark-based liveness (blink detection) | 3D liveness needs depth-camera hardware or a trained 3D CNN — out of scope for a 3-week team of 2 |
| Passive liveness | Not yet implemented | Week 2 candidate if time allows — passive liveness (texture/reflection analysis from a single image) is lower priority than active liveness for the demo |
| Full document forensics | Simplified ELA + noise-consistency heuristics | Real forensic tools use trained CNNs on large tampered-document datasets; we're demonstrating the *concept* with lightweight, explainable heuristics |

## Next steps (Week 2)
- Deepfake detection (pretrained classifier) — see `app/modules/deepfake_detection/`
- Voice authentication (Whisper + speaker embeddings) — see `app/modules/voice_auth/`
- Trust Scoring Engine combining all signals — see `app/modules/trust_scoring/`
