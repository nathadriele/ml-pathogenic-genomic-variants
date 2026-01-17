# Data Raw - Arquivos VCF de Entrada

Este diretório deve conter arquivos VCF (Variant Call Format) brutos para processamento.

## Formato Aceito

- VCF versão 4.2+
- Comprimido ou não (.vcf, .vcf.gz)
- Codificação UTF-8
- Headers obrigatórios: ##fileformat, ##reference

## Estrutura Esperada

### Colunas Obrigatórias (VCF padrão)
```
#CHROM  POS ID  REF  ALT  QUAL  FILTER  INFO  FORMAT  SAMPLE
```

### Campos INFO Recomendados
- Gene: Symbol do gene afetado
- Consequence: Tipo de consequência funcional
- AF: Frequência alélica
- DP: Profundidade de cobertura

## Exemplo de Uso

```bash
# Copiar arquivo VCF para este diretório
cp /caminho/seu/arquivo.vcf.gz data/raw/

# Processar com pipeline de ingestão
python scripts/process_vcf.py --input data/raw/arquivo.vcf.gz
```

## Dados de Exemplo

Este diretório contém arquivos de exemplo para demonstração:

1. `example_brca1.vcf` - Variantes do gene BRCA1
2. `example_lung_cancer_panel.vcf` - Painel de câncer de pulmão
3. `example_mmr_genes.vcf` - Genes MMR (síndrome de Lynch)

## Notas

- Arquivos deste diretório NÃO são versionados no Git
- Use dados anonimizados para conformidade com LGPD/GDPR
- Mantenha backups dos arquivos originais
