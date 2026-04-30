from fastapi import FastAPI

from .routers import challenges, teams

app = FastAPI()


app.include_router(challenges.router)
app.include_router(teams.router)
