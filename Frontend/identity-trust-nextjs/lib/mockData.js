/**
 * MOCK DATA - for endpoints that don't exist on the backend yet.
 * See README.md for the full real-vs-mock breakdown.
 */
export function mockSessionsList() {
  return [
    { id: "e1cabb12-2b75-486d-a368-3a8625e9ceed", user_email: "sasha@test.com", status: "passed", trust_score: 82.1, created_at: "2026-08-24T05:10:45Z" },
    { id: "a2f9c001-1234-4abc-9def-000000000001", user_email: "bob@test.com", status: "failed", trust_score: 15.0, created_at: "2026-08-24T06:02:10Z" },
    { id: "a2f9c001-1234-4abc-9def-000000000002", user_email: "carol@test.com", status: "review", trust_score: 52.3, created_at: "2026-08-24T06:15:33Z" },
    { id: "a2f9c001-1234-4abc-9def-000000000003", user_email: "dave@test.com", status: "passed", trust_score: 91.4, created_at: "2026-08-23T18:44:02Z" },
    { id: "a2f9c001-1234-4abc-9def-000000000004", user_email: "erin@test.com", status: "failed", trust_score: 8.2, created_at: "2026-08-23T14:20:11Z" },
  ];
}

export function mockSessionDetail(sessionId) {
  return {
    id: sessionId,
    user_email: "sasha@test.com",
    status: "passed",
    created_at: "2026-08-24T05:10:45Z",
    document: { document_type: "national_id", is_forged: false, forgery_reasons: [], consistency_issues: [] },
    face_match: { score: 0.7389, passed: true },
    liveness: { passed: true, blinks_detected: 9 },
    deepfake: { score: 0.2435, flag: false },
    voice: { match_score: 0.996, spoof_score: 0.5588 },
  };
}

export function mockAlerts() {
  return [
    { id: "al-1", type: "deepfake_detected", severity: "high", session_id: "a2f9c001-1234-4abc-9def-000000000001", description: "Deepfake artifact score 0.90 exceeded threshold", created_at: "2026-08-24T06:02:10Z" },
    { id: "al-2", type: "voice_clone_attempt", severity: "medium", session_id: "a2f9c001-1234-4abc-9def-000000000002", description: "Voice spoof score 0.68 flagged for review", created_at: "2026-08-24T06:15:33Z" },
    { id: "al-3", type: "device_anomaly", severity: "high", session_id: "a2f9c001-1234-4abc-9def-000000000004", description: "Device fingerprint shared with 2 other accounts", created_at: "2026-08-23T14:20:11Z" },
  ];
}
