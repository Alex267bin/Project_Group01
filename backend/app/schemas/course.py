cd "C:\Users\Duc Khoa\Downloads\Project_Group01"from pydantic import BaseModel, ConfigDict, Field


class CourseCreate(BaseModel):
    course_code: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    credits: int = Field(default=0, ge=0, le=20)


class CourseUpdate(BaseModel):
    course_code: str | None = Field(default=None, min_length=1, max_length=50)
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    credits: int | None = Field(default=None, ge=0, le=20)


class CourseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    course_id: str
    course_code: str
    name: str
    description: str | None
    credits: int
