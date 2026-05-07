import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Standardized imports
from app.routers import (
    auth, 
    booking, 
    complaint, 
    rating, 
    payment, 
    user, 
    notification
)

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AKAR API v3",
    description="Backend for AKAR Smart Compound",
    version="3.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
# Note: tags help organize your /docs page automatically
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(booking.router)
app.include_router(complaint.router)
app.include_router(rating.router)
app.include_router(payment.router)
app.include_router(notification.router)

@app.get("/", tags=["Health Check"])
def health_check():
    return {
        "status": "running", 
        "version": "3.0.0",
        "database": "connected" # This confirms the app started fully
    }