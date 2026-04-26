import streamlit as st
from pymongo import MongoClient
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import time

# --- 1. CONFIGURACIÓN Y CONEXIÓN ---
MONGO_URL = "mongodb+srv://gtech:Ingenieria2026@g-tech.0p52gdx.mongodb.net/?appName=G-Tech"

@st.cache_resource
def init_connection():
    # Aumentamos el tiempo de espera para evitar el "Error al cargar datos"
    return MongoClient(MONGO_URL, serverSelectionTimeoutMS=10000)

try:
    client = init_connection()
    db = client.GTechDB
    ordenes_col = db.ordenes
    # Verificación de conexión activa
    client.admin.command('ping')
except:
    st.error("⚠️ Error crítico: No se pudo conectar con MongoDB Atlas. Revisa tu conexión.")

# --- 2. LÓGICA DE PROCESOS (BACKEND) ---

def obtener_siguiente_orden():
    try:
        # Buscamos el valor numérico más alto para evitar repeticiones
        ultimo = list(ordenes_col.find().sort("n_orden", -1).limit(1))
        if ultimo:
            return str(int(ultimo[0]["n_orden"]) + 1)
        return "1001"
    except:
        return "1001"

def generar_pdf_reporte(datos):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_fill_color(14, 75, 122)
    pdf.rect(0, 0, 210, 45, 'F')
    pdf.set_font("Arial", 'B', 24); pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 15, "G-TECH ENGINEERING SYSTEM", ln=True, align='C')
    pdf.set_font("Arial", size=12); pdf.cell(0, 10, "REPORTE TÉCNICO DE CONTROL DE PROCESOS", ln=True, align='C')
    pdf.ln(35); pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", 'B', 14); pdf.set_fill_color(235, 235, 235)
    pdf.cell(0, 10, f"  DETALLES DE LA ORDEN: {datos['n_orden']}", ln=True, fill=True)
    pdf.ln(5); pdf.set_font("Arial", size=11)
    
    tabla = [
        ("Cliente:", datos['cliente']), ("Fecha Recepción:", datos['f_recepcion']),
        ("Material:", datos['material']), ("Cantidad:", str(datos['cantidad'])),
        ("Entrega:", datos['entrega']), ("Etapa:", datos.get('etapa', 'Registro'))
    ]
    for etiqueta, valor in tabla:
        pdf.set_font("Arial", 'B', 11); pdf.cell(60, 8, etiqueta)
        pdf.set_font("Arial", size=11); pdf.cell(0, 8, valor, ln=True)
    
    if datos.get('historial'):
        pdf.ln(10); pdf.set_font("Arial", 'B', 14); pdf.cell(0, 10, "  TRAZABILIDAD", ln=True, fill=True)
        for h in datos['historial']:
            pdf.set_font("Arial", 'B', 10); pdf.cell(0, 7, f"• {h['etapa']} | {h['inicio']} - {h['fin']}", ln=True)
            pdf.set_font("Arial", 'I', 9); pdf.cell(0, 7, f"  Nota: {h['nota']}", ln=True)
    
    return pdf.output(dest='S').encode('latin-1')

def reset_completo():
    for key in list(st.session_state.keys()):
        if "form_" in key:
            del st.session_state[key]
    st.session_state.registro_ok = False
    st.session_state.id_proxima = obtener_siguiente_orden()

# --- 3. UI Y ESTILOS ---
st.set_page_config(page_title="G-Tech Engineering", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f0f2f6; }
    .main-title { color: #0e4b7a; text-align: center; font-weight: 800; font-size: 3rem; margin-bottom: 40px; }
    div[data-testid="stForm"] { background-color: white; padding: 40px; border-radius: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); border: none; }
    .stTabs [aria-selected="true"] { background-color: #0e4b7a !important; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

if 'auth' not in st.session_state: st.session_state.auth = False
if 'id_proxima' not in st.session_state: st.session_state.id_proxima = obtener_siguiente_orden()
if 'registro_ok' not in st.session_state: st.session_state.registro_ok = False

# --- PANTALLAS ---

if not st.session_state.auth:
    st.write("<br><br><br><br>", unsafe_allow_html=True)
    st.markdown("<h1 class='main-title'>G-TECH ENGINEERING</h1>", unsafe_allow_html=True)
    # Se eliminó el subtítulo solicitado
    _, col_acceso, _ = st.columns([1, 1, 1])
    if col_acceso.button("🔓 INGRESAR AL PANEL"):
        st.session_state.auth = True
        st.rerun()

else:
    st.markdown("<h1 class='main-title'>🛡️ Panel de Control</h1>", unsafe_allow_html=True)
    tab_reg, tab_traz, tab_hist = st.tabs(["📝 REGISTRO", "⚙️ TRAZABILIDAD", "📊 HISTORIAL"])

    with tab_reg:
        if st.session_state.registro_ok:
            st.success(f"✅ ORDEN {st.session_state.ultima_orden['n_orden']} GUARDADA.")
            pdf_file = generar_pdf_reporte(st.session_state.ultima_orden)
            c1, c2 = st.columns(2)
            c1.download_button("📥 DESCARGAR PDF", data=pdf_file, file_name=f"GTech_{st.session_state.ultima_orden['n_orden']}.pdf")
            if c2.button("➕ NUEVA ORDEN"):
                reset_completo(); st.rerun()
        else:
            with st.form("form_registro"):
                st.markdown("### 📋 Datos de Recepción")
                col1, col2 = st.columns(2)
                f_in = col1.date_input("Fecha Ingreso", value=datetime.now())
                n_id = col2.text_input("ID Orden", value=st.session_state.id_proxima, key="form_n_orden")
                cli = col1.text_input("Cliente", key="form_cliente")
                qty = col2.number_input("Cantidad", min_value=1, key="form_cantidad")
                mat = col1.text_input("Material", key="form_material")
                f_out = col2.date_input("Fecha Entrega")
                st.markdown("---")
                ok = st.checkbox("Planos validados")
                up = st.file_uploader("Cargar plano", type=['pdf','png','jpg'])
                b_s, b_l = st.columns(2)
                if b_s.form_submit_button("💾 GUARDAR"):
                    if not ok or up is None: st.error("Falta plano.")
                    elif not n_id or not cli: st.warning("Campos vacíos.")
                    else:
                        try:
                            if ordenes_col.find_one({"n_orden": n_id}):
                                st.error("ID duplicada."); st.session_state.id_proxima = obtener_siguiente_orden()
                            else:
                                d = {"n_orden": n_id, "cliente": cli, "f_recepcion": str(f_in), "material": mat, "cantidad": qty, "entrega": str(f_out), "etapa": "Registro", "status": "Pendiente", "historial": []}
                                ordenes_col.insert_one(d); st.session_state.ultima_orden = d; st.session_state.registro_ok = True; st.rerun()
                        except: st.error("Fallo de red.")
                if b_l.form_submit_button("🧹 LIMPIAR"): reset_completo(); st.rerun()

    with tab_traz:
        st.markdown("### ⚙️ Actualizar Etapa")
        try:
            # Validación robusta de datos para evitar "Error al cargar datos"
            activas = list(ordenes_col.find({"status": "Pendiente"}))
            if activas:
                with st.form("form_traz"):
                    sel = st.selectbox("Orden", [o["n_orden"] for o in activas])
                    c1, c2 = st.columns(2)
                    et = c1.selectbox("Nueva Etapa", ["Maquinado", "Rectificado", "Calidad", "Finalizado"])
                    h1, h2 = c1.time_input("Inicio"), c2.time_input("Fin")
                    obs = st.text_area("Notas")
                    if st.form_submit_button("ACTUALIZAR"):
                        st_f = "Finalizado" if et == "Finalizado" else "Pendiente"
                        ordenes_col.update_one({"n_orden": sel}, {"$set": {"etapa": et, "status": st_f}, "$push": {"historial": {"etapa": et, "inicio": str(h1), "fin": str(h2), "nota": obs}}})
                        st.success("Actualizado."); time.sleep(1); st.rerun()
            else: st.info("No hay pendientes.")
        except Exception as e: st.error(f"Error de base de datos: {e}")

    with tab_hist:
        st.markdown("### 📊 Historial")
        try:
            todo = list(ordenes_col.find())
            if todo:
                df = pd.DataFrame(todo)[["n_orden", "cliente", "etapa", "status"]]
                st.dataframe(df, use_container_width=True)
                sel_h = st.selectbox("Reporte PDF", df["n_orden"].tolist())
                if st.button("📄 GENERAR"):
                    det = ordenes_col.find_one({"n_orden": sel_h})
                    st.download_button("📥 DESCARGAR", data=generar_pdf_reporte(det), file_name=f"Reporte_{sel_h}.pdf")
        except: st.error("Error al cargar historial.")
