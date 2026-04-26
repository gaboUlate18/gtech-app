import streamlit as st
from pymongo import MongoClient
import pandas as pd
from datetime import datetime
import io

# 1. CONEXIÓN (Asegúrate de que tu link sea el correcto con tu contraseña)
client = MongoClient("mongodb+srv://gtech:Ingenieria2026@g-tech.0p52gdx.mongodb.net/?appName=G-Tech")
db = client.GTechDB
ordenes_col = db.ordenes

# CONFIGURACIÓN PROFESIONAL
st.set_page_config(page_title="G-Tech Engineering", layout="centered")

# ESTILO PERSONALIZADO (Colores y Centrado)
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #007bff; color: white; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; justify-content: center; }
    div.stButton { text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# PANTALLA DE BIENVENIDA CENTRADA
if 'ingresado' not in st.session_state:
    st.session_state.ingresado = False

if not st.session_state.ingresado:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.write("") # Espaciado
        st.write("")
        st.image("https://cdn-icons-png.flaticon.com/512/4252/4252440.png", width=100) # Icono industrial genérico
        st.title("Bienvenido al sistema de G-Tech")
        st.subheader("Gestión de Procesos y Calidad")
        if st.button("INGRESAR AL SISTEMA"):
            st.session_state.ingresado = True
            st.rerun()
else:
    # SISTEMA PRINCIPAL
    st.title("🛡️ G-TECH Engineering")
    
    # Pestañas: Registro, Trazabilidad, y la nueva "Órdenes Registradas"
    tab1, tab2, tab3 = st.tabs(["📝 Registro", "⚙️ Trazabilidad", "📊 Órdenes Registradas"])

    # --- TAB 1: REGISTRO ---
    with tab1:
        st.subheader("Nueva Orden de Trabajo")
        with st.form("form_orden", clear_on_submit=True): # clear_on_submit reinicia los campos
            f_recepcion = st.date_input("Fecha de recepción de orden")
            col1, col2 = st.columns(2)
            n_orden = col1.text_input("Número de Orden")
            cliente = col2.text_input("Cliente")
            material = col1.text_input("Material")
            cant_piezas = col2.number_input("Cantidad de piezas", min_value=1)
            entrega = st.date_input("Fecha de entrega prometida")
            
            planos = st.radio("¿Tiene planos del cliente?", ["Sí", "No"], horizontal=True)
            
            # Requisito obligatorio de adjuntar archivo si dice "Sí"
            archivo_plano = None
            if planos == "Sí":
                archivo_plano = st.file_uploader("Adjuntar planos (PDF, PNG, JPG)", type=['pdf', 'png', 'jpg'])

            if st.form_submit_button("Guardar Orden"):
                if planos == "Sí" and archivo_plano is None:
                    st.error("ERROR: Si tiene planos, debe adjuntar el archivo obligatoriamente.")
                else:
                    nueva_orden = {
                        "n_orden": n_orden,
                        "cliente": cliente,
                        "f_recepcion": str(f_recepcion),
                        "material": material,
                        "cantidad": cant_piezas,
                        "entrega": str(entrega),
                        "etapa": "Diseño",
                        "status": "Pendiente",
                        "historial": []
                    }
                    ordenes_col.insert_one(nueva_orden)
                    st.success(f"Orden {n_orden} guardada. Generando reporte inicial...")
                    # Simulación de generación de PDF inicial
                    st.download_button("Descargar PDF de Nueva Orden", data="Contenido del reporte...", file_name=f"Orden_{n_orden}.pdf")
                    st.rerun() # Refresca para limpiar y actualizar

    # --- TAB 2: TRAZABILIDAD ---
    with tab2:
        st.subheader("Actualización de Trazabilidad")
        lista_ordenes = [o["n_orden"] for o in ordenes_col.find({"status": "Pendiente"})]
        
        if lista_ordenes:
            with st.form("form_actualizar"):
                orden_sel = st.selectbox("Seleccione la Orden", lista_ordenes)
                etapa_nueva = st.selectbox("Nueva Etapa", ["Diseño", "Preparación", "Maquinado", "Calidad", "Empaque", "Finalizado"])
                h_inicio = st.time_input("Hora Inicio")
                h_fin = st.time_input("Hora Fin")
                
                if st.form_submit_button("Actualizar etapa"):
                    nuevo_status = "Finalizado" if etapa_nueva == "Finalizado" else "Pendiente"
                    ordenes_col.update_one(
                        {"n_orden": orden_sel},
                        {"$set": {"etapa": etapa_nueva, "status": nuevo_status}}
                    )
                    st.success(f"Actualizado: {orden_sel} -> {etapa_nueva}")
                    st.download_button("Descargar Comprobante de Etapa", data="Contenido...", file_name=f"Etapa_{orden_sel}.pdf")
                    st.rerun() # Refresca automáticamente al dar clic
        else:
            st.info("No hay órdenes pendientes para actualizar.")

    # --- TAB 3: ÓRDENES REGISTRADAS ---
    with tab3:
        st.subheader("Historial de Producción")
        data = list(ordenes_col.find())
        if data:
            df = pd.DataFrame(data)
            # Formateo visual del status
            df = df[["n_orden", "cliente", "etapa", "status", "entrega"]]
            st.dataframe(df.style.map(lambda x: 'color: green' if x == 'Finalizado' else ('color: orange' if x == 'Pendiente' else ''), subset=['status']), use_container_width=True)
            
            st.download_button("Generar Reporte General (PDF/Excel)", data="Lista completa...", file_name="reporte_general_gtech.pdf")
        else:
            st.warning("No hay registros en la base de datos.")
