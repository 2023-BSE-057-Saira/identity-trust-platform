"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { ShieldCheck, ScanFace, Fingerprint } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { login } from "@/lib/api";

function BrandPanel() {
  return (
    <div className="relative hidden w-[44%] flex-col justify-between overflow-hidden bg-card px-12 py-12 lg:flex">
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.06]"
        style={{ backgroundImage: "repeating-linear-gradient(0deg, #3fbfae 0px, #3fbfae 1px, transparent 1px, transparent 48px), repeating-linear-gradient(90deg, #3fbfae 0px, #3fbfae 1px, transparent 1px, transparent 48px)" }}
      />
      <div className="relative flex items-center gap-2">
        <ShieldCheck className="h-5 w-5 text-primary" strokeWidth={1.75} />
        <span className="font-mono text-sm font-medium tracking-wide text-foreground">IDENTITY TRUST</span>
      </div>
      <div className="relative">
        <h1 className="max-w-sm text-3xl font-medium leading-tight text-foreground">Every signal, verified before it&apos;s trusted.</h1>
        <p className="mt-4 max-w-xs text-sm leading-relaxed text-muted-foreground">Biometric matching, deepfake forensics, and voice authentication in one investigation console.</p>
        <div className="mt-10 flex gap-8">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-border bg-background">
              <ScanFace className="h-4 w-4 text-primary" strokeWidth={1.75} />
            </div>
            <div><p className="text-sm font-medium text-foreground">Biometric</p><p className="text-xs text-muted-foreground">face + liveness</p></div>
          </div>
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg border border-border bg-background">
              <Fingerprint className="h-4 w-4 text-primary" strokeWidth={1.75} />
            </div>
            <div><p className="text-sm font-medium text-foreground">Forensic</p><p className="text-xs text-muted-foreground">deepfake + voice</p></div>
          </div>
        </div>
      </div>
      <p className="relative font-mono text-xs text-muted-foreground">AI-236 · verification platform</p>
    </div>
  );
}

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    if (!email || !password) { setError("Enter your email and password."); return; }
    setLoading(true);
    try {
      await login(email, password);
      router.push("/");
    } catch {
      setError("Incorrect email or password.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen bg-background">
      <BrandPanel />
      <div className="flex flex-1 items-center justify-center px-6">
        <div className="w-full max-w-sm">
          <h2 className="text-xl font-medium text-foreground">Sign in</h2>
          <p className="mt-1.5 text-sm text-muted-foreground">Analyst access to the verification console.</p>
          <form onSubmit={handleSubmit} className="mt-8 flex flex-col gap-4">
            <div>
              <label className="mb-1.5 block text-sm text-muted-foreground" htmlFor="email">Email</label>
              <Input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="name@company.com" />
            </div>
            <div>
              <label className="mb-1.5 block text-sm text-muted-foreground" htmlFor="password">Password</label>
              <Input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
            </div>
            {error && <p className="text-sm text-destructive">{error}</p>}
            <Button type="submit" disabled={loading} className="mt-2">{loading ? "Signing in…" : "Sign in"}</Button>
          </form>
        </div>
      </div>
    </div>
  );
}
