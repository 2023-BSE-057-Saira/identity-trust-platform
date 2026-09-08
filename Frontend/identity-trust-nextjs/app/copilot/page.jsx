"use client";
import { useState } from "react";
import { Send, MessageSquareText } from "lucide-react";
import AppShell from "@/components/layout/AppShell";
import TopBar from "@/components/layout/TopBar";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { ScrollArea } from "@/components/ui/scroll-area";
import { askCopilot } from "@/lib/api";
import { mockSessionsList } from "@/lib/mockData";

const SUGGESTED_QUESTIONS = ["Why did verification fail?", "Explain the fraud indicators.", "Compare this face with previous records.", "Show deepfake probability.", "Generate investigation summary.", "Recommend verification action."];

export default function CopilotPage() {
  const sessions = mockSessionsList();
  const [sessionId, setSessionId] = useState(sessions[0].id);
  const [messages, setMessages] = useState([]);
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
      setMessages((m) => [...m, { role: "assistant", text: "Couldn't reach the Copilot for this session." }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <AppShell>
      <TopBar title="AI Identity Copilot" subtitle="Ask questions grounded in a session's trust score breakdown" />
      <div className="flex flex-1 flex-col overflow-hidden px-8 py-6">
        <div className="mb-4 flex items-center gap-3">
          <p className="text-sm text-muted-foreground">Session:</p>
          <Select value={sessionId} onValueChange={setSessionId}>
            <SelectTrigger className="w-72"><SelectValue /></SelectTrigger>
            <SelectContent>{sessions.map((s) => <SelectItem key={s.id} value={s.id}>{s.user_email} — {s.id.slice(0, 8)}…</SelectItem>)}</SelectContent>
          </Select>
        </div>
        <Card className="flex flex-1 flex-col overflow-hidden">
          <CardContent className="flex flex-1 flex-col gap-4 overflow-hidden pt-5">
            <ScrollArea className="flex-1">
              {messages.length === 0 ? (
                <div className="flex h-full flex-col items-center justify-center gap-2 text-center">
                  <MessageSquareText className="h-8 w-8 text-muted-foreground" strokeWidth={1.5} />
                  <p className="text-sm text-muted-foreground">Pick a suggested question below, or ask your own.</p>
                </div>
              ) : (
                <div className="flex flex-col gap-3 pr-2">
                  {messages.map((m, i) => (
                    <div key={i} className={`max-w-[70%] rounded-lg px-4 py-2.5 text-sm ${m.role === "user" ? "ml-auto bg-primary/15 text-foreground" : "bg-muted text-foreground"}`}>{m.text}</div>
                  ))}
                  {loading && <div className="max-w-[70%] rounded-lg bg-muted px-4 py-2.5 text-sm text-muted-foreground">Thinking…</div>}
                </div>
              )}
            </ScrollArea>
            <div className="flex flex-wrap gap-1.5">
              {SUGGESTED_QUESTIONS.map((q) => (
                <button key={q} onClick={() => send(q)} className="rounded-full border border-border px-2.5 py-1 text-xs text-muted-foreground transition-colors hover:border-primary hover:text-primary">{q}</button>
              ))}
            </div>
            <form onSubmit={(e) => { e.preventDefault(); send(input); }} className="flex gap-2">
              <Input value={input} onChange={(e) => setInput(e.target.value)} placeholder="Ask a question about this session…" />
              <Button type="submit" size="icon" disabled={loading}><Send className="h-4 w-4" /></Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}
