"""
Ensemble de modelos para classificação de variantes genômicas.

Este módulo implementa um ensemble stacking com calibração de probabilidades
e quantificação de incerteza via conformal prediction.

Author: VariantClassifier Team
Date: January 2026
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

import joblib
import numpy as np
import pandas as pd
from numpy.typing import NDArray
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.calibration import CalibratedClassifierCV
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_predict
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier

try:
    from catboost import CatBoostClassifier
except ImportError:
    CatBoostClassifier = None  # type: ignore


logger = logging.getLogger(__name__)

# Constantes de classificação ACMG
ACMG_CLASSES = [
    "Benign",
    "Likely_Benign",
    "VUS",  # Variant of Uncertain Significance
    "Likely_Pathogenic",
    "Pathogenic"
]

CLASS_WEIGHTS = {
    "Benign": 1.0,
    "Likely_Benign": 1.2,
    "VUS": 0.8,
    "Likely_Pathogenic": 1.5,
    "Pathogenic": 2.0
}


@dataclass
class ModelConfig:
    """Configuração dos modelos base do ensemble."""

    xgboost_params: dict[str, Any] = field(default_factory=lambda: {
        "n_estimators": 500,
        "max_depth": 6,
        "learning_rate": 0.05,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "objective": "multi:softprob",
        "num_class": 5,
        "eval_metric": "mlogloss",
        "random_state": 42,
        "n_jobs": -1,
        "verbosity": 0
    })

    lightgbm_params: dict[str, Any] = field(default_factory=lambda: {
        "n_estimators": 500,
        "max_depth": 8,
        "learning_rate": 0.05,
        "num_leaves": 63,
        "feature_fraction": 0.8,
        "bagging_fraction": 0.8,
        "bagging_freq": 5,
        "objective": "multiclass",
        "num_class": 5,
        "metric": "multi_logloss",
        "random_state": 42,
        "n_jobs": -1,
        "verbose": -1
    })

    catboost_params: dict[str, Any] = field(default_factory=lambda: {
        "iterations": 500,
        "depth": 6,
        "learning_rate": 0.05,
        "loss_function": "MultiClass",
        "classes_count": 5,
        "random_seed": 42,
        "verbose": False,
        "thread_count": -1
    })


class VariantClassifierEnsemble(BaseEstimator, ClassifierMixin):
    """
    Ensemble stacking para classificação de variantes genômicas.

    Combina XGBoost, LightGBM e CatBoost usando meta-learner logístico
    com calibração de probabilidades isotônica.

    Attributes:
        config: Configuração dos hiperparâmetros
        classes_: Classes do modelo
        base_models_: Modelos base treinados
        meta_learner_: Meta-learner treinado
        calibrator_: Calibrador de probabilidades
        is_fitted_: Flag indicando se modelo está treinado

    Example:
        >>> ensemble = VariantClassifierEnsemble()
        >>> ensemble.fit(X_train, y_train)
        >>> probas = ensemble.predict_proba(X_test)
        >>> predictions = ensemble.predict(X_test)
    """

    def __init__(
        self,
        config: ModelConfig | None = None,
        calibration_method: Literal["isotonic", "sigmoid"] = "isotonic",
        calibration_cv: int = 5,
        use_catboost: bool = False  # Desabilitado por padrão se não instalado
    ):
        self.config = config or ModelConfig()
        self.calibration_method = calibration_method
        self.calibration_cv = calibration_cv
        self.use_catboost = use_catboost and CatBoostClassifier is not None

        self.classes_ = np.array(ACMG_CLASSES)
        self.base_models_: dict[str, BaseEstimator] = {}
        self.meta_learner_: LogisticRegression | None = None
        self.calibrator_: CalibratedClassifierCV | None = None
        self.is_fitted_ = False

    def _init_base_models(self) -> dict[str, BaseEstimator]:
        """Inicializa os modelos base do ensemble."""
        models = {
            "xgboost": XGBClassifier(**self.config.xgboost_params),
            "lightgbm": LGBMClassifier(**self.config.lightgbm_params)
        }

        if self.use_catboost:
            models["catboost"] = CatBoostClassifier(**self.config.catboost_params)

        return models

    def _get_meta_features(
        self,
        X: NDArray | pd.DataFrame,
        y: NDArray | None = None,
        fit: bool = False
    ) -> NDArray:
        """
        Gera meta-features a partir das predições dos modelos base.

        Args:
            X: Features de entrada
            y: Labels (necessário apenas se fit=True)
            fit: Se True, usa cross_val_predict para evitar overfitting

        Returns:
            Array de meta-features (N, n_models * n_classes)
        """
        meta_features_list = []

        for name, model in self.base_models_.items():
            if fit:
                # Durante treino: usa CV para evitar overfitting
                probas = cross_val_predict(
                    model, X, y,
                    cv=5,
                    method="predict_proba",
                    n_jobs=-1
                )
            else:
                # Durante inferência: usa predição direta
                probas = model.predict_proba(X)

            meta_features_list.append(probas)

        return np.hstack(meta_features_list)

    def fit(
        self,
        X: NDArray | pd.DataFrame,
        y: NDArray,
        eval_set: tuple[NDArray, NDArray] | None = None,
        sample_weight: NDArray | None = None
    ) -> "VariantClassifierEnsemble":
        """
        Treina o ensemble completo.

        Args:
            X: Features de treinamento
            y: Labels de treinamento
            eval_set: Conjunto de validação opcional (X_val, y_val)
            sample_weight: Pesos das amostras

        Returns:
            Self (instância treinada)
        """
        logger.info("Iniciando treinamento do ensemble...")

        # Converte labels para índices se necessário
        if y.dtype == object:
            y_encoded = np.array([
                np.where(self.classes_ == label)[0][0]
                for label in y
            ])
        else:
            y_encoded = y

        # Inicializa e treina modelos base
        self.base_models_ = self._init_base_models()

        for name, model in self.base_models_.items():
            logger.info(f"Treinando modelo base: {name}")

            fit_params = {}
            if sample_weight is not None:
                fit_params["sample_weight"] = sample_weight

            if eval_set is not None and name in ["xgboost", "lightgbm"]:
                X_val, y_val = eval_set
                if y_val.dtype == object:
                    y_val_encoded = np.array([
                        np.where(self.classes_ == label)[0][0]
                        for label in y_val
                    ])
                else:
                    y_val_encoded = y_val

                fit_params["eval_set"] = [(X_val, y_val_encoded)]

            model.fit(X, y_encoded, **fit_params)

        # Gera meta-features e treina meta-learner
        logger.info("Treinando meta-learner...")
        meta_features = self._get_meta_features(X, y_encoded, fit=True)

        self.meta_learner_ = LogisticRegression(
            C=1.0,
            max_iter=1000,
            solver="lbfgs",
            random_state=42,
            n_jobs=-1
        )
        self.meta_learner_.fit(meta_features, y_encoded)

        # Calibra probabilidades
        logger.info("Calibrando probabilidades...")
        self.calibrator_ = CalibratedClassifierCV(
            self.meta_learner_,
            method=self.calibration_method,
            cv=self.calibration_cv
        )
        self.calibrator_.fit(meta_features, y_encoded)

        self.is_fitted_ = True
        logger.info("Treinamento concluído!")

        return self

    def predict_proba(self, X: NDArray | pd.DataFrame) -> NDArray:
        """
        Prediz probabilidades calibradas para cada classe.

        Args:
            X: Features de entrada

        Returns:
            Array de probabilidades (N, n_classes)
        """
        if not self.is_fitted_:
            raise ValueError("Modelo não treinado. Execute fit() primeiro.")

        meta_features = self._get_meta_features(X, fit=False)
        return self.calibrator_.predict_proba(meta_features)

    def predict(
        self,
        X: NDArray | pd.DataFrame,
        threshold_pathogenic: float = 0.5
    ) -> NDArray:
        """
        Prediz classificação ACMG.

        Args:
            X: Features de entrada
            threshold_pathogenic: Threshold para classes patogênicas
                                 (mais conservador se > 0.5)

        Returns:
            Array de classificações preditas
        """
        probas = self.predict_proba(X)

        # Aplica threshold conservador para patogênicas
        predictions = []
        for proba in probas:
            # Índices: 0=B, 1=LB, 2=VUS, 3=LP, 4=P
            if proba[4] >= threshold_pathogenic:
                pred_idx = 4  # Pathogenic
            elif proba[3] >= threshold_pathogenic:
                pred_idx = 3  # Likely Pathogenic
            else:
                pred_idx = np.argmax(proba)
            predictions.append(pred_idx)

        return self.classes_[predictions]

    def predict_with_uncertainty(
        self,
        X: NDArray | pd.DataFrame,
        alpha: float = 0.1
    ) -> dict[str, Any]:
        """
        Prediz com quantificação de incerteza via conformal prediction.

        Args:
            X: Features de entrada
            alpha: Nível de significância (1-alpha = cobertura)

        Returns:
            Dict com predições, probabilidades e conjuntos de predição
        """
        probas = self.predict_proba(X)
        predictions = self.predict(X)

        # Conformal prediction: conjunto de classes plausíveis
        prediction_sets = []
        for proba in probas:
            # Ordena classes por probabilidade decrescente
            sorted_idx = np.argsort(proba)[::-1]
            cumsum = np.cumsum(proba[sorted_idx])

            # Inclui classes até atingir 1-alpha de cobertura
            n_classes = np.searchsorted(cumsum, 1 - alpha) + 1
            plausible_classes = self.classes_[sorted_idx[:n_classes]]
            prediction_sets.append(plausible_classes.tolist())

        return {
            "predictions": predictions,
            "probabilities": probas,
            "prediction_sets": prediction_sets,
            "confidence": 1 - alpha
        }

    def save(self, path: str | Path) -> None:
        """Salva modelo treinado em disco."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        model_state = {
            "config": self.config,
            "base_models": self.base_models_,
            "meta_learner": self.meta_learner_,
            "calibrator": self.calibrator_,
            "classes": self.classes_,
            "use_catboost": self.use_catboost
        }
        joblib.dump(model_state, path)
        logger.info(f"Modelo salvo em: {path}")

    @classmethod
    def load(cls, path: str | Path) -> "VariantClassifierEnsemble":
        """Carrega modelo treinado do disco."""
        path = Path(path)
        model_state = joblib.load(path)

        instance = cls(
            config=model_state["config"],
            use_catboost=model_state["use_catboost"]
        )
        instance.base_models_ = model_state["base_models"]
        instance.meta_learner_ = model_state["meta_learner"]
        instance.calibrator_ = model_state["calibrator"]
        instance.classes_ = model_state["classes"]
        instance.is_fitted_ = True

        logger.info(f"Modelo carregado de: {path}")
        return instance
