from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import attempts, employees, errors, scenarios

app = FastAPI(title="ВСМ Геймификация — Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

errors.install(app)

app.include_router(employees.router)
app.include_router(scenarios.router)
app.include_router(attempts.router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
