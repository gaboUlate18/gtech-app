import streamlit as st
from pymongo import MongoClient
import pandas as pd
from datetime import datetime
import io

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
        
        # Quitamos clear_on_submit para que los datos NO se borren solos al fallar
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

            if st.form_submit_button("GUARDAR ORDEN"):
                # VALIDACIÓN ESTRICTA
                if planos == "No":
                    st.error("❌ ACCESO DENEGADO: No se puede registrar la orden sin planos. Solicite planos antes de intentar de nuevo.")
                    # Como clear_on_submit es False, los datos siguen ahí para que el usuario los corrija
                elif planos == "Sí" and archivo_plano is None:
                    st.error("❌ ERROR DE DOCUMENTACIÓN: Debe adjuntar el archivo de planos.")
                elif not n_orden or not cliente:
                    st.warning("⚠️ CAMPOS INCOMPLETOS: N° de orden y cliente son requeridos.")
                else:
                    # SI TODO ESTÁ BIEN, GUARDAMOS
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
                    st.success(f"✅ Orden {n_orden} guardada. El formulario se limpiará al realizar la siguiente acción.")
                    
                    # Generación de PDF
                    pdf_content = f"G-TECH REPORT\nIngreso: {n_orden}\nCliente: {cliente}"
                    st.download_button("📂 Descargar PDF de Ingreso", data=pdf_content, file_name=f"Ingreso_{n_orden}.pdf")
                    
                    # FORZAMOS EL REINICIO MANUAL: Solo después de un éxito rotundo
                    st.info("Haga clic en cualquier otra pestaña o refresque para ingresar una nueva orden limpia.")
                    st.rerun()

    # --- SECCIÓN 2: TRAZABILIDAD (Mantiene lógica anterior) ---
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

                if st.form_submit_button("ACTUALIZAR ETAPA"):
                    nuevo_status = "Finalizado" if etapa_nueva == "Finalizado" else "Pendiente"
                    ordenes_col.update_one(
                        {"n_orden": orden_sel},
                        {"$set": {"etapa": etapa_nueva, "status": nuevo_status},
                         "$push": {"historial": {"etapa": etapa_nueva, "inicio": str(h_inicio), "fin": str(h_fin), "nota": notas}}}
                    )
                    st.success(f"✅ {orden_sel} actualizado exitosamente.")
                    st.rerun()
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
        else:
            st.warning("Sin registros.")
