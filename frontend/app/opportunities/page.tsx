"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useState } from "react";
import { api } from "@/lib/api";

export default function OpportunitiesPage() {
  const [q, setQ] = useState("");
  const [ranking, setRanking] = useState("highest_opportunity");
  const { data } = useQuery({
    queryKey: ["opps", q, ranking],
    queryFn: () => api<{ items: any[] }>(`/api/opportunities?q=${encodeURIComponent(q)}&ranking=${ranking}`),
  });
  return (
    <div>
      <h1 className="mb-4 text-2xl font-semibold">Startup opportunities</h1>
      <div className="mb-4 flex gap-3">
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search"
          className="w-72 rounded-md border border-line bg-ink px-3 py-2 text-sm"
        />
        <select
          value={ranking}
          onChange={(e) => setRanking(e.target.value)}
          className="rounded-md border border-line bg-ink px-3 py-2 text-sm"
        >
          <option value="highest_opportunity">Highest opportunity</option>
          <option value="verified">Verified only</option>
          <option value="provisional">Provisional / discoverable</option>
          <option value="highest_confidence">Highest confidence</option>
          <option value="best_founder_fit">Best founder fit</option>
          <option value="recently_discovered">Recently discovered</option>
        </select>
      </div>
      <div className="space-y-3">
        {(data?.items || []).map((item) => (
          <Link key={item.id} href={`/opportunities/${item.id}`} className="block rounded-lg border border-line bg-panel p-4">
            <div className="flex items-center justify-between">
              <div className="font-medium">{item.working_name}</div>
              <div className="text-sm text-muted">
                observed {item.observed_quality_score ?? "—"} · complete{" "}
                {item.research_completeness != null ? Math.round(item.research_completeness * 100) : "—"}% · founder{" "}
                {item.founder_fit_score ?? "—"}
              </div>
            </div>
            <div className="mt-1 text-sm text-muted">{item.one_line_pitch}</div>
            <div className="mt-2 text-xs text-muted">
              {item.industry} · {item.target_customer} · {item.is_provisional ? "provisional" : "evaluated"} ·{" "}
              {item.quality_status}
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
