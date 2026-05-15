import uuid

from pydantic import BaseModel, Field, model_validator


class ResearchDigestRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=400)
    max_papers: int = Field(default=8, ge=3, le=20)


class DataframeQueryRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=2000)
    attachment_id: uuid.UUID | None = None
    google_sheet_id: str | None = Field(default=None, min_length=10, max_length=500)
    worksheet_name: str | None = Field(default=None, min_length=1, max_length=200)

    @model_validator(mode="after")
    def validate_source(self) -> "DataframeQueryRequest":
        sources = [self.attachment_id is not None, bool((self.google_sheet_id or "").strip())]
        if sum(sources) != 1:
            raise ValueError("Provide exactly one data source: attachment_id or google_sheet_id")
        return self


class DataframeQueryResponse(BaseModel):
    answer: str
    source_type: str
    source_name: str
    row_count: int
    column_count: int
    columns: list[str]
    generated_code: str | None = None
    intermediate_steps: list[str] = Field(default_factory=list)


class TicTacToeMoveRequest(BaseModel):
    board: list[str] = Field(..., min_length=9, max_length=9)
    player_move: int = Field(..., ge=0, le=8)


class TicTacToeMoveResponse(BaseModel):
    board: list[str]
    ai_move: int | None = None
    winner: str | None = None
    status: str
    next_turn: str | None = None
