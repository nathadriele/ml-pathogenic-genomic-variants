"""
API FastAPI para classificação de variantes genômicas.

Author: VariantClassifier Team
Date: January 2026
"""

import time
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.api.schemas import (
    PredictionRequest,
    BatchPredictionRequest,
    PredictionResult,
    BatchPredictionResult,
    HealthResponse,
    ErrorResponse
)
from src.modeling.ensemble import VariantClassifierEnsemble
from src.modeling.preprocessing import VariantPreprocessor


# Configuração
API_TITLE = "VariantClassifier API"
API_VERSION = "1.0.0"
MODEL_PATH = Path("models/ensemble_model.joblib")
PREPROCESSOR_PATH = Path("models/preprocessor.joblib")

# Inicializa FastAPI
app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description="API for genomic variant classification following ACMG/AMP guidelines",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Variáveis globais para modelo e preprocessor
model: VariantClassifierEnsemble | None = None
preprocessor: VariantPreprocessor | None = None


@app.on_event("startup")
async def startup_event():
    """Carrega modelo e preprocessor ao iniciar a API."""
    global model, preprocessor

    logger.info("Iniciando API...")

    try:
        # Carrega modelo
        if MODEL_PATH.exists():
            logger.info(f"Carregando modelo de {MODEL_PATH}...")
            model = VariantClassifierEnsemble.load(MODEL_PATH)
            logger.info("Modelo carregado com sucesso!")
        else:
            logger.error(f"Modelo não encontrado em {MODEL_PATH}")
            raise FileNotFoundError(f"Model not found: {MODEL_PATH}")

        # Carrega preprocessor
        if PREPROCESSOR_PATH.exists():
            logger.info(f"Carregando preprocessor de {PREPROCESSOR_PATH}...")
            preprocessor = VariantPreprocessor.load(PREPROCESSOR_PATH)
            logger.info("Preprocessor carregado com sucesso!")
        else:
            logger.error(f"Preprocessor não encontrado em {PREPROCESSOR_PATH}")
            raise FileNotFoundError(f"Preprocessor not found: {PREPROCESSOR_PATH}")

        logger.info("API iniciada com sucesso!")

    except Exception as e:
        logger.error(f"Erro ao iniciar API: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Limpeza ao desligar a API."""
    logger.info("Desligando API...")


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Verifica saúde da API.

    Returns:
        HealthResponse com status dos componentes
    """
    return HealthResponse(
        status="healthy",
        model_loaded=model is not None,
        preprocessor_loaded=preprocessor is not None,
        version=API_VERSION
    )


@app.post("/predict", response_model=PredictionResult, tags=["Prediction"])
async def predict_variant(request: PredictionRequest) -> PredictionResult:
    """
    Classifica uma única variante genômica.

    Args:
        request: PredictionRequest com features da variante

    Returns:
        PredictionResult com classificação e probabilidades

    Raises:
        HTTPException: Se erro na predição
    """
    if model is None or preprocessor is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model or preprocessor not loaded"
        )

    try:
        start_time = time.time()

        # Converte para DataFrame
        variant_dict = request.variant.model_dump()
        df = pd.DataFrame([variant_dict])

        # Pré-processa
        df_processed = preprocessor.transform(df)

        # Prediz
        probabilities = model.predict_proba(df_processed)[0]
        classification = model.predict(df_processed)[0]
        confidence = np.max(probabilities)

        # Cria resultado
        class_names = preprocessor.get_class_names()
        prob_dict = {class_names[i]: float(prob) for i, prob in enumerate(probabilities)}

        processing_time = (time.time() - start_time) * 1000
        logger.info(f"Predição concluída em {processing_time:.2f}ms: {classification}")

        return PredictionResult(
            classification=classification,
            confidence=float(confidence),
            probabilities=prob_dict
        )

    except Exception as e:
        logger.error(f"Erro na predição: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction error: {str(e)}"
        )


@app.post("/predict/batch", response_model=BatchPredictionResult, tags=["Prediction"])
async def predict_batch(request: BatchPredictionRequest) -> BatchPredictionResult:
    """
    Classifica múltiplas variantes em lote.

    Args:
        request: BatchPredictionRequest com lista de variantes

    Returns:
        BatchPredictionResult com predições de todas as variantes

    Raises:
        HTTPException: Se erro na predição
    """
    if model is None or preprocessor is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model or preprocessor not loaded"
        )

    try:
        start_time = time.time()

        # Converte para DataFrame
        variants_dict = [v.model_dump() for v in request.variants]
        df = pd.DataFrame(variants_dict)

        # Pré-processa
        df_processed = preprocessor.transform(df)

        # Prediz
        probabilities = model.predict_proba(df_processed)
        classifications = model.predict(df_processed)

        # Cria resultados
        class_names = preprocessor.get_class_names()
        predictions = []

        for i, (classification, proba) in enumerate(zip(classifications, probabilities)):
            confidence = np.max(proba)
            prob_dict = {class_names[j]: float(p) for j, p in enumerate(proba)}

            predictions.append(
                PredictionResult(
                    classification=classification,
                    confidence=float(confidence),
                    probabilities=prob_dict
                )
            )

        processing_time = (time.time() - start_time) * 1000
        logger.info(f"Predição em lote de {len(df)} variantes concluída em {processing_time:.2f}ms")

        return BatchPredictionResult(
            predictions=predictions,
            total_variants=len(df),
            processing_time_ms=processing_time
        )

    except Exception as e:
        logger.error(f"Erro na predição em lote: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch prediction error: {str(e)}"
        )


@app.get("/model/info", tags=["Model"])
async def model_info():
    """
    Retorna informações sobre o modelo carregado.

    Returns:
        Dict com metadados do modelo
    """
    if model is None or preprocessor is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model or preprocessor not loaded"
    )

    return {
        "model_type": "Ensemble (XGBoost + LightGBM + LogisticRegression)",
        "classes": preprocessor.get_class_names(),
        "n_features": len(preprocessor.get_feature_names()),
        "calibration_method": model.calibration_method,
        "use_catboost": model.use_catboost,
        "version": API_VERSION
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handler global de exceções."""
    logger.error(f"Unhandled exception: {exc}")

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "status_code": 500
        }
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
