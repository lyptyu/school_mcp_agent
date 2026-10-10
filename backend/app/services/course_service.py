from app.schemas.course import CourseUpdateRequest
from app.common.exceptions import BusinessException
from app.schemas.course import CourseCreateRequest
from sqlalchemy import or_
from app.schemas.course import CourseResponse
from sqlalchemy.orm import Session
from app.models.course import Course


def list_courses(db: Session,
                 keywords: str | None = None) -> list[CourseResponse]:
    query = db.query(Course)
    if keywords and keywords.strip():
        kw = f"%{keywords.strip()}%"
        query = query.filter(
            or_(Course.name.ilike(kw), Course.code.ilike(kw),
                Course.description.ilike(kw)))

    rows = query.order_by(Course.id.desc()).all()
    return [CourseResponse.model_validate(row) for row in rows]


def create_courses(db: Session, data: CourseCreateRequest) -> CourseResponse:
    code = data.code.strip()
    if not code:
        raise BusinessException(message="课程编码必传")
    exist = db.query(Course).filter(Course.code == code).first()
    if exist:
        raise BusinessException(message="课程编码已存在")
    course = Course(name=data.name.strip(),
                    code=code.strip(),
                    description=(data.description or "").strip() or None,
                    status=data.status if data.status else 1)
    db.add(course)
    db.commit()
    db.refresh(course)
    return CourseResponse.model_validate(course)


def update_courses(db: Session, course_id: int,
                   data: CourseUpdateRequest) -> CourseResponse:
    row = db.query(Course).filter(Course.id == course_id).first()
    if not row:
        raise BusinessException(message="课程不存在")
    payload = data.model_dump(exclude_none=True)
    if "name" in payload:
        payload['name'] = payload['name'].strip()
    if "code" in payload:
        code = payload['code'].strip()
        conflict = db.query(Course).filter(Course.code == code, Course.id
                                           != course_id).first()
        if conflict:
            raise BusinessException(message="课程编号已存在")
        payload['code'] = code
    if "description" in payload:
        payload['description'] = payload['description'].strip()

    for field, value in payload.items():
        setattr(row, field, value)
    db.commit()
    db.refresh(row)
    return CourseResponse.model_validate(row)

def delete_courses(db: Session, course_id: int) -> None:
    row = db.query(Course).filter(Course.id == course_id).first()
    if not row:
        raise BusinessException(message="课程不存在")
    db.delete(row)
    db.commit()
