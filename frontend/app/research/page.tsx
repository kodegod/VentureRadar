"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

export default function ResearchPage() {
  const qc = useQueryClient();
  const { data } = useQuery({ queryKey: ["ops"], queryFn: () => api<any>("/api/research/ops") });
  const run = useMutation({
    mutationFn: () => api("/api/research/run", { method: "POST" }),
    onSuccess: () => qc.invalidateQueries(),
  });
  const pause = useMutation({
    mutationFn: () => api("/api/research/pause", { method: "POST" }),
    onSuccess: () => qc.invalidateQueries(),
  });
  const resume = useMutation({
    mutationFn: () => api("/api/research/resume", { method: "POST" }),
    onSuccess: () => qc.invalidateQueries(),
  });
  return (
    <div>
      <h1 className="mb-2 text-2xl font-semibold">Research operations</h1>
      <p className="mb-6 text-sm text-muted">{data?.banner}</p>
      <div className="mb-6 flex gap-3">
        <button className="rounded-md bg-accent px-3 py-2 text-sm text-black" onClick={() => run.mutate()}>
          Run synthetic pipeline
        </button>
        <button className="rounded-md border border-line px-3 py-2 text-sm" onClick={() => pause.mutate()}>
          Pause
        </button>
        <button className="rounded-md border border-line px-3 py-2 text-sm" onClick={() => resume.mutate()}>
          Resume
        </button>
        <span className="self-center text-sm text-muted">{data?.paused ? "Paused" : "Active"}</span>
      </div>
      <div className="grid grid-cols-5 gap-3">
        {Object.entries(data?.agents || {}).map(([name, agent]: any) => (
          <div key={name} className="rounded-lg border border-line bg-panel p-3 text-sm">
            <div className="font-medium capitalize">{name}</div>
            <div className="text-muted">{agent.status}</div>
            <div className="text-xs text-muted">last {agent.last_run || "—"}</div>
            <div className="text-xs text-muted">tasks {agent.completed_tasks}</div>
            <div className="text-xs text-muted">errors {agent.errors}</div>
            <div className="text-xs text-muted">tokens {agent.tokens_used}</div>
          </div>
        ))}
      </div>
      <h2 className="mb-2 mt-8 text-lg">Job queue</h2>
      <ul className="text-sm text-muted">
        {(data?.jobs || []).map((j: any) => (
          <li key={j.id}>
            {j.job_type} · {j.status}
          </li>
        ))}
      </ul>
      <h2 className="mb-2 mt-6 text-lg">History</h2>
      <ul className="text-sm text-muted">
        {(data?.history || []).map((r: any) => (
          <li key={r.id}>
            {r.status} · {r.trigger} · {r.finished_at || "running"}
          </li>
        ))}
      </ul>
      <div className="mt-6 text-sm">
        Source APIs: Reddit {data?.source_api?.reddit} · X {data?.source_api?.x} · Tavily {data?.source_api?.tavily}
      </div>
    </div>
  );
}
