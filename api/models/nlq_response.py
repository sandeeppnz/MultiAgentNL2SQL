# api/models/nlq_response.py

from pydantic import BaseModel
from typing import List, Tuple, Any

class NLQResponse(BaseModel):
    best_sql: str
    best_score: float
    selected_tables: List[str]
    candidates: List[Tuple[float, str]]
