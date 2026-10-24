"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { api } from "@/lib/api";

type Dash = {
  totals: Record<string, number>;
  last_run: string | null;
  top_opportunities: Array<{
    id: string;
    working_name: string;
    target_customer: string;
    industry: string;
    observed_quality_score: number | null;
    evidence_confidence: number | null;
    founder_fit_score: number | null;
    observation_count: number;
    trend: string;
    is_provisional: boolean;
    verified: boolean;
    updated_at: string | null;
  }>;
};

export default function DashboardPage() {
  const { data } = useQuery({ queryKey: ["dashboard"], queryFn: () => api<Dash>("/api/dashboard") });
  const totals = data?.totals;
  return (
    <div>
      <h1 className="mb-6 text-2xl font-semibold">Dashboard</h1>
      <div className="mb-8 grid grid-cols-4 gap-4">
        {[
          ["Problems", totals?.problems],
          ["Opportunities", totals?.opportunities],
          ["Verified", totals?.high_priority],
          ["Reddit posts", totals?.reddit_posts],
          ["X posts", totals?.x_posts],
          ["Est. cost", totals?.estimated_cost],
          ["Last run", data?.last_run],
        ].map(([label, value]) => (
          <div key={String(label)} className="rounded-lg border border-line bg-panel p-4">
            <div className="text-xs uppercase text-muted">{label}</div>
            <div className="mt-2 text-xl">{value ?? "—"}</div>
          </div>
        ))}
      </div>
      <h2 className="mb-3 text-lg">Top startup opportunities</h2>
      <table className="w-full text-left text-sm">
        <thead className="text-muted">
          <tr>
            <th className="py-2">Rank</th>
            <th>Name</th>
            <th>Customer</th>
            <th>Industry</th>
            <th>Observed /100</th>
            <th>Confidence</th>
            <th>Founder fit</th>
            <th>Evidence</th>
            <th>Trend</th>
          </tr>
        </thead>
        <tbody>
          {(data?.top_opportunities || []).map((row, i) => (
            <tr key={row.id} className="border-t border-line">
              <td className="py-2">{i + 1}</td>
              <td>
                <Link className="text-accent" href={`/opportunities/${row.id}`}>
                  {row.working_name}
                </Link>
                {row.is_provisional && <span className="ml-2 text-xs text-amber-200">provisional</span>}
                {row.verified && <span className="ml-2 text-xs text-emerald-300">verified</span>}
              </td>
              <td>{row.target_customer}</td>
              <td>{row.industry}</td>
              <td>{row.observed_quality_score ?? "—"}</td>
              <td>{row.evidence_confidence ?? "—"}</td>
              <td>{row.founder_fit_score ?? "—"}</td>
              <td>{row.observation_count}</td>
              <td>{row.trend === "insufficient_comparable_data" ? "Insufficient comparable data" : row.trend}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
