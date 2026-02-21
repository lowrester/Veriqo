from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from veriqko.db.base import get_db
from veriqko.dependencies import get_current_active_user
from veriqko.printing.models import Printer
from veriqko.users.models import User, UserRole

router = APIRouter(prefix="/printing/printers", tags=["printing"])

# --- Schemas ---
class PrinterBase(BaseModel):
    name: str
    ip_address: str
    port: int = 9100
    protocol: str = "ZPL"
    is_active: bool = True
    station_id: str | None = None

class PrinterCreate(PrinterBase):
    pass

class PrinterResponse(PrinterBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# --- Endpoints ---

@router.get("", response_model=list[PrinterResponse])
async def list_printers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all configured printers."""
    query = select(Printer).order_by(Printer.name)
    result = await db.execute(query)
    return result.scalars().all()

@router.post("", response_model=PrinterResponse, status_code=status.HTTP_201_CREATED)
async def create_printer(
    data: PrinterCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Add a new printer (Admin/Supervisor only)."""
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPERVISOR]:
        raise HTTPException(status_code=403, detail="Not authorized")

    printer = Printer(**data.model_dump())
    db.add(printer)
    await db.commit()
    await db.refresh(printer)
    return printer

@router.get("/{printer_id}", response_model=PrinterResponse)
async def get_printer(
    printer_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get a specific printer."""
    printer = await db.get(Printer, printer_id)
    if not printer:
        raise HTTPException(status_code=404, detail="Printer not found")
    return printer

@router.put("/{printer_id}", response_model=PrinterResponse)
async def update_printer(
    printer_id: UUID,
    data: PrinterCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update a printer (Admin/Supervisor only)."""
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPERVISOR]:
        raise HTTPException(status_code=403, detail="Not authorized")

    printer = await db.get(Printer, printer_id)
    if not printer:
        raise HTTPException(status_code=404, detail="Printer not found")

    for field, value in data.model_dump().items():
        setattr(printer, field, value)

    await db.commit()
    await db.refresh(printer)
    return printer

@router.delete("/{printer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_printer(
    printer_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a printer (Admin only)."""
    if current_user.role not in [UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")

    printer = await db.get(Printer, printer_id)
    if not printer:
        raise HTTPException(status_code=404, detail="Printer not found")

    await db.delete(printer)
    await db.commit()
    return None
