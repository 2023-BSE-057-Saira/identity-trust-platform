"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { FileText, ScanFace, Eye, VideoOff, Mic, Send } from "lucide-react";
import AppShell from "@/components/layout/AppShell";
import TopBar from "@/components/layout/TopBar";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/table";
import StatusBadge from "@/components/shared/StatusBadge";
import TrustGauge from "@/components/shared/TrustGauge";
import SignalBar from "@/components/shared/SignalBar";
import { computeTrustScore, askCopilot } from "@/lib/api";
import { mockSessionDetail } from "@/lib/mockData";

const SUGGESTED_QUESTIONS = ["Why did verification fail?", "Explain the fraud indicators.", "Show deepfake probability.", "Recommend verification action."];

function EvidenceCard({ icon: Icon, title, children }) {
  return (
    <Card>
      <CardHeader className="flex-row items-center gap-2.5 space-y-0"><Icon className="h-4 w-4 text-muted-foreground" strokeWidth={1.75} /><CardTitle>{title}</CardTitle></CardHeader>
      <CardContent>{children}</CardContent>
    </Card>
  );
}

function CopilotPanel({ sessionId }) {
  const [messages, setMessages] = useState([{ role: "assistant", text: "Ask me anything about this session — I'll ground my answer in the actual trust score breakdown." }]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  async function send(question) {
    if (!question.trim()) return;
    setMessages((m) => [...m, { role: "user", text: question }]);
    setInput("");
    setLoading(true);
    try {
      const res = await askCopilot(sessionId, question);
      setMessages((m) => [...m, { role: "assistant", text: res.answer }]);
    } catch {
      setMessages((m) => [...m, { role: "assistant", text: "Couldn't reach the Copilot — confirm your analyst session is still valid." }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card className="flex h-full flex-col">
      <CardHeader><CardTitle>AI Identity Copilot</CardTitle><CardDescription>Grounded in this session&apos;s real trust score breakdown.</CardDescription></CardHeader>
      <CardContent className="flex flex-1 flex-col gap-3 overflow-hidden">
        <ScrollArea className="flex-1 pr-2">
          <div className="flex flex-col gap-3">
            {messages.map((m, i) => (
              <div key={i} className={`rounded-lg px-3 py-2 text-sm ${m.role === "user" ? "ml-8 bg-primary/15 text-foreground" : "mr-8 bg-muted text-foreground"}`}>{m.text}</div>
            ))}
            {loading && <div className="mr-8 rounded-lg bg-muted px-3 py-2 text-sm text-muted-foreground">Thinking…</div>}
          </div>
        </ScrollArea>
        <div className="flex flex-wrap gap-1.5">
          {SUGGESTED_QUESTIONS.map((q) => (
            <button key={q} onClick={() => send(q)} className="rounded-full border border-border px-2.5 py-1 text-xs text-muted-foreground transition-colors hover:border-primary hover:text-primary">{q}</button>
          ))}
        </div>
        <form onSubmit={(e) => { e.preventDefault(); send(input); }} className="flex gap-2">
          <Input value={input} onChange={(e) => setInput(e.target.value)} placeholder="Ask a question…" />
          <Button type="submit" size="icon" disabled={loading}><Send className="h-4 w-4" /></Button>
        </form>
      </CardContent>
    </Card>
  );
}

export default function SessionDetailPage() {
  const params = useParams();
  const sessionId = params.sessionId;
  const [trustResult, setTrustResult] = useState(null);
  const [trustError, setTrustError] = useState(false);
  const detail = mockSessionDetail(sessionId);

  useEffect(() => {
    computeTrustScore(sessionId).then(setTrustResult).catch(() => setTrustError(true));
  }, [sessionId]);

  return (
    <AppShell>
      <TopBar title="Session investigation" subtitle={sessionId} />
      <div className="flex-1 overflow-y-auto px-8 py-6">
        {trustError && (
          <div className="mb-4 rounded-lg border border-caution/30 bg-caution/10 px-4 py-2.5 text-xs text-caution">
            Live trust score unavailable for this session ID — showing mock evidence below. Try a real session ID from your backend testing to see this pull live.
          </div>
        )}
        <div className="mb-6 flex items-center gap-4">
          <StatusBadge status={detail.status} />
          <p className="text-sm text-muted-foreground">{new Date(detail.created_at).toLocaleString()}</p>
        </div>
        <div className="grid grid-cols-3 gap-5">
          <div className="col-span-2 flex flex-col gap-4">
            <div className="flex gap-4">
              <Card className="flex w-56 shrink-0 items-center justify-center py-6">
                <TrustGauge score={trustResult?.trust_score ?? detail.face_match.score * 100} size={180} />
              </Card>
              <div className="flex flex-1 flex-col gap-4">
                <EvidenceCard icon={FileText} title="Document integrity">
                  <p className="text-sm text-muted-foreground">{detail.document.is_forged ? "Flagged for forgery/consistency issues." : "Passed forgery and consistency checks."}</p>
                </EvidenceCard>
                <EvidenceCard icon={ScanFace} title="Face match"><SignalBar label="Similarity" value={detail.face_match.score} invert /></EvidenceCard>
              </div>
            </div>
            <EvidenceCard icon={Eye} title="Liveness">
              <p className="text-sm text-muted-foreground">{detail.liveness.passed ? `${detail.liveness.blinks_detected} blinks detected — live subject confirmed.` : "No blink detected — possible spoof."}</p>
            </EvidenceCard>
            <EvidenceCard icon={VideoOff} title="Deepfake analysis"><SignalBar label="Artifact score" value={detail.deepfake.score} /></EvidenceCard>
            <EvidenceCard icon={Mic} title="Voice authentication">
              <div className="flex flex-col gap-2">
                <SignalBar label="Speaker match" value={detail.voice.match_score} invert />
                <SignalBar label="Spoof score" value={detail.voice.spoof_score} />
              </div>
            </EvidenceCard>
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
          </div>
          <div className="col-span-1"><CopilotPanel sessionId={sessionId} /></div>
        </div>
      </div>
    </AppShell>
  );
}
