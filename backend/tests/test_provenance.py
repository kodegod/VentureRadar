from sqlalchemy import select

from app.models import SourcePost
from app.services.pipeline import run_full_pipeline
from app.services.provenance import tombstone_source_post


def test_deletion_wipes_source_and_marks_derived(db):
    run_full_pipeline(db, trigger="test")
    post = db.scalars(select(SourcePost).where(SourcePost.deleted_at.is_(None))).first()
    assert post is not None
    tombstone_source_post(db, post, "source_deleted")
    db.refresh(post)
    assert post.deleted_at is not None
    assert post.title is None
    assert post.body is None
    assert post.author_fingerprint is None
