from fastapi import APIRouter
from app.api.endpoints import graph

api_router = APIRouter()

api_router.include_router(graph.router)