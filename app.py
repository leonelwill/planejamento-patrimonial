import streamlit as st
import pandas as pd
import plotly.express as px

# --- Configuração da Página ---
st.set_page_config(
    page_title="Planejamento Patrimonial",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CSS Personalizado ---
st.markdown("""
    <style>
    /* 1. Título Centralizado e Branco */
    h1 {
        text-align: center;
        color: #FFFFFF !important;
        padding-bottom: 20px;
    }
    h2, h3, h4 {
        color: #FFFFFF !important;
    }
    /* Ajuste de métricas */
    div[data-testid="stMetricValue"] {
        font-size: 1.6rem;
        color: #00FF7F; 
    }
    /* Estilo para o Texto do Cliente */
    .client-box {
        background-color: #1E1E1E;
        padding: 25px;
        border-radius: 10px;
        border-left: 5px solid #FFD700;
        margin-top: 20px;
    }
    .client-text {
        color: #E0E0E0;
        font-size: 1.1rem;
        line-height: 1.6;
    }
    .highlight {
        color: #FF4B4B;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# --- Funções Auxiliares ---
def format_currency(value):
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def obter_aliquota_pl_sp_fixa(valor_base):
    """
    Define a alíquota baseada na faixa do valor total (Progressividade Simples/Tabela).
    Não é cálculo marginal, é alíquota sobre o total dependendo de onde cai.
    Valores baseados em UFESPs aproximadas do PL.
    """
    if valor_base <= 353600.00:
        return 2.0
    elif valor_base <= 3005600.00:
        return 4.0
    elif valor_base <= 9900800.00:
        return 6.0
    else:
        return 8.0

# --- Título Centralizado ---
st.title("Calculadora de Planejamento Patrimonial")

# --- Colunas Principais ---
col_patrimonio, col_custos = st.columns([1, 1.2], gap="large")

# ==========================================================
# SEÇÃO 1: PATRIMÔNIO
# ==========================================================
with col_patrimonio:
    st.subheader("1. Levantamento Patrimonial")
    st.caption("Digite os valores (o formato R$ aparece após confirmar)")
    
    # Inputs formatados para exibir separadores de milhar após o Enter
    val_imoveis = st.number_input("Imóveis", min_value=0.0, step=100000.0, format="%.2f")
    val_aplicacoes = st.number_input("Aplicações Financeiras", min_value=0.0, step=50000.0, format="%.2f")
    val_veiculos = st.number_input("Veículos", min_value=0.0, step=10000.0, format="%.2f")
    val_empresas = st.number_input("Participação em Empresas", min_value=0.0, step=100000.0, format="%.2f")
    val_outros = st.number_input("Outros Bens", min_value=0.0, step=10000.0, format="%.2f")
    
    st.markdown("### Previdência Privada *")
    col_prev_input, col_prev_check = st.columns([0.7, 0.3])
    with col_prev_input:
        val_previdencia = st.number_input("Saldo em Previdência", min_value=0.0, step=50000.0, format="%.2f")
    with col_prev_check:
        st.write("") 
        st.write("")
        incluir_prev = st.checkbox("Incluir?", value=False)
    
    st.info("* Obs: Como padrão, a previdência privada não entra no cálculo de inventário, porém depende de cada estado.")

    # Cálculo do Total Patrimonial
    total_patrimonio = val_imoveis + val_aplicacoes + val_veiculos + val_empresas + val_outros
    if incluir_prev:
        total_patrimonio += val_previdencia
        
    st.divider()
    st.metric(label="Total Inventariável", value=format_currency(total_patrimonio))

# ==========================================================
# SEÇÃO 2: CUSTOS DE INVENTÁRIO
# ==========================================================
with col_custos:
    st.subheader("2. Custos de Sucessão")
    
    # Seleção de Estado e Botão PL na mesma linha para economizar espaço
    col_uf, col_pl = st.columns([1, 1])
    with col_uf:
        estados = ["São Paulo (SP)", "Rio de Janeiro (RJ)", "Minas Gerais (MG)", "Outros"]
        estado_selecionado = st.selectbox("Estado Base:", estados)
    
    with col_pl:
        st.write("") # Espaço para alinhar verticalmente
        st.write("") 
        # Botão PL - Se ativo, recalculamos a sugestão de alíquota
        usar_pl = st.toggle("Simular PL n.7/2024 (SP)?")

    # --- Lógica de Alíquotas ---
    # 1. Define a alíquota SUGERIDA baseada na escolha (Estado ou PL)
    if usar_pl:
        aliquota_sugerida = obter_aliquota_pl_sp_fixa(total_patrimonio)
        texto_aviso = f"Pelo valor do patrimônio, a alíquota na nova tabela seria **{aliquota_sugerida}%**."
        cor_aviso = "warning"
    else:
        # Lógica padrão dos estados
        if estado_selecionado == "Rio de Janeiro (RJ)":
            aliquota_sugerida = 4.0 # Deixamos 4 como base, mas RJ tem progressiva também
        elif estado_selecionado == "Minas Gerais (MG)":
            aliquota_sugerida = 5.0
        else:
            aliquota_sugerida = 4.0
        texto_aviso = None

    # --- Tabela de Custos Alinhada ---
    st.markdown("#### Detalhamento de Custos")
    
    # Se houver aviso de mudança de alíquota pelo PL
    if usar_pl:
        st.caption(f"⚠️ {texto_aviso}")

    # Cabeçalho da Tabela
    c_head1, c_head2, c_head3 = st.columns([3, 1.5, 2])
    c_head1.markdown("**Item**")
    c_head2.markdown("**Alíquota (%)**")
    c_head3.markdown("**Valor (R$)**")

    # --- Linha 1: ITCMD ---
    c_itcmd1, c_itcmd2, c_itcmd3 = st.columns([3, 1.5, 2])
    with c_itcmd1:
        st.write("ITCMD (Imposto Estadual)")
    with c_itcmd2:
        # O valor padrão vem da lógica acima, mas o usuário PODE editar sempre
        aliquota_itcmd = st.number_input(
            "Aliq ITCMD", 
            value=float(aliquota_sugerida), 
            step=0.5, 
            label_visibility="collapsed",
            key="input_itcmd"
        )
    with c_itcmd3:
        val_itcmd = total_patrimonio * (aliquota_itcmd / 100)
        st.write(f"**{format_currency(val_itcmd)}**")

    # --- Linha 2: Honorários ---
    c_hon1, c_hon2, c_hon3 = st.columns([3, 1.5, 2])
    with c_hon1:
        st.write("Honorários Advocatícios")
    with c_hon2:
        aliquota_hon = st.number_input(
            "Aliq Hon", 
            value=6.0, 
            step=0.5, 
            label_visibility="collapsed", 
            key="input_hon"
        )
    with c_hon3:
        val_hon = total_patrimonio * (aliquota_hon / 100)
        st.write(f"{format_currency(val_hon)}")

    # --- Linha 3: Cartório/Outros ---
    c_cart1, c_cart2, c_cart3 = st.columns([3, 1.5, 2])
    with c_cart1:
        st.write("Custos Cartório/Outros")
    with c_cart2:
        aliquota_cart = st.number_input(
            "Aliq Cart", 
            value=2.0, 
            step=0.5, 
            label_visibility="collapsed", 
            key="input_cart"
        )
    with c_cart3:
        val_cart = total_patrimonio * (aliquota_cart / 100)
        st.write(f"{format_currency(val_cart)}")

    st.divider()

    # --- Totais ---
    custo_total = val_itcmd + val_hon + val_cart
    percentual_total = (custo_total / total_patrimonio * 100) if total_patrimonio > 0 else 0

    # Box de Destaque
    st.markdown(
        f"""
        <div style="background-color: #4a1515; padding: 15px; border-radius: 8px; border: 1px solid #ff4b4b; text-align: center;">
            <p style="color: white; margin:0; font-size: 1.2rem;">Custo Total Estimado</p>
            <h1 style="color: #ff4b4b; margin: 5px 0; font-size: 2.8rem;">{format_currency(custo_total)}</h1>
            <p style="color: #ddd; margin:0;">Comprometimento Patrimonial: <b>{percentual_total:.2f}%</b></p>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    # Comparativo PL (Delta)
    if usar_pl:
        # Comparar com o cenário base de 4% (SP padrão atual)
        custo_base = total_patrimonio * 0.04
        delta = val_itcmd - custo_base
        if delta > 0:
            st.error(f"📈 Impacto da Nova Lei: Aumento de {format_currency(delta)} apenas em impostos.")

# ==========================================================
# SEÇÃO 3: GRÁFICO GLOBAL
# ==========================================================
st.write("")
st.subheader("3. Onde você está no mundo?")

# Dados Gráfico
aliquota_efetiva_imposto = aliquota_itcmd # Usamos a alíquota configurada no input
data_paises = {
    'País': ['Japão', 'Coreia do Sul', 'França', 'EUA', 'Reino Unido', 'Chile', 'Brasil (Sua Simulação)'],
    'Taxa Máxima': [55, 50, 45, 40, 40, 25, aliquota_efetiva_imposto],
    'Tipo': ['Mundo', 'Mundo', 'Mundo', 'Mundo', 'Mundo', 'Mundo', 'Voce']
}
df_paises = pd.DataFrame(data_paises).sort_values(by='Taxa Máxima', ascending=False)

fig = px.bar(
    df_paises, x='País', y='Taxa Máxima', color='Tipo', text_auto='.1f',
    color_discrete_map={'Mundo': 'gray', 'Voce': '#FF4B4B'},
    title=None
)
fig.update_layout(
    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
    font_color='white', showlegend=False, height=350,
    yaxis=dict(showgrid=False, title=None), xaxis=dict(title=None)
)
st.plotly_chart(fig, use_container_width=True)

# ==========================================================
# SEÇÃO 4: TEXTO PARA O CLIENTE (Diagnóstico)
# ==========================================================
st.markdown("### 4. Diagnóstico Preliminar")

texto_diagnostico = f"""
<div class="client-box">
    <p class="client-text">
        Prezado(a), com base no levantamento realizado, seu patrimônio total inventariável soma 
        <span class="highlight">{format_currency(total_patrimonio)}</span>.
    </p>
    <p class="client-text">
        No cenário atual, sem um planejamento sucessório eficiente, estima-se que sua família terá que desembolsar 
        cerca de <span class="highlight">{format_currency(custo_total)}</span> ({percentual_total:.1f}%) apenas para ter acesso aos bens. 
        Isso exige alta liquidez imediata no momento mais delicado para a família.
    </p>
    <p class="client-text">
        Além disso, observando o cenário global e o <span class="highlight">Projeto de Lei n.7/2024</span>, 
        há uma tendência clara de aumento da carga tributária no Brasil, o que pode elevar significativamente 
        esse custo caso a sucessão ocorra sob a nova vigência.
        A antecipação e a estruturação (Holding, Doações, Previdência) são as únicas ferramentas para travar esses custos.
    </p>
</div>
"""
st.markdown(texto_diagnostico, unsafe_allow_html=True)
