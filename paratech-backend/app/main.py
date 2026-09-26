import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from prometheus_client import generate_latest

from app.auth.router import router as auth_router
from app.database import create_db_and_tables

from app.recommendation.router import router as recommendation_router
from app.recommendation.service import load_recommendation_pipeline

from app.barcode.router import router as barcode_router
from app.barcode.pipeline import load_barcode_pipeline

from app.demand.router import router as demand_router

from app.stock_ml.router import router as stock_ml_router
from app.stock_ml.service import load_stock_ml_pipeline


app = FastAPI(
    title="ParaTech API",
    version="1.0.0",
    description="Backend API for ParaTech decision-support platform.",
)


# ---------------------------------------------------------
# CORS
# ---------------------------------------------------------

allowed_origins = [
    "http://localhost:4200",
    "http://127.0.0.1:4200",
]

# Later on Render, this will contain the deployed Vercel URL.
production_origin = os.getenv("FRONTEND_URL")

if production_origin:
    allowed_origins.append(production_origin.rstrip("/"))


app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# Startup
# ---------------------------------------------------------

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

    try:
        load_barcode_pipeline()
        print("Barcode pipeline loaded successfully.")
    except Exception as error:
        print(f"Barcode pipeline loading failed: {error}")

    try:
        load_recommendation_pipeline()
        print("Recommendation pipeline loaded successfully.")
    except Exception as error:
        print(f"Recommendation pipeline loading failed: {error}")

    try:
        load_stock_ml_pipeline()
        print("Stock ML pipeline loaded successfully.")
    except Exception as error:
        print(f"Stock ML pipeline loading failed: {error}")


# ---------------------------------------------------------
# Routers
# ---------------------------------------------------------

app.include_router(
    auth_router,
    prefix="/auth",
    tags=["Authentication"],
)

app.include_router(
    recommendation_router,
    prefix="/recommendations",
    tags=["Recommendations"],
)

app.include_router(
    barcode_router,
    prefix="/barcode",
    tags=["Barcode"],
)

app.include_router(
    demand_router,
    prefix="/demand",
    tags=["Demand Forecasting"],
)

app.include_router(
    stock_ml_router,
    prefix="/stock-ml",
    tags=["Stock ML Risk"],
)


# ---------------------------------------------------------
# API status
# ---------------------------------------------------------

@app.get("/")
def home():
    return {
        "message": "ParaTech Backend is running",
        "modules": [
            "authentication",
            "recommendations",
            "barcode",
            "demand_forecasting",
            "stock_ml_risk",
        ],
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "api": "ParaTech API",
        "modules": {
            "auth": "loaded",
            "recommendations": "loaded",
            "barcode": "loaded",
            "demand_forecasting": "loaded",
            "stock_ml_risk": "loaded",
        },
    }


# ---------------------------------------------------------
# Prometheus metrics
# ---------------------------------------------------------

@app.get("/metrics")
def metrics():
    return Response(
        generate_latest(),
        media_type="text/plain",
    )