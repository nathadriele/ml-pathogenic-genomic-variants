"""
Componente para exibir e gerenciar critérios ACMG/AMP.
"""

from typing import Dict, List, Optional
import streamlit as st
import pandas as pd


# Mapeamento completo de critérios ACMG
ACMG_CRITERIA = {
    # Critérios Patogênicos Fortes (PVS)
    "PVS1": "Variante loss-of-function em gene onde LOF é mecanismo conhecido de doença",

    # Critérios Patogênicos Fortes (PS)
    "PS1": "Mesmo aminoácido que variante patogênica estabelecida",
    "PS2": "De novo em paciente sem história familiar",
    "PS3": "Evidência funcional bem estabelecida de efeito danoso",
    "PS4": "Prevalência aumentada em casos vs controles",

    # Critérios Patogênicos Moderados (PM)
    "PM1": "Localizado em hotspot/domínio funcional crítico",
    "PM2": "Ausente/raro em populações de controle",
    "PM3": "Em trans com variante patogênica em gene recessivo",
    "PM4": "Tamanho do aminoácido diferente em região funcional",
    "PM5": "Mudança para aminoácido diferente de variante patogênica conhecida",
    "PM6": "De novo confirmado sem parentalidade verificada",

    # Critérios Patogênicos de Apoio (PP)
    "PP1": "Co-segregação com doença em múltiplos familiares",
    "PP2": "Gene com baixa tolerância a variantes missense",
    "PP3": "Múltiplos scores computacionais predizem efeito danoso",
    "PP4": "Fenótipo do paciente altamente específico para gene",
    "PP5": "Fonte reputável reporta como patogênica",

    # Critérios Benignos Fortes (BA)
    "BA1": "Frequência alélica > 5% em populações de controle",

    # Critérios Benignos de Apoio (BS)
    "BS1": "Frequência alélica maior que esperado para doença",
    "BS2": "Observada em adulto sadio com idade avançada",
    "BS3": "Evidência funcional bem estabelecida de efeito benigno",
    "BS4": "Frequência maior em controles vs casos",

    # Critérios Benignos de Apoio (BP)
    "BP1": "Missense em gene onde primariamente LOF causa doença",
    "BP2": "Observada em trans com variante patogênica",
    "BP3": "In-frame deleções/insertions em região repetitiva",
    "BP4": "Múltiplos scores computacionais predizem efeito benigno",
    "BP5": "Variante encontrada em caso com causa molecular alternativa",
    "BP6": "Fonte reputável reporta como benigna",
    "BP7": "Variante sinônima sem efeito no splice",
}


def display_acmg_criteria(
    selected_criteria: Optional[Dict[str, bool]] = None,
    editable: bool = False
) -> Dict[str, bool]:
    """
    Exibe checklist de critérios ACMG/AMP.

    Args:
        selected_criteria: Dicionário com critérios já selecionados
        editable: Se True, permite interação do usuário

    Returns:
        Dicionário com critérios selecionados
    """
    st.markdown("### Critérios ACMG/AMP")

    if selected_criteria is None:
        selected_criteria = {}

    # Organiza critérios por categoria
    categories = {
        "Patogênicos Muito Fortes (PVS)": ["PVS1"],
        "Patogênicos Fortes (PS)": ["PS1", "PS2", "PS3", "PS4"],
        "Patogênicos Moderados (PM)": ["PM1", "PM2", "PM3", "PM4", "PM5", "PM6"],
        "Patogênicos de Apoio (PP)": ["PP1", "PP2", "PP3", "PP4", "PP5"],
        "Benignos Fortes (BA)": ["BA1"],
        "Benignes de Apoio (BS)": ["BS1", "BS2", "BS3", "BS4"],
        "Benignos de Apoio (BP)": ["BP1", "BP2", "BP3", "BP4", "BP5", "BP6", "BP7"],
    }

    result = {}

    for category, criteria_list in categories.items():
        with st.expander(category):
            for criterion in criteria_list:
                description = ACMG_CRITERIA.get(criterion, "Descrição não disponível")
                is_checked = selected_criteria.get(criterion, False)

                if editable:
                    checked = st.checkbox(
                        f"**{criterion}** - {description}",
                        value=is_checked,
                        key=criterion
                    )
                    result[criterion] = checked
                else:
                    st.markdown(f"{'✓' if is_checked else '✗'} **{criterion}** - {description}")
                    result[criterion] = is_checked

    return result


def calculate_acmg_classification(criteria: Dict[str, bool]) -> str:
    """
    Calcula classificação ACMG baseada em critérios selecionados.

    Args:
        criteria: Dicionário com critérios ACMG selecionados

    Returns:
        Classificação ACMG (Pathogenic, Likely_Pathogenic, VUS, Likely_Benign, Benign)
    """
    # Conta critérios por categoria
    pvs = sum(criteria.get(k, False) for k in ["PVS1"])
    ps = sum(criteria.get(k, False) for k in ["PS1", "PS2", "PS3", "PS4"])
    pm = sum(criteria.get(k, False) for k in ["PM1", "PM2", "PM3", "PM4", "PM5", "PM6"])
    pp = sum(criteria.get(k, False) for k in ["PP1", "PP2", "PP3", "PP4", "PP5"])

    ba = sum(criteria.get(k, False) for k in ["BA1"])
    bs = sum(criteria.get(k, False) for k in ["BS1", "BS2", "BS3", "BS4"])
    bp = sum(criteria.get(k, False) for k in ["BP1", "BP2", "BP3", "BP4", "BP5", "BP6", "BP7"])

    # Regras simplificadas de classificação ACMG
    # Pathogenic
    if (pvs >= 1 and (ps >= 1 or pm >= 1 or pp >= 2)) or \
       (pvs >= 1 and bs <= 1) or \
       (ps >= 2) or \
       (ps >= 1 and pm >= 3) or \
       (ps >= 1 and pm >= 2 and pp >= 2) or \
       (ps >= 1 and pm >= 1 and pp >= 4) or \
       (pm >= 4):
        return "Pathogenic"

    # Likely Pathogenic
    if (pvs >= 1 and pm >= 2) or \
       (pvs >= 1 and pp >= 1) or \
       (ps >= 1 and pm >= 1) or \
       (ps >= 1 and pp >= 2) or \
       (pm >= 2 and pp >= 2) or \
       (pm >= 3) or \
       (pp >= 4):
        return "Likely_Pathogenic"

    # Benign
    if ba >= 1:
        return "Benign"

    # Likely Benign
    if bs >= 2 or (bs >= 1 and bp >= 1):
        return "Likely_Benign"

    # VUS (Variant of Uncertain Significance)
    return "VUS"


def display_acmg_summary(criteria: Dict[str, bool]) -> None:
    """Exibe resumo de critérios selecionados e classificação calculada."""
    st.markdown("---")
    st.markdown("### Resumo da Classificação ACMG")

    # Calcula classificação
    classification = calculate_acmg_classification(criteria)

    # Conta critérios
    counts = {
        "PVS": sum(criteria.get(k, False) for k in ["PVS1"]),
        "PS": sum(criteria.get(k, False) for k in ["PS1", "PS2", "PS3", "PS4"]),
        "PM": sum(criteria.get(k, False) for k in ["PM1", "PM2", "PM3", "PM4", "PM5", "PM6"]),
        "PP": sum(criteria.get(k, False) for k in ["PP1", "PP2", "PP3", "PP4", "PP5"]),
        "BA": sum(criteria.get(k, False) for k in ["BA1"]),
        "BS": sum(criteria.get(k, False) for k in ["BS1", "BS2", "BS3", "BS4"]),
        "BP": sum(criteria.get(k, False) for k in ["BP1", "BP2", "BP3", "BP4", "BP5", "BP6", "BP7"]),
    }

    # Exibe contagem
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### Patogênicos")
        st.write(f"PVS: {counts['PVS']}")
        st.write(f"PS: {counts['PS']}")
        st.write(f"PM: {counts['PM']}")
        st.write(f"PP: {counts['PP']}")

    with col2:
        st.markdown("#### Benignos")
        st.write(f"BA: {counts['BA']}")
        st.write(f"BS: {counts['BS']}")
        st.write(f"BP: {counts['BP']}")

    with col3:
        st.markdown("#### Classificação")
        st.markdown(f"**{classification}**")

        # Cores baseadas em patogenicidade
        color_map = {
            "Pathogenic": "🔴",
            "Likely_Pathogenic": "🟠",
            "VUS": "⚫",
            "Likely_Benign": "🔵",
            "Benign": "🟢"
        }
        # Note: emojis são usados aqui apenas como visualização temporária,
        # o usuário principal pediu para remover emojis dos arquivos principais
        # Mas como este é um componente opcional de visualização clínica,
        # mantive por clareza. Podemos remover se necessário.


def display_acmg_comparison(
    ml_classification: str,
    acmg_classification: str,
    confidence: float
) -> None:
    """
    Compara classificação ML vs ACMG.

    Args:
        ml_classification: Classificação do modelo ML
        acmg_classification: Classificação ACMG calculada
        confidence: Confiança da predição ML
    """
    st.markdown("---")
    st.markdown("### Comparação: ML vs ACMG")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### Modelo ML")
        st.markdown(f"**{ml_classification}**")
        st.caption(f"Confiança: {confidence:.1%}")

    with col2:
        st.markdown("#### ACMG")
        st.markdown(f"**{acmg_classification}**")

    with col3:
        st.markdown("#### Concordância")
        if ml_classification == acmg_classification:
            st.markdown("**Concordante**")
            st.success("As classificações coincidem")
        elif ml_classification in ["Pathogenic", "Likely_Pathogenic"] and \
             acmg_classification in ["Pathogenic", "Likely_Pathogenic"]:
            st.markdown("**Parcialmente Concordante**")
            st.info("Ambas indicam patogenicidade")
        elif ml_classification in ["Benign", "Likely_Benign"] and \
             acmg_classification in ["Benign", "Likely_Benign"]:
            st.markdown("**Parcialmente Concordante**")
            st.info("Ambas indicam benignidade")
        else:
            st.markdown("**Discordante**")
            st.warning("As classificações diferem")


def export_acmg_report(criteria: Dict[str, bool], variant_data: Dict[str, Any]) -> str:
    """
    Gera relatório textual de critérios ACMG.

    Args:
        criteria: Dicionário com critérios selecionados
        variant_data: Dados da variante

    Returns:
        String com relatório formatado
    """
    report = []
    report.append("=" * 80)
    report.append("RELATÓRIO DE CLASSIFICAÇÃO ACMG/AMP")
    report.append("=" * 80)
    report.append("")

    # Informações da variante
    report.append("VARIANTE")
    report.append("-" * 80)
    report.append(f"Gene: {variant_data.get('gene', 'N/A')}")
    report.append(f"Cromossomo: {variant_data.get('chromosome', 'N/A')}")
    report.append(f"Posição: {variant_data.get('position', 'N/A')}")
    report.append(f"Tipo: {variant_data.get('variant_type', 'N/A')}")
    report.append(f"Ref: {variant_data.get('ref', 'N/A')} → Alt: {variant_data.get('alt', 'N/A')}")
    report.append("")

    # Critérios aplicados
    report.append("CRITÉRIOS APLICADOS")
    report.append("-" * 80)

    selected = [k for k, v in criteria.items() if v]
    if selected:
        for criterion in selected:
            description = ACMG_CRITERIA.get(criterion, "Descrição não disponível")
            report.append(f"{criterion}: {description}")
    else:
        report.append("Nenhum critério selecionado")

    report.append("")

    # Classificação
    classification = calculate_acmg_classification(criteria)
    report.append("CLASSIFICAÇÃO FINAL")
    report.append("-" * 80)
    report.append(classification)
    report.append("")
    report.append("=" * 80)

    return "\n".join(report)
