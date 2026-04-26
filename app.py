import streamlit as st
from pymongo import MongoClient
import pandas as pd
from datetime import datetime
from fpdf import FPDF

# 1. CONEXIÓN A BASE DE DATOS
# Asegúrate de colocar tu link de MongoDB Atlas aquí
MONGO_URL = "mongodb+srv://gtech:Ingenieria2026@g-tech.0p52gdx.mongodb.net/?appName=G-Tech"

try:
    client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)
    db = client.GTechDB
    ordenes_col = db.ordenes
except Exception as e:
    st.error("Error de conexión con el servidor de datos.")

# 2. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="G-Tech Engineering System", layout="wide")

# 3. FUNCIONES TÉCNICAS (Lógica de Negocio)

def obtener_siguiente_orden():
    """Busca el ID más alto y sugiere el siguiente (Poka-Yoke de duplicados)."""
    try:
        todas = list(ordenes_col.find().sort("n_orden", -1).limit(1))
        if todas:
            return str(int(todas[0]["n_orden"]) + 1)
        return "1001"
    except:
        return ""

def generar_pdf_completo(datos):
    """Genera un reporte PDF profesional con toda la información técnica."""
    pdf = FPDF()
    pdf.add_page()
    
    # Encabezado Industrial
    pdf.set_fill_color(14, 75, 122)
    pdf.rect(0, 0, 210, 45, 'F')
    pdf.set_font("Arial", 'B', 22)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 15, "G-TECH ENGINEERING SYSTEM", ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, "REPORTE TÉCNICO DE CONTROL DE CALIDAD Y PROCESOS", ln=True, align='C')
    
    pdf.ln(35)
    pdf.set_text_color(0, 0, 0)
    
    # Sección 1: Información General
    pdf.set_font("Arial", 'B', 14)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(0, 10, f" DETALLES DE LA ORDEN DE TRABAJO: {datos['n_orden']}", ln=True, fill=True)
    pdf.ln(5)
    
    pdf.set_font("Arial", size=11)
    # Tabla de datos maestros
    info = [
        ("Cliente:", datos['cliente']),
        ("Fecha de Recepción:", datos['f_recepcion']),
        ("Material / Especificación:", datos['material']),
        ("Cantidad de Piezas:", str(datos['cantidad'])),
        ("Fecha de Entrega Final:", datos['entrega']),
        ("Etapa Actual:", datos.get('etapa', 'Diseño')),
        ("Estado de Orden:", datos.get('status', 'Pendiente'))
    ]
    
    for label, val in info:
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(60, 8, label)
        pdf.set_font("Arial", size=11)
        pdf.cell(0, 8, val, ln=True)
    
    # Sección 2: Historial de Trazabilidad
    if datos.get('historial'):
        pdf.ln(10)
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, " HISTORIAL DE TRAZABILIDAD (ETAPAS)", ln=True, fill=True)
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(40, 8, "Etapa", border=1)
        pdf.cell(40, 8, "Inicio", border=1)
        pdf.cell(40, 8, "Fin", border=1)
        pdf.cell(70, 8, "Observaciones", border=1, ln=True)
        
        pdf.set_font("Arial", size=9)
        for h in datos['historial']:
            pdf.cell(40, 8, h.get('etapa', '-'), border=1)
            pdf.cell(40, 8, h.get('inicio', '-'), border=1)
            pdf.cell(40, 8, h.get('fin', '-'), border=1)
            pdf.cell(70, 8, h.get('nota', 'Sin notas'), border=1, ln=True)

    # Pie de página
    pdf.ln(20)
    pdf.set_font("Arial", 'I', 8)
    pdf.cell(0, 10, f"Documento de validez interna. Generado el: {datetime.now().strftime('%Y-%m-%d %H:%M')}", align='C')
    
    return pdf.output(dest='S').encode('latin-1')

def limpiar_campos():
    st.session_state["n_orden_form"] = obtener_siguiente_orden()
    st.session_state["cliente_form"] = ""
    st.session_state["material_form"] = ""
    st.session_state["cantidad_form"] = 1

# 4. INTERFAZ DE USUARIO (UI)
st.markdown("""
    <style>
    .stApp { background-color: #f4f7f9; }
    h1 { color: #0e4b7a; font-family: 'Segoe UI'; font-weight: 700; text-align: center; }
    h3 { color: #1a5a96; border-bottom: 2px solid #1a5a96; padding-bottom: 10px; }
    .stButton>button { width: 100%; border-radius: 8px; height: 3.5em; background-color: #1a5a96; color: white; font-weight: bold; }
    [data-testid="stForm"] { background-color: white; padding: 30px; border-radius: 15px; border: 1px solid #d3d9de; }
    </style>
    """, unsafe_allow_html=True)

if 'auth' not in st.session_state:
    st.session_state.auth = False

# --- PANTALLA DE BIENVENIDA (CENTRADA) ---
if not st.session_state.auth:
    st.write("<br><br><br>", unsafe_allow_html=True)
    st.markdown("<h1>Bienvenido al sistema de G-Tech</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1.2, 1, 1.2])
    with c2:
        if st.button("INGRESAR AL SISTEMA"):
            st.session_state.auth = True
            st.rerun()

else:
    st.markdown("<h1>🛡️ G-TECH ENGINEERING SYSTEM</h1>", unsafe_allow_html=True)
    t1, t2, t3 = st.tabs(["📝 REGISTRO DE ÓRDENES", "⚙️ TRAZABILIDAD", "📊 HISTORIAL GENERAL"])

    # SECCIÓN 1: REGISTRO
    with t1:
        st.markdown("<h3>Formulario de Recepción de Pedidos</h3>", unsafe_allow_html=True)
        if "n_orden_form" not in st.session_state:
            st.session_state["n_orden_form"] = obtener_siguiente_orden()

        with st.form("reg_form", clear_on_submit=False):
            ca, cb = st.columns(2)
            f_recep = ca.date_input("Fecha de ingreso", value=datetime.now())
            id_orden = cb.text_input("Número de Orden", value=st.session_state["n_orden_form"], key="n_orden_form")
            
            client_name = ca.text_input("Nombre del Cliente", key="cliente_form")
            qty = cb.number_input("Cantidad de piezas", min_value=1, key="cantidad_form")
            spec = ca.text_input("Material / Especificación Técnica", key="material_form")
            f_limit = cb.date_input("Fecha límite de entrega")
            
            st.markdown("---")
            docs = st.radio("¿Cuenta con planos aprobados?", ["Sí", "No"], horizontal=True)
            file = st.file_uploader("Adjuntar Plano (Requerido)", type=['pdf', 'jpg', 'png'])
            
            b1, b2 = st.columns(2)
            if b1.form_submit_button("💾 GUARDAR E IMPRIMIR"):
                if docs == "No" or file is None:
                    st.error("❌ Proceso Detenido: Se requiere el plano físico o digital para iniciar.")
                elif not id_orden or not client_name:
                    st.warning("⚠️ Datos Faltantes: Identifique la orden y el cliente.")
                else:
                    try:
                        if ordenes_col.find_one({"n_orden": id_orden}):
                            st.error(f"❌ La Orden {id_orden} ya existe.")
                        else:
                            data_master = {
                                "n_orden": id_orden, "cliente": client_name, "f_recepcion": str(f_recep),
                                "material": spec, "cantidad": qty, "entrega": str(f_limit),
                                "etapa": "Diseño", "status": "Pendiente", "historial": []
                            }
                            ordenes_col.insert_one(data_master)
                            st.success(f"✅ Orden {id_orden} registrada en base de datos.")
                            
                            pdf_bytes = generar_pdf_completo(data_master)
                            st.download_button("📥 DESCARGAR REPORTE PDF", data=pdf_bytes, file_name=f"Orden_{id_orden}.pdf", mime="application/pdf")
                            st.session_state["n_orden_form"] = obtener_siguiente_orden()
                    except:
                        st.error("🔌 Error de red con MongoDB Atlas.")
            
            if b2.form_submit_button("🧹 LIMPIAR"):
                limpiar_campos()
                st.rerun()

    # SECCIÓN 2: TRAZABILIDAD (ACTUALIZACIÓN)
    with t2:
        st.markdown("<h3>Control de Etapas de Producción</h3>", unsafe_allow_html=True)
        try:
            items = list(ordenes_col.find({"status": "Pendiente"}))
            if items:
                with st.form("upd_form"):
                    sel_id = st.selectbox("Seleccione Orden para actualizar", [i["n_orden"] for i in items])
                    ca, cb = st.columns(2)
                    et_n = ca.selectbox("Nueva Etapa", ["Maquinado", "Rectificado", "Ensamble", "Calidad", "Finalizado"])
                    h_i = ca.time_input("Hora Inicio")
                    h_f = cb.time_input("Hora Fin")
                    nota = st.text_area("Notas del operador")
                    
                    if st.form_submit_button("REGISTRAR CAMBIO DE ETAPA"):
                        st_n = "Finalizado" if et_n == "Finalizado" else "Pendiente"
                        ordenes_col.update_one(
                            {"n_orden": sel_id},
                            {"$set": {"etapa": et_n, "status": st_n},
                             "$push": {"historial": {"etapa": et_n, "inicio": str(h_i), "fin": str(h_f), "nota": nota}}}
                        )
                        st.success(f"✅ Orden {sel_id} actualizada correctamente.")
            else:
                st.info("No hay órdenes pendientes en el sistema.")
        except: st.error("Error al cargar trazabilidad.")

    # SECCIÓN 3: HISTORIAL (TABLA Y PDF FINAL)
    with t3:
        st.markdown("<h3>Historial y Reportes de Salida</h3>", unsafe_allow_html=True)
        try:
            df_raw = list(ordenes_col.find())
            if df_raw:
                df = pd.DataFrame(df_raw)
                # Mostrar tabla con colores
                def style_st(v):
                    return 'background-color: #d4edda' if v == 'Finalizado' else 'background-color: #fff3cd'
                st.dataframe(df[["n_orden", "cliente", "etapa", "status", "entrega"]].style.map(style_st, subset=['status']), use_container_width=True)
                
                st.markdown("---")
                sel_rep = st.selectbox("Seleccione una orden para generar Reporte de Trazabilidad Completo", df["n_orden"].tolist())
                if st.button("📄 GENERAR PDF DE TRAZABILIDAD"):
                    doc_data = ordenes_col.find_one({"n_orden": sel_rep})
                    pdf_final = generar_pdf_completo(doc_data)
                    st.download_button("📥 DESCARGAR PDF FINAL", data=pdf_final, file_name=f"Reporte_Completo_{sel_rep}.pdf", mime="application/pdf")
            else:
                st.warning("Sin datos registrados.")
        except: st.error("Error al generar historial.")
