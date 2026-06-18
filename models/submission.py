"""Student information model — matches the frontend form fields."""

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import date


class StudentInfo(BaseModel):
    """All student-submitted data consolidated from the frontend form."""

    # Personal
    full_name: str = Field(..., min_length=1, description="Student's full name")
    email: str = Field(..., description="Student's email address")
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None

    # Academic background
    high_school: str = Field(..., min_length=1, description="Current high school name")
    graduation_year: Optional[int] = Field(None, ge=2024, le=2030)
    gpa: float = Field(..., ge=0.0, le=4.0, description="Unweighted GPA")
    sat_score: Optional[int] = Field(None, ge=400, le=1600)
    act_score: Optional[int] = Field(None, ge=1, le=36)
    intended_majors: list[str] = Field(
        default_factory=list,
        description="List of intended college majors",
    )
    coursework: list[str] = Field(
        default_factory=list,
        description="Relevant courses taken (AP/IB/honors)",
    )

    # Preferences
    preferred_regions: list[str] = Field(
        default_factory=list,
        description="Preferred geographic regions or states",
    )
    budget_range: Optional[str] = Field(
        None,
        description="Annual budget range for tuition, e.g. '30k-50k'",
    )

    # Activities
    extracurriculars: list[str] = Field(default_factory=list)
    awards: list[str] = Field(default_factory=list)
    personal_statement: Optional[str] = Field(
        None,
        max_length=5000,
        description="Personal essay or statement summary",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "full_name": "Zhang Wei",
                "email": "zhangwei@example.com",
                "high_school": "Beijing No.4 High School",
                "graduation_year": 2025,
                "gpa": 3.8,
                "sat_score": 1450,
                "intended_majors": ["Computer Science", "Mathematics"],
                "coursework": ["AP Calculus BC", "AP Physics C", "AP Computer Science"],
                "preferred_regions": ["California", "New York"],
                "extracurriculars": [
                    "Math Club President",
                    "Varsity Basketball",
                    "Volunteer Tutor",
                ],
                "personal_statement": "I want to combine AI and healthcare...",
            }
        },
    )


class ErrorResponse(BaseModel):
    """Consistent error payload returned on failures."""

    error: dict = Field(default_factory=lambda: {"code": "", "message": ""})


class SubmitResponse(BaseModel):
    """Successful submission response with the generated report."""

    report_id: str
    generated_at: str
    student_summary: dict
    recommendations: list[dict]
    action_items: list[str]
