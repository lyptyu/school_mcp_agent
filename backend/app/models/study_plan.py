from sqlalchemy import Text
from datetime import date
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Date, ForeignKey, Integer, String
from app.database import Base


class StudyPlan(Base):
    __tablename__ = "study_plan"
    __table_args__ = {"comment": "学习计划"}

    user_id: Mapped[int] = mapped_column(Integer,
                                         ForeignKey("users.id"),
                                         comment="用户id",
                                         nullable=False)
    content:Mapped[str] = mapped_column(Text,comment="学习计划内容",nullable=False)