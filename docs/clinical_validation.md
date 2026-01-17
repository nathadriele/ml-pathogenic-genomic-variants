# Clinical Validation Protocol - VariantClassifier

Protocolo de validação clínica para o VariantClassifier seguindo diretrizes ACMG/AMP.

## Sumário

1. [Introdução](#introdução)
2. [Critérios de Validação](#critérios-de-validação)
3. [Dataset de Validação](#dataset-de-validação)
4. [Métricas Clínicas](#métricas-clínicas)
5. [Protocolo de Teste](#protocolo-de-teste)
6. [Interpretação dos Resultados](#interpretação-dos-resultados)
7. [Documentação Obrigatória](#documentação-obrigatória)

---

## Introdução

A validação clínica do VariantClassifier deve seguir as diretrizes do ACMG/AMP (American College of Medical Genetics and Genomics / Association for Molecular Pathology) para classificação de variantes.

### Objetivos

1. **Concordância com especialistas:** Avaliar concordância com classificações de especialistas humanos
2. **Reprodutibilidade:** Medir consistência de predições em cenários clínicos
3. **Performance clínica:** Avaliar impacto em decisões clínicas
4. **Erros críticos:** Identificar e quantificar erros de alta severidade

### Escopo

- Variantes missense
- Variantes nonsense/frameshift (loss-of-function)
- Variantes de splice site
- Genes associados a doenças hereditárias

---

## Critérios de Validação

### Critérios de Aceitação

**Métricas de Performance:**

| Métrica | Mínimo Aceitável | Alvo | Excelente |
|---------|------------------|------|-----------|
| Accuracy | ≥ 0.70 | ≥ 0.80 | ≥ 0.90 |
| ROC-AUC (macro) | ≥ 0.75 | ≥ 0.85 | ≥ 0.95 |
| F1-score (macro) | ≥ 0.70 | ≥ 0.80 | ≥ 0.90 |
| Critical Error Rate | ≤ 5% | ≤ 2% | ≤ 1% |

**Métricas Clínicas:**

| Métrica | Mínimo Aceitável | Alvo |
|---------|------------------|------|
| Sensibilidade (Pathogenic) | ≥ 0.85 | ≥ 0.95 |
| Especificidade (Benign) | ≥ 0.85 | ≥ 0.95 |
| Binary Concordance | ≥ 0.90 | ≥ 0.95 |
| Calibration (ECE) | ≤ 0.10 | ≤ 0.05 |

**Concordância com Especialistas:**

- Cohen's Kappa ≥ 0.80 (quase perfeita)
- Concordância ≥ 85% com curadoria manual

---

## Dataset de Validação

### Fontes de Dados

**ClinVar:**
- Variantes com status de revisão "practice guideline"
- Variantes com "review status" de 2-4 estrelas
- Excluir: "no assertion criteria provided"

**Gold Standard Interno:**
- Variantes revisadas por múltiplos especialistas
- Consenso de 3+ geneticistas clínicos
- Documentação de evidências ACMG

### Estrutura do Dataset

```
Validation Set (N=1000 variantes):
├── Pathogenic (n=200)
│   ├── PVS1 + PS1-4 (n=100)
│   └── PS1-4 forte (n=100)
├── Likely Pathogenic (n=200)
│   ├── PS moderados (n=100)
│   └── PM + PP (n=100)
├── VUS (n=200)
│   ├── Evidências conflitantes (n=100)
│   └── Evidências insuficientes (n=100)
├── Likely Benign (n=200)
│   ├── BS1-4 forte (n=100)
│   └── BP + BS (n=100)
└── Benign (n=200)
    ├── BA1 (n=100)
    └── BS1-4 forte (n=100)
```

### Critérios de Exclusão

1. Variantes com evidências conflitantes não resolvidas
2. Variantes sem evidências suficientes
3. Variantes em genes sem validação clínica
4. Variantes em regiões não cobertas pelo modelo

---

## Métricas Clínicas

### 1. Critical Error Rate

**Definição:** Predições que poderiam levar a decisões clínicas prejudiciais.

**Tipos de Erros Críticos:**

| Erro | Descrição | Impacto |
|------|-----------|---------|
| Pathogenic → Benign | Falso negativo | Falha em tratar doença grave |
| Benign → Pathogenic | Falso positivo | Tratamento desnecessário |
| Pathogenic → VUS | Perda de confiança | Atraso em tratamento |

**Cálculo:**

```python
critical_errors = 0
total_predictions = 0

for true_label, pred_label, prob_pathogenic in validation_data:
    # Erro tipo 1: Pathogenic classificado como Benign
    if true_label == "Pathogenic" and pred_label == "Benign":
        critical_errors += 1

    # Erro tipo 2: Benign classificado como Pathogenic
    elif true_label == "Benign" and pred_label == "Pathogenic":
        critical_errors += 1

    # Erro tipo 3: Pathogenic com baixa confiança
    elif true_label == "Pathogenic" and prob_pathogenic < 0.7:
        critical_errors += 1

    total_predictions += 1

critical_error_rate = critical_errors / total_predictions
```

### 2. Sensibilidade e Especificidade

**Binary Classification:**

```python
# Agrupar classes
pathogenic_classes = ["Pathogenic", "Likely_Pathogenic"]
benign_classes = ["Benign", "Likely_Benign"]
vus_class = "VUS"

# Converter para binário
y_true_binary = [
    1 if label in pathogenic_classes else 0
    for label in y_true
]

y_pred_binary = [
    1 if label in pathogenic_classes else 0
    for label in y_pred
]

# Calcular métricas
sensitivity = TP / (TP + FN)  # Recall para pathogenic
specificity = TN / (TN + FP)  # Recall para benign
```

### 3. Binary Concordance

**Definição:** Concordância quando VUS é excluído.

```python
# Excluir VUS
mask = [
    true not in ["VUS"] and pred not in ["VUS"]
    for true, pred in zip(y_true, y_pred)
]

y_true_no_vus = [y for y, m in zip(y_true_binary, mask) if m]
y_pred_no_vus = [y for y, m in zip(y_pred_binary, mask) if m]

# Calcular concordância
binary_concordance = accuracy_score(y_true_no_vus, y_pred_no_vus)
```

### 4. Calibration

**Expected Calibration Error (ECE):**

```python
def compute_ece(y_true, y_proba, n_bins=10):
    """
    Calcula Expected Calibration Error.
    """
    bin_edges = np.linspace(0, 1, n_bins + 1)
    bin_width = 1.0 / n_bins

    ece = 0.0
    for bin_lower, bin_upper in zip(bin_edges[:-1], bin_edges[1:]):
        # Mask para predições neste bin
        in_bin = np.logical_and(
            y_proba >= bin_lower,
            y_proba < bin_upper
        )

        if in_bin.sum() > 0:
            # Accuracy média no bin
            bin_accuracy = (y_true[in_bin] == y_pred[in_bin]).mean()

            # Confiança média no bin
            bin_confidence = y_proba[in_bin].mean()

            # Peso do bin (proporção de amostras)
            bin_weight = in_bin.mean()

            # Contribuição ao ECE
            ece += bin_weight * np.abs(bin_accuracy - bin_confidence)

    return ece
```

### 5. Cohen's Kappa

**Concordância com especialistas:**

```python
from sklearn.metrics import cohen_kappa_score

kappa = cohen_kappa_score(
    y_true_clinician,
    y_pred_model,
    weights="quadratic"  # Penaliza erros graves
)
```

---

## Protocolo de Teste

### Fase 1: Validacao Interna (1-2 meses)

**Objetivo:** Validar em dataset holdout interno.

**Passos:**

1. **Preparação:**
   - Coletar 1000 variantes com gold standard
   - Split: 70% treino, 15% validação, 15% teste
   - Stratified split por classe ACMG

2. **Treinamento:**
   - Treinar ensemble em dados de treino
   - Otimizar hyperparâmetros em validação
   - Calibrar probabilidades

3. **Teste:**
   - Avaliar em conjunto de teste
   - Computar todas as métricas clínicas
   - Gerar relatório de validação

4. **Revisão:**
   - Analisar erros críticos
   - Investigar casos de discordância
   - Ajustar thresholds se necessário

### Fase 2: Validacao Externa (2-3 meses)

**Objetivo:** Validar em dados de laboratórios externos.

**Passos:**

1. **Coleta:**
   - Parceria com 2-3 laboratórios externos
   - Coletar 500-1000 variantes anonimizadas
   - Garantir diversidade de genes e populações

2. **Teste Cego:**
   - Laboratórios enviam variantes sem labels
   - VariantClassifier retorna predições
   - Comparar com curadoria local

3. **Análise:**
   - Computar concordância inter-laboratório
   - Analisar diferenças populacionais
   - Identificar viéses específicos

### Fase 3: Validacao Clinica (3-6 meses)

**Objetivo:** Validar impacto em decisões clínicas reais.

**Passos:**

1. **Piloto:**
   - Implementar em 1-2 hospitais
   - Usar como suporte à decisão (não substituto)
   - Coletar feedback de geneticistas

2. **Monitoramento:**
   - Registrar concordância com curadoria final
   - Rastrear mudanças em decisão clínica
   - Documentar tempo economizado

3. **Avaliação:**
   - Entrevistas com usuários
   - Análise de casos discordantes
   - Cálculo de ROI (tempo, custo)

---

## Interpretação dos Resultados

### Critérios de Pass/Fail

**Pass em Todas as Fases Se:**
- Critical error rate ≤ 2%
- Sensibilidade (Pathogenic) ≥ 0.90
- Especificidade (Benign) ≥ 0.90
- Binary concordance ≥ 0.95
- Cohen's Kappa ≥ 0.80

**Pass Condicional Se:**
- Critical error rate ≤ 5%
- Sensibilidade ≥ 0.85
- Especificidade ≥ 0.85
- Concordância ≥ 0.90
- Kappa ≥ 0.70

**Requer Revisão Se:**
- Qualquer métrica abaixo de "Pass Condicional"
- Erros críticos > 5%
- Viéses populacionais significativos

### Análise de Erros

**Para Cada Erro Crítico:**

1. **Investigação:**
   - Revisar evidências ACMG
   - Consultar especialistas
   - Verificar qualidade dos dados

2. **Categorização:**
   - Erro do modelo (falso positivo/negativo)
   - Erro dos dados (gold standard incorreto)
   - Caso limítrofe (ambiguidade genuína)

3. **Ação Corretiva:**
   - Retreinar com mais dados
   - Ajustar threshold de decisão
   - Adicionar features específicas
   - Adicionar warning manual para caso

---

## Documentação Obrigatória

### Relatório de Validação

**Seções:**

1. **Resumo Executivo**
   - Objetivos
   - Principais resultados
   - Conclusão

2. **Metodologia**
   - Dataset de validação
   - Procedimentos de teste
   - Métricas utilizadas

3. **Resultados**
   - Tabelas de métricas
   - Matrizes de confusão
   - Curvas ROC e calibração

4. **Análise de Erros**
   - Lista de erros críticos
   - Investigação de casos
   - Plano de ação

5. **Limitações**
   - Viéses conhecidos
   - Populações não representadas
   - Classes de variantes não cobertas

6. **Conclusão**
   - Status de validação
   - Recomendações de uso
   - Próximos passos

### Regulatory Documentation

**Para FDA/CE:**

1. **Intended Use:** Diagnóstico de suporte para variantes genômicas
2. **Indications for Use:** Pacientes com suspeita de doenças genéticas hereditárias
3. **Contraindications:** Nenhuma (uso apenas como suporte)
4. **Warnings:** Não substituir avaliação de especialista
5. **Performance Summary:** Tabelas de sensibilidade/especificidade

---

## Controle de Versão e Auditoria

### Versionamento

- Cada validação deve ter número de versão
- Mudanças no modelo requerem revalidação
- Manter histórico de todas as versões

### Auditoria

**Trilha de Auditoria:**

1. Data e hora da validação
2. Versão do modelo
3. Dataset utilizado (hash)
4. Responsável pela validação
5. Resultados completos
6. Aprovações

**Armazenamento:**

- Dados de validação: 5 anos
- Relatórios: 10 anos
- Logs de predição: 2 anos

---

## Referências

1. ACMG/AMP Guidelines (Richards et al. 2015)
2. ClinGen Variant Classification Guidelines
3. FDA Software as a Medical Device (SaMD) Guidelines
4. EU IVDR Requirements
5. ISO 13485 Quality Management

---

## Checklist de Validação

**Planejamento:**
- [ ] Objetivos definidos
- [ ] Métricas estabelecidas
- [ ] Dataset preparado
- [ ] Comitê de revisão formado

**Execução:**
- [ ] Fase 1 completa
- [ ] Fase 2 completa
- [ ] Fase 3 completa
- [ ] Todos os testes passaram

**Documentação:**
- [ ] Relatório de validação
- [ ] Análise de erros
- [ ] Documentação regulatory
- [ ] Aprovação ética (se aplicável)

**Deploy:**
- [ ] Modelo aprovado para produção
- [ ] Monitoramento configurado
- [ ] Plano de contingência
- [ ] Treinamento de usuários
