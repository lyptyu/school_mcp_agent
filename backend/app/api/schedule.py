from app.schemas.schedule import ScheduleUpdateRequest
from app.dependencies.auth import get_current_admin
from app.schemas.schedule import ScheduleCreateRequest
from app.common.response import Response
from app.services import schedule_service
from app.database import get_db
from sqlalchemy.orm import Session
from app.dependencies.auth import get_current_user
from fastapi import Depends
from app.models.user import User
from fastapi import Query
from fastapi import APIRouter
from datetime import date

router = APIRouter(prefix="/schedules", tags=['课表相关api'])


@router.get("")
def list_page_schedules(
        user_id: int | None = Query(default=None, description="按用户筛选（仅管理员使用）"),
        date: date | None = Query(default=None, description="上课日期，YYYY-MM-DD"),
        page: int = Query(default=1, ge=1),
        page_size: int = Query(default=10, ge=1, le=100),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)):

    if current_user.role != "admin":
        user_id = current_user.id
    data = schedule_service.list_page_schedules(db, user_id, date, page,
                                                page_size)
    return Response.success(data=data)


@router.post("")
def create_schedules(data: ScheduleCreateRequest,
                     _: User = Depends(get_current_admin),
                     db: Session = Depends(get_db)):
    schedule = schedule_service.create_schedules(db, data)
    return Response.success(data=schedule)


@router.put("/{schedule_id}")
def update_schedules(schedule_id: int,
                     data: ScheduleUpdateRequest,
                     _: User = Depends(get_current_admin),
                     db: Session = Depends(get_db)):
    schedule = schedule_service.update_schedule(db, schedule_id, data)
    return Response.success(data=schedule)


@router.delete("/{schedule_id}")
def delete_schedules(schedule_id: int,
                     _: User = Depends(get_current_admin),
                     db: Session = Depends(get_db)):
    course = schedule_service.delete_schedule(db, schedule_id)
    return Response.success()
