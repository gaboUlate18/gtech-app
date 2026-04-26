import streamlit as st
from pymongo import MongoClient
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import time

# --- 1. CONEXIÓN ---
MONGO_URL = "mongodb+srv://gtech:Ingenieria2026@g-tech.0p52gdx.mongodb.net/?appName=G-Tech"

@st.cache_resource
def init_connection():
    return MongoClient(MONGO_URL, serverSelectionTimeoutMS=10000)

try:
    client = init_connection()
    db = client.GTechDB
    ordenes_col = db.ordenes
except:
    st.error("Error de conexión con la base de datos.")

# --- 2. LÓGICA DE NEGOCIO ---

def obtener_primera_id_disponible():
    try:
        cursor = ordenes_col.find({}, {"n_orden": 1, "_id": 0})
        ids_ocupadas = set()
        for doc in cursor:
            try:
                ids_ocupadas.add(int(doc["n_orden"]))
            except: continue
        sugerencia = 1
        while sugerencia in ids_ocupadas:
            sugerencia += 1
        return str(sugerencia)
    except:
        return "1"

def reset_manual():
    for key in list(st.session_state.keys()):
        if "form_" in key: del st.session_state[key]
    st.session_state.registro_ok = False
    st.session_state.id_proxima = obtener_primera_id_disponible()

# --- 3. GENERACIÓN DE REPORTES PDF ---

def generar_pdf_orden(datos):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_fill_color(14, 75, 122)
    pdf.rect(0, 0, 210, 45, 'F')
    pdf.set_font("Arial", 'B', 20); pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 15, "G-TECH ENGINEERING", ln=True, align='C')
    pdf.ln(30); pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", 'B', 12)
    for k, v in [("ID Orden:", datos['n_orden']), ("Cliente:", datos['cliente']), ("Material:", datos['material']), ("Etapa:", datos.get('etapa', 'Registro'))]:
        pdf.cell(50, 8, k); pdf.cell(0, 8, str(v), ln=True)
    return pdf.output(dest='S').encode('latin-1')

def generar_pdf_historial(df):
    pdf = FPDF(orientation='L')
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16); pdf.cell(0, 10, "REPORTE DE HISTORIAL G-TECH", ln=True, align='C')
    pdf.ln(10); pdf.set_font("Arial", 'B', 10); pdf.set_fill_color(200, 200, 200)
    headers, widths = ["Orden", "Cliente", "Material", "Etapa", "Estado"], [30, 70, 70, 50, 40]
    for i, h in enumerate(headers): pdf.cell(widths[i], 10, h, border=1, fill=True)
    pdf.ln(); pdf.set_font("Arial", size=9)
    for _, row in df.iterrows():
        for i, col in enumerate(["n_orden", "cliente", "material", "etapa", "status"]):
            pdf.cell(widths[i], 8, str(row[col])[:35], border=1)
        pdf.ln()
    return pdf.output(dest='S').encode('latin-1')

# --- 4. INTERFAZ ---
st.set_page_config(page_title="G-Tech System", layout="wide")

if 'auth' not in st.session_state: st.session_state.auth = False
if 'id_proxima' not in st.session_state: st.session_state.id_proxima = obtener_primera_id_disponible()
if 'registro_ok' not in st.session_state: st.session_state.registro_ok = False

st.markdown("""<style>.main-title { color: #0e4b7a; text-align: center; font-weight: 800; font-size: 3.5rem; margin-top: 50px; }</style>""", unsafe_allow_html=True)

if not st.session_state.auth:
    st.markdown("<h1 class='main-title'>G-TECH ENGINEERING</h1>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1, 1])
    if col.button("🔓 INGRESAR AL PANEL"): st.session_state.auth = True; st.rerun()

else:
    st.markdown("<h1 style='text-align:center; color:#0e4b7a;'>🛡️ Panel de Control</h1>", unsafe_allow_html=True)
    t1, t2, t3 = st.tabs(["📝 REGISTRO", "⚙️ TRAZABILIDAD", "📊 HISTORIAL"])

    with t1:
        if st.session_state.registro_ok:
            st.success(f"✅ Orden {st.session_state.ultima_orden['n_orden']} registrada.")
            pdf_b = generar_pdf_orden(st.session_state.ultima_orden)
            c1, c2 = st.columns(2)
            c1.download_button("📥 DESCARGAR PDF", data=pdf_b, file_name=f"Orden_{st.session_state.ultima_orden['n_orden']}.pdf")
            if c2.button("➕ NUEVA ORDEN"): reset_manual(); st.rerun()
        else:
            with st.form("form_reg"):
                c1, c2 = st.columns(2)
                f_in = c1.date_input("Fecha Ingreso", value=datetime.now())
                n_id = c2.text_input("ID Orden Sugerida", value=st.session_state.id_proxima, key="form_n_orden")
                cli, cant = c1.text_input("Cliente", key="form_cli"), c2.number_input("Cantidad", min_value=1, key="form_cant")
                mat, f_out = c1.text_input("Material", key="form_mat"), c2.date_input("Fecha Entrega")
                up = st.file_uploader("Cargar Plano Técnico", type=['pdf','png','jpg'])
                if st.form_submit_button("💾 GUARDAR"):
                    if up is None: st.error("El plano es obligatorio.")
                    elif ordenes_col.find_one({"n_orden": n_id}): st.error("ID ocupada."); st.rerun()
                    else:
                        d = {"n_orden": n_id, "cliente": cli, "f_recepcion": str(f_in), "material": mat, "cantidad": cant, "entrega": str(f_out), "etapa": "Registro", "status": "Pendiente", "historial": []}
                        ordenes_col.insert_one(d); st.session_state.ultima_orden = d; st.session_state.registro_ok = True; st.rerun()
                if st.form_submit_button("🧹 LIMPIAR"): reset_manual(); st.rerun()

    with t2:
        st.markdown("### ⚙️ Trazabilidad de Procesos")
        activas = list(ordenes_col.find({"status": "Pendiente"}))
        if activas:
            etapas_full = ["Registro", "Maquinado", "Rectificado", "Tratamiento", "Ensamble", "Calidad", "Pulido", "Finalizado"]
            
            with st.form("form_traz"):
                sel = st.selectbox("Seleccionar Orden", [o["n_orden"] for o in activas])
                orden_data = next(item for item in activas if item["n_orden"] == sel)
                
                # CORRECCIÓN: Limpieza de espacios y validación de índice
                etapa_actual = str(orden_data.get("etapa", "Registro")).strip()
                
                if etapa_actual in etapas_full:
                    indice_actual = etapas_full.index(etapa_actual)
                else:
                    indice_actual = 0 # Por seguridad, si no se encuentra, empieza desde el inicio
                
                etapas_disponibles = etapas_full[indice_actual + 1:]
                
                if etapas_disponibles:
                    et = st.selectbox("Siguiente Etapa", etapas_disponibles)
                    h1, h2 = st.columns(2)
                    t_i, t_f = h1.time_input("Inicio"), h2.time_input("Fin")
                    obs = st.text_area("Notas")
                    if st.form_submit_button("ACTUALIZAR"):
                        st_f = "Finalizado" if et == "Finalizado" else "Pendiente"
                        ordenes_col.update_one({"n_orden": sel}, {"$set": {"etapa": et, "status": st_f}, "$push": {"historial": {"etapa": et, "inicio": str(t_i), "fin": str(t_f), "nota": obs}}})
                        st.success(f"Orden {sel} movida a {et}."); time.sleep(1); st.rerun()
                else:
                    st.warning("Esta orden ya ha completado todas las etapas disponibles.")
                    st.form_submit_button("Cerrar", disabled=True)
        else: st.info("No hay órdenes pendientes.")

    with t3:
        st.markdown("### 📊 Historial y Estatus Visual")
        todo = list(ordenes_col.find())
        if todo:
            df = pd.DataFrame(todo)[["n_orden", "cliente", "material", "etapa", "status"]]
            def color_status(val):
                return f'background-color: {"#d4edda" if val == "Finalizado" else "#f8d7da"}'
            st.dataframe(df.style.map(color_status, subset=['status']), use_container_width=True)
            if st.button("📄 GENERAR PDF DEL HISTORIAL COMPLETO"):
                st.download_button("📥 DESCARGAR REPORTE", data=generar_pdf_historial(df), file_name="Historial_GTech.pdf")
        else: st.warning("Sin datos.")
