"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { LayoutDashboard, ShieldCheck, Share2, MessageSquareText, ShieldAlert, LogOut } from "lucide-react";
import { cn } from "@/lib/utils";
import { logout } from "@/lib/api";

const NAV_ITEMS = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/verifications", label: "Verifications", icon: ShieldCheck },
  { href: "/fraud-rings", label: "Fraud rings", icon: Share2 },
  { href: "/alerts", label: "Alert center", icon: ShieldAlert },
  { href: "/copilot", label: "Copilot", icon: MessageSquareText },
];

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();

  return (
    <aside className="flex h-screen w-60 shrink-0 flex-col border-r border-border bg-card px-3 py-5">
      <div className="mb-8 flex items-center gap-2 px-3">
        <ShieldCheck className="h-[18px] w-[18px] text-primary" strokeWidth={1.75} />
        <div>
          <p className="font-mono text-[13px] font-medium tracking-wide text-foreground">IDENTITY TRUST</p>
          <p className="text-[11px] text-muted-foreground">analyst console</p>
        </div>
      </div>
      <nav className="flex flex-1 flex-col gap-0.5">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "group relative flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm transition-colors",
                isActive ? "bg-secondary text-foreground" : "text-muted-foreground hover:bg-secondary/60 hover:text-foreground"
              )}
            >
              {isActive && <span className="absolute -left-3 top-1/2 h-4 w-0.5 -translate-y-1/2 rounded-full bg-primary" />}
              <Icon className="h-4 w-4" strokeWidth={1.75} />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>
      <button
        onClick={() => { logout(); router.push("/login"); }}
        className="flex items-center gap-2.5 rounded-lg px-3 py-2 text-left text-sm text-muted-foreground transition-colors hover:bg-secondary/60 hover:text-foreground"
      >
        <LogOut className="h-4 w-4" strokeWidth={1.75} />
        Sign out
      </button>
    </aside>
  );
}
