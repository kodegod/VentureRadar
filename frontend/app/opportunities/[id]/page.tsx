"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "@/lib/api";

export default function OpportunityDetailPage() {
  const params = useParams<{ id: string }>();
  const { data } = useQuery({
    queryKey: ["opp", params.id],
    queryFn: () => api<any>(`/api/opportunities/${params.id}`),
  });
  const o = data?.opportunity;
  if (!o) return <div>Loading…</div>;
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">{o.working_name}</h1>
        <p className="text-muted">{o.one_line_pitch}</p>
      </div>
      <div className="grid grid-cols-4 gap-3">
        <Metric label="Observed quality" value={o.observed_quality_score} />
        <Metric label="Research completeness" value={o.research_completeness != null ? `${Math.round(o.research_completeness * 100)}%` : "—"} />
        <Metric label="Conservative heuristic" value={o.conservative_score} hint="Heuristic, not a statistical lower bound" />
        <Metric label="Founder fit (separate)" value={o.founder_fit_score} />
      </div>
      <Section title="Concept">{o.description}</Section>
      <Section title="Target customer">{o.target_customer}</Section>
      <Section title="Problem">{o.customer_problem}</Section>
      <Section title="Solution">{o.proposed_solution}</Section>
      <Section title="Business model">
        {o.business_model}. Pricing: {o.pricing_approach}
      </Section>
      <Section title="MVP">{JSON.stringify(o.mvp, null, 2)}</Section>
      <Section title="Evidence">
        {(data.evidence || []).map((e: any, i: number) => (
          <div key={i} className="mb-2 text-sm">
            <a className="text-accent" href={e.source_url} target="_blank">
              {e.claim}
            </a>
            <div className="text-muted">“{e.quote}”</div>
            <div className="text-xs text-muted">
              {e.evidence_level} · {e.polarity}
            </div>
          </div>
        ))}
      </Section>
      <Section title="Existing solutions / competitors">
        {(data.competitors || []).map((c: any, i: number) => (
          <div key={i} className="mb-2 text-sm">
            <div>
              {c.name} · {c.status}
            </div>
            <div className="text-muted">{c.notes}</div>
            {c.source_url && (
              <a className="text-accent" href={c.source_url}>
                {c.source_url}
              </a>
            )}
          </div>
        ))}
      </Section>
      <Section title="Score breakdown">
        {(data.factors || []).map((f: any) => (
          <div key={f.criterion} className="mb-3 border-b border-line pb-2 text-sm">
            <div className="font-medium">
              {f.criterion} · {f.status} · {f.score ?? "not researched / unknown"}
            </div>
            <div className="text-muted">{f.explanation}</div>
          </div>
        ))}
      </Section>
      <Section title="Skeptical analysis">
        <div>Status: {data.audit?.status}</div>
        <ul className="list-disc pl-5 text-sm text-muted">
          {(data.audit?.arguments_against || []).map((x: string) => (
            <li key={x}>{x}</li>
          ))}
        </ul>
      </Section>
      <Section title="Risks and experiments">
        <ul className="list-disc pl-5 text-sm">
          {(data.audit?.risks || []).map((x: string) => (
            <li key={x}>{x}</li>
          ))}
        </ul>
        <ul className="mt-2 list-disc pl-5 text-sm text-muted">
          {(data.audit?.validation_experiments || []).map((x: string) => (
            <li key={x}>{x}</li>
          ))}
        </ul>
      </Section>
      <Section title="Score history">
        <div className="h-48">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data.score_history || []}>
              <XAxis dataKey="created_at" hide />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="observed_quality_score" stroke="#7c9cff" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </Section>
    </div>
  );
}

function Metric({ label, value, hint }: { label: string; value: any; hint?: string }) {
  return (
    <div className="rounded-lg border border-line bg-panel p-3">
      <div className="text-xs text-muted">{label}</div>
      <div className="text-xl">{value ?? "—"}</div>
      {hint && <div className="text-xs text-muted">{hint}</div>}
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-lg border border-line bg-panel p-4">
      <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-muted">{title}</h2>
      <div className="whitespace-pre-wrap text-sm">{children}</div>
    </section>
  );
}
