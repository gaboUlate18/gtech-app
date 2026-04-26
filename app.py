import streamlit as st
from pymongo import MongoClient
import pandas as pd
from datetime import datetime
from fpdf import FPDF

# 1. CONEXIÓN (Estable)
MONGO_URL = "mongodb+srv://gtech:Ingenieria2026@g-tech.0p52gdx.mongodb.net/?appName=G-Tech"

@st.cache_resource
def init_connection():
    return MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)

try:
    client = init_connection()
    db = client.GTechDB
    ordenes_col = db.ordenes
except:
    st.error("Error de conexión.")

# 2. FUNCIONES DE APOYO
def obtener_siguiente_orden():
    try:
        todas = list(ordenes_col.find().sort("n_orden", -1).limit(1))
        if todas:
            return str(int(todas[0]["n_orden"]) + 1)
        return "1001"
    except:
        return "1001"

def generar_pdf_completo(datos):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_fill_color(14, 75, 122)
    pdf.rect(0, 0, 210, 45, 'F')
    pdf.set_font("Arial", 'B', 20); pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 15, "G-TECH ENGINEERING SYSTEM", ln=True, align='C')
    pdf.ln(35); pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", 'B', 14); pdf.cell(0, 10, f"ORDEN: {datos['n_orden']}", ln=True)
    pdf.set_font("Arial", size=12)
    for k, v in [("Cliente:", datos['cliente']), ("Material:", datos['material']), ("Cantidad:", str(datos['cantidad']))]:
        pdf.cell(50, 10, k); pdf.cell(0, 10, v, ln=True)
    return pdf.output(dest='S').encode('latin-1')

def reset_manual():
    # Borramos las llaves de los widgets para forzar el vacío
    for key in ["n_orden_form", "cliente_form", "material_form", "cantidad_form"]:
        if key in st.session_state:
            del st.session_state[key]
    st.session_state["orden_sugerida"] = obtener_siguiente_orden()

# 3. CONFIGURACIÓN UI
st.set_page_config(page_title="G-Tech Engineering System", layout="wide")

if 'auth' not in st.session_state: st.session_state.auth = False
if 'orden_sugerida' not in st.session_state:
    st.session_state["orden_sugerida"] = obtener_siguiente_orden()

if not st.session_state.auth:
    st.markdown("<h1 style='text-align: center;'>Bienvenido a G-Tech</h1>", unsafe_allow_html=True)
    _, col_btn, _ = st.columns([1, 1, 1])
    if col_btn.button("INGRESAR AL SISTEMA"):
        st.session_state.auth = True
        st.rerun()

else:
    st.markdown("<h1>🛡️ G-TECH ENGINEERING SYSTEM</h1>", unsafe_allow_html=True)
    t1, t2, t3 = st.tabs(["📝 REGISTRO", "⚙️ TRAZABILIDAD", "📊 HISTORIAL"])

    with t1:
        with st.form("reg_form", clear_on_submit=False):
            ca, cb = st.columns(2)
            f_recep = ca.date_input("Fecha ingreso", value=datetime.now())
            id_orden = cb.text_input("ID Orden", value=st.session_state["orden_sugerida"], key="n_orden_form")
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
                reset_manual(); st.rerun()

        # LÓGICA DE PROCESAMIENTO FUERA DEL FORMULARIO
        if save_clicked:
            if docs == "No" or file is None:
                st.error("❌ Se requiere el plano.")
            elif not id_orden or not client_name:
                st.warning("⚠️ Datos incompletos.")
            else:
                try:
                    if ordenes_col.find_one({"n_orden": id_orden}):
                        st.error(f"❌ La Orden {id_orden} ya existe.")
                    else:
                        data = {
                            "n_orden": id_orden, "cliente": client_name, "f_recepcion": str(f_recep),
                            "material": spec, "cantidad": qty, "entrega": str(f_limit),
                            "etapa": "Diseño", "status": "Pendiente", "historial": []
                        }
                        ordenes_col.insert_one(data)
                        
                        # GUARDAMOS LOS DATOS EN SESSION STATE PARA EL BOTÓN DE DESCARGA
                        st.session_state["ultimo_registro"] = data
                        st.session_state["registro_exitoso"] = True
                        
                        # Limpiamos los campos para la siguiente entrada
                        reset_manual()
                        st.rerun() # Refrescamos para aplicar el reset
                except:
                    st.error("🔌 Error de conexión.")

        # MOSTRAR RESULTADO Y PDF (Si el registro fue exitoso)
        if st.session_state.get("registro_exitoso"):
            st.success(f"✅ Orden {st.session_state['ultimo_registro']['n_orden']} registrada correctamente.")
            pdf_bytes = generar_pdf_completo(st.session_state['ultimo_registro'])
            st.download_button(
                label="📥 DESCARGAR COMPROBANTE PDF",
                data=pdf_bytes,
                file_name=f"Orden_{st.session_state['ultimo_registro']['n_orden']}.pdf",
                mime="application/pdf"
            )
            if st.button("Finalizar y Nueva Orden"):
                st.session_state["registro_exitoso"] = False
                st.rerun()

    # ... Secciones 2 y 3 (Trazabilidad e Historial)
