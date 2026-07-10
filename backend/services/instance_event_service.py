import sys

from core.unit_of_work import UnitOfWork
from models.instance_event import InstanceEvent
from schemas.instance_event import InstanceEventResponse


async def record_event(
    uow: UnitOfWork, instance_id: int, severity: str, message: str
) -> None:
    try:
        event = InstanceEvent(
            instance_id=instance_id, severity=severity, message=message[:255]
        )
        await uow.instance_events.add(event)
        await uow.commit()
    except Exception as exc:  # pragma: no cover - logging must not break the request
        print(f"[record_event] failed: {exc}", file=sys.stderr)
        try:
            await uow.rollback()
        except Exception:
            pass


async def list_events(
    uow: UnitOfWork, instance_id: int, limit: int = 100
) -> list[InstanceEventResponse]:
    limit = max(1, min(limit, 200))
    rows = await uow.instance_events.get_by_instance(instance_id, limit=limit)
    return [InstanceEventResponse.model_validate(r) for r in rows]
