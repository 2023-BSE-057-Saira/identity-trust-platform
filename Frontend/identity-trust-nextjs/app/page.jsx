"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { CheckCircle2, XCircle, Clock, VideoOff, MicOff, ArrowRight, Info } from "lucide-react";
import AppShell from "@/components/layout/AppShell";
import TopBar from "@/components/layout/TopBar";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/table";
import StatusBadge from "@/components/shared/StatusBadge";
import TrustGauge from "@/components/shared/TrustGauge";
import { getDashboardSummary, getTrustDistribution } from "@/lib/api";
import { mockSessionsList } from "@/lib/mockData";

function MetricCard({ icon: Icon, label, value, description, tone, loading }) {
  const toneColor = { primary: "#3fbfae", destructive: "#d6564b", caution: "#e8a33d", neutral: "#9ca9c2" }[tone || "neutral"];
  return (
    <Card className="flex flex-1 items-start gap-3 px-5 py-4">
      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg" style={{ backgroundColor: `${toneColor}1A` }}>
        <Icon className="h-4 w-4" style={{ color: toneColor }} strokeWidth={1.75} />
      </div>
      <div className="min-w-0">
        {loading ? <Skeleton className="h-7 w-16" /> : <p className="font-mono-tabular text-2xl font-medium text-foreground">{value}</p>}
        <p className="mt-0.5 text-xs font-medium text-foreground">{label}</p>
        {description && <p className="mt-0.5 text-[11px] leading-snug text-muted-foreground">{description}</p>}
      </div>
    </Card>
  );
}

// Bulletproof bar chart - plain divs with inline height percentages, not
// a chart library. Recharts' ResponsiveContainer needs a reliably-sized
// parent to render correctly and was producing broken output with sparse
// data - this renders identically regardless of data volume or container
// timing quirks.
const BUCKET_COLORS = { "0-25": "#d6564b", "26-50": "#e8a33d", "51-75": "#e8a33d", "76-100": "#3fbfae" };
const BUCKET_LABELS = { "0-25": "High risk", "26-50": "Medium risk", "51-75": "Medium risk", "76-100": "Low risk" };

function DistributionCard({ distribution, loading }) {
  const buckets = distribution ? Object.entries(distribution.distribution) : [];
  const isEmpty = !loading && (!distribution || distribution.total_scored_sessions === 0);
  const max = Math.max(...buckets.map(([, count]) => count), 1);

  return (
    <Card className="flex-1">
      <CardHeader>
        <CardTitle>Trust score distribution</CardTitle>
        <CardDescription>How many sessions fall into each risk tier, based on their final trust score.</CardDescription>
      </CardHeader>
      <CardContent>
        {loading ? (
          <Skeleton className="h-52 w-full" />
        ) : isEmpty ? (
          <div className="flex h-52 flex-col items-center justify-center gap-1.5 text-center">
            <p className="text-sm text-foreground">No scored sessions yet.</p>
            <p className="text-xs text-muted-foreground">This fills in as more verifications complete - right now there&apos;s only 1 real session in the system.</p>
          </div>
        ) : (
          <div className="flex h-52 items-end gap-6 px-2">
            {buckets.map(([range, count]) => (
              <div key={range} className="flex flex-1 flex-col items-center gap-2">
                <span className="font-mono-tabular text-sm font-medium text-foreground">{count}</span>
                <div className="flex w-full flex-1 items-end">
                  <div
                    className="w-full rounded-t-md transition-all"
                    style={{
                      height: count > 0 ? `${Math.max((count / max) * 100, 6)}%` : "2px",
                      backgroundColor: count > 0 ? BUCKET_COLORS[range] : "hsl(var(--border))",
                    }}
                  />
                </div>
                <div className="text-center">
                  <p className="font-mono text-xs text-muted-foreground">{range}</p>
                  <p className="text-[10px] text-muted-foreground">{BUCKET_LABELS[range]}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function RecentSessions() {
  const sessions = mockSessionsList().slice(0, 5);
  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <div>
          <CardTitle>Recent sessions</CardTitle>
          <CardDescription>The latest verification attempts, most recent first. (Mock data — sessions list endpoint not built yet.)</CardDescription>
        </div>
        <Link href="/verifications" className="flex items-center gap-1 text-xs font-medium text-primary hover:underline">View all <ArrowRight className="h-3 w-3" /></Link>
      </CardHeader>
      <CardContent className="px-0 pb-0">
        <Table>
          <TableHeader><TableRow><TableHead>Session</TableHead><TableHead>User</TableHead><TableHead>Status</TableHead><TableHead className="text-right">Trust score</TableHead></TableRow></TableHeader>
          <TableBody>
            {sessions.map((s) => (
              <TableRow key={s.id}>
                <TableCell><Link href={`/verifications/${s.id}`} className="font-mono text-xs text-primary hover:underline">{s.id.slice(0, 8)}…</Link></TableCell>
                <TableCell className="text-sm">{s.user_email}</TableCell>
                <TableCell><StatusBadge status={s.status} /></TableCell>
                <TableCell className="text-right font-mono-tabular text-sm">{s.trust_score.toFixed(1)}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}

export default function DashboardPage() {
  const [summary, setSummary] = useState(null);
  const [distribution, setDistribution] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([getDashboardSummary(), getTrustDistribution()])
      .then(([s, d]) => { setSummary(s); setDistribution(d); })
      .catch(() => setError("Couldn't load dashboard data. Confirm your account has analyst access."))
      .finally(() => setLoading(false));
  }, []);

  return (
    <AppShell>
      <TopBar title="Dashboard" subtitle="Verification activity across all sessions" />
      <div className="flex-1 overflow-y-auto px-8 py-6">
        <div className="mb-6 flex items-start gap-2 rounded-lg border border-border bg-card/50 px-4 py-3">
          <Info className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" strokeWidth={1.75} />
          <p className="text-xs leading-relaxed text-muted-foreground">
            This is the analyst&apos;s starting point — a system-wide snapshot of every identity verification session.
            Use it to spot rising fraud activity, confirm the platform is behaving as expected, and jump into specific
            sessions or alerts that need attention. With only 1 real session recorded so far, most numbers below will
            look sparse until more verifications run.
          </p>
        </div>

        {error && <div className="mb-6 rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">{error}</div>}

        <div className="mb-6 flex gap-5">
          <Card className="flex w-64 shrink-0 flex-col items-center justify-center gap-1 py-8">
            <TrustGauge score={summary?.average_trust_score} />
            <p className="mt-2 max-w-[180px] text-center text-[11px] leading-snug text-muted-foreground">Average across every scored session. Higher is better.</p>
          </Card>
          <div className="grid flex-1 grid-cols-2 gap-4">
            <MetricCard icon={CheckCircle2} label="Passed" description="Sessions that cleared every check." value={summary?.passed} tone="primary" loading={loading} />
            <MetricCard icon={XCircle} label="Failed" description="Sessions rejected by one or more checks." value={summary?.failed} tone="destructive" loading={loading} />
            <MetricCard icon={Clock} label="Under review" description="Borderline sessions needing analyst judgment." value={summary?.under_review} tone="caution" loading={loading} />
            <MetricCard icon={CheckCircle2} label="Success rate" description="Share of sessions that passed." value={summary ? `${summary.verification_success_rate}%` : null} tone="neutral" loading={loading} />
          </div>
        </div>

        <div className="mb-6 flex gap-4">
          <MetricCard icon={VideoOff} label="Deepfake alerts" description="Sessions where video showed manipulation signs." value={summary?.deepfake_alerts} tone="destructive" loading={loading} />
          <MetricCard icon={MicOff} label="Voice spoof alerts" description="Sessions where audio looked synthetic or replayed." value={summary?.voice_spoof_alerts} tone="destructive" loading={loading} />
          <MetricCard icon={CheckCircle2} label="Total sessions" description="Every verification attempt on record." value={summary?.total_sessions} tone="neutral" loading={loading} />
        </div>

        <div className="mb-6"><DistributionCard distribution={distribution} loading={loading} /></div>

        <RecentSessions />
      </div>
    </AppShell>
  );
}
