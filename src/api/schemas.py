"""
Pydantic schemas para API de classificação de variantes.

Author: VariantClassifier Team
Date: January 2026
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, validator


class VariantFeatures(BaseModel):
    """Features de uma variante genômica para predição."""

    # Metadados básicos
    chromosome: str = Field(..., description="Cromossomo (ex: chr1)")
    position: int = Field(..., ge=0, description="Posição genômica")
    variant_type: str = Field(..., description="Tipo de variante: SNV, insertion, deletion")
    ref: str = Field(..., description="Base de referência")
    alt: str = Field(..., description="Base alternativa")
    consequence: str = Field(..., description="Consequência funcional")
    exon_number: int = Field(None, ge=0, description="Número do exão")
    transcript_biotype: str = Field("protein_coding", description="Biotype do transcript")

    # Frequência populacional
    gnomad_af: float = Field(0.0, ge=0.0, le=1.0, description="Frequência alélica gnomAD")
    gnomad_af_popmax: float = Field(0.0, ge=0.0, le=1.0, description="Frequência máxima por população")
    is_absent_gnomad: bool = Field(False, description="Ausente em controles gnomAD")

    # Scores computacionais
    revel_score: float = Field(0.0, ge=0.0, le=1.0, description="REVEL score")
    cadd_phred: float = Field(0.0, ge=0.0, le=99.0, description="CADD Phred score")
    spliceai_max: float = Field(0.0, ge=0.0, le=1.0, description="SpliceAI score máximo")
    phylop_100way: float = Field(0.0, ge=0.0, description="Conservação Phylop")
    gerp_rs: float = Field(0.0, description="GERP++ RS score")

    # Features funcionais
    consequence_severity: int = Field(0, ge=0, le=10, description="Severidade da consequência")
    is_lof: bool = Field(False, description="Loss of function")
    is_missense: bool = Field(False, description="Missense variant")
    is_splice_region: bool = Field(False, description="Região de splice")

    # Evidências clínicas
    clinvar_stars: int = Field(0, ge=0, le=4, description="Nível de revisão ClinVar")
    clinvar_submissions: int = Field(0, ge=0, description="Número de submissões ClinVar")
    has_functional_study: bool = Field(False, description="Estudo funcional disponível")

    # Contexto do gene
    gene_symbol: str = Field(..., description="Símbolo do gene")
    gene_pli: float = Field(0.0, ge=0.0, le=1.0, description="pLI score do gene")
    gene_loeuf: float = Field(0.5, ge=0.0, description="LOEUF score")
    gene_missense_z: float = Field(0.0, description="Missense Z-score")
    is_disease_gene: bool = Field(True, description="Gene associado a doença")
    inheritance_mode: str = Field("AD", description="Modo de herança")

    # Contexto proteico
    domain_annotation: str = Field("None", description="Anotação de domínio")
    is_active_site: bool = Field(False, description="Sítio ativo")
    aa_change_grantham: float = Field(0.0, ge=0.0, description="Distância de Grantham")
    protein_position_normalized: float = Field(
        0.5, ge=0.0, le=1.0, description="Posição normalizada na proteína"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "chromosome": "chr17",
                "position": 43044295,
                "variant_type": "SNV",
                "ref": "G",
                "alt": "A",
                "consequence": "missense_variant",
                "gene_symbol": "BRCA1",
                "gnomad_af": 0.0,
                "revel_score": 0.94,
                "cadd_phred": 35.0
            }
        }


class PredictionRequest(BaseModel):
    """Request para predição de uma única variante."""

    variant: VariantFeatures


class BatchPredictionRequest(BaseModel):
    """Request para predição em lote de variantes."""

    variants: List[VariantFeatures] = Field(..., min_items=1, max_items=100)


class PredictionResult(BaseModel):
    """Resultado da predição de uma variante."""

    # Predição
    classification: str = Field(..., description="Classificação ACMG prevista")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confiança da predição")

    # Probabilidades por classe
    probabilities: Dict[str, float] = Field(..., description="Probabilidades por classe ACMG")

    # Incerteza (opcional)
    prediction_set: Optional[List[str]] = Field(
        None, description="Conjunto de classes plausíveis (conformal prediction)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "classification": "Pathogenic",
                "confidence": 0.94,
                "probabilities": {
                    "Benign": 0.01,
                    "Likely_Benign": 0.02,
                    "VUS": 0.03,
                    "Likely_Pathogenic": 0.10,
                    "Pathogenic": 0.84
                }
            }
        }


class BatchPredictionResult(BaseModel):
    """Resultado de predição em lote."""

    predictions: List[PredictionResult]
    total_variants: int
    processing_time_ms: float


class HealthResponse(BaseModel):
    """Response de health check."""

    status: str
    model_loaded: bool
    preprocessor_loaded: bool
    version: str


class ErrorResponse(BaseModel):
    """Response de erro."""

    error: str
    detail: str
    status_code: int
