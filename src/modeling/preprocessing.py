"""
Pipeline de pré-processamento e feature engineering.

Realiza transformações nos dados brutos para prepará-los para os modelos ML,
incluindo encoding de categóricas, imputação de valores ausentes e scaling.

Author: VariantClassifier Team
Date: January 2026
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Final

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import (
    LabelEncoder,
    StandardScaler,
    OrdinalEncoder
)
from numpy.typing import NDArray


# Features por tipo
NUMERICAL_FEATURES: Final = [
    "position",
    "gnomad_af",
    "gnomad_af_popmax",
    "revel_score",
    "cadd_phred",
    "spliceai_max",
    "phylop_100way",
    "gerp_rs",
    "consequence_severity",
    "clinvar_submissions",
    "gene_pli",
    "gene_loeuf",
    "gene_missense_z",
    "aa_change_grantham",
    "protein_position_normalized"
]

CATEGORICAL_FEATURES: Final = [
    "variant_type",
    "consequence",
    "transcript_biotype",
    "domain_annotation",
    "inheritance_mode"
]

BOOLEAN_FEATURES: Final = [
    "is_absent_gnomad",
    "is_lof",
    "is_missense",
    "is_splice_region",
    "has_functional_study",
    "is_disease_gene",
    "is_active_site"
]

# Features que devem ser excluídas do modelo
FEATURES_TO_DROP: Final = [
    "chromosome",
    "ref",
    "alt",
    "gene_symbol",
    "clinvar_stars"  # Data leakage: muito correlacionado com target
]

# Target
TARGET_COLUMN: Final = "classification"

ACMG_CLASSES: Final = ["Benign", "Likely_Benign", "Variant_of_Uncertain_Significance",
                       "Likely_Pathogenic", "Pathogenic"]


class VariantPreprocessor(BaseEstimator, TransformerMixin):
    """
    Pipeline completo de pré-processamento para variantes genômicas.

    Realiza:
    1. Drop de colunas desnecessárias
    2. Imputação de valores ausentes
    3. Encoding de variáveis categóricas
    4. Escala de features numéricas (opcional)

    Attributes:
        numerical_features: Lista de features numéricas
        categorical_features: Lista de features categóricas
        boolean_features: Lista de features booleanas
        scale_numerical: Se True, aplica StandardScaler
        label_encoder: Encoder para o target
        ordinal_encoder: Encoder para categóricas
        scaler: Scaler para numéricas (se scale_numerical=True)
        fitted_: Se o pré-processador foi fitted
    """

    def __init__(
        self,
        numerical_features: list[str] | None = None,
        categorical_features: list[str] | None = None,
        boolean_features: list[str] | None = None,
        scale_numerical: bool = False
    ):
        """
        Inicializa o pré-processador.

        Args:
            numerical_features: Lista de features numéricas
            categorical_features: Lista de features categóricas
            boolean_features: Lista de features booleanas
            scale_numerical: Se True, aplica StandardScaler nas numéricas
        """
        self.numerical_features = numerical_features or NUMERICAL_FEATURES.copy()
        self.categorical_features = categorical_features or CATEGORICAL_FEATURES.copy()
        self.boolean_features = boolean_features or BOOLEAN_FEATURES.copy()
        self.scale_numerical = scale_numerical

        self.label_encoder = LabelEncoder()
        self.ordinal_encoder = OrdinalEncoder(
            handle_unknown="use_encoded_value",
            unknown_value=-1
        )
        self.scaler = StandardScaler() if scale_numerical else None

        self.fitted_ = False

    def fit(self, X: pd.DataFrame, y: pd.Series | None = None) -> "VariantPreprocessor":
        """
        Fit do pré-processador nos dados.

        Args:
            X: DataFrame com features
            y: Series com target (opcional, necessário para label encoding)

        Returns:
            Self
        """
        # Cria cópia para não modificar original
        X = X.copy()

        # Fit label encoder se y fornecido
        if y is not None:
            self.label_encoder.fit(y)

        # Imputa valores ausentes em categóricas antes do encoding
        for col in self.categorical_features:
            if col in X.columns:
                X[col] = X[col].fillna("Unknown")

        # Fit ordinal encoder
        if self.categorical_features:
            cat_data = X[self.categorical_features].values
            self.ordinal_encoder.fit(cat_data)

        # Fit scaler se solicitado
        if self.scale_numerical and self.numerical_features:
            num_data = X[self.numerical_features].values
            self.scaler.fit(num_data)

        self.fitted_ = True
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Transforma os dados usando o pré-processador fitted.

        Args:
            X: DataFrame com features

        Returns:
            DataFrame transformado
        """
        if not self.fitted_:
            raise ValueError("Preprocessor não fitted. Execute fit() primeiro.")

        X = X.copy()

        # Drop de features desnecessárias
        cols_to_drop = [col for col in FEATURES_TO_DROP if col in X.columns]
        if cols_to_drop:
            X = X.drop(columns=cols_to_drop)

        # Imputa valores ausentes
        X = self._impute_missing(X)

        # Garante tipos corretos
        X = self._ensure_dtypes(X)

        # Encode categóricas
        if self.categorical_features:
            cat_data = X[self.categorical_features].values
            encoded = self.ordinal_encoder.transform(cat_data)
            for i, col in enumerate(self.categorical_features):
                X[col] = encoded[:, i]

        # Converte booleanas para int
        for col in self.boolean_features:
            if col in X.columns:
                X[col] = X[col].astype(int)

        # Escala numéricas se solicitado
        if self.scale_numerical and self.scaler is not None:
            num_data = X[self.numerical_features].values
            scaled = self.scaler.transform(num_data)
            for i, col in enumerate(self.numerical_features):
                X[col] = scaled[:, i]

        return X

    def fit_transform(self, X: pd.DataFrame, y: pd.Series | None = None) -> pd.DataFrame:
        """Fit e transforma em uma única operação."""
        return self.fit(X, y).transform(X)

    def _impute_missing(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Imputa valores ausentes.

        Estratégia:
        - Numéricas: mediana
        - Categóricas: "Unknown"
        - Booleanas: False
        """
        X = X.copy()

        # Numéricas
        for col in self.numerical_features:
            if col in X.columns and X[col].isnull().any():
                median_val = X[col].median()
                X[col] = X[col].fillna(median_val)

        # Categóricas
        for col in self.categorical_features:
            if col in X.columns and X[col].isnull().any():
                X[col] = X[col].fillna("Unknown")

        # Booleanas
        for col in self.boolean_features:
            if col in X.columns and X[col].isnull().any():
                X[col] = X[col].fillna(False)

        return X

    def _ensure_dtypes(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Garante que as colunas tenham os tipos de dados corretos.

        Args:
            X: DataFrame com tipos possivelmente incorretos

        Returns:
            DataFrame com tipos corrigidos
        """
        X = X.copy()

        # Converte numéricas para float/int
        for col in self.numerical_features:
            if col in X.columns:
                # Tenta converter para int primeiro, depois float
                try:
                    X[col] = pd.to_numeric(X[col], errors="coerce")
                    # Se for exon_number ou position, converte para int
                    if col in ["exon_number", "position"]:
                        X[col] = X[col].fillna(0).astype(int)
                except Exception:
                    pass

        # Converte categóricas para string
        for col in self.categorical_features:
            if col in X.columns:
                X[col] = X[col].astype(str)

        # Converte booleanas para bool
        for col in self.boolean_features:
            if col in X.columns:
                X[col] = X[col].astype(bool)

        return X

    def encode_target(self, y: pd.Series | NDArray) -> NDArray:
        """
        Encode do target (classes ACMG).

        Args:
            y: Labels originais

        Returns:
            Labels encoded (0 a n_classes-1)
        """
        if not self.fitted_:
            raise ValueError("Preprocessor não fitted. Execute fit() com y primeiro.")

        return self.label_encoder.transform(y)

    def decode_target(self, y_encoded: NDArray) -> NDArray:
        """
        Decode do target (numérico para string).

        Args:
            y_encoded: Labels encoded

        Returns:
            Labels originais (string)
        """
        if not self.fitted_:
            raise ValueError("Preprocessor não fitted. Execute fit() com y primeiro.")

        return self.label_encoder.inverse_transform(y_encoded)

    def get_feature_names(self) -> list[str]:
        """Retorna nome das features após pré-processamento."""
        feature_names = (
            self.numerical_features +
            self.categorical_features +
            self.boolean_features
        )
        return feature_names

    def get_class_names(self) -> list[str]:
        """Retorna nome das classes ACMG."""
        return list(self.label_encoder.classes_)

    def save(self, path: str | Path) -> None:
        """Salva o pré-processador em disco."""
        import joblib

        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        joblib.dump({
            "numerical_features": self.numerical_features,
            "categorical_features": self.categorical_features,
            "boolean_features": self.boolean_features,
            "scale_numerical": self.scale_numerical,
            "label_encoder": self.label_encoder,
            "ordinal_encoder": self.ordinal_encoder,
            "scaler": self.scaler,
            "fitted_": self.fitted_
        }, path)

    @classmethod
    def load(cls, path: str | Path) -> "VariantPreprocessor":
        """Carrega o pré-processador do disco."""
        import joblib

        path = Path(path)
        data = joblib.load(path)

        instance = cls(
            numerical_features=data["numerical_features"],
            categorical_features=data["categorical_features"],
            boolean_features=data["boolean_features"],
            scale_numerical=data["scale_numerical"]
        )
        instance.label_encoder = data["label_encoder"]
        instance.ordinal_encoder = data["ordinal_encoder"]
        instance.scaler = data["scaler"]
        instance.fitted_ = data["fitted_"]

        return instance


def load_and_split_data(
    data_path: str | Path,
    train_path: str | Path | None = None,
    val_path: str | Path | None = None,
    test_path: str | Path | None = None
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Carrega dados de treino, validação e teste.

    Args:
        data_path: Caminho para dataset completo
        train_path: Caminho para split de treino (opcional)
        val_path: Caminho para split de validação (opcional)
        test_path: Caminho para split de teste (opcional)

    Returns:
        Tupla (train_df, val_df, test_df)
    """
    # Se splits individuais fornecidos, usa eles
    if train_path and val_path and test_path:
        train_df = pd.read_csv(train_path)
        val_df = pd.read_csv(val_path)
        test_df = pd.read_csv(test_path)
        return train_df, val_df, test_df

    # Caso contrário, carrega dataset completo
    df = pd.read_csv(data_path)

    # Split estratificado (70/15/15)
    if 'pathogenicity' in df.columns:
        # Primeiro split: 70% treino, 30% temp
        train_df, temp_df = train_test_split(
            df,
            test_size=0.3,
            stratify=df['pathogenicity'],
            random_state=42
        )

        # Segundo split: 50% de temp para val, 50% para test (15% cada)
        val_df, test_df = train_test_split(
            temp_df,
            test_size=0.5,
            stratify=temp_df['pathogenicity'],
            random_state=42
        )

        return train_df, val_df, test_df
    else:
        # Se não tiver coluna target, split simples
        train_df, temp_df = train_test_split(df, test_size=0.3, random_state=42)
        val_df, test_df = train_test_split(temp_df, test_size=0.5, random_state=42)
        return train_df, val_df, test_df


def create_sample_weights(
    y: NDArray,
    class_weights: dict[int, float] | None = None,
    class_names: list[str] | None = None
) -> NDArray:
    """
    Cria pesos das amostras para treino balanceado.

    Args:
        y: Labels encoded (índices inteiros)
        class_weights: Dicionário com pesos por classe (índice -> peso)
        class_names: Lista de nomes das classes (opcional, para gerar pesos automáticos)

    Returns:
        Array com pesos para cada amostra
    """
    # Se não fornecido, calcula pesos inversamente proporcionais à frequência
    if class_weights is None and class_names is not None:
        unique, counts = np.unique(y, return_counts=True)
        total = len(y)
        n_classes = len(unique)

        # Pesos balanceados: total / (n_classes * count_class)
        class_weights = {}
        for idx, count in zip(unique, counts):
            class_weights[int(idx)] = total / (n_classes * count)

    # Pesos padrão se nem class_weights nem class_names fornecidos
    if class_weights is None:
        class_weights = {0: 1.0, 1: 1.2, 2: 0.8, 3: 1.5, 4: 2.0}

    # Mapeia pesos para cada amostra
    weights = np.array([class_weights.get(int(label), 1.0) for label in y])

    return weights
