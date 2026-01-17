#  VariantClassifier

Sistema de classificação de variantes genômicas baseado em Machine Learning, seguindo as diretrizes ACMG/AMP (American College of Medical Genetics).

##  Visão Geral

O VariantClassifier é um sistema end-to-end para classificação automática de variantes genômicas em 5 categorias clínicas:
- **Benign** (Benigna)
- **Likely Benign** (Provavelmente Benigna)
- **VUS** (Variant of Uncertain Significance)
- **Likely Pathogenic** (Provavelmente Patogênica)
- **Pathogenic** (Patogênica)

##  Funcionalidades

- **Ensemble de Modelos**: XGBoost + LightGBM + CatBoost com meta-learner
- **Calibração de Probabilidades**: Calibração isotônica para confiabilidade clínica
- **Interpretabilidade**: SHAP values para cada predição
- **Quantificação de Incerteza**: Conformal prediction sets
- **API REST**: FastAPI com documentação OpenAPI
- **Interface Web**: Dashboard Streamlit interativo
- **MLOps**: MLflow tracking, monitoramento, e CI/CD

##  Quick Start

### Pré-requisitos

- Python 3.11+
- Docker & Docker Compose
- Git

### Instalação

```bash
# Clone o repositório
git clone https://github.com/variantclassifier/variant-classifier.git
cd variant-classifier

# Crie ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Instale dependências
pip install -e ".[dev]"

# Copie arquivo de ambiente
cp .env.example .env
```

### Gerar Dados Sintéticos

```bash
python scripts/generate_synthetic_data.py \
    --n-samples 10000 \
    --output-dir data/processed
```

### Treinar Modelo

```bash
python scripts/train_model.py \
    --config configs/config.yaml \
    --data-dir data/processed \
    --output-dir models
```

### Executar API

```bash
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

Acesse: http://localhost:8000/docs

### Executar Frontend

```bash
streamlit run frontend/app.py
```

Acesse: http://localhost:8501

### Docker Compose (Deploy Completo)

```bash
docker-compose up -d
```

Serviços disponíveis:
- API: http://localhost:8000
- Frontend: http://localhost:8501
- MLflow: http://localhost:5000
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000

##  Estrutura do Projeto

```
variant-classifier/
├── configs/              # Arquivos de configuração
├── data/                 # Dados brutos, processados e splits
├── docs/                 # Documentação
├── docker/               # Dockerfiles e docker-compose
├── frontend/             # Interface Streamlit
├── models/               # Modelos treinados
├── notebooks/            # Jupyter notebooks para análise
├── scripts/              # Scripts utilitários
├── src/                  # Código fonte
│   ├── ingestion/        # Ingestão de dados
│   ├── annotation/       # Anotação de variantes
│   ├── modeling/         # Modelos ML
│   ├── evaluation/       # Métricas e avaliação
│   └── api/              # API FastAPI
└── tests/                # Testes unitários e integração
```

##  Métricas de Performance

| Métrica | Target | Status |
|---------|--------|--------|
| AUROC (macro) | ≥ 0.92 | ⏳ |
| AUPRC (Patogênica) | ≥ 0.85 | ⏳ |
| Calibration Error | ≤ 0.05 | ⏳ |
| Concordância ACMG | ≥ 0.88 | ⏳ |
| Cobertura Conformal | 0.90 | ⏳ |

##  Desenvolvimento

### Executar Testes

```bash
# Testes unitários
pytest tests/unit/

# Testes de integração
pytest tests/integration/

# Testes clínicos
pytest tests/clinical/

# Todos com cobertura
pytest --cov=src --cov-report=html
```

### Formatação e Linting

```bash
# Format code with black
black src/ tests/

# Lint with ruff
ruff check src/ tests/

# Type checking with mypy
mypy src/
```

##  Documentação

- [Arquitetura](docs/architecture.md)
- [API Reference](docs/api_reference.md)
- [Guia de Deploy](docs/deployment_guide.md)
- [Protocolo de Validação Clínica](docs/clinical_validation.md)

##  Contribuindo

Contribuições são bem-vindas!

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

##  Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## ️ Observação

**AVISO IMPORTANTE**: Este sistema é destinado apenas para fins de pesquisa e educacionais. Não deve ser usado como única fonte para decisões clínicas. Todas as predições devem ser revisadas por geneticistas clínicos qualificados.

##  Contato

- **Issues**: https://github.com/variantclassifier/variant-classifier/issues
- **Discussions**: https://github.com/variantclassifier/variant-classifier/discussions

---

**Desenvolvido com ️ para a comunidade de genômica**
