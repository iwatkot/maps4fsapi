from fastapi import FastAPI

from maps4fsapi.components.dem import dem_router
from maps4fsapi.components.dtm import dtm_router
from maps4fsapi.components.task import task_router

app = FastAPI()

app.include_router(dtm_router, prefix="/dtm")
app.include_router(dem_router, prefix="/dem")
app.include_router(task_router, prefix="/task")


@app.get("/")
async def root():
    return {"message": "Welcome to the Maps4FS API!"}
