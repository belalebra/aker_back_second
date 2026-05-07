import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, booking, complaint, rating, payment, user, notification

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

app = FastAPI(
    title="AKAR Smart Compound API",
    description="Production-Ready Backend for AKAR Service Platform",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(booking.router)
app.include_router(complaint.router)
app.include_router(rating.router)
app.include_router(payment.router)
app.include_router(user.router)
app.include_router(notification.router)

@app.get("/", tags=["Health"])
def root():
    return {"message": "AKAR API v3 is running", "docs": "/docs"}