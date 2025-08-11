from fastapi import FastAPI, HTTPException
from app.routes.payment_route import payment_router
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


app.include_router(payment_router, prefix="/payments", tags=["payments"])
