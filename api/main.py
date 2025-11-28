# api/main.py

from fastapi import FastAPI
from api.routers import nl2sql, nl2sql_fast, nl2sql_ultrafast

app = FastAPI(
    title="Ultimate NL → SQL Agent",
    version="1.0.0"
)

app.include_router(nl2sql.router, prefix="/nl2sql")
app.include_router(nl2sql_fast.router, prefix="/nl2sql")
app.include_router(nl2sql_ultrafast.router, prefix="/nl2sql")
