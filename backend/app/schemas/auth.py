from pydantic import BaseModel, ConfigDict, Field


class AuthenticatedUser(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1, max_length=128)
    email: str | None = Field(default=None, max_length=320)
