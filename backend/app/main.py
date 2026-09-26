from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import attempts, auth, employees, errors, me, scenarios
from app.core.config import settings

app = FastAPI(title="Рейс 400 — тренажёр проводника ВСМ", version="0.2.0")

# The web client is served from the same origin (nginx / Vite proxy), so CORS is off unless
# CORS_ORIGINS explicitly lists trusted origins; a wildcard is never combined with cookies.
if settings.cors_origin_list:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Content-Type"],
    )

errors.install(app)

app.include_router(auth.router)
app.include_router(employees.router)
app.include_router(scenarios.router)
app.include_router(attempts.router)
app.include_router(me.router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
