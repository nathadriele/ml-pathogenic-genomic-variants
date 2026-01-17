# Data External - Dados de Referência Externa

Este diretório contém bases de dados e recursos de referência utilizados para anotação de variantes genômicas.

## Bases de Dados Disponíveis

### 1. ClinVar
**Descrição:** Arquivo público de relações entre variantes humanas e fenótipos
**Fonte:** https://ftp.ncbi.nlm.nih.gov/pub/clinvar/vcf_GRCh38/
**Atualização:** Mensal
**Uso:** Classificação clínica de variantes, evidências de patogenicidade

**Campos Importantes:**
- `CLNSIG`: Significado clínico (Pathogenic, Benign, VUS)
- `CLNREVSTAT`: Status de revisão por expert panel
- `CLNDN`: Nome da doença associada

### 2. gnomAD (Genome Aggregation Database)
**Descrição:** Frequências alélicas em populações humanas
**Fonte:** https://gnomad.broadinstitute.org/downloads
**Atualização:** Trimestral
**Uso:** Critérios de frequência populacional (BA1, BS1, PM2)

**Campos Importantes:**
- `AF`: Frequência alélica global
- `AF_popmax`: Frequência máxima por subpopulação
- `Hom`: Contagem de homozigotos

### 3. dbNSFP
**Descrição:** Banco de scores de predição funcional
**Fonte:** https://dbnsfp.sv.genomen.org/
**Atualização:** Anual
**Uso:** Evidências computacionais (PP3/BP4)

**Scores Disponíveis:**
- REVEL: Ensemble de scores
- CADD: Combined Annotation Dependent Depletion
- SIFT: Sort Intolerant From Tolerant
- PolyPhen-2: Polymorphism Phenotyping v2
- MutationTaster: Predição de impacto funcional

### 4. Ensembl VEP
**Descrição:** Variant Effect Predictor - Anotação de variantes
**Fonte:** https://useast.ensembl.org/info/docs/tools/vep/index.html
**API:** Disponível localmente ou via REST
**Uso:** Consequência funcional, posição na proteína, domínios

### 5. SpliceAI
**Descrição:** Predição de splicing via deep learning
**Fonte:** https://github.com/Illumina/SpliceAI
**Uso:** Evidências de impacto em sítios de splicing

**Pontos de Corte:**
- Delta score > 0.5: provável efeito no splice
- Delta score > 0.8: forte evidência de efeito

### 6. Gene Databases
**ClinGen:** https://clinicalgenome.org/
- Gene-Disease Validity
- Dosage Sensitivity
- Variant Pathogenicity

**OMIM:** https://omim.org/
- Fenótipos Mendelianos
- Modos de herança

## Download de Dados

### Script de Download Automatizado

```bash
# Download de todas as bases de dados
python scripts/download_references.sh --all

# Download individual
python scripts/download_references.sh --clinvar
python scripts/download_references.sh --gnomad
python scripts/download_references.sh --dbnsfp
```

## Formato dos Arquivos

### ClinVar (VCF)
```vcf
##fileformat=VCFv4.2
##INFO=<ID=CLNSIG,Number=.,Type=String,Description="Clinical significance">
#CHROM  POS     ID  REF  ALT  QUAL  FILTER  INFO
chr1    235772  .   A    G    .     .      CLNSIG=Pathogenic;CLNREVSTAT=practice_guideline
```

### gnomAD (VCF)
```vcf
##INFO=<ID=AF,Number=A,Type=Float,Description="Allele frequency">
#CHROM  POS     REF  ALT  INFO
chr1    235772  A    G    AF=0.0001;AF_popmax=0.0003;Hom=1
```

### dbNSFP (TSV)
```tsv
chr    pos     ref   alt   aaref   aapos   REVEL   CADD   SIFT   PolyPhen2
chr1    235772  A     G     0.001   0       0.94    35.0   D      D
```

## Uso no Pipeline

### Ordem de Anotação

1. **Parser de VCF** (`src/ingestion/vcf_parser.py`)
   - Lê arquivos VCF brutos
   - Extrai variantes e metadados
   - Valida qualidade

2. **Normalizador** (`src/ingestion/normalizer.py`)
   - Normaliza representação de variantes
   - Padroniza coordenadas
   - Remove duplicatas

3. **Anotador** (`src/annotation/`)
   - VEP: consequências funcionais
   - dbNSFP: scores computacionais
   - ClinVar: classificações clínicas
   - gnomAD: frequências populacionais

4. **Feature Builder** (`src/annotation/feature_builder.py`)
   - Mapeia evidências para critérios ACMG
   - Constrói features finais (28 total)
   - Codifica variáveis categóricas

## Espaço Requerido

- ClinVar VCF: ~500 MB (comprimido)
- gnomAD exomes: ~15 GB (comprimido)
- dbNSFP: ~10 GB (TSV comprimido)
- Total: ~25-30 GB descomprimido

## Manutenção

### Atualização Mensal

```bash
# Atualiza ClinVar
wget -P data/external/ https://ftp.ncbi.nlm.nih.gov/pub/clinvar/vcf_GRCh38/clinvar.vcf.gz

# Atualiza gnomAD (verificar versão mais recente)
# Baixar do site oficial: https://gnomad.broadinstitute.org/downloads
```

### Verificação de Integridade

```bash
# Verifica checksums
md5sum data/external/*.vcf.gz > checksums.md5

# Valida arquivos VCF
bcftools stats data/external/clinvar.vcf.gz
```

## Referências

1. ClinVar: Landrum et al. (2018) Nucleic Acids Res
2. gnomAD: Karczewski et al. (2020) Nature
3. dbNSFP: Liu et al. (2020) Nucleic Acids Res
4. VEP: McLaren et al. (2016) Genome Biol
5. SpliceAI: Jaganathan et al. (2019) Science
