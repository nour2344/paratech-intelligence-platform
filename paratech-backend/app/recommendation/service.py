import json
import os
from datetime import datetime
from typing import Any

import joblib
import numpy as np
import pandas as pd
from fastapi import HTTPException
from sqlmodel import Session, select

from app.database import engine
from app.recommendation.models import RecommendationHistory


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "model_files")

PRODUCTS_PATH = os.path.join(MODEL_DIR, "products_df.pkl")
TFIDF_PATH = os.path.join(MODEL_DIR, "tfidf_vectorizer.pkl")
COSINE_PATH = os.path.join(MODEL_DIR, "cosine_similarity.pkl")


products_df: pd.DataFrame | None = None
tfidf_vectorizer: Any = None
cosine_similarity_matrix: Any = None


def load_recommendation_pipeline() -> None:
    global products_df, tfidf_vectorizer, cosine_similarity_matrix

    if not os.path.exists(PRODUCTS_PATH):
        raise RuntimeError(f"Missing file: {PRODUCTS_PATH}")

    if not os.path.exists(TFIDF_PATH):
        raise RuntimeError(f"Missing file: {TFIDF_PATH}")

    if not os.path.exists(COSINE_PATH):
        raise RuntimeError(f"Missing file: {COSINE_PATH}")

    products_df = joblib.load(PRODUCTS_PATH)
    tfidf_vectorizer = joblib.load(TFIDF_PATH)
    cosine_similarity_matrix = joblib.load(COSINE_PATH)

    products_df.columns = products_df.columns.str.strip()

    print("Recommendation model loaded.")
    print("Products:", len(products_df))
    print("Columns:", list(products_df.columns))


def ensure_pipeline_loaded() -> None:
    if products_df is None or tfidf_vectorizer is None or cosine_similarity_matrix is None:
        load_recommendation_pipeline()


def find_column(possible_names: list[str]) -> str | None:
    if products_df is None:
        return None

    for col in possible_names:
        if col in products_df.columns:
            return col

    return None


def clean_value(value: Any) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def build_product_text(df: pd.DataFrame) -> pd.Series:
    text_columns = []

    possible_text_columns = [
        "ProductName",
        "product_name",
        "name",
        "Name",
        "designation",
        "Product",
        "ProductCategory",
        "category",
        "Category",
        "Description",
        "description",
        "Brand",
        "brand",
    ]

    for col in possible_text_columns:
        if col in df.columns:
            text_columns.append(col)

    if not text_columns:
        raise HTTPException(
            status_code=500,
            detail=f"No text columns found in products dataframe. Columns: {list(df.columns)}",
        )

    return (
        df[text_columns]
        .fillna("")
        .astype(str)
        .agg(" ".join, axis=1)
        .str.lower()
        .str.strip()
    )


def format_product(row: pd.Series, score: float | None = None) -> dict:
    name_col = find_column(
        [
            "ProductName",
            "product_name",
            "name",
            "Name",
            "designation",
            "Product",
        ]
    )

    category_col = find_column(
        [
            "ProductCategory",
            "category",
            "Category",
            "categorie",
            "Categorie",
        ]
    )

    brand_col = find_column(
        [
            "Brand",
            "brand",
            "Marque",
            "marque",
        ]
    )

    price_col = find_column(
        [
            "ProductPrice",
            "price",
            "Price",
            "PrixTtc",
            "Prix",
            "prix",
        ]
    )

    product_id_col = find_column(
        [
            "ProductId",
            "ProductKey",
            "product_id",
            "id",
        ]
    )

    if name_col is None:
        raise HTTPException(
            status_code=500,
            detail=f"No product name column found. Columns: {list(products_df.columns)}",
        )

    result = {
        "name": clean_value(row[name_col]),
        "score": round(float(score), 4) if score is not None else None,
    }

    if product_id_col:
        try:
            result["product_id"] = int(row[product_id_col])
        except Exception:
            result["product_id"] = None

    if category_col:
        result["category"] = clean_value(row[category_col])

    if brand_col:
        result["brand"] = clean_value(row[brand_col])

    if price_col:
        try:
            result["price"] = float(row[price_col])
        except Exception:
            result["price"] = None

    return result


def recommend_by_product_name(query: str, top_n: int = 5) -> list[dict]:
    ensure_pipeline_loaded()

    if not query or not query.strip():
        raise HTTPException(
            status_code=400,
            detail="Product query is required.",
        )

    query_clean = query.lower().strip()
    df = products_df.copy()

    search_text = build_product_text(df)

    query_vector = tfidf_vectorizer.transform([query_clean])
    product_vectors = tfidf_vectorizer.transform(search_text)

    similarities = (product_vectors @ query_vector.T).toarray().ravel()

    best_score = float(np.max(similarities))

    if best_score <= 0:
        raise HTTPException(
            status_code=404,
            detail=f"No similar product found for '{query}'. Try another product name.",
        )

    base_index = int(np.argmax(similarities))

    print("Query:", query)
    print("Best matched product index:", base_index)
    print("Best score:", best_score)
    print("Best product:", format_product(df.iloc[base_index]))

    similarity_scores = list(enumerate(cosine_similarity_matrix[base_index]))
    similarity_scores = sorted(similarity_scores, key=lambda x: x[1], reverse=True)

    recommendations = []

    for idx, score in similarity_scores:
        if idx == base_index:
            continue

        if idx >= len(df):
            continue

        product = format_product(df.iloc[idx], score=float(score))
        recommendations.append(product)

        if len(recommendations) >= top_n:
            break

    return recommendations


def recommend_by_preferences(
    category: str | None = None,
    max_price: float | None = None,
    top_n: int = 5,
) -> list[dict]:
    ensure_pipeline_loaded()

    df = products_df.copy()

    category_col = find_column(
        [
            "ProductCategory",
            "category",
            "Category",
            "categorie",
            "Categorie",
        ]
    )

    price_col = find_column(
        [
            "ProductPrice",
            "price",
            "Price",
            "PrixTtc",
            "Prix",
            "prix",
        ]
    )

    if category and category_col:
        df = df[
            df[category_col]
            .fillna("")
            .astype(str)
            .str.lower()
            .str.contains(category.lower(), na=False)
        ]

    if max_price is not None and price_col:
        df[price_col] = pd.to_numeric(df[price_col], errors="coerce")
        df = df[df[price_col] <= float(max_price)]

    if df.empty:
        raise HTTPException(
            status_code=404,
            detail="No products found for these preferences.",
        )

    return [format_product(row, score=None) for _, row in df.head(top_n).iterrows()]


def save_recommendation_history(
    user_id: int,
    query: str,
    input_data: dict,
    recommended_products: list[dict],
) -> None:
    with Session(engine) as session:
        history = RecommendationHistory(
            user_id=user_id,
            query=query,
            input_data=json.dumps(input_data, ensure_ascii=False),
            recommended_products=json.dumps(recommended_products, ensure_ascii=False),
            created_at=datetime.utcnow(),
        )

        session.add(history)
        session.commit()


def predict_recommendation_service(request) -> dict:
    input_data = request.input_data or {}
    mode = input_data.get("mode", "content_based")

    if mode == "preference_based":
        recommendations = recommend_by_preferences(
            category=input_data.get("category"),
            max_price=input_data.get("max_price"),
            top_n=5,
        )
    else:
        recommendations = recommend_by_product_name(
            query=request.query,
            top_n=5,
        )

    save_recommendation_history(
        user_id=request.user_id,
        query=request.query,
        input_data=input_data,
        recommended_products=recommendations,
    )

    return {
        "message": "Recommendation generated successfully.",
        "recommended_products": recommendations,
    }


def get_user_recommendation_history_service(user_id: int):
    with Session(engine) as session:
        statement = (
            select(RecommendationHistory)
            .where(RecommendationHistory.user_id == user_id)
            .order_by(RecommendationHistory.created_at.desc())
        )

        return session.exec(statement).all()


def get_all_recommendation_history_service():
    with Session(engine) as session:
        statement = select(RecommendationHistory).order_by(
            RecommendationHistory.created_at.desc()
        )

        return session.exec(statement).all()