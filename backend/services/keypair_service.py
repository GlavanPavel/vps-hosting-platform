import hashlib
import base64
from fastapi import HTTPException
from core.unit_of_work import UnitOfWork
from models.keypair import Keypair
from schemas.keypair import KeypairCreate, KeypairResponse


def _fingerprint(public_key: str) -> str:
    """Compute SHA-256 fingerprint of an OpenSSH public key."""
    key_part = public_key.strip().split()[1]
    raw = base64.b64decode(key_part)
    digest = hashlib.sha256(raw).digest()
    return "SHA256:" + base64.b64encode(digest).rstrip(b"=").decode()


async def create_keypair(uow: UnitOfWork, data: KeypairCreate, user_id: int) -> KeypairResponse:
    existing = await uow.keypairs.get_by_name_and_user(data.name, user_id)
    if existing:
        raise HTTPException(status_code=409, detail="A keypair with this name already exists")

    try:
        fingerprint = _fingerprint(data.public_key)
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid public key format")

    keypair = Keypair(
        user_id=user_id,
        name=data.name,
        public_key=data.public_key,
        fingerprint=fingerprint,
    )
    await uow.keypairs.add(keypair)
    await uow.commit()
    await uow.refresh(keypair)
    return KeypairResponse.model_validate(keypair)


async def list_keypairs(uow: UnitOfWork, user_id: int) -> list[KeypairResponse]:
    keypairs = await uow.keypairs.get_by_user(user_id)
    return [KeypairResponse.model_validate(kp) for kp in keypairs]


async def delete_keypair(uow: UnitOfWork, keypair_id: int, user_id: int) -> dict:
    keypair = await uow.keypairs.get_by_id_and_user(keypair_id, user_id)
    if not keypair:
        raise HTTPException(status_code=404, detail="Keypair not found")
    await uow.keypairs.delete(keypair)
    await uow.commit()
    return {"message": "Keypair deleted"}
