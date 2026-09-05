from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter
import os
from app.api.endpoints import ml, trips, references
from fastapi.middleware.cors import CORSMiddleware

origins = os.getenv("ALLOWED_ORIGINS", "").split(",")
ml_models = {}

REQUEST_COUNT = Counter(
    "app_request_count",
    "Nombre de requêtes par endpoint et status code",
    ["method", "endpoint", "status_code"]
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    model_path = "app/ml_assets/emission_model.joblib"
    if os.path.exists(model_path):
        print("Modèle ML chargé.")
    else:
        print("Aucun modèle ML trouvé — utilisez POST /api/ml/train pour l'entraîner.")

    yield

    ml_models.clear()

app = FastAPI(
    title="OB Rail — Co2 Optimizer",
    lifespan=lifespan,
    redirect_slashes=True,
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
app.include_router(referentiel.router, prefix="/api")