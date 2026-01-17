# API Reference - VariantClassifier

Documentação completa da API REST do VariantClassifier.

## Base URL

```
http://localhost:8000
```

## Autenticação

A API atual não requer autenticação. Para produção, implemente:
- JWT tokens
- API keys
- Rate limiting

## Endpoints

### 1. Health Check

Verifica status da API e se o modelo está carregado.

**Endpoint:** `GET /health`

**Resposta:**

```json
{
  "status": "healthy",
  "model_loaded": true,
  "preprocessor_loaded": true,
  "version": "1.0.0"
}
```

**Status Codes:**
- 200: API funcionando
- 503: API ou modelo não disponível

---

### 2. Predição Individual

Classifica uma única variante genômica.

**Endpoint:** `POST /predict`

**Request Body:**

```json
{
  "variant": {
    "chromosome": "chr17",
    "position": 43044295,
    "variant_type": "SNV",
    "ref": "G",
    "alt": "A",
    "consequence": "missense_variant",
    "exon_number": 10,
    "transcript_biotype": "protein_coding",
    "gnomad_af": 0.0,
    "gnomad_af_popmax": 0.0,
    "is_absent_gnomad": true,
    "revel_score": 0.94,
    "cadd_phred": 35.0,
    "spliceai_max": 0.1,
    "phylop_100way": 5.2,
    "gerp_rs": 5.0,
    "consequence_severity": 5,
    "is_lof": false,
    "is_missense": true,
    "is_splice_region": false,
    "clinvar_stars": 2,
    "clinvar_submissions": 15,
    "has_functional_study": true,
    "gene_symbol": "BRCA1",
    "gene_pli": 0.99,
    "gene_loeuf": 0.05,
    "gene_missense_z": 3.5,
    "is_disease_gene": true,
    "inheritance_mode": "AD",
    "domain_annotation": "BRCT",
    "is_active_site": false,
    "aa_change_grantham": 150.0,
    "protein_position_normalized": 0.75
  }
}
```

**Resposta:**

```json
{
  "classification": "Pathogenic",
  "confidence": 0.9423,
  "probabilities": {
    "Benign": 0.0034,
    "Likely_Benign": 0.0089,
    "VUS": 0.0145,
    "Likely_Pathogenic": 0.0309,
    "Pathogenic": 0.9423
  }
}
```

**Status Codes:**
- 200: Predição realizada com sucesso
- 400: Dados de entrada inválidos
- 422: Validação Pydantic falhou
- 500: Erro interno no servidor

**Field Descriptions:**

**Metadados Básicos:**
- `chromosome`: Cromossomo (formato "chrX")
- `position`: Posição genômica (inteiro >= 0)
- `variant_type`: Tipo da variante ("SNV", "insertion", "deletion")
- `ref`: Base de referência
- `alt`: Base alternativa
- `consequence`: Consequência funcional (ex: "missense_variant")
- `exon_number`: Número do exão (opcional)
- `transcript_biotype`: Biotype do transcript (default: "protein_coding")

**Frequência Populacional:**
- `gnomad_af`: Frequência alélica gnomAD (0.0 a 1.0)
- `gnomad_af_popmax`: Frequência máxima por população (0.0 a 1.0)
- `is_absent_gnomad`: Ausente em controles gnomAD (boolean)

**Scores Computacionais:**
- `revel_score`: REVEL score (0.0 a 1.0)
- `cadd_phred`: CADD Phred score (0.0 a 99.0)
- `spliceai_max`: SpliceAI score máximo (0.0 a 1.0)
- `phylop_100way`: Conservação PhyloP
- `gerp_rs`: GERP++ RS score

**Features Funcionais:**
- `consequence_severity`: Severidade da consequência (0 a 10)
- `is_lof`: Loss of function (boolean)
- `is_missense`: Missense variant (boolean)
- `is_splice_region`: Região de splice (boolean)

**Evidências Clínicas:**
- `clinvar_stars`: Nível de revisão ClinVar (0 a 4)
- `clinvar_submissions`: Número de submissões ClinVar
- `has_functional_study`: Estudo funcional disponível (boolean)

**Contexto do Gene:**
- `gene_symbol`: Símbolo do gene (obrigatório)
- `gene_pli`: pLI score do gene (0.0 a 1.0)
- `gene_loeuf`: LOEUF score (>= 0.0)
- `gene_missense_z`: Missense Z-score
- `is_disease_gene`: Gene associado a doença (boolean)
- `inheritance_mode`: Modo de herança ("AD", "AR", "XLR")

**Contexto Proteico:**
- `domain_annotation`: Anotação de domínio
- `is_active_site`: Sítio ativo (boolean)
- `aa_change_grantham`: Distância de Grantham (>= 0.0)
- `protein_position_normalized`: Posição normalizada na proteína (0.0 a 1.0)

---

### 3. Predição em Lote

Classifica múltiplas variantes em uma única requisição.

**Endpoint:** `POST /predict/batch`

**Request Body:**

```json
{
  "variants": [
    { /* variante 1 */ },
    { /* variante 2 */ },
    ...
  ]
}
```

**Resposta:**

```json
{
  "predictions": [
    { /* resultado 1 */ },
    { /* resultado 2 */ },
    ...
  ],
  "total_variants": 2,
  "processing_time_ms": 123.45
}
```

**Limites:**
- Mínimo: 1 variante
- Máximo: 100 variantes por requisição

**Status Codes:**
- 200: Predições realizadas com sucesso
- 400: Requisição inválida
- 422: Validação Pydantic falhou
- 500: Erro interno

---

### 4. Informações do Modelo

Retorna metadados sobre o modelo carregado.

**Endpoint:** `GET /model/info`

**Resposta:**

```json
{
  "model_type": "VariantClassifierEnsemble",
  "version": "1.0.0",
  "classes": [
    "Benign",
    "Likely_Benign",
    "VUS",
    "Likely_Pathogenic",
    "Pathogenic"
  ],
  "n_features": 34,
  "model_metadata": {
    "training_date": "2026-01-17",
    "training_samples": 7000,
    "calibration_method": "isotonic",
    "ensemble_models": ["xgboost", "lightgbm"],
    "metric_roc_auc": 0.769
  }
}
```

---

## Exemplos de Uso

### Python

```python
import requests
import json

API_URL = "http://localhost:8000"

# Exemplo 1: Predição individual
variant_data = {
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

response = requests.post(f"{API_URL}/predict", json={"variant": variant_data})
result = response.json()

print(f"Classificação: {result['classification']}")
print(f"Confiança: {result['confidence']:.2%}")

# Exemplo 2: Predição em lote
variants = [variant_data_1, variant_data_2, variant_data_3]

response = requests.post(
    f"{API_URL}/predict/batch",
    json={"variants": variants}
)

results = response.json()
for i, pred in enumerate(results['predictions']):
    print(f"Variante {i+1}: {pred['classification']} ({pred['confidence']:.2%})")
```

### cURL

```bash
# Health check
curl http://localhost:8000/health

# Predição individual
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "variant": {
      "chromosome": "chr17",
      "position": 43044295,
      "gene_symbol": "BRCA1",
      "gnomad_af": 0.0,
      "revel_score": 0.94,
      "cadd_phred": 35.0
    }
  }'

# Informações do modelo
curl http://localhost:8000/model/info
```

### JavaScript

```javascript
const API_URL = 'http://localhost:8000';

// Predição individual
async function predictVariant(variantData) {
  const response = await fetch(`${API_URL}/predict`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ variant: variantData })
  });

  const result = await response.json();
  console.log('Classificação:', result.classification);
  console.log('Confiança:', (result.confidence * 100).toFixed(2) + '%');
  return result;
}

// Uso
const variant = {
  chromosome: 'chr17',
  position: 43044295,
  gene_symbol: 'BRCA1',
  gnomad_af: 0.0,
  revel_score: 0.94,
  cadd_phred: 35.0
};

predictVariant(variant);
```

---

## Tratamento de Erros

### Formato de Resposta de Erro

```json
{
  "error": "ValidationError",
  "detail": "1 validation error for VariantFeatures\\nposition\\n  ensure this value is greater than or equal to 0",
  "status_code": 422
}
```

### Erros Comuns

**400 Bad Request**
- Requisição mal formatada
- JSON inválido

**422 Unprocessable Entity**
- Validação Pydantic falhou
- Campos obrigatórios faltando
- Tipos de dados incorretos

**500 Internal Server Error**
- Erro ao carregar modelo
- Erro durante predição
- Falha no pré-processamento

**503 Service Unavailable**
- Modelo não carregado
- API em manutenção

---

## Performance

**Latência esperada:**
- Single prediction: 50-200ms
- Batch prediction (10 variants): 200-500ms
- Batch prediction (100 variants): 1500-3000ms

**Throughput esperado:**
- ~100-500 predictions/segundo (dependendo do hardware)

---

## Rate Limiting

Atualmente sem rate limiting. Recomendado para produção:
- 100 requests/minuto por IP
- 1000 requests/minuto por API key

---

## Versionamento

A API usa versionamento por URL (ex: `/v1/predict`). A versão atual é v1.

Mudanças breaking serão incrementadas para v2, com período de suporte para v1.

---

## CORS

CORS habilitado para:
- `http://localhost:8501` (Streamlit)
- `http://localhost:3000` (React dev)

Para produção, configure origens permitidas no `main.py`.

---

## Suporte

Para dúvidas ou problemas:
- GitHub Issues: [repository_url]
- Documentation: [docs_url]
- Email: support@example.com
