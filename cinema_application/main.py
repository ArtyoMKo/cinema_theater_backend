from fastapi import FastAPI
from starlette.responses import JSONResponse
from starlette.requests import Request

from cinema_application.database import engine
from cinema_application.routers import rooms, auth, movies, movie_sessions
from cinema_application import models

app = FastAPI()

models.Base.metadata.create_all(bind=engine)
app.include_router(rooms.router)
app.include_router(auth.router)
app.include_router(movies.router)
app.include_router(movie_sessions.router)


@app.exception_handler(Exception)
async def exception_handler(
    request: Request, exc: Exception
):  # pylint: disable=unused-argument
    return JSONResponse(
        status_code=500,
        content={"message": f"Oops!. Internal server error with message {exc}"},
    )
