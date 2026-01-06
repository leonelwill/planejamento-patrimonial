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
    /* Títulos Brancos e Centralizados */
    h1 { text-align: center; color: #FFFFFF !important; padding-bottom: 20px; }
    h2, h3, h4 { color: #FFFFFF !important; }
    
    /* Métricas */
    div[data-testid="stMetricValue"] { font-size: 1.6rem; color: #00FF7F; }
    
    /* Box do Cliente */
    .client-box {
        background-color: #1E1E1E;
        padding: 25px;
        border-radius: 10px;
        border-left: 5px solid #FFD700;
        margin-top: 20px;
    }
    .client-text { color: #E0E0E0; font-size: 1.1rem; line-height: 1.6; }
    .highlight { color: #FF4B4B; font-weight: bold; }
    
    /* Ajuste de inputs numéricos para alinhar texto */
    input { text-align: right; }
    </style>
""", unsafe_allow_html=True)

# --- Funções Auxiliares ---
def format_currency(value):
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def obter_aliquota_pl_sp_fixa(valor_base):
    """
    Retorna a alíquota fixa baseada na faixa (Não progressiva marginal, mas fixa por faixa).
    """
    if valor_base <= 353600.00:
        return 2.0
    elif valor_base <= 3005600.00:
        return 4.0
    elif valor_base <= 9900800.00:
        return 6.0
    else:
        return 8.0

# --- Callbacks (Lógica de Atualização Automática) ---
def atualizar_aliquota_itcmd():
    """
    Chamada quando o botão 'Simular PL' é alterado.
    Calcula e joga o valor para dentro do input de ITCMD, mas deixa editável.
    """
    # Recalcula o total aqui para garantir (pegando do session state se possível ou inputs)
    # Como os inputs de valores não estão em session state com keys fixas simples para soma direta no callback,
    # vamos usar uma lógica simplificada: O app roda, calcula o total, e se o toggle mudar, forçamos o update.
    # Mas para o callback funcionar bem, precisamos dos valores. 
    # TRUQUE: O callback roda antes do resto do script.
    pass 
    # Nota: No Streamlit, fazer isso direto no callback sem todos os valores em session_state é complexo.
    # Vou fazer a lógica de atualização dentro do fluxo principal usando st.session_state para controlar o valor do widget.

# --- Título e Nome do Cliente ---
st.title("Calculadora de Planejamento Patrimonial")
col_nome, col_vazia = st.columns([1, 1])
with col_nome:
    nome_cliente = st.text_input("Nome do Cliente", placeholder="Ex: João da Silva")

st.markdown("---")

# --- Colunas Principais ---
col_patrimonio, col_custos = st.columns([1, 1.2], gap="large")

# ==========================================================
# SEÇÃO 1: PATRIMÔNIO
# ==========================================================
with col_patrimonio:
    st.subheader("1. Levantamento Patrimonial")
    st.caption("Digite os valores e tecle Enter para formatar (R$)")
    
    val_imoveis = st.number_input("Imóveis", min_value=0.0, step=100000.0, format="%.2f", key="v_imoveis")
    val_aplicacoes = st.number_input("Aplicações Financeiras", min_value=0.0, step=50000.0, format="%.2f", key="v_aplicacoes")
    val_veiculos = st.number_input("Veículos", min_value=0.0, step=10000.0, format="%.2f", key="v_veiculos")
    val_empresas = st.number_input("Participação em Empresas", min_value=0.0, step=100000.0, format="%.2f", key="v_empresas")
    val_outros = st.number_input("Outros Bens", min_value=0.0, step=10000.0, format="%.2f", key="v_outros")
    
    st.markdown("### Previdência Privada *")
    col_prev_input, col_prev_check = st.columns([0.7, 0.3])
    with col_prev_input:
        val_previdencia = st.number_input("Saldo em Previdência", min_value=0.0, step=50000.0, format="%.2f", key="v_prev")
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
    
    col_uf, col_pl = st.columns([1, 1])
    with col_uf:
        estados = ["São Paulo (SP)", "Rio de Janeiro (RJ)", "Minas Gerais (MG)", "Outros"]
        estado_selecionado = st.selectbox("Estado Base:", estados)
    
    with col_pl:
        st.write("") 
        st.write("") 
        # Botão PL - Agora usamos uma chave para controlar o estado
        usar_pl = st.toggle("Simular PL n.7/2024 (SP)?", key="toggle_pl")

    # --- LÓGICA INTELIGENTE DE ALÍQUOTA AUTOMÁTICA ---
    # Inicializa o valor da alíquota no session_state se não existir
    if 'aliq_itcmd_input' not in st.session_state:
        st.session_state.aliq_itcmd_input = 4.0

    # Verifica se houve mudança de estado para atualizar o input
    # Se o PL está ativado, calculamos a alíquota sugerida baseada na faixa
    if usar_pl:
        aliquota_sugerida = obter_aliquota_pl_sp_fixa(total_patrimonio)
        # Se o toggle acabou de ser ativado ou o patrimonio mudou, podemos querer atualizar
        # Para simplificar e garantir que atualize:
        # Vamos atualizar o session_state SOMENTE se o valor atual for diferente da sugestão 
        # E se quisermos forçar a automação. 
        # Mas para respeitar a "edição", vamos fazer o seguinte:
        # Se o usuário clicar no toggle, vamos forçar a atualização.
        # Infelizmente detectar o clique exato requer callback, vamos usar a lógica de valor sugerido.
        pass
    else:
        # Se PL desligado, volta pro padrão do estado
        if estado_selecionado == "Minas Gerais (MG)":
            aliquota_sugerida = 5.0
        else:
            aliquota_sugerida = 4.0

    # Lógica de atualização do Widget:
    # Vamos usar um container ou recriar o widget se necessário, mas o melhor é usar o 'value' dinâmico
    # apenas quando o gatilho muda. 
    # Solução Prática:
    # O widget abaixo terá 'value' igual ao session_state se o usuário tiver editado, 
    # ou igual ao sugerido se o usuário tiver acabado de trocar o toggle.
    
    # Para simplificar: Vamos apenas mostrar o aviso e pré-setar o valor.
    # Se usar_pl for True, vamos sugerir o valor da tabela.
    
    val_padrao_itcmd = 4.0
    if usar_pl:
        val_padrao_itcmd = obter_aliquota_pl_sp_fixa(total_patrimonio)
    elif estado_selecionado == "Minas Gerais (MG)":
        val_padrao_itcmd = 5.0
    
    # OBSERVAÇÃO IMPORTANTE: 
    # Streamlit não muda o valor de um number_input já renderizado apenas mudando a variável 'value',
    # a menos que mudemos a 'key'. Mas mudar a key reseta o widget.
    # Vamos usar um truque: Atualizar o session_state manualmente se o toggle mudou.
    if 'ultimo_estado_pl' not in st.session_state:
        st.session_state.ultimo_estado_pl = usar_pl
    
    if st.session_state.ultimo_estado_pl != usar_pl:
        # O toggle mudou! Atualiza o input para o valor sugerido
        st.session_state.aliq_itcmd_input = val_padrao_itcmd
        st.session_state.ultimo_estado_pl = usar_pl
    
    # --- Tabela de Custos Alinhada ---
    st.markdown("#### Detalhamento de Custos")
    
    # Cabeçalho
    c_head1, c_head2, c_head3 = st.columns([3, 1.5, 2])
    c_head1.markdown("**Item**")
    c_head2.markdown("**Alíquota (%)**")
    c_head3.markdown("**Valor (R$)**")

    # Linha 1: ITCMD
    c_itcmd1, c_itcmd2, c_itcmd3 = st.columns([3, 1.5, 2])
    with c_itcmd1:
        st.write("ITCMD (Imposto Estadual)")
    with c_itcmd2:
        # Input vinculado ao session_state para permitir edição e automação
        aliquota_itcmd = st.number_input(
            "Aliq ITCMD", 
            min_value=0.0, max_value=20.0, step=0.5,
            label_visibility="collapsed",
            key="aliq_itcmd_input" # Vincula ao session state
        )
    with c_itcmd3:
        val_itcmd = total_patrimonio * (aliquota_itcmd / 100)
        st.write(f"**{format_currency(val_itcmd)}**")

    # Linha 2: Honorários
    c_hon1, c_hon2, c_hon3 = st.columns([3, 1.5, 2])
    with c_hon1:
        st.write("Honorários Advocatícios")
    with c_hon2:
        aliquota_hon = st.number_input("Aliq Hon", value=6.0, step=0.5, label_visibility="collapsed", key="aliq_hon")
    with c_hon3:
        val_hon = total_patrimonio * (aliquota_hon / 100)
        st.write(f"{format_currency(val_hon)}")

    # Linha 3: Cartório
    c_cart1, c_cart2, c_cart3 = st.columns([3, 1.5, 2])
    with c_cart1:
        st.write("Custos Cartório/Outros")
    with c_cart2:
        aliquota_cart = st.number_input("Aliq Cart", value=2.0, step=0.5, label_visibility="collapsed", key="aliq_cart")
    with c_cart3:
        val_cart = total_patrimonio * (aliquota_cart / 100)
        st.write(f"{format_currency(val_cart)}")

    st.divider()

    # --- Totais ---
    custo_total = val_itcmd + val_hon + val_cart
    percentual_total = (custo_total / total_patrimonio * 100) if total_patrimonio > 0 else 0

    # Box Vermelho
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
    
    # --- TEXTO DE ALERTA DO PL (O que você pediu de volta) ---
    if usar_pl:
        # Comparativo: Valor calculado agora (PL) vs Valor base (4%)
        # Nota: Usamos a aliquota que está no input (que pode ter sido editada) vs 4% fixo base
        custo_base_itcmd = total_patrimonio * 0.04
        delta = val_itcmd - custo_base_itcmd
        
        if delta > 0:
            st.error(f"🚨 IMPACTO DA NOVA LEI: O cliente pagará {format_currency(delta)} A MAIS em impostos se a sucessão ocorrer após a aprovação.")
        elif delta < 0:
             st.info("Neste cenário específico de faixa de valor, a alíquota é menor ou igual à atual.")
        else:
             st.warning("Nesta faixa de valor (até R$ 3M), a alíquota permanece similar (4%), mas atente-se à progressividade futura.")

# ==========================================================
# SEÇÃO 3: GRÁFICO GLOBAL
# ==========================================================
st.write("")
st.subheader("3. Onde você está no mundo?")

aliquota_efetiva_imposto = aliquota_itcmd
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
# SEÇÃO 4: DIAGNÓSTICO PRELIMINAR (COM NOME)
# ==========================================================
st.markdown("### 4. Diagnóstico Preliminar")

saudacao = f"Prezado(a) <b>{nome_cliente}</b>" if nome_cliente else "Prezado(a)"

texto_diagnostico = f"""
<div class="client-box">
    <p class="client-text">
        {saudacao}, com base no levantamento realizado, seu patrimônio total inventariável soma 
        <span class="highlight">{format_currency(total_patrimonio)}</span>.
    </p>
    <p class="client-text">
        No cenário atual simulado, sem um planejamento sucessório eficiente, estima-se que sua família terá que desembolsar 
        cerca de <span class="highlight">{format_currency(custo_total)}</span> ({percentual_total:.1f}%) apenas para ter acesso aos bens. 
        Isso exige alta liquidez imediata no momento mais delicado para a família.
    </p>
    <p class="client-text">
        Observando o cenário global e os projetos de lei em tramitação (ex: PL n.7/2024), 
        há uma tendência clara de aumento da carga tributária. A estruturação antecipada é fundamental para proteção patrimonial.
    </p>
</div>
"""
st.markdown(texto_diagnostico, unsafe_allow_html=True)
