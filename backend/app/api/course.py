from app.schemas.course import CourseUpdateRequest
from app.schemas.course import CourseCreateRequest
from app.common.response import Response
from app.services import course_service
from app.database import get_db
from app.dependencies.auth import get_current_admin
from app.models.user import User
from fastapi import Query
from fastapi import Depends
from sqlalchemy.orm import Session
from fastapi import APIRouter

router = APIRouter(prefix='/course', tags=['课程相关api'])


@router.get("")
def list_courses(keywords: str | None = Query(default=None,
                                              description="按名称/编码/简介查询"),
                 _: User = Depends(get_current_admin),
                 db: Session = Depends(get_db)):
    data = course_service.list_courses(db, keywords)
    return Response.success(data=data)


@router.post("")
def create_courses(data: CourseCreateRequest,
                   _: User = Depends(get_current_admin),
                   db: Session = Depends(get_db)):
    course = course_service.create_courses(db, data)
    return Response.success(data=course)


@router.put("/{course_id}")
def update_courses(course_id: int,
                   data: CourseUpdateRequest,
                   _: User = Depends(get_current_admin),
                   db: Session = Depends(get_db)):
    course = course_service.update_courses(db, course_id, data)
    return Response.success(data=course)


@router.delete("/{course_id}")
def delete_courses(course_id: int,
                   _: User = Depends(get_current_admin),
                   db: Session = Depends(get_db)):
    course = course_service.delete_courses(db, course_id)
    return Response.success()
