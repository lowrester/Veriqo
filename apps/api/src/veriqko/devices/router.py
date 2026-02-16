from typing import Annotated, List
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from veriqko.db.base import get_db
from veriqko.dependencies import get_current_user
from veriqko.devices.models import Device, Brand, GadgetType
from veriqko.devices.schemas import (
    DeviceCreate, DeviceResponse, DeviceUpdate,
    BrandBase, BrandResponse,
    GadgetTypeBase, GadgetTypeResponse
)
from veriqko.users.models import User

router = APIRouter(prefix="/admin", tags=["devices"])

# --- Brands ---

@router.get("/brands", response_model=List[BrandResponse])
async def list_brands(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    stmt = select(Brand).order_by(Brand.name)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/brands", response_model=BrandResponse, status_code=status.HTTP_201_CREATED)
async def create_brand(
    brand_in: BrandBase,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    brand = Brand(**brand_in.model_dump())
    db.add(brand)
    await db.commit()
    await db.refresh(brand)
    return brand

# --- Gadget Types ---

@router.get("/gadget-types", response_model=List[GadgetTypeResponse])
async def list_gadget_types(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    stmt = select(GadgetType).order_by(GadgetType.name)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/gadget-types", response_model=GadgetTypeResponse, status_code=status.HTTP_201_CREATED)
async def create_gadget_type(
    type_in: GadgetTypeBase,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    gadget_type = GadgetType(**type_in.model_dump())
    db.add(gadget_type)
    await db.commit()
    await db.refresh(gadget_type)
    return gadget_type

# --- Devices ---

@router.get("/devices", response_model=List[DeviceResponse])
async def list_devices(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """List all device types."""
    stmt = select(Device).options(
        joinedload(Device.brand),
        joinedload(Device.gadget_type)
    ).order_by(Device.model)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/devices", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
async def create_device(
    device_in: DeviceCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Create a new device type."""
    device = Device(**device_in.model_dump())
    db.add(device)
    await db.commit()
    await db.refresh(device)
    
    # Reload with relationships
    stmt = select(Device).options(
        joinedload(Device.brand),
        joinedload(Device.gadget_type)
    ).where(Device.id == device.id)
    result = await db.execute(stmt)
    return result.scalar_one()

@router.get("/devices/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get a device type by ID."""
    stmt = select(Device).options(
        joinedload(Device.brand),
        joinedload(Device.gadget_type)
    ).where(Device.id == device_id)
    result = await db.execute(stmt)
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device

@router.put("/devices/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: str,
    device_in: DeviceUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Update a device type."""
    device = await db.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    update_data = device_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(device, field, value)
        
    await db.commit()
    
    # Reload with relationships
    stmt = select(Device).options(
        joinedload(Device.brand),
        joinedload(Device.gadget_type)
    ).where(Device.id == device.id)
    result = await db.execute(stmt)
    return result.scalar_one()

@router.delete("/devices/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_device(
    device_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Delete a device type."""
    device = await db.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    await db.delete(device)
    await db.commit()
