# api/main.py

from fastapi import FastAPI
from api.routers import nl2sql

app = FastAPI(
    title="Ultimate NL → SQL Agent",
    version="1.0.0"
)

app.include_router(nl2sql.router, prefix="/nl2sql")
