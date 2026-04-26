import streamlit as st
from pymongo import MongoClient
import pandas as pd
from datetime import datetime

# 1. CONEXIÓN A LA BASE DE DATOS
client = MongoClient("TU_LINK_DE_MONGODB_AQUI")
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

# LÓGICA DE ESTADO DE SESIÓN
if 'ingresado' not in st.session_state:
    st.session_state.ingresado = False
if 'orden_guardada' not in st.session_state:
    st.session_state.orden_guardada = False

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
            n_orden = col_b.text_input("Número de Orden (ID)")
            cliente = col_a.text_input("Cliente")
            cant_piezas = col_b.number_input("Cantidad de piezas", min_value=1, step=1)
            material = col_a.text_input("Material / Especificación")
            f_entrega = col_b.date_input("Fecha de entrega prometida")
            st.markdown("---")
            planos = st.radio("¿Tiene planos del cliente?", ["Sí", "No"], horizontal=True)
            archivo_plano = st.file_uploader("Adjuntar planos técnicos (Obligatorio)", type=['pdf', 'png', 'jpg'])

            submit_registro = st.form_submit_button("GUARDAR ORDEN")

        if submit_registro:
            # 1. Verificar si ya se guardó para evitar duplicados
            if ordenes_col.find_one({"n_orden": n_orden}) and n_orden != "":
                st.error(f"❌ LA ORDEN {n_orden} YA EXISTE EN EL SISTEMA. No se pueden duplicar registros.")
            elif planos == "No":
                st.error("❌ ACCESO DENEGADO: No se puede registrar sin planos.")
            elif planos == "Sí" and archivo_plano is None:
                st.error("❌ ERROR: Falta adjuntar el archivo de planos.")
            elif not n_orden or not cliente:
                st.warning("⚠️ El número de orden y el cliente son obligatorios.")
            else:
                # Guardar en DB
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
                st.session_state.orden_guardada = True
                st.success(f"✅ Orden {n_orden} registrada con éxito.")
                
                # Generar contenido del reporte (PDF/TXT seguro)
                reporte = f"""
                G-TECH ENGINEERING SYSTEM
                REPORTE DE INGRESO DE ORDEN
                ---------------------------
                Orden ID: {n_orden}
                Cliente: {cliente}
                Fecha Recepción: {f_recepcion}
                Cantidad: {cant_piezas}
                Material: {material}
                Fecha Entrega: {f_entrega}
                ---------------------------
                Estado: Registrada en Firme
                """
                
                # Botón de descarga con formato de texto (evita el error de apertura)
                st.download_button(
                    label="📂 DESCARGAR REPORTE DE INGRESO",
                    data=reporte,
                    file_name=f"Orden_{n_orden}.txt",
                    mime="text/plain"
                )
                st.info("💡 Para limpiar el formulario e ingresar una nueva orden, refresque la página o cambie de pestaña.")

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
                st.success(f"✅ Etapa actualizada para {orden_sel}.")
                
                # Reporte de trazabilidad
                rep_traza = f"TRAZABILIDAD G-TECH\nOrden: {orden_sel}\nNueva Etapa: {etapa_nueva}\nStatus: {nuevo_status}"
                st.download_button("📂 DESCARGAR ACTUALIZACIÓN", data=rep_traza, file_name=f"Update_{orden_sel}.txt", mime="text/plain")
        else:
            st.info("No hay órdenes pendientes.")

    # --- SECCIÓN 3: HISTORIAL ---
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

            try:
                st.dataframe(df_display.style.map(highlight_status, subset=['status']), use_container_width=True)
            except:
                st.dataframe(df_display.style.applymap(highlight_status, subset=['status']), use_container_width=True)
            
            st.download_button("📂 GENERAR REPORTE GENERAL", data=df_display.to_csv(index=False), file_name="Reporte_GTech.csv")
        else:
            st.warning("Sin registros.")
