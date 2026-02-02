from pydantic import BaseModel, ConfigDict

class DeviceBase(BaseModel):
    platform: str
    model: str
    model_number: str | None = None
    test_config: dict = {}

class DeviceCreate(DeviceBase):
    pass

class DeviceUpdate(BaseModel):
    platform: str | None = None
    model: str | None = None
    model_number: str | None = None
    test_config: dict | None = None

class DeviceResponse(DeviceBase):
    id: str
    created_at: str | None = None # DateTime serialized
    updated_at: str | None = None

    model_config = ConfigDict(from_attributes=True)
