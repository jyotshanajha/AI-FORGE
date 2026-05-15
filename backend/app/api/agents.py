import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.agents import (
    DataframeQueryRequest,
    DataframeQueryResponse,
    ResearchDigestRequest,
    TicTacToeMoveRequest,
    TicTacToeMoveResponse,
)
from app.services.research_digest_service import ResearchDigestService
from app.services.tic_tac_toe_service import TicTacToeService


router = APIRouter()


@router.post("/dataframe-query", response_model=DataframeQueryResponse)
async def dataframe_query(
    payload: DataframeQueryRequest,
    current_user: User = Depends(get_current_user),
) -> DataframeQueryResponse:
    from app.services.dataframe_query_service import DataframeQueryService

    return await DataframeQueryService.answer_question(payload, current_user)


@router.post("/research-digest/stream")
async def stream_research_digest(
    payload: ResearchDigestRequest,
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    async def event_generator() -> object:
        async for chunk in ResearchDigestService.stream_digest(
            query=payload.query,
            max_papers=payload.max_papers,
            user_email=current_user.email,
        ):
            yield f"data: {json.dumps({'token': chunk})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/tic-tac-toe/move", response_model=TicTacToeMoveResponse)
async def tic_tac_toe_move(payload: TicTacToeMoveRequest) -> TicTacToeMoveResponse:
    try:
        state = TicTacToeService.play_turn(payload.board, payload.player_move)
        return TicTacToeMoveResponse(
            board=state.board,
            ai_move=state.ai_move,
            winner=state.winner,
            status=state.status,
            next_turn=state.next_turn,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"error": "invalid_move", "message": str(exc)}) from exc
