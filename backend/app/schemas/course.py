from pydantic import ConfigDict
from pydantic import BaseModel


class CourseCreateRequest(BaseModel):
    name: str
    code: str
    description: str | None = None
    status: int = 1


class CourseUpdateRequest(BaseModel):
    name: str | None = None
    code: str | None = None
    description: str | None = None
    status: int | None = None

class CourseResponse(BaseModel):
    id: int
    name: str
    code: str
    description: str | None = None
    status: int = 1

    model_config = ConfigDict(from_attributes=True)