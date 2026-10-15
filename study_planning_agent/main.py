from fastapi import FastAPI
from api.agent_routes import router as agent_router

import logging

logging.basicConfig(level=logging.INFO)
app = FastAPI(title="Study Planning Agent")
app.include_router(agent_router)

@app.get("/")
def home():
    return {"message": "Study Planning Agent is running"}