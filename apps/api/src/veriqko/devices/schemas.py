from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BrandBase(BaseModel):
    name: str
    logo_url: str | None = None

class BrandCreate(BrandBase):
    pass

class BrandUpdate(BaseModel):
    name: str | None = None
    logo_url: str | None = None

class BrandResponse(BrandBase):
    id: str
    model_config = ConfigDict(from_attributes=True)

class GadgetTypeBase(BaseModel):
    name: str

class GadgetTypeCreate(GadgetTypeBase):
    pass

class GadgetTypeUpdate(BaseModel):
    name: str | None = None

class GadgetTypeResponse(GadgetTypeBase):
    id: str
    model_config = ConfigDict(from_attributes=True)

class DeviceBase(BaseModel):
    brand_id: str
    type_id: str
    model: str
    model_number: str | None = None
    colour: str | None = None
    storage: str | None = None
    test_config: dict = {}

class DeviceCreate(DeviceBase):
    pass

class DeviceUpdate(BaseModel):
    brand_id: str | None = None
    type_id: str | None = None
    model: str | None = None
    model_number: str | None = None
    colour: str | None = None
    storage: str | None = None
    test_config: dict | None = None

class DeviceResponse(BaseModel):
    id: str
    brand_id: str
    type_id: str
    model: str
    model_number: str | None = None
    colour: str | None = None
    storage: str | None = None
    test_config: dict = {}
    brand: BrandResponse
    gadget_type: GadgetTypeResponse
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
