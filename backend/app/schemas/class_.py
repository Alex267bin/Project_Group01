from pydantic import BaseModel, ConfigDict, Field


class ClassCreate(BaseModel):
    class_code: str = Field(min_length=1, max_length=50)
    course_id: str
    lecturer_code: str
    academic_year: str = Field(min_length=1, max_length=20)
    semester: str = Field(min_length=1, max_length=20)
    room: str | None = Field(default=None, max_length=100)


class ClassUpdate(BaseModel):
    class_code: str | None = Field(default=None, min_length=1, max_length=50)
    course_id: str | None = None
    lecturer_code: str | None = None
    academic_year: str | None = Field(default=None, min_length=1, max_length=20)
    semester: str | None = Field(default=None, min_length=1, max_length=20)
    room: str | None = Field(default=None, max_length=100)


class ClassResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    class_id: str
    class_code: str
    course_id: str
    lecturer_code: str
    academic_year: str
    semester: str
    room: str | None
