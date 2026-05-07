import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, booking, complaint, rating, payment, user, notification

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="AKAR API v3")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Centralized Routers
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(booking.router)
app.include_router(complaint.router)
app.include_router(rating.router)
app.include_router(payment.router)
app.include_router(notification.router)

@app.get("/")
def health_check():
    return {"status": "running", "version": "3.0.0"}