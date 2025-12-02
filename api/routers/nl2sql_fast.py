from fastapi import APIRouter, HTTPException
from api.models.nlq_request import NLQRequest
from api.models.nlq_response import NLQResponse

from core.agent_fast import FastNL2SQLOrchestrator
from core.config import settings
from core.db.db_executor import DBExecutionError

router = APIRouter()
fast_orch = FastNL2SQLOrchestrator()


@router.post("/generate_sql_fast", response_model=NLQResponse)
async def generate_sql(payload: NLQRequest):
    result = await fast_orch.run(payload.question)
    
    execution = None
    if settings.EXECUTE_SQL:
        try:
            best_sql = result["sql"]
            execution = await db.execute(best_sql)
        except DBExecutionError as e:
            raise HTTPException(status_code=400, detail=f"SQL execution failed: {str(e)}")



    return NLQResponse(
        best_sql=result["best_sql"],
        best_score=result["best_score"],
        selected_tables=result["selected_tables"],
        candidates=result["candidates"],
        execution_result=execution   
    )
