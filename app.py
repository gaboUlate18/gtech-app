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
    return MongoClient(MONGO_URL, serverSelectionTimeoutMS=10000)

try:
    client = init_connection()
    db = client.GTechDB
    ordenes_col = db.ordenes
except:
    st.error("⚠️ Error de conexión con el servidor.")

# --- 2. LÓGICA DE PROCESOS ---

def obtener_primera_id_disponible():
    try:
        cursor = ordenes_col.find({}, {"n_orden": 1, "_id": 0})
        ids_ocupadas = {int(doc["n_orden"]) for doc in cursor if str(doc["n_orden"]).isdigit()}
        sugerencia = 1
        while sugerencia in ids_ocupadas: sugerencia += 1
        return str(sugerencia)
    except: return "1"

def generar_pdf_completo_orden(datos):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_fill_color(14, 75, 122)
    pdf.rect(0, 0, 210, 40, 'F')
    pdf.set_font("Arial", 'B', 22); pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 20, "G-TECH ENGINEERING", ln=True, align='C')
    pdf.set_font("Arial", '', 12); pdf.cell(0, 10, "Comprobante de Registro de Orden", ln=True, align='C')
    pdf.ln(20); pdf.set_text_color(0, 0, 0); pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, f"DETALLES DE LA ORDEN # {datos['n_orden']}", ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y()); pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 11)
    detalles = [
        ("Cliente:", datos['cliente']), 
        ("Material:", datos['material']), 
        ("Cantidad:", str(datos['cantidad'])), 
        ("Fecha Ingreso:", datos['f_recepcion']), 
        ("Fecha Entrega:", datos['entrega']), 
        ("Etapa Inicial:", datos['etapa']), 
        ("Estatus:", datos['status'])
    ]
    for label, valor in detalles:
        pdf.set_font("Arial", 'B', 11); pdf.cell(50, 10, label)
        pdf.set_font("Arial", '', 11); pdf.cell(0, 10, valor, ln=True)
    return pdf.output(dest='S').encode('latin-1')

def generar_pdf_tabla_historial(df):
    pdf = FPDF(orientation='L')
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16); pdf.cell(0, 10, "REPORTE GENERAL DE HISTORIAL - G-TECH", ln=True, align='C')
    pdf.ln(10); pdf.set_font("Arial", 'B', 10); pdf.set_fill_color(200, 200, 200)
    headers, widths = ["Orden", "Cliente", "Material", "Etapa", "Estado"], [30, 70, 70, 50, 40]
    for i, h in enumerate(headers): pdf.cell(widths[i], 10, h, border=1, fill=True)
    pdf.ln(); pdf.set_font("Arial", size=9)
    for _, row in df.iterrows():
        for i, col in enumerate(["n_orden", "cliente", "material", "etapa", "status"]):
            pdf.cell(widths[i], 8, str(row[col])[:35], border=1)
        pdf.ln()
    return pdf.output(dest='S').encode('latin-1')

def reset_manual():
    for key in list(st.session_state.keys()):
        if "form_" in key: del st.session_state[key]
    st.session_state.registro_ok = False
    st.session_state.id_proxima = obtener_primera_id_disponible()

# --- 3. CONFIGURACIÓN VISUAL (CSS) ---
st.set_page_config(page_title="G-Tech Engineering", layout="wide")

st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(180deg, #ffffff 0%, #eef2f7 100%);
    }
    
    .welcome-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 70vh;
        text-align: center;
    }
    
    .main-title {
        color: #0e4b7a;
        font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        font-size: 6rem; /* Letra mucho más grande */
        font-weight: 900;
        letter-spacing: -3px;
        margin-bottom: 50px;
        line-height: 1;
    }

    /* Botón */
    div.stButton > button {
        background-color: #0e4b7a;
        color: white;
        font-size: 22px;
        font-weight: 700;
        padding: 20px 60px;
        border-radius: 12px; /* Bordes un poco más rectos pero modernos */
        border: none;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        box-shadow: 0 10px 20px rgba(14, 75, 122, 0.2);
    }
    
    div.stButton > button:hover {
        background-color: #1a5f96;
        transform: scale(1.05);
        box-shadow: 0 15px 25px rgba(14, 75, 122, 0.3);
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. INTERFAZ ---
ETAPAS_MASTER = ["Registro", "Diseño", "Preparación del material", "Maquinado", "Rectificado", "Control de Calidad", "Empaque", "Finalizado"]

if 'auth' not in st.session_state: st.session_state.auth = False
if 'id_proxima' not in st.session_state: st.session_state.id_proxima = obtener_primera_id_disponible()
if 'registro_ok' not in st.session_state: st.session_state.registro_ok = False

# PANTALLA DE INICIO
if not st.session_state.auth:
    st.markdown('<div class="welcome-container">', unsafe_allow_html=True)
    st.markdown('<h1 class="main-title">G-TECH<br>ENGINEERING</h1>', unsafe_allow_html=True)
    
    _, btn_col, _ = st.columns([1, 0.8, 1])
    with btn_col:
        if st.button("🔓 INGRESAR AL PANEL"):
            st.session_state.auth = True
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# PANEL DE CONTROL
else:
    st.markdown("<h2 style='text-align:center; color:#0e4b7a; margin-bottom:30px;'>🛡️ Panel de Control Operativo</h2>", unsafe_allow_html=True)
    t1, t2, t3 = st.tabs(["📝 REGISTRO DE ORDEN", "⚙️ TRAZABILIDAD", "📊 HISTORIAL"])

    with t1:
        if st.session_state.registro_ok:
            st.success(f"✅ Orden {st.session_state.ultima_orden['n_orden']} registrada.")
            pdf_b = generar_pdf_completo_orden(st.session_state.ultima_orden)
            c1, c2 = st.columns(2)
            c1.download_button("📥 DESCARGAR COMPROBANTE PDF", data=pdf_b, file_name=f"Orden_{st.session_state.ultima_orden['n_orden']}.pdf")
            if c2.button("➕ NUEVA ORDEN"): reset_manual(); st.rerun()
        else:
            with st.form("form_reg"):
                c1, c2 = st.columns(2)
                f_in = c1.date_input("Fecha Ingreso", value=datetime.now())
                n_id = c2.text_input("ID Orden Sugerida", value=st.session_state.id_proxima, key="form_n_orden")
                cli, cant = c1.text_input("Cliente", key="form_cli"), c2.number_input("Cantidad", min_value=1, key="form_cant")
                mat, f_out = c1.text_input("Material", key="form_mat"), c2.date_input("Fecha Entrega")
                up = st.file_uploader("Cargar Plano Técnico", type=['pdf','png','jpg'])
                if st.form_submit_button("💾 GUARDAR REGISTRO"):
                    if up is None: st.error("El plano es obligatorio.")
                    elif ordenes_col.find_one({"n_orden": n_id}): st.error("ID ya ocupada."); st.rerun()
                    else:
                        d = {"n_orden": n_id, "cliente": cli, "f_recepcion": str(f_in), "material": mat, "cantidad": cant, "entrega": str(f_out), "etapa": "Registro", "status": "Pendiente", "historial": []}
                        ordenes_col.insert_one(d); st.session_state.ultima_orden = d; st.session_state.registro_ok = True; st.rerun()
                if st.form_submit_button("🧹 LIMPIAR"): reset_manual(); st.rerun()

    with t2:
        activas = list(ordenes_col.find({"status": "Pendiente"}))
        if activas:
            with st.form("form_traz"):
                sel = st.selectbox("Seleccionar Orden", [o["n_orden"] for o in activas])
                orden_data = next(item for item in activas if item["n_orden"] == sel)
                et_act = str(orden_data.get("etapa", "Registro")).strip()
                idx = ETAPAS_MASTER.index(et_act) if et_act in ETAPAS_MASTER else 0
                disp = ETAPAS_MASTER[idx + 1:]
                if disp:
                    et = st.selectbox("Siguiente Etapa", disp)
                    h1, h2 = st.columns(2)
                    t_i, t_f = h1.time_input("Inicio"), h2.time_input("Fin")
                    obs = st.text_area("Observaciones")
                    if st.form_submit_button("ACTUALIZAR PROCESO"):
                        st_f = "Finalizado" if et == "Finalizado" else "Pendiente"
                        ordenes_col.update_one({"n_orden": sel}, {"$set": {"etapa": et, "status": st_f}, "$push": {"historial": {"etapa": et, "inicio": str(t_i), "fin": str(t_f), "nota": obs}}})
                        st.success(f"Orden {sel} actualizada a {et}."); time.sleep(1); st.rerun()
                else: st.warning("Proceso completo."); st.form_submit_button("Cerrar", disabled=True)
        else: st.info("No hay procesos pendientes.")

    with t3:
        todo = list(ordenes_col.find())
        if todo:
            df = pd.DataFrame(todo)[["n_orden", "cliente", "material", "etapa", "status"]]
            def color_status(val):
                return f'background-color: {"#d4edda; color: #155724" if val == "Finalizado" else "#f8d7da; color: #721c24"}'
            st.dataframe(df.style.map(color_status, subset=['status']), use_container_width=True)
            if st.button("📄 GENERAR PDF DEL HISTORIAL"):
                st.download_button("📥 DESCARGAR REPORTE", data=generar_pdf_tabla_historial(df), file_name="Historial_GTech.pdf")
