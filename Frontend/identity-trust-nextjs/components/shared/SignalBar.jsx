export default function SignalBar({ label, value, invert = false }) {
  const pct = Math.min(Math.max(value ?? 0, 0), 1) * 100;
  const good = invert ? pct > 60 : pct < 40;
  const bad = invert ? pct < 40 : pct > 60;
  const color = bad ? "#d6564b" : good ? "#3fbfae" : "#e8a33d";

  return (
    <div className="flex items-center gap-3">
      <span className="w-40 shrink-0 text-sm text-muted-foreground">{label}</span>
      <div className="h-1.5 flex-1 overflow-hidden rounded-sm bg-muted">
        <div className="h-full rounded-sm" style={{ width: `${pct}%`, backgroundColor: color, transition: "width 0.4s ease" }} />
      </div>
      <span className="w-12 shrink-0 text-right font-mono-tabular text-sm text-foreground">{value == null ? "—" : value.toFixed(2)}</span>
    </div>
  );
}
