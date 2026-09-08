"use client";
import { useState } from "react";
import Link from "next/link";
import { Plus } from "lucide-react";
import AppShell from "@/components/layout/AppShell";
import TopBar from "@/components/layout/TopBar";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/table";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import StatusBadge from "@/components/shared/StatusBadge";
import { mockSessionsList } from "@/lib/mockData";

export default function VerificationsPage() {
  const [statusFilter, setStatusFilter] = useState("all");
  const sessions = mockSessionsList();
  const filtered = statusFilter === "all" ? sessions : sessions.filter((s) => s.status === statusFilter);

  return (
    <AppShell>
      <TopBar
        title="Verifications"
        subtitle="All verification sessions across users"
        action={<Button asChild size="sm"><Link href="/verifications/new"><Plus className="h-4 w-4" /> New verification</Link></Button>}
      />
      <div className="flex-1 overflow-y-auto px-8 py-6">
        <div className="mb-4 rounded-lg border border-caution/30 bg-caution/10 px-4 py-2.5 text-xs text-caution">
          Showing mock data — the backend sessions-list endpoint hasn&apos;t been built yet.
        </div>
        <div className="mb-4 flex items-center gap-3">
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-40"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All statuses</SelectItem>
              <SelectItem value="passed">Passed</SelectItem>
              <SelectItem value="failed">Failed</SelectItem>
              <SelectItem value="review">Review</SelectItem>
            </SelectContent>
          </Select>
          <p className="text-sm text-muted-foreground">{filtered.length} sessions</p>
        </div>
        <Card>
          <CardContent className="p-0">
            <Table>
              <TableHeader><TableRow><TableHead>Session ID</TableHead><TableHead>User</TableHead><TableHead>Status</TableHead><TableHead className="text-right">Trust score</TableHead><TableHead className="text-right">Created</TableHead></TableRow></TableHeader>
              <TableBody>
                {filtered.map((s) => (
                  <TableRow key={s.id}>
                    <TableCell><Link href={`/verifications/${s.id}`} className="font-mono text-xs text-primary hover:underline">{s.id}</Link></TableCell>
                    <TableCell className="text-sm">{s.user_email}</TableCell>
                    <TableCell><StatusBadge status={s.status} /></TableCell>
                    <TableCell className="text-right font-mono-tabular text-sm">{s.trust_score.toFixed(1)}</TableCell>
                    <TableCell className="text-right text-xs text-muted-foreground">{new Date(s.created_at).toLocaleString()}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}
