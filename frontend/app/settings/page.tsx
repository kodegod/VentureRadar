"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export default function SettingsPage() {
  const { data } = useQuery({ queryKey: ["settings"], queryFn: () => api<any>("/api/settings") });
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Settings</h1>
      <p className="text-sm text-muted">{data?.note}</p>
      <section className="rounded-lg border border-line bg-panel p-4 text-sm">
        <h2 className="mb-2 font-medium">Connector status</h2>
        <div>Live collection operational: {String(data?.live_collection_operational)}</div>
        <div>Reddit credentials present: {String(data?.credentials_configured?.reddit)} (connector disabled)</div>
        <div>X credentials present: {String(data?.credentials_configured?.x)} (connector disabled)</div>
        <div>LLM key present: {String(data?.credentials_configured?.llm)}</div>
        <div>Tavily key present: {String(data?.credentials_configured?.tavily)}</div>
      </section>
      <section className="rounded-lg border border-line bg-panel p-4 text-sm">
        <h2 className="mb-2 font-medium">Founder profile</h2>
        <div>{data?.founder_profile?.background}</div>
        <div>Skills: {(data?.founder_profile?.skills || []).join(", ")}</div>
        <div>Location: {data?.founder_profile?.location}</div>
      </section>
      <section className="rounded-lg border border-line bg-panel p-4 text-sm">
        <h2 className="mb-2 font-medium">Budgets (estimated / reserved / actual — not provider invoices)</h2>
        {(data?.budgets || []).map((b: any) => (
          <div key={`${b.name}-${b.period}`}>
            {b.name} {b.period}: limit {b.limit_amount} reserved {b.reserved} actual {b.actual}
          </div>
        ))}
      </section>
      <section className="rounded-lg border border-line bg-panel p-4 text-sm">
        <h2 className="mb-2 font-medium">Search queries</h2>
        {(data?.search_queries || []).map((q: any) => (
          <div key={q.id}>
            {q.platform} · {q.community || "global"} · {q.query}
          </div>
        ))}
      </section>
      <section className="rounded-lg border border-line bg-panel p-4 text-sm">
        <h2 className="mb-2 font-medium">Retention policies (confirm against your access agreement)</h2>
        {(data?.retention_policies || []).map((p: any) => (
          <div key={p.rule_type + p.platform} className="mb-2">
            <div className="font-medium">
              {p.platform} · {p.rule_type} · {p.value}
            </div>
            <div className="text-muted">{p.source_of_rule}</div>
          </div>
        ))}
      </section>
    </div>
  );
}
