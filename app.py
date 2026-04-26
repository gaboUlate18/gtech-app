import streamlit as st
from pymongo import MongoClient
import pandas as pd
from datetime import datetime
from fpdf import FPDF

# 1. CONEXIÓN (Mantenemos la lógica estable)
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

def limpiar_formulario():
    """Solo se llama cuando estamos seguros de que la orden se guardó."""
    keys_to_reset = ["n_orden_form", "cliente_form", "material_form", "cantidad_form"]
    for key in keys_to_reset:
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
        # IMPORTANTE: clear_on_submit debe estar en FALSE para no borrar datos ante errores
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
            
            if b2.form_submit_button("🧹 LIMPIAR FORMULARIO MANUALLY"):
                limpiar_formulario()
                st.rerun()

        if save_clicked:
            # VALIDACIONES LOCALES (No borran datos, solo muestran advertencias)
            if docs == "No" or file is None:
                st.error("❌ Detenido: Se requiere el plano para proceder.")
            elif not id_orden or not client_name:
                st.warning("⚠️ Información faltante en campos obligatorios.")
            else:
                try:
                    # INTENTO DE GUARDADO
                    if ordenes_col.find_one({"n_orden": id_orden}):
                        st.error(f"❌ La Orden {id_orden} ya existe. Cambie el ID para guardar.")
                        # Al no llamar a limpiar_formulario(), los datos siguen en los campos
                    else:
                        data = {
                            "n_orden": id_orden, "cliente": client_name, 
                            "f_recepcion": str(f_recep), "material": spec, 
                            "cantidad": qty, "entrega": str(f_limit),
                            "etapa": "Diseño", "status": "Pendiente", "historial": []
                        }
                        ordenes_col.insert_one(data)
                        
                        # SI LLEGAMOS AQUÍ, TODO SALIÓ BIEN
                        st.success(f"✅ Orden {id_orden} guardada con éxito.")
                        
                        # Mostramos el botón de descarga del PDF (Asumiendo que tienes la función definida)
                        # pdf_bytes = generar_pdf_completo(data)
                        # st.download_button("Descargar PDF", ...)

                        # SOLO EN ESTE PUNTO LIMPIAMOS
                        limpiar_formulario()
                        st.info("Formulario reseteado para la siguiente orden.")
                        st.balloons() # Feedback visual de éxito
                        
                except Exception as e:
                    # SI HAY ERROR DE RED, LOS DATOS SIGUEN EN EL FORMULARIO
                    st.error(f"🔌 Error de conexión con Atlas. Los datos no se han perdido, intente guardar de nuevo.")
