"use client";
import { useEffect, useState } from "react";
import { Users, Share2 } from "lucide-react";
import AppShell from "@/components/layout/AppShell";
import TopBar from "@/components/layout/TopBar";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { getFraudRings } from "@/lib/api";

export default function FraudRingsPage() {
  const [rings, setRings] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getFraudRings().then((data) => setRings(data.fraud_rings || [])).catch(() => setError("Couldn't load fraud rings. Confirm your account has analyst access."));
  }, []);

  return (
    <AppShell>
      <TopBar title="Fraud rings" subtitle="Accounts connected through shared devices or IP addresses" />
      <div className="flex-1 overflow-y-auto px-8 py-6">
        {error && <div className="mb-6 rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">{error}</div>}
        {rings === null && !error && <div className="grid grid-cols-2 gap-4"><Skeleton className="h-32 w-full" /><Skeleton className="h-32 w-full" /></div>}
        {rings && rings.length === 0 && (
          <Card><CardContent className="flex flex-col items-center justify-center gap-2 py-16 text-center">
            <Share2 className="h-8 w-8 text-muted-foreground" strokeWidth={1.5} />
            <p className="text-sm font-medium text-foreground">No fraud rings detected</p>
            <p className="text-xs text-muted-foreground">This is good news — no accounts are currently sharing suspicious devices or IPs.</p>
          </CardContent></Card>
        )}
        {rings && rings.length > 0 && (
          <div className="grid grid-cols-2 gap-4">
            {rings.map((ring, i) => (
              <Card key={i}>
                <CardHeader className="flex-row items-center justify-between space-y-0">
                  <div className="flex items-center gap-2"><Users className="h-4 w-4 text-destructive" strokeWidth={1.75} /><CardTitle>Ring #{i + 1}</CardTitle></div>
                  <Badge variant="destructive">{ring.ring_size} accounts</Badge>
                </CardHeader>
                <CardContent>
                  <p className="mb-2 text-xs text-muted-foreground">Connected users</p>
                  <div className="mb-3 flex flex-wrap gap-1.5">{ring.users.map((u) => <Badge key={u} variant="outline">{u.replace("user:", "")}</Badge>)}</div>
                  <p className="mb-2 text-xs text-muted-foreground">Shared fingerprints</p>
                  <div className="flex flex-wrap gap-1.5">{ring.shared_devices_or_ips.map((d) => <span key={d} className="rounded bg-muted px-2 py-0.5 font-mono text-xs text-muted-foreground">{d}</span>)}</div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </AppShell>
  );
}
