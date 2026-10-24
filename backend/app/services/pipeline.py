from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, TypedDict
import uuid

from langgraph.graph import END, START, StateGraph
from sqlalchemy.orm import Session

from app.agents.clustering import run_clustering
from app.agents.discovery import run_discovery
from app.agents.extraction import run_extraction
from app.agents.opportunity import run_opportunity
from app.agents.quality import run_quality
from app.models import ResearchRun
from app.services.bootstrap import is_paused


class PipelineState(TypedDict, total=False):
    run_id: str
    discovery: dict[str, Any]
    extraction: dict[str, Any]
    clustering: dict[str, Any]
    opportunity: dict[str, Any]
    quality: dict[str, Any]


def compile_pipeline(db: Session):
    graph = StateGraph(PipelineState)

    def discovery(state: PipelineState) -> PipelineState:
        return {**state, "discovery": run_discovery(db, uuid.UUID(state["run_id"]))}

    def extraction(state: PipelineState) -> PipelineState:
        return {**state, "extraction": run_extraction(db, uuid.UUID(state["run_id"]))}

    def clustering(state: PipelineState) -> PipelineState:
        return {**state, "clustering": run_clustering(db, uuid.UUID(state["run_id"]))}

    def opportunity(state: PipelineState) -> PipelineState:
        return {**state, "opportunity": run_opportunity(db, uuid.UUID(state["run_id"]))}

    def quality(state: PipelineState) -> PipelineState:
        return {**state, "quality": run_quality(db, uuid.UUID(state["run_id"]))}

    graph.add_node("discovery", discovery)
    graph.add_node("extraction", extraction)
    graph.add_node("clustering", clustering)
    graph.add_node("opportunity", opportunity)
    graph.add_node("quality", quality)
    graph.add_edge(START, "discovery")
    graph.add_edge("discovery", "extraction")
    graph.add_edge("extraction", "clustering")
    graph.add_edge("clustering", "opportunity")
    graph.add_edge("opportunity", "quality")
    graph.add_edge("quality", END)
    return graph.compile()


def run_full_pipeline(db: Session, trigger: str = "manual") -> ResearchRun:
    if is_paused(db):
        run = ResearchRun(status="paused", trigger=trigger, data_origin="synthetic")
        db.add(run)
        db.flush()
        return run

    run = ResearchRun(status="running", trigger=trigger, data_origin="synthetic")
    db.add(run)
    db.flush()
    try:
        graph = compile_pipeline(db)
        state = graph.invoke({"run_id": str(run.id)})
        run.stats = {
            "discovery": state.get("discovery") or {},
            "extraction": state.get("extraction") or {},
            "clustering": state.get("clustering") or {},
            "opportunity": state.get("opportunity") or {},
            "quality": state.get("quality") or {},
            "dataset": "synthetic_labeled",
        }
        run.status = "completed"
        run.finished_at = datetime.now(timezone.utc)
        db.flush()
        return run
    except Exception as exc:
        run.status = "failed"
        run.error = str(exc)
        run.finished_at = datetime.now(timezone.utc)
        db.flush()
        raise
