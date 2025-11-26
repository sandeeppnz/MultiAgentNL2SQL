# api/routers/nl2sql.py

from fastapi import APIRouter
from api.models.nlq_request import NLQRequest
from api.models.nlq_response import NLQResponse

from core.agent import NL2SQLOrchestrator

router = APIRouter()
orchestrator = NL2SQLOrchestrator()


@router.post("/generate_sql", response_model=NLQResponse)
async def generate_sql(payload: NLQRequest):

    result = await orchestrator.run(payload.question)

    return NLQResponse(
        best_sql=result["best_sql"],
        best_score=result["best_score"],
        selected_tables=result["selected_tables"],
        candidates=result["all_candidates"]
    )
