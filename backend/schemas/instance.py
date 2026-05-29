from pydantic import BaseModel, Field

class InstanceRequest(BaseModel):
    name: str = Field(..., max_length=100, description="Numele mașinii virtuale ales de utilizator")
    flavor_name: str = Field(..., max_length=50, description="Numele pachetului de resurse (ex: m1.tiny)")
    image_name: str = Field(..., max_length=50, description="Numele sistemului de operare / imaginii (ex: cirros)")