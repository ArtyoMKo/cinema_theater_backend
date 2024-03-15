from fastapi import FastAPI
from starlette.responses import JSONResponse
from starlette.requests import Request

app = FastAPI()


@app.exception_handler(Exception)
async def exception_handler(
    request: Request, exc: Exception
):  # pylint: disable=unused-argument
    return JSONResponse(
        status_code=500,
        content={"message": f"Oops!. Internal server error with message {exc}"},
    )
