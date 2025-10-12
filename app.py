import streamlit as st
from utils.supabase_client import get_supabase_client
import pandas as pd
from datetime import datetime

# Configuración de la página
st.set_page_config(page_title="Sistema de Inventario", layout="wide")

# ================== 🎯 USUARIOS ==================
USUARIOS = {
    "david": {"password": "david123", "rol": "admin"},
    "briget": {"password": "briget123", "rol": "admin"},
    "brian": {"password": "brian123", "rol": "admin"},
    "ivan": {"password": "ivan123", "rol": "admin"},
    "lector": {"password": "lector123", "rol": "lector"},
    "invitado": {"password": "invitado123", "rol": "lector"}
}

# ================== 🔧 FUNCIONES BASE DE DATOS ==================

def obtener_proveedores():
    """Obtener lista de proveedores desde la base de datos"""
    try:
        response = supabase.table("proveedores").select("id, nombre").execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Error al obtener proveedores: {e}")
        return []

def obtener_productos():
    """Obtener productos con información de proveedores"""
    try:
        response = supabase.table("inventario").select("*, proveedores!inner(nombre)").execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Error al obtener productos: {e}")
        # Fallback: obtener sin join
        try:
            response = supabase.table("inventario").select("*").execute()
            return response.data if response.data else []
        except:
            return []

def obtener_categorias():
    """Obtener categorías únicas de productos"""
    try:
        response = supabase.table("inventario").select("categoria").execute()
        if response.data:
            categorias = list(set([item['categoria'] for item in response.data if item.get('categoria')]))
            return sorted([cat for cat in categorias if cat])
        return ["Tecnología", "Mobiliario", "Accesorios", "Insumos"]
    except:
        return ["Tecnología", "Mobiliario", "Accesorios", "Insumos"]

def agregar_producto(nombre, cantidad, categoria, precio, provedor_id):
    """Agregar nuevo producto usando provedor_id"""
    try:
        # Obtener máximo ID
        max_response = supabase.table("inventario").select("id").order("id", desc=True).limit(1).execute()
        next_id = max_response.data[0]['id'] + 1 if max_response.data else 1

        producto_data = {
            "id": next_id,
            "nombre": nombre.strip(),
            "categoria": categoria,
            "precio": precio,
            "cantidad": cantidad,
            "provedor_id": provedor_id,
            "fecha_actualizacion": datetime.now().isoformat()
        }
        
        response = supabase.table("inventario").insert(producto_data).execute()
        return bool(response.data)
    except Exception as e:
        st.error(f"Error al agregar producto: {e}")
        return False

def actualizar_producto(producto_id, datos):
    """Actualizar producto"""
    try:
        datos['fecha_actualizacion'] = datetime.now().isoformat()
        response = supabase.table("inventario").update(datos).eq("id", producto_id).execute()
        return True
    except Exception as e:
        st.error(f"Error al actualizar: {e}")
        return False

def eliminar_producto(producto_id):
    """Eliminar producto"""
    try:
        response = supabase.table("inventario").delete().eq("id", producto_id).execute()
        return True
    except Exception as e:
        st.error(f"Error al eliminar: {e}")
        return False

def insertar_datos_ejemplo():
    """Insertar datos de ejemplo usando provedor_id"""
    try:
        productos = obtener_productos()
        if not productos:
            # Usar provedor_id = 1 (HP Inc.) para todos los productos de ejemplo
            datos_ejemplo = [
                {"nombre": "Laptop HP Pavilion", "cantidad": 15, "categoria": "Tecnología", "provedor_id": 1, "precio": 3500000},
                {"nombre": "Mouse Inalámbrico", "cantidad": 50, "categoria": "Accesorios", "provedor_id": 2, "precio": 120000},
                {"nombre": "Monitor 24 Pulgadas", "cantidad": 8, "categoria": "Tecnología", "provedor_id": 3, "precio": 850000},
                {"nombre": "Silla de Oficina", "cantidad": 12, "categoria": "Mobiliario", "provedor_id": 4, "precio": 450000},
            ]
            for producto in datos_ejemplo:
                supabase.table("inventario").insert(producto).execute()
            return True
    except Exception as e:
        st.error(f"Error insertando datos: {e}")
    return False

# ================== 🔐 AUTENTICACIÓN ==================

def check_password():
    if st.session_state.get("password_correct"):
        return True
        
    st.title("🔐 Iniciar Sesión - Sistema de Inventario")
    st.markdown("---")
    
    with st.form("login_form"):
        username = st.text_input("👤 Usuario")
        password = st.text_input("🔒 Contraseña", type="password")
        submitted = st.form_submit_button("🚀 Ingresar al Sistema")
        
        if submitted:
            username_lower = username.strip().lower()
            if username_lower in USUARIOS and password == USUARIOS[username_lower]["password"]:
                st.session_state["password_correct"] = True
                st.session_state["user_role"] = USUARIOS[username_lower]["rol"]
                st.session_state["current_user"] = username_lower
                st.success(f"✅ ¡Bienvenido/a {username.title()}!")
                st.rerun()
            else:
                st.error("❌ Usuario o contraseña incorrectos")
    
    with st.expander("📋 Usuarios de Prueba"):
        st.write("**Administradores:** david/david123, briget/briget123")
        st.write("**Lectores:** lector/lector123, invitado/invitado123")
    
    return False

def tiene_permiso(permiso_requerido):
    roles_permisos = {
        "lector": ["ver"],
        "admin": ["ver", "agregar", "editar", "eliminar", "admin"]
    }
    user_role = st.session_state.get("user_role", "lector")
    return permiso_requerido in roles_permisos.get(user_role, ["ver"])

# ================== 🎨 INTERFAZ ==================

def main():
    if not check_password():
        return
        
    global supabase
    supabase = get_supabase_client()
    
    if 'inicializado' not in st.session_state:
        insertar_datos_ejemplo()
        st.session_state.inicializado = True
    
    # Sidebar
    with st.sidebar:
        user = st.session_state.get("current_user", "usuario").title()
        rol = st.session_state.get("user_role", "lector")
        st.success(f"👤 {user} ({rol})")
        
        if st.button("🚪 Cerrar Sesión"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        
        st.header("🔧 Navegación")
        opciones = ["📊 Dashboard", "📦 Productos", "📈 Reportes"]
        if tiene_permiso("admin"):
            opciones.append("⚙️ Administración")
        opcion = st.radio("Menú", opciones)
        
        st.markdown("---")
        st.info("💰 **Moneda:** Pesos Colombianos (COP)")
    
    # Contenido principal
    if opcion == "📊 Dashboard":
        mostrar_dashboard()
    elif opcion == "📦 Productos":
        gestionar_productos()
    elif opcion == "📈 Reportes":
        mostrar_reportes()
    elif opcion == "⚙️ Administración":
        mostrar_administracion()

def mostrar_dashboard():
    st.header("📊 Dashboard de Inventario")
    
    productos = obtener_productos()
    if not productos:
        st.warning("No hay productos en el inventario")
        return
    
    # Crear DataFrame seguro
    df_data = []
    for p in productos:
        # Manejar proveedor (puede venir de la relación)
        proveedor_nombre = "N/A"
        if 'proveedores' in p and p['proveedores']:
            proveedor_nombre = p['proveedores'].get('nombre', 'N/A')
        
        df_data.append({
            'id': p.get('id', 0),
            'nombre': p.get('nombre', 'Sin nombre'),
            'cantidad': p.get('cantidad', 0),
            'categoria': p.get('categoria', 'Sin categoría'),
            'precio': p.get('precio', 0),
            'proveedor': proveedor_nombre
        })
    df = pd.DataFrame(df_data)
    
    # Calcular métricas
    df['valor_total'] = df['cantidad'] * df['precio']
    total_valor = df['valor_total'].sum()
    
    # Mostrar métricas
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Valor Total", f"${total_valor:,.0f}".replace(",", "."))
    col2.metric("Total Productos", len(df))
    col3.metric("Stock Total", f"{df['cantidad'].sum():,}".replace(",", "."))
    col4.metric("Stock Bajo", len(df[df['cantidad'] <= 5]))
    
    # Productos con stock bajo
    bajos = df[df['cantidad'] <= 5]
    if not bajos.empty:
        st.warning("🚨 **Productos con Stock Bajo**")
        st.dataframe(bajos[['nombre', 'categoria', 'cantidad', 'precio']], use_container_width=True)
    
    # Gráficos
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Stock por Categoría")
        stock_cat = df.groupby('categoria')['cantidad'].sum()
        st.bar_chart(stock_cat)
    with col2:
        st.subheader("Valor por Categoría")
        valor_cat = df.groupby('categoria')['valor_total'].sum()
        st.bar_chart(valor_cat)

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
                               placeholder="Escribe para filtrar productos...",
                               key="busqueda_editar")
        
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

def mostrar_reportes():
    st.header("📈 Reportes y Análisis")
    
    productos = obtener_productos()
    if not productos:
        st.warning("No hay datos para mostrar")
        return
    
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
    df['valor_total'] = df['cantidad'] * df['precio']
    
    # Resumen
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Valor Total", f"${df['valor_total'].sum():,.0f}".replace(",", "."))
    col2.metric("Productos", len(df))
    col3.metric("Stock Total", df['cantidad'].sum())
    col4.metric("Categorías", df['categoria'].nunique())
    
    # Resumen por categoría
    if 'categoria' in df.columns:
        st.subheader("Resumen por Categoría")
        resumen = df.groupby('categoria').agg({
            'id': 'count',
            'cantidad': 'sum',
            'valor_total': 'sum'
        }).rename(columns={'id': 'Cantidad Productos'})
        st.dataframe(resumen, use_container_width=True)
        
        # Gráficos
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Productos por Categoría")
            st.bar_chart(resumen['Cantidad Productos'])
        with col2:
            st.subheader("Valor por Categoría")
            st.bar_chart(resumen['valor_total'])

def mostrar_administracion():
    st.header("⚙️ Panel de Administración")
    
    st.subheader("👥 Usuarios del Sistema")
    usuarios_df = pd.DataFrame([
        {"Usuario": "david", "Rol": "admin", "Contraseña": "david123"},
        {"Usuario": "briget", "Rol": "admin", "Contraseña": "briget123"},
        {"Usuario": "brian", "Rol": "admin", "Contraseña": "brian123"},
        {"Usuario": "ivan", "Rol": "admin", "Contraseña": "ivan123"},
        {"Usuario": "lector", "Rol": "lector", "Contraseña": "lector123"},
        {"Usuario": "invitado", "Rol": "lector", "Contraseña": "invitado123"}
    ])
    st.dataframe(usuarios_df, use_container_width=True)
    
    st.subheader("🔧 Configuración")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Reinicializar Datos"):
            productos = obtener_productos()
            for p in productos:
                eliminar_producto(p['id'])
            insertar_datos_ejemplo()
            st.success("✅ Datos reinicializados")
            st.rerun()
    
    with col2:
        if st.button("📊 Generar Reporte"):
            productos = obtener_productos()
            if productos:
                df_data = []
                for p in productos:
                    proveedor_nombre = "N/A"
                    if 'proveedores' in p and p['proveedores']:
                        proveedor_nombre = p['proveedores'].get('nombre', 'N/A')
                    
                    df_data.append({
                        'nombre': p.get('nombre', ''),
                        'categoria': p.get('categoria', ''),
                        'cantidad': p.get('cantidad', 0),
                        'precio': p.get('precio', 0),
                        'proveedor': proveedor_nombre
                    })
                df = pd.DataFrame(df_data)
                csv = df.to_csv(index=False)
                st.download_button(
                    "📥 Descargar CSV",
                    csv,
                    f"reporte_{datetime.now().strftime('%Y-%m-%d')}.csv",
                    "text/csv"
                )

# Inicializar la app
if __name__ == "__main__":
    supabase = get_supabase_client()
    main()
