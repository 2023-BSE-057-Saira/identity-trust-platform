import { Search } from "lucide-react";
import { Input } from "@/components/ui/input";

export default function TopBar({ title, subtitle, action }) {
  return (
    <header className="flex items-center justify-between border-b border-border bg-background px-8 py-5">
      <div>
        <h1 className="text-lg font-medium text-foreground">{title}</h1>
        {subtitle && <p className="mt-0.5 text-sm text-muted-foreground">{subtitle}</p>}
      </div>
      <div className="flex items-center gap-4">
        {action}
        <div className="relative">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" strokeWidth={1.75} />
          <Input placeholder="Search session ID…" className="w-56 pl-9" />
        </div>
        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-secondary font-mono text-xs font-medium text-foreground">AN</div>
      </div>
    </header>
  );
}
