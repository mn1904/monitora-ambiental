import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF
import datetime
import requests
import os
from google import genai

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Monitora Ambiental",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILO MINIMALISTA & PALETA AMBIENTAL NEUTRA ---
st.markdown("""
    <style>
    @import url('https://googleapis.com');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: #2B302C;
    }
    .stApp {
        background-color: #F4F6F4;
    }
    section[data-testid="stSidebar"] {
        background-color: #EBF0EC;
        border-right: 1px solid #DCE3DE;
    }
    h1, h2, h3 {
        color: #243B2A !important;
        font-weight: 600 !important;
        letter-spacing: -0.02em;
    }
    div[data-testid="stMetric"] {
        background-color: #FFFFFF;
        border: 1px solid #E2E8E4;
        padding: 16px 20px;
        border-radius: 12px;
        box-shadow: 0 2px 6px rgba(36, 59, 42, 0.04);
    }
    div[data-testid="stMetricLabel"] {
        color: #5C6B60 !important;
        font-size: 0.85rem !important;
        font-weight: 500 !important;
    }
    div[data-testid="stMetricValue"] {
        color: #243B2A !important;
        font-size: 1.55rem !important;
        font-weight: 700 !important;
    }
    div[data-testid="stForm"] {
        background-color: #FFFFFF;
        border: 1px solid #E2E8E4;
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 2px 8px rgba(36, 59, 42, 0.03);
    }
    .stButton>button, .stDownloadButton>button {
        background-color: #3A5A40 !important;
        color: #FFFFFF !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 0.55rem 1.2rem !important;
        font-weight: 500 !important;
        transition: all 0.2s ease;
    }
    .stButton>button:hover, .stDownloadButton>button:hover {
        background-color: #2D4732 !important;
        box-shadow: 0 3px 8px rgba(58, 90, 64, 0.2);
    }
    button[data-baseweb="tab"] {
        font-weight: 500 !important;
        color: #5C6B60 !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #3A5A40 !important;
        border-bottom-color: #3A5A40 !important;
    }
    .header-box {
        background: linear-gradient(135deg, #FFFFFF 0%, #EBF0EC 100%);
        border: 1px solid #DCE3DE;
        border-radius: 14px;
        padding: 20px 26px;
        margin-bottom: 20px;
    }
    .header-title {
        font-size: 1.75rem;
        font-weight: 700;
        color: #243B2A;
        margin: 0;
    }
    .header-sub {
        font-size: 0.92rem;
        color: #5C6B60;
        margin-top: 4px;
    }
    .lgpd-note {
        font-size: 0.78rem;
        color: #5C6B60;
        text-align: center;
        margin-top: 12px;
        line-height: 1.4;
    }
    </style>
""", unsafe_allow_html=True)

# --- NORMAS AMBIENTAIS OFICIAIS DE REFERÊNCIA ---
NORMAS_AMBIENTAIS = {
    "CONAMA 357/2005 (Águas Doces - Classe 2)": "pH: 6.0 a 9.0 | Turbidez: até 100 UNT | OD: >= 5.0 mg/L",
    "CONAMA 430/2011 (Lançamento de Efluentes)": "pH: 5.0 a 9.0 | Temperatura: < 40°C | Óleos/Graxas: <= 20 mg/L",
    "CONAMA 420/2009 (Qualidade do Solo - Prevenção)": "Chumbo: 72 mg/kg | Cádmio: 1.3 mg/kg | Cobre: 60 mg/kg",
    "CONAMA 491/2018 (Qualidade do Ar / Emissões)": "MP10: 50 µg/m³ (anual) / 120 µg/m³ (24h) | MP2.5: 25 µg/m³",
    "CONAMA 001/1990 / NBR 10151 (Ruído Ambiental)": "Área Residencial: 55 dB (diurno) / 50 dB (noturno)",
    "Lei 12.305/2010 (PNRS - Resíduos Sólidos)": "Classificação NBR 10004 e destinação ambientalmente adequada",
    "Parâmetro Customizado / Pesquisa Específica": "Definido pelo pesquisador ou condicionante específica"
}

# --- BANCO DE DADOS ---
ARQUIVO_DADOS = "banco_monitora_prod.csv"

def carregar_dados():
    if os.path.exists(ARQUIVO_DADOS):
        return pd.read_csv(ARQUIVO_DADOS)
    df_inicial = pd.DataFrame([
        {
            "Projeto": "Pesquisa - Bacia Hidrográfica",
            "Modo": "Pesquisa",
            "Data": "2026-11-26", "Ano": 2026, "Mes": "11 - Nov",
            "Cidade": "Umbaúba", "Ponto": "P01 - Nascente",
            "Categoria": "Água Superficial/Subterrânea",
            "Norma": "CONAMA 357/2005 (Águas Doces - Classe 2)",
            "Parametro": "Turbidez (UNT)", "Valor": 48.0, "Limite": 100.0,
            "Status": "Conforme", "Responsavel": "tecnico1"
        },
        {
            "Projeto": "Cliente - Área Industrial",
            "Modo": "Clientes",
            "Data": "2026-11-26", "Ano": 2026, "Mes": "11 - Nov",
            "Cidade": "Umbaúba", "Ponto": "P02 - Solo Perímetro",
            "Categoria": "Solo",
            "Norma": "CONAMA 420/2009 (Qualidade do Solo - Prevenção)",
            "Parametro": "Chumbo (mg/kg)", "Valor": 85.0, "Limite": 72.0,
            "Status": "Alerta", "Responsavel": "tecnico2"
        },
    ])
    df_inicial.to_csv(ARQUIVO_DADOS, index=False)
    return df_inicial

def salvar_dados(df):
    df.to_csv(ARQUIVO_DADOS, index=False)

if 'df' not in st.session_state:
    st.session_state.df = carregar_dados()

# --- CLIMA EM TEMPO REAL ---
def buscar_clima(cidade):
    try:
        geo = requests.get(
            f"https://open-meteo.com{cidade}&count=1&language=pt",
            timeout=5
        ).json()
        if "results" not in geo:
            return None
        lat = geo["results"][0]["latitude"]
        lon = geo["results"][0]["longitude"]
        nome_oficial = f"{geo['results'][0]['name']} - {geo['results'][0].get('admin1', '')}"
        clima = requests.get(
            f"https://open-meteo.com{lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m",
            timeout=5
        ).json()["current"]
        return nome_oficial, clima
    except Exception:
        return None

# --- GERADOR AUTOMÁTICO DE MATRIZ DE INTERVENÇÃO ---
def gerar_matriz_intervencao(df_alertas):
    intervencoes = []
    for _, row in df_alertas.iterrows():
        cat = str(row["Categoria"])
        param = row["Parametro"]
        val = row["Valor"]
        lim = row["Limite"]
        norma = row["Norma"]

        if "Solo" in cat:
            acao_imediata = "Isolamento da área e cobertura impermeável contra chuvas."
            medida_corretiva = "Avaliar fitorremediação, estabilização química ou remoção controlada de camada superficial."
            prazo = "Imediato (até 7 dias)"
        elif "Água" in cat:
            acao_imediata = "Identificar fonte de aporte/lançamento a montante e suspender captação direta."
            medida_corretiva = "Instalar barreiras de contenção de sedimentos, recompor mata ciliar e ampliar frequência de coleta."
            prazo = "Urgente (até 48h)"
        elif "Emissões" in cat:
            acao_imediata = "Inspecionar filtros/lavadores de gases e umectação de vias internas."
            medida_corretiva = "Manutenção preventiva de exaustores, ajuste de queima e cortina arbórea perimetral."
            prazo = "Curto prazo (até 15 dias)"
        elif "Ruído" in cat:
            acao_imediata = "Restringir operação de equipamentos críticos ao horário diurno."
            medida_corretiva = "Instalar enclausuramento acústico, silenciadores e barreiras de atenuação."
            prazo = "Curto prazo (até 15 dias)"
        else:
            acao_imediata = "Segregação imediata e acondicionamento em área impermeabilizada."
            medida_corretiva = "Destinação via MTR para receptor licenciado conforme PNRS."
            prazo = "Imediato (até 5 dias)"

        intervencoes.append({
            "Modo": row["Modo"],
            "Projeto": row["Projeto"],
            "Ponto": row["Ponto"],
            "Matriz / Parâmetro": f"{cat} ({param})",
            "Medido vs Limite": f"{val} / {lim}",
            "Base Legal": norma,
            "Ação Imediata": acao_imediata,
            "Medida Corretiva Estrutural": medida_corretiva,
            "Prazo Recomendado": prazo
        })
    return pd.DataFrame(intervencoes)

# --- CONTROLE DE ACESSO ---
USUARIOS = {
    "vanianazac": {"senha": "190427m.", "nome": "Vânia Nazac", "perfil": "Administrador"},
    "vânianazac": {"senha": "190427m.", "nome": "Vânia Nazac", "perfil": "Administrador"},
    "tecnico1": {"senha": "Campo1@2026", "nome": "Pesquisador / Técnico 1", "perfil": "Operador"},
    "tecnico2": {"senha": "Campo2@2026", "nome": "Pesquisador / Técnico 2", "perfil": "Operador"}
}

if 'usuario' not in st.session_state:
    st.session_state.usuario = None

if st.session_state.usuario is None:
    col_l1, col_l2, col_l3 = st.columns([1, 1.4, 1])
    with col_l2:
        st.markdown("""
            <div class="header-box" style="text-align:center; margin-top: 30px;">
                <p class="header-title">🌿 Monitora Ambiental</p>
                <p class="header-sub">Plataforma de Pesquisa, Clientes e Conformidade Ambiental</p>
            </div>
        """, unsafe_allow_html=True)
        with st.form("login"):
            u = st.text_input("Usuário", placeholder="Digite seu usuário").strip().lower()
            s = st.text_input("Senha", type="password", placeholder="Digite sua senha").strip()
            aceite_lgpd = st.checkbox("Concordo com a política de sigilo técnico e tratamento de dados (LGPD).", value=True)
            if st.form_submit_button("Acessar Plataforma", use_container_width=True):
                if not aceite_lgpd:
                    st.warning("É necessário concordar com o termo de sigilo e LGPD para acessar.")
                elif u in USUARIOS and USUARIOS[u]["senha"] == s:
                    st.session_state.usuario = u
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")
        st.markdown("""
            <p class="lgpd-note">
                🔒 Ambiente restrito. Os dados coletados e laudos anexados são tratados em conformidade com a Lei Geral de Proteção de Dados (Lei nº 13.709/2018).
            </p>
        """, unsafe_allow_html=True)
    st.stop()

info = USUARIOS[st.session_state.usuario]

# --- BARRA LATERAL ---
with st.sidebar:
    st.markdown(f"### 👤 {info['nome']}")
    st.caption(f"Nível: **{info['perfil']}**")
    if st.button("Encerrar Sessão", use_container_width=True):
        st.session_state.usuario = None
        st.rerun()

    st.divider()
    st.markdown("#### 🗂️ Modos de Projetos")
    modo_ativo = st.radio("Selecione o modo:", ["Todos", "Pesquisa", "Clientes"], horizontal=True)

    df_por_modo = st.session_state.df if modo_ativo == "Todos" else st.session_state.df[st.session_state.df["Modo"] == modo_ativo]
    projetos_existentes = ["Todos os Projetos"] + sorted(list(df_por_modo["Projeto"].dropna().unique()))
    projeto_ativo = st.selectbox("Filtrar Projeto Específico:", projetos_existentes)

    st.divider()
    st.markdown("#### 🔑 Inteligência Artificial")
    api_key = st.text_input("Chave Google Gemini (Opcional)", type="password", placeholder="Cole sua API Key aqui")
    st.caption("Ativa leitura de laudos PDF/fotos e atualização normativa em tempo real.")

# --- CABEÇALHO PRINCIPAL ---
st.markdown(f"""
    <div class="header-box">
        <p class="header-title">🌿 Monitora Ambiental</p>
        <p class="header-sub">Modo: <b>{modo_ativo}</b> &nbsp;|&nbsp; Escopo Ativo: <b>{projeto_ativo}</b></p>
    </div>
""", unsafe_allow_html=True)

# --- PAINEL DE CLIMA ---
col_c1, col_c2 = st.columns([2, 3])
cidade_busca = col_c1.text_input("📍 Município do Projeto", value="Umbaúba")

dados_clima = buscar_clima(cidade_busca)
clima_resumo_texto = f"Município: {cidade_busca}"
if dados_clima:
    nome_loc, c = dados_clima
    clima_resumo_texto = f"{nome_loc} | Temp: {c['temperature_2m']}°C | Umidade: {c['relative_humidity_2m']}% | Chuva: {c['precipitation']}mm | Vento: {c['wind_speed_10m']}km/h"
    col_c2.markdown(f"<div style='padding-top: 32px; color:#5C6B60; font-size:0.9rem;'>Estação de referência: <b>{nome_loc}</b></div>", unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Temperatura", f"{c['temperature_2m']} °C")
    m2.metric("Umidade Relativa", f"{c['relative_humidity_2m']}%")
    m3.metric("Precipitação", f"{c['precipitation']} mm")
    m4.metric("Velocidade do Vento", f"{c['wind_speed_10m']} km/h")

    if c['precipitation'] > 2.0:
        st.warning("⚠️ **Alerta Climático:** Precipitação ativa. Risco de carreamento de sedimentos e lixiviação em áreas de solo exposto.")
    elif c['relative_humidity_2m'] < 35:
        st.warning("⚠️ **Alerta Climático:** Umidade baixa. Risco elevado de dispersão de material particulado e poeira.")
    else:
        st.success("✅ **Condição Climática Estável:** Condições favoráveis para amostragem e monitoramento em campo.")

st.write("")

# Filtragem global por modo e projeto
df_filtrado_proj = df_por_modo if projeto_ativo == "Todos os Projetos" else df_por_modo[df_por_modo["Projeto"] == projeto_ativo]

# --- ABAS DO SISTEMA ---
aba1, aba2, aba3, aba4, aba5 = st.tabs([
    "📋 Coleta de Campo",
    "🛡️ Matriz de Intervenção",
    "🤖 IA & Atualidade Legal",
    "📊 Evolução & Gráficos",
    "📄 Planilhas & Relatório PDF"
])

# ABA 1: COLETA DE CAMPO
with aba1:
    st.subheader("Novo Registro de Monitoramento")
    with st.form("form_coleta"):
        p1, p2 = st.columns([2, 1])
        nome_projeto = p1.text_input("Nome do Projeto", value="Pesquisa - Bacia Hidrográfica" if projeto_ativo == "Todos os Projetos" else projeto_ativo)
        modo_coleta = p2.selectbox("Modo de Projeto", ["Pesquisa", "Clientes"], index=0 if modo_ativo != "Clientes" else 1)

        c1, c2, c3 = st.columns(3)
        data_c = c1.date_input("Data da Coleta", datetime.date.today())
        cidade_c = c2.text_input("Município", value=cidade_busca)
        ponto_c = c3.text_input("Ponto / Coordenada", placeholder="Ex: P01 - Jusante / Lat -11.38")

        c4, c5 = st.columns(2)
        cat = c4.selectbox("Matriz Ambiental", ["Solo", "Água Superficial/Subterrânea", "Emissões Atmosféricas", "Ruído", "Resíduos"])
        norma_escolhida = c5.selectbox("Norma / Direito Ambiental de Referência", list(NORMAS_AMBIENTAIS.keys()))

        st.caption(f"📌 **Referência rápida da norma:** {NORMAS_AMBIENTAIS[norma_escolhida]}")

        c6, c7, c8 = st.columns(3)
        param = c6.text_input("Parâmetro Analisado", placeholder="Ex: pH, Turbidez, Chumbo, MP10")
        val = c7.number_input("Valor Medido", format="%.2f")
        lim = c8.number_input("Limite Legal da Norma", format="%.2f")

        if st.form_submit_button("💾 Salvar Registro de Campo"):
            if param and nome_projeto:
                status = "Alerta" if (lim > 0 and val > lim) else "Conforme"
                nova_linha = pd.DataFrame([{
                    "Projeto": nome_projeto,
                    "Modo": modo_coleta,
                    "Data": str(data_c),
                    "Ano": data_c.year,
                    "Mes": data_c.strftime("%m - %b"),
                    "Cidade": cidade_c,
                    "Ponto": ponto_c if ponto_c else "Ponto Geral",
                    "Categoria": cat,
                    "Norma": norma_escolhida,
                    "Parametro": param,
                    "Valor": val,
                    "Limite": lim,
                    "Status": status,
                    "Responsavel": st.session_state.usuario
                }])
                st.session_state.df = pd.concat([st.session_state.df, nova_linha], ignore_index=True)
                salvar_dados(st.session_state.df)
                st.success(f"Coleta salva em **{modo_coleta}**! Classificação segundo **{norma_escolhida}**: **{status}**")
            else:
                st.error("Preencha o nome do projeto e o parâmetro analisado.")

# ABA 2: MATRIZ DE INTERVENÇÃO TÉCNICA
with aba2:
    st.subheader("Matriz de Intervenção e Plano de Ação Ambiental")
    st.write("Geração automática de medidas corretivas com base nos parâmetros em não conformidade e na legislação selecionada.")

    df_alertas = df_filtrado_proj[df_filtrado_proj["Status"] == "Alerta"]

    if df_alertas.empty:
        st.success("✅ **Nenhuma não conformidade detectada** neste escopo até o momento. Todos os parâmetros estão dentro dos limites legais.")
    else:
        st.warning(f"⚠️ Foram identificados **{len(df_alertas)} ponto(s) em Alerta** que exigem intervenção:")
        df_matriz = gerar_matriz_intervencao(df_alertas)
        st.dataframe(df_matriz, use_container_width=True, hide_index=True)

        csv_matriz = df_matriz.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Baixar Matriz de Intervenção (CSV)", data=csv_matriz, file_name="matriz_intervencao_ambiental.csv", mime="text/csv")

# ABA 3: IA, LEITURA DE LAUDOS & ATUALIDADE AMBIENTAL
with aba3:
    st.subheader("Leitura de Laudos (PDF/Foto) & Atualização Normativa com IA")
    col_ia1, col_ia2 = st.columns(2)
    norma_ia = col_ia1.selectbox("Legislação Base para Auditoria", list(NORMAS_AMBIENTAIS.keys()), key="norma_ia")
    foco_ia = col_ia2.selectbox("Tipo de Saída Desejada", [
        "Extrair dados do laudo + Gerar Matriz de Intervenção",
        "Verificar atualizações recentes da legislação e jurisprudência ambiental",
        "Elaborar parecer técnico para Pesquisa / Clientes"
    ])

    arq = st.file_uploader("Anexe laudo laboratorial (PDF) ou foto de vistoria em campo (opcional)", type=["pdf", "png", "jpg", "jpeg"])
    prompt_user = st.text_area(
        "Comando técnico para o sistema",
        value=f"Atue como especialista em Direito e Engenharia Ambiental no Brasil. Com base na norma '{norma_ia}' e nas diretrizes ambientais atuais, realize: {foco_ia}. Apresente os resultados em formato estruturado com tabela de intervenção."
    )

    if st.button("🚀 Executar Análise Técnica com IA"):
        if not api_key:
            st.info("💡 Cole sua chave gratuita do Google AI Studio na barra lateral esquerda para ativar a leitura de arquivos e consultas normativas.")
        else:
            with st.spinner("Processando parâmetros, legislação e recomendações..."):
                try:
                    client = genai.Client(api_key=api_key)
                    conteudos = [prompt_user]
                    if arq is not None:
                        conteudos.append(genai.types.Part.from_bytes(data=arq.getvalue(), mime_type=arq.type))
                    resposta = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=conteudos
                    )
                    st.markdown(resposta.text)
                except Exception as e:
                    st.error(f"Erro ao processar solicitação: {e}")

# ABA 4: GRÁFICOS COMPARATIVOS
with aba4:
    st.subheader("Evolução Temporal e Comparativo Mensal/Anual")
    filtro_cat = st.selectbox("Filtrar por Matriz Ambiental", ["Todas"] + list(df_filtrado_proj["Categoria"].dropna().unique()))
    df_plot = df_filtrado_proj if filtro_cat == "Todas" else df_filtrado_proj[df_filtrado_proj["Categoria"] == filtro_cat]

    if df_plot.empty:
        st.info("Sem dados suficientes para gerar gráficos neste filtro.")
    else:
        c_g1, c_g2 = st.columns(2)
        fig1 = px.bar(
            df_plot, x="Mes", y="Valor", color="Status", barmode="group",
            title="Comparativo Mensal por Conformidade",
            color_discrete_map={"Conforme": "#3A5A40", "Alerta": "#C87D32"}
        )
        fig1.update_layout(paper_bgcolor="#FFFFFF", plot_bgcolor="#F9FBF9", font_color="#2B302C")
        c_g1.plotly_chart(fig1, use_container_width=True)

        fig2 = px.line(
            fig2 = px.line(
            df_plot, x="Data", y="Valor", color="Parametro", markers=True,
            title="Evolução Histórica dos Parâmetros",
            color_discrete_sequence=["#3A5A40", "#588157", "#A3B18A", "#C87D32"]
        )
        fig2.update_layout(paper_bgcolor="#FFFFFF", plot_bgcolor="#F9FBF9", font_color="#2B302C")
        c_g2.plotly_chart(fig2, use_container_width=True)

# ABA 5: PLANILHAS, BACKUP E RELATÓRIO PDF PROFISSIONAL
with aba5:
    st.subheader("Base de Dados e Emissão de Relatório Técnico PDF")
    if info["perfil"] == "Administrador":
        st.caption("Modo Administrador: você pode editar células diretamente na planilha abaixo.")
        df_editado = st.data_editor(st.session_state.df, num_rows="dynamic", use_container_width=True)
        if st.button("Salvar Alterações na Planilha"):
            st.session_state.df = df_editado
            salvar_dados(df_editado)
            st.success("Base de dados atualizada com sucesso!")
    else:
        st.dataframe(df_filtrado_proj, use_container_width=True)

    col_b1, col_b2 = st.columns(2)
    csv = df_filtrado_proj.to_csv(index=False).encode('utf-8')
    col_b1.download_button("📥 Baixar Planilha / Backup (CSV)", data=csv, file_name="monitora_ambiental_backup.csv", mime="text/csv")

    def gerar_pdf_completo(df_rel, clima_txt):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_fill_color(244, 246, 244)
        pdf.rect(0, 0, 210, 297, 'F')

        pdf.set_fill_color(58, 90, 64)
        pdf.rect(0, 0, 210, 28, 'F')
        pdf.set_font("Arial", "B", 14)
        pdf.set_text_color(255, 255, 255)
        pdf.set_y(8)
        pdf.cell(0, 10, "MONITORA AMBIENTAL - RELATORIO TECNICO", ln=True, align="C")

        pdf.set_y(34)
        pdf.set_font("Arial", "", 9)
        pdf.set_text_color(92, 107, 96)
        cabecalho_info = f"Emissao: {datetime.date.today()} | Responsavel: {info['nome']} | Modo: {modo_ativo} | Projeto: {projeto_ativo}"
        pdf.cell(0, 6, cabecalho_info.encode('latin-1', 'replace').decode('latin-1'), ln=True, align="C")
        pdf.cell(0, 6, f"Condicoes Climaticas: {clima_txt}".encode('latin-1', 'replace').decode('latin-1'), ln=True, align="C")
        pdf.ln(6)

        pdf.set_font("Arial", "B", 11)
        pdf.set_text_color(36, 59, 42)
        pdf.cell(0, 8, "1. RESULTADOS ANALITICOS E CONFORMIDADE LEGAL", ln=True)
        pdf.set_font("Arial", "", 9)
        pdf.set_text_color(43, 48, 44)

        for _, r in df_rel.iterrows():
            linha = f"[{r['Data']}] ({r['Modo']}) {r['Ponto']} | {r['Categoria']} - {r['Parametro']}: {r['Valor']} (Lim: {r['Limite']}) -> {r['Status']} | Ref: {r['Norma']}"
            pdf.multi_cell(0, 6, linha.encode('latin-1', 'replace').decode('latin-1'))
            pdf.ln(1)

        df_al = df_rel[df_rel["Status"] == "Alerta"]
        pdf.ln(4)
        pdf.set_font("Arial", "B", 11)
        pdf.set_text_color(36, 59, 42)
        pdf.cell(0, 8, "2. MATRIZ DE INTERVENCAO RECOMENDADA", ln=True)
        pdf.set_font("Arial", "", 9)
        pdf.set_text_color(43, 48, 44)

        if df_al.empty:
            pdf.cell(0, 7, "Nenhuma intervencao corretiva necessaria. Parametros conformes.", ln=True)
        else:
            df_mat = gerar_matriz_intervencao(df_al)
            for _, m in df_mat.iterrows():
                bloco = (
                    f"Ponto: {m['Ponto']} | {m['Matriz / Parâmetro']} ({m['Medido vs Limite']}) - {m['Base Legal']}\n"
                    f"  - Acao Imediata: {m['Ação Imediata']}\n"
                    f"  - Medida Corretiva: {m['Medida Corretiva Estrutural']} (Prazo: {m['Prazo Recomendado']})"
                )
                pdf.multi_cell(0, 6, bloco.encode('latin-1', 'replace').decode('latin-1'))
                pdf.ln(2)

        return pdf.output(dest="S").encode("latin-1")

    if col_b2.button("📄 Gerar Relatório Técnico em PDF"):
        pdf_pronto = gerar_pdf_completo(df_filtrado_proj, clima_resumo_texto)
        st.download_button("⬇️ Baixar Relatório PDF Agora", data=pdf_pronto, file_name="Relatorio_Tecnico_Monitora_Ambiental.pdf", mime="application/pdf")

    st.divider()
    with st.expander("🔄 Restaurar Backup de Dados (CSV)"):
        st.caption("Ao final do dia de testes, baixe sempre a planilha acima. Se precisar restaurar seus dados depois, envie o arquivo CSV aqui:")
        arq_backup = st.file_uploader("Selecionar arquivo de backup (.csv)", type=["csv"])
        if arq_backup is not None and st.button("Restaurar Dados do Arquivo"):
            df_restaurado = pd.read_csv(arq_backup)
            st.session_state.df = df_restaurado
            salvar_dados(df_restaurado)
            st.success("Backup restaurado com sucesso!")
            st.rerun()
