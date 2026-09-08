import { Badge } from "@/components/ui/badge";

const STATUS_MAP = {
  passed: { variant: "default", label: "Passed" },
  failed: { variant: "destructive", label: "Failed" },
  review: { variant: "caution", label: "Review" },
  pending: { variant: "outline", label: "Pending" },
};

export default function StatusBadge({ status }) {
  const cfg = STATUS_MAP[status] || STATUS_MAP.pending;
  return <Badge variant={cfg.variant}>{cfg.label}</Badge>;
}
