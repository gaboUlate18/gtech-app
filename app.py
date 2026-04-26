import streamlit as st
from pymongo import MongoClient
import pandas as pd
from datetime import datetime
from fpdf import FPDF

# 1. CONEXIÓN A BASE DE DATOS
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

# --- CAMBIO CRUCIAL AQUÍ ---
def limpiar_formulario():
    # En lugar de asignar directamente a las llaves de los widgets, 
    # limpiamos el estado de sesión de forma que Streamlit lo resetee al recargar.
    keys_to_reset = ["n_orden_form", "cliente_form", "material_form", "cantidad_form"]
    for key in keys_to_reset:
        if key in st.session_state:
            del st.session_state[key]
    # Forzamos la nueva sugerencia de orden
    st.session_state["orden_sugerida"] = obtener_siguiente_orden()

# 3. CONFIGURACIÓN UI
st.set_page_config(page_title="G-Tech Engineering System", layout="wide")

if 'auth' not in st.session_state:
    st.session_state.auth = False
if 'orden_sugerida' not in st.session_state:
    st.session_state["orden_sugerida"] = obtener_siguiente_orden()

# --- PANTALLA DE BIENVENIDA ---
if not st.session_state.auth:
    st.markdown("<h1 style='text-align: center; margin-top: 50px;'>Bienvenido a G-Tech</h1>", unsafe_allow_html=True)
    _, col_btn, _ = st.columns([1, 1, 1])
    if col_btn.button("INGRESAR AL SISTEMA"):
        st.session_state.auth = True
        st.rerun()

else:
    st.markdown("<h1>🛡️ G-TECH ENGINEERING SYSTEM</h1>", unsafe_allow_html=True)
    t1, t2, t3 = st.tabs(["📝 REGISTRO", "⚙️ TRAZABILIDAD", "📊 HISTORIAL"])

    with t1:
        with st.form("reg_form", clear_on_submit=True): # clear_on_submit ayuda a limpiar visualmente
            ca, cb = st.columns(2)
            f_recep = ca.date_input("Fecha ingreso", value=datetime.now())
            
            # Usamos el valor sugerido que guardamos en session_state
            id_orden = cb.text_input("ID Orden", value=st.session_state["orden_sugerida"], key="n_orden_form")
            
            client_name = ca.text_input("Cliente", key="cliente_form")
            qty = cb.number_input("Cantidad", min_value=1, value=1, key="cantidad_form")
            spec = ca.text_input("Material", key="material_form")
            f_limit = cb.date_input("Fecha límite")
            
            st.markdown("---")
            docs = st.radio("¿Planos aprobados?", ["Sí", "No"], horizontal=True)
            file = st.file_uploader("Adjuntar Plano", type=['pdf', 'jpg', 'png'])
            
            b1, b2 = st.columns(2)
            save_clicked = b1.form_submit_button("💾 GUARDAR E IMPRIMIR")
            
            # El botón de limpiar ahora llama a la función corregida
            if b2.form_submit_button("🧹 LIMPIAR"):
                limpiar_formulario()
                st.rerun()

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
                        data = {"n_orden": id_orden, "cliente": client_name, "f_recepcion": str(f_recep), "material": spec, "cantidad": qty, "entrega": str(f_limit), "etapa": "Diseño", "status": "Pendiente", "historial": []}
                        ordenes_col.insert_one(data)
                        st.success(f"✅ Orden {id_orden} registrada.")
                        
                        # (Aquí iría tu función de PDF ya definida)
                        
                        # Tras guardar, preparamos la limpieza para la siguiente orden
                        limpiar_formulario()
                        st.info("Formulario listo para nueva orden. Use el botón de descarga arriba si generó PDF.")
                except:
                    st.error("Error de red.")

    # ... Resto de pestañas (Trazabilidad e Historial) se mantienen igual ...
