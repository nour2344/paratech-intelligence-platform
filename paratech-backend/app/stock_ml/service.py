from __future__ import annotations

from pathlib import Path
from typing import Optional

import joblib
import numpy as np
import pandas as pd
from fastapi import HTTPException

from app.stock_ml.schemas import (
    StockMlAlert,
    StockMlAnalysisResponse,
    StockMlAnalyzeRequest,
    StockMlPredictRequest,
    StockMlPredictResponse,
    StockMlProductSearchItem,
    StockMlSearchResponse,
)


BASE_DIR = Path(__file__).resolve().parent
BACKEND_APP_DIR = BASE_DIR.parent

MODEL_PATH = BASE_DIR / "model_files" / "model_v2.pkl"

STOCK_DATA_PATH = BASE_DIR / "data" / "DimProducts.csv"
SALES_DATA_PATH = BASE_DIR / "data" / "factSales.csv"

FALLBACK_STOCK_PATHS = [
    BACKEND_APP_DIR / "stock" / "data" / "DimProducts.csv",
    BACKEND_APP_DIR / "demand" / "data" / "dimProducts.csv",
    BACKEND_APP_DIR / "demand" / "data" / "DimProducts.csv",
]

FALLBACK_SALES_PATHS = [
    BACKEND_APP_DIR / "demand" / "data" / "factSales.csv",
    BACKEND_APP_DIR / "stock" / "data" / "factSales.csv",
]


model = None
model_error: Optional[str] = None
products_df: Optional[pd.DataFrame] = None
sales_df: Optional[pd.DataFrame] = None
active_alerts: list[StockMlAnalysisResponse] = []


FEATURE_COLUMNS = [
    "StockQuantity",
    "AlertQuantity",
    "avg_daily_sales",
    "stock_coverage",
    "stock_value_ratio",
    "days_to_stockout",
    "StockValue",
    "ProductCategory_enc",
]


def _find_existing_file(primary_path: Path, fallback_paths: list[Path]) -> Path:
    if primary_path.exists():
        return primary_path

    for path in fallback_paths:
        if path.exists():
            return path

    raise FileNotFoundError(f"File not found: {primary_path}")


def _read_csv(path: Path) -> pd.DataFrame:
    encodings = ["utf-8", "utf-8-sig", "latin1", "cp1252"]
    separators = ["|", ";", ",", "\t"]

    last_error = None

    for encoding in encodings:
        for separator in separators:
            try:
                df = pd.read_csv(
                    path,
                    sep=separator,
                    encoding=encoding,
                    engine="python",
                    on_bad_lines="skip",
                )

                df.columns = [str(column).strip() for column in df.columns]

                if len(df.columns) > 1:
                    print(
                        f"CSV loaded successfully: {path.name} | "
                        f"encoding={encoding} | separator='{separator}' | "
                        f"columns={len(df.columns)} | rows={len(df)}"
                    )
                    return df

            except Exception as error:
                last_error = error

    raise ValueError(f"Could not read CSV file {path}. Last error: {last_error}")

def _clean_string(value) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value).strip()


def _safe_float(value, default: float = 0.0) -> float:
    try:
        if value is None or pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def load_stock_ml_pipeline() -> None:
    global model, model_error, products_df, sales_df

    model_error = None

    try:
        model = joblib.load(MODEL_PATH)
        print(f"Stock ML model loaded successfully from: {MODEL_PATH}")
    except Exception as error:
        model = None
        model_error = str(error)
        print(f"Stock ML model loading failed: {error}")

    try:
        stock_path = _find_existing_file(STOCK_DATA_PATH, FALLBACK_STOCK_PATHS)
        products_df = _read_csv(stock_path)

        required_columns = [
            "ProductName",
            "ProductCategory",
            "StockQuantity",
            "AlertQuantity",
            "StockValue",
        ]

        for column in required_columns:
            if column not in products_df.columns:
                raise ValueError(f"Missing required column in stock data: {column}")

        products_df["ProductName_clean"] = (
            products_df["ProductName"].fillna("").astype(str).str.strip()
        )

        products_df["ProductCategory_clean"] = (
            products_df["ProductCategory"].fillna("UNKNOWN").astype(str).str.strip()
        )

        categories = sorted(products_df["ProductCategory_clean"].dropna().unique())
        category_mapping = {category: index for index, category in enumerate(categories)}

        products_df["ProductCategory_enc"] = (
            products_df["ProductCategory_clean"]
            .map(category_mapping)
            .fillna(0)
            .astype(int)
        )

        print(f"Stock ML product data loaded successfully: {len(products_df)} products")
        print(f"Stock ML columns: {list(products_df.columns)}")

    except Exception as error:
        products_df = None
        print(f"Stock ML product data loading failed: {error}")

    try:
        sales_path = _find_existing_file(SALES_DATA_PATH, FALLBACK_SALES_PATHS)
        sales_df = _read_csv(sales_path)
        print(f"Stock ML sales data loaded successfully: {len(sales_df)} rows")
    except Exception as error:
        sales_df = None
        print(f"Stock ML sales data loading failed: {error}")

    print("Stock ML pipeline loaded successfully.")


def is_model_loaded() -> bool:
    return model is not None


def get_model_info_service() -> dict:
    return {
        "model_loaded": model is not None,
        "model_type": type(model).__name__ if model is not None else None,
        "features": FEATURE_COLUMNS,
        "classes": ["high", "low", "medium"],
        "note": "The /predict endpoint is technical. Use /analyze for the frontend.",
    }


def _normalize_model_risk(prediction) -> str:
    risk_mapping = {
        0: "high",
        1: "low",
        2: "medium",
        "0": "high",
        "1": "low",
        "2": "medium",
        "high": "high",
        "low": "low",
        "medium": "medium",
    }

    return risk_mapping.get(prediction, str(prediction).lower())


def _apply_business_correction(
    ml_risk: str,
    stock_quantity: float,
    alert_quantity: float,
    days_to_stockout: float,
) -> str:
    if stock_quantity <= 0:
        return "high"

    if alert_quantity > 0 and stock_quantity <= alert_quantity:
        return "high"

    if days_to_stockout <= 7:
        return "high"

    if 7 < days_to_stockout <= 30:
        return "medium"

    if alert_quantity > 0 and stock_quantity >= alert_quantity * 3 and days_to_stockout > 30:
        return "low"

    return ml_risk


def predict_stock_ml_service(request: StockMlPredictRequest) -> StockMlPredictResponse:
    if model is None:
        raise HTTPException(
            status_code=503,
            detail=f"Stock ML model is not loaded. Error: {model_error}",
        )

    input_data = pd.DataFrame(
        [
            {
                "StockQuantity": request.StockQuantity,
                "AlertQuantity": request.AlertQuantity,
                "avg_daily_sales": request.avg_daily_sales,
                "stock_coverage": request.stock_coverage,
                "stock_value_ratio": request.stock_value_ratio,
                "days_to_stockout": request.days_to_stockout,
                "StockValue": request.StockValue,
                "ProductCategory_enc": request.ProductCategory_enc,
            }
        ],
        columns=FEATURE_COLUMNS,
    )

    try:
        raw_prediction = model.predict(input_data)[0]
        ml_risk = _normalize_model_risk(raw_prediction)

        confidence = 0.0
        if hasattr(model, "predict_proba"):
            probabilities = model.predict_proba(input_data)[0]
            confidence = float(np.max(probabilities))

        corrected_risk = _apply_business_correction(
            ml_risk=ml_risk,
            stock_quantity=request.StockQuantity,
            alert_quantity=request.AlertQuantity,
            days_to_stockout=request.days_to_stockout,
        )

        return StockMlPredictResponse(
            risk_level=corrected_risk,
            alert=corrected_risk in ["high", "medium"],
            confidence=round(confidence, 4),
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Stock ML prediction failed: {error}",
        )


def search_stock_ml_products_service(name: str) -> StockMlSearchResponse:
    if products_df is None:
        raise HTTPException(
            status_code=503,
            detail="Stock product data is not loaded.",
        )

    query = _clean_string(name).lower()

    if len(query) < 2:
        raise HTTPException(
            status_code=400,
            detail="Please enter at least 2 characters.",
        )

    filtered = products_df[
        products_df["ProductName_clean"].str.lower().str.contains(query, na=False)
    ].head(15)

    results = []

    for _, row in filtered.iterrows():
        results.append(
            StockMlProductSearchItem(
                product_name=_clean_string(row.get("ProductName")),
                category=_clean_string(row.get("ProductCategory")),
                current_stock=_safe_float(row.get("StockQuantity")),
                alert_threshold=_safe_float(row.get("AlertQuantity")),
            )
        )

    return StockMlSearchResponse(
        count=len(results),
        results=results,
    )


def _get_product_by_name(product_name: str) -> pd.Series:
    if products_df is None:
        raise HTTPException(
            status_code=503,
            detail="Stock product data is not loaded.",
        )

    query = _clean_string(product_name).lower()

    exact_match = products_df[
        products_df["ProductName_clean"].str.lower() == query
    ]

    if not exact_match.empty:
        return exact_match.iloc[0]

    partial_match = products_df[
        products_df["ProductName_clean"].str.lower().str.contains(query, na=False)
    ]

    if not partial_match.empty:
        return partial_match.iloc[0]

    raise HTTPException(
        status_code=404,
        detail=f"Product '{product_name}' not found.",
    )


def _compute_average_daily_sales(product_row: pd.Series) -> float:
    if sales_df is None or sales_df.empty:
        return 0.0

    possible_product_columns = [
        "ProductKey",
        "ProductId",
        "product_id",
        "product_key",
        "ProductStockId",
    ]

    possible_quantity_columns = [
        "TotalQuantitySold",
        "Quantity",
        "quantity",
        "SalesQuantity",
        "Qty",
    ]

    product_column = next(
        (column for column in possible_product_columns if column in sales_df.columns),
        None,
    )

    quantity_column = next(
        (column for column in possible_quantity_columns if column in sales_df.columns),
        None,
    )

    if product_column is None or quantity_column is None:
        return 0.0

    product_ids_to_try = [
        product_row.get("ProductId"),
        product_row.get("ProductStockId"),
        product_row.get("IDC"),
    ]

    matched_sales = pd.DataFrame()

    for product_id in product_ids_to_try:
        if product_id is None or pd.isna(product_id):
            continue

        matched_sales = sales_df[
            sales_df[product_column].astype(str) == str(int(product_id))
        ]

        if not matched_sales.empty:
            break

    if matched_sales.empty:
        return 0.0

    total_quantity = pd.to_numeric(
        matched_sales[quantity_column],
        errors="coerce",
    ).fillna(0).sum()

    if "dateKey" in matched_sales.columns:
        number_of_days = matched_sales["dateKey"].nunique()
    elif "Date" in matched_sales.columns:
        number_of_days = matched_sales["Date"].nunique()
    else:
        number_of_days = max(len(matched_sales), 1)

    if number_of_days <= 0:
        return 0.0

    return float(total_quantity / number_of_days)


def _build_alert(
    product_name: str,
    risk_level: str,
    current_stock: float,
    alert_threshold: float,
    days_to_stockout: float,
) -> StockMlAlert:
    if risk_level == "high":
        return StockMlAlert(
            active=True,
            severity="CRITIQUE",
            title="Alerte rupture de stock",
            message=(
                f"{product_name} présente un risque élevé de rupture. "
                f"Stock actuel: {current_stock:.0f}, seuil d’alerte: {alert_threshold:.0f}. "
                "Un réapprovisionnement urgent est recommandé."
            ),
        )

    if risk_level == "medium":
        return StockMlAlert(
            active=True,
            severity="MOYEN",
            title="Stock à surveiller",
            message=(
                f"{product_name} doit être surveillé. "
                f"Le stock couvre environ {days_to_stockout:.0f} jours de vente."
            ),
        )

    return StockMlAlert(
        active=False,
        severity="FAIBLE",
        title="Stock stable",
        message=(
            f"{product_name} ne présente pas de risque immédiat. "
            f"Le stock couvre environ {days_to_stockout:.0f} jours de vente."
        ),
    )


def _get_recommendation(risk_level: str) -> str:
    if risk_level == "high":
        return "Commander rapidement ce produit pour éviter une rupture."

    if risk_level == "medium":
        return "Surveiller le stock et prévoir une commande si la demande augmente."

    return "Aucune action urgente. Continuer le suivi normal du stock."


def _get_risk_label(risk_level: str) -> str:
    if risk_level == "high":
        return "Risque élevé"

    if risk_level == "medium":
        return "Risque moyen"

    return "Risque faible"


def analyze_stock_ml_product_service(
    request: StockMlAnalyzeRequest,
) -> StockMlAnalysisResponse:
    product_row = _get_product_by_name(request.product_name)

    product_name = _clean_string(product_row.get("ProductName"))
    category = _clean_string(product_row.get("ProductCategory"))

    current_stock = _safe_float(product_row.get("StockQuantity"))
    alert_threshold = _safe_float(product_row.get("AlertQuantity"))
    stock_value = _safe_float(product_row.get("StockValue"))
    category_encoded = int(_safe_float(product_row.get("ProductCategory_enc")))

    average_daily_sales = _compute_average_daily_sales(product_row)

    if average_daily_sales > 0:
        estimated_days_before_stockout = current_stock / average_daily_sales
    else:
        estimated_days_before_stockout = 999.0 if current_stock > 0 else 0.0

    stock_coverage = estimated_days_before_stockout

    max_stock_value = 1.0

    if products_df is not None and "StockValue" in products_df.columns:
        max_stock_value = max(
            pd.to_numeric(products_df["StockValue"], errors="coerce").fillna(0).max(),
            1.0,
        )

    stock_value_ratio = stock_value / max_stock_value

    technical_request = StockMlPredictRequest(
        StockQuantity=current_stock,
        AlertQuantity=alert_threshold,
        avg_daily_sales=average_daily_sales,
        stock_coverage=stock_coverage,
        stock_value_ratio=stock_value_ratio,
        days_to_stockout=estimated_days_before_stockout,
        StockValue=stock_value,
        ProductCategory_enc=category_encoded,
    )

    prediction = predict_stock_ml_service(technical_request)

    alert = _build_alert(
        product_name=product_name,
        risk_level=prediction.risk_level,
        current_stock=current_stock,
        alert_threshold=alert_threshold,
        days_to_stockout=estimated_days_before_stockout,
    )

    response = StockMlAnalysisResponse(
        product_name=product_name,
        category=category,
        current_stock=round(current_stock, 2),
        alert_threshold=round(alert_threshold, 2),
        average_daily_sales=round(average_daily_sales, 2),
        estimated_days_before_stockout=round(estimated_days_before_stockout, 2),
        risk_level=prediction.risk_level,
        risk_label=_get_risk_label(prediction.risk_level),
        confidence=prediction.confidence,
        alert=alert,
        recommendation=_get_recommendation(prediction.risk_level),
    )

    if response.alert.active:
        existing_index = next(
            (
                index
                for index, item in enumerate(active_alerts)
                if item.product_name.lower() == response.product_name.lower()
            ),
            None,
        )

        if existing_index is not None:
            active_alerts[existing_index] = response
        else:
            active_alerts.insert(0, response)

    return response


def get_stock_ml_alerts_service() -> list[StockMlAnalysisResponse]:
    return active_alerts

