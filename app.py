import streamlit as st
from utils.supabase_client import get_supabase_client
import pandas as pd
from datetime import datetime
import hashlib

# Configuración de la página
st.set_page_config(page_title="Sistema de Inventario", layout="wide")

# Función para formatear números en pesos colombianos
def formato_cop(valor):
    if pd.isna(valor) or valor is None:
        return "$ 0"
    try:
        return f"$ {valor:,.0f}".replace(",", ".")
    except:
        return f"$ {valor}"

# Sistema simple de autenticación
def check_password():
    """Simple sistema de login"""
    def password_entered():
        if st.session_state["username"] in st.secrets["passwords"]:
            password_hash = hashlib.sha256(st.session_state["password"].encode()).hexdigest()
            if password_hash == st.secrets["passwords"][st.session_state["username"]]:
                st.session_state["password_correct"] = True
                st.session_state["user_role"] = st.secrets["user_roles"][st.session_state["username"]]
                st.session_state["current_user"] = st.session_state["username"]
                del st.session_state["password"]
                del st.session_state["username"]
            else:
                st.session_state["password_correct"] = False
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Usuario", key="username")
        st.text_input("Contraseña", type="password", key="password")
        st.button("Ingresar", on_click=password_entered)
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Usuario", key="username")
        st.text_input("Contraseña", type="password", key="password")
        st.button("Ingresar", on_click=password_entered)
        st.error("😕 Usuario o contraseña incorrectos")
        return False
    else:
        return True

# Verificar permisos
def tiene_permiso(permiso_requerido):
    roles_permisos = {
        "lector": ["ver"],
        "editor": ["ver", "agregar", "editar"],
        "admin": ["ver", "agregar", "editar", "eliminar", "admin"]
    }
    
    user_role = st.session_state.get("user_role", "lector")
    return permiso_requerido in roles_permisos.get(user_role, ["ver"])

# Función para obtener categorías actualizadas
def obtener_categorias_actualizadas():
    try:
        response = supabase.table("inventario").select("categoria").execute()
        if response.data:
            categorias = list(set([item['categoria'] for item in response.data]))
            return sorted([cat for cat in categorias if cat])
        return []
    except Exception as e:
        st.error(f"Error al obtener categorías: {e}")
        return []

def obtener_productos():
    try:
        response = supabase.table("inventario").select("*").order("id").execute()
        return response.data
    except Exception as e:
        st.error(f"Error al obtener productos: {e}")
        return []

# ... (mantén todas las demás funciones como formato_cop, insertar_datos_ejemplo, etc.)

def main():
    # Verificar login
    if not check_password():
        st.stop()
    
    # Mostrar información del usuario
    st.sidebar.success(f"👤 {st.session_state.current_user} ({st.session_state.user_role})")
    
    if st.sidebar.button("🚪 Cerrar Sesión"):
        for key in ["password_correct", "user_role", "current_user"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()
    
    # Navegación según permisos
    st.title("🏢 Sistema de Inventario Completo - COP")
    
    with st.sidebar:
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
    st.header("📊 Dashboard de Inventario - COP")
    # ... (mantén el código del dashboard igual)

def gestionar_productos():
    st.header("📦 Gestión de Productos - COP")
    
    # Determinar qué pestañas mostrar según permisos
    tabs = []
    if tiene_permiso("ver"):
        tabs.append("📋 Ver Todos")
    if tiene_permiso("agregar"):
        tabs.append("➕ Agregar Nuevo")
    if tiene_permiso("editar"):
        tabs.append("✏️ Editar Productos")
    
    if not tabs:
        st.warning("❌ No tienes permisos para ver productos")
        return
    
    tab1, tab2, tab3 = st.tabs(tabs)
    
    with tab1:
        if tiene_permiso("ver"):
            productos = obtener_productos()
            if productos:
                df = pd.DataFrame(productos)
                df_show = df.copy()
                df_show['precio'] = df_show['precio'].apply(formato_cop)
                df_show['valor_total'] = (df['cantidad'] * df['precio']).apply(formato_cop)
                st.dataframe(df_show, use_container_width=True)
            else:
                st.info("No hay productos registrados")
    
    with tab2:
        if tiene_permiso("agregar"):
            st.subheader("Agregar Nuevo Producto")
            categorias_actuales = obtener_categorias_actualizadas()
            
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
                    proveedor = st.text_input("Proveedor")
                    min_stock = st.number_input("Stock mínimo alerta", min_value=0, value=5)
                
                if st.form_submit_button("➕ Agregar Producto"):
                    if nombre and categoria and precio > 0:
                        nuevo_producto = {
                            "nombre": nombre.strip(),
                            "categoria": categoria,
                            "precio": precio,
                            "cantidad": cantidad,
                            "proveedor": proveedor.strip(),
                            "min_stock": min_stock
                        }
                        try:
                            result = supabase.table("inventario").insert(nuevo_producto).execute()
                            if result.data:
                                st.success("✅ Producto agregado exitosamente!")
                                st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error: {e}")
    
    with tab3:
        if tiene_permiso("editar"):
            st.subheader("Editar Productos")
            productos = obtener_productos()
            
            if productos:
                for producto in productos:
                    with st.expander(f"📦 {producto['nombre']} - {formato_cop(producto['precio'])}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Categoría:** {producto['categoria']}")
                            st.write(f"**Stock:** {producto['cantidad']}")
                        with col2:
                            st.write(f"**Precio:** {formato_cop(producto['precio'])}")
                            st.write(f"**Proveedor:** {producto.get('proveedor', 'N/A')}")
                        
                        with st.form(f"editar_{producto['id']}"):
                            nuevo_nombre = st.text_input("Nombre", value=producto['nombre'], key=f"nombre_{producto['id']}")
                            nueva_cantidad = st.number_input("Cantidad", value=producto['cantidad'], key=f"cantidad_{producto['id']}")
                            
                            if st.form_submit_button("💾 Guardar Cambios"):
                                datos = {"nombre": nuevo_nombre, "cantidad": nueva_cantidad}
                                try:
                                    supabase.table("inventario").update(datos).eq("id", producto['id']).execute()
                                    st.success("✅ Producto actualizado")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Error: {e}")
                        
                        # Botón eliminar solo para admin
                        if tiene_permiso("eliminar"):
                            if st.button(f"🗑️ Eliminar", key=f"eliminar_{producto['id']}"):
                                try:
                                    supabase.table("inventario").delete().eq("id", producto['id']).execute()
                                    st.success("✅ Producto eliminado")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Error: {e}")

def mostrar_administracion():
    if not tiene_permiso("admin"):
        st.error("❌ No tienes permisos de administrador")
        return
    
    st.header("⚙️ Panel de Administración")
    
    tab1, tab2 = st.tabs(["Gestión de Usuarios", "Configuración del Sistema"])
    
    with tab1:
        st.subheader("Usuarios y Permisos")
        st.info("""
        **Roles disponibles:**
        - 👁️ **Lector**: Solo puede ver productos y reportes
        - ✏️ **Editor**: Puede ver, agregar y editar productos  
        - ⚙️ **Admin**: Acceso completo + administración
        """)
        
        # Aquí podrías agregar gestión de usuarios en el futuro
        
    with tab2:
        st.subheader("Configuración del Sistema")
        if st.button("🔄 Reinicializar Datos de Ejemplo"):
            try:
                productos = obtener_productos()
                for producto in productos:
                    supabase.table("inventario").delete().eq("id", producto['id']).execute()
                # Llama a tu función para insertar datos de ejemplo
                st.success("✅ Sistema reinicializado")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {e}")

# Inicializar Supabase
supabase = get_supabase_client()

if __name__ == "__main__":
    main()
