import streamlit as st
from pymongo import MongoClient
import pandas as pd
from datetime import datetime

# 1. CONEXIÓN A LA BASE DE DATOS
# REEMPLAZA ESTE LINK CON EL TUYO DE MONGODB
client = MongoClient("mongodb+srv://gtech:Ingenieria2026@g-tech.0p52gdx.mongodb.net/?appName=G-Tech")
db = client.GTechDB
ordenes_col = db.ordenes

# CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(page_title="G-Tech Engineering", layout="wide")

# PANTALLA DE BIENVENIDA
if 'ingresado' not in st.session_state:
    st.session_state.ingresado = False

if not st.session_state.ingresado:
    st.title("BIENVENIDO A G-TECH")
    st.subheader("Soluciones de Ingeniería y Calidad")
    if st.button("INGRESAR AL SISTEMA"):
        st.session_state.ingresado = True
        st.rerun()
else:
    # EL SISTEMA UNA VEZ DENTRO
    st.title("G-TECH: Panel de Control")
    tab1, tab2 = st.tabs(["Registro de Órdenes", "Trazabilidad de Etapas"])

    # --- TAB 1: REGISTRO ---
    with tab1:
        st.header("Nueva Orden de Trabajo")
        with st.form("form_orden"):
            col1, col2 = st.columns(2)
            n_orden = col1.text_input("Número de Orden")
            cliente = col2.text_input("Cliente")
            material = col1.text_input("Material")
            cantidad = col2.number_input("Cantidad", min_value=1)
            entrega = st.date_input("Fecha de Entrega")
            
            planos = st.radio("¿Tiene planos del cliente?", ["Seleccione", "Sí", "No"])
            
            if st.form_submit_button("Guardar Orden"):
                if planos == "No":
                    st.error("ADVERTENCIA: Se requiere diseñar planos del cliente.")
                elif planos == "Seleccione":
                    st.warning("Por favor indique si tiene planos.")
                else:
                    nueva_orden = {
                        "n_orden": n_orden,
                        "cliente": cliente,
                        "material": material,
                        "cantidad": cantidad,
                        "entrega": str(entrega),
                        "etapa": "Diseño",
                        "historial": []
                    }
                    ordenes_col.insert_one(nueva_orden)
                    st.success(f"Orden {n_orden} guardada con éxito.")

        st.divider()
        st.subheader("Órdenes Registradas")
        data = list(ordenes_col.find({}, {"_id": 0}))
        if data:
            st.table(pd.DataFrame(data)[["n_orden", "cliente", "etapa"]])

    # --- TAB 2: TRAZABILIDAD ---
    with tab2:
        st.header("Actualizar Etapa de Producto")
        lista_ordenes = [o["n_orden"] for o in ordenes_col.find()]
        
        if lista_ordenes:
            orden_sel = st.selectbox("Seleccione la Orden", lista_ordenes)
            etapa = st.selectbox("Nueva Etapa", ["Diseño", "Preparación", "Maquinado", "Rectificado", "Calidad", "Empaque"])
            h_inicio = st.time_input("Hora Inicio")
            h_fin = st.time_input("Hora Fin")
            comentario = st.text_area("Comentarios")
            
            if st.button("Actualizar Etapa"):
                ordenes_col.update_one(
                    {"n_orden": orden_sel},
                    {"$set": {"etapa": etapa}}
                )
                st.success(f"La orden {orden_sel} ahora está en etapa: {etapa}")
        else:
            st.info("No hay órdenes registradas aún.")
