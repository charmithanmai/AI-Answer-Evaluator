from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.evaluate import router as evaluate_router
from backend.api.history import router as history_router
from backend.database import init_db

app = FastAPI(title="AI Answer Evaluator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()  # creates the SQLite table if it does not exist yet

app.include_router(evaluate_router)
app.include_router(history_router)


@app.get("/")
def home():
    return {"message": "AI Answer Evaluator API is running"}
    