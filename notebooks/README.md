# Jupyter Notebooks - VariantClassifier

Este diretório contém notebooks Jupyter para análise e desenvolvimento do VariantClassifier.

## Notebooks Disponíveis

### 1. 01_eda.ipynb - Análise Exploratória de Dados

**Objetivo:** Análise exploratória completa do dataset de variantes genômicas.

**Conteúdo:**
- Distribuição das classes ACMG
- Análise de features numéricas
- Correlações entre features
- Análise de features categóricas
- Valores ausentes
- Análise por gene
- Resumo estatístico

**Pré-requisitos:**
- Dados gerados em `data/splits/`
- Bibliotecas: pandas, numpy, matplotlib, seaborn

**Como usar:**
```bash
jupyter notebooks/01_eda.ipynb
```

---

### 2. 02_feature_engineering.ipynb - Feature Engineering

**Objetivo:** Demonstrar o processo de feature engineering para variantes genômicas.

**Conteúdo:**
- Carregamento de dados
- Inicialização do preprocessor
- Fit e transform de dados
- Análise de features transformadas
- Encoding de target
- Feature importance basal
- Análise de correlação pós-processamento
- Distribuição de features por classe

**Pré-requisitos:**
- Dados gerados em `data/splits/`
- Preprocessor salvo em `models/preprocessor.joblib`
- Bibliotecas: pandas, numpy, scikit-learn, matplotlib

**Como usar:**
```bash
jupyter notebooks/02_feature_engineering.ipynb
```

---

### 3. 03_model_selection.ipynb - Seleção de Modelos

**Objetivo:** Comparar diferentes algoritmos de ML para classificação de variantes.

**Conteúdo:**
- Modelos candidatos (Logistic Regression, Random Forest, Gradient Boosting, Naive Bayes)
- Cross-validation estratificada
- Avaliação em conjunto de validação
- Matriz de confusão
- Ensemble de modelos
- XGBoost e LightGBM
- Comparação final

**Pré-requisitos:**
- Dados gerados em `data/splits/`
- Preprocessor salvo em `models/preprocessor.joblib`
- Bibliotecas: pandas, numpy, scikit-learn, xgboost, lightgbm, matplotlib, seaborn

**Como usar:**
```bash
jupyter notebooks/03_model_selection.ipynb
```

---

### 4. 04_inference_examples.ipynb - Exemplos de Inferência

**Objetivo:** Demonstrar como usar o modelo treinado para inferência.

**Conteúdo:**
- Carregar modelo treinado
- Inferência em uma variante
- Inferência em lote
- Inferência via API REST
- Batch prediction via API
- Análise de incerteza
- Recomendações de uso

**Pré-requisitos:**
- Modelo treinado em `models/variant_ensemble.joblib`
- Preprocessor salvo em `models/preprocessor.joblib`
- API rodando em `http://localhost:8000` (para exemplos de API)
- Bibliotecas: pandas, numpy, requests, scikit-learn

**Como usar:**
```bash
# Terminal 1: Iniciar API
bash start_api.sh

# Terminal 2: Abrir notebook
jupyter notebooks/04_inference_examples.ipynb
```

---

## Configuração do Ambiente

### Instalar Jupyter

```bash
pip install jupyter notebook
```

### Instalar dependências

```bash
pip install pandas numpy matplotlib seaborn scikit-learn requests ipykernel
```

### Iniciar Jupyter

```bash
# No diretório raiz do projeto
jupyter notebook
```

Ou abra um notebook específico:

```bash
jupyter notebook notebooks/01_eda.ipynb
```

---

## Uso Recomendado

### Fluxo de Trabalho Sugerido

1. **01_eda.ipynb** - Execute primeiro para entender os dados
2. **02_feature_engineering.ipynb** - Veja como features são processadas
3. **03_model_selection.ipynb** - Compare diferentes modelos
4. **04_inference_examples.ipynb** - Aprenda a usar o modelo em produção

### Ordem de Execução

Os notebooks devem ser executados nesta ordem:

1. Primeiro, gere os dados sintéticos:
```bash
python scripts/generate_synthetic_data.py
```

2. Treine o modelo:
```bash
python scripts/train_model.py
```

3. Execute os notebooks em ordem (01 a 04)

---

## Dicas

### Kernel do Jupyter

Certifique-se de usar o ambiente virtual correto:

```bash
# Adicionar kernel ao Jupyter
python -m ipykernel install --user --name=variantclassifier --display-name "VariantClassifier"
```

Depois selecione o kernel "VariantClassifier" no Jupyter.

### Performance

Para datasets grandes, alguns notebooks podem levar tempo para executar. Considere:
- Usar uma amostra dos dados para desenvolvimento
- Aumentar a RAM do Jupyter se necessário
- Fechar notebooks não utilizados

### Salvar Resultados

Os notebooks não salvam dados automaticamente. Para persistir resultados:
```python
# Salvar DataFrame processado
df.to_csv('../data/processed/result.csv', index=False)
```

---

## Troubleshooting

### Erro: ModuleNotFoundError

Certifique-se de estar no diretório raiz do projeto e que o `src/` está no PYTHONPATH:

```python
import sys
sys.path.append('../src')
```

### Erro: FileNotFoundError

Verifique se os dados existem:

```bash
ls data/splits/
ls models/
```

### Erro: Model not found

Treine o modelo primeiro:

```bash
python scripts/train_model.py
```

### Memória Insuficiente

Se o Jupyter ficar sem memória:
- Use uma amostra menor dos dados
- Feche outros notebooks
- Aumente a memória do Jupyter

---

## Referências

- [Jupyter Documentation](https://jupyter-notebook.readthedocs.io/)
- [Project README](../README.md)
- [Architecture Documentation](../docs/architecture.md)
