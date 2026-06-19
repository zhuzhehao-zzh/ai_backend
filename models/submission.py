"""Student information model — matches the Gaokao guidance frontend form."""

from pydantic import BaseModel, ConfigDict, Field


class StudentInfo(BaseModel):
    """Student data from the Gaokao (高考) college guidance frontend."""

    subjectTrack: str = Field(
        ...,
        description="选科: 理科 / 文科 / 新高考选科组合",
    )
    province: str = Field(
        ...,
        min_length=1,
        description="考生所在省份",
    )
    score: int = Field(
        ...,
        ge=0,
        le=750,
        description="高考总分",
    )
    interests: str = Field(
        ...,
        description="兴趣爱好描述, e.g. '写代码、研究 AI'",
    )
    skills: str = Field(
        ...,
        description="技能特长, e.g. '数学能力、逻辑推理'",
    )
    preferences: str = Field(
        ...,
        description="职业偏好, e.g. '高收入潜力、技术壁垒'",
    )
    preferredCities: list[str] = Field(
        default_factory=list,
        description="偏好城市列表, e.g. ['深圳', '杭州']",
    )
    dislikes: str = Field(
        ...,
        description="排斥的行业/方向, e.g. '不想学医、不接受高压行业'",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "subjectTrack": "理科",
                "province": "广东",
                "score": 610,
                "interests": "写代码、研究 AI、解决工程问题",
                "skills": "数学能力、逻辑推理、自学能力",
                "preferences": "高收入潜力、技术壁垒、稳定性",
                "preferredCities": ["深圳", "杭州"],
                "dislikes": "不想学医、不接受高压行业",
            }
        },
    )


class ErrorResponse(BaseModel):
    """Consistent error payload returned on failures."""

    error: dict = Field(default_factory=lambda: {"code": "", "message": ""})


class SubmitResponse(BaseModel):
    """Successful submission response — passes through model output with metadata."""

    report_id: str
    generated_at: str
    profileSummary: dict
    top: list[dict]
    cautious: list[dict]
    all: list[dict]
