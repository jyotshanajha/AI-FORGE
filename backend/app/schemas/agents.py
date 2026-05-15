from pydantic import BaseModel, Field


class ResearchDigestRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=400)
    max_papers: int = Field(default=8, ge=3, le=20)


class TicTacToeMoveRequest(BaseModel):
    board: list[str] = Field(..., min_length=9, max_length=9)
    player_move: int = Field(..., ge=0, le=8)


class TicTacToeMoveResponse(BaseModel):
    board: list[str]
    ai_move: int | None = None
    winner: str | None = None
    status: str
    next_turn: str | None = None
