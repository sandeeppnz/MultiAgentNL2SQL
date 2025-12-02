# api/routers/nl2sql_ultrafast.py

from fastapi import APIRouter, HTTPException
from api.models.nlq_request import NLQRequest
from api.models.nlq_response import NLQResponse
from core.agent_ultrafast import UltraFastNL2SQLOrchestrator
from core.db.db_executor import DBExecutionError, DBExecutor
from core.schema_graph.schema_loader import SchemaLoader

router = APIRouter()

# load schema once
schema = SchemaLoader().load()
engine = UltraFastNL2SQLOrchestrator(schema)
db = DBExecutor(timeout=8, row_limit=200)   # fast + safe

@router.post("/generate_sql_ultrafast", response_model=NLQResponse)
async def generate_sql(payload: NLQRequest):
    result = await engine.run(payload.question)

    best_sql = result["sql"]

    try:
        execution = await db.execute(best_sql)
    except DBExecutionError as e:
        raise HTTPException(status_code=400, detail=f"SQL execution failed: {str(e)}")

    return NLQResponse(
        best_sql=result["sql"],
        best_score=1.0,
        selected_tables=result["tables"],
        candidates=[(1.0, result["sql"])],
        execution_result=execution   

    )
