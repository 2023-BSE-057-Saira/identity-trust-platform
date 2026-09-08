import axios from "axios";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
const api = axios.create({ baseURL: API_BASE });

api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401 && typeof window !== "undefined") {
      localStorage.removeItem("access_token");
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);

export async function login(email, password) {
  const form = new URLSearchParams();
  form.append("username", email);
  form.append("password", password);
  const res = await api.post("/api/v1/auth/login", form, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  if (typeof window !== "undefined") localStorage.setItem("access_token", res.data.access_token);
  return res.data;
}

export function logout() {
  if (typeof window !== "undefined") localStorage.removeItem("access_token");
}

export function isLoggedIn() {
  if (typeof window === "undefined") return false;
  return !!localStorage.getItem("access_token");
}

// --- New Verification wizard - real multipart calls to the actual
// verification pipeline (same endpoints tested throughout Weeks 1-2). ---

export const uploadDocument = (documentType, file) => {
  const form = new FormData();
  form.append("file", file);
  return api
    .post(`/api/v1/identity/document/upload?document_type=${documentType}`, form)
    .then((r) => r.data);
};

export const verifyFace = (documentId, selfieFile) => {
  const form = new FormData();
  form.append("selfie", selfieFile);
  return api
    .post(`/api/v1/identity/face/verify?document_id=${documentId}`, form)
    .then((r) => r.data);
};

export const checkLiveness = (sessionId, videoFile) => {
  const form = new FormData();
  form.append("video", videoFile);
  return api
    .post(`/api/v1/identity/liveness/check?session_id=${sessionId}`, form)
    .then((r) => r.data);
};

export const analyzeDeepfake = (sessionId, videoFile) => {
  const form = new FormData();
  form.append("video", videoFile);
  return api
    .post(`/api/v1/identity/deepfake/analyze?session_id=${sessionId}`, form)
    .then((r) => r.data);
};

export const verifyVoice = (sessionId, referenceFile, testFile) => {
  const form = new FormData();
  form.append("reference_audio", referenceFile);
  form.append("test_audio", testFile);
  return api
    .post(`/api/v1/identity/voice/verify?session_id=${sessionId}`, form)
    .then((r) => r.data);
};

export const getDashboardSummary = () => api.get("/api/v1/dashboard/summary").then((r) => r.data);
export const getTrustDistribution = () => api.get("/api/v1/dashboard/trust-score-distribution").then((r) => r.data);
export const getFraudRings = () => api.get("/api/v1/graph/fraud-rings").then((r) => r.data);
export const computeTrustScore = (sessionId) =>
  api.post(`/api/v1/identity/trust-score/compute?session_id=${sessionId}`).then((r) => r.data);
export const askCopilot = (sessionId, question) =>
  api.post("/api/v1/copilot/ask", { session_id: sessionId, question }).then((r) => r.data);

export default api;
