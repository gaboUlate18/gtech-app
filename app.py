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

# --- 2. LÓGICA DE NEGOCIO (PROCESOS) ---

def obtener_primera_id_desocupada():
    """Busca el primer hueco numérico disponible empezando desde 1001."""
    try:
        # Obtenemos todas las IDs y las convertimos a enteros
        cursor = ordenes_col.find({}, {"n_orden": 1})
        ids_existentes = set()
        for doc in cursor:
            try:
                ids_existentes.add(int(doc["n_orden"]))
            except:
                continue
        
        # Buscamos el primer número que no esté en el set
        sugerencia = 1001
        while sugerencia in ids_existentes:
            sugerencia += 1
        return str(sugerencia)
    except:
        return "1001"

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

def generar_pdf_tabla_historial(df):
    pdf = FPDF(orientation='L')
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "REPORTE GENERAL DE HISTORIAL - G-TECH", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 10); pdf.set_fill_color(200, 200, 200)
    pdf.cell(30, 10, "Orden", border=1, fill=True)
    pdf.cell(60, 10, "Cliente", border=1, fill=True)
    pdf.cell(60, 10, "Material", border=1, fill=True)
    pdf.cell(40, 10, "Etapa", border=1, fill=True)
    pdf.cell(40, 10, "Estado", border=1, fill=True)
    pdf.ln()
    pdf.set_font("Arial", size=9)
    for _, row in df.iterrows():
        pdf.cell(30, 8, str(row['n_orden']), border=1)
        pdf.cell(60, 8, str(row['cliente'])[:30], border=1)
        pdf.cell(60, 8, str(row['material'])[:30], border=1)
        pdf.cell(40, 8, str(row['etapa']), border=1)
        pdf.cell(40, 8, str(row['status']), border=1)
        pdf.ln()
    return pdf.output(dest='S').encode('latin-1')

def reset_manual():
    for key in list(st.session_state.keys()):
        if "form_" in key: del st.session_state[key]
    st.session_state.registro_ok = False
    st.session_state.id_proxima = obtener_primera_id_desocupada()

# --- 3. INTERFAZ ---
st.set_page_config(page_title="G-Tech System", layout="wide")

if 'auth' not in st.session_state: st.session_state.auth = False
if 'id_proxima' not in st.session_state: st.session_state.id_proxima = obtener_primera_id_desocupada()
if 'registro_ok' not in st.session_state: st.session_state.registro_ok = False

if not st.session_state.auth:
    st.write("<br><br><br><br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align:center; color:#0e4b7a; font-size: 3.5rem;'>G-TECH ENGINEERING</h1>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1, 1])
    if col.button("🔓 INGRESAR AL PANEL"):
        st.session_state.auth = True; st.rerun()

else:
    st.markdown("<h1 style='text-align:center; color:#0e4b7a;'>🛡️ Panel de Control</h1>", unsafe_allow_html=True)
    t1, t2, t3 = st.tabs(["📝 REGISTRO", "⚙️ TRAZABILIDAD", "📊 HISTORIAL"])

    with t1:
        if st.session_state.registro_ok:
            st.success(f"✅ Orden {st.session_state.ultima_orden['n_orden']} registrada.")
            pdf_bytes = generar_pdf_orden(st.session_state.ultima_orden)
            c1, c2 = st.columns(2)
            c1.download_button("📥 DESCARGAR PDF", data=pdf_bytes, file_name=f"Orden_{st.session_state.ultima_orden['n_orden']}.pdf")
            if c2.button("➕ NUEVA ORDEN"): reset_manual(); st.rerun()
        else:
            with st.form("form_reg"):
                c1, c2 = st.columns(2)
                f_in = c1.date_input("Fecha Ingreso", value=datetime.now())
                n_id = c2.text_input("ID Orden (Sugerida)", value=st.session_state.id_proxima, key="form_n_orden")
                cli = c1.text_input("Cliente", key="form_cli")
                cant = c2.number_input("Cantidad", min_value=1, key="form_cant")
                mat = c1.text_input("Material", key="form_mat")
                f_out = c2.date_input("Fecha Entrega Compromiso")
                up = st.file_uploader("Cargar plano", type=['pdf','png','jpg'])
                
                b1, b2 = st.columns(2)
                if b1.form_submit_button("💾 GUARDAR"):
                    if up is None: st.error("Falta plano.")
                    elif not n_id or not cli: st.warning("ID y Cliente son obligatorios.")
                    else:
                        if ordenes_col.find_one({"n_orden": n_id}):
                            st.error("Esa ID ya está en uso. El sistema sugerirá una nueva."); st.session_state.id_proxima = obtener_primera_id_desocupada(); st.rerun()
                        else:
                            d = {"n_orden": n_id, "cliente": cli, "f_recepcion": str(f_in), "material": mat, "cantidad": cant, "entrega": str(f_out), "etapa": "Registro", "status": "Pendiente", "historial": []}
                            ordenes_col.insert_one(d); st.session_state.ultima_orden = d; st.session_state.registro_ok = True; st.rerun()
                if b2.form_submit_button("🧹 LIMPIAR"): reset_manual(); st.rerun()

    with t2:
        st.markdown("### ⚙️ Actualizar Etapa")
        activas = list(ordenes_col.find({"status": "Pendiente"}))
        if activas:
            with st.form("form_traz"):
                sel = st.selectbox("Orden", [o["n_orden"] for o in activas])
                etapas_lista = ["Registro", "Maquinado", "Rectificado", "Tratamiento", "Ensamble", "Calidad", "Pulido", "Finalizado"]
                et = st.selectbox("Etapa Actual", etapas_lista)
                h1, h2 = st.columns(2)
                t_i = h1.time_input("Inicio")
                t_f = h2.time_input("Fin")
                obs = st.text_area("Observaciones")
                if st.form_submit_button("ACTUALIZAR PROCESO"):
                    st_f = "Finalizado" if et == "Finalizado" else "Pendiente"
                    ordenes_col.update_one({"n_orden": sel}, {"$set": {"etapa": et, "status": st_f}, "$push": {"historial": {"etapa": et, "inicio": str(t_i), "fin": str(t_f), "nota": obs}}})
                    st.success(f"Orden {sel} actualizada."); time.sleep(1); st.rerun()
        else: st.info("No hay procesos pendientes.")

    with t3:
        st.markdown("### 📊 Historial y Gestión Visual")
        todo = list(ordenes_col.find())
        if todo:
            df = pd.DataFrame(todo)[["n_orden", "cliente", "material", "etapa", "status"]]
            
            # Formato condicional: Pendiente (Rojo) / Finalizado (Verde)
            def apply_style(val):
                if val == 'Finalizado': return 'background-color: #d4edda; color: #155724'
                return 'background-color: #f8d7da; color: #721c24'
            
            st.dataframe(df.style.applymap(apply_style, subset=['status']), use_container_width=True)
            
            st.markdown("---")
            if st.button("📄 GENERAR PDF DEL HISTORIAL COMPLETO"):
                pdf_total = generar_pdf_tabla_historial(df)
                st.download_button("📥 DESCARGAR REPORTE", data=pdf_total, file_name="Historial_General_GTech.pdf")
        else: st.warning("Sin registros.")
