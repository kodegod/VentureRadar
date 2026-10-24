"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  ["/", "Dashboard"],
  ["/opportunities", "Opportunities"],
  ["/problems", "Problems"],
  ["/research", "Research"],
  ["/settings", "Settings"],
];

export function Shell({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  return (
    <div className="min-h-screen grid grid-cols-[220px_1fr]">
      <aside className="border-r border-line bg-panel px-4 py-6">
        <div className="mb-8 text-sm font-semibold tracking-wide">VentureRadar</div>
        <nav className="space-y-1 text-sm">
          {links.map(([href, label]) => (
            <Link
              key={href}
              href={href}
              className={`block rounded-md px-3 py-2 ${path === href ? "bg-white/10 text-white" : "text-muted hover:bg-white/5"}`}
            >
              {label}
            </Link>
          ))}
        </nav>
      </aside>
      <main className="px-8 py-6">
        <div className="mb-6 rounded-md border border-amber-500/40 bg-amber-500/10 px-4 py-3 text-sm text-amber-100">
          Synthetic research mode. Live social-media collection is not operational. Benchmarks are
          dataset=synthetic_labeled, not real-world model performance.
        </div>
        {children}
      </main>
    </div>
  );
}
