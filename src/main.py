from fastapi import FastAPI, Request
from src.routes import accounts_router, movies_router, shopping_cart_router, order_router, payments_router


app = FastAPI(
    title="Online Cinema",
    description="Online cinema FastApi project!!!",
    version="0.1.0",
)


@app.middleware("http")
async def log_headers(request: Request, call_next):
    print(f"Incoming Headers: {request.headers.keys()}")
    return await call_next(request)


app.include_router(accounts_router, prefix="/accounts", tags=["accounts"])
app.include_router(movies_router, prefix="/movies", tags=["movies"])
app.include_router(shopping_cart_router, prefix="/shopping", tags=["shopping_cart"])
app.include_router(order_router, prefix="/order", tags=["order"])
app.include_router(payments_router, prefix="/payments", tags=["payments"])
