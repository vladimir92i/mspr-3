from fastapi import FastAPI

from app.api.endpoints import references, trips, ml

app = FastAPI(title="API Transport")

# Attachement des routeurs à l'application
app.include_router(references.router)
app.include_router(trips.router)
app.include_router(ml.router)