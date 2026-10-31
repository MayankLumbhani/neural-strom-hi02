"""Municipal department table."""

from sqlmodel import Field, SQLModel


class Department(SQLModel, table=True):
    """A municipal department that receives grievance tickets."""

    __tablename__ = "departments"

    id: int | None = Field(default=None, primary_key=True)
    code: str = Field(max_length=50, unique=True, index=True)
    name_en: str = Field(max_length=120)
    name_hi: str = Field(max_length=120)
    name_gu: str = Field(max_length=120)
    sla_hours: int = Field(gt=0)
