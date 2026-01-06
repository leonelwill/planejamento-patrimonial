import streamlit as st
import pandas as pd
import plotly.express as px

# --- Configuração da Página ---
st.set_page_config(
    page_title="Planejamento Patrimonial",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CSS Personalizado (Estilo Dark e Títulos Brancos) ---
st.markdown("""
    <style>
    /* Forçar cor branca nos títulos principais */
    h1, h2, h3, h4 {
        color: #FFFFFF !important;
    }
    /* Ajuste de métricas para destacar valores */
    div[data-testid="stMetricValue"] {
        font-size: 1.5rem;
        color: #00FF7F; /* Verde Primavera para valores positivos */
    }
    /* Fundo dos cards de aviso */
    .stAlert {
        background-color: #2b2b2b;
        color: #ddd;
    }
    /* Estilizar o expander do roteiro */
    .streamlit-expanderHeader {
        font-weight: bold;
        color: #FFD700 !important; /* Dourado */
    }
    </style>
""", unsafe_allow_html=True)

# --- Funções Auxiliares ---
def format_currency(value):
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def calcular_itcmd_progressivo(valor_base):
    """
    Calcula o ITCMD progressivo baseado no PL n.7/2024 (SP).
    Lógica de faixas (cálculo marginal).
    """
    faixa_1_limite = 353600.00      # 2%
    faixa_2_limite = 3005600.00     # 4%
    faixa_3_limite = 9900800.00     # 6%
    # Acima disso 8%

    imposto = 0.0

    # Faixa 1: Até 353k
    if valor_base > 0:
        base_faixa_1 = min(valor_base, faixa_1_limite)
        imposto += base_faixa_1 * 0.02
    
    # Faixa 2: 353k a 3MM
    if valor_base > faixa_1_limite:
        base_faixa_2 = min(valor_base, faixa_2_limite) - faixa_1_limite
        imposto += base_faixa_2 * 0.04
        
    # Faixa 3: 3MM a 9.9MM
    if valor_base > faixa_2_limite:
        base_faixa_3 = min(valor_base, faixa_3_limite) - faixa_2_limite
        imposto += base_faixa_3 * 0.06
        
    # Faixa 4: Acima de 9.9MM
    if valor_base > faixa_3_limite:
        base_faixa_4 = valor_base - faixa_3_limite
        imposto += base_faixa_4 * 0.08
        
    return imposto

# --- Cabeçalho ---
st.title("Calculadora de Planejamento Patrimonial")
st.markdown("---")

# --- Colunas Principais ---
col_patrimonio, col_custos = st.columns([1, 1.2], gap="large")

# ==========================================================
# SEÇÃO 1: PATRIMÔNIO
# ==========================================================
with col_patrimonio:
    st.subheader("1. Levantamento Patrimonial")
    
    val_imoveis = st.number_input("Imóveis", min_value=0.0, step=50000.0, format="%.2f")
    val_aplicacoes = st.number_input("Aplicações Financeiras", min_value=0.0, step=10000.0, format="%.2f")
    val_veiculos = st.number_input("Veículos", min_value=0.0, step=5000.0, format="%.2f")
    val_empresas = st.number_input("Participação em Empresas", min_value=0.0, step=50000.0, format="%.2f")
    val_outros = st.number_input("Outros Bens", min_value=0.0, step=5000.0, format="%.2f")
    
    st.markdown("### Previdência Privada *")
    col_prev_input, col_prev_check = st.columns([0.7, 0.3])
    with col_prev_input:
        val_previdencia = st.number_input("Saldo em Previdência", min_value=0.0, step=10000.0, format="%.2f")
    with col_prev_check:
        st.write("") # Espaçamento
        st.write("")
        incluir_prev = st.checkbox("Incluir no Inventário?", value=False)
    
    st.info("* Como padrão, a previdência privada (VGBL) não entra no cálculo de inventário, porém isso depende da legislação estadual e da estrutura do plano (PGBL vs VGBL).")

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
    
    # Seleção de Estado
    col_estado, col_toggle = st.columns([1, 1])
    with col_estado:
        estados = ["São Paulo (SP)", "Rio de Janeiro (RJ)", "Minas Gerais (MG)", "Outros"]
        estado_selecionado = st.selectbox("Selecione o Estado:", estados)
    
    # Definição da Alíquota Padrão por Estado
    aliquota_padrao = 4.0
    if estado_selecionado == "Rio de Janeiro (RJ)":
        aliquota_padrao = 4.0 
    elif estado_selecionado == "Minas Gerais (MG)":
        aliquota_padrao = 5.0
    
    # Botão de Pânico (PL 7/2024)
    with col_toggle:
        st.write("") 
        st.write("")
        usar_progressivo = st.toggle("⚠️ Simular PL n.7/2024 (SP)?")
    
    if usar_progressivo:
        st.warning(f"Simulação PL 7/2024 (SP) Ativada: Alíquotas progressivas de 2% a 8%.")
        valor_itcmd = calcular_itcmd_progressivo(total_patrimonio)
        # Evitar divisão por zero para exibição
        aliquota_itcmd_exibicao = (valor_itcmd / total_patrimonio * 100) if total_patrimonio > 0 else 0.0
    else:
        aliquota_itcmd_exibicao = aliquota_padrao
        valor_itcmd = total_patrimonio * (aliquota_itcmd_exibicao / 100)

    # Tabela de Custos
    st.markdown("#### Detalhamento de Custos")
    col_c1, col_c2, col_c3 = st.columns([2, 1, 1.5])
    
    # Cabeçalhos
    with col_c1: st.write("**Item**")
    with col_c2: st.write("**%**")
    with col_c3: st.write("**Valor (R$)**")
    
    # Linha 1: ITCMD
    with col_c1: st.markdown("ITCMD (Imposto)")
    with col_c2:
        if usar_progressivo:
            st.write(f"~{aliquota_itcmd_exibicao:.2f}%") 
        else:
            aliquota_itcmd_input = st.number_input("Alíquota ITCMD", value=aliquota_padrao, step=0.5, label_visibility="collapsed", key="aliq_itcmd")
            valor_itcmd = total_patrimonio * (aliquota_itcmd_input / 100)
    with col_c3:
        st.write(format_currency(valor_itcmd))
        
    # Linha 2: Honorários
    with col_c1: st.markdown("Honorários Advocatícios")
    with col_c2:
        aliquota_adv = st.number_input("Aliq. Adv", value=6.0, step=0.5, label_visibility="collapsed", key="aliq_adv")
    with col_c3:
        valor_adv = total_patrimonio * (aliquota_adv / 100)
        st.write(format_currency(valor_adv))
        
    # Linha 3: Cartório/Outros
    with col_c1: st.markdown("Custos Cartório/Outros")
    with col_c2:
        aliquota_cart = st.number_input("Aliq. Cart", value=2.0, step=0.5, label_visibility="collapsed", key="aliq_cart")
    with col_c3:
        valor_cart = total_patrimonio * (aliquota_cart / 100)
        st.write(format_currency(valor_cart))

    st.divider()
    
    # Totais Finais
    custo_total = valor_itcmd + valor_adv + valor_cart
    percentual_perda = (custo_total / total_patrimonio * 100) if total_patrimonio > 0 else 0
    
    # Caixa de destaque final
    st.markdown(
        f"""
        <div style="background-color: #4a1515; padding: 20px; border-radius: 10px; border: 1px solid #ff4b4b; text-align: center;">
            <h3 style="color: white; margin:0;">Custo Total do Inventário</h3>
            <h1 style="color: #ff4b4b; margin:10px 0; font-size: 2.5rem;">{format_currency(custo_total)}</h1>
            <p style="color: #ddd; margin:0; font-size: 1.1rem;">Isso representa <b>{percentual_perda:.2f}%</b> do seu patrimônio atual.</p>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    if usar_progressivo:
        itcmd_antigo = total_patrimonio * 0.04 # Comparando com a base de 4%
        diferenca = valor_itcmd - itcmd_antigo
        if diferenca > 0:
            st.error(f"🚨 A MUDANÇA NA LEI AUMENTARIA SEU CUSTO EM: {format_currency(diferenca)}")

# ==========================================================
# SEÇÃO 3: CENÁRIO GLOBAL (GRÁFICO)
# ==========================================================
st.write("")
st.subheader("3. Cenário Global de Imposto sobre Herança")

# Dados para o gráfico
aliquota_itcmd_final = (valor_itcmd / total_patrimonio * 100) if total_patrimonio > 0 else 0

data_paises = {
    'País': ['Japão', 'Coreia do Sul', 'França', 'EUA', 'Reino Unido', 'Chile', 'Brasil (Sua Família)'],
    'Alíquota Máxima (%)': [55, 50, 45, 40, 40, 25, aliquota_itcmd_final],
    'Cor': ['Mundo', 'Mundo', 'Mundo', 'Mundo', 'Mundo', 'Mundo', 'Você']
}

df_paises = pd.DataFrame(data_paises)
df_paises = df_paises.sort_values(by='Alíquota Máxima (%)', ascending=False)

fig = px.bar(
    df_paises, 
    x='País', 
    y='Alíquota Máxima (%)', 
    color='Cor',
    text_auto='.1f',
    color_discrete_map={'Mundo': 'lightgrey', 'Você': '#ff4b4b'},
    title='Comparativo Internacional de Imposto sobre Herança'
)
fig.update_layout(
    plot_bgcolor='rgba(0,0,0,0)', 
    paper_bgcolor='rgba(0,0,0,0)', 
    font_color='white',
    showlegend=False,
    yaxis=dict(showgrid=False, title=None),
    xaxis=dict(title=None)
)
st.plotly_chart(fig, use_container_width=True)

# ==========================================================
# SEÇÃO 4: ROTEIRO DE APOIO (SCRIPT)
# ==========================================================
with st.expander("📝 Roteiro de Apoio para Apresentação (Clique para abrir)"):
    st.markdown("""
    ### 🗣️ Sugestão de Discurso para o Cliente
    
    **1. O Choque de Realidade:**
    *"Fulano, parabéns pelo patrimônio que você construiu. O que muitas pessoas ignoram é que existe um 'sócio oculto' nesses bens: o Estado e a Burocracia."*
    
    **2. Apresentando a Conta (Aponte para a caixa vermelha):**
    *"Olhe para este número em vermelho. Se algo acontecesse hoje, sua família não receberia os {patrimonio}, mas sim o valor descontado desse custo de **{custo}**. Estamos falando de quase **{pct}%** do seu trabalho de vida virando pó em taxas e honorários."*
    
    **3. O Senso de Urgência (Use o botão PL 7/2024):**
    *"E tem um detalhe: esse é o cenário 'barato'. Existe um projeto de lei em SP (e tendência nacional) para dobrar essa alíquota. (Clique no botão). Veja como o custo salta. A janela para proteger seu patrimônio com as regras atuais está se fechando."*
    
    **4. O Contexto Global (Aponte para o gráfico):**
    *"O Brasil ainda é um paraíso fiscal para herança comparado ao Japão ou EUA. Mas a tendência é subirmos nesse gráfico. A pergunta é: você prefere planejar agora e travar os custos lá embaixo, ou deixar sua família pagar a conta cheia no futuro?"*
    
    **5. Fechamento:**
    *"Existem formas legais (Holdings, Doações em vida, Previdência bem estruturada, Seguro de Vida para liquidez) de reduzir drasticamente essa conta. Posso desenhar um cenário comparativo para você?"*
    """.format(
        patrimonio=format_currency(total_patrimonio), 
        custo=format_currency(custo_total),
        pct=f"{percentual_perda:.1f}"
    ))
