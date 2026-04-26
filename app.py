import streamlit as st
from pymongo import MongoClient
import pandas as pd
from datetime import datetime
from fpdf import FPDF

# 1. CONFIGURACIÓN DE CONEXIÓN (MongoDB Atlas)
# Reemplaza con tu cadena de conexión real.
MONGO_URL = "mongodb+srv://gtech:Ingenieria2026@g-tech.0p52gdx.mongodb.net/?appName=G-Tech"

try:
    client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)
    db = client.GTechDB
    ordenes_col = db.ordenes
except Exception as e:
    st.error("Error crítico de conexión con la base de datos.")

# 2. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="G-Tech Engineering System", layout="wide")

# 3. ESTILO CSS PERSONALIZADO (UI/UX)
st.markdown("""
    <style>
    .stApp { background-color: #f4f7f9; }
    h1 { color: #0e4b7a; font-family: 'Segoe UI'; font-weight: 700; text-align: center; }
    h3 { color: #1a5a96; border-bottom: 2px solid #1a5a96; padding-bottom: 10px; }
    /* Estilo para los botones principales */
    .stButton>button { 
        width: 100%; border-radius: 8px; height: 3.5em; 
        background-color: #1a5a96; color: white; font-weight: bold; 
    }
    /* Estilo para el contenedor de bienvenida */
    .welcome-box {
        text-align: center;
        padding: 50px;
    }
    [data-testid="stForm"] { background-color: white; padding: 30px; border-radius: 15px; border: 1px solid #d3d9de; }
    </style>
    """, unsafe_allow_html=True)

# 4. FUNCIONES DE APOYO (Lógica de Negocio)

def generar_pdf_orden(datos):
    """Genera un archivo PDF con formato industrial profesional."""
    pdf = FPDF()
    pdf.add_page()
    
    # Encabezado azul
    pdf.set_fill_color(14, 75, 122)
    pdf.rect(0, 0, 210, 40, 'F')
    
    pdf.set_font("Arial", 'B', 20)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 10, "G-TECH ENGINEERING SYSTEM", ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, "Comprobante Oficial de Registro de Orden", ln=True, align='C')
    
    pdf.ln(30)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, f"Orden de Trabajo: {datos['n_orden']}", ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    # Datos de la orden
    pdf.set_font("Arial", size=12)
    campos = [
        ("Cliente:", datos['cliente']),
        ("Fecha Recepción:", datos['f_recepcion']),
        ("Material:", datos['material']),
        ("Cantidad:", str(datos['cantidad'])),
        ("Fecha Entrega:", datos['entrega'])
    ]
    
    for label, value in campos:
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(50, 10, label)
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, value, ln=True)
    
    pdf.ln(20)
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(0, 10, f"Generado automáticamente por sistema G-Tech el {datetime.now().strftime('%Y-%m-%d')}", align='C')
    
    return pdf.output(dest='S').encode('latin-1')

def limpiar_formulario():
    """Resetea los valores de los campos en el estado de sesión."""
    st.session_state["n_orden"] = ""
    st.session_state["cliente"] = ""
    st.session_state["material"] = ""
    st.session_state["cantidad"] = 1

# 5. CONTROL DE NAVEGACIÓN
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

# --- PANTALLA DE INICIO (CENTRADO CORREGIDO) ---
if not st.session_state.autenticado:
    st.markdown("<div class='welcome-box'>", unsafe_allow_html=True)
    st.markdown("<h1>Bienvenido al sistema de G-Tech</h1>", unsafe_allow_html=True)
    st.write("---")
    
    # Columnas para centrar el botón: [Izquierda, Centro, Derecha]
    # El ratio [1.2, 1, 1.2] hace que la columna del medio sea el foco central
    c1, c2, c3 = st.columns([1.2, 1, 1.2])
    with c2:
        if st.button("INGRESAR AL SISTEMA"):
            st.session_state.autenticado = True
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# --- SISTEMA PRINCIPAL ---
else:
    st.markdown("<h1>🛡️ G-TECH ENGINEERING SYSTEM</h1>", unsafe_allow_html=True)
    t1, t2, t3 = st.tabs(["📝 REGISTRO", "⚙️ TRAZABILIDAD", "📊 HISTORIAL"])

    # SECCIÓN 1: REGISTRO DE ÓRDENES
    with t1:
        st.markdown("<h3>Nuevo Ingreso de Orden</h3>", unsafe_allow_html=True)
        with st.form("registro_form", clear_on_submit=False):
            ca, cb = st.columns(2)
            f_rec = ca.date_input("Fecha de recepción", value=datetime.now())
            id_orden = cb.text_input("Número de Orden (ID)", key="n_orden")
            client_name = ca.text_input("Cliente", key="cliente")
            cant = cb.number_input("Cantidad", min_value=1, key="cantidad")
            mat = ca.text_input("Material / Especificación", key="material")
            f_ent = cb.date_input("Fecha de entrega estimada")
            
            st.markdown("---")
            tiene_planos = st.radio("¿Posee documentación técnica / planos?", ["Sí", "No"], horizontal=True)
            archivo = st.file_uploader("Subir plano (Obligatorio)", type=['pdf', 'jpg', 'png'])
            
            col_b1, col_b2 = st.columns(2)
            btn_save = col_b1.form_submit_button("💾 GUARDAR REGISTRO")
            btn_clear = col_b2.form_submit_button("🧹 LIMPIAR CAMPOS")

        if btn_clear:
            limpiar_formulario()
            st.rerun()

        if btn_save:
            # Validaciones de Seguridad (Poka-Yoke)
            if tiene_planos == "No":
                st.error("❌ Error de Proceso: No se permite el ingreso sin planos técnicos.")
            elif tiene_planos == "Sí" and archivo is None:
                st.error("❌ Error de Documentación: Debe adjuntar el archivo para validar el diseño.")
            elif not id_orden or not client_name:
                st.warning("⚠️ Información Incompleta: Identificación de orden y cliente requeridos.")
            else:
                try:
                    # Evitar duplicados en base de datos
                    if ordenes_col.find_one({"n_orden": id_orden}):
                        st.error(f"❌ La Orden {id_orden} ya existe. Use un ID único.")
                    else:
                        dict_orden = {
                            "n_orden": id_orden, "cliente": client_name, "f_recepcion": str(f_rec),
                            "material": mat, "cantidad": cant, "entrega": str(f_ent)
                        }
                        # Guardar con estado inicial
                        ordenes_col.insert_one({**dict_orden, "etapa": "Diseño", "status": "Pendiente", "historial": []})
                        st.success(f"✅ Orden {id_orden} guardada exitosamente.")
                        
                        # Generación inmediata del PDF Real
                        pdf_data = generar_pdf_orden(dict_orden)
                        st.download_button(
                            label="📥 DESCARGAR COMPROBANTE PDF",
                            data=pdf_data,
                            file_name=f"GTech_Orden_{id_orden}.pdf",
                            mime="application/pdf"
                        )
                        limpiar_formulario()
                except Exception:
                    st.error("🔌 Fallo de comunicación con el servidor de datos.")

    # SECCIÓN 2: TRAZABILIDAD (Mismo manejo de errores)
    with t2:
        st.markdown("<h3>Actualización de Estado de Producción</h3>", unsafe_allow_html=True)
        try:
            pendientes = list(ordenes_col.find({"status": "Pendiente"}))
            ids_pendientes = [o["n_orden"] for o in pendientes]
            if ids_pendientes:
                with st.form("update_form"):
                    sel = st.selectbox("Seleccione Orden", ids_pendientes)
                    nueva_et = st.selectbox("Mover a Etapa", ["Preparación", "Maquinado", "Rectificado", "Calidad", "Finalizado"])
                    obs = st.text_area("Notas de Producción")
                    if st.form_submit_button("ACTUALIZAR PROCESO"):
                        st_fin = "Finalizado" if nueva_et == "Finalizado" else "Pendiente"
                        ordenes_col.update_one(
                            {"n_orden": sel},
                            {"$set": {"etapa": nueva_et, "status": st_fin},
                             "$push": {"historial": {"etapa": nueva_et, "fecha": str(datetime.now()), "nota": obs}}}
                        )
                        st.success(f"Orden {sel} movida a {nueva_et}.")
            else:
                st.info("No hay órdenes activas en el taller.")
        except:
            st.error("Error al cargar trazabilidad.")

    # SECCIÓN 3: HISTORIAL (Visual Management)
    with t3:
        st.markdown("<h3>Control Visual de Órdenes</h3>", unsafe_allow_html=True)
        try:
            data = list(ordenes_col.find())
            if data:
                df = pd.DataFrame(data)
                df = df[["n_orden", "cliente", "f_recepcion", "etapa", "status"]]
                
                def color_status(val):
                    color = '#d4edda' if val == 'Finalizado' else '#fff3cd'
                    return f'background-color: {color}'
                
                st.dataframe(df.style.map(color_status, subset=['status']), use_container_width=True)
            else:
                st.warning("La base de datos está vacía.")
        except:
            st.error("Error al visualizar historial.")
