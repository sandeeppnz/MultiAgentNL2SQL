# api/routers/nl2sql_ultrafast.py

from fastapi import APIRouter
from api.models.nlq_request import NLQRequest
from api.models.nlq_response import NLQResponse
from core.agent_ultrafast import UltraFastNL2SQLOrchestrator
from core.schema_graph.schema_loader import SchemaLoader

router = APIRouter()

# load schema once
schema = SchemaLoader().load()
engine = UltraFastNL2SQLOrchestrator(schema)

@router.post("/generate_sql_ultrafast", response_model=NLQResponse)
async def generate_sql(payload: NLQRequest):
    result = await engine.run(payload.question)
    return NLQResponse(
        best_sql=result["sql"],
        best_score=1.0,
        selected_tables=result["tables"],
        candidates=[(1.0, result["sql"])]
    )
