
# app_cloud.py (versão para Streamlit Cloud)
import streamlit as st
import pandas as pd
from datetime import datetime
import os, re

st.set_page_config(page_title="Controle de Chamados - Engenharia", layout="wide")

PALETA = {
    "primaria": "#0A6EB5",
    "secundaria": "#00A6A6",
    "acento": "#FF6B00",
    "fundo": "#F7F9FC",
    "texto": "#222222",
}

# =========================
# HELPERS
# =========================

def safe_rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        try:
            st.experimental_rerun()
        except Exception:
            pass

def clear_query_params():
    try:
        if hasattr(st, "query_params"):
            st.query_params.clear()
        else:
            st.experimental_set_query_params()
    except Exception:
        pass

def kpi(label, value):
    st.metric(label, value if value is not None else "-")

# =========================
# CAMINHO / ABA PADRÃO
# =========================
# No Streamlit Cloud, use um arquivo no repositório.
# Mantenha o mesmo nome quando atualizar no GitHub.
CAMINHO_EXCEL = "BASE_CONTROLE.xlsx"  # coloque este arquivo junto ao app
ABA_PADRAO = "SOLICITAÇÃO DE PAGAMENTO"

# =========================
# COLUNAS
# =========================
COLUNAS_BASE = [
    "EMP","FILIAL","LOJA","CNPJ","COORDENADOR","PROJETO","SERVIÇO","NOTA","FORNECEDOR",
    "VALOR RC","VALOR A PAGAR","VALOR BI","STATUS RC","PEDIDO","CHAMADO","DATA_PGTO_SAP",
    "MIRO","STATUS RESULT1","DATA CRIAÇÃO TICKET","PRAZO"
]

COLUNAS_CHAVE_VAZIAS = [
    "EMP","FILIAL","LOJA","CNPJ","COORDENADOR","PROJETO","SERVIÇO","NOTA","FORNECEDOR",
    "STATUS RC","PEDIDO","CHAMADO","STATUS RESULT1","PRAZO"
]

# =========================
# HELPERS DE DADOS
# =========================

def listar_abas_excel(caminho_excel: str) -> list:
    if not os.path.exists(caminho_excel):
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho_excel}")
    if caminho_excel.lower().endswith(".xlsx"):
        xls = pd.ExcelFile(caminho_excel, engine="openpyxl")
        return xls.sheet_names
    elif caminho_excel.lower().endswith(".xls"):
        xls = pd.ExcelFile(caminho_excel, engine="xlrd")
        return xls.sheet_names
    else:
        return ["(arquivo CSV - sem abas)"]


def to_numeric_safe(x) -> float:
    try:
        s = str(x).strip()
        if s == "" or s.lower() in {"nan", "none"}:
            return float("nan")
        s = re.sub(r"[^\d\.,\-]", "", s)
        if "," in s and "." in s:
            s = s.replace(".", "").replace(",", ".")
        elif "," in s and "." not in s:
            s = s.replace(",", ".")
        return float(s)
    except Exception:
        return float("nan")


def formatar_moeda_val(x) -> str:
    try:
        val = to_numeric_safe(x)
        if pd.notna(val):
            s = f"R${val:,.2f}"
            return s.replace(",", "X").replace(".", ",").replace("X", ".")
        return ""
    except Exception:
        return ""


def formatar_moeda_df(df: pd.DataFrame, cols: list) -> pd.DataFrame:
    f = df.copy()
    for c in cols:
        if c in f.columns:
            f[c] = f[c].apply(formatar_moeda_val)
    return f


def limpar_vazios_texto(df: pd.DataFrame, cols: list) -> pd.DataFrame:
    f = df.copy()
    for c in cols:
        if c in f.columns:
            f[c] = f[c].astype(str).str.strip()
            f[c] = f[c].replace({"": pd.NA, "nan": pd.NA, "None": pd.NA, "NONE": pd.NA})
    return f


def filtrar_linhas_uteis(df: pd.DataFrame, exigir_qualquer_preenchido: list, aplicar_drop_all_empty: bool = True) -> pd.DataFrame:
    f = df.copy()
    if aplicar_drop_all_empty:
        chaves_presentes = [c for c in COLUNAS_CHAVE_VAZIAS if c in f.columns]
        if chaves_presentes:
            f = f.dropna(subset=chaves_presentes, how="all")
    if exigir_qualquer_preenchido:
        campos = [c for c in exigir_qualquer_preenchido if c in f.columns]
        if campos:
            mask = False
            for c in campos:
                mask = (mask | (f[c].notna()))
            f = f[mask]
    return f

@st.cache_data(show_spinner=True)
def carregar_base(caminho_excel: str, aba: str, exigir_qualquer_preenchido: list, aplicar_drop_all_empty: bool) -> pd.DataFrame:
    if not os.path.exists(caminho_excel):
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho_excel}")
    if caminho_excel.lower().endswith(".xlsx"):
        xls = pd.ExcelFile(caminho_excel, engine="openpyxl")
        if aba not in xls.sheet_names:
            raise ValueError(f"Aba '{aba}' não encontrada. Abas disponíveis: {xls.sheet_names}")
        df = pd.read_excel(xls, sheet_name=aba)
    elif caminho_excel.lower().endswith(".xls"):
        xls = pd.ExcelFile(caminho_excel, engine="xlrd")
        if aba not in xls.sheet_names:
            raise ValueError(f"Aba '{aba}' não encontrada. Abas disponíveis: {xls.sheet_names}")
        df = pd.read_excel(xls, sheet_name=aba)
    else:
        df = pd.read_csv(caminho_excel, sep=";", encoding="utf-8")

    df.columns = [str(c).strip().upper() for c in df.columns]
    df = limpar_vazios_texto(df, list(set(COLUNAS_CHAVE_VAZIAS + COLUNAS_BASE)))

    for c in ["DATA_PGTO_SAP","DATA CRIAÇÃO TICKET","DATA CRIAÇÃO RC","DATA CRIAÇÃO TICKET BR"]:
        if c in df.columns:
            try:
                df[c] = pd.to_datetime(df[c], errors="coerce")
            except Exception:
                pass

    df = filtrar_linhas_uteis(df, exigir_qualquer_preenchido, aplicar_drop_all_empty)
    return df


def aplicar_filtros(df: pd.DataFrame, coord_sel, forn_sel, projeto_sel, status_ticket_sel, status_pgto_sel,
                    status_rc_sel, prazo_sel, prazo_texto, loja_texto, pedido_texto, busca_texto):
    f = df.copy()
    if coord_sel and "COORDENADOR" in f.columns:
        f = f[f["COORDENADOR"].isin(coord_sel)]
    if forn_sel and "FORNECEDOR" in f.columns:
        f = f[f["FORNECEDOR"].isin(forn_sel)]
    if projeto_sel and "PROJETO" in f.columns:
        f = f[f["PROJETO"].isin(projeto_sel)]
    if status_rc_sel and "STATUS RC" in f.columns:
        f = f[f["STATUS RC"].isin(status_rc_sel)]
    if status_ticket_sel and "CHAMADO" in f.columns:
        f = f[f["CHAMADO"].isin(status_ticket_sel)]
    if status_pgto_sel and "STATUS RESULT1" in f.columns:
        f = f[f["STATUS RESULT1"].isin(status_pgto_sel)]
    if prazo_sel and "PRAZO" in f.columns:
        f = f[f["PRAZO"].isin(prazo_sel)]
    if prazo_texto and "PRAZO" in f.columns:
        f = f[f["PRAZO"].astype(str).str.contains(prazo_texto, na=False, case=False)]
    if loja_texto and "LOJA" in f.columns:
        f = f[f["LOJA"].astype(str).str.contains(loja_texto, na=False, case=False)]
    if pedido_texto and "PEDIDO" in f.columns:
        f = f[f["PEDIDO"].astype(str).str.contains(pedido_texto, na=False, case=False)]
    if busca_texto:
        q = busca_texto.lower()
        f = f[f.apply(lambda r: q in (" ".join(r.astype(str))).lower(), axis=1)]
    return f


def agregar(df: pd.DataFrame, eixo: str, ref_data_col: str = None, excluir_nulos_eixo: bool = False) -> pd.DataFrame:
    f = df.copy()
    if eixo == "MÊS":
        if ref_data_col not in f.columns:
            raise ValueError(f"A coluna de data '{ref_data_col}' não existe.")
        f["_REF_DATA"] = pd.to_datetime(f[ref_data_col], errors="coerce")
        f["MÊS"] = f["_REF_DATA"].dt.strftime("%Y-%m")
        grupo = "MÊS"
        if excluir_nulos_eixo:
            f = f[f["MÊS"].notna()]
    elif eixo == "PROJETO":
        if "PROJETO" not in f.columns:
            raise ValueError("Coluna 'PROJETO' não encontrada.")
        grupo = "PROJETO"
        if excluir_nulos_eixo:
            f = f[f["PROJETO"].notna() & (f["PROJETO"].astype(str).str.strip() != "")]
    elif eixo == "COORDENADOR":
        if "COORDENADOR" not in f.columns:
            raise ValueError("Coluna 'COORDENADOR' não encontrada.")
        grupo = "COORDENADOR"
        if excluir_nulos_eixo:
            f = f[f["COORDENADOR"].notna() & (f["COORDENADOR"].astype(str).str.strip() != "")]
    else:
        raise ValueError("Eixo inválido. Use 'MÊS', 'PROJETO' ou 'COORDENADOR'.")

    for c in ["VALOR RC","VALOR A PAGAR","VALOR BI"]:
        if c in f.columns:
            f[c] = f[c].apply(to_numeric_safe).fillna(0)

    agreg = f.groupby(grupo, dropna=False).agg({
        "VALOR RC": "sum" if "VALOR RC" in f.columns else "size",
        "VALOR A PAGAR": "sum" if "VALOR A PAGAR" in f.columns else "size",
        "VALOR BI": "sum" if "VALOR BI" in f.columns else "size",
        grupo: "size"
    }).rename(columns={grupo: "QTD_TICKETS"}).reset_index()

    if eixo == "MÊS":
        try:
            agreg["_ORD"] = pd.to_datetime(agreg["MÊS"] + "-01", errors="coerce")
            agreg = agreg.sort_values("_ORD", ascending=True).drop(columns=["_ORD"])
        except Exception:
            agreg = agreg.sort_values("MÊS", ascending=True)
    else:
        agreg = agreg.sort_values("QTD_TICKETS", ascending=False)
    return agreg

# =========================
# UI
# =========================
col_logo, col_titulo, col_search = st.columns([0.8, 4, 2])
with col_logo:
    st.markdown("**PagueMenos**")
with col_titulo:
    st.title("CONTROLE DE CHAMADOS • ENGENHARIA • 2025")
with col_search:
    busca_header = st.text_input("Ex.: coordenador, fornecedor, nota, loja, ped")

c_diag1, c_diag2, c_diag3 = st.columns([2,1,1])
with c_diag1:
    st.info("✨ Use o .BAT. Se atualizar a planilha, substitua o arquivo no GitHub e clique em **Atualizar cache**.")
with c_diag2:
    if st.button("Atualizar cache"):
        st.cache_data.clear()
        safe_rerun()
with c_diag3:
    mostrar_debug = st.checkbox("Debug (ver status da base)")

with st.expander("🧪 Seleção da aba / Saneamento da base"):
    st.write(f"**Arquivo:** `{CAMINHO_EXCEL}`")
    try:
        abas = listar_abas_excel(CAMINHO_EXCEL)
        idx_default = abas.index(ABA_PADRAO) if ABA_PADRAO in abas else 0
        aba_sel = st.selectbox("Aba do Excel", abas, index=idx_default)
    except Exception as e:
        st.error(f"Falha ao listar abas.

**Erro**: {e}")
        aba_sel = ABA_PADRAO

    aplicar_drop_all_empty = st.checkbox("Remover linhas totalmente vazias (recomendado)", value=True)
    exigir_campos = st.multiselect(
        "Exigir que ao menos um destes campos esteja preenchido",
        options=[c for c in COLUNAS_CHAVE_VAZIAS if c != "PRAZO"],
        default=[c for c in ["FORNECEDOR","COORDENADOR","PROJETO","PEDIDO","NOTA"] if c in COLUNAS_CHAVE_VAZIAS]
    )
    st.caption("Evita contar linhas lixo com formatação ou fórmulas sem dados.")

try:
    df = carregar_base(CAMINHO_EXCEL, aba_sel, exigir_campos, aplicar_drop_all_empty)
except Exception as e:
    st.error(f"❌ Não consegui abrir a base.

**Erro**: {e}")
    st.stop()

if mostrar_debug:
    st.success(f"✅ Base lida: **{CAMINHO_EXCEL}**  
 Aba: **{aba_sel}**")
    st.write(f"**Linhas (após saneamento):** {len(df)}  
 **Colunas:** {len(df.columns)}")
    st.write("**Colunas (até 50):**", df.columns.tolist()[:50])
    st.dataframe(df.head(5), use_container_width=True)

if df.empty:
    st.warning("⚠️ A aba selecionada, após saneamento, ficou **vazia**. Ajuste os critérios e clique em **Atualizar cache**.")
    st.stop()

colunas = df.columns.tolist()

st.sidebar.header("Filtros")
coord = st.sidebar.multiselect("Coordenador", sorted(df["COORDENADOR"].dropna().unique().tolist())) if "COORDENADOR" in colunas else []
forn = st.sidebar.multiselect("Fornecedor", sorted(df["FORNECEDOR"].dropna().unique().tolist())) if "FORNECEDOR" in colunas else []
projeto = st.sidebar.multiselect("Projeto", sorted(df["PROJETO"].dropna().unique().tolist())) if "PROJETO" in colunas else []
status_rc = st.sidebar.multiselect("Status RC", sorted(df["STATUS RC"].dropna().unique().tolist())) if "STATUS RC" in colunas else []
status_ticket = st.sidebar.multiselect("Status do Ticket", sorted(df["CHAMADO"].dropna().unique().tolist())) if "CHAMADO" in colunas else []
status_pgto = st.sidebar.multiselect("Status de Pagamento", sorted(df["STATUS RESULT1"].dropna().unique().tolist())) if "STATUS RESULT1" in colunas else []

prazo_opcoes = []
if "PRAZO" in colunas:
    base_prazo = df["PRAZO"].dropna().astype(str)
    sugestao = ["no prazo", "fora do prazo"]
    prazo_opcoes = sorted(set(sugestao + base_prazo.unique().tolist()))

prazo_sel = st.sidebar.multiselect("Prazo (valores exatos)", prazo_opcoes) if prazo_opcoes else []
prazo_texto = st.sidebar.text_input("Prazo (contém texto)", placeholder='Ex.: "13 dias"')
loja = st.sidebar.text_input("Número da Loja (ex.: 1427)")
pedido = st.sidebar.text_input("Número do Pedido")
busca_livre = st.sidebar.text_input("Busca livre (coordenador, fornecedor, nota, etc.)")

c1, c2 = st.sidebar.columns(2)
with c1:
    if st.button("Limpar filtros"):
        loja = ""; pedido = ""; busca_livre = ""; prazo_sel = []; prazo_texto = ""
        clear_query_params()
with c2:
    reset_cols = st.button("Colunas recomendadas")

filtrado = aplicar_filtros(
    df=df,
    coord_sel=coord,
    forn_sel=forn,
    projeto_sel=projeto,
    status_ticket_sel=status_ticket,
    status_pgto_sel=status_pgto,
    status_rc_sel=status_rc,
    prazo_sel=prazo_sel,
    prazo_texto=prazo_texto,
    loja_texto=loja,
    pedido_texto=pedido,
    busca_texto=(busca_header or busca_livre)
)

st.subheader("Indicadores")
kp1, kp2, kp3, kp4 = st.columns(4)

total_reg = len(filtrado)
no_prazo = None; fora_prazo = None
if "PRAZO" in filtrado.columns:
    prazos_norm = filtrado["PRAZO"].astype(str).str.lower()
    no_prazo = prazos_norm.str.startswith("no prazo").sum()
    fora_prazo = prazos_norm.str.startswith("fora do prazo").sum()

aguardando_prog = None
if "STATUS RESULT1" in filtrado.columns:
    aguardando_prog = filtrado["STATUS RESULT1"].astype(str).str.lower().str.contains("programa").sum()

with kp1: kpi("Total de registros", f"{total_reg}")
with kp2: kpi("No Prazo", f"{no_prazo}" if no_prazo is not None else None)
with kp3: kpi("Fora do Prazo", f"{fora_prazo}" if fora_prazo is not None else None)
with kp4: kpi("Aguardando programação", f"{aguardando_prog}" if aguardando_prog is not None else None)

st.divider()
st.subheader("Análises agregadas")
col_a, col_b, col_c, col_d = st.columns(4)
with col_a:
    eixo = st.selectbox("Eixo de análise", ["MÊS", "PROJETO", "COORDENADOR"])
with col_b:
    ref_data_col = st.selectbox(
        "Coluna de referência (para MÊS)",
        options=[c for c in ["DATA_PGTO_SAP","DATA CRIAÇÃO TICKET BR","DATA CRIAÇÃO TICKET","DATA CRIAÇÃO RC"] if c in filtrado.columns] or ["(indisponível)"]
    )
with col_c:
    ordenar_por = st.selectbox("Ordenar por", ["QTD_TICKETS","VALOR A PAGAR","VALOR RC","VALOR BI"])
with col_d:
    excluir_nulos_eixo = st.checkbox("Excluir nulos do gráfico (eixo)")

try:
    agreg = agregar(
        filtrado,
        eixo=eixo,
        ref_data_col=None if eixo != "MÊS" else ref_data_col,
        excluir_nulos_eixo=excluir_nulos_eixo
    )
except Exception as e:
    st.error(f"Erro ao agregar: {e}")
    agreg = pd.DataFrame()

if not agreg.empty and ordenar_por in agreg.columns and eixo != "MÊS":
    agreg = agreg.sort_values(ordenar_por, ascending=False)

agreg_fmt = formatar_moeda_df(agreg, ["VALOR RC","VALOR A PAGAR","VALOR BI"])
st.dataframe(agreg_fmt, use_container_width=True)

try:
    import plotly.express as px
    if not agreg.empty:
        st.plotly_chart(
            px.bar(
                agreg, x=agreg.columns[0], y=ordenar_por, text=ordenar_por, color=agreg.columns[0],
                title=f"{ordenar_por} por {agreg.columns[0]}", height=400
            ), use_container_width=True
        )
        st.plotly_chart(
            px.pie(
                agreg, names=agreg.columns[0], values="QTD_TICKETS",
                title=f"Distribuição de tickets por {agreg.columns[0]}", hole=0.45, height=400
            ), use_container_width=True
        )
except Exception as e:
    st.warning(f"Plotly não está instalado ou houve erro ao renderizar os gráficos. Instale com: pip install plotly

Detalhe: {e}")

st.divider()
st.subheader("Tabela detalhada (filtrada)")
cols_presentes = [c for c in COLUNAS_BASE if c in filtrado.columns]
filtrado_restrito = filtrado[cols_presentes].copy()

for chave in ["DATA_PGTO_SAP","DATA CRIAÇÃO TICKET"]:
    if chave in filtrado_restrito.columns:
        filtrado_restrito = filtrado_restrito.sort_values(by=chave, ascending=True, na_position="last")
        break

filtrado_restrito_fmt = formatar_moeda_df(filtrado_restrito, ["VALOR RC","VALOR A PAGAR","VALOR BI"])

if filtrado_restrito_fmt.empty:
    st.warning("Nenhum registro após aplicação dos filtros. Ajuste os filtros e tente novamente.")
else:
    st.dataframe(filtrado_restrito_fmt, use_container_width=True)

st.download_button(
    label="Baixar resultado (CSV)",
    data=filtrado_restrito.to_csv(index=False, sep=";", encoding="utf-8-sig"),
    file_name=f"controle_chamados_filtrado_{datetime.now().strftime('%Y-%m-%d_%Hh%Mm')}.csv",
    mime="text/csv"
)

col_a1, col_a2 = st.columns([1,3])
with col_a1:
    if st.button("Atualizar"):
        st.cache_data.clear()
        safe_rerun()
with col_a2:
    st.caption("Após substituir a planilha no GitHub, clique em **Atualizar cache** para recarregar os dados.")
