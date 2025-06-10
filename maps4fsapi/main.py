from fastapi import FastAPI

from maps4fsapi.components.dtm import dtm_router

app = FastAPI()

app.include_router(dtm_router, prefix="/dtm")


@app.get("/")
async def root():
    return {"message": "Welcome to the Maps4FS API!"}
