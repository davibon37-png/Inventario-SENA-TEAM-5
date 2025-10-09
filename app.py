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
# =============================================================================

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

# ================== 🔧 FUNCIONES ACTUALIZADAS CON NUEVA BASE DE DATOS ==================

# Función para obtener categorías actualizadas
def obtener_categorias_actualizadas():
    """Obtiene categorías directamente de la base de datos"""
    try:
        response = supabase.table("inventario").select("categoria").execute()
        if response.data:
            categorias = list(set([item['categoria'] for item in response.data]))
            return sorted([cat for cat in categorias if cat])
        return []
    except Exception as e:
        st.error(f"Error al obtener categorías: {e}")
        return []

# Función para obtener todos los productos CON RELACIONES CORREGIDAS
def obtener_productos():
    try:
        # Consulta segura con join corregido
        response = supabase.table("inventario").select("""
            id, nombre, cantidad, categoria, precio, activo, fecha_actualizacion,
            proveedores (id, nombre, telefono, email)
        """).execute()
        
        return response.data if hasattr(response, 'data') else []
            
    except Exception as e:
        st.error(f"Error al obtener productos: {e}")
        # Fallback seguro
        try:
            response = supabase.table("inventario").select("*").execute()
            return response.data if hasattr(response, 'data') else []
        except:
            return []

# Función para obtener proveedores
def obtener_proveedores():
    try:
        response = supabase.table("proveedores").select("*").eq("activo", True).execute()
        return response.data if hasattr(response, 'data') else []
    except Exception as e:
        st.error(f"Error al obtener proveedores: {e}")
        return []

# Función para agregar producto ACTUALIZADA
def agregar_producto(nombre, cantidad, categoria, precio, proveedor_id):
    try:
        # Obtener el máximo ID actual para evitar duplicados
        max_response = supabase.table("inventario").select("id").order("id", desc=True).limit(1).execute()
        next_id = 1
        if max_response.data:
            next_id = max_response.data[0]['id'] + 1

        producto_data = {
            "id": next_id,
            "nombre": nombre,
            "cantidad": cantidad,
            "categoria": categoria,
            "precio": float(precio),
            "proveedor_id": proveedor_id,
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

# Función para agregar proveedor
def agregar_proveedor(nombre, contacto, telefono, email, direccion):
    try:
        proveedor_data = {
            "nombre": nombre,
            "contacto": contacto,
            "telefono": telefono,
            "email": email,
            "direccion": direccion
        }
        
        response = supabase.table("proveedores").insert(proveedor_data).execute()
        
        if hasattr(response, 'data') and response.data:
            st.success("✅ Proveedor agregado exitosamente!")
            return True
        else:
            st.error("❌ Error al agregar proveedor")
            return False
            
    except Exception as e:
        st.error(f"❌ Error: {e}")
        return False

# Función para insertar datos de ejemplo ACTUALIZADA
def insertar_datos_ejemplo():
    try:
        productos = obtener_productos()
        if not productos:
            # Obtener proveedores existentes
            proveedores = obtener_proveedores()
            if not proveedores:
                st.error("No hay proveedores en la base de datos")
                return False
                
            proveedor_id = proveedores[0]['id']  # Usar el primer proveedor disponible
            
            datos_ejemplo = [
                {"nombre": "Laptop HP Pavilion", "cantidad": 15, "categoria": "Tecnología", "proveedor_id": proveedor_id, "precio": 3500000, "min_stock": 5},
                {"nombre": "Mouse Inalámbrico", "cantidad": 50, "categoria": "Tecnología", "proveedor_id": proveedor_id, "precio": 120000, "min_stock": 10},
                {"nombre": "Monitor 24 Pulgadas", "cantidad": 8, "categoria": "Tecnología", "proveedor_id": proveedor_id, "precio": 850000, "min_stock": 3},
                {"nombre": "Silla de Oficina", "cantidad": 12, "categoria": "Mobiliario", "proveedor_id": proveedor_id, "precio": 450000, "min_stock": 2},
                {"nombre": "Escritorio Ejecutivo", "cantidad": 5, "categoria": "Mobiliario", "proveedor_id": proveedor_id, "precio": 1200000, "min_stock": 1},
                {"nombre": "Tóner Negro", "cantidad": 25, "categoria": "Insumos", "proveedor_id": proveedor_id, "precio": 180000, "min_stock": 15},
            ]
            
            for producto in datos_ejemplo:
                supabase.table("inventario").insert(producto).execute()
            
            return True
    except Exception as e:
        st.error(f"Error: {e}")
    return False

# Funciones CRUD ACTUALIZADAS
def actualizar_producto(producto_id, datos):
    try:
        datos['fecha_actualizacion'] = datetime.now().isoformat()
        supabase.table("inventario").update(datos).eq("id", producto_id).execute()
        return True
    except Exception as e:
        st.error(f"Error al actualizar: {e}")
        return False

def eliminar_producto(producto_id):
    try:
        supabase.table("inventario").delete().eq("id", producto_id).execute()
        return True
    except Exception as e:
        st.error(f"Error al eliminar: {e}")
        return False

# ================== 🎨 INTERFAZ PRINCIPAL (MISMO DISEÑO) ==================

def main():
    # Verificar login
    if not check_password():
        st.stop()
    
    # Inicializar Supabase
    supabase = get_supabase_client()
    
    # Inicializar datos si es necesario
    if 'inicializado' not in st.session_state:
        if insertar_datos_ejemplo():
            st.session_state.inicializado = True
    
    # Mostrar información del usuario
    rol_emoji = {
        "admin": "⚙️",
        "lector": "👁️"
    }
    
    with st.sidebar:
        user_display_name = st.session_state.current_user.title()
        st.success(f"{rol_emoji.get(st.session_state.user_role, '👤')} {user_display_name} ({st.session_state.user_role})")
        
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
    
    # Cálculo de valores en COP
    df['valor_total'] = df['cantidad'] * df['precio']
    total_valor = df['valor_total'].sum()
    valor_promedio = df['precio'].mean()
    
    # Métricas principales EN PESOS COLOMBIANOS
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Valor Total Inventario", formato_cop(total_valor))
    with col2:
        st.metric("Total Productos", len(df))
    with col3:
        st.metric("Stock Total", f"{df['cantidad'].sum():,}".replace(",", "."))
    with col4:
        productos_bajos = df[df['cantidad'] <= df['min_stock']]
        st.metric("Stock Bajo", len(productos_bajos))
    
    # Alertas de stock bajo
    if not productos_bajos.empty:
        st.warning("🚨 **Productos con Stock Bajo**")
        df_bajos = productos_bajos[['nombre', 'categoria', 'cantidad', 'min_stock', 'precio']].copy()
        df_bajos['precio'] = df_bajos['precio'].apply(formato_cop)
        st.dataframe(df_bajos, use_container_width=True)
    
    # Gráficos
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Stock por Categoría")
        stock_categoria = df.groupby('categoria')['cantidad'].sum()
        st.bar_chart(stock_categoria)
    
    with col2:
        st.subheader("Valor por Categoría")
        valor_categoria = df.groupby('categoria')['valor_total'].sum()
        st.bar_chart(valor_categoria)

def gestionar_productos():
    st.header("📦 Gestión de Productos")
    
    # Para lectores: solo mostrar vista, sin pestañas
    if st.session_state.user_role == "lector":
        productos = obtener_productos()
        if productos:
            df = pd.DataFrame(productos)
            df_show = df.copy()
            df_show['precio'] = df_show['precio'].apply(formato_cop)
            df_show['valor_total'] = (df['cantidad'] * df['precio']).apply(formato_cop)
            
            # Manejar proveedores en la visualización
            if 'proveedores' in df_show.columns:
                df_show['proveedor_nombre'] = df_show['proveedores'].apply(
                    lambda x: x.get('nombre', 'N/A') if x else 'N/A'
                )
            
            st.dataframe(df_show, use_container_width=True)
            
            st.info("👁️ **Modo de solo lectura:** No tienes permisos para modificar productos.")
        else:
            st.info("No hay productos registrados")
        return
    
    # Para administradores: mostrar pestañas completas
    tabs = st.tabs(["📋 Ver Todos", "➕ Agregar Nuevo", "✏️ Editar Productos"])
    
    with tabs[0]:
        productos = obtener_productos()
        if productos:
            df = pd.DataFrame(productos)
            df_show = df.copy()
            df_show['precio'] = df_show['precio'].apply(formato_cop)
            df_show['valor_total'] = (df['cantidad'] * df['precio']).apply(formato_cop)
            
            # Manejar proveedores en la visualización
            if 'proveedores' in df_show.columns:
                df_show['proveedor_nombre'] = df_show['proveedores'].apply(
                    lambda x: x.get('nombre', 'N/A') if x else 'N/A'
                )
            
            st.dataframe(df_show, use_container_width=True)
            
            # Exportar datos
            csv = df.to_csv(index=False)
            st.download_button("📥 Exportar CSV", csv, "inventario.csv", "text/csv")
        else:
            st.info("No hay productos registrados")
    
    with tabs[1]:
        st.subheader("Agregar Nuevo Producto")
        categorias_actuales = obtener_categorias_actualizadas()
        proveedores = obtener_proveedores()
        
        if not categorias_actuales:
            st.error("❌ No hay categorías disponibles.")
            return
        
        with st.form("agregar_producto_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                nombre = st.text_input("Nombre del producto*")
                categoria = st.selectbox("Categoría*", options=categorias_actuales)
                precio = st.number_input("Precio unitario (COP)*", min_value=0, value=0, step=10000)
            with col2:
                cantidad = st.number_input("Cantidad inicial*", min_value=0, value=0)
                
                # Selectbox para proveedores
                if proveedores:
                    opciones_proveedores = {f"{p['id']} - {p['nombre']}": p['id'] for p in proveedores}
                    proveedor_seleccionado = st.selectbox("Proveedor*", options=list(opciones_proveedores.keys()))
                    proveedor_id = opciones_proveedores[proveedor_seleccionado]
                else:
                    st.warning("No hay proveedores disponibles")
                    proveedor_id = None
                
                min_stock = st.number_input("Stock mínimo alerta", min_value=0, value=5)
            
            if st.form_submit_button("➕ Agregar Producto"):
                if nombre and categoria and precio > 0 and proveedor_id is not None:
                    nuevo_producto = {
                        "nombre": nombre.strip(),
                        "categoria": categoria,
                        "precio": precio,
                        "cantidad": cantidad,
                        "proveedor_id": proveedor_id,
                        "min_stock": min_stock
                    }
                    try:
                        result = agregar_producto(nombre, cantidad, categoria, precio, proveedor_id)
                        if result:
                            st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
                else:
                    st.error("❌ Por favor completa todos los campos requeridos")
    
    with tabs[2]:
        st.subheader("Editar Productos")
        productos = obtener_productos()
        
        if productos:
            for producto in productos:
                with st.expander(f"📦 {producto['nombre']} - {formato_cop(producto['precio'])}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Categoría:** {producto['categoria']}")
                        st.write(f"**Stock:** {producto['cantidad']:,} unidades".replace(",", "."))
                    with col2:
                        st.write(f"**Precio:** {formato_cop(producto['precio'])}")
                        # Mostrar proveedor
                        proveedor_info = producto.get('proveedores', {})
                        proveedor_nombre = proveedor_info.get('nombre', 'N/A') if proveedor_info else 'N/A'
                        st.write(f"**Proveedor:** {proveedor_nombre}")
                    
                    with st.form(f"editar_{producto['id']}"):
                        st.write("**Editar información:**")
                        nuevo_nombre = st.text_input("Nombre", value=producto['nombre'], key=f"nombre_{producto['id']}")
                        
                        col_edit1, col_edit2 = st.columns(2)
                        with col_edit1:
                            nueva_cantidad = st.number_input("Cantidad", value=producto['cantidad'], key=f"cantidad_{producto['id']}")
                            nuevo_precio = st.number_input("Precio (COP)", value=int(producto['precio']), key=f"precio_{producto['id']}", step=10000)
                        
                        with col_edit2:
                            # Selectbox para proveedores en edición
                            proveedores_edicion = obtener_proveedores()
                            if proveedores_edicion:
                                opciones_proveedores_edicion = {f"{p['id']} - {p['nombre']}": p['id'] for p in proveedores_edicion}
                                proveedor_actual = producto.get('proveedor_id')
                                proveedor_actual_nombre = next((f"{p['id']} - {p['nombre']}" for p in proveedores_edicion if p['id'] == proveedor_actual), list(opciones_proveedores_edicion.keys())[0])
                                nuevo_proveedor = st.selectbox("Proveedor", options=list(opciones_proveedores_edicion.keys()), 
                                                             index=list(opciones_proveedores_edicion.keys()).index(proveedor_actual_nombre) if proveedor_actual_nombre in opciones_proveedores_edicion else 0,
                                                             key=f"proveedor_{producto['id']}")
                                nuevo_proveedor_id = opciones_proveedores_edicion[nuevo_proveedor]
                            else:
                                st.warning("No hay proveedores")
                                nuevo_proveedor_id = producto.get('proveedor_id')
                            
                            nuevo_min_stock = st.number_input("Stock mínimo", value=producto.get('min_stock', 5), key=f"minstock_{producto['id']}")
                        
                        if st.form_submit_button("💾 Guardar Cambios"):
                            datos = {
                                "nombre": nuevo_nombre,
                                "cantidad": nueva_cantidad,
                                "precio": nuevo_precio,
                                "proveedor_id": nuevo_proveedor_id,
                                "min_stock": nuevo_min_stock
                            }
                            try:
                                actualizar_producto(producto['id'], datos)
                                st.success("✅ Producto actualizado")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Error: {e}")
                    
                    if st.button(f"🗑️ Eliminar Producto", key=f"eliminar_{producto['id']}"):
                        try:
                            eliminar_producto(producto['id'])
                            st.success("✅ Producto eliminado")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error: {e}")

def mostrar_reportes():
    st.header("📈 Reportes y análisis")
    
    productos = obtener_productos()
    if not productos:
        st.warning("No hay datos para mostrar")
        return
    
    df = pd.DataFrame(productos)
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
        st.metric("Categorías", df['categoria'].nunique())
    
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
                    supabase.table("inventario").delete().eq("id", producto['id']).execute()
                
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
                df['valor_total'] = df['cantidad'] * df['precio']
                
                # Crear reporte detallado
                reporte = df[['nombre', 'categoria', 'cantidad', 'precio', 'valor_total']]
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
