from fastapi import FastAPI
from .routes.oauth_routes import router as oauth_router
from .routes.payment_link import router as payment_link_router

app = FastAPI()

# OAuth routes (one-time to capture refresh token)
app.include_router(oauth_router)

# Payment Link routes
app.include_router(payment_link_router)
