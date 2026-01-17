#!/usr/bin/env python3
"""
Gerador de dados sintéticos para variantes genômicas.

Gera variantes realistas seguindo distribuições observadas em ClinVar e gnomAD,
com features baseadas em critérios ACMG/AMP.

Author: VariantClassifier Team
Date: January 2026
"""

import argparse
import json
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd
from numpy.typing import NDArray


# Constantes
ACMG_CLASSES: Final = ["Benign", "Likely_Benign", "VUS", "Likely_Pathogenic", "Pathogenic"]

# Genes associados a doenças mendelianas comuns
DISEASE_GENES: Final = [
    "BRCA1", "BRCA2", "TP53", "MLH1", "MSH2", "MSH6", "PMS2",
    "APC", "PALB2", "PTEN", "STK11", "CDH1", "RAD51C", "RAD51D",
    "ATM", "CHEK2", "NBN", "BRIP1", "FANCM", "RECQL4"
]

# Tipos de consequências funcionais
CONSEQUENCES: Final = [
    "synonymous_variant",
    "missense_variant",
    "frameshift_variant",
    "stop_gained",
    "splice_donor_variant",
    "splice_acceptor_variant",
    "start_lost",
    "inframe_insertion",
    "inframe_deletion"
]

# Modos de herança
INHERITANCE_MODES: Final = ["AD", "AR", "XL", "Mitochondrial"]

# Domínios proteicos comuns
PROTEIN_DOMAINS: Final = [
    "RING", "BRCT", "Kinase", "DNA_binding", "Zinc_finger",
    "Homeobox", "HLH", "Immunoglobulin", "Fibrinogen", "None"
]


class SyntheticVariantGenerator:
    """Gerador de variantes genômicas sintéticas realistas."""

    def __init__(
        self,
        n_samples: int = 10000,
        random_seed: int = 42,
        class_distribution: dict[str, float] | None = None
    ):
        """
        Inicializa o gerador.

        Args:
            n_samples: Número de variantes a gerar
            random_seed: Semente aleatória para reprodutibilidade
            class_distribution: Distribuição personalizada das classes ACMG
        """
        self.n_samples = n_samples
        self.random_seed = random_seed
        np.random.seed(random_seed)

        # Distribuição padrão baseada em ClinVar
        self.class_distribution = class_distribution or {
            "Benign": 0.30,
            "Likely_Benign": 0.15,
            "VUS": 0.25,
            "Likely_Pathogenic": 0.15,
            "Pathogenic": 0.15
        }

        self._validate_distribution()

    def _validate_distribution(self) -> None:
        """Valida se a distribuição soma 1.0."""
        total = sum(self.class_distribution.values())
        if not np.isclose(total, 1.0, atol=0.01):
            raise ValueError(f"Distribuição deve somar 1.0, obtido: {total}")

    def generate(self) -> pd.DataFrame:
        """
        Gera o dataset completo de variantes sintéticas.

        Returns:
            DataFrame com todas as features e labels
        """
        print(f"🧬 Gerando {self.n_samples} variantes sintéticas...")

        # Gera classes primeiro
        classes = self._generate_classes()

        # Gera grupos de features correlacionadas com a classe
        data = {"classification": classes}

        # 1. Metadados básicos da variante
        data.update(self._generate_variant_metadata())

        # 2. Features de frequência populacional
        data.update(self._generate_population_frequency(classes))

        # 3. Scores computacionais
        data.update(self._generate_computational_scores(classes))

        # 4. Features funcionais
        data.update(self._generate_functional_features(classes))

        # 5. Evidências clínicas
        data.update(self._generate_clinical_evidence(classes))

        # 6. Contexto do gene
        data.update(self._generate_gene_context())

        # 7. Contexto proteico
        data.update(self._generate_protein_context(classes))

        df = pd.DataFrame(data)
        print(f"✅ Dataset gerado: {df.shape[0]} variantes, {df.shape[1]} features")

        return df

    def _generate_classes(self) -> NDArray:
        """Gera classes ACMG conforme distribuição especificada."""
        classes_list = list(self.class_distribution.keys())
        probabilities = list(self.class_distribution.values())

        classes = np.random.choice(
            classes_list,
            size=self.n_samples,
            p=probabilities
        )

        return classes

    def _generate_variant_metadata(self) -> dict[str, NDArray]:
        """Gera metadados básicos das variantes."""
        # Cromossomos (autosssomos 1-22 + X)
        chromosomes = np.random.choice(
            [f"chr{i}" for i in range(1, 23)] + ["chrX"],
            size=self.n_samples
        )

        # Posições (simuladas)
        positions = np.random.randint(1, 250_000_000, size=self.n_samples)

        # Tipo de variante
        variant_types = np.random.choice(
            ["SNV", "insertion", "deletion"],
            size=self.n_samples,
            p=[0.85, 0.08, 0.07]
        )

        # Tipo de ref/alt (simplificado)
        refs = np.random.choice(list("ACGT"), size=self.n_samples)
        alts = np.random.choice(list("ACGT"), size=self.n_samples)
        alts = np.where(alts == refs, "A", alts)  # Garante ref != alt

        # Consequência
        consequences = np.random.choice(
            CONSEQUENCES,
            size=self.n_samples,
            p=[0.10, 0.45, 0.15, 0.12, 0.08, 0.05, 0.02, 0.02, 0.01]
        )

        # Número do exão
        exon_numbers = np.random.randint(1, 50, size=self.n_samples)

        # Biotype do transcript
        biotypes = np.random.choice(
            ["protein_coding", "nonsense_mediated_decay"],
            size=self.n_samples,
            p=[0.95, 0.05]
        )

        return {
            "chromosome": chromosomes,
            "position": positions,
            "variant_type": variant_types,
            "ref": refs,
            "alt": alts,
            "consequence": consequences,
            "exon_number": exon_numbers,
            "transcript_biotype": biotypes
        }

    def _generate_population_frequency(self, classes: NDArray) -> dict[str, NDArray]:
        """
        Gera frequências populacionais baseadas na classe.

        Patogênicas tendem a ser raras, benignas mais comuns.
        """
        n = self.n_samples
        gnomad_af = np.zeros(n)
        gnomad_af_popmax = np.zeros(n)
        is_absent_gnomad = np.zeros(n, dtype=bool)

        for i, cls in enumerate(classes):
            if cls in ["Pathogenic", "Likely_Pathogenic"]:
                # Muito raras
                if np.random.random() < 0.95:
                    gnomad_af[i] = 0.0
                    is_absent_gnomad[i] = True
                else:
                    gnomad_af[i] = np.random.exponential(0.0001)
            elif cls == "VUS":
                # Distribuição mista
                if np.random.random() < 0.7:
                    gnomad_af[i] = 0.0
                    is_absent_gnomad[i] = True
                else:
                    gnomad_af[i] = np.random.exponential(0.001)
            else:  # Benign / Likely_Benign
                # Mais comuns
                gnomad_af[i] = np.random.beta(2, 50)  # Tail heavy, valores baixos

        # Popmax é sempre >= af
        gnomad_af_popmax = gnomad_af * np.random.uniform(1.0, 5.0, size=n)
        gnomad_af_popmax = np.minimum(gnomad_af_popmax, 1.0)

        return {
            "gnomad_af": gnomad_af,
            "gnomad_af_popmax": gnomad_af_popmax,
            "is_absent_gnomad": is_absent_gnomad
        }

    def _generate_computational_scores(self, classes: NDArray) -> dict[str, NDArray]:
        """
        Gera scores de patogenicidade computacionais.

        Scores maiores indicam maior probabilidade de patogenicidade.
        """
        n = self.n_samples

        # REVEL: 0-1, patogênicas > 0.7
        revel_score = np.zeros(n)
        # CADD Phred: 0-99, patogênicas > 20-25
        cadd_phred = np.zeros(n)
        # SpliceAI: 0-1
        spliceai_max = np.random.exponential(0.05, size=n)
        spliceai_max = np.minimum(spliceai_max, 1.0)
        # Conservação
        phylop_100way = np.random.exponential(0.5, size=n)
        phylop_100way = np.minimum(phylop_100way, 6.0)
        gerp_rs = np.random.exponential(1.0, size=n)
        gerp_rs = np.maximum(gerp_rs, -5.0)
        gerp_rs = np.minimum(gerp_rs, 5.0)

        for i, cls in enumerate(classes):
            if cls == "Pathogenic":
                revel_score[i] = np.random.beta(8, 2)  # Alta
                cadd_phred[i] = np.random.normal(30, 5)
            elif cls == "Likely_Pathogenic":
                revel_score[i] = np.random.beta(6, 3)
                cadd_phred[i] = np.random.normal(25, 6)
            elif cls == "VUS":
                revel_score[i] = np.random.beta(2, 2)  # Distribuição uniforme
                cadd_phred[i] = np.random.normal(20, 8)
            elif cls == "Likely_Benign":
                revel_score[i] = np.random.beta(2, 5)
                cadd_phred[i] = np.random.normal(15, 7)
            else:  # Benign
                revel_score[i] = np.random.beta(1, 8)  # Baixa
                cadd_phred[i] = np.random.normal(10, 8)

        # Clip valores
        revel_score = np.clip(revel_score, 0, 1)
        cadd_phred = np.clip(cadd_phred, 0, 99)

        return {
            "revel_score": revel_score,
            "cadd_phred": cadd_phred,
            "spliceai_max": spliceai_max,
            "phylop_100way": phylop_100way,
            "gerp_rs": gerp_rs
        }

    def _generate_functional_features(self, classes: NDArray) -> dict[str, NDArray]:
        """Gera features do impacto funcional."""
        n = self.n_samples

        # Severidade da consequência (0-10)
        consequence_severity = np.zeros(n)
        is_lof = np.zeros(n, dtype=bool)
        is_missense = np.zeros(n, dtype=bool)
        is_splice_region = np.zeros(n, dtype=bool)

        for i, cls in enumerate(classes):
            if cls == "Pathogenic":
                consequence_severity[i] = np.random.choice([8, 9, 10], p=[0.3, 0.4, 0.3])
                is_lof[i] = np.random.random() < 0.6
                is_missense[i] = ~is_lof[i] and (np.random.random() < 0.8)
                is_splice_region[i] = np.random.random() < 0.4
            elif cls == "Likely_Pathogenic":
                consequence_severity[i] = np.random.randint(6, 10)
                is_lof[i] = np.random.random() < 0.4
                is_missense[i] = ~is_lof[i] and (np.random.random() < 0.7)
                is_splice_region[i] = np.random.random() < 0.3
            elif cls == "VUS":
                consequence_severity[i] = np.random.randint(3, 9)
                is_lof[i] = np.random.random() < 0.2
                is_missense[i] = ~is_lof[i] and (np.random.random() < 0.5)
                is_splice_region[i] = np.random.random() < 0.15
            elif cls == "Likely_Benign":
                consequence_severity[i] = np.random.randint(1, 6)
                is_lof[i] = np.random.random() < 0.05
                is_missense[i] = ~is_lof[i] and (np.random.random() < 0.4)
            else:  # Benign
                consequence_severity[i] = np.random.randint(0, 4)
                is_lof[i] = np.random.random() < 0.01
                is_missense[i] = ~is_lof[i] and (np.random.random() < 0.3)

        return {
            "consequence_severity": consequence_severity,
            "is_lof": is_lof,
            "is_missense": is_missense,
            "is_splice_region": is_splice_region
        }

    def _generate_clinical_evidence(self, classes: NDArray) -> dict[str, NDArray]:
        """Gera evidências clínicas (ClinVar)."""
        n = self.n_samples

        clinvar_stars = np.zeros(n, dtype=int)
        clinvar_submissions = np.zeros(n, dtype=int)
        has_functional_study = np.zeros(n, dtype=bool)

        for i, cls in enumerate(classes):
            if cls == "Pathogenic":
                clinvar_stars[i] = np.random.choice([2, 3, 4], p=[0.3, 0.5, 0.2])
                clinvar_submissions[i] = np.random.randint(5, 50)
                has_functional_study[i] = np.random.random() < 0.6
            elif cls == "Likely_Pathogenic":
                clinvar_stars[i] = np.random.choice([1, 2, 3], p=[0.4, 0.4, 0.2])
                clinvar_submissions[i] = np.random.randint(2, 20)
                has_functional_study[i] = np.random.random() < 0.3
            elif cls == "VUS":
                clinvar_stars[i] = np.random.choice([0, 1, 2], p=[0.5, 0.3, 0.2])
                clinvar_submissions[i] = np.random.randint(1, 10)
                has_functional_study[i] = np.random.random() < 0.1
            else:  # Benign / Likely_Benign
                clinvar_stars[i] = np.random.choice([1, 2, 3, 4], p=[0.2, 0.4, 0.3, 0.1])
                clinvar_submissions[i] = np.random.randint(10, 100)
                has_functional_study[i] = np.random.random() < 0.05

        return {
            "clinvar_stars": clinvar_stars,
            "clinvar_submissions": clinvar_submissions,
            "has_functional_study": has_functional_study
        }

    def _generate_gene_context(self) -> dict[str, NDArray]:
        """Gera contexto do gene."""
        n = self.n_samples

        # Gene aleatório
        gene_symbol = np.random.choice(DISEASE_GENES, size=n)

        # pLI (probabilidade de intolerância a LoF)
        gene_pli = np.random.beta(2, 2, size=n)

        # LOEUF (loess residual)
        gene_loeuf = np.random.normal(0.5, 0.3, size=n)
        gene_loeuf = np.clip(gene_loeuf, 0, 2)

        # Missense Z-score
        gene_missense_z = np.random.normal(0, 2, size=n)

        # É gene de doença
        is_disease_gene = np.ones(n, dtype=bool)

        # Modo de herança
        inheritance_mode = np.random.choice(INHERITANCE_MODES, size=n, p=[0.7, 0.2, 0.08, 0.02])

        return {
            "gene_symbol": gene_symbol,
            "gene_pli": gene_pli,
            "gene_loeuf": gene_loeuf,
            "gene_missense_z": gene_missense_z,
            "is_disease_gene": is_disease_gene,
            "inheritance_mode": inheritance_mode
        }

    def _generate_protein_context(self, classes: NDArray) -> dict[str, NDArray]:
        """Gera contexto proteico."""
        n = self.n_samples

        # Domínio
        domain_annotation = np.random.choice(PROTEIN_DOMAINS, size=n, p=[0.08, 0.08, 0.08, 0.08, 0.08, 0.05, 0.05, 0.05, 0.05, 0.40])

        # Sítio ativo (mais comum em patogênicas)
        is_active_site = np.zeros(n, dtype=bool)
        for i, cls in enumerate(classes):
            if cls in ["Pathogenic", "Likely_Pathogenic"]:
                is_active_site[i] = np.random.random() < 0.15
            else:
                is_active_site[i] = np.random.random() < 0.02

        # Distância de Grantham (para missense)
        aa_change_grantham = np.zeros(n)
        for i in range(n):
            if np.random.random() < 0.7:  # 70% são missense
                aa_change_grantham[i] = np.random.randint(10, 185)
            else:
                aa_change_grantham[i] = 0

        # Posição normalizada na proteína
        protein_position_normalized = np.random.beta(2, 2, size=n)

        return {
            "domain_annotation": domain_annotation,
            "is_active_site": is_active_site,
            "aa_change_grantham": aa_change_grantham,
            "protein_position_normalized": protein_position_normalized
        }


def main():
    """Função principal."""
    parser = argparse.ArgumentParser(
        description="Gerar dados sintéticos de variantes genômicas"
    )
    parser.add_argument(
        "--n-samples",
        type=int,
        default=10000,
        help="Número de variantes a gerar (padrão: 10000)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/processed",
        help="Diretório de saída (padrão: data/processed)"
    )
    parser.add_argument(
        "--train-val-test-split",
        action="store_true",
        help="Se definido, cria splits de treino/val/teste"
    )
    parser.add_argument(
        "--train-size",
        type=float,
        default=0.7,
        help="Proporção de treino (padrão: 0.7)"
    )
    parser.add_argument(
        "--val-size",
        type=float,
        default=0.15,
        help="Proporção de validação (padrão: 0.15)"
    )
    parser.add_argument(
        "--random-seed",
        type=int,
        default=42,
        help="Semente aleatória (padrão: 42)"
    )

    args = parser.parse_args()

    # Cria diretório de saída
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Gera dados
    generator = SyntheticVariantGenerator(
        n_samples=args.n_samples,
        random_seed=args.random_seed
    )

    df = generator.generate()

    # Salva dataset completo
    output_path = output_dir / "synthetic_variants.csv"
    df.to_csv(output_path, index=False)
    print(f"💾 Dataset salvo em: {output_path}")

    # Cria splits se solicitado
    if args.train_val_test_split:
        from sklearn.model_selection import train_test_split

        test_size = 1.0 - args.train_size - args.val_size

        # Stratified split
        train_df, temp_df = train_test_split(
            df,
            train_size=args.train_size,
            stratify=df["classification"],
            random_state=args.random_seed
        )

        val_df, test_df = train_test_split(
            temp_df,
            train_size=args.val_size / (args.val_size + test_size),
            stratify=temp_df["classification"],
            random_state=args.random_seed
        )

        # Salva splits
        splits_dir = Path("data/splits")
        splits_dir.mkdir(parents=True, exist_ok=True)

        train_df.to_csv(splits_dir / "train.csv", index=False)
        val_df.to_csv(splits_dir / "val.csv", index=False)
        test_df.to_csv(splits_dir / "test.csv", index=False)

        print(f"\n📊 Splits criados:")
        print(f"  Treino:     {len(train_df)} variantes ({len(train_df)/len(df):.1%})")
        print(f"  Validação:  {len(val_df)} variantes ({len(val_df)/len(df):.1%})")
        print(f"  Teste:      {len(test_df)} variantes ({len(test_df)/len(df):.1%})")

    # Salva metadados
    metadata = {
        "n_samples": args.n_samples,
        "n_features": df.shape[1] - 1,  # Exclui classificação
        "class_distribution": df["classification"].value_counts().to_dict(),
        "random_seed": args.random_seed,
        "feature_names": list(df.columns)
    }

    metadata_path = output_dir / "synthetic_metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"\n📋 Metadados salvos em: {metadata_path}")
    print(f"\n✅ Concluído!")


if __name__ == "__main__":
    main()
