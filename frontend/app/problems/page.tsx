"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "@/lib/api";

export default function ProblemsPage() {
  const [q, setQ] = useState("");
  const [open, setOpen] = useState<string | null>(null);
  const { data } = useQuery({
    queryKey: ["problems", q],
    queryFn: () => api<{ items: any[] }>(`/api/problems?q=${encodeURIComponent(q)}`),
  });
  const detail = useQuery({
    queryKey: ["problem", open],
    queryFn: () => api<any>(`/api/problems/${open}`),
    enabled: !!open,
  });
  return (
    <div className="grid grid-cols-[1.2fr_1fr] gap-6">
      <div>
        <h1 className="mb-4 text-2xl font-semibold">Problem database</h1>
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search problems"
          className="mb-4 w-full rounded-md border border-line bg-ink px-3 py-2 text-sm"
        />
        <table className="w-full text-left text-sm">
          <thead className="text-muted">
            <tr>
              <th className="py-2">Problem</th>
              <th>Industry</th>
              <th>Segment</th>
              <th>Sev</th>
              <th>Evidence</th>
              <th>Trend</th>
            </tr>
          </thead>
          <tbody>
            {(data?.items || []).map((row) => (
              <tr key={row.id} className="cursor-pointer border-t border-line" onClick={() => setOpen(row.id)}>
                <td className="py-2">{row.canonical_title}</td>
                <td>{row.industry}</td>
                <td>{row.customer_segment}</td>
                <td>{row.severity_score}</td>
                <td>{row.independent_observation_count}</td>
                <td>{row.trend === "insufficient_comparable_data" ? "Insufficient comparable data" : row.trend}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="rounded-lg border border-line bg-panel p-4 text-sm">
        {!open && <div className="text-muted">Select a problem</div>}
        {detail.data && (
          <div>
            <h2 className="mb-2 text-lg">{detail.data.problem.canonical_title}</h2>
            <p className="mb-3 text-muted">{detail.data.problem.description}</p>
            <div className="mb-2">Workarounds: {(detail.data.problem.workarounds || []).join(", ") || "—"}</div>
            {(detail.data.observations || []).map((o: any) => (
              <div key={o.id} className="mb-3 border-t border-line pt-2">
                <a className="text-accent" href={o.source_url}>
                  {o.title}
                </a>
                <div className="text-muted">“{o.source_span}”</div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
