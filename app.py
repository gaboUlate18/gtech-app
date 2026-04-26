import streamlit as st
from pymongo import MongoClient
import pandas as pd
from datetime import datetime

# 1. CONEXIÓN A LA BASE DE DATOS
# REEMPLAZA EL LINK CON TU CADENA DE CONEXIÓN REAL
client = MongoClient("mongodb+srv://gtech:Ingenieria2026@g-tech.0p52gdx.mongodb.net/?appName=G-Tech")
db = client.GTechDB
ordenes_col = db.ordenes

# CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="G-Tech Engineering System", layout="wide")

# ESTILO CSS AVANZADO
st.markdown("""
    <style>
    .stApp { background-color: #f4f7f9; }
    h1 { color: #0e4b7a; font-family: 'Segoe UI'; font-weight: 700; text-align: center; }
    h3 { color: #1a5a96; border-bottom: 2px solid #1a5a96; padding-bottom: 10px; }
    .stButton>button { 
        width: 100%; border-radius: 8px; height: 3.5em; 
        background-color: #1a5a96; color: white; font-weight: bold;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; justify-content: center; }
    .stTabs [aria-selected="true"] { background-color: #1a5a96 !important; color: white !important; }
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
        
        # clear_on_submit=False para que los datos permanezcan si hay un error de validación
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

        # Lógica de validación fuera del formulario para permitir st.download_button
        if submit_registro:
            if planos == "No":
                st.error("❌ ACCESO DENEGADO: No se puede registrar la orden sin planos. Se requiere documentación técnica para iniciar el proceso.")
            elif planos == "Sí" and archivo_plano is None:
                st.error("❌ ERROR DE DOCUMENTACIÓN: Ha indicado que tiene planos pero no ha adjuntado el archivo.")
            elif not n_orden or not cliente:
                st.warning("⚠️ CAMPOS REQUERIDOS: El número de orden y el nombre del cliente son obligatorios.")
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
                st.success(f"✅ Orden {n_orden} guardada correctamente.")
                
                # Botón de descarga (ahora funciona porque está fuera del st.form)
                pdf_resumen = f"REPORTE DE INGRESO G-TECH\nOrden: {n_orden}\nCliente: {cliente}\nFecha: {f_recepcion}\nCant: {cant_piezas}"
                st.download_button("📂 DESCARGAR PDF DE INGRESO", data=pdf_resumen, file_name=f"Ingreso_{n_orden}.pdf")
                st.info("Nota: Los datos se mantendrán en pantalla hasta que refresque o cambie de sección.")

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
                notas = st.text_area("Observaciones de Proceso")
                submit_update = st.form_submit_button("ACTUALIZAR ETAPA")

            if submit_update:
                nuevo_status = "Finalizado" if etapa_nueva == "Finalizado" else "Pendiente"
                ordenes_col.update_one(
                    {"n_orden": orden_sel},
                    {"$set": {"etapa": etapa_nueva, "status": nuevo_status},
                     "$push": {"historial": {"etapa": etapa_nueva, "inicio": str(h_inicio), "fin": str(h_fin), "nota": notas}}}
                )
                st.success(f"✅ Etapa '{etapa_nueva}' registrada para la orden {orden_sel}.")
                
                pdf_etapa = f"TRAZABILIDAD G-TECH\nOrden: {orden_sel}\nEtapa Actualizada: {etapa_nueva}\nStatus: {nuevo_status}"
                st.download_button("📂 DESCARGAR PDF DE ACTUALIZACIÓN", data=pdf_etapa, file_name=f"Trazabilidad_{orden_sel}.pdf")
        else:
            st.info("No existen órdenes pendientes de finalización.")

    # --- SECCIÓN 3: ÓRDENES REGISTRADAS (Pestaña aparte) ---
    with tab3:
        st.markdown("<h3>Historial de Producción</h3>", unsafe_allow_html=True)
        raw_data = list(ordenes_col.find())
        
        if raw_data:
            df = pd.DataFrame(raw_data)
            columnas_finales = ["n_orden", "cliente", "f_recepcion", "cantidad", "etapa", "status", "entrega"]
            
            # Asegurar que no falten columnas por registros viejos
            for col in columnas_finales:
                if col not in df.columns:
                    df[col] = "---"
            
            df_display = df[columnas_finales]
            
            def highlight_status(val):
                if val == 'Finalizado': return 'background-color: #d4edda; color: #155724' # Verde claro
                if val == 'Pendiente': return 'background-color: #fff3cd; color: #856404' # Amarillo claro
                return ''

            # Uso de .map() para compatibilidad con versiones nuevas de Pandas
            try:
                st.dataframe(df_display.style.map(highlight_status, subset=['status']), use_container_width=True)
            except AttributeError:
                st.dataframe(df_display.style.applymap(highlight_status, subset=['status']), use_container_width=True)
            
            st.markdown("---")
            st.download_button("📂 GENERAR REPORTE GENERAL (CSV)", data=df_display.to_csv(index=False), file_name="Reporte_General_GTech.csv")
        else:
            st.warning("No se encontraron registros en la base de datos.")
