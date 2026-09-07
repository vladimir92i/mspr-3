from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter
import os
from app.api.endpoints import ml, trips, references
from fastapi.middleware.cors import CORSMiddleware

origins = os.getenv("ALLOWED_ORIGINS", "").split(",")
ml_models = {}
app = FastAPI()

REQUEST_COUNT = Counter(
    "app_request_count",
    "Nombre de requêtes par endpoint et status code",
    ["method", "endpoint", "status_code"]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def count_requests(request: Request, call_next):
    response = await call_next(request)
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status_code=str(response.status_code)
    ).inc()
    return response

Instrumentator().instrument(app).expose(app)

app.include_router(trips.router, prefix="/api")
app.include_router(ml.router, prefix="/api")
app.include_router(references.router, prefix="/api")