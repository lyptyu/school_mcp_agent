from app.schemas.schedule import ScheduleUpdateRequest
from app.common.exceptions import BusinessException
from app.schemas.schedule import ScheduleCreateRequest
from fastapi import Query
from app.schemas.schedule import ScheduleResponse
from app.models.course import Course
from app.models.user import User
from app.models.schedule import Schedule
from app.common.response import PageResponse
from datetime import date
from sqlalchemy.orm import Session

def _to_response(
    row: Schedule,
    username: str,
    user_name: str,
    course_name: str,
) -> ScheduleResponse:
    """把课表行 + 联表字段组装成响应。"""
    return ScheduleResponse(
        id=row.id,
        user_id=row.user_id,
        username=username,
        user_name=user_name,
        class_date=row.class_date,
        period=row.period,
        course_id=row.course_id,
        course_name=course_name,
        location=row.location,
    )


def list_page_schedules(db: Session,
                        user_id: int | None = None,
                        class_date: date | None = None,
                        page: int = 1,
                        page_size: int = 10) -> PageResponse:
    """分页查询课表列表"""
    query = _base_query(db, user_id, class_date)
    total = query.count()
    rows = query.order_by(Schedule.id.desc()).offset(
        page_size * (page - 1)).limit(page_size).all()
    return PageResponse(list=[
        _to_response(row, username, user_name, course_name)
        for row, username, user_name, course_name in rows
    ],
                        total=total)


def _base_query(db: Session,
                user_id: int | None = None,
                class_date: date | None = None) -> Query:
    query = db.query(Schedule, User.username, User.name,
                     Course.name).join(User, Schedule.user_id == User.id).join(
                         Course, Schedule.course_id == Course.id)
    if user_id is not None:
        query = query.filter(Schedule.user_id == user_id)
    if class_date is not None:
        query = query.filter(Schedule.class_date == class_date)
    return query


def list_schedules(
    db: Session,
    user_id: int | None = None,
    class_date: date | None = None,
) -> PageResponse:
    """查询全部课表列表,MCP工具使用"""

    query = _base_query(db, user_id, class_date)
    rows = query.order_by(Schedule.id.desc()).all()
    return PageResponse(list=[
        _to_response(row, username, user_name, course_name)
        for row, username, user_name, course_name in rows
    ])

def list_schedules_as_dict(
    db: Session,
    user_id: int | None = None,
    date_str: str | None = None, #YYYY-MM-dd
) -> list[dict]:
    """查询全部课表列表,返回字典里列表，MCP工具使用"""
    date_text = (date_str or "").strip()
    class_date = date.fromisoformat(date_text) if date_text else None
    items = list_schedules(db,user_id,class_date).list
    return [
        {
            "date":item.class_date.isoformat(),
            "period":item.period,
            "course_id":item.course_id,
            "course_name":item.course_name,
            "location":item.location,
        }
        for item in items
    ]


def create_schedules(db: Session,
                     data: ScheduleCreateRequest) -> ScheduleResponse:
    """创建课表"""

    user = db.query(User).filter(User.id == data.user_id).first()
    if not user:
        raise BusinessException(message="用户不存在")
    if user.role != 'student':
        raise BusinessException(message="只能给学生安排课表")

    course = db.query(Course).filter(Course.id == data.course_id).first()
    if not course:
        raise BusinessException(message="课程不存在")

    row = Schedule(**data.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return _to_response(row, user.username, user.name, course.name)


def update_schedule(db: Session, schedule_id: int,
                    data: ScheduleUpdateRequest) -> ScheduleResponse:
    row = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not row:
        raise BusinessException(message='课表不存在')
    payload = data.model_dump(exclude_none=True)
    user_id = payload.get('user_id', row.user_id)
    course_id = payload.get('course_id', row.course_id)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise BusinessException(message="用户不存在")
    if user.role != 'student':
        raise BusinessException(message="只能给学生安排课表")
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise BusinessException(message="课程不存在")

    for field, value in payload.items():
        setattr(row, field, value)
    db.commit()
    db.refresh(row)
    return _to_response(row, user.username, user.name, course.name)


def delete_schedule(db: Session, schedule_id: int):
    row = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not row:
        raise BusinessException(message='课表不存在')
    db.delete(row)
    db.commit()

