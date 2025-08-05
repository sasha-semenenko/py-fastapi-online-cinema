from fastapi import FastAPI
from routes import accounts_router

app = FastAPI(
    title="Cinema Project",
    description="Digital platform that allows users to select, watch, and purchase access to movies "
                "and other video materials via the internet",
)


api_version_prefix = "/api/v1"



app.include_router(accounts_router, prefix=f"{api_version_prefix}/accounts", tags=["accounts"])
