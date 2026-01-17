#!/bin/bash
#
# Script para download de bases de dados de referência
#
# Uso:
#   bash scripts/download_references.sh [--all] [--clinvar] [--gnomad] [--dbnsfp]
#

set -e

EXTERNAL_DIR="data/external"
mkdir -p "$EXTERNAL_DIR"

echo "======================================="
echo " Download de Dados de Referência"
echo "======================================="
echo ""

# Função para mostrar progresso
download_file() {
    local url=$1
    local output=$2
    local name=$3

    echo "Baixando $name..."
    echo "URL: $url"
    echo "Output: $output"

    if [ -f "$output" ]; then
        echo "Arquivo já existe. Pulando (use --force para baixar novamente)."
        return 0
    fi

    if command -v wget >/dev/null 2>&1; then
        wget -O "$output" "$url"
    elif command -v curl >/dev/null 2>&1; then
        curl -L -o "$output" "$url"
    else
        echo "ERRO: Nem wget nem curl encontrados."
        exit 1
    fi

    echo "$name baixado com sucesso!"
    echo ""
}

# Parse argumentos
DOWNLOAD_ALL=false
DOWNLOAD_CLINVAR=false
DOWNLOAD_GNOMAD=false
DOWNLOAD_DBNSFP=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --all)
            DOWNLOAD_ALL=true
            shift
            ;;
        --clinvar)
            DOWNLOAD_CLINVAR=true
            shift
            ;;
        --gnomad)
            DOWNLOAD_GNOMAD=true
            shift
            ;;
        --dbnsfp)
            DOWNLOAD_DBNSFP=true
            shift
            ;;
        *)
            echo "Opção desconhecida: $1"
            echo "Uso: $0 [--all] [--clinvar] [--gnomad] [--dbnsfp]"
            exit 1
            ;;
    esac
done

if [ "$DOWNLOAD_ALL" = true ]; then
    DOWNLOAD_CLINVAR=true
    DOWNLOAD_GNOMAD=true
    DOWNLOAD_DBNSFP=true
fi

# ClinVar
if [ "$DOWNLOAD_CLINVAR" = true ]; then
    echo "======================================="
    echo "ClinVar"
    echo "======================================="
    download_file \
        "https://ftp.ncbi.nlm.nih.gov/pub/clinvar/vcf_GRCh38/clinvar.vcf.gz" \
        "$EXTERNAL_DIR/clinvar.vcf.gz" \
        "ClinVar VCF"

    # Indexa com bcftools se disponível
    if command -v bcftools >/dev/null 2>&1; then
        echo "Indexando ClinVar..."
        bcftools index "$EXTERNAL_DIR/clinvar.vcf.gz"
    fi
fi

# gnomAD
if [ "$DOWNLOAD_GNOMAD" = true ]; then
    echo "======================================="
    echo "gnomAD"
    echo "======================================="
    echo ""
    echo "NOTA: gnomAD requer registro manual em:"
    echo "https://gnomad.broadinstitute.org/register"
    echo ""
    echo "Após registro, baixe os arquivos de:"
    echo "https://gnomad.broadinstitute.org/downloads"
    echo ""
    echo "Arquivos recomendados:"
    echo "  - exomes/gnomad.exomes.r3.1.sites.vcf.gz"
    echo "  - genomes/gnomad.genomes.v3.1.sites.vcf.gz"
fi

# dbNSFP
if [ "$DOWNLOAD_DBNSFP" = true ]; then
    echo "======================================="
    echo "dbNSFP"
    echo "======================================="
    echo ""
    echo "dbNSFP está disponível em:"
    echo "https://dbnsfp.sv.genomen.org/"
    echo ""
    echo "Versão mais recente: 4.6a"
    echo "Arquivo: dbNSFP4.6a.zip (~40GB)"
    echo ""
    echo "Download direto:"
    download_file \
        "https://dbnsfp.sv.genomen.org/dbNSFP4.6a.zip.gz" \
        "$EXTERNAL_DIR/dbnsfp4.6a.zip.gz" \
        "dbNSFP"

    echo "Descomprimindo..."
    cd "$EXTERNAL_DIR"
    gunzip -c dbnsfp4.6a.zip.gz | unzip - dbnsfp4.6a_chromosomewise.zip 2>/dev/null || true
    cd -
fi

echo ""
echo "======================================="
echo "Download Concluído!"
echo "======================================="
echo ""
echo "Arquivos baixados:"
ls -lh "$EXTERNAL_DIR"
echo ""
echo "Próximo passo: Processar com scripts/prepare_references.py"
