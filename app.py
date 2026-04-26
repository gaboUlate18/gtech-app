import streamlit as st
from pymongo import MongoClient
import pandas as pd
from datetime import datetime
from fpdf import FPDF

# 1. CONFIGURACIÓN DE CONEXIÓN
MONGO_URL = "mongodb+srv://gtech:Ingenieria2026@g-tech.0p52gdx.mongodb.net/?appName=G-Tech"

try:
    client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)
    db = client.GTechDB
    ordenes_col = db.ordenes
except Exception as e:
    st.error("Error crítico de conexión con la base de datos.")

# 2. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="G-Tech Engineering System", layout="wide")

# 3. ESTILO CSS
st.markdown("""
    <style>
    .stApp { background-color: #f4f7f9; }
    h1 { color: #0e4b7a; font-family: 'Segoe UI'; font-weight: 700; text-align: center; }
    h3 { color: #1a5a96; border-bottom: 2px solid #1a5a96; padding-bottom: 10px; }
    .stButton>button { width: 100%; border-radius: 8px; height: 3.5em; background-color: #1a5a96; color: white; font-weight: bold; }
    [data-testid="stForm"] { background-color: white; padding: 30px; border-radius: 15px; border: 1px solid #d3d9de; }
    </style>
    """, unsafe_allow_html=True)

# 4. FUNCIONES DE APOYO

def obtener_siguiente_orden():
    """Busca el número de orden más alto y devuelve el siguiente disponible."""
    try:
        # Buscamos todas las órdenes y las ordenamos por n_orden de forma descendente
        todas = list(ordenes_col.find().sort("n_orden", -1).limit(1))
        if todas:
            # Intentamos convertir a entero para sumar 1
            ultimo_id = int(todas[0]["n_orden"])
            return str(ultimo_id + 1)
        else:
            return "1001" # Punto de partida si la DB está vacía
    except (ValueError, TypeError, IndexError):
        return "" # Si los IDs no son numéricos, dejamos que el usuario lo escriba

def generar_pdf_orden(datos):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_fill_color(14, 75, 122)
    pdf.rect(0, 0, 210, 40, 'F')
    pdf.set_font("Arial", 'B', 20)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 10, "G-TECH ENGINEERING SYSTEM", ln=True, align='C')
    pdf.ln(30)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, f"Orden de Trabajo: {datos['n_orden']}", ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    pdf.set_font("Arial", size=12)
    campos = [("Cliente:", datos['cliente']), ("Material:", datos['material']), ("Cantidad:", str(datos['cantidad']))]
    for label, value in campos:
        pdf.set_font("Arial", 'B', 12); pdf.cell(50, 10, label)
        pdf.set_font("Arial", size=12); pdf.cell(0, 10, value, ln=True)
    return pdf.output(dest='S').encode('latin-1')

def limpiar_formulario():
    st.session_state["n_orden_val"] = obtener_siguiente_orden()
    st.session_state["cliente_val"] = ""
    st.session_state["material_val"] = ""
    st.session_state["cantidad_val"] = 1

# 5. CONTROL DE NAVEGACIÓN
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

# Inicializar ID sugerido la primera vez
if "n_orden_val" not in st.session_state:
    st.session_state["n_orden_val"] = obtener_siguiente_orden()

# --- PANTALLA DE INICIO ---
if not st.session_state.autenticado:
    st.markdown("<h1 style='margin-top:100px;'>Bienvenido al sistema de G-Tech</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1.2, 1, 1.2])
    with c2:
        if st.button("INGRESAR AL SISTEMA"):
            st.session_state.autenticado = True
            st.rerun()
else:
    st.markdown("<h1>🛡️ G-TECH ENGINEERING SYSTEM</h1>", unsafe_allow_html=True)
    t1, t2, t3 = st.tabs(["📝 REGISTRO", "⚙️ TRAZABILIDAD", "📊 HISTORIAL"])

    # SECCIÓN 1: REGISTRO
    with t1:
        st.markdown("<h3>Nuevo Ingreso de Orden</h3>", unsafe_allow_html=True)
        with st.form("registro_form", clear_on_submit=False):
            ca, cb = st.columns(2)
            f_rec = ca.date_input("Fecha de recepción", value=datetime.now())
            
            # El campo de Orden ahora muestra la sugerencia automática
            id_orden = cb.text_input("Número de Orden (Sugerido)", value=st.session_state["n_orden_val"], key="n_orden_input")
            
            client_name = ca.text_input("Cliente", key="cliente_val")
            cant = cb.number_input("Cantidad", min_value=1, key="cantidad_val")
            mat = ca.text_input("Material / Especificación", key="material_val")
            f_ent = cb.date_input("Fecha de entrega estimada")
            
            st.markdown("---")
            tiene_planos = st.radio("¿Posee planos?", ["Sí", "No"], horizontal=True)
            archivo = st.file_uploader("Subir plano", type=['pdf', 'jpg', 'png'])
            
            c_b1, c_b2 = st.columns(2)
            btn_save = c_b1.form_submit_button("💾 GUARDAR REGISTRO")
            if c_b2.form_submit_button("🧹 LIMPIAR"):
                limpiar_formulario()
                st.rerun()

        if btn_save:
            if tiene_planos == "No" or archivo is None:
                st.error("❌ Documentación insuficiente (Planos obligatorios).")
            elif not id_orden or not client_name:
                st.warning("⚠️ Complete Orden y Cliente.")
            else:
                try:
                    if ordenes_col.find_one({"n_orden": id_orden}):
                        st.error(f"❌ La Orden {id_orden} ya existe.")
                    else:
                        dict_orden = {"n_orden": id_orden, "cliente": client_name, "f_recepcion": str(f_rec), "material": mat, "cantidad": cant, "entrega": str(f_ent)}
                        ordenes_col.insert_one({**dict_orden, "etapa": "Diseño", "status": "Pendiente", "historial": []})
                        st.success(f"✅ Orden {id_orden} guardada.")
                        
                        pdf_data = generar_pdf_orden(dict_orden)
                        st.download_button(label="📥 DESCARGAR PDF", data=pdf_data, file_name=f"Orden_{id_orden}.pdf", mime="application/pdf")
                        
                        # Al guardar, calculamos el siguiente número para la próxima vez
                        st.session_state["n_orden_val"] = obtener_siguiente_orden()
                except:
                    st.error("🔌 Error de conexión.")

    # SECCIONES 2 y 3 (Trazabilidad e Historial simplificadas para el ejemplo)
    with t2: st.write("Sección de Trazabilidad Activa")
    with t3: st.write("Historial de Producción Activo")
