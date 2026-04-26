# --- PANTALLA DE BIENVENIDA (Lógica corregida para centrado) ---
if not st.session_state.ingresado:
    st.write("") # Espaciador para bajar un poco el título
    st.write("") 
    st.write("")
    
    # 1. El título (Este sí se centra solo con HTML)
    st.markdown("<h1 style='text-align: center;'>Bienvenido al sistema de G-Tech</h1>", unsafe_allow_html=True)
    
    st.write("") # Espaciador entre título y botón
    
    # 2. EL TRUCO DE CENTRADO DEL BOTÓN
    # Creamos 3 columnas. La del centro (col2) será donde pondremos el botón.
    # El ratio [1, 2, 1] significa: 25% vacio | 50% botón | 25% vacío.
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Colocamos el botón en la columna central.
        # Al estar dentro de col2, se verá centrado respecto a toda la página.
        if st.button("INGRESAR AL SISTEMA"):
            st.session_state.ingresado = True
            st.rerun() # Refresca para entrar al sistema principal

else:
    # --- SISTEMA PRINCIPAL (Aquí va el resto de tu código) ---
    st.title("🛡️ Panel de Control G-TECH")
    # ... resto del código ...
