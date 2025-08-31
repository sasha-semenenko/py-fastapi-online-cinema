from fastapi import FastAPI
from routes import accounts_router


app = FastAPI(
    title="Online Cinema",
    description="Online cinema FastApi project!!!",
    version="0.1.0",
)
app.include_router(accounts_router, tags=["accounts"])
