from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.evaluate import router as evaluate_router

app = FastAPI(title="AI Answer Evaluator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(evaluate_router)


@app.get("/")
def home():
    return {"message": "AI Answer Evaluator API is running"}