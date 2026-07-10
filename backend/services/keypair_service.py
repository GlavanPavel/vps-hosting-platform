import hashlib
import base64
from fastapi import HTTPException
from cryptography.hazmat.primitives.asymmetric import ed25519, rsa
from cryptography.hazmat.primitives import serialization
from core.unit_of_work import UnitOfWork
from models.keypair import Keypair
from schemas.keypair import (
    KeypairCreate,
    KeypairGenerate,
    KeypairResponse,
    KeypairGenerateResponse,
)
from domain.events import KeypairCreated, KeypairDeletionRequested
from domain.dispatcher import dispatch


def _fingerprint(public_key: str) -> str:
    key_part = public_key.strip().split()[1]
    raw = base64.b64decode(key_part)
    digest = hashlib.sha256(raw).digest()
    return "SHA256:" + base64.b64encode(digest).rstrip(b"=").decode()


def _generate_openssh_keypair(key_type: str, comment: str) -> tuple[str, str]:
    if key_type == "rsa":
        private = rsa.generate_private_key(public_exponent=65537, key_size=4096)
    else:
        private = ed25519.Ed25519PrivateKey.generate()

    private_pem = private.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.OpenSSH,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()

    public_openssh = private.public_key().public_bytes(
        encoding=serialization.Encoding.OpenSSH,
        format=serialization.PublicFormat.OpenSSH,
    ).decode()
    if comment:
        public_openssh = f"{public_openssh} {comment}"

    return public_openssh, private_pem


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

    dispatch(KeypairCreated(
        keypair_id=keypair.id,
        name=keypair.name,
        public_key=keypair.public_key,
    ))

    return KeypairResponse.model_validate(keypair)


async def generate_keypair(
    uow: UnitOfWork, data: KeypairGenerate, user_id: int
) -> KeypairGenerateResponse:
    existing = await uow.keypairs.get_by_name_and_user(data.name, user_id)
    if existing:
        raise HTTPException(status_code=409, detail="A keypair with this name already exists")

    public_key, private_key = _generate_openssh_keypair(data.key_type, comment=data.name)
    fingerprint = _fingerprint(public_key)

    keypair = Keypair(
        user_id=user_id,
        name=data.name,
        public_key=public_key,
        fingerprint=fingerprint,
    )
    await uow.keypairs.add(keypair)
    await uow.commit()
    await uow.refresh(keypair)

    dispatch(KeypairCreated(
        keypair_id=keypair.id,
        name=keypair.name,
        public_key=keypair.public_key,
    ))

    return KeypairGenerateResponse(
        id=keypair.id,
        name=keypair.name,
        fingerprint=keypair.fingerprint,
        openstack_name=keypair.openstack_name,
        created_at=keypair.created_at,
        private_key=private_key,
    )


async def list_keypairs(uow: UnitOfWork, user_id: int) -> list[KeypairResponse]:
    keypairs = await uow.keypairs.get_by_user(user_id)
    return [KeypairResponse.model_validate(kp) for kp in keypairs]


async def delete_keypair(uow: UnitOfWork, keypair_id: int, user_id: int) -> dict:
    keypair = await uow.keypairs.get_by_id_and_user(keypair_id, user_id)
    if not keypair:
        raise HTTPException(status_code=404, detail="Keypair not found")

    openstack_name = keypair.openstack_name
    await uow.keypairs.delete(keypair)
    await uow.commit()

    if openstack_name:
        dispatch(KeypairDeletionRequested(openstack_name=openstack_name))

    return {"message": "Keypair deleted"}
