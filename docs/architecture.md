# Arquitetura do VariantClassifier

## Visão Geral

O VariantClassifier segue uma arquitetura em camadas típica de sistemas de Machine Learning em produção.

```
┌────────────────────────────────────────────────────────────┐
│                     Camada de Apresentação                │
│  ┌──────────────────┐         ┌──────────────────────┐    │
│  │  API FastAPI     │         │  Streamlit UI        │    │
│  │  (REST/JSON)      │         │  (Visual Interface)   │    │
│  └──────────────────┘         └──────────────────────┘    │
└────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────────┐
│                    Camada de Serviços                    │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Request Router / Validation (Pydantic)           │  │
│  │  Business Logic (Prediction, Batch, Info)         │  │
│  │  Response Formatting                                │  │
│  └────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────────┐
│                    Camada de Modelagem                    │
│  ┌──────────────────┐    ┌──────────────────────┐         │
│  │ Preprocessor     │───▶│  Ensemble Model      │         │
│  │  (Feature Eng.)   │    │  (XGBoost + LGBM)     │         │
│  │                  │    │                      │         │
│  │  - Encoding      │    │  - Calibration       │         │
│  │  - Imputation    │    │  - Meta-learner      │         │
│  │  - Type Casting   │    │                      │         │
│  └──────────────────┘    └──────────────────────┘         │
│                           │                              │
│                           ▼                              │
│                    ┌─────────────────┐                   │
│                    │  Explainer    │                   │
│                    │  (SHAP values) │                   │
│                    └─────────────────┘                   │
└────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────────┐
│                    Camada de Dados                        │
│  ┌──────────────────┐    ┌──────────────────────┐         │
│  │  Data Storage    │    │  Model Storage       │         │
│  │  (CSV/VCF)        │    │  (Joblib)            │         │
│  └──────────────────┘    └──────────────────────┘         │
└────────────────────────────────────────────────────────────┘
```

## Componentes Principais

### 1. Camada de Ingestão (`src/ingestion/`)

**Responsabilidade:** Ler e validar dados de entrada

**Componentes:**
- `vcf_parser.py`: Parser de arquivos VCF
- `normalizer.py`: Normalização de variantes
- `validator.py`: Validação de qualidade

**Fluxo:**
```
VCF File → VCF Parser → Normalizer → Validator → DataFrame
```

### 2. Camada de Anotação (`src/annotation/`)

**Responsabilidade:** Enriquecer variantes com dados externos

**Componentes:**
- `vep_client.py`: Cliente Ensembl VEP
- `dbnsfp_annotator.py`: Anotação com dbNSFP
- `clinvar_lookup.py`: Busca no ClinVar
- `feature_builder.py`: Construção de features ACMG

**Fluxo:**
```
DataFrame → VEP → dbNSFP → ClinVar → Feature Builder → Features (28)
```

### 3. Camada de Modelagem (`src/modeling/`)

**Responsabilidade:** Treinar e executar predições

**Componentes:**
- `preprocessing.py`: Pré-processamento de dados
- `ensemble.py`: Modelo ensemble
- `calibration.py`: Calibração de probabilidades
- `uncertainty.py`: Quantificação de incerteza

**Arquitetura do Ensemble:**
```
Features (28) → XGBoost ──┐
               LightGBM ──┼── Meta-learner (Logistic)
               CatBoost ──┘      ↓
                            Probabilidades (5 classes)
```

### 4. Camada de Avaliação (`src/evaluation/`)

**Responsabilidade:** Avaliar performance do modelo

**Componentes:**
- `metrics.py`: Métricas de classificação, calibração e clínicas
- `validation.py**: Validação cruzada estratificada
- `clinical_audit.py`: Auditoria de erros clínicos

### 5. Camada de API (`src/api/`)

**Responsabilidade:** Interface REST para predições

**Componentes:**
- `main.py`: Aplicação FastAPI
- `schemas.py`: Modelos Pydantic
- `routes.py`: Endpoints (integrado no main.py)
- `middleware.py`: Middleware de logging/CORS

**Endpoints:**
- `GET /health` - Health check
- `POST /predict` - Predição individual
- `POST /predict/batch` - Predição em lote
- `GET /model/info` - Informações do modelo

## Fluxo de Dados End-to-End

### Pipeline de Treinamento

```
1. Dados Sintéticos (10K variantes)
   ↓
2. Split Estratificado (70/15/15)
   ↓
3. Pré-processamento
   - Encoding de categóricas
   - Imputação de missing
   - Type casting
   ↓
4. Treinamento Ensemble
   - XGBoost (500 trees)
   - LightGBM (500 trees)
   - Meta-learner (Logistic)
   ↓
5. Calibração (Isotonic, 5-fold CV)
   ↓
6. Avaliação
   - Métricas de classificação
   - Calibração
   - Métricas clínicas
   ↓
7. Salvar Modelo (models/)
```

### Pipeline de Inferência

```
1. API Request
   ↓
2. Validação Pydantic
   ↓
3. Pré-processamento
   - Input → DataFrame
   - Transform → Processed DataFrame
   ↓
4. Predição Ensemble
   - Model.predict_proba()
   - Classificação + Probabilidades
   ↓
5. Pós-processamento
   - Formatação resposta
   - Adição de metadados
   ↓
6. Response JSON
```

## Decisões de Design

### 1. Framework de Modelagem
**Escolha:** Ensemble de XGBoost + LightGBM + Meta-learner

**Justificativa:**
- Melhor performance que modelos isolados
- Diversidade de algoritmos reduz overfitting
- Meta-learner simples calibra automaticamente

### 2. Calibração de Probabilidades
**Escolha:** Isotonic Regression (5-fold CV)

**Justificativa:**
- Não assume forma paramétrica
- Superior para dados não lineares
- Cross-validation evita overfitting

### 3. Feature Engineering
**Escolha:** 28 features baseadas em ACMG

**Categorias:**
- Frequência populacional (3 features)
- Scores computacionais (5 features)
- Evidências funcionais (4 features)
- Evidências clínicas (3 features)
- Contexto do gene (6 features)
- Contexto proteico (4 features)
- Metadados (3 features)

### 4. API Framework
**Escolha:** FastAPI

**Justificativa:**
- Validação automática com Pydantic
- Performance assíncrona
- Documentação OpenAPI automática
- Suporte nativo a Python 3.11+

### 5. Frontend
**Escolha:** Streamlit

**Justificativa:**
- Desenvolvimento rápido em Python
- Integração fácil com pandas/plotly
- Sem necessidade de frontend skills
- Deployment simples

## Limitações e Mitigações

### Limitação 1: Dados Sintéticos
**Problema:** Dados gerados artificialmente podem não refletir realidade

**Mitigação:**
- Estrutura baseada em distribuições reais (ClinVar/gnomAD)
- Correlações features-target realistas
- Documentar que é proof-of-concept

### Limitação 2: Não tem SHAP implementado
**Problema:** Interpretabilidade limitada

**Mitigação:**
- Feature importance global disponível
- Probabilidades calibradas por classe
- Documentação de features ACMG

### Limitação 3: Sem validação externa real
**Problema:** Overfitting para distribuição específica

**Mitigação:**
- Cross-validation estratificada
- Métricas de calibração
- Monitoramento de drift recomendado

## Escalabilidade

### Vertical (Mais Features/Dados)
- Adicionar mais features: Simple (adicionar ao preprocess)
- Aumentar dados: Escala bem linearmente
- Otimizações: Feature selection, PCA

### Horizontal (Mais Requests)
- API: Deploy múltiplas instâncias
- Load balancer: Nginx/HAProxy
- Cache: Redis para requests repetidos

## Segurança

### Implementado
- Validação de entrada (Pydantic)
- CORS configurado
- Rate limiting (recomendado para prod)

### Recomendado para Produção
- Autenticação JWT
- HTTPS/TLS
- API keys
- Rate limiting por usuário
- Audit logging

## Monitoramento

### Métricas a Coletar
- QPS (Queries Per Second)
- Latência P50/P95/P99
- Taxa de erro
- Uso de recursos (CPU, memória)
- Drift de performance

### Ferramentas Sugeridas
- Prometheus + Grafana
- Sentry para erros
- MLflow para tracking
- Datadog/New Relic para APM

## Manutenção

### Operações Regulares
1. **Mensal:** Atualizar dados de referência (ClinVar, gnomAD)
2. **Trimestral:** Re-treinar modelo com novos dados
3. **Semestral:** Auditoria de performance e calibração
4. **Anual:** Revisão completa de arquitetura

### Troubleshooting Comum

**Problema: Latência alta**
- Verificar tamanho do batch
- Otimizar número de trees nos modelos
- Usar batch prediction

**Problema: Predições erradas**
- Verificar pré-processamento
- Validar features de entrada
- Comparar com distribuição de treino

**Problema: Memória cheia**
- Reduzir tamanho do modelo
- Limpar cache
- Aumentar swap
