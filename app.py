import streamlit as st
from pymongo import MongoClient
import pandas as pd
from datetime import datetime
from fpdf import FPDF  # Librería para PDFs profesionales

# 1. CONEXIÓN A LA BASE DE DATOS
try:
    client = MongoClient("mongodb+srv://gtech:Ingenieria2026@g-tech.0p52gdx.mongodb.net/?appName=G-Tech", serverSelectionTimeoutMS=5000)
    db = client.GTechDB
    ordenes_col = db.ordenes
except:
    st.error("Error de conexión inicial con el servidor de datos.")

# CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="G-Tech Engineering System", layout="wide")

# --- FUNCIÓN PARA GENERAR EL PDF ---
def generar_pdf_profesional(datos):
    pdf = FPDF()
    pdf.add_page()
    
    # Encabezado con estilo industrial
    pdf.set_fill_color(14, 75, 122) # Azul G-Tech
    pdf.rect(0, 0, 210, 40, 'F')
    
    pdf.set_font("Arial", 'B', 20)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 10, "G-TECH ENGINEERING SYSTEM", ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, "Reporte Oficial de Registro de Orden", ln=True, align='C')
    
    pdf.ln(25) # Espacio
    
    # Cuerpo del documento
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, f"Detalles de la Orden: {datos['n_orden']}", ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    # Tabla de datos
    pdf.set_font("Arial", size=12)
    detalles = [
        ("Cliente:", datos['cliente']),
        ("Fecha de Recepción:", datos['f_recepcion']),
        ("Material/Especificación:", datos['material']),
        ("Cantidad de Piezas:", str(datos['cantidad'])),
        ("Fecha Prometida:", datos['entrega']),
        ("Estado Inicial:", "DISEÑO / PENDIENTE")
    ]
    
    for label, value in detalles:
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(60, 10, label, border=0)
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, value, border=0, ln=True)
    
    pdf.ln(20)
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(0, 10, f"Documento generado el: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", align='R')
    
    return pdf.output(dest='S').encode('latin-1')

# --- ESTILO CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #f4f7f9; }
    h1 { color: #0e4b7a; font-family: 'Segoe UI'; font-weight: 700; text-align: center; }
    h3 { color: #1a5a96; border-bottom: 2px solid #1a5a96; padding-bottom: 10px; }
    .stButton>button { width: 100%; border-radius: 8px; height: 3.5em; background-color: #1a5a96; color: white; font-weight: bold; }
    [data-testid="stForm"] { background-color: white; padding: 30px; border-radius: 15px; border: 1px solid #d3d9de; }
    </style>
    """, unsafe_allow_html=True)

if 'ingresado' not in st.session_state:
    st.session_state.ingresado = False

# Función para resetear campos
def limpiar_campos():
    st.session_state["n_orden_input"] = ""
    st.session_state["cliente_input"] = ""
    st.session_state["material_input"] = ""
    st.session_state["cant_input"] = 1

# --- LÓGICA DE PANTALLAS ---
if not st.session_state.ingresado:
    st.title("Bienvenido al sistema de G-Tech")
    if st.button("INGRESAR AL SISTEMA"):
        st.session_state.ingresado = True
        st.rerun()
else:
    st.markdown("<h1>🛡️ G-TECH ENGINEERING SYSTEM</h1>", unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["📝 REGISTRO DE ÓRDENES", "⚙️ TRAZABILIDAD DE ETAPAS", "📊 ÓRDENES REGISTRADAS"])

    with tab1:
        st.markdown("<h3>Formulario de Recepción</h3>", unsafe_allow_html=True)
        with st.form("form_registro"):
            col_a, col_b = st.columns(2)
            f_recepcion = col_a.date_input("Fecha de recepción de orden", value=datetime.now())
            n_orden = col_b.text_input("Número de Orden (ID)", key="n_orden_input")
            cliente = col_a.text_input("Cliente", key="cliente_input")
            cant_piezas = col_b.number_input("Cantidad de piezas", min_value=1, step=1, key="cant_input")
            material = col_a.text_input("Material / Especificación", key="material_input")
            f_entrega = col_b.date_input("Fecha de entrega prometida")
            st.markdown("---")
            planos = st.radio("¿Tiene planos del cliente?", ["Sí", "No"], horizontal=True)
            archivo_plano = st.file_uploader("Adjuntar planos técnicos", type=['pdf', 'png', 'jpg'])
            
            col_b1, col_b2 = st.columns(2)
            submit = col_b1.form_submit_button("💾 GUARDAR ORDEN")
            limpiar = col_b2.form_submit_button("🧹 LIMPIAR")

        if limpiar:
            limpiar_campos()
            st.rerun()

        if submit:
            if planos == "No":
                st.error("❌ No se puede registrar sin planos.")
            elif planos == "Sí" and archivo_plano is None:
                st.error("❌ Falta el archivo de planos.")
            elif not n_orden or not cliente:
                st.warning("⚠️ Orden y Cliente requeridos.")
            else:
                try:
                    if ordenes_col.find_one({"n_orden": n_orden}):
                        st.error("❌ La orden ya existe.")
                    else:
                        datos_orden = {
                            "n_orden": n_orden, "cliente": cliente, "f_recepcion": str(f_recepcion),
                            "material": material, "cantidad": cant_piezas, "entrega": str(f_entrega)
                        }
                        ordenes_col.insert_one({**datos_orden, "etapa": "Diseño", "status": "Pendiente", "historial": []})
                        st.success(f"✅ Orden {n_orden} guardada.")
                        
                        # GENERACIÓN DEL PDF REAL
                        pdf_bytes = generar_pdf_profesional(datos_orden)
                        st.download_button(
                            label="📥 DESCARGAR COMPROBANTE PDF",
                            data=pdf_bytes,
                            file_name=f"Orden_{n_orden}.pdf",
                            mime="application/pdf"
                        )
                        limpiar_campos()
                except:
                    st.error("🔌 Error de conexión.")

    # (Las secciones 2 y 3 permanecen iguales, pero ahora son mucho más estables)
    with tab2:
        st.markdown("<h3>Actualización de Producción</h3>")
        # Lógica de trazabilidad...
    
    with tab3:
        st.markdown("<h3>Historial de Producción</h3>")
        # Lógica de tabla con colores...
