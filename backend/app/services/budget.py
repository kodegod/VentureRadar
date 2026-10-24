from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models import BudgetAccount, BudgetReservation


class BudgetRejected(Exception):
    pass


def remaining(account: BudgetAccount) -> float:
    return float(account.limit_amount) - float(account.reserved) - float(account.actual)


def reserve(
    db: Session,
    *,
    name: str,
    period: str,
    estimated: float,
    ceiling: float,
    purpose: str,
    idempotency_key: str,
) -> BudgetReservation:
    existing = db.scalar(select(BudgetReservation).where(BudgetReservation.idempotency_key == idempotency_key))
    if existing:
        return existing

    account = db.scalar(select(BudgetAccount).where(BudgetAccount.name == name, BudgetAccount.period == period))
    if account is None:
        raise BudgetRejected(f"missing budget account {name}/{period}")
    if account.paused:
        raise BudgetRejected(f"budget class {name} is paused")

    reserved_amount = max(float(estimated), float(ceiling))
    result = db.execute(
        update(BudgetAccount)
        .where(BudgetAccount.id == account.id)
        .where(BudgetAccount.paused.is_(False))
        .where(BudgetAccount.limit_amount - BudgetAccount.reserved - BudgetAccount.actual >= reserved_amount)
        .values(reserved=BudgetAccount.reserved + reserved_amount)
        .returning(BudgetAccount.id)
    )
    row = result.first()
    if row is None:
        account.paused = True
        db.flush()
        raise BudgetRejected(f"insufficient {name} {period} budget for ceiling {reserved_amount}")

    reservation = BudgetReservation(
        id=uuid.uuid4(),
        account_id=account.id,
        idempotency_key=idempotency_key,
        estimated=float(estimated),
        reserved=reserved_amount,
        status="reserved",
        purpose=purpose,
    )
    db.add(reservation)
    db.flush()
    return reservation


def reconcile(db: Session, reservation: BudgetReservation, actual: float, provider_billed: float | None = None) -> None:
    """Move reserved → actual. Provider invoices may arrive later; this is not an exact-spend guarantee."""
    if reservation.status == "reconciled":
        return
    actual = float(actual)
    db.execute(
        update(BudgetAccount)
        .where(BudgetAccount.id == reservation.account_id)
        .values(
            reserved=BudgetAccount.reserved - reservation.reserved,
            actual=BudgetAccount.actual + actual,
            provider_billed=provider_billed,
        )
    )
    reservation.actual = actual
    reservation.provider_billed = provider_billed
    reservation.status = "reconciled"
    db.flush()


def release(db: Session, reservation: BudgetReservation) -> None:
    if reservation.status != "reserved":
        return
    db.execute(
        update(BudgetAccount)
        .where(BudgetAccount.id == reservation.account_id)
        .values(reserved=BudgetAccount.reserved - reservation.reserved)
    )
    reservation.status = "released"
    db.flush()


def reset_period_if_needed(db: Session, account: BudgetAccount, now: datetime | None = None) -> None:
    now = now or datetime.now(timezone.utc)
    start = account.period_start
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    elapsed = (now - start).total_seconds()
    limit = 86400 if account.period == "daily" else 86400 * 30
    if elapsed >= limit:
        account.reserved = 0.0
        account.actual = 0.0
        account.provider_billed = None
        account.period_start = now
        account.paused = False
        db.flush()
