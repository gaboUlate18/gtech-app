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
    return MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)

try:
    client = init_connection()
    db = client.GTechDB
    ordenes_col = db.ordenes
except:
    st.error("⚠️ Error de conexión con MongoDB Atlas. Revisa tu internet o URL.")

# --- 2. LÓGICA DE PROCESOS (BACKEND) ---

def obtener_siguiente_orden():
    """Busca el ID más alto numéricamente para sugerir el siguiente."""
    try:
        ultimo = list(ordenes_col.find().sort("n_orden", -1).limit(1))
        if ultimo:
            return str(int(ultimo[0]["n_orden"]) + 1)
        return "1001"
    except:
        return "1001"

def generar_pdf_reporte(datos):
    """Genera un PDF profesional con todos los datos y trazabilidad."""
    pdf = FPDF()
    pdf.add_page()
    
    # Encabezado corporativo G-Tech
    pdf.set_fill_color(14, 75, 122)
    pdf.rect(0, 0, 210, 45, 'F')
    pdf.set_font("Arial", 'B', 24); pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 15, "G-TECH ENGINEERING SYSTEM", ln=True, align='C')
    pdf.set_font("Arial", size=12); pdf.cell(0, 10, "REPORTE TÉCNICO DE CONTROL DE PROCESOS", ln=True, align='C')
    
    pdf.ln(35); pdf.set_text_color(0, 0, 0)
    
    # Bloque 1: Información General
    pdf.set_font("Arial", 'B', 14); pdf.set_fill_color(235, 235, 235)
    pdf.cell(0, 10, f"  DETALLES DE LA ORDEN: {datos['n_orden']}", ln=True, fill=True)
    pdf.ln(5)
    
    pdf.set_font("Arial", size=11)
    tabla_datos = [
        ("Cliente:", datos['cliente']),
        ("Fecha de Recepción:", datos['f_recepcion']),
        ("Material / Especificación:", datos['material']),
        ("Cantidad de Unidades:", str(datos['cantidad'])),
        ("Fecha Prometida de Entrega:", datos['entrega']),
        ("Estado de la Orden:", datos.get('status', 'Pendiente')),
        ("Etapa Actual:", datos.get('etapa', 'Registro'))
    ]
    
    for etiqueta, valor in tabla_datos:
        pdf.set_font("Arial", 'B', 11); pdf.cell(60, 8, etiqueta)
        pdf.set_font("Arial", size=11); pdf.cell(0, 8, valor, ln=True)
    
    # Bloque 2: Historial si existe
    if datos.get('historial'):
        pdf.ln(10)
        pdf.set_font("Arial", 'B', 14); pdf.cell(0, 10, "  TRAZABILIDAD DE PRODUCCIÓN", ln=True, fill=True)
        pdf.ln(5)
        for h in datos['historial']:
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(0, 7, f"• Etapa: {h['etapa']} | Inicio: {h['inicio']} - Fin: {h['fin']}", ln=True)
            pdf.set_font("Arial", 'I', 9)
            pdf.cell(0, 7, f"  Nota: {h['nota']}", ln=True)
            pdf.ln(2)

    pdf.ln(20)
    pdf.set_font("Arial", 'I', 8); pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 10, f"Documento generado el {datetime.now().strftime('%Y-%m-%d %H:%M')}. Validez interna G-Tech.", align='C')
    
    return pdf.output(dest='S').encode('latin-1')

def reset_completo():
    """Limpia los widgets y fuerza actualización de ID."""
    for key in list(st.session_state.keys()):
        if "form_" in key:
            del st.session_state[key]
    st.session_state.registro_ok = False
    st.session_state.id_proxima = obtener_siguiente_orden()

# --- 3. INTERFAZ Y ESTILOS (UI/UX) ---
st.set_page_config(page_title="G-Tech Engineering", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f0f2f6; }
    .main-title { color: #0e4b7a; text-align: center; font-weight: 800; font-size: 2.8rem; margin-bottom: 5px; }
    .sub-title { text-align: center; color: #555; margin-bottom: 30px; }
    
    /* Estilo de los formularios */
    div[data-testid="stForm"] {
        background-color: white; padding: 40px; border-radius: 20px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.05); border: none;
    }
    
    /* Tabs personalizadas */
    .stTabs [data-baseweb="tab-list"] { gap: 15px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #ddd; border-radius: 10px 10px 0 0; 
        padding: 10px 30px; font-weight: 600;
    }
    .stTabs [aria-selected="true"] { background-color: #0e4b7a !important; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# Inicializar estados globales
if 'auth' not in st.session_state: st.session_state.auth = False
if 'id_proxima' not in st.session_state: st.session_state.id_proxima = obtener_siguiente_orden()
if 'registro_ok' not in st.session_state: st.session_state.registro_ok = False

# --- FLUJO DE PANTALLAS ---

if not st.session_state.auth:
    st.write("<br><br><br>", unsafe_allow_html=True)
    st.markdown("<h1 class='main-title'>G-TECH ENGINEERING</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-title'>Sistema de Gestión de Procesos y Calidad</p>", unsafe_allow_html=True)
    _, col_acceso, _ = st.columns([1, 1, 1])
    if col_acceso.button("🔓 INGRESAR AL SISTEMA"):
        st.session_state.auth = True
        st.rerun()

else:
    st.markdown("<h1 class='main-title'>🛡️ Panel de Control</h1>", unsafe_allow_html=True)
    tab_reg, tab_traz, tab_hist = st.tabs(["📝 REGISTRO DE ÓRDENES", "⚙️ TRAZABILIDAD", "📊 HISTORIAL"])

    # SECCIÓN 1: REGISTRO
    with tab_reg:
        if st.session_state.registro_ok:
            st.success(f"✅ ¡ORDEN {st.session_state.ultima_orden['n_orden']} GUARDADA EXITOSAMENTE!")
            pdf_file = generar_pdf_reporte(st.session_state.ultima_orden)
            
            c1, c2 = st.columns(2)
            c1.download_button("📥 DESCARGAR COMPROBANTE PDF", data=pdf_file, 
                             file_name=f"GTech_Orden_{st.session_state.ultima_orden['n_orden']}.pdf")
            if c2.button("➕ REGISTRAR NUEVA ORDEN"):
                reset_completo()
                st.rerun()
        else:
            with st.form("form_registro"):
                st.markdown("### 📋 Datos de Recepción")
                col1, col2 = st.columns(2)
                f_recep = col1.date_input("Fecha de Ingreso", value=datetime.now())
                n_orden = col2.text_input("Número de Orden (ID)", value=st.session_state.id_proxima, key="form_n_orden")
                
                cliente = col1.text_input("Nombre del Cliente", key="form_cliente")
                cantidad = col2.number_input("Cantidad de Piezas", min_value=1, key="form_cantidad")
                material = col1.text_input("Especificación de Material", key="form_material")
                f_entrega = col2.date_input("Fecha de Entrega Compromiso")
                
                st.markdown("---")
                st.markdown("### 📐 Documentación Técnica")
                planos = st.checkbox("Confirmo que los planos técnicos han sido validados")
                archivo = st.file_uploader("Cargar plano (Requerido)", type=['pdf', 'png', 'jpg'])
                
                b_guardar, b_limpiar = st.columns(2)
                if b_guardar.form_submit_button("💾 GUARDAR E IMPRIMIR"):
                    if not planos or archivo is None:
                        st.error("❌ El sistema de calidad requiere el plano adjunto.")
                    elif not n_orden or not cliente:
                        st.warning("⚠️ Complete los campos de identificación.")
                    else:
                        try:
                            if ordenes_col.find_one({"n_orden": n_orden}):
                                st.error(f"La orden {n_orden} ya existe. Actualice el número.")
                                st.session_state.id_proxima = obtener_siguiente_orden()
                            else:
                                data = {
                                    "n_orden": n_orden, "cliente": cliente, "f_recepcion": str(f_recep),
                                    "material": material, "cantidad": cantidad, "entrega": str(f_entrega),
                                    "etapa": "Registro", "status": "Pendiente", "historial": []
                                }
                                ordenes_col.insert_one(data)
                                st.session_state.ultima_orden = data
                                st.session_state.registro_ok = True
                                st.rerun()
                        except:
                            st.error("🔌 Error de comunicación con la DB.")
                
                if b_limpiar.form_submit_button("🧹 LIMPIAR"):
                    reset_completo()
                    st.rerun()

    # SECCIÓN 2: TRAZABILIDAD
    with tab_traz:
        st.markdown("### ⚙️ Actualizar Etapa de Producción")
        try:
            activas = list(ordenes_col.find({"status": "Pendiente"}))
            if activas:
                with st.form("form_traz"):
                    sel_orden = st.selectbox("Seleccione Orden", [o["n_orden"] for o in activas])
                    c1, c2 = st.columns(2)
                    nueva_etapa = c1.selectbox("Nueva Etapa", ["Maquinado", "Rectificado", "Tratamiento", "Calidad", "Finalizado"])
                    h_ini = c1.time_input("Hora Inicio")
                    h_fin = c2.time_input("Hora Fin")
                    notas = st.text_area("Observaciones del proceso")
                    
                    if st.form_submit_button("ACTUALIZAR PROCESO"):
                        estado_final = "Finalizado" if nueva_etapa == "Finalizado" else "Pendiente"
                        ordenes_col.update_one(
                            {"n_orden": sel_orden},
                            {"$set": {"etapa": nueva_etapa, "status": estado_final},
                             "$push": {"historial": {"etapa": nueva_etapa, "inicio": str(h_ini), "fin": str(h_fin), "nota": notas}}}
                        )
                        st.success(f"Orden {sel_orden} movida a {nueva_etapa}")
                        time.sleep(1)
                        st.rerun()
            else:
                st.info("No hay órdenes pendientes para procesar.")
        except: st.error("Error al cargar datos.")

    # SECCIÓN 3: HISTORIAL
    with tab_hist:
        st.markdown("### 📊 Registro General de Órdenes")
        try:
            todo = list(ordenes_col.find())
            if todo:
                df = pd.DataFrame(todo)
                df = df[["n_orden", "cliente", "material", "etapa", "status"]]
                
                def color_status(val):
                    color = '#d4edda' if val == 'Finalizado' else '#fff3cd'
                    return f'background-color: {color}'
                
                st.dataframe(df.style.applymap(color_status, subset=['status']), use_container_width=True)
                
                st.markdown("---")
                sel_rep = st.selectbox("Ver Reporte Detallado", df["n_orden"].tolist())
                if st.button("📄 GENERAR PDF HISTÓRICO"):
                    detalles = ordenes_col.find_one({"n_orden": sel_rep})
                    st.download_button("📥 DESCARGAR REPORTE COMPLETO", 
                                     data=generar_pdf_reporte(detalles), 
                                     file_name=f"Reporte_GTech_{sel_rep}.pdf")
            else:
                st.warning("Base de datos vacía.")
        except: st.error("Error de visualización.")
