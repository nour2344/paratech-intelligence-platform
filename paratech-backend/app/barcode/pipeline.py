import os
import pickle
from typing import Any

import cv2
import pandas as pd
from pyzbar.pyzbar import decode
from ultralytics import YOLO


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "model_files")

TFIDF_PATH = os.path.join(MODEL_DIR, "tfidf.pkl")
COSINE_PATH = os.path.join(MODEL_DIR, "cosine_sim.pkl")
PRODUCTS_PATH = os.path.join(MODEL_DIR, "products.csv")
YOLO_PATH = os.path.join(MODEL_DIR, "yolov8n.pt")


tfidf = None
cosine_sim = None
products = None
yolo_model = None
pipeline_loaded = False
pipeline_error = None


def load_barcode_pipeline() -> None:
    global tfidf, cosine_sim, products, yolo_model, pipeline_loaded, pipeline_error

    try:
        tfidf = pickle.load(open(TFIDF_PATH, "rb"))
        cosine_sim = pickle.load(open(COSINE_PATH, "rb"))
        products = pd.read_csv(PRODUCTS_PATH)
        yolo_model = YOLO(YOLO_PATH)

        pipeline_loaded = True
        pipeline_error = None

        print(f"Barcode pipeline loaded successfully: {len(products)} products")

    except Exception as error:
        pipeline_loaded = False
        pipeline_error = str(error)
        print(f"Barcode pipeline loading failed: {pipeline_error}")


def get_pipeline_status() -> dict[str, Any]:
    return {
        "loaded": pipeline_loaded,
        "error": pipeline_error,
        "model_dir": MODEL_DIR,
        "products_count": 0 if products is None else len(products),
    }


def detect_barcode_region(image):
    if yolo_model is None:
        return image

    results = yolo_model(image, verbose=False)
    best_crop = None
    best_confidence = 0.0

    for result in results:
        for box in result.boxes:
            confidence = float(box.conf[0])
            x1, y1, x2, y2 = map(int, box.xyxy[0])

            if confidence > best_confidence:
                best_confidence = confidence
                best_crop = image[y1:y2, x1:x2]

    return best_crop if best_crop is not None else image


def decode_barcode(image):
    region = detect_barcode_region(image)
    barcodes = decode(region)

    if not barcodes:
        barcodes = decode(image)

    if not barcodes:
        return None

    return barcodes[0].data.decode("utf-8")


def find_product_by_barcode(barcode: str):
    if products is None:
        return None

    barcode = str(barcode)

    possible_columns = ["Barcode", "RawBarcode", "barcode", "raw_barcode"]

    for column in possible_columns:
        if column in products.columns:
            match = products[products[column].astype(str) == barcode]
            if not match.empty:
                return match.iloc[0], match.index[0]

    return None


def get_recommendations_by_index(product_index: int, top_n: int = 5):
    if products is None or cosine_sim is None:
        return []

    similarity_scores = sorted(
        enumerate(cosine_sim[product_index]),
        key=lambda item: item[1],
        reverse=True,
    )

    similarity_scores = [
        item for item in similarity_scores if item[0] != product_index
    ][:top_n]

    recommendations = []

    for index, score in similarity_scores:
        product = products.iloc[index]

        recommendations.append(
            {
                "product_id": int(product["ProductId"])
                if "ProductId" in product and pd.notna(product["ProductId"])
                else index,
                "product_name": str(product.get("ProductName", "")),
                "product_category": str(product.get("ProductCategory", "")),
                "similarity_score": round(float(score), 4),
            }
        )

    return recommendations


def run_barcode_scan(image):
    if not pipeline_loaded:
        return {
            "success": False,
            "barcode": None,
            "product": None,
            "recommendations": [],
            "error": f"Barcode pipeline not loaded: {pipeline_error}",
        }

    barcode = decode_barcode(image)

    if not barcode:
        return {
            "success": False,
            "barcode": None,
            "product": None,
            "recommendations": [],
            "error": "No barcode detected in image",
        }

    product_result = find_product_by_barcode(barcode)

    if not product_result:
        return {
            "success": False,
            "barcode": barcode,
            "product": None,
            "recommendations": [],
            "error": f"Product not found for barcode: {barcode}",
        }

    product, product_index = product_result
    recommendations = get_recommendations_by_index(product_index)

    return {
        "success": True,
        "barcode": barcode,
        "product": {
            "product_id": str(product.get("ProductId", "")),
            "product_name": str(product.get("ProductName", "")),
            "product_category": str(product.get("ProductCategory", "")),
            "product_description": str(product.get("ProductDescription", "")),
            "stock_quantity": str(product.get("StockQuantity", "")),
            "stock_value": str(product.get("StockValue", "")),
            "tva": str(product.get("Tva", "")),
            "alert_quantity": str(product.get("AlertQuantity", "")),
        },
        "recommendations": recommendations,
        "error": None,
    }