from sqlalchemy import select

from app.models import BudgetAccount
from app.services.budget import BudgetRejected, reconcile, reserve


def test_atomic_reservation_and_reconcile(db):
    account = db.scalar(select(BudgetAccount).where(BudgetAccount.name == "llm", BudgetAccount.period == "daily"))
    assert account is not None
    account.limit_amount = 1.0
    account.reserved = 0.0
    account.actual = 0.0
    db.flush()

    first = reserve(db, name="llm", period="daily", estimated=0.4, ceiling=0.5, purpose="test", idempotency_key="a")
    assert first.status == "reserved"
    db.refresh(account)
    assert account.reserved == 0.5

    try:
        reserve(db, name="llm", period="daily", estimated=0.6, ceiling=0.6, purpose="test", idempotency_key="b")
        raise AssertionError("should reject")
    except BudgetRejected:
        pass
    db.refresh(account)
    assert account.paused is True

    same = reserve(db, name="llm", period="daily", estimated=0.4, ceiling=0.5, purpose="test", idempotency_key="a")
    assert same.id == first.id

    account.paused = False
    reconcile(db, first, actual=0.2)
    db.refresh(account)
    assert first.status == "reconciled"
    assert account.reserved == 0.0
    assert account.actual == 0.2
    assert first.reserved == 0.5
