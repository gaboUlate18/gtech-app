import streamlit as st
from pymongo import MongoClient
import pandas as pd
from datetime import datetime

# 1. CONEXIÓN A LA BASE DE DATOS
try:
    client = MongoClient("mongodb+srv://gtech:Ingenieria2026@g-tech.0p52gdx.mongodb.net/?appName=G-Tech", serverSelectionTimeoutMS=5000)
    db = client.GTechDB
    ordenes_col = db.ordenes
except:
    st.error("Error de conexión inicial con el servidor de datos.")

# CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="G-Tech Engineering System", layout="wide")

# ESTILO CSS
st.markdown("""
    <style>
    .stApp { background-color: #f4f7f9; }
    h1 { color: #0e4b7a; font-family: 'Segoe UI'; font-weight: 700; text-align: center; }
    h3 { color: #1a5a96; border-bottom: 2px solid #1a5a96; padding-bottom: 10px; }
    .stButton>button { width: 100%; border-radius: 8px; height: 3.5em; background-color: #1a5a96; color: white; font-weight: bold; }
    .btn-limpiar>button { background-color: #6c757d !important; } /* Gris para el botón de limpiar */
    [data-testid="stForm"] { background-color: white; padding: 30px; border-radius: 15px; border: 1px solid #d3d9de; }
    .welcome-container { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 60vh; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# MANEJO DE ESTADO DE SESIÓN PARA LIMPIEZA
if 'ingresado' not in st.session_state:
    st.session_state.ingresado = False

# Función para resetear campos
def limpiar_campos():
    st.session_state["n_orden_input"] = ""
    st.session_state["cliente_input"] = ""
    st.session_state["material_input"] = ""
    st.session_state["cant_input"] = 1

# --- PANTALLA DE BIENVENIDA ---
if not st.session_state.ingresado:
    st.markdown('<div class="welcome-container">', unsafe_allow_html=True)
    st.title("Bienvenido al sistema de G-Tech")
    st.write("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("INGRESAR AL SISTEMA"):
            st.session_state.ingresado = True
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

else:
    st.markdown("<h1>🛡️ G-TECH ENGINEERING SYSTEM</h1>", unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["📝 REGISTRO DE ÓRDENES", "⚙️ TRAZABILIDAD DE ETAPAS", "📊 ÓRDENES REGISTRADAS"])

    # --- SECCIÓN 1: REGISTRO ---
    with tab1:
        st.markdown("<h3>Formulario de Recepción</h3>", unsafe_allow_html=True)
        
        with st.form("form_registro", clear_on_submit=False):
            col_a, col_b = st.columns(2)
            f_recepcion = col_a.date_input("Fecha de recepción de orden", value=datetime.now())
            
            # Usamos keys para poder limpiar los valores después
            n_orden = col_b.text_input("Número de Orden (ID)", key="n_orden_input")
            cliente = col_a.text_input("Cliente", key="cliente_input")
            cant_piezas = col_b.number_input("Cantidad de piezas", min_value=1, step=1, key="cant_input")
            material = col_a.text_input("Material / Especificación", key="material_input")
            f_entrega = col_b.date_input("Fecha de entrega prometida")
            
            st.markdown("---")
            planos = st.radio("¿Tiene planos del cliente?", ["Sí", "No"], horizontal=True)
            archivo_plano = st.file_uploader("Adjuntar planos técnicos (Obligatorio)", type=['pdf', 'png', 'jpg'])

            # Botones del formulario
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                submit_registro = st.form_submit_button("💾 GUARDAR ORDEN")
            with col_btn2:
                # El botón de limpiar dentro de un form debe ser de tipo form_submit_button o manejarse fuera
                limpiar = st.form_submit_button("🧹 LIMPIAR FORMULARIO")

        # Lógica al presionar Limpiar
        if limpiar:
            limpiar_campos()
            st.rerun()

        # Lógica al presionar Guardar
        if submit_registro:
            if planos == "No":
                st.error("❌ ACCESO DENEGADO: No se puede registrar sin planos.")
            elif planos == "Sí" and archivo_plano is None:
                st.error("❌ ERROR: Falta adjuntar el archivo de planos.")
            elif not n_orden or not cliente:
                st.warning("⚠️ El número de orden y el cliente son obligatorios.")
            else:
                try:
                    if ordenes_col.find_one({"n_orden": n_orden}):
                        st.error(f"❌ LA ORDEN {n_orden} YA EXISTE. Evite duplicados.")
                    else:
                        nueva_orden = {
                            "n_orden": n_orden, "cliente": cliente, "f_recepcion": str(f_recepcion),
                            "material": material, "cantidad": cant_piezas, "entrega": str(f_entrega),
                            "etapa": "Diseño", "status": "Pendiente", "historial": []
                        }
                        ordenes_col.insert_one(nueva_orden)
                        st.success(f"✅ Orden {n_orden} registrada correctamente.")
                        
                        reporte = f"G-TECH REPORT\nID: {n_orden}\nCliente: {cliente}\nFecha: {f_recepcion}"
                        st.download_button("📂 DESCARGAR REPORTE", data=reporte, file_name=f"Orden_{n_orden}.txt", mime="text/plain")
                        
                        # Limpiar campos automáticamente tras un guardado exitoso
                        limpiar_campos()
                except:
                    st.error("🔌 Error de conexión con la base de datos.")

    # --- SECCIÓN 2 y 3 se mantienen igual para asegurar estabilidad ---
    with tab2:
        st.markdown("<h3>Actualización de Producción</h3>", unsafe_allow_html=True)
        try:
            pendientes = list(ordenes_col.find({"status": {"$ne": "Finalizado"}}))
            lista_n = [o["n_orden"] for o in pendientes]
            if lista_n:
                with st.form("form_update"):
                    orden_sel = st.selectbox("Seleccione la Orden", lista_n)
                    etapa_nueva = st.selectbox("Nueva Etapa", ["Diseño", "Preparación", "Maquinado", "Rectificado", "Calidad", "Empaque", "Finalizado"])
                    c1, c2 = st.columns(2)
                    h_i, h_f = c1.time_input("Hora Inicio"), c2.time_input("Hora Fin")
                    notas = st.text_area("Observaciones")
                    if st.form_submit_button("ACTUALIZAR ETAPA"):
                        nuevo_status = "Finalizado" if etapa_nueva == "Finalizado" else "Pendiente"
                        ordenes_col.update_one({"n_orden": orden_sel}, {"$set": {"etapa": etapa_nueva, "status": nuevo_status}, "$push": {"historial": {"etapa": etapa_nueva, "inicio": str(h_i), "fin": str(h_f), "nota": notas}}})
                        st.success(f"✅ {orden_sel} actualizado.")
            else: st.info("No hay órdenes pendientes.")
        except: st.error("Error en conexión.")

    with tab3:
        st.markdown("<h3>Historial de Producción</h3>", unsafe_allow_html=True)
        try:
            raw_data = list(ordenes_col.find())
            if raw_data:
                df = pd.DataFrame(raw_data)
                cols = ["n_orden", "cliente", "f_recepcion", "cantidad", "etapa", "status", "entrega"]
                for c in cols:
                    if c not in df.columns: df[c] = "---"
                def highlight_status(val):
                    if val == 'Finalizado': return 'background-color: #d4edda; color: #155724'
                    if val == 'Pendiente': return 'background-color: #fff3cd; color: #856404'
                    return ''
                st.dataframe(df[cols].style.map(highlight_status, subset=['status']), use_container_width=True)
            else: st.warning("Sin registros.")
        except: st.error("Error al cargar historial.")
