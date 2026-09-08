"use client";
import Link from "next/link";
import { VideoOff, Mic, ShieldAlert, FileWarning } from "lucide-react";
import AppShell from "@/components/layout/AppShell";
import TopBar from "@/components/layout/TopBar";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { mockAlerts } from "@/lib/mockData";

const TYPE_ICON = { deepfake_detected: VideoOff, voice_clone_attempt: Mic, device_anomaly: ShieldAlert, fake_document: FileWarning };

export default function AlertsPage() {
  const alerts = mockAlerts();
  return (
    <AppShell>
      <TopBar title="Alert center" subtitle="Flagged sessions requiring analyst attention" />
      <div className="flex-1 overflow-y-auto px-8 py-6">
        <div className="mb-4 rounded-lg border border-caution/30 bg-caution/10 px-4 py-2.5 text-xs text-caution">
          Showing mock data — the backend alerts endpoint hasn&apos;t been built yet.
        </div>
        <div className="flex flex-col gap-2">
          {alerts.map((alert) => {
            const Icon = TYPE_ICON[alert.type] || ShieldAlert;
            return (
              <Card key={alert.id}>
                <CardContent className="flex items-center gap-4 px-5 py-4">
                  <div className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ${alert.severity === "high" ? "bg-destructive/15" : "bg-caution/15"}`}>
                    <Icon className={`h-4 w-4 ${alert.severity === "high" ? "text-destructive" : "text-caution"}`} strokeWidth={1.75} />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm text-foreground">{alert.description}</p>
                    <Link href={`/verifications/${alert.session_id}`} className="font-mono text-xs text-primary hover:underline">{alert.session_id.slice(0, 8)}…</Link>
                  </div>
                  <Badge variant={alert.severity === "high" ? "destructive" : "caution"}>{alert.severity}</Badge>
                  <p className="w-32 shrink-0 text-right text-xs text-muted-foreground">{new Date(alert.created_at).toLocaleString()}</p>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>
    </AppShell>
  );
}
