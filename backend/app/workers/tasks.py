from __future__ import annotations

from sqlalchemy import select

from app.database import SessionLocal
from app.models import PlatformRetentionPolicy, SourcePost
from app.services.bootstrap import bootstrap
from app.services.pipeline import run_full_pipeline
from app.services.provenance import tombstone_source_post
from app.services.trends import refresh_cluster_trends
from app.workers.celery_app import celery_app


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 5})
def run_pipeline_task(self):
    db = SessionLocal()
    try:
        bootstrap(db)
        run = run_full_pipeline(db, trigger="beat")
        db.commit()
        return {"run_id": str(run.id), "status": run.status}
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@celery_app.task
def refresh_trends_task():
    db = SessionLocal()
    try:
        refresh_cluster_trends(db)
        db.commit()
    finally:
        db.close()


@celery_app.task
def retention_pass_task():
    """Honor platform_retention_policies. No hardcoded universal TTL."""
    db = SessionLocal()
    try:
        policies = db.scalars(select(PlatformRetentionPolicy)).all()
        delete_on_source = any(p.rule_type == "delete_on_source_deletion" and p.platform != "synthetic" for p in policies)
        if delete_on_source:
            flagged = db.scalars(
                select(SourcePost).where(SourcePost.deletion_reason == "source_deleted_pending")
            ).all()
            for post in flagged:
                tombstone_source_post(db, post, "source_deleted")
        db.commit()
    finally:
        db.close()
