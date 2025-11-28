from fastapi import APIRouter
from api.models.nlq_request import NLQRequest
from api.models.nlq_response import NLQResponse

from core.agent_fast import FastNL2SQLOrchestrator

router = APIRouter()
fast_orch = FastNL2SQLOrchestrator()


@router.post("/fast", response_model=NLQResponse)
async def fast_generate(payload: NLQRequest):
    result = await fast_orch.run(payload.question)

    return NLQResponse(
        best_sql=result["best_sql"],
        best_score=result["best_score"],
        selected_tables=result["selected_tables"],
        candidates=result["candidates"]
    )
