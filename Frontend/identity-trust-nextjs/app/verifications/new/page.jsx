"use client";
import { useState } from "react";
import Link from "next/link";
import { Check, FileText, ScanFace, Eye, VideoOff, Mic, ArrowRight, ArrowLeft, ExternalLink } from "lucide-react";
import AppShell from "@/components/layout/AppShell";
import TopBar from "@/components/layout/TopBar";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import FileField from "@/components/shared/FileField";
import TrustGauge from "@/components/shared/TrustGauge";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/table";
import {
  uploadDocument, verifyFace, checkLiveness, analyzeDeepfake, verifyVoice, computeTrustScore,
} from "@/lib/api";

const STEPS = [
  { key: "document", label: "Document", icon: FileText },
  { key: "face", label: "Face match", icon: ScanFace },
  { key: "liveness", label: "Liveness", icon: Eye },
  { key: "deepfake", label: "Deepfake", icon: VideoOff },
  { key: "voice", label: "Voice", icon: Mic },
  { key: "result", label: "Result", icon: Check },
];

function StepIndicator({ currentIndex }) {
  return (
    <div className="mb-8 flex items-center">
      {STEPS.map((step, i) => {
        const Icon = step.icon;
        const done = i < currentIndex;
        const active = i === currentIndex;
        return (
          <div key={step.key} className="flex flex-1 items-center last:flex-none">
            <div className="flex flex-col items-center gap-1.5">
              <div
                className={`flex h-8 w-8 items-center justify-center rounded-full border text-xs font-medium transition-colors ${
                  done ? "border-primary bg-primary text-primary-foreground"
                  : active ? "border-primary text-primary"
                  : "border-border text-muted-foreground"
                }`}
              >
                {done ? <Check className="h-4 w-4" /> : <Icon className="h-4 w-4" strokeWidth={1.75} />}
              </div>
              <span className={`text-[11px] ${active ? "text-foreground" : "text-muted-foreground"}`}>{step.label}</span>
            </div>
            {i < STEPS.length - 1 && <div className={`mx-2 h-px flex-1 ${done ? "bg-primary" : "bg-border"}`} />}
          </div>
        );
      })}
    </div>
  );
}

function ResultRow({ label, value, tone = "neutral" }) {
  const color = { good: "text-primary", bad: "text-destructive", caution: "text-caution", neutral: "text-foreground" }[tone];
  return (
    <div className="flex items-center justify-between border-b border-border py-2 text-sm last:border-0">
      <span className="text-muted-foreground">{label}</span>
      <span className={`font-mono-tabular ${color}`}>{value}</span>
    </div>
  );
}

export default function NewVerificationPage() {
  const [stepIndex, setStepIndex] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [documentType, setDocumentType] = useState("national_id");
  const [documentFile, setDocumentFile] = useState(null);
  const [documentId, setDocumentId] = useState(null);
  const [documentResult, setDocumentResult] = useState(null);

  const [selfieFile, setSelfieFile] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [faceResult, setFaceResult] = useState(null);

  const [livenessFile, setLivenessFile] = useState(null);
  const [livenessResult, setLivenessResult] = useState(null);

  const [deepfakeFile, setDeepfakeFile] = useState(null);
  const [deepfakeResult, setDeepfakeResult] = useState(null);

  const [refAudioFile, setRefAudioFile] = useState(null);
  const [testAudioFile, setTestAudioFile] = useState(null);
  const [voiceResult, setVoiceResult] = useState(null);

  const [trustResult, setTrustResult] = useState(null);

  function goNext() { setStepIndex((i) => Math.min(i + 1, STEPS.length - 1)); setError(""); }
  function goBack() { setStepIndex((i) => Math.max(i - 1, 0)); setError(""); }

  function extractErrorMessage(err, fallback) {
    // Surface the REAL backend error instead of a generic guess - FastAPI
    // returns { detail: "..." } on errors, and network-level failures
    // (backend down, CORS block) look different from that. Logging the
    // full error to console too so it's visible in DevTools regardless.
    console.error(fallback, err);
    if (err.response?.data?.detail) return `${fallback}: ${err.response.data.detail}`;
    if (err.response?.status) return `${fallback} (HTTP ${err.response.status}). Check the backend terminal for the full error.`;
    if (err.request) return `${fallback}: no response from backend. Is uvicorn running, and is CORS configured for this origin?`;
    return `${fallback}: ${err.message}`;
  }

  async function handleDocumentSubmit() {
    if (!documentFile) { setError("Choose a document image first."); return; }
    setLoading(true); setError("");
    try {
      const res = await uploadDocument(documentType, documentFile);
      setDocumentId(res.document_id);
      setDocumentResult(res);
      goNext();
    } catch (err) { setError(extractErrorMessage(err, "Document upload failed")); }
    finally { setLoading(false); }
  }

  async function handleFaceSubmit() {
    if (!selfieFile) { setError("Choose a selfie image first."); return; }
    setLoading(true); setError("");
    try {
      const res = await verifyFace(documentId, selfieFile);
      setSessionId(res.session_id);
      setFaceResult(res);
      goNext();
    } catch (err) { setError(extractErrorMessage(err, "Face verification failed")); }
    finally { setLoading(false); }
  }

  async function handleLivenessSubmit() {
    if (!livenessFile) { setError("Choose a liveness video first."); return; }
    setLoading(true); setError("");
    try {
      const res = await checkLiveness(sessionId, livenessFile);
      setLivenessResult(res);
      goNext();
    } catch (err) { setError(extractErrorMessage(err, "Liveness check failed")); }
    finally { setLoading(false); }
  }

  async function handleDeepfakeSubmit() {
    if (!deepfakeFile) { setError("Choose a video first."); return; }
    setLoading(true); setError("");
    try {
      const res = await analyzeDeepfake(sessionId, deepfakeFile);
      setDeepfakeResult(res);
      goNext();
    } catch (err) { setError(extractErrorMessage(err, "Deepfake analysis failed")); }
    finally { setLoading(false); }
  }

  async function handleVoiceSubmit() {
    if (!refAudioFile || !testAudioFile) { setError("Choose both audio clips first."); return; }
    setLoading(true); setError("");
    try {
      const res = await verifyVoice(sessionId, refAudioFile, testAudioFile);
      setVoiceResult(res);
      const trust = await computeTrustScore(sessionId);
      setTrustResult(trust);
      goNext();
    } catch (err) { setError(extractErrorMessage(err, "Voice verification failed")); }
    finally { setLoading(false); }
  }

  async function skipToResult() {
    const trust = await computeTrustScore(sessionId).catch(() => null);
    if (trust) setTrustResult(trust);
    goNext();
  }

  const step = STEPS[stepIndex].key;

  return (
    <AppShell>
      <TopBar title="New verification" subtitle="Run a session through the full pipeline, step by step" />
      <div className="flex-1 overflow-y-auto px-8 py-6">
        <div className="mx-auto max-w-2xl">
          <StepIndicator currentIndex={stepIndex} />

          {error && <div className="mb-4 rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-2.5 text-sm text-destructive">{error}</div>}

          {step === "document" && (
            <Card>
              <CardHeader><CardTitle>Step 1 · Upload identity document</CardTitle><CardDescription>OCR, forgery, and consistency checks run automatically.</CardDescription></CardHeader>
              <CardContent className="flex flex-col gap-4">
                <div>
                  <label className="mb-1.5 block text-sm text-muted-foreground">Document type</label>
                  <Select value={documentType} onValueChange={setDocumentType}>
                    <SelectTrigger className="w-full"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="national_id">National ID</SelectItem>
                      <SelectItem value="passport">Passport</SelectItem>
                      <SelectItem value="license">Driving license</SelectItem>
                      <SelectItem value="employee_id">Employee ID</SelectItem>
                      <SelectItem value="residence_permit">Residence permit</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <FileField label="Document image" accept="image/*" onChange={setDocumentFile} />

                {documentResult && (
                  <div className="rounded-lg border border-border bg-background px-4 py-3">
                    <ResultRow label="Forgery check" value={documentResult.is_forged ? "Flagged" : "Passed"} tone={documentResult.is_forged ? "bad" : "good"} />
                    <ResultRow label="Consistency check" value={documentResult.consistency_check?.consistent ? "Passed" : "Issues found"} tone={documentResult.consistency_check?.consistent ? "good" : "caution"} />
                  </div>
                )}

                <Button onClick={handleDocumentSubmit} disabled={loading} className="mt-2">
                  {loading ? "Uploading…" : "Upload & continue"} <ArrowRight className="h-4 w-4" />
                </Button>
              </CardContent>
            </Card>
          )}

          {step === "face" && (
            <Card>
              <CardHeader><CardTitle>Step 2 · Face match</CardTitle><CardDescription>Compares this selfie against the photo on the uploaded document.</CardDescription></CardHeader>
              <CardContent className="flex flex-col gap-4">
                <FileField label="Selfie image" accept="image/*" onChange={setSelfieFile} />
                {faceResult && (
                  <div className="rounded-lg border border-border bg-background px-4 py-3">
                    <ResultRow label="Similarity score" value={faceResult.score?.toFixed(4)} />
                    <ResultRow label="Result" value={faceResult.passed ? "Passed" : "Below threshold"} tone={faceResult.passed ? "good" : "bad"} />
                  </div>
                )}
                <div className="flex gap-2">
                  <Button variant="outline" onClick={goBack}><ArrowLeft className="h-4 w-4" /> Back</Button>
                  <Button onClick={handleFaceSubmit} disabled={loading} className="flex-1">{loading ? "Verifying…" : "Verify & continue"} <ArrowRight className="h-4 w-4" /></Button>
                </div>
              </CardContent>
            </Card>
          )}

          {step === "liveness" && (
            <Card>
              <CardHeader><CardTitle>Step 3 · Liveness check</CardTitle><CardDescription>A short video of the subject blinking - defeats a static photo spoof.</CardDescription></CardHeader>
              <CardContent className="flex flex-col gap-4">
                <FileField label="Liveness video" accept="video/*" onChange={setLivenessFile} />
                {livenessResult && (
                  <div className="rounded-lg border border-border bg-background px-4 py-3">
                    <ResultRow label="Blinks detected" value={livenessResult.blinks_detected} />
                    <ResultRow label="Result" value={livenessResult.liveness_passed ? "Live subject confirmed" : "No blink detected"} tone={livenessResult.liveness_passed ? "good" : "bad"} />
                  </div>
                )}
                <div className="flex gap-2">
                  <Button variant="outline" onClick={goBack}><ArrowLeft className="h-4 w-4" /> Back</Button>
                  <Button variant="ghost" onClick={goNext}>Skip</Button>
                  <Button onClick={handleLivenessSubmit} disabled={loading} className="flex-1">{loading ? "Checking…" : "Check & continue"} <ArrowRight className="h-4 w-4" /></Button>
                </div>
              </CardContent>
            </Card>
          )}

          {step === "deepfake" && (
            <Card>
              <CardHeader><CardTitle>Step 4 · Deepfake analysis</CardTitle><CardDescription>Scans video frames for manipulation artifacts using frequency-domain analysis.</CardDescription></CardHeader>
              <CardContent className="flex flex-col gap-4">
                <FileField label="Video (can reuse the liveness clip)" accept="video/*" onChange={setDeepfakeFile} />
                {deepfakeResult && (
                  <div className="rounded-lg border border-border bg-background px-4 py-3">
                    <ResultRow label="Deepfake score" value={deepfakeResult.deepfake_score?.toFixed(4)} />
                    <ResultRow label="Result" value={deepfakeResult.flag ? "Flagged" : "Clean"} tone={deepfakeResult.flag ? "bad" : "good"} />
                  </div>
                )}
                <div className="flex gap-2">
                  <Button variant="outline" onClick={goBack}><ArrowLeft className="h-4 w-4" /> Back</Button>
                  <Button variant="ghost" onClick={goNext}>Skip</Button>
                  <Button onClick={handleDeepfakeSubmit} disabled={loading} className="flex-1">{loading ? "Analyzing…" : "Analyze & continue"} <ArrowRight className="h-4 w-4" /></Button>
                </div>
              </CardContent>
            </Card>
          )}

          {step === "voice" && (
            <Card>
              <CardHeader><CardTitle>Step 5 · Voice authentication</CardTitle><CardDescription>Compares a reference clip against a test clip, and checks for synthetic/replayed audio.</CardDescription></CardHeader>
              <CardContent className="flex flex-col gap-4">
                <FileField label="Reference audio" accept="audio/*" onChange={setRefAudioFile} />
                <FileField label="Test audio" accept="audio/*" onChange={setTestAudioFile} />
                {voiceResult && (
                  <div className="rounded-lg border border-border bg-background px-4 py-3">
                    <ResultRow label="Voice match score" value={voiceResult.match?.score?.toFixed(4)} />
                    <ResultRow label="Spoof score" value={voiceResult.spoof_check?.spoof_score?.toFixed(4)} tone={voiceResult.spoof_check?.flag ? "bad" : "good"} />
                  </div>
                )}
                <div className="flex gap-2">
                  <Button variant="outline" onClick={goBack}><ArrowLeft className="h-4 w-4" /> Back</Button>
                  <Button variant="ghost" onClick={skipToResult}>Skip</Button>
                  <Button onClick={handleVoiceSubmit} disabled={loading} className="flex-1">{loading ? "Verifying…" : "Verify & finish"} <ArrowRight className="h-4 w-4" /></Button>
                </div>
              </CardContent>
            </Card>
          )}

          {step === "result" && (
            <div className="flex flex-col gap-5">
              <Card className="flex flex-col items-center py-8">
                <TrustGauge score={trustResult?.trust_score} />
                <p className="mt-3 text-sm text-muted-foreground">Session ID: <span className="font-mono text-foreground">{sessionId}</span></p>
              </Card>

              {trustResult && (
                <Card>
                  <CardHeader><CardTitle>Trust score breakdown</CardTitle></CardHeader>
                  <CardContent className="px-0 pb-0">
                    <Table>
                      <TableHeader><TableRow><TableHead>Factor</TableHead><TableHead>Explanation</TableHead><TableHead className="text-right">Points</TableHead></TableRow></TableHeader>
                      <TableBody>
                        {trustResult.breakdown.map((b) => (
                          <TableRow key={b.factor}>
                            <TableCell className="text-sm font-medium">{b.factor}</TableCell>
                            <TableCell className="text-xs text-muted-foreground">{b.explanation}</TableCell>
                            <TableCell className="text-right font-mono-tabular text-sm">{b.points} / {b.max_points}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </CardContent>
                </Card>
              )}

              <div className="flex gap-3">
                <Button asChild className="flex-1">
                  <Link href={`/verifications/${sessionId}`}>Open full investigation <ExternalLink className="h-4 w-4" /></Link>
                </Button>
                <Button variant="outline" onClick={() => window.location.reload()}>Start another</Button>
              </div>
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
