from fastapi import FastAPI
from src.routes import accounts_router, movies_router, shopping_cart_router


app = FastAPI(
    title="Online Cinema",
    description="Online cinema FastApi project!!!",
    version="0.1.0",
)
app.include_router(accounts_router, prefix="/accounts", tags=["accounts"])
app.include_router(movies_router, prefix="/movies", tags=["movies"])
app.include_router(shopping_cart_router, prefix="/shopping", tags=["shopping_cart"])
