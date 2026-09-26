import os
from typing import Any

import pandas as pd
from fastapi import HTTPException, status

from app.demand.forecasting import CSV_PATH, forecast_product_api


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DIM_PRODUCTS_CSV_PATH = os.path.join(
    BASE_DIR,
    "data",
    "dimProducts.csv",
)


def clean_json_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cleaned_records = []

    for record in records:
        cleaned_record = {}

        for key, value in record.items():
            if pd.isna(value):
                cleaned_record[key] = None
            elif isinstance(value, float) and value.is_integer():
                cleaned_record[key] = int(value)
            else:
                cleaned_record[key] = value

        cleaned_records.append(cleaned_record)

    return cleaned_records


def forecast_demand_service(product_id: int, horizon: int):
    if horizon <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Horizon must be greater than 0",
        )

    try:
        return forecast_product_api(
            product_id=product_id,
            horizon=horizon,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )

    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Demand forecasting failed: {str(error)}",
        )


def get_existing_sales_product_keys() -> set[int]:
    sales = pd.read_csv(CSV_PATH, sep="|")
    sales.columns = sales.columns.str.strip()

    if "ProductKey" not in sales.columns:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Column ProductKey not found in factSales.csv. Found: {sales.columns.tolist()}",
        )

    return set(
        pd.to_numeric(sales["ProductKey"], errors="coerce")
        .dropna()
        .astype(int)
        .unique()
        .tolist()
    )


def load_dim_products() -> pd.DataFrame:
    if not os.path.exists(DIM_PRODUCTS_CSV_PATH):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"dimProducts.csv not found: {DIM_PRODUCTS_CSV_PATH}",
        )

    products = pd.read_csv(DIM_PRODUCTS_CSV_PATH, sep="|")
    products.columns = products.columns.str.strip()

    required_columns = {"ProductId", "ProductName"}
    missing = required_columns - set(products.columns)

    if missing:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Missing columns in dimProducts.csv: {missing}. Found: {products.columns.tolist()}",
        )

    products["ProductId"] = pd.to_numeric(products["ProductId"], errors="coerce")
    products = products.dropna(subset=["ProductId", "ProductName"])

    products["ProductId"] = products["ProductId"].astype(int)
    products["ProductName"] = products["ProductName"].astype(str)

    return products


def get_forecastable_products():
    products = load_dim_products()
    sales_product_keys = get_existing_sales_product_keys()

    forecastable = products[products["ProductId"].isin(sales_product_keys)].copy()

    selected_columns = ["ProductId", "ProductName"]

    if "ProductCategory" in forecastable.columns:
        selected_columns.append("ProductCategory")

    if "ProductSubCategory" in forecastable.columns:
        selected_columns.append("ProductSubCategory")

    if "Brand" in forecastable.columns:
        selected_columns.append("Brand")

    forecastable = forecastable[selected_columns]
    forecastable = forecastable.sort_values("ProductName")

    records = forecastable.to_dict(orient="records")

    return clean_json_records(records)


def find_product_by_name(product_name: str):
    searched_name = product_name.strip().lower()

    if not searched_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product name is required",
        )

    products = load_dim_products()
    sales_product_keys = get_existing_sales_product_keys()

    products["ProductName_clean"] = (
        products["ProductName"]
        .astype(str)
        .str.lower()
        .str.strip()
    )

    forecastable_products = products[products["ProductId"].isin(sales_product_keys)]

    exact_match = forecastable_products[
        forecastable_products["ProductName_clean"] == searched_name
    ]

    if not exact_match.empty:
        product = exact_match.iloc[0]
        return int(product["ProductId"]), str(product["ProductName"])

    partial_match = forecastable_products[
        forecastable_products["ProductName_clean"].str.contains(searched_name, na=False)
    ]

    if not partial_match.empty:
        product = partial_match.iloc[0]
        return int(product["ProductId"]), str(product["ProductName"])

    all_products_match = products[
        products["ProductName_clean"].str.contains(searched_name, na=False)
    ]

    if not all_products_match.empty:
        product = all_products_match.iloc[0]

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Product '{product['ProductName']}' exists in dimProducts.csv "
                f"with ProductId {int(product['ProductId'])}, but it has no sales history "
                f"in factSales.csv. Choose a product from /demand/products."
            ),
        )

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Product name not found: {product_name}",
    )


def forecast_demand_by_name_service(product_name: str, horizon: int):
    product_key, real_product_name = find_product_by_name(product_name)

    result = forecast_demand_service(
        product_id=product_key,
        horizon=horizon,
    )

    result["product_name"] = real_product_name

    return result