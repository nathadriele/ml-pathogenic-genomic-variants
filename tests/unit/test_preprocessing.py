"""
Testes unitários para preprocessamento de variantes.

Author: VariantClassifier Team
Date: January 2026
"""

import pytest
import pandas as pd
import numpy as np

from src.modeling.preprocessing import VariantPreprocessor


@pytest.fixture
def sample_data():
    """Dados de exemplo para testes."""
    return pd.DataFrame({
        "chromosome": ["chr1", "chr2", "chr3"],
        "position": [1000, 2000, 3000],
        "variant_type": ["SNV", "insertion", "deletion"],
        "ref": ["A", "C", "G"],
        "alt": ["G", "AT", "A"],
        "consequence": ["missense_variant", "frameshift_variant", "synonymous_variant"],
        "exon_number": [5, 10, 15],
        "transcript_biotype": ["protein_coding"] * 3,
        "gnomad_af": [0.0, 0.001, 0.1],
        "gnomad_af_popmax": [0.0, 0.002, 0.15],
        "is_absent_gnomad": [True, False, False],
        "revel_score": [0.8, 0.5, 0.1],
        "cadd_phred": [25.0, 15.0, 5.0],
        "spliceai_max": [0.1, 0.5, 0.0],
        "phylop_100way": [2.5, 1.5, 0.5],
        "gerp_rs": [3.0, 2.0, 1.0],
        "consequence_severity": [8, 9, 3],
        "is_lof": [False, True, False],
        "is_missense": [True, False, False],
        "is_splice_region": [False, True, False],
        "clinvar_stars": [3, 2, 1],
        "clinvar_submissions": [10, 5, 2],
        "has_functional_study": [True, False, False],
        "gene_symbol": ["BRCA1", "TP53", "MLH1"],
        "gene_pli": [0.9, 0.8, 0.7],
        "gene_loeuf": [0.2, 0.3, 0.4],
        "gene_missense_z": [3.5, 2.5, 1.5],
        "is_disease_gene": [True, True, True],
        "inheritance_mode": ["AD", "AD", "AR"],
        "domain_annotation": ["RING", "DNA_binding", "None"],
        "is_active_site": [False, True, False],
        "aa_change_grantham": [120.0, 80.0, 40.0],
        "protein_position_normalized": [0.7, 0.5, 0.3],
        "classification": ["Pathogenic", "Likely_Pathogenic", "Benign"]
    })


def test_preprocessor_initialization():
    """Testa inicialização do preprocessor."""
    preprocessor = VariantPreprocessor()
    assert preprocessor.scale_numerical == False
    assert preprocessor.fitted_ == False


def test_preprocessor_fit(sample_data):
    """Testa fit do preprocessor."""
    preprocessor = VariantPreprocessor()

    X = sample_data.drop(columns=["classification"])
    y = sample_data["classification"]

    preprocessor.fit(X, y)

    assert preprocessor.fitted_ == True
    assert len(preprocessor.get_class_names()) == 5


def test_preprocessor_transform(sample_data):
    """Testa transform do preprocessor."""
    preprocessor = VariantPreprocessor()

    X = sample_data.drop(columns=["classification"])
    y = sample_data["classification"]

    preprocessor.fit(X, y)
    X_transformed = preprocessor.transform(X)

    # Verifica que shape é mantido
    assert X_transformed.shape[0] == X.shape[0]

    # Verifica que colunas desnecessárias foram removidas
    assert "chromosome" not in X_transformed.columns
    assert "ref" not in X_transformed.columns
    assert "alt" not in X_transformed.columns


def test_preprocessor_encode_target(sample_data):
    """Testa encoding do target."""
    preprocessor = VariantPreprocessor()

    y = sample_data["classification"]
    preprocessor.fit(sample_data.drop(columns=["classification"]), y)

    y_encoded = preprocessor.encode_target(y)

    assert len(y_encoded) == len(y)
    assert all(isinstance(yi, (int, np.integer)) for yi in y_encoded)


def test_preprocessor_impute_missing():
    """Testa imputação de valores ausentes."""
    preprocessor = VariantPreprocessor()

    df = pd.DataFrame({
        "position": [1000, None, 3000],
        "gnomad_af": [0.0, None, 0.1],
        "consequence": ["missense", None, "synonymous"],
        "is_lof": [True, None, False]
    })

    df_imputed = preprocessor._impute_missing(df)

    assert df_imputed["position"].isnull().sum() == 0
    assert df_imputed["gnomad_af"].isnull().sum() == 0
    assert df_imputed["consequence"].isnull().sum() == 0
    assert df_imputed["is_lof"].isnull().sum() == 0


def test_preprocessor_ensure_dtypes():
    """Testa correção de tipos de dados."""
    preprocessor = VariantPreprocessor()

    df = pd.DataFrame({
        "position": ["1000", "2000", "3000"],  # strings
        "exon_number": [5, None, 15],  # tem None
        "gnomad_af": [0.0, 0.001, 0.1],
        "consequence": ["missense", "frameshift", "synonymous"],
        "is_lof": [True, False, False]
    })

    df_fixed = preprocessor._ensure_dtypes(df)

    assert df_fixed["position"].dtype in [int, np.integer]
    assert df_fixed["exon_number"].dtype in [int, np.integer]
    assert df_fixed["gnomad_af"].dtype in [float, np.floating]
