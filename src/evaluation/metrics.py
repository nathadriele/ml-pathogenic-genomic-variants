"""
Métricas de avaliação para classificação de variantes genômicas.

Inclui métricas padrão de ML e métricas específicas para contexto clínico
como concordância ACMG e análise de erro clínico.

Author: VariantClassifier Team
Date: January 2026
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd
from numpy.typing import NDArray
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    cohen_kappa_score,
    confusion_matrix,
    f1_score,
    roc_auc_score,
    average_precision_score,
    log_loss,
    brier_score_loss
)
from sklearn.calibration import calibration_curve


ACMG_CLASSES = [
    "Benign",
    "Likely_Benign",
    "VUS",  # Variant of Uncertain Significance
    "Likely_Pathogenic",
    "Pathogenic"
]

# Mapeamento para análise clínica binária
CLINICAL_MAPPING = {
    "Benign": "Non-Pathogenic",
    "Likely_Benign": "Non-Pathogenic",
    "VUS": "Uncertain",
    "Likely_Pathogenic": "Pathogenic",
    "Pathogenic": "Pathogenic"
}


@dataclass
class ClassificationMetrics:
    """Container para métricas de classificação."""

    accuracy: float
    balanced_accuracy: float
    macro_f1: float
    weighted_f1: float
    cohen_kappa: float
    roc_auc_macro: float
    roc_auc_weighted: float
    average_precision_macro: float
    log_loss_value: float

    per_class_f1: dict[str, float]
    per_class_precision: dict[str, float]
    per_class_recall: dict[str, float]

    confusion_matrix: NDArray
    classification_report_str: str


@dataclass
class CalibrationMetrics:
    """Container para métricas de calibração."""

    expected_calibration_error: float
    maximum_calibration_error: float
    brier_score: float
    reliability_diagram_data: dict[str, NDArray]


@dataclass
class ClinicalMetrics:
    """Container para métricas de relevância clínica."""

    # Concordância com classificação ACMG
    acmg_concordance: float

    # Erros críticos (Patogênica classificada como Benigna ou vice-versa)
    critical_error_rate: float
    critical_errors: pd.DataFrame

    # Sensibilidade para variantes patogênicas
    pathogenic_sensitivity: float
    pathogenic_specificity: float

    # Taxa de VUS (objetivo: minimizar)
    vus_rate: float

    # Concordância binária (Patogênico vs Não-Patogênico)
    binary_concordance: float


def compute_classification_metrics(
    y_true: NDArray,
    y_pred: NDArray,
    y_proba: NDArray,
    labels: list[str] = ACMG_CLASSES
) -> ClassificationMetrics:
    """
    Calcula métricas completas de classificação.

    Args:
        y_true: Labels verdadeiros
        y_pred: Labels preditos
        y_proba: Probabilidades preditas (N, n_classes)
        labels: Lista ordenada de labels

    Returns:
        ClassificationMetrics com todas as métricas
    """
    # Métricas gerais
    accuracy = accuracy_score(y_true, y_pred)
    balanced_acc = balanced_accuracy_score(y_true, y_pred)
    macro_f1 = f1_score(y_true, y_pred, labels=labels, average="macro")
    weighted_f1 = f1_score(y_true, y_pred, labels=labels, average="weighted")
    kappa = cohen_kappa_score(y_true, y_pred, labels=labels)

    # One-hot encoding para ROC-AUC
    y_true_onehot = np.zeros((len(y_true), len(labels)))
    for i, label in enumerate(y_true):
        if label in labels:
            y_true_onehot[i, labels.index(label)] = 1

    roc_auc_macro = roc_auc_score(
        y_true_onehot, y_proba,
        average="macro",
        multi_class="ovr"
    )
    roc_auc_weighted = roc_auc_score(
        y_true_onehot, y_proba,
        average="weighted",
        multi_class="ovr"
    )

    ap_macro = average_precision_score(
        y_true_onehot, y_proba,
        average="macro"
    )

    logloss = log_loss(y_true, y_proba, labels=labels)

    # Métricas por classe
    report = classification_report(
        y_true, y_pred,
        labels=labels,
        output_dict=True,
        zero_division=0
    )

    per_class_f1 = {label: report[label]["f1-score"] for label in labels if label in report}
    per_class_precision = {label: report[label]["precision"] for label in labels if label in report}
    per_class_recall = {label: report[label]["recall"] for label in labels if label in report}

    cm = confusion_matrix(y_true, y_pred, labels=labels)
    report_str = classification_report(y_true, y_pred, labels=labels)

    return ClassificationMetrics(
        accuracy=accuracy,
        balanced_accuracy=balanced_acc,
        macro_f1=macro_f1,
        weighted_f1=weighted_f1,
        cohen_kappa=kappa,
        roc_auc_macro=roc_auc_macro,
        roc_auc_weighted=roc_auc_weighted,
        average_precision_macro=ap_macro,
        log_loss_value=logloss,
        per_class_f1=per_class_f1,
        per_class_precision=per_class_precision,
        per_class_recall=per_class_recall,
        confusion_matrix=cm,
        classification_report_str=report_str
    )


def compute_calibration_metrics(
    y_true: NDArray,
    y_proba: NDArray,
    labels: list[str] = ACMG_CLASSES,
    n_bins: int = 10
) -> CalibrationMetrics:
    """
    Calcula métricas de calibração de probabilidades.

    Args:
        y_true: Labels verdadeiros
        y_proba: Probabilidades preditas
        labels: Lista ordenada de labels
        n_bins: Número de bins para reliability diagram

    Returns:
        CalibrationMetrics com ECE, MCE, Brier score
    """
    # Converte para one-hot
    y_true_onehot = np.zeros((len(y_true), len(labels)))
    for i, label in enumerate(y_true):
        if label in labels:
            y_true_onehot[i, labels.index(label)] = 1

    # Brier score (média sobre classes)
    brier_scores = []
    for i in range(len(labels)):
        brier = brier_score_loss(y_true_onehot[:, i], y_proba[:, i])
        brier_scores.append(brier)
    brier_score_mean = np.mean(brier_scores)

    # ECE e MCE (Expected/Maximum Calibration Error)
    ece_per_class = []
    mce_per_class = []
    reliability_data = {"prob_true": [], "prob_pred": [], "class": []}

    for i, label in enumerate(labels):
        prob_true, prob_pred = calibration_curve(
            y_true_onehot[:, i],
            y_proba[:, i],
            n_bins=n_bins,
            strategy="uniform"
        )

        # Calcula ECE para esta classe
        bin_totals = np.histogram(y_proba[:, i], bins=n_bins, range=(0, 1))[0]
        bin_totals = bin_totals / len(y_proba)

        if len(prob_true) > 0:
            ece = np.sum(bin_totals[:len(prob_true)] * np.abs(prob_true - prob_pred))
            mce = np.max(np.abs(prob_true - prob_pred))
            ece_per_class.append(ece)
            mce_per_class.append(mce)

            reliability_data["prob_true"].extend(prob_true)
            reliability_data["prob_pred"].extend(prob_pred)
            reliability_data["class"].extend([label] * len(prob_true))

    ece = np.mean(ece_per_class) if ece_per_class else 0.0
    mce = np.max(mce_per_class) if mce_per_class else 0.0

    return CalibrationMetrics(
        expected_calibration_error=ece,
        maximum_calibration_error=mce,
        brier_score=brier_score_mean,
        reliability_diagram_data={
            "prob_true": np.array(reliability_data["prob_true"]),
            "prob_pred": np.array(reliability_data["prob_pred"]),
            "class": reliability_data["class"]
        }
    )


def compute_clinical_metrics(
    y_true: NDArray,
    y_pred: NDArray,
    variant_ids: NDArray | None = None,
    labels: list[str] = ACMG_CLASSES
) -> ClinicalMetrics:
    """
    Calcula métricas de relevância clínica para genética médica.

    Args:
        y_true: Labels verdadeiros
        y_pred: Labels preditos
        variant_ids: IDs das variantes (para rastreio de erros)
        labels: Lista ordenada de labels

    Returns:
        ClinicalMetrics com concordância ACMG e análise de erros críticos
    """
    if variant_ids is None:
        variant_ids = np.arange(len(y_true))

    # Concordância exata com ACMG
    acmg_concordance = accuracy_score(y_true, y_pred)

    # Identifica erros críticos
    critical_errors_list = []
    for i, (true_label, pred_label, var_id) in enumerate(
        zip(y_true, y_pred, variant_ids)
    ):
        # Erro crítico: Patogênica -> Benigna ou vice-versa
        is_critical = (
            (true_label in ["Pathogenic", "Likely_Pathogenic"] and
             pred_label in ["Benign", "Likely_Benign"]) or
            (true_label in ["Benign", "Likely_Benign"] and
             pred_label in ["Pathogenic", "Likely_Pathogenic"])
        )

        if is_critical:
            critical_errors_list.append({
                "variant_id": var_id,
                "true_label": true_label,
                "predicted_label": pred_label,
                "error_type": "False_Negative" if "Pathogenic" in true_label else "False_Positive"
            })

    critical_errors_df = pd.DataFrame(critical_errors_list)
    critical_error_rate = len(critical_errors_list) / len(y_true)

    # Sensibilidade e especificidade para patogênicas
    y_true_binary = np.array([
        1 if label in ["Pathogenic", "Likely_Pathogenic"] else 0
        for label in y_true
    ])
    y_pred_binary = np.array([
        1 if label in ["Pathogenic", "Likely_Pathogenic"] else 0
        for label in y_pred
    ])

    # True positives, etc.
    tp = np.sum((y_true_binary == 1) & (y_pred_binary == 1))
    tn = np.sum((y_true_binary == 0) & (y_pred_binary == 0))
    fp = np.sum((y_true_binary == 0) & (y_pred_binary == 1))
    fn = np.sum((y_true_binary == 1) & (y_pred_binary == 0))

    pathogenic_sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    pathogenic_specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0

    # Taxa de VUS
    vus_rate = np.sum(y_pred == "VUS") / len(y_pred)

    # Concordância binária (excluindo VUS)
    mask_no_vus = (y_true != "VUS") & (y_pred != "VUS")
    if np.sum(mask_no_vus) > 0:
        y_true_binary_no_vus = np.array([
            "Pathogenic" if label in ["Pathogenic", "Likely_Pathogenic"]
            else "Non-Pathogenic"
            for label in y_true[mask_no_vus]
        ])
        y_pred_binary_no_vus = np.array([
            "Pathogenic" if label in ["Pathogenic", "Likely_Pathogenic"]
            else "Non-Pathogenic"
            for label in y_pred[mask_no_vus]
        ])
        binary_concordance = accuracy_score(y_true_binary_no_vus, y_pred_binary_no_vus)
    else:
        binary_concordance = 0.0

    return ClinicalMetrics(
        acmg_concordance=acmg_concordance,
        critical_error_rate=critical_error_rate,
        critical_errors=critical_errors_df,
        pathogenic_sensitivity=pathogenic_sensitivity,
        pathogenic_specificity=pathogenic_specificity,
        vus_rate=vus_rate,
        binary_concordance=binary_concordance
    )


def generate_evaluation_report(
    y_true: NDArray,
    y_pred: NDArray,
    y_proba: NDArray,
    variant_ids: NDArray | None = None,
    output_format: Literal["dict", "markdown"] = "dict"
) -> dict | str:
    """
    Gera relatório completo de avaliação do modelo.

    Args:
        y_true: Labels verdadeiros
        y_pred: Labels preditos
        y_proba: Probabilidades preditas
        variant_ids: IDs das variantes
        output_format: Formato de saída

    Returns:
        Relatório completo em dict ou markdown
    """
    cls_metrics = compute_classification_metrics(y_true, y_pred, y_proba)
    cal_metrics = compute_calibration_metrics(y_true, y_proba)
    clin_metrics = compute_clinical_metrics(y_true, y_pred, variant_ids)

    report = {
        "classification": {
            "accuracy": cls_metrics.accuracy,
            "balanced_accuracy": cls_metrics.balanced_accuracy,
            "macro_f1": cls_metrics.macro_f1,
            "cohen_kappa": cls_metrics.cohen_kappa,
            "roc_auc_macro": cls_metrics.roc_auc_macro,
            "per_class_f1": cls_metrics.per_class_f1
        },
        "calibration": {
            "ece": cal_metrics.expected_calibration_error,
            "mce": cal_metrics.maximum_calibration_error,
            "brier_score": cal_metrics.brier_score
        },
        "clinical": {
            "acmg_concordance": clin_metrics.acmg_concordance,
            "critical_error_rate": clin_metrics.critical_error_rate,
            "pathogenic_sensitivity": clin_metrics.pathogenic_sensitivity,
            "pathogenic_specificity": clin_metrics.pathogenic_specificity,
            "vus_rate": clin_metrics.vus_rate,
            "binary_concordance": clin_metrics.binary_concordance
        },
        "confusion_matrix": cls_metrics.confusion_matrix.tolist(),
        "n_critical_errors": len(clin_metrics.critical_errors)
    }

    if output_format == "markdown":
        return _format_report_markdown(report, clin_metrics.critical_errors)

    return report


def _format_report_markdown(report: dict, critical_errors: pd.DataFrame) -> str:
    """Formata relatório em markdown."""
    md = """# Relatório de Avaliação do Modelo

## Métricas de Classificação

| Métrica | Valor |
|---------|-------|
| Acurácia | {accuracy:.4f} |
| Acurácia Balanceada | {balanced_accuracy:.4f} |
| F1-Score (Macro) | {macro_f1:.4f} |
| Cohen's Kappa | {cohen_kappa:.4f} |
| ROC-AUC (Macro) | {roc_auc_macro:.4f} |

### F1-Score por Classe

| Classe | F1-Score |
|--------|----------|
""".format(**report["classification"])

    for cls, f1 in report["classification"]["per_class_f1"].items():
        md += f"| {cls} | {f1:.4f} |\n"

    md += """
## Métricas de Calibração

| Métrica | Valor |
|---------|-------|
| ECE | {ece:.4f} |
| MCE | {mce:.4f} |
| Brier Score | {brier_score:.4f} |

## Métricas Clínicas

| Métrica | Valor |
|---------|-------|
| Concordância ACMG | {acmg_concordance:.4f} |
| Taxa de Erros Críticos | {critical_error_rate:.4f} |
| Sensibilidade (Patogênicas) | {pathogenic_sensitivity:.4f} |
| Especificidade (Patogênicas) | {pathogenic_specificity:.4f} |
| Taxa de VUS | {vus_rate:.4f} |
| Concordância Binária | {binary_concordance:.4f} |
""".format(**report["calibration"], **report["clinical"])

    if len(critical_errors) > 0:
        md += f"\n## Erros Críticos ({len(critical_errors)} casos)\n\n"
        md += critical_errors.head(10).to_markdown(index=False)

    return md
