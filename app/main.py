from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.database import Base, engine
from app import models
from app.routers.user_router import router as users_router
from app.routers.auth_router import router as auth_router
from app.routers.game_questions_router import router as game_questions_router
from app.routers.game_feedback_router import router as game_feedback_router

app = FastAPI()

app.mount("/static", StaticFiles(directory="app/static"), name="static")

Base.metadata.create_all(bind=engine)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(game_questions_router)
app.include_router(game_feedback_router)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
