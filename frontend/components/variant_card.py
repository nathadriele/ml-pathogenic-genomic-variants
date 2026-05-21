from typing import Dict, Any, Optional
import streamlit as st
import plotly.graph_objects as go


def display_variant_card(
    variant_data: Dict[str, Any],
    prediction_result: Optional[Dict[str, Any]] = None,
    show_details: bool = True
) -> None:
    st.subheader("Informações da Variante")

    # Layout em duas colunas
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Localização")
        st.write(f"**Cromossomo:** {variant_data.get('chromosome', 'N/A')}")
        st.write(f"**Posição:** {variant_data.get('position', 'N/A')}")
        st.write(f"**Gene:** {variant_data.get('gene_symbol', 'N/A')}")

    with col2:
        st.markdown("### Tipo de Variante")
        st.write(f"**Tipo:** {variant_data.get('variant_type', 'N/A')}")
        st.write(f"**Ref:** {variant_data.get('ref', 'N/A')}")
        st.write(f"**Alt:** {variant_data.get('alt', 'N/A')}")

    st.markdown("---")

    if show_details:
        display_detailed_features(variant_data)

    if prediction_result:
        display_prediction_result(prediction_result)


def display_detailed_features(variant_data: Dict[str, Any]) -> None:
    """Exibe features detalhadas da variante."""
    st.markdown("### Features ACMG")

    # Tabs para organizar as features
    tab1, tab2, tab3, tab4 = st.tabs([
        "Frequência Populacional",
        "Scores Computacionais",
        "Evidências Funcionais",
        "Contexto do Gene"
    ])

    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            st.metric("AF (global)", f"{variant_data.get('gnomad_af', 0):.6f}")
            st.metric(
                "AF_popmax",
                f"{variant_data.get('gnomad_af_popmax', 0):.6f}"
            )
        with col2:
            st.metric(
                "Ausente gnomAD",
                "Sim" if variant_data.get('is_absent_gnomad', False) else "Não"
            )

    with tab2:
        col1, col2 = st.columns(2)
        with col1:
            revel = variant_data.get('revel_score', 0)
            st.metric("REVEL", f"{revel:.3f}")
            st.metric(
                "PP3 (REVEL)",
                "Sim" if revel > 0.75 else "Não"
            )

            cadd = variant_data.get('cadd_phred', 0)
            st.metric("CADD Phred", f"{cadd:.1f}")
            st.metric(
                "PP3 (CADD)",
                "Sim" if cadd > 20 else "Não"
            )

        with col2:
            spliceai = variant_data.get('spliceai_max', 0)
            st.metric("SpliceAI Max", f"{spliceai:.3f}")
            st.metric(
                "PP3 (SpliceAI)",
                "Sim" if spliceai > 0.5 else "Não"
            )

            phylop = variant_data.get('phylop_100way', 0)
            st.metric("PhyloP", f"{phylop:.3f}")
            st.metric(
                "Conservação alta",
                "Sim" if phylop > 2.0 else "Não"
            )

    with tab3:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Evidências Funcionais")
            st.checkbox("Estudo funcional", variant_data.get('has_functional_study', False), disabled=True)
            st.checkbox("Loss of function", variant_data.get('is_lof', False), disabled=True)
            st.checkbox("Missense", variant_data.get('is_missense', False), disabled=True)
            st.checkbox("Região de splice", variant_data.get('is_splice_region', False), disabled=True)

        with col2:
            st.markdown("#### Evidências Clínicas")
            st.checkbox("Gene de doença", variant_data.get('is_disease_gene', True), disabled=True)
            st.metric("ClinVar Stars", variant_data.get('clinvar_stars', 0))
            st.metric("ClinVar Submissões", variant_data.get('clinvar_submissions', 0))

    with tab4:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Gene/Doença")
            st.write(f"**Gene:** {variant_data.get('gene_symbol', 'N/A')}")
            st.write(f"**Exon:** {variant_data.get('exon_number', 'N/A')}")
            st.write(f"**Herança:** {variant_data.get('inheritance_mode', 'N/A')}")

        with col2:
            st.markdown("#### Scores do Gene")
            st.metric("pLI", f"{variant_data.get('gene_pli', 0):.3f}")
            st.metric("LOEUF", f"{variant_data.get('gene_loeuf', 0.5):.3f}")
            st.metric("Missense Z", f"{variant_data.get('gene_missense_z', 0):.2f}")


def display_prediction_result(prediction_result: Dict[str, Any]) -> None:
    """Exibe resultado da predição com visualização."""
    st.markdown("---")
    st.subheader("Resultado da Predição")

    classification = prediction_result.get('classification', 'N/A')
    confidence = prediction_result.get('confidence', 0)
    probabilities = prediction_result.get('probabilities', {})

    # Classificação e confiança
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### Classificação")
        st.markdown(f"**{classification}**")

    with col2:
        st.markdown("### Confiança")
        st.markdown(f"**{confidence:.1%}**")

    with col3:
        st.markdown("### Status")
        if confidence >= 0.9:
            st.markdown("**Alta confiança**")
        elif confidence >= 0.7:
            st.markdown("**Moderada confiança**")
        else:
            st.markdown("**Baixa confiança**")

    st.markdown("---")

    # Gráfico de barras com probabilidades
    display_probability_chart(probabilities, classification)


def display_probability_chart(probabilities: Dict[str, float], predicted_class: str) -> None:
    """Exibe gráfico de barras com probabilidades por classe."""
    st.markdown("### Distribuição de Probabilidades")

    # Ordena classes ACMG
    class_order = [
        "Benign",
        "Likely_Benign",
        "VUS",
        "Likely_Pathogenic",
        "Pathogenic"
    ]

    probs = [probabilities.get(cls, 0.0) for cls in class_order]

    # Cores baseadas em patogenicidade
    colors = ['#2ecc71', '#27ae60', '#95a5a6', '#e67e22', '#e74c3c']

    fig = go.Figure(data=[
        go.Bar(
            x=class_order,
            y=probs,
            marker_color=colors,
            text=[f"{p:.1%}" for p in probs],
            textposition='auto',
        )
    ])

    fig.update_layout(
        title="Probabilidades por Classe ACMG",
        xaxis_title="Classe",
        yaxis_title="Probabilidade",
        yaxis=dict(tickformat=".1%"),
        height=400,
        showlegend=False,
    )

    st.plotly_chart(fig, use_container_width=True)

    # Tabela com probabilidades detalhadas
    st.markdown("#### Probabilidades Detalhadas")

    prob_data = []
    for cls in class_order:
        prob = probabilities.get(cls, 0.0)
        prob_data.append({
            "Classe": cls,
            "Probabilidade": f"{prob:.2%}",
            "Valor": f"{prob:.4f}"
        })

    st.dataframe(
        prob_data,
        hide_index=True,
        use_container_width=True
    )


def display_variant_comparison(
    variants: list[Dict[str, Any]],
    predictions: list[Dict[str, Any]]
) -> None:
    """
    Exibe tabela comparativa de múltiplas variantes.

    Args:
        variants: Lista de dicionários com dados das variantes
        predictions: Lista de dicionários com resultados das predições
    """
    st.subheader("Comparação de Variantes")

    # Prepara dados para tabela
    comparison_data = []
    for var, pred in zip(variants, predictions):
        comparison_data.append({
            "Gene": var.get('gene_symbol', 'N/A'),
            "Posição": var.get('position', 'N/A'),
            "Tipo": var.get('variant_type', 'N/A'),
            "Classificação": pred.get('classification', 'N/A'),
            "Confiança": f"{pred.get('confidence', 0):.1%}",
            "AF": f"{var.get('gnomad_af', 0):.6f}",
            "REVEL": f"{var.get('revel_score', 0):.3f}",
            "CADD": f"{var.get('cadd_phred', 0):.1f}"
        })

    st.dataframe(
        comparison_data,
        use_container_width=True,
        hide_index=True
    )
