export default function TrustGauge({ score, size = 224 }) {
  const value = score ?? 0;
  const radius = size * 0.357;
  const circumference = 2 * Math.PI * radius;
  const pct = Math.min(Math.max(value, 0), 100) / 100;
  const offset = circumference * (1 - pct * 0.75);
  const center = size / 2;
  const color = value >= 75 ? "#3fbfae" : value >= 45 ? "#e8a33d" : "#d6564b";
  const label = value >= 75 ? "low risk" : value >= 45 ? "medium risk" : "high risk";

  return (
    <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="absolute inset-0 -rotate-[135deg]">
        <circle cx={center} cy={center} r={radius} fill="none" stroke="hsl(var(--border))" strokeWidth="12"
          strokeDasharray={`${circumference * 0.75} ${circumference}`} strokeLinecap="round" />
        <circle cx={center} cy={center} r={radius} fill="none" stroke={color} strokeWidth="12"
          strokeDasharray={circumference} strokeDashoffset={offset} strokeLinecap="round"
          style={{ transition: "stroke-dashoffset 0.8s cubic-bezier(0.4,0,0.2,1), stroke 0.3s ease" }} />
      </svg>
      <div className="relative flex flex-col items-center">
        <span className="font-mono-tabular text-5xl font-medium text-foreground">{score == null ? "—" : value.toFixed(1)}</span>
        <span className="mt-1.5 text-[11px] font-medium uppercase tracking-[0.12em] text-muted-foreground">trust score</span>
        {score != null && (
          <span className="mt-3 rounded-full px-2.5 py-1 text-xs font-medium" style={{ color, backgroundColor: `${color}1A` }}>{label}</span>
        )}
      </div>
    </div>
  );
}
