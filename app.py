import streamlit as st
from utils.supabase_client import get_supabase_client
import pandas as pd
from datetime import datetime
import hashlib

# Configuración de la página
st.set_page_config(page_title="Sistema de Inventario", layout="wide")

# ================== 🎯 USUARIOS ACTUALIZADOS ==================
USUARIOS = {
    "david": {
        "password": "david123",
        "rol": "admin"
    },
    "briget": {
        "password": "briget123",
        "rol": "admin"
    },
    "brian": {
        "password": "brian123", 
        "rol": "admin"
    },
    "ivan": {
        "password": "ivan123",
        "rol": "admin"
    },
    "lector": {
        "password": "lector123",
        "rol": "lector"
    },
    "invitado": {
        "password": "invitado123",
        "rol": "lector"
    }
}

# Función para formatear números en pesos colombianos
def formato_cop(valor):
    """Formatea un número como moneda colombiana"""
    if pd.isna(valor) or valor is None:
        return "$ 0"
    try:
        return f"$ {valor:,.0f}".replace(",", ".")
    except:
        return f"$ {valor}"

# Sistema simple de autenticación
def check_password():
    """Sistema de login simplificado y corregido"""
    
    # Si ya está autenticado, no hacer nada
    if "password_correct" in st.session_state and st.session_state["password_correct"]:
        return True
        
    # Si no está autenticado, mostrar formulario de login
    st.title("🔐 Iniciar Sesión - Sistema de Inventario")
    st.markdown("---")
    
    with st.form("login_form"):
        username = st.text_input("👤 Usuario", placeholder="Ingresa tu usuario")
        password = st.text_input("🔒 Contraseña", type="password", placeholder="Ingresa tu contraseña")
        
        submitted = st.form_submit_button("🚀 Ingresar al Sistema")
        
        if submitted:
            username_lower = username.strip().lower()
            
            # Verificar si el usuario existe
            if username_lower in USUARIOS:
                user_data = USUARIOS[username_lower]
                
                # Verificar contraseña
                if password == user_data["password"]:
                    st.session_state["password_correct"] = True
                    st.session_state["user_role"] = user_data["rol"]
                    st.session_state["current_user"] = username_lower
                    st.success(f"✅ ¡Bienvenido/a {username.title()}!")
                    st.rerun()
                else:
                    st.error("❌ Contraseña incorrecta")
            else:
                st.error("❌ Usuario no encontrado")
    
    # Mostrar usuarios de prueba
    with st.expander("📋 Usuarios del Sistema (Haz clic para ver)"):
        st.write("""
        **👨‍💼 Administradores (Acceso completo):**
        - Usuario: **david** / Contraseña: **david123**
        - Usuario: **briget** / Contraseña: **briget123**
        - Usuario: **brian** / Contraseña: **brian123**
        - Usuario: **ivan** / Contraseña: **ivan123**
        
        **👁️ Lectores (Solo visualización):**
        - Usuario: **lector** / Contraseña: **lector123**
        - Usuario: **invitado** / Contraseña: **invitado123**
        """)
    
    return False

# Verificar permisos
def tiene_permiso(permiso_requerido):
    roles_permisos = {
        "lector": ["ver"],
        "admin": ["ver", "agregar", "editar", "eliminar", "admin"]
    }
    
    user_role = st.session_state.get("user_role", "lector")
    return permiso_requerido in roles_permisos.get(user_role, ["ver"])

# ================== 🔧 FUNCIONES CORREGIDAS ==================

# Función para obtener productos
def obtener_productos():
    try:
        response = supabase.table("inventario").select("*").order("id").execute()
        return response.data
    except Exception as e:
        st.error(f"Error al obtener productos: {e}")
        return []

# Función para obtener categorías
def obtener_categorias_actualizadas():
    try:
        response = supabase.table("inventario").select("categoria").execute()
        if response.data:
            categorias = list(set([item['categoria'] for item in response.data if item.get('categoria')]))
            return sorted([cat for cat in categorias if cat])
        return []
    except Exception as e:
        st.error(f"Error al obtener categorías: {e}")
        return []

# Función para agregar producto
def agregar_producto(nombre, cantidad, categoria, precio, proveedor):
    try:
        # Obtener el máximo ID actual
        max_response = supabase.table("inventario").select("id").order("id", desc=True).limit(1).execute()
        next_id = 1
        if max_response.data:
            next_id = max_response.data[0]['id'] + 1

        producto_data = {
            "id": next_id,
            "nombre": nombre.strip(),
            "categoria": categoria,
            "precio": precio,
            "cantidad": cantidad,
            "proveedor": proveedor.strip(),
            "fecha_actualizacion": datetime.now().isoformat()
        }
        
        response = supabase.table("inventario").insert(producto_data).execute()
        
        if hasattr(response, 'data') and response.data:
            st.success("✅ Producto agregado exitosamente!")
            return True
        else:
            st.error("❌ Error al agregar producto")
            return False
            
    except Exception as e:
        st.error(f"❌ Error: {e}")
        return False

# Función para actualizar producto
def actualizar_producto(producto_id, datos):
    try:
        datos['fecha_actualizacion'] = datetime.now().isoformat()
        response = supabase.table("inventario").update(datos).eq("id", producto_id).execute()
        return True
    except Exception as e:
        st.error(f"Error al actualizar: {e}")
        return False

# Función para eliminar producto
def eliminar_producto(producto_id):
    try:
        response = supabase.table("inventario").delete().eq("id", producto_id).execute()
        return True
    except Exception as e:
        st.error(f"Error al eliminar: {e}")
        return False

# Función para insertar datos de ejemplo
def insertar_datos_ejemplo():
    try:
        productos = obtener_productos()
        if not productos:
            datos_ejemplo = [
                {"nombre": "Laptop HP Pavilion", "cantidad": 15, "categoria": "Tecnología", "proveedor": "HP Inc.", "precio": 3500000},
                {"nombre": "Mouse Inalámbrico", "cantidad": 50, "categoria": "Tecnología", "proveedor": "Logitech", "precio": 120000},
                {"nombre": "Monitor 24 Pulgadas", "cantidad": 8, "categoria": "Tecnología", "proveedor": "Samsung", "precio": 850000},
                {"nombre": "Silla de Oficina", "cantidad": 12, "categoria": "Mobiliario", "proveedor": "ErgoChair", "precio": 450000},
                {"nombre": "Escritorio Ejecutivo", "cantidad": 5, "categoria": "Mobiliario", "proveedor": "OfficeMax", "precio": 1200000},
                {"nombre": "Tóner Negro", "cantidad": 25, "categoria": "Insumos", "proveedor": "Canon", "precio": 180000},
            ]
            
            for producto in datos_ejemplo:
                supabase.table("inventario").insert(producto).execute()
            
            return True
    except Exception as e:
        st.error(f"Error: {e}")
    return False

# ================== 🎨 INTERFAZ PRINCIPAL ==================

def main():
    # Verificar login
    if not check_password():
        st.stop()
    
    # Inicializar Supabase
    global supabase
    supabase = get_supabase_client()
    
    # Inicializar datos si es necesario
    if 'inicializado' not in st.session_state:
        insertar_datos_ejemplo()
        st.session_state.inicializado = True
    
    # Mostrar información del usuario
    rol_emoji = {
        "admin": "⚙️",
        "lector": "👁️"
    }
    
    with st.sidebar:
        user_display_name = st.session_state.get("current_user", "Usuario").title()
        user_role = st.session_state.get("user_role", "lector")
        st.success(f"{rol_emoji.get(user_role, '👤')} {user_display_name} ({user_role})")
        
        if st.button("🚪 Cerrar Sesión"):
            for key in ["password_correct", "user_role", "current_user", "inicializado"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
        
        st.header("🔧 Navegación")
        
        # Opciones básicas para todos
        opciones = ["📊 Dashboard", "📦 Productos", "📈 Reportes"]
        
        # Solo admin ve configuración
        if tiene_permiso("admin"):
            opciones.append("⚙️ Administración")
        
        opcion = st.radio("Selecciona una opción:", opciones)
        
        # Mostrar categorías
        categorias_sidebar = obtener_categorias_actualizadas()
        if categorias_sidebar:
            st.markdown("---")
            st.subheader("🏷️ Categorías Existentes")
            for categoria in categorias_sidebar:
                st.write(f"• {categoria}")
        
        st.markdown("---")
        st.info("💰 **Moneda:** Pesos Colombianos (COP)")
    
    # Contenido según opción seleccionada
    if opcion == "📊 Dashboard":
        mostrar_dashboard()
    elif opcion == "📦 Productos":
        gestionar_productos()
    elif opcion == "📈 Reportes":
        mostrar_reportes()
    elif opcion == "⚙️ Administración" and tiene_permiso("admin"):
        mostrar_administracion()

def mostrar_dashboard():
    st.header("📊 Dashboard de Inventario")
    
    productos = obtener_productos()
    if not productos:
        st.warning("No hay productos en el inventario")
        return
    
    df = pd.DataFrame(productos)
    
    # Asegurar que las columnas necesarias existen
    if 'cantidad' not in df.columns:
        df['cantidad'] = 0
    if 'precio' not in df.columns:
        df['precio'] = 0
    
    # Cálculo de valores en COP
    df['valor_total'] = df['cantidad'] * df['precio']
    total_valor = df['valor_total'].sum()
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Valor Total Inventario", formato_cop(total_valor))
    with col2:
        st.metric("Total Productos", len(df))
    with col3:
        st.metric("Stock Total", f"{df['cantidad'].sum():,}".replace(",", "."))
    with col4:
        # Stock bajo - si no existe min_stock, usar 5 como default
        if 'min_stock' in df.columns:
            productos_bajos = df[df['cantidad'] <= df['min_stock']]
        else:
            productos_bajos = df[df['cantidad'] <= 5]
        st.metric("Stock Bajo", len(productos_bajos))
    
    # Alertas de stock bajo
    if len(productos_bajos) > 0:
        st.warning("🚨 **Productos con Stock Bajo**")
        columnas_mostrar = ['nombre', 'categoria', 'cantidad', 'precio']
        df_bajos = productos_bajos[columnas_mostrar].copy()
        df_bajos['precio'] = df_bajos['precio'].apply(formato_cop)
        st.dataframe(df_bajos, use_container_width=True)
    
    # Gráficos
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Stock por Categoría")
        if 'categoria' in df.columns:
            stock_categoria = df.groupby('categoria')['cantidad'].sum()
            st.bar_chart(stock_categoria)
    
    with col2:
        st.subheader("Valor por Categoría")
        if 'categoria' in df.columns:
            valor_categoria = df.groupby('categoria')['valor_total'].sum()
            st.bar_chart(valor_categoria)

def gestionar_productos():
    st.header("📦 Gestión de Productos")
    
    # Para lectores: solo mostrar vista, sin pestañas
    if st.session_state.get("user_role") == "lector":
        productos = obtener_productos()
        if productos:
            df = pd.DataFrame(productos)
            df_show = df.copy()
            
            # Formatear columnas que existen
            if 'precio' in df_show.columns:
                df_show['precio'] = df_show['precio'].apply(formato_cop)
            
            # Calcular valor total si existen las columnas necesarias
            if 'cantidad' in df.columns and 'precio' in df.columns:
                df_show['valor_total'] = (df['cantidad'] * df['precio']).apply(formato_cop)
            
            st.dataframe(df_show, use_container_width=True)
            
            st.info("👁️ **Modo de solo lectura:** No tienes permisos para modificar productos.")
        else:
            st.info("No hay productos registrados")
        return
    
    # Para administradores: mostrar pestañas completas
    tab1, tab2, tab3 = st.tabs(["📋 Ver Todos", "➕ Agregar Nuevo", "✏️ Editar Productos"])
    
    with tab1:
        productos = obtener_productos()
        if productos:
            df = pd.DataFrame(productos)
            df_show = df.copy()
            
            if 'precio' in df_show.columns:
                df_show['precio'] = df_show['precio'].apply(formato_cop)
            
            if 'cantidad' in df.columns and 'precio' in df.columns:
                df_show['valor_total'] = (df['cantidad'] * df['precio']).apply(formato_cop)
            
            st.dataframe(df_show, use_container_width=True)
            
            # Exportar datos
            csv = df.to_csv(index=False)
            st.download_button("📥 Exportar CSV", csv, "inventario.csv", "text/csv")
        else:
            st.info("No hay productos registrados")
    
    with tab2:
        st.subheader("Agregar Nuevo Producto")
        categorias_actuales = obtener_categorias_actualizadas()
        
        with st.form("agregar_producto_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                nombre = st.text_input("Nombre del producto*")
                categoria = st.selectbox("Categoría*", options=categorias_actuales if categorias_actuales else ["Tecnología", "Mobiliario", "Insumos"])
                precio = st.number_input("Precio unitario (COP)*", min_value=0, value=0, step=10000)
            with col2:
                cantidad = st.number_input("Cantidad inicial*", min_value=0, value=0)
                proveedor = st.text_input("Proveedor")
            
            if st.form_submit_button("➕ Agregar Producto"):
                if nombre and categoria and precio > 0:
                    if agregar_producto(nombre, cantidad, categoria, precio, proveedor):
                        st.rerun()
                else:
                    st.error("❌ Por favor completa todos los campos requeridos")
    
    with tab3:
        st.subheader("Editar Productos")
        productos = obtener_productos()
        
        if productos:
            for producto in productos:
                with st.expander(f"📦 {producto.get('nombre', 'Sin nombre')} - {formato_cop(producto.get('precio', 0))}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Categoría:** {producto.get('categoria', 'N/A')}")
                        st.write(f"**Stock:** {producto.get('cantidad', 0):,} unidades".replace(",", "."))
                    with col2:
                        st.write(f"**Precio:** {formato_cop(producto.get('precio', 0))}")
                        st.write(f"**Proveedor:** {producto.get('proveedor', 'N/A')}")
                    
                    with st.form(f"editar_{producto['id']}"):
                        st.write("**Editar información:**")
                        nuevo_nombre = st.text_input("Nombre", value=producto.get('nombre', ''), key=f"nombre_{producto['id']}")
                        
                        col_edit1, col_edit2 = st.columns(2)
                        with col_edit1:
                            nueva_cantidad = st.number_input("Cantidad", value=producto.get('cantidad', 0), key=f"cantidad_{producto['id']}")
                            nuevo_precio = st.number_input("Precio (COP)", value=int(producto.get('precio', 0)), key=f"precio_{producto['id']}", step=10000)
                        
                        with col_edit2:
                            nuevo_proveedor = st.text_input("Proveedor", value=producto.get('proveedor', ''), key=f"proveedor_{producto['id']}")
                        
                        if st.form_submit_button("💾 Guardar Cambios"):
                            datos = {
                                "nombre": nuevo_nombre,
                                "cantidad": nueva_cantidad,
                                "precio": nuevo_precio,
                                "proveedor": nuevo_proveedor
                            }
                            if actualizar_producto(producto['id'], datos):
                                st.rerun()
                    
                    if st.button(f"🗑️ Eliminar Producto", key=f"eliminar_{producto['id']}"):
                        if eliminar_producto(producto['id']):
                            st.rerun()

def mostrar_reportes():
    st.header("📈 Reportes y análisis")
    
    productos = obtener_productos()
    if not productos:
        st.warning("No hay datos para mostrar")
        return
    
    df = pd.DataFrame(productos)
    
    # Asegurar columnas necesarias
    if 'cantidad' not in df.columns:
        df['cantidad'] = 0
    if 'precio' not in df.columns:
        df['precio'] = 0
    
    df['valor_total'] = df['cantidad'] * df['precio']
    
    # Resumen general
    st.subheader("📊 Resumen General del Inventario")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Valor Total", formato_cop(df['valor_total'].sum()))
    with col2:
        st.metric("Productos Totales", len(df))
    with col3:
        st.metric("Inversión Promedio", formato_cop(df['precio'].mean()))
    with col4:
        categorias_count = df['categoria'].nunique() if 'categoria' in df.columns else 0
        st.metric("Categorías", categorias_count)
    
    if 'categoria' in df.columns:
        st.subheader("Resumen por Categoría")
        resumen_categorias = df.groupby('categoria').agg({
            'id': 'count',
            'cantidad': 'sum',
            'precio': 'mean',
            'valor_total': 'sum'
        }).round(0)
        
        resumen_categorias.columns = ['N° Productos', 'Stock Total', 'Precio Promedio', 'Valor Total']
        resumen_categorias_show = resumen_categorias.copy()
        resumen_categorias_show['Precio Promedio'] = resumen_categorias_show['Precio Promedio'].apply(formato_cop)
        resumen_categorias_show['Valor Total'] = resumen_categorias_show['Valor Total'].apply(formato_cop)
        
        st.dataframe(resumen_categorias_show, use_container_width=True)
        
        # Gráficos
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Distribución de Productos por Categoría")
            conteo_categorias = df['categoria'].value_counts()
            st.bar_chart(conteo_categorias)
        
        with col2:
            st.subheader("Valor de Inventario por Categoría (COP)")
            valor_por_categoria = df.groupby('categoria')['valor_total'].sum()
            st.bar_chart(valor_por_categoria)

def mostrar_administracion():
    st.header("⚙️ Panel de Administración")
    
    st.subheader("👥 Usuarios del Sistema")
    
    # Mostrar tabla de usuarios actuales
    usuarios_data = []
    for usuario, info in USUARIOS.items():
        usuarios_data.append({
            "Usuario": usuario,
            "Rol": info["rol"],
            "Contraseña": info["password"]
        })
    
    usuarios_df = pd.DataFrame(usuarios_data)
    st.dataframe(usuarios_df, use_container_width=True)
    
    st.info("""
    **📋 Resumen de permisos:**
    
    **⚙️ Administradores (4 usuarios):**
    - David, Briget, Brian, Ivan
    - Acceso completo a todas las funciones
    
    **👁️ Lectores (2 usuarios):**
    - lector, invitado  
    - Solo pueden ver productos y reportes
    - No pueden modificar, agregar ni eliminar
    """)
    
    st.subheader("🔧 Configuración del Sistema")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Reinicializar Datos de Ejemplo", type="secondary"):
            try:
                # Eliminar todos los productos
                productos = obtener_productos()
                for producto in productos:
                    eliminar_producto(producto['id'])
                
                # Insertar datos de ejemplo
                insertar_datos_ejemplo()
                st.success("✅ Sistema reinicializado correctamente")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {e}")
    
    with col2:
        if st.button("📊 Generar Reporte Completo", type="primary"):
            productos = obtener_productos()
            if productos:
                df = pd.DataFrame(productos)
                # Asegurar columnas
                if 'cantidad' not in df.columns:
                    df['cantidad'] = 0
                if 'precio' not in df.columns:
                    df['precio'] = 0
                
                df['valor_total'] = df['cantidad'] * df['precio']
                
                # Crear reporte detallado
                columnas_reporte = ['nombre', 'categoria', 'cantidad', 'precio', 'valor_total']
                if 'proveedor' in df.columns:
                    columnas_reporte.append('proveedor')
                
                reporte = df[columnas_reporte]
                csv = reporte.to_csv(index=False)
                
                st.download_button(
                    "📥 Descargar Reporte CSV",
                    csv,
                    f"reporte_inventario_{datetime.now().strftime('%Y-%m-%d')}.csv",
                    "text/csv"
                )
            else:
                st.warning("No hay datos para generar reporte")

# Inicializar Supabase
supabase = get_supabase_client()

if __name__ == "__main__":
    main()
