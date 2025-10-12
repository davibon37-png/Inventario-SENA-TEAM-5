def gestionar_productos():
    st.header("📦 Gestión de Productos")
    
    if st.session_state.get("user_role") == "lector":
        productos = obtener_productos()
        if productos:
            # Crear DataFrame para visualización
            df_data = []
            for p in productos:
                proveedor_nombre = "N/A"
                if 'proveedores' in p and p['proveedores']:
                    proveedor_nombre = p['proveedores'].get('nombre', 'N/A')
                
                df_data.append({
                    'id': p.get('id', 0),
                    'nombre': p.get('nombre', ''),
                    'categoria': p.get('categoria', ''),
                    'cantidad': p.get('cantidad', 0),
                    'precio': p.get('precio', 0),
                    'proveedor': proveedor_nombre
                })
            df = pd.DataFrame(df_data)
            st.dataframe(df, use_container_width=True)
            st.info("👁️ **Modo de solo lectura**")
        else:
            st.info("No hay productos registrados")
        return
    
    tab1, tab2, tab3 = st.tabs(["📋 Ver Todos", "➕ Agregar Nuevo", "✏️ Editar Productos"])
    
    with tab1:
        productos = obtener_productos()
        if productos:
            df_data = []
            for p in productos:
                proveedor_nombre = "N/A"
                if 'proveedores' in p and p['proveedores']:
                    proveedor_nombre = p['proveedores'].get('nombre', 'N/A')
                
                df_data.append({
                    'id': p.get('id', 0),
                    'nombre': p.get('nombre', ''),
                    'categoria': p.get('categoria', ''),
                    'cantidad': p.get('cantidad', 0),
                    'precio': p.get('precio', 0),
                    'proveedor': proveedor_nombre
                })
            df = pd.DataFrame(df_data)
            st.dataframe(df, use_container_width=True)
            
            csv = df.to_csv(index=False)
            st.download_button("📥 Exportar CSV", csv, "inventario.csv", "text/csv")
        else:
            st.info("No hay productos registrados")
    
    with tab2:
        st.subheader("Agregar Nuevo Producto")
        categorias = obtener_categorias()
        proveedores = obtener_proveedores()
        
        with st.form("agregar_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                nombre = st.text_input("Nombre del producto*")
                categoria = st.selectbox("Categoría*", categorias)
                precio = st.number_input("Precio (COP)*", min_value=0, value=0, step=10000)
            with col2:
                cantidad = st.number_input("Cantidad*", min_value=0, value=0)
                # Select de proveedores
                if proveedores:
                    opciones_proveedores = {f"{p['nombre']}": p['id'] for p in proveedores}
                    proveedor_seleccionado = st.selectbox("Proveedor*", options=list(opciones_proveedores.keys()))
                    provedor_id = opciones_proveedores[proveedor_seleccionado]
                else:
                    st.warning("No hay proveedores disponibles")
                    provedor_id = None
            
            if st.form_submit_button("➕ Agregar Producto"):
                if nombre and precio > 0 and provedor_id is not None:
                    if agregar_producto(nombre, cantidad, categoria, precio, provedor_id):
                        st.rerun()
                else:
                    st.error("❌ Todos los campos requeridos deben ser completados")
    
    with tab3:
        st.subheader("Editar Productos")
        productos = obtener_productos()
        proveedores = obtener_proveedores()
        
        # 🔍 BARRA DE BÚSQUEDA - AÑADIDO
        st.markdown("### 🔍 Buscar Productos")
        busqueda = st.text_input("Buscar por nombre, categoría o proveedor:", 
                               placeholder="Escribe para filtrar productos...")
        
        # Filtrar productos según la búsqueda
        productos_filtrados = productos
        if busqueda:
            busqueda_lower = busqueda.lower()
            productos_filtrados = [
                p for p in productos 
                if (busqueda_lower in p.get('nombre', '').lower() or 
                    busqueda_lower in p.get('categoria', '').lower() or 
                    ('proveedores' in p and p['proveedores'] and 
                     busqueda_lower in p['proveedores'].get('nombre', '').lower()))
            ]
        
        # Mostrar contador de resultados
        st.info(f"📊 Mostrando {len(productos_filtrados)} de {len(productos)} productos")
        
        if not productos_filtrados:
            if busqueda:
                st.warning("❌ No se encontraron productos que coincidan con la búsqueda")
            else:
                st.info("No hay productos registrados")
        else:
            for producto in productos_filtrados:
                # Obtener nombre del proveedor actual
                proveedor_actual_nombre = "N/A"
                if 'proveedores' in producto and producto['proveedores']:
                    proveedor_actual_nombre = producto['proveedores'].get('nombre', 'N/A')
                
                with st.expander(f"📦 {producto.get('nombre', 'Sin nombre')} - {proveedor_actual_nombre}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Categoría:** {producto.get('categoria', 'N/A')}")
                        st.write(f"**Stock:** {producto.get('cantidad', 0):,} uds".replace(",", "."))
                    with col2:
                        st.write(f"**Precio:** ${producto.get('precio', 0):,}".replace(",", "."))
                        st.write(f"**Proveedor:** {proveedor_actual_nombre}")
                    
                    with st.form(f"editar_{producto['id']}"):
                        nuevo_nombre = st.text_input("Nombre", value=producto.get('nombre', ''), key=f"n_{producto['id']}")
                        col1, col2 = st.columns(2)
                        with col1:
                            nueva_cantidad = st.number_input("Cantidad", value=producto.get('cantidad', 0), key=f"c_{producto['id']}")
                            nuevo_precio = st.number_input("Precio", value=producto.get('precio', 0), key=f"p_{producto['id']}")
                        with col2:
                            # Select de proveedores para edición
                            if proveedores:
                                opciones_proveedores = {f"{p['nombre']}": p['id'] for p in proveedores}
                                # Encontrar el proveedor actual
                                provedor_actual_id = producto.get('provedor_id')
                                nombre_proveedor_actual = next((p['nombre'] for p in proveedores if p['id'] == provedor_actual_id), list(opciones_proveedores.keys())[0])
                                
                                nuevo_proveedor_nombre = st.selectbox(
                                    "Proveedor", 
                                    options=list(opciones_proveedores.keys()),
                                    index=list(opciones_proveedores.keys()).index(nombre_proveedor_actual) if nombre_proveedor_actual in opciones_proveedores else 0,
                                    key=f"prov_{producto['id']}"
                                )
                                nuevo_provedor_id = opciones_proveedores[nuevo_proveedor_nombre]
                            else:
                                st.warning("No hay proveedores")
                                nuevo_provedor_id = producto.get('provedor_id')
                        
                        if st.form_submit_button("💾 Guardar"):
                            datos = {
                                "nombre": nuevo_nombre,
                                "cantidad": nueva_cantidad,
                                "precio": nuevo_precio,
                                "provedor_id": nuevo_provedor_id
                            }
                            if actualizar_producto(producto['id'], datos):
                                st.rerun()
                    
                    if st.button(f"🗑️ Eliminar", key=f"del_{producto['id']}"):
                        if eliminar_producto(producto['id']):
                            st.rerun()
