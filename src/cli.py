"""
CLI para VariantClassifier.

Author: VariantClassifier Team
Date: January 2026
"""

import typer
from pathlib import Path

app = typer.Typer(
    name="variant-classifier",
    help="VariantClassifier - Sistema de classificação de variantes genômicas",
    add_completion=False
)


@app.command()
def version():
    """Mostra versão do VariantClassifier."""
    typer.echo("VariantClassifier v1.0.0")


@app.command()
def predict(
    input_file: Path = typer.Option(
        ...,
        "--input", "-i",
        help="Arquivo CSV com variantes para classificar",
        exists=True
    ),
    output_file: Path = typer.Option(
        ...,
        "--output", "-o",
        help="Arquivo CSV para salvar resultados"
    ),
    model_path: Path = typer.Option(
        "models/variant_ensemble.joblib",
        "--model", "-m",
        help="Caminho para o modelo treinado"
    )
):
    """
    Realiza predição em lote de variantes.

    Exemplo:
        variant-classifier predict --input data.csv --output results.csv
    """
    import pandas as pd
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))

    from src.modeling.ensemble import VariantClassifierEnsemble
    from src.modeling.preprocessing import VariantPreprocessor

    typer.echo(f"Carregando modelo de {model_path}...")
    model = VariantClassifierEnsemble.load(model_path)

    typer.echo("Carregando preprocessor...")
    preprocessor = VariantPreprocessor.load("models/preprocessor.joblib")

    typer.echo(f"Lendo dados de {input_file}...")
    df = pd.read_csv(input_file)

    typer.echo(f"Processando {len(df)} variantes...")
    df_processed = preprocessor.transform(df)

    typer.echo("Realizando predições...")
    predictions = model.predict(df_processed)
    probabilities = model.predict_proba(df_processed)

    typer.echo("Compilando resultados...")
    df['prediction'] = predictions
    df['confidence'] = probabilities.max(axis=1)

    for i, cls in enumerate(model.classes):
        df[f'prob_{cls}'] = probabilities[:, i]

    typer.echo(f"Salvando resultados em {output_file}...")
    df.to_csv(output_file, index=False)

    typer.echo(f"\nPredição concluída! {len(df)} variantes classificadas.")


@app.command()
def train(
    train_data: Path = typer.Option(
        ...,
        "--train", "-t",
        help="Arquivo CSV de treino",
        exists=True
    ),
    val_data: Path = typer.Option(
        ...,
        "--val", "-v",
        help="Arquivo CSV de validação",
        exists=True
    ),
    output_dir: Path = typer.Option(
        "models",
        "--output", "-o",
        help="Diretório para salvar modelos"
    )
):
    """
    Treina ensemble de modelos.

    Exemplo:
        variant-classifier train --train train.csv --val val.csv --output models/
    """
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))

    typer.echo("Esta funcionalidade está disponível via:")
    typer.echo("  python scripts/train_model.py")


@app.command()
def evaluate(
    model_path: Path = typer.Option(
        "models/variant_ensemble.joblib",
        "--model", "-m",
        help="Caminho para o modelo treinado",
        exists=True
    ),
    test_data: Path = typer.Option(
        ...,
        "--test", "-t",
        help="Arquivo CSV de teste",
        exists=True
    ),
    output_file: Path = typer.Option(
        ...,
        "--output", "-o",
        help="Arquivo JSON para salvar métricas"
    )
):
    """
    Avalia modelo em conjunto de teste.

    Exemplo:
        variant-classifier evaluate --test test.csv --output metrics.json
    """
    import pandas as pd
    import json
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))

    from src.modeling.ensemble import VariantClassifierEnsemble
    from src.modeling.preprocessing import VariantPreprocessor
    from src.evaluation.metrics import compute_classification_metrics

    typer.echo(f"Carregando modelo de {model_path}...")
    model = VariantClassifierEnsemble.load(model_path)

    typer.echo("Carregando preprocessor...")
    preprocessor = VariantPreprocessor.load("models/preprocessor.joblib")

    typer.echo(f"Lendo dados de {test_data}...")
    df = pd.read_csv(test_data)

    y_true = df['pathogenicity']
    X_test = df.drop('pathogenicity', axis=1)

    typer.echo("Processando dados...")
    X_test_proc = preprocessor.transform(X_test)
    y_true_enc = preprocessor.encode_target(y_true)

    typer.echo("Realizando predições...")
    y_pred = model.predict(X_test_proc)
    y_proba = model.predict_proba(X_test_proc)

    typer.echo("Computando métricas...")
    metrics = compute_classification_metrics(
        y_true_enc, y_pred, y_proba,
        class_names=model.classes
    )

    typer.echo(f"Salvando métricas em {output_file}...")
    with open(output_file, 'w') as f:
        json.dump(metrics, f, indent=2)

    typer.echo("\nMétricas principais:")
    typer.echo(f"  Accuracy: {metrics['accuracy']:.4f}")
    typer.echo(f"  ROC-AUC (macro): {metrics['roc_auc_macro']:.4f}")
    typer.echo(f"  F1-score (macro): {metrics['f1_macro']:.4f}")


if __name__ == "__main__":
    app()
