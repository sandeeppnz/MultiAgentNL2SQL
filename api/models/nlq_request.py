# api/models/nlq_request.py

from pydantic import BaseModel

class NLQRequest(BaseModel):
    question: str
