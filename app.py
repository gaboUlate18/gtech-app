import streamlit as st
from pymongo import MongoClient
import pandas as pd
from datetime import datetime
import io

# 1. CONEXIÓN A LA BASE DE DATOS
# REEMPLAZA EL LINK CON EL TUYO REAL
client = MongoClient("mongodb+srv://gtech:Ingenieria2026@g-tech.0p52gdx.mongodb.net/?appName=G-Tech")
db = client.GTechDB
ordenes_col = db.ordenes

# CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="G-Tech Engineering System", layout="wide")

# ESTILO CSS AVANZADO (DISEÑO PROFESIONAL)
st.markdown("""
    <style>
    /* Fondo y tipografía */
    .stApp { background-color: #f4f7f9; }
    
    /* Títulos y Header */
    h1 { color: #0e4b7a; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-weight: 700; text-align: center; }
    h3 { color: #1a5a96; border-bottom: 2px solid #1a5a96; padding-bottom: 10px; }
    
    /* Botones principales */
    .stButton>button { 
        width: 100%; border-radius: 8px; height: 3.5em; 
        background-color: #1a5a96; color: white; border: none;
        font-weight: bold; transition: 0.3s;
    }
    .stButton>button:hover { background-color: #0e3a63; border: none; color: white; }
    
    /* Estilo de las pestañas (Tabs) */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; justify-content: center; }
    .stTabs [data-baseweb="tab"] { 
        background-color: #e1e8ed; border-radius: 5px 5px 0 0; 
        padding: 10px 25px; font-weight: 600;
    }
    .stTabs [aria-selected="true"] { background-color: #1a5a96 !important; color: white !important; }
    
    /* Contenedores de formularios */
    [data-testid="stForm"] { 
        background-color: white; padding: 30px; 
        border-radius: 15px; border: 1px solid #d3d9de;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }

    /* Pantalla de Bienvenida */
    .welcome-container {
        display: flex; flex-direction: column; align-items: center; justify-content: center;
        height: 60vh; text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# LÓGICA DE NAVEGACIÓN
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
    # --- INTERFAZ PRINCIPAL ---
    st.markdown("<h1>🛡️ G-TECH ENGINEERING SYSTEM</h1>", unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["📝 REGISTRO DE ÓRDENES", "⚙️ TRAZABILIDAD DE ETAPAS", "📊 ÓRDENES REGISTRADAS"])

    # --- SECCIÓN 1: REGISTRO ---
    with tab1:
        st.markdown("<h3>Formulario de Recepción</h3>", unsafe_allow_html=True)
        with st.form("form_registro", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            f_recepcion = col_a.date_input("Fecha de recepción de orden", value=datetime.now())
            n_orden = col_b.text_input("Número de Orden (ID)", help="Ejemplo: GT-1001")
            
            cliente = col_a.text_input("Cliente")
            cant_piezas = col_b.number_input("Cantidad de piezas", min_value=1, step=1)
            
            material = col_a.text_input("Material / Especificación")
            f_entrega = col_b.date_input("Fecha de entrega prometida")
            
            st.markdown("---")
            planos = st.radio("¿Tiene planos del cliente?", ["Sí", "No"], horizontal=True)
            
            archivo_plano = None
            if planos == "Sí":
                archivo_plano = st.file_uploader("Adjuntar planos técnicos (Obligatorio)", type=['pdf', 'png', 'jpg'])

            if st.form_submit_button("GUARDAR ORDEN"):
                if planos == "Sí" and archivo_plano is None:
                    st.error("❌ ERROR CRÍTICO: Debe adjuntar el archivo de planos para proceder.")
                elif not n_orden or not cliente:
                    st.warning("⚠️ Campos obligatorios vacíos: Número de Orden y Cliente.")
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
                    st.success(f"✅ Orden {n_orden} registrada correctamente.")
                    
                    # Generación de PDF (Simulado)
                    pdf_data = f"G-TECH REPORT\nIngreso de Orden: {n_orden}\nCliente: {cliente}\nFecha: {f_recepcion}"
                    st.download_button("📂 Generar Comprobante de Ingreso (PDF)", data=pdf_data, file_name=f"Ingreso_{n_orden}.pdf")
                    st.rerun()

    # --- SECCIÓN 2: TRAZABILIDAD ---
    with tab2:
        st.markdown("<h3>Actualización de Producción</h3>", unsafe_allow_html=True)
        # Solo órdenes que no estén finalizadas
        pendientes = list(ordenes_col.find({"status": {"$ne": "Finalizado"}}))
        lista_n = [o["n_orden"] for o in pendientes]

        if lista_n:
            with st.form("form_update"):
                orden_sel = st.selectbox("Seleccione la Orden a actualizar", lista_n)
                etapa_nueva = st.selectbox("Nueva Etapa de Proceso", 
                                         ["Diseño", "Preparación", "Maquinado", "Rectificado", "Calidad", "Empaque", "Finalizado"])
                
                c1, c2 = st.columns(2)
                h_inicio = c1.time_input("Hora Inicio")
                h_fin = c2.time_input("Hora Fin")
                notas = st.text_area("Observaciones de Calidad / Proceso")

                if st.form_submit_button("ACTUALIZAR ETAPA"):
                    nuevo_status = "Finalizado" if etapa_nueva == "Finalizado" else "Pendiente"
                    ordenes_col.update_one(
                        {"n_orden": orden_sel},
                        {"$set": {"etapa": etapa_nueva, "status": nuevo_status},
                         "$push": {"historial": {"etapa": etapa_nueva, "inicio": str(h_inicio), "fin": str(h_fin), "nota": notas}}}
                    )
                    st.success(f"✅ Estado actualizado: {orden_sel} -> {etapa_nueva}")
                    
                    # PDF de actualización
                    reporte_etapa = f"REPORTE DE ETAPA\nOrden: {orden_sel}\nNueva Etapa: {etapa_nueva}\nStatus: {nuevo_status}"
                    st.download_button("📂 Generar Reporte de Etapa (PDF)", data=reporte_etapa, file_name=f"Trazabilidad_{orden_sel}.pdf")
                    st.rerun()
        else:
            st.info("No hay órdenes pendientes en el sistema actualmente.")

    # --- SECCIÓN 3: HISTORIAL (LA QUE TENÍA EL ERROR) ---
    with tab3:
        st.markdown("<h3>Órdenes Registradas en Sistema</h3>", unsafe_allow_html=True)
        raw_data = list(ordenes_col.find())
        
        if raw_data:
            df = pd.DataFrame(raw_data)
            
            # SOLUCIÓN AL KEYERROR: Asegurar columnas
            columnas_finales = ["n_orden", "cliente", "f_recepcion", "cantidad", "etapa", "status", "entrega"]
            for col in columnas_finales:
                if col not in df.columns:
                    df[col] = "---"

            # Ordenar y filtrar
            df_display = df[columnas_finales]
            
            # Estilo de tabla
            def highlight_status(val):
                if val == 'Finalizado': return 'background-color: #d4edda; color: #155724'
                if val == 'Pendiente': return 'background-color: #fff3cd; color: #856404'
                return ''

            st.dataframe(df_display.style.applymap(highlight_status, subset=['status']), use_container_width=True)
            
            # Botón de reporte general
            st.markdown("---")
            st.download_button("📂 Generar Reporte General de Producción (PDF)", 
                             data=df_display.to_csv(), 
                             file_name="Reporte_General_GTech.csv")
        else:
            st.warning("La base de datos está vacía.")
