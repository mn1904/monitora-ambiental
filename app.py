import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF
import datetime
import requests
import os
from google import genai

st.set_page_config(page_title="Monitora Ambiental", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #F7F9F9; color: #2C3E50; }
    .stButton>button { background-color: #5D7B6F; color: white; border-radius: 6px; border: none; width: 100%; }
    .stButton>button:hover { background-color: #4A6359; }
    </style>
""", unsafe_allow_html=True)

ARQUIVO_DADOS = "banco_ambiental.csv"

def carregar_dados():
    if os.path.exists(ARQUIVO_DADOS):
        return pd.read_csv(ARQUIVO_DADOS)
    df_inicial = pd.DataFrame([
        {"Data": "2026-01-15", "Ano": 2026, "Mes": "01 - Jan", "Cidade": "Umbaúba", "Categoria": "Água", "Parametro": "pH", "Valor": 7.1, "Limite": 9.0, "Status": "Conforme", "Responsavel": "tecnico1"},
        {"Data": "2026-02-15", "Ano": 2026, "Mes": "02 - Fev", "Cidade": "Umbaúba", "Categoria": "Solo", "Parametro": "Chumbo (mg/kg)", "Valor": 85.0, "Limite": 72.0, "Status": "Alerta", "Responsavel": "tecnico2"},
        {"Data": "2025-02-15", "Ano": 2025, "Mes": "02 - Fev", "Cidade": "Umbaúba", "Categoria": "Solo", "Parametro": "Chumbo (mg/kg)", "Valor": 60.0, "Limite": 72.0, "Status": "Conforme", "Responsavel": "admin"},
    ])
    df_inicial.to_csv(ARQUIVO_DADOS, index=False)
    return df_inicial

def salvar_dados(df):
    df.to_csv(ARQUIVO_DADOS, index=False)

if 'df' not in st.session_state:
    st.session_state.df = carregar_dados()

def buscar_clima(cidade):
    try:
        geo = requests.get(f"https://open-meteo.com{cidade}&count=1&language=pt").json()
        if "results" not in geo:
            return None
        lat = geo["results"]["latitude"]
        lon = geo["results"]["longitude"]
        nome_oficial = f"{geo['results']['name']} - {geo['results'].get('admin1', '')}"
        clima = requests.get(f"https://open-meteo.com{lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m").json()["current"]
        return nome_oficial, clima
    except Exception:
        return None

USUARIOS = {
    "admin": {"senha": "123", "nome": "Administrador Geral", "perfil": "Administrador"},
    "tecnico1": {"senha": "123", "nome": "Técnico de Campo 1", "perfil": "Operador"},
    "tecnico2": {"senha": "123", "nome": "Técnico de Campo 2", "perfil": "Operador"}
}

if 'usuario' not in st.session_state:
    st.session_state.usuario = None

if st.session_state.usuario is None:
    st.title("🌿 Monitora Ambiental")
    st.write("Sistema de Monitoramento, Análise e Relatórios de Campo")
    with st.form("login"):
        u = st.text_input("Usuário (digite: admin, tecnico1 ou tecnico2)").strip().lower()
        s = st.text_input("Senha (digite: 123)", type="password").strip()
        if st.form_submit_button("Entrar no Sistema"):
            if u in USUARIOS and USUARIOS[u]["senha"] == s:
                st.session_state.usuario = u
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")
    st.stop()

info = USUARIOS[st.session_state.usuario]

with st.sidebar:
    st.header(f"👤 {info['nome']}")
    st.caption(f"Nível: **{info['perfil']}**")
    if st.button("Sair"):
        st.session_state.usuario = None
        st.rerun()
    st.divider()
    st.subheader("🔑 Ativar IA Real (Opcional)")
    api_key = st.text_input("Cole sua Chave Google Gemini", type="password")

st.title("🌿 Monitora Ambiental")
col_c1, col_c2 = st.columns(2)
cidade_busca = col_c1.text_input("📍 Cidade do Projeto (Clima em Tempo Real)", value="Umbaúba")

dados_clima = buscar_clima(cidade_busca)
if dados_clima:
    nome_loc, c = dados_clima
    st.caption(f"Estação meteorológica próxima a: **{nome_loc}**")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Temperatura", f"{c['temperature_2m']} °C")
    m2.metric("Umidade", f"{c['relative_humidity_2m']}%")
    m3.metric("Chuva Atual", f"{c['precipitation']} mm")
    m4.metric("Vento", f"{c['wind_speed_10m']} km/h")
    
    if c['precipitation'] > 2.0:
        st.warning("⚠️ **Alerta Climático:** Chuva detectada na região. Risco elevado de carreamento de sedimentos e lixiviação de solo.")
    elif c['relative_humidity_2m'] < 35:
        st.warning("⚠️ **Alerta Climático:** Umidade baixa. Risco aumentado de dispersão de material particulado.")
    else:
        st.success("✅ **Condição Climática Estável:** Sem alertas críticos imediatos para operações de campo.")

aba1, aba2, aba3, aba4 = st.tabs(["📋 Nova Coleta", "🤖 Ler PDF/Foto (IA)", "📊 Gráficos", "📄 Planilha & PDF"])

with aba1:
    st.subheader("Registrar Dados Coletados em Campo")
    with st.form("form_coleta"):
        c1, c2 = st.columns(2)
        data_c = c1.date_input("Data da Coleta", datetime.date.today())
        cidade_c = c2.text_input("Município / Local", value=cidade_busca)
        c3, c4 = st.columns(2)
        cat = c3.selectbox("Matriz Ambiental", ["Solo", "Água Superficial/Subterrânea", "Emissões Atmosféricas", "Ruído", "Resíduos"])
        param = c4.text_input("Parâmetro (ex: pH, Turbidez, Chumbo, CO2)")
        c5, c6 = st.columns(2)
        val = c5.number_input("Valor Medido", format="%.2f")
        lim = c6.number_input("Limite Legal (CONAMA/Referência)", format="%.2f")
        
        if st.form_submit_button("💾 Salvar Coleta"):
            if param:
                status = "Alerta" if (lim > 0 and val > lim) else "Conforme"
                nova_linha = pd.DataFrame([{
                    "Data": str(data_c),
                    "Ano": data_c.year,
                    "Mes": data_c.strftime("%m - %b"),
                    "Cidade": cidade_c,
                    "Categoria": cat,
                    "Parametro": param,
                    "Valor": val,
                    "Limite": lim,
                    "Status": status,
                    "Responsavel": st.session_state.usuario
                }])
                st.session_state.df = pd.concat([st.session_state.df, nova_linha], ignore_index=True)
                salvar_dados(st.session_state.df)
                st.success(f"Registro salvo com sucesso! Status: **{status}**")
            else:
                st.error("Digite o nome do parâmetro antes de salvar.")

with aba2:
    st.subheader("Analisar Laudo (PDF) ou Foto de Campo")
    arq = st.file_uploader("Envie PDF ou Imagem", type=["pdf", "png", "jpg", "jpeg"])
    prompt_user = st.text_area("O que você quer que o sistema faça?", value="Extraia os parâmetros e valores deste arquivo, compare com padrões ambientais brasileiros e sugira opções práticas de intervenção.")
    
    if st.button("🚀 Analisar com Inteligência Artificial"):
        if not api_key:
            st.info("💡 Cole sua chave gratuita do Google AI Studio no menu lateral esquerdo para analisar arquivos reais.")
        elif arq is not None:
            with st.spinner("Lendo arquivo e gerando análise..."):
                try:
                    client = genai.Client(api_key=api_key)
                    bytes_arq = arq.getvalue()
                    resposta = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=[
                            prompt_user,
                            genai.types.Part.from_bytes(data=bytes_arq, mime_type=arq.type)
                        ]
                    )
                    st.markdown(resposta.text)
                except Exception as e:
                    st.error(f"Erro ao processar: {e}")
        else:
            st.warning("Envie um arquivo PDF ou foto primeiro.")

with aba3:
    st.subheader("Evolução Mensal e Anual")
    df_atual = st.session_state.df
    filtro = st.selectbox("Filtrar Matriz", ["Todas"] + list(df_atual["Categoria"].unique()))
    df_plot = df_atual if filtro == "Todas" else df_atual[df_atual["Categoria"] == filtro]
    
    fig1 = px.bar(df_plot, x="Mes", y="Valor", color="Status", barmode="group", title="Comparativo Mensal",
                  color_discrete_map={"Conforme": "#5D7B6F", "Alerta": "#D9822B"})
    fig1.update_layout(paper_bgcolor="#F7F9F9", plot_bgcolor="#FFFFFF")
    st.plotly_chart(fig1, use_container_width=True)
    
    fig2 = px.line(df_plot, x="Data", y="Valor", color="Parametro", markers=True, title="Evolução Temporal (Anual)")
    fig2.update_layout(paper_bgcolor="#F7F9F9", plot_bgcolor="#FFFFFF")
    st.plotly_chart(fig2, use_container_width=True)

with aba4:
    st.subheader("Gerenciamento de Planilha e Relatório PDF")
    if info["perfil"] == "Administrador":
        st.caption("Modo Administrador: Você pode editar células diretamente na tabela abaixo.")
        df_editado = st.data_editor(st.session_state.df, num_rows="dynamic", use_container_width=True)
        if st.button("Salvar Alterações da Planilha"):
            st.session_state.df = df_editado
            salvar_dados(df_editado)
            st.success("Planilha atualizada!")
    else:
        st.dataframe(st.session_state.df, use_container_width=True)

    csv = st.session_state.df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Baixar Planilha Excel (CSV)", data=csv, file_name="dados_ambientais.csv", mime="text/csv")

    def gerar_pdf(df_rel):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_fill_color(247, 249, 249)
        pdf.rect(0, 0, 210, 297, 'F')
        pdf.set_font("Arial", "B", 14)
        pdf.set_text_color(44, 62, 80)
        pdf.cell(0, 10, "RELATORIO DE MONITORAMENTO AMBIENTAL", ln=True, align="C")
        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 8, f"Data: {datetime.date.today()} | Emitido por: {info['nome']}", ln=True, align="C")
        pdf.ln(6)
        for _, r in df_rel.iterrows():
          txt = f"{r['Data']} | {r['Cidade']} | {r['Categoria']} - {r['Parametro']}: {r['Valor']} (Lim: {r['Limite']}) [{r['Status']}]"
          pdf.cell(0, 8, txt.encode('latin-1', 'replace').decode('latin-1'), ln=True)
        return pdf.output(dest="S").encode("latin-1")

    if st.button("📄 Gerar Relatório PDF"):
        pdf_pronto = gerar_pdf(st.session_state.df)
        st.download_button("⬇️ Baixar PDF Agora", data=pdf_pronto, file_name="Relatorio_Monitora_Ambiental.pdf", mime="application/pdf")
