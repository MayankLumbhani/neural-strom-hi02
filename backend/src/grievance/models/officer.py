"""Department officer and administrator table."""

from sqlmodel import Field, SQLModel


class Officer(SQLModel, table=True):
    """An authenticated user assigned to a department or administration."""

    __tablename__ = "officers"

    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(max_length=100, unique=True, index=True)
    password_hash: str = Field(max_length=255)
    role: str = Field(max_length=32)
    department_id: int | None = Field(default=None, foreign_key="departments.id", index=True)
    is_active: bool = Field(default=True)
