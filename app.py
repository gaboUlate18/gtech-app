import streamlit as st
from pymongo import MongoClient
import pandas as pd
from datetime import datetime

# 1. CONEXIÓN A LA BASE DE DATOS
client = MongoClient("mongodb+srv://gtech:Ingenieria2026@g-tech.0p52gdx.mongodb.net/?appName=G-Tech")
db = client.GTechDB
ordenes_col = db.ordenes

# CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="G-Tech Engineering System", layout="wide")

# ESTILO CSS
st.markdown("""
    <style>
    .stApp { background-color: #f4f7f9; }
    h1 { color: #0e4b7a; font-family: 'Segoe UI'; font-weight: 700; text-align: center; }
    h3 { color: #1a5a96; border-bottom: 2px solid #1a5a96; padding-bottom: 10px; }
    .stButton>button { width: 100%; border-radius: 8px; height: 3.5em; background-color: #1a5a96; color: white; font-weight: bold; }
    [data-testid="stForm"] { background-color: white; padding: 30px; border-radius: 15px; border: 1px solid #d3d9de; }
    .welcome-container { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 60vh; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

if 'ingresado' not in st.session_state:
    st.session_state.ingresado = False

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
        
        # El formulario se queda con clear_on_submit=False para no borrar datos si hay error
        with st.form("form_registro", clear_on_submit=False):
            col_a, col_b = st.columns(2)
            f_recepcion = col_a.date_input("Fecha de recepción de orden", value=datetime.now())
            n_orden = col_b.text_input("Número de Orden (ID)")
            cliente = col_a.text_input("Cliente")
            cant_piezas = col_b.number_input("Cantidad de piezas", min_value=1, step=1)
            material = col_a.text_input("Material / Especificación")
            f_entrega = col_b.date_input("Fecha de entrega prometida")
            st.markdown("---")
            planos = st.radio("¿Tiene planos del cliente?", ["Sí", "No"], horizontal=True)
            archivo_plano = st.file_uploader("Adjuntar planos técnicos (Obligatorio si marcó 'Sí')", type=['pdf', 'png', 'jpg'])

            submit_registro = st.form_submit_button("GUARDAR ORDEN")

        # LA LÓGICA DE GUARDADO Y EL BOTÓN DE PDF VAN AFUERA DEL FORM
        if submit_registro:
            if planos == "No":
                st.error("❌ ACCESO DENEGADO: No se puede registrar la orden sin planos. Solicite planos antes de intentar de nuevo.")
            elif planos == "Sí" and archivo_plano is None:
                st.error("❌ ERROR DE DOCUMENTACIÓN: Debe adjuntar el archivo de planos.")
            elif not n_orden or not cliente:
                st.warning("⚠️ CAMPOS INCOMPLETOS: N° de orden y cliente son requeridos.")
            else:
                nueva_orden = {
                    "n_orden": n_orden,
                    "cliente": cliente,
                    "f_recepcion": str(f_recepcion),
                    "material": material,
                    "cantidad": cant_piezas,
                    "entrega": str(f_entrega),
                    "etapa": "Diseño",
                    "status": "Pendiente",
                    "historial": []
                }
                ordenes_col.insert_one(nueva_orden)
                st.success(f"✅ Orden {n_orden} guardada exitosamente en el sistema.")
                
                # BOTÓN DE DESCARGA FUERA DEL FORM
                pdf_content = f"G-TECH REPORT\nIngreso: {n_orden}\nCliente: {cliente}\nFecha: {f_recepcion}"
                st.download_button("📂 DESCARGAR PDF DE INGRESO", data=pdf_content, file_name=f"Ingreso_{n_orden}.pdf")
                st.info("Una vez descargado el PDF, puede refrescar la página para una nueva entrada limpia.")

    # --- SECCIÓN 2: TRAZABILIDAD ---
    with tab2:
        st.markdown("<h3>Actualización de Producción</h3>", unsafe_allow_html=True)
        pendientes = list(ordenes_col.find({"status": {"$ne": "Finalizado"}}))
        lista_n = [o["n_orden"] for o in pendientes]

        if lista_n:
            with st.form("form_update"):
                orden_sel = st.selectbox("Seleccione la Orden", lista_n)
                etapa_nueva = st.selectbox("Nueva Etapa", ["Diseño", "Preparación", "Maquinado", "Rectificado", "Calidad", "Empaque", "Finalizado"])
                c1, c2 = st.columns(2)
                h_inicio = c1.time_input("Hora Inicio")
                h_fin = c2.time_input("Hora Fin")
                notas = st.text_area("Observaciones")
                submit_update = st.form_submit_button("ACTUALIZAR ETAPA")

            if submit_update:
                nuevo_status = "Finalizado" if etapa_nueva == "Finalizado" else "Pendiente"
                ordenes_col.update_one(
                    {"n_orden": orden_sel},
                    {"$set": {"etapa": etapa_nueva, "status": nuevo_status},
                     "$push": {"historial": {"etapa": etapa_nueva, "inicio": str(h_inicio), "fin": str(h_fin), "nota": notas}}}
                )
                st.success(f"✅ {orden_sel} actualizado correctamente.")
                # Botón de PDF fuera del form
                reporte_etapa = f"TRAZABILIDAD G-TECH\nOrden: {orden_sel}\nEtapa: {etapa_nueva}"
                st.download_button("📂 DESCARGAR PDF DE ETAPA", data=reporte_etapa, file_name=f"Update_{orden_sel}.pdf")
        else:
            st.info("No hay órdenes pendientes.")

    # --- SECCIÓN 3: ÓRDENES REGISTRADAS ---
    with tab3:
        st.markdown("<h3>Historial de Producción</h3>", unsafe_allow_html=True)
        raw_data = list(ordenes_col.find())
        if raw_data:
            df = pd.DataFrame(raw_data)
            columnas_finales = ["n_orden", "cliente", "f_recepcion", "cantidad", "etapa", "status", "entrega"]
            for col in columnas_finales:
                if col not in df.columns: df[col] = "---"
            
            df_display = df[columnas_finales]
            
            def highlight_status(val):
                if val == 'Finalizado': return 'background-color: #d4edda; color: #155724'
                if val == 'Pendiente': return 'background-color: #fff3cd; color: #856404'
                return ''

            st.dataframe(df_display.style.applymap(highlight_status, subset=['status']), use_container_width=True)
            
            # Botón de reporte general (Este siempre estuvo fuera del form, así que no falla)
            st.download_button("📂 GENERAR REPORTE GENERAL", data=df_display.to_csv(), file_name="Reporte_GTech.csv")
        else:
            st.warning("Sin registros.")
