from fastapi import FastAPI

from src.api.routes.rca import router as rca_router

app = FastAPI(

    title="RCA-SLM API",

    version="1.0.0",

)

app.include_router(rca_router)


@app.get("/")
def home():

    return {

        "message": "RCA-SLM Backend Running"

    }