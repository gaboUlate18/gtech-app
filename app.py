import streamlit as st
from pymongo import MongoClient
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import time

# 1. CONEXIÓN A BASE DE DATOS (Con reintentos para evitar errores de red)
MONGO_URL = "mongodb+srv://gtech:Ingenieria2026@g-tech.0p52gdx.mongodb.net/?appName=G-Tech"

@st.cache_resource
def init_connection():
    return MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)

try:
    client = init_connection()
    db = client.GTechDB
    ordenes_col = db.ordenes
    # Test de conexión rápido
    client.admin.command('ping')
except Exception as e:
    st.error("⚠️ No se pudo establecer conexión estable con MongoDB. Verifique su internet.")

# 2. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="G-Tech Engineering System", layout="wide")

# 3. FUNCIONES TÉCNICAS
def obtener_siguiente_orden():
    try:
        todas = list(ordenes_col.find().sort("n_orden", -1).limit(1))
        if todas:
            return str(int(todas[0]["n_orden"]) + 1)
        return "1001"
    except:
        return ""

def generar_pdf_completo(datos):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_fill_color(14, 75, 122)
    pdf.rect(0, 0, 210, 45, 'F')
    pdf.set_font("Arial", 'B', 22); pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 15, "G-TECH ENGINEERING SYSTEM", ln=True, align='C')
    pdf.set_font("Arial", size=12); pdf.cell(0, 10, "REPORTE TÉCNICO DE CALIDAD", ln=True, align='C')
    pdf.ln(35); pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", 'B', 14); pdf.set_fill_color(230, 230, 230)
    pdf.cell(0, 10, f" DETALLES DE LA ORDEN: {datos['n_orden']}", ln=True, fill=True)
    pdf.ln(5); pdf.set_font("Arial", size=11)
    info = [("Cliente:", datos['cliente']), ("Fecha Ingreso:", datos['f_recepcion']), ("Material:", datos['material']), ("Cantidad:", str(datos['cantidad'])), ("Entrega:", datos['entrega'])]
    for label, val in info:
        pdf.set_font("Arial", 'B', 11); pdf.cell(60, 8, label)
        pdf.set_font("Arial", size=11); pdf.cell(0, 8, val, ln=True)
    if datos.get('historial'):
        pdf.ln(10); pdf.set_font("Arial", 'B', 14); pdf.cell(0, 10, " TRAZABILIDAD", ln=True, fill=True)
        for h in datos['historial']:
            pdf.set_font("Arial", size=9)
            pdf.cell(0, 7, f"- {h.get('etapa')}: {h.get('inicio')} a {h.get('fin')} | Nota: {h.get('nota')}", ln=True)
    return pdf.output(dest='S').encode('latin-1')

def limpiar_campos():
    st.session_state["n_orden_form"] = obtener_siguiente_orden()
    st.session_state["cliente_form"] = ""
    st.session_state["material_form"] = ""
    st.session_state["cantidad_form"] = 1

# 4. ESTILO CSS
st.markdown("""
    <style>
    .stApp { background-color: #f4f7f9; }
    h1 { color: #0e4b7a; font-family: 'Segoe UI'; font-weight: 700; text-align: center; }
    .stButton>button { width: 100%; border-radius: 8px; height: 3.5em; background-color: #1a5a96; color: white; font-weight: bold; }
    [data-testid="stForm"] { background-color: white; padding: 30px; border-radius: 15px; border: 1px solid #d3d9de; }
    </style>
    """, unsafe_allow_html=True)

if 'auth' not in st.session_state: st.session_state.auth = False

# --- PANTALLA DE BIENVENIDA ---
if not st.session_state.auth:
    st.write("<br><br><br>", unsafe_allow_html=True)
    st.markdown("<h1>Bienvenido al sistema de G-Tech</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1.2, 1, 1.2])
    with c2:
        if st.button("INGRESAR AL SISTEMA"):
            st.session_state.auth = True
            st.rerun()
else:
    st.markdown("<h1>🛡️ G-TECH ENGINEERING SYSTEM</h1>", unsafe_allow_html=True)
    t1, t2, t3 = st.tabs(["📝 REGISTRO", "⚙️ TRAZABILIDAD", "📊 HISTORIAL"])

    with t1:
        st.markdown("<h3>Nuevo Ingreso de Orden</h3>", unsafe_allow_html=True)
        if "n_orden_form" not in st.session_state: st.session_state["n_orden_form"] = obtener_siguiente_orden()
        with st.form("reg_form", clear_on_submit=False):
            ca, cb = st.columns(2)
            f_recep = ca.date_input("Fecha ingreso", value=datetime.now())
            id_orden = cb.text_input("ID Orden", value=st.session_state["n_orden_form"], key="n_orden_form")
            client_name = ca.text_input("Cliente", key="cliente_form")
            qty = cb.number_input("Cantidad", min_value=1, key="cantidad_form")
            spec = ca.text_input("Material", key="material_form")
            f_limit = cb.date_input("Fecha límite")
            st.markdown("---")
            docs = st.radio("¿Planos aprobados?", ["Sí", "No"], horizontal=True)
            file = st.file_uploader("Adjuntar Plano", type=['pdf', 'jpg', 'png'])
            b1, b2 = st.columns(2)
            save_clicked = b1.form_submit_button("💾 GUARDAR E IMPRIMIR")
            if b2.form_submit_button("🧹 LIMPIAR"):
                limpiar_campos(); st.rerun()

        if save_clicked:
            if docs == "No" or file is None: st.error("❌ Se requiere el plano.")
            elif not id_orden or not client_name: st.warning("⚠️ Datos incompletos.")
            else:
                try:
                    if ordenes_col.find_one({"n_orden": id_orden}):
                        st.error(f"❌ La Orden {id_orden} ya existe.")
                    else:
                        data_master = {"n_orden": id_orden, "cliente": client_name, "f_recepcion": str(f_recep), "material": spec, "cantidad": qty, "entrega": str(f_limit), "etapa": "Diseño", "status": "Pendiente", "historial": []}
                        ordenes_col.insert_one(data_master)
                        st.success(f"✅ Orden {id_orden} registrada correctamente.")
                        pdf_bytes = generar_pdf_completo(data_master)
                        st.download_button("📥 DESCARGAR PDF", data=pdf_bytes, file_name=f"Orden_{id_orden}.pdf", mime="application/pdf")
                        st.session_state["n_orden_form"] = obtener_siguiente_orden()
                except Exception as e:
                    st.error("🔌 Error de conexión temporal. Verifique si la orden se guardó en el historial.")

    with t2:
        st.markdown("<h3>Control de Etapas</h3>", unsafe_allow_html=True)
        try:
            items = list(ordenes_col.find({"status": "Pendiente"}))
            if items:
                with st.form("upd_form"):
                    sel_id = st.selectbox("Orden", [i["n_orden"] for i in items])
                    et_n = st.selectbox("Nueva Etapa", ["Maquinado", "Rectificado", "Ensamble", "Calidad", "Finalizado"])
                    h_i = st.time_input("Inicio"); h_f = st.time_input("Fin")
                    nota = st.text_area("Notas")
                    if st.form_submit_button("ACTUALIZAR"):
                        st_n = "Finalizado" if et_n == "Finalizado" else "Pendiente"
                        ordenes_col.update_one({"n_orden": sel_id}, {"$set": {"etapa": et_n, "status": st_n}, "$push": {"historial": {"etapa": et_n, "inicio": str(h_i), "fin": str(h_f), "nota": nota}}})
                        st.success(f"✅ Orden {sel_id} actualizada.")
            else: st.info("No hay órdenes pendientes.")
        except: st.error("Error de conexión.")

    with t3:
        st.markdown("<h3>Historial General</h3>", unsafe_allow_html=True)
        try:
            df_raw = list(ordenes_col.find())
            if df_raw:
                df = pd.DataFrame(df_raw)
                st.dataframe(df[["n_orden", "cliente", "etapa", "status"]], use_container_width=True)
                sel_rep = st.selectbox("Seleccione orden para PDF completo", df["n_orden"].tolist())
                if st.button("📄 GENERAR REPORTE"):
                    doc = ordenes_col.find_one({"n_orden": sel_rep})
                    st.download_button("📥 DESCARGAR", data=generar_pdf_completo(doc), file_name=f"Reporte_{sel_rep}.pdf", mime="application/pdf")
        except: st.error("Error al cargar historial.")
