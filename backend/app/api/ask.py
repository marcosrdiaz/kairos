"""`POST /portfolios/{id}/ask`: respuesta `text/event-stream` (diseño del MVP §4.4)."""

from collections.abc import Iterator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import TypeAdapter

from app.agents import service
from app.schemas.agents import AskEvent, AskRequest

router = APIRouter(tags=["ask"])

_EVENT = TypeAdapter(AskEvent)


def _sse(events: Iterator[AskEvent]) -> Iterator[str]:
    for event in events:
        yield f"data: {_EVENT.dump_json(event).decode()}\n\n"


@router.post("/portfolios/{portfolio_id}/ask", response_class=StreamingResponse)
def ask(portfolio_id: str, body: AskRequest) -> StreamingResponse:
    events = service.ask(portfolio_id, body)  # NOT_FOUND sale aquí, antes de abrir el stream
    return StreamingResponse(
        _sse(events),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
