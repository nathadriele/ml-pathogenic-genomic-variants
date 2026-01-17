#!/usr/bin/env python3
"""
Script de treinamento do modelo de classificação de variantes.

Integra pré-processamento, treinamento do ensemble, e avaliação completa.

Author: VariantClassifier Team
Date: January 2026
"""

import argparse
import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

# Configura logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Importa módulos do projeto
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.modeling.preprocessing import VariantPreprocessor
from src.modeling.ensemble import VariantClassifierEnsemble, ModelConfig
from src.evaluation.metrics import (
    generate_evaluation_report,
    compute_classification_metrics,
    compute_calibration_metrics,
    compute_clinical_metrics
)


def load_data(
    train_path: str | Path,
    val_path: str | Path,
    test_path: str | Path
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Carrega datasets de treino, validação e teste.

    Args:
        train_path: Caminho para CSV de treino
        val_path: Caminho para CSV de validação
        test_path: Caminho para CSV de teste

    Returns:
        Tupla (train_df, val_df, test_df)
    """
    logger.info("Carregando datasets...")

    train_df = pd.read_csv(train_path)
    val_df = pd.read_csv(val_path)
    test_df = pd.read_csv(test_path)

    logger.info(f"Treino: {len(train_df)} variantes")
    logger.info(f"Validação: {len(val_df)} variantes")
    logger.info(f"Teste: {len(test_df)} variantes")

    return train_df, val_df, test_df


def prepare_features(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
    target_column: str = "classification"
) -> tuple[Any, Any, Any, Any, Any, Any, VariantPreprocessor]:
    """
    Prepara features e targets para treinamento.

    Args:
        train_df: DataFrame de treino
        val_df: DataFrame de validação
        test_df: DataFrame de teste
        target_column: Nome da coluna target

    Returns:
        Tupla (X_train, X_val, X_test, y_train, y_val, y_test, preprocessor)
    """
    logger.info("Preparando features...")

    # Separa features e target
    X_train = train_df.drop(columns=[target_column])
    y_train = train_df[target_column]

    X_val = val_df.drop(columns=[target_column])
    y_val = val_df[target_column]

    X_test = test_df.drop(columns=[target_column])
    y_test = test_df[target_column]

    # Inicializa e fit preprocessor
    preprocessor = VariantPreprocessor(scale_numerical=False)
    preprocessor.fit(X_train, y_train)

    # Transforma dados
    X_train_proc = preprocessor.transform(X_train)
    X_val_proc = preprocessor.transform(X_val)
    X_test_proc = preprocessor.transform(X_test)

    # Encode targets
    y_train_enc = preprocessor.encode_target(y_train)
    y_val_enc = preprocessor.encode_target(y_val)
    y_test_enc = preprocessor.encode_target(y_test)

    logger.info(f"Features após pré-processamento: {X_train_proc.shape[1]}")
    logger.info(f"Classes: {list(preprocessor.get_class_names())}")

    return (
        X_train_proc, X_val_proc, X_test_proc,
        y_train_enc, y_val_enc, y_test_enc,
        preprocessor
    )


def train_model(
    X_train: pd.DataFrame,
    y_train: np.ndarray,
    X_val: pd.DataFrame,
    y_val: np.ndarray,
    use_catboost: bool = False
) -> VariantClassifierEnsemble:
    """
    Treina o modelo ensemble.

    Args:
        X_train: Features de treino
        y_train: Target de treino
        X_val: Features de validação
        y_val: Target de validação
        use_catboost: Se True, inclui CatBoost no ensemble

    Returns:
        Modelo treinado
    """
    logger.info("Iniciando treinamento do ensemble...")

    # Cria modelo
    model = VariantClassifierEnsemble(
        config=ModelConfig(),
        calibration_method="isotonic",
        calibration_cv=5,
        use_catboost=use_catboost
    )

    # Treina
    eval_set = (X_val, y_val)
    model.fit(
        X_train,
        y_train,
        eval_set=eval_set
    )

    logger.info("✅ Treinamento concluído!")

    return model


def evaluate_model(
    model: VariantClassifierEnsemble,
    X_test: pd.DataFrame,
    y_test: np.ndarray,
    preprocessor: VariantPreprocessor
) -> dict[str, Any]:
    """
    Avalia o modelo no conjunto de teste.

    Args:
        model: Modelo treinado
        X_test: Features de teste
        y_test: Target de teste (encoded)
        preprocessor: Preprocessor ajustado

    Returns:
        Dicionário com métricas
    """
    logger.info("Avaliando modelo no conjunto de teste...")

    # Decodifica y_test
    y_test_decoded = preprocessor.decode_target(y_test)

    # Predições
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)

    # IDs das variantes (para rastreamento de erros)
    variant_ids = np.arange(len(y_test))

    # Calcula métricas
    cls_metrics = compute_classification_metrics(
        y_test_decoded, y_pred, y_proba
    )

    cal_metrics = compute_calibration_metrics(
        y_test_decoded, y_proba
    )

    clin_metrics = compute_clinical_metrics(
        y_test_decoded, y_pred, variant_ids
    )

    # Log das principais métricas
    logger.info(f"\n{'='*60}")
    logger.info("RESULTADOS DA AVALIAÇÃO")
    logger.info(f"{'='*60}")
    logger.info(f"\n📊 Classificação:")
    logger.info(f"  Acurácia:              {cls_metrics.accuracy:.4f}")
    logger.info(f"  Acurácia Balanceada:   {cls_metrics.balanced_accuracy:.4f}")
    logger.info(f"  F1-Score (Macro):      {cls_metrics.macro_f1:.4f}")
    logger.info(f"  Cohen's Kappa:         {cls_metrics.cohen_kappa:.4f}")
    logger.info(f"  ROC-AUC (Macro):       {cls_metrics.roc_auc_macro:.4f}")

    logger.info(f"\n🎯 Calibração:")
    logger.info(f"  ECE:                   {cal_metrics.expected_calibration_error:.4f}")
    logger.info(f"  MCE:                   {cal_metrics.maximum_calibration_error:.4f}")
    logger.info(f"  Brier Score:           {cal_metrics.brier_score:.4f}")

    logger.info(f"\n🏥 Clínicas:")
    logger.info(f"  Concordância ACMG:     {clin_metrics.acmg_concordance:.4f}")
    logger.info(f"  Taxa de Erros Críticos:{clin_metrics.critical_error_rate:.4f}")
    logger.info(f"  Sensibilidade (Patho): {clin_metrics.pathogenic_sensitivity:.4f}")
    logger.info(f"  Especificidade (Patho):{clin_metrics.pathogenic_specificity:.4f}")
    logger.info(f"  Taxa de VUS:           {clin_metrics.vus_rate:.4f}")
    logger.info(f"  Concordância Binária:  {clin_metrics.binary_concordance:.4f}")
    logger.info(f"{'='*60}\n")

    # Gera relatório completo
    report = generate_evaluation_report(
        y_test_decoded, y_pred, y_proba, variant_ids,
        output_format="dict"
    )

    return report


def save_artifacts(
    model: VariantClassifierEnsemble,
    preprocessor: VariantPreprocessor,
    report: dict[str, Any],
    output_dir: str | Path
) -> None:
    """
    Salva artefatos do treinamento.

    Args:
        model: Modelo treinado
        preprocessor: Preprocessor
        report: Relatório de avaliação
        output_dir: Diretório de saída
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Salva modelo
    model_path = output_dir / "ensemble_model.joblib"
    model.save(model_path)
    logger.info(f"💾 Modelo salvo em: {model_path}")

    # Salva preprocessor
    preprocessor_path = output_dir / "preprocessor.joblib"
    preprocessor.save(preprocessor_path)
    logger.info(f"💾 Preprocessor salvo em: {preprocessor_path}")

    # Salva relatório
    report_path = output_dir / "evaluation_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    logger.info(f"💾 Relatório salvo em: {report_path}")

    # Salva relatório em markdown
    report_md_path = output_dir / "evaluation_report.md"
    with open(report_md_path, "w") as f:
        # Regenera relatório em markdown
        pass  # TODO: implementar
    logger.info(f"💾 Relatório MD salvo em: {report_md_path}")


def main():
    """Função principal."""
    parser = argparse.ArgumentParser(
        description="Treinar modelo de classificação de variantes"
    )
    parser.add_argument(
        "--train-path",
        type=str,
        default="data/splits/train.csv",
        help="Caminho para CSV de treino"
    )
    parser.add_argument(
        "--val-path",
        type=str,
        default="data/splits/val.csv",
        help="Caminho para CSV de validação"
    )
    parser.add_argument(
        "--test-path",
        type=str,
        default="data/splits/test.csv",
        help="Caminho para CSV de teste"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="models",
        help="Diretório de saída para modelo e artefatos"
    )
    parser.add_argument(
        "--use-catboost",
        action="store_true",
        help="Incluir CatBoost no ensemble"
    )
    parser.add_argument(
        "--skip-training",
        action="store_true",
        help="Pular treinamento e apenas avaliar modelo existente"
    )

    args = parser.parse_args()

    try:
        # Carrega dados
        train_df, val_df, test_df = load_data(
            args.train_path,
            args.val_path,
            args.test_path
        )

        # Prepara features
        (
            X_train, X_val, X_test,
            y_train, y_val, y_test,
            preprocessor
        ) = prepare_features(train_df, val_df, test_df)

        # Treina modelo (se não skip)
        if not args.skip_training:
            model = train_model(
                X_train, y_train,
                X_val, y_val,
                use_catboost=args.use_catboost
            )

            # Salva artefatos
            # (ainda não temos report, salva apenas modelo e preprocessor)
            output_dir = Path(args.output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

            model_path = output_dir / "ensemble_model.joblib"
            model.save(model_path)

            preprocessor_path = output_dir / "preprocessor.joblib"
            preprocessor.save(preprocessor_path)

            logger.info(f"✅ Modelo salvo em: {model_path}")
            logger.info(f"✅ Preprocessor salvo em: {preprocessor_path}")

        # Avalia modelo
        # Recarrega modelo se skip_training
        if args.skip_training:
            logger.info("Carregando modelo existente...")
            model_path = Path(args.output_dir) / "ensemble_model.joblib"
            preprocessor_path = Path(args.output_dir) / "preprocessor.joblib"

            model = VariantClassifierEnsemble.load(model_path)
            preprocessor = VariantPreprocessor.load(preprocessor_path)

        # Avalia
        report = evaluate_model(model, X_test, y_test, preprocessor)

        # Salva relatório
        report_path = Path(args.output_dir) / "evaluation_report.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2, default=str)
        logger.info(f"✅ Relatório salvo em: {report_path}")

        logger.info("\n🎉 Treinamento concluído com sucesso!")

    except Exception as e:
        logger.error(f"❌ Erro durante treinamento: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
