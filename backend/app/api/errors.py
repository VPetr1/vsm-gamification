from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.scenarios.errors import ScenarioError

STATUS_BY_CODE = {
    "unauthorized": 401,
    "invalid_credentials": 401,
    "forbidden": 403,
    "attempt_not_found": 404,
    "employee_not_found": 404,
    "scenario_not_found": 404,
    "attempt_finished": 409,
    "timer_not_expired": 409,
    "step_mismatch": 409,
    "attempt_not_finished": 409,
    "choice_not_available": 422,
    "choice_required": 422,
    "bad_scope": 422,
    "invalid_scenario": 422,
    "nothing_published": 409,
}


def install(app: FastAPI) -> None:
    @app.exception_handler(ScenarioError)
    async def _scenario_error(_: Request, exc: ScenarioError) -> JSONResponse:
        return JSONResponse(
            status_code=STATUS_BY_CODE.get(exc.code, 400),
            content={"detail": {"code": exc.code, "message": exc.message, **exc.extra}},
        )
