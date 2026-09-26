# -*- coding: utf-8 -*-

import os
import warnings

import joblib
import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd
from prophet import Prophet
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from xgboost import XGBRegressor

warnings.filterwarnings("ignore")
mlflow.set_experiment("demand_forecasting")
# =========================================================
# CONFIG
# =========================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "data", "factSales.csv")
FORECAST_DAYS_7 = 7
FORECAST_DAYS_30 = 30


# =========================================================
# LOAD + PREPARE DATA
# =========================================================
def load_and_prepare_data(csv_path: str) -> pd.DataFrame:
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"File not found: {csv_path}")

    df = pd.read_csv(csv_path, sep="|")
    df.columns = df.columns.str.strip()

    required_cols = {"Product_Id", "TotalQuantitySold", "date_Id"}
    missing = required_cols - set(df.columns)

    if missing:
        raise ValueError(f"Missing required columns in CSV: {missing}")

    df["date_Id"] = pd.to_datetime(
        df["date_Id"],
        unit="D",
        origin="2024-01-01",
    )

    df = df.rename(
        columns={
            "Product_Id": "ProductId",
            "TotalQuantitySold": "Quantity",
            "date_Id": "MovementDate",
        }
    )

    df["ProductId"] = pd.to_numeric(df["ProductId"], errors="coerce")
    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")

    df = df.dropna(subset=["ProductId", "Quantity", "MovementDate"])
    df["ProductId"] = df["ProductId"].astype(int)
    df["Quantity"] = df["Quantity"].astype(float)

    daily_sales = (
        df.groupby(["ProductId", "MovementDate"], as_index=False)
        .agg({"Quantity": "sum"})
        .sort_values(["ProductId", "MovementDate"])
    )

    return daily_sales


# =========================================================
# PRODUCT SELECTION
# =========================================================
def choose_product(daily_sales: pd.DataFrame, product_id: int | None = None) -> int:
    if product_id is not None:
        available = daily_sales["ProductId"].unique()

        if product_id not in available:
            raise ValueError(f"ProductId {product_id} not found in dataset.")

        return product_id

    counts = daily_sales.groupby("ProductId").size().sort_values(ascending=False)
    chosen = int(counts.index[0])

    print(f"No product_id provided. Using product with most history: {chosen}")
    return chosen


# =========================================================
# PROPHET
# =========================================================
def load_and_prepare_data(csv_path: str) -> pd.DataFrame:
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"File not found: {csv_path}")

    df = pd.read_csv(csv_path, sep="|")
    df.columns = df.columns.str.strip()

    print("COLUMNS FOUND:")
    print(df.columns.tolist())

    # Support both possible CSV versions
    if {"Product_Id", "TotalQuantitySold", "date_Id"}.issubset(df.columns):
        product_col = "Product_Id"
        date_col = "date_Id"
        quantity_col = "TotalQuantitySold"

    elif {"ProductKey", "TotalQuantitySold", "dateKey"}.issubset(df.columns):
        product_col = "ProductKey"
        date_col = "dateKey"
        quantity_col = "TotalQuantitySold"

    else:
        raise ValueError(
            "Missing required columns in CSV. Expected either "
            "{'Product_Id', 'date_Id', 'TotalQuantitySold'} or "
            "{'ProductKey', 'dateKey', 'TotalQuantitySold'}. "
            f"Found columns: {df.columns.tolist()}"
        )

    # Convert date key to real date
    df[date_col] = pd.to_datetime(
        df[date_col],
        unit="D",
        origin="2024-01-01",
    )

    df = df.rename(
        columns={
            product_col: "ProductId",
            quantity_col: "Quantity",
            date_col: "MovementDate",
        }
    )

    df["ProductId"] = pd.to_numeric(df["ProductId"], errors="coerce")
    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")

    df = df.dropna(subset=["ProductId", "Quantity", "MovementDate"])
    df["ProductId"] = df["ProductId"].astype(int)
    df["Quantity"] = df["Quantity"].astype(float)

    daily_sales = (
        df.groupby(["ProductId", "MovementDate"], as_index=False)
        .agg({"Quantity": "sum"})
        .sort_values(["ProductId", "MovementDate"])
    )

    return daily_sales

# =========================================================
# XGBOOST FEATURES
# =========================================================
def add_xgb_features(product_df: pd.DataFrame) -> pd.DataFrame:
    df = product_df.copy().sort_values("MovementDate")

    df["lag_1"] = df["Quantity"].shift(1)
    df["lag_7"] = df["Quantity"].shift(7)
    df["rolling_7"] = df["Quantity"].rolling(7).mean()

    df["day_of_week"] = df["MovementDate"].dt.dayofweek
    df["month"] = df["MovementDate"].dt.month

    df = df.dropna().reset_index(drop=True)

    return df


# =========================================================
# XGBOOST
# =========================================================
def predict_future_xgb(model, history_df: pd.DataFrame, days: int) -> pd.DataFrame:
    history = history_df.copy().sort_values("MovementDate").reset_index(drop=True)
    predictions = []

    for _ in range(days):
        next_date = history["MovementDate"].max() + pd.Timedelta(days=1)

        lag_1 = history["Quantity"].iloc[-1]
        lag_7 = history["Quantity"].iloc[-7] if len(history) >= 7 else lag_1
        rolling_7 = history["Quantity"].tail(7).mean()

        row = pd.DataFrame(
            [
                {
                    "lag_1": lag_1,
                    "lag_7": lag_7,
                    "rolling_7": rolling_7,
                    "day_of_week": next_date.dayofweek,
                    "month": next_date.month,
                }
            ]
        )

        pred = float(model.predict(row)[0])
        pred = max(0.0, pred)

        predictions.append(
            {
                "Date": next_date,
                "PredictedQuantity": pred,
            }
        )

        history = pd.concat(
            [
                history,
                pd.DataFrame(
                    [
                        {
                            "MovementDate": next_date,
                            "Quantity": pred,
                        }
                    ]
                ),
            ],
            ignore_index=True,
        )

    return pd.DataFrame(predictions)


def run_xgboost(product_df: pd.DataFrame, future_days: int = 30):
    featured = add_xgb_features(product_df)

    if len(featured) < 20:
        raise ValueError(
            "Not enough data for XGBoost after feature engineering. Need more history."
        )

    features = ["lag_1", "lag_7", "rolling_7", "day_of_week", "month"]

    split_index = int(len(featured) * 0.8)

    train = featured.iloc[:split_index].copy()
    test = featured.iloc[split_index:].copy()

    X_train = train[features]
    y_train = train["Quantity"]

    X_test = test[features]
    y_test = test["Quantity"]

    with mlflow.start_run():
        model = XGBRegressor(
            n_estimators=200,
            max_depth=5,
            learning_rate=0.05,
            objective="reg:squarederror",
            random_state=42,
        )

        model.fit(X_train, y_train)

        y_pred = model.predict(X_test)

        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        r2 = r2_score(y_test, y_pred)

        mlflow.log_param("model", "XGBoost")
        mlflow.log_param("n_estimators", 200)
        mlflow.log_param("max_depth", 5)
        mlflow.log_param("learning_rate", 0.05)
        mlflow.log_param("future_days", future_days)

        mlflow.log_metric("mae", mae)
        mlflow.log_metric("rmse", rmse)
        mlflow.log_metric("r2", r2)

        os.makedirs("models", exist_ok=True)
        joblib.dump(model, "models/xgb_model.pkl")

        mlflow.sklearn.log_model(model, "model")

    future_forecast = predict_future_xgb(
        model,
        product_df[["MovementDate", "Quantity"]],
        future_days,
    )

    metrics = {
        "MAE": mae,
        "RMSE": rmse,
        "R2": r2,
    }

    return model, metrics, future_forecast, test, y_pred


# =========================================================
# API FUNCTION
# =========================================================
def forecast_product_api(product_id: int, horizon: int = 30) -> dict:
    daily_sales = load_and_prepare_data(CSV_PATH)

    if product_id not in daily_sales["ProductId"].unique():
        raise ValueError(f"Product {product_id} not found")

    product_df = daily_sales[daily_sales["ProductId"] == product_id].copy()

    _, xgb_metrics, future_forecast, _, _ = run_xgboost(
        product_df,
        future_days=horizon,
    )

    forecast_rows = []

    for _, row in future_forecast.iterrows():
        forecast_rows.append(
            {
                "date": str(pd.to_datetime(row["Date"]).date()),
                "predicted_quantity": float(round(row["PredictedQuantity"], 2)),
            }
        )

    return {
        "product_id": int(product_id),
        "model": "xgboost",
        "horizon": int(horizon),
        "metrics": {
            "mae": float(round(xgb_metrics["MAE"], 4)),
            "rmse": float(round(xgb_metrics["RMSE"], 4)),
            "r2": float(round(xgb_metrics["R2"], 4)),
        },
        "forecast": forecast_rows,
    }


# =========================================================
# MAIN TEST
# =========================================================
def main():
    daily_sales = load_and_prepare_data(CSV_PATH)
    product_id = choose_product(daily_sales)

    product_df = daily_sales[daily_sales["ProductId"] == product_id].copy()

    print(f"Product selected: {product_id}")

    _, xgb_metrics, xgb_30, _, _ = run_xgboost(
        product_df,
        future_days=FORECAST_DAYS_30,
    )

    print("===== XGBOOST RESULTS =====")
    print(f"MAE  : {xgb_metrics['MAE']:.4f}")
    print(f"RMSE : {xgb_metrics['RMSE']:.4f}")
    print(f"R2   : {xgb_metrics['R2']:.4f}")

    print("===== 30 DAYS FORECAST =====")
    print(xgb_30)


if __name__ == "__main__":
    print("🚀 Running training pipeline...")

    daily_sales = load_and_prepare_data(CSV_PATH)

    product_id = choose_product(daily_sales)
    product_df = daily_sales[daily_sales["ProductId"] == product_id].copy()

    model, metrics, forecast, _, _ = run_xgboost(product_df)

    print("✅ Training done")
    print(metrics)
