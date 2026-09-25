from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.models import Employee

router = APIRouter(prefix="/employees", tags=["employees"])


class EmployeeIn(BaseModel):
    full_name: str
    depot: str = ""
    brigade: str = ""


class EmployeeOut(BaseModel):
    id: str
    full_name: str
    depot: str
    brigade: str

    model_config = {"from_attributes": True}


@router.post("", response_model=EmployeeOut, status_code=201)
def create_employee(payload: EmployeeIn, db: Session = Depends(get_db)) -> Employee:
    employee = Employee(**payload.model_dump())
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee


@router.get("", response_model=list[EmployeeOut])
def list_employees(db: Session = Depends(get_db)) -> list[Employee]:
    return db.query(Employee).all()
