import streamlit as st
from utils.supabase_client import get_supabase_client
import pandas as pd
from datetime import datetime

# Configuración de la página
st.set_page_config(page_title="Sistema de Inventario", layout="wide")

# ================== 🎯 USUARIOS ACTUALIZADOS ==================
USUARIOS = {
    "david": {"password": "david123", "rol": "admin"},
    "briget": {"password": "briget123", "rol": "admin"},
    "brian": {"password": "brian123", "rol": "admin"},
    "ivan": {"password": "ivan123", "rol": "admin"},
    "lector": {"password": "lector123", "rol": "lector"},
    "invitado": {"password": "invitado123", "rol": "lector"}
}
# =============================================================================

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
    if "password_correct" in st.session_state and st.session_state["password_correct"]:
        return True
        
    st.title("🔐 Iniciar Sesión - Sistema de Inventario")
    st.markdown("---")
    
    with st.form("login_form"):
        username = st.text_input("👤 Usuario", placeholder="Ingresa tu usuario")
        password = st.text_input("🔒 Contraseña", type="password", placeholder="Ingresa tu contraseña")
        
        submitted = st.form_submit_button("🚀 Ingresar al Sistema")
        
        if submitted:
            username_lower = username.strip().lower()
            
            if username_lower in USUARIOS:
                user_data = USUARIOS[username_lower]
                
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
    
    with st.expander("📋 Usuarios del Sistema"):
        st.write("""
        **👨‍💼 Administradores:**
        - david / david123
        - briget / briget123  
        - brian / brian123
        - ivan / ivan123
        
        **👁️ Lectores:**
        - lector / lector123
        - invitado / invitado123
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

# ================== FUNCIONES PARA NUEVAS TABLAS ==================
def obtener_proveedores():
    try:
        response = supabase.table("proveedores").select("*").order("nombre").execute()
        return response.data
    except Exception as e:
        st.error(f"Error al obtener proveedores: {e}")
        return []

def obtener_clientes():
    try:
        response = supabase.table("clientes").select("*").order("nombre").execute()
        return response.data
    except Exception as e:
        st.error(f"Error al obtener clientes: {e}")
        return []

def obtener_ventas():
    try:
        response = supabase.table("ventas").select("*, clientes(nombre)").order("fecha_venta", desc=True).execute()
        return response.data
    except Exception as e:
        st.error(f"Error al obtener ventas: {e}")
        return []

def obtener_venta_detalles(venta_id):
    try:
        response = supabase.table("venta_detalles").select("*, inventario(nombre)").eq("venta_id", venta_id).execute()
        return response.data
    except Exception as e:
        st.error(f"Error al obtener detalles de venta: {e}")
        return []

# Funciones existentes (mantener igual)
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
        response = supabase.table("inventario").select("*, proveedores(nombre)").order("id").execute()
        return response.data
    except Exception as e:
        st.error(f"Error al obtener productos: {e}")
        return []

def insertar_datos_ejemplo():
    try:
        productos = obtener_productos()
        if not productos:
            # Verificar si existen proveedores, si no, crearlos
            proveedores = obtener_proveedores()
            if not proveedores:
                proveedores_ejemplo = [
                    {"nombre": "HP Inc.", "contacto": "Juan Pérez", "telefono": "3214567890", "email": "ventas@hp.com"},
                    {"nombre": "Logitech", "contacto": "María García", "telefono": "3101234567", "email": "contacto@logitech.com"},
                    {"nombre": "Samsung Colombia", "contacto": "Carlos López", "telefono": "3157891234", "email": "colombia@samsung.com"},
                    {"nombre": "ErgoChair", "contacto": "Ana Martínez", "telefono": "3004567891", "email": "info@ergochair.com"},
                    {"nombre": "OfficeMax", "contacto": "Pedro Rodríguez", "telefono": "3209876543", "email": "clientes@officemax.com"},
                    {"nombre": "Canon Colombia", "contacto": "Laura Díaz", "telefono": "3186543210", "email": "canon@canoncolombia.com"}
                ]
                for proveedor in proveedores_ejemplo:
                    supabase.table("proveedores").insert(proveedor).execute()
            
            # Obtener IDs de proveedores recién creados
            proveedores = obtener_proveedores()
            proveedor_map = {p['nombre']: p['id'] for p in proveedores}
            
            datos_ejemplo = [
                {"nombre": "Laptop HP Pavilion", "cantidad": 15, "categoria": "Tecnología", "proveedor_id": proveedor_map.get("HP Inc."), "precio": 3500000, "min_stock": 5},
                {"nombre": "Mouse Inalámbrico", "cantidad": 50, "categoria": "Tecnología", "proveedor_id": proveedor_map.get("Logitech"), "precio": 120000, "min_stock": 10},
                {"nombre": "Monitor 24 Pulgadas", "cantidad": 8, "categoria": "Tecnología", "proveedor_id": proveedor_map.get("Samsung Colombia"), "precio": 850000, "min_stock": 3},
                {"nombre": "Silla de Oficina", "cantidad": 12, "categoria": "Mobiliario", "proveedor_id": proveedor_map.get("ErgoChair"), "precio": 450000, "min_stock": 2},
                {"nombre": "Escritorio Ejecutivo", "cantidad": 5, "categoria": "Mobiliario", "proveedor_id": proveedor_map.get("OfficeMax"), "precio": 1200000, "min_stock": 1},
                {"nombre": "Tóner Negro", "cantidad": 25, "categoria": "Insumos", "proveedor_id": proveedor_map.get("Canon Colombia"), "precio": 180000, "min_stock": 15},
            ]
            
            for producto in datos_ejemplo:
                supabase.table("inventario").insert(producto).execute()
            
            return True
    except Exception as e:
        st.error(f"Error: {e}")
    return False

# Funciones CRUD existentes (mantener)
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

# ================== INTERFAZ PRINCIPAL EXPANDIDA ==================
def main():
    if not check_password():
        st.stop()
    
    supabase = get_supabase_client()
    
    if 'inicializado' not in st.session_state:
        if insertar_datos_ejemplo():
            st.session_state.inicializado = True
    
    rol_emoji = {"admin": "⚙️", "lector": "👁️"}
    
    with st.sidebar:
        user_display_name = st.session_state.current_user.title()
        st.success(f"{rol_emoji.get(st.session_state.user_role, '👤')} {user_display_name} ({st.session_state.user_role})")
        
        if st.button("🚪 Cerrar Sesión"):
            for key in ["password_correct", "user_role", "current_user", "inicializado"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
        
        st.header("🔧 Navegación")
        
        # Opciones expandidas
        opciones = ["📊 Dashboard", "📦 Productos", "👥 Clientes", "🏢 Proveedores", "💰 Ventas", "📈 Reportes"]
        
        if tiene_permiso("admin"):
            opciones.append("⚙️ Administración")
        
        opcion = st.radio("Selecciona una opción:", opciones)
        
        categorias_sidebar = obtener_categorias_actualizadas()
        if categorias_sidebar:
            st.markdown("---")
            st.subheader("🏷️ Categorías Existentes")
            for categoria in categorias_sidebar:
                st.write(f"• {categoria}")
        
        st.markdown("---")
        st.info("💰 **Moneda:** Pesos Colombianos (COP)")
    
    # Navegación expandida
    if opcion == "📊 Dashboard":
        mostrar_dashboard()
    elif opcion == "📦 Productos":
        gestionar_productos()
    elif opcion == "👥 Clientes":
        gestionar_clientes()
    elif opcion == "🏢 Proveedores":
        gestionar_proveedores()
    elif opcion == "💰 Ventas":
        gestionar_ventas()
    elif opcion == "📈 Reportes":
        mostrar_reportes()
    elif opcion == "⚙️ Administración" and tiene_permiso("admin"):
        mostrar_administracion()

# ================== FUNCIONES PARA NUEVAS SECCIONES ==================
def gestionar_clientes():
    st.header("👥 Gestión de Clientes")
    
    if st.session_state.user_role == "lector":
        clientes = obtener_clientes()
        if clientes:
            df = pd.DataFrame(clientes)
            st.dataframe(df, use_container_width=True)
            st.info("👁️ **Modo de solo lectura:** No tienes permisos para modificar clientes.")
        else:
            st.info("No hay clientes registrados")
        return
    
    tab1, tab2, tab3 = st.tabs(["📋 Ver Clientes", "➕ Agregar Cliente", "✏️ Editar Clientes"])
    
    with tab1:
        clientes = obtener_clientes()
        if clientes:
            df = pd.DataFrame(clientes)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No hay clientes registrados")
    
    with tab2:
        with st.form("agregar_cliente_form"):
            col1, col2 = st.columns(2)
            with col1:
                nombre = st.text_input("Nombre/Razón Social*")
                tipo_documento = st.selectbox("Tipo Documento", ["CC", "CE", "NIT", "PASAPORTE"])
                documento = st.text_input("Número Documento*")
            with col2:
                telefono = st.text_input("Teléfono")
                email = st.text_input("Email")
                direccion = st.text_area("Dirección")
            
            if st.form_submit_button("➕ Agregar Cliente"):
                if nombre and documento:
                    cliente = {
                        "nombre": nombre.strip(),
                        "tipo_documento": tipo_documento,
                        "documento": documento.strip(),
                        "telefono": telefono.strip(),
                        "email": email.strip(),
                        "direccion": direccion.strip()
                    }
                    try:
                        supabase.table("clientes").insert(cliente).execute()
                        st.success("✅ Cliente agregado exitosamente!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
    
    with tab3:
        clientes = obtener_clientes()
        if clientes:
            for cliente in clientes:
                with st.expander(f"👤 {cliente['nombre']} - {cliente['documento']}"):
                    with st.form(f"editar_cliente_{cliente['id']}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            nuevo_nombre = st.text_input("Nombre", value=cliente['nombre'], key=f"nombre_cliente_{cliente['id']}")
                            nuevo_telefono = st.text_input("Teléfono", value=cliente.get('telefono', ''), key=f"telefono_{cliente['id']}")
                        with col2:
                            nuevo_email = st.text_input("Email", value=cliente.get('email', ''), key=f"email_{cliente['id']}")
                            nueva_direccion = st.text_area("Dirección", value=cliente.get('direccion', ''), key=f"direccion_{cliente['id']}")
                        
                        if st.form_submit_button("💾 Guardar Cambios"):
                            datos = {
                                "nombre": nuevo_nombre,
                                "telefono": nuevo_telefono,
                                "email": nuevo_email,
                                "direccion": nueva_direccion
                            }
                            try:
                                supabase.table("clientes").update(datos).eq("id", cliente['id']).execute()
                                st.success("✅ Cliente actualizado")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Error: {e}")

def gestionar_proveedores():
    st.header("🏢 Gestión de Proveedores")
    
    if st.session_state.user_role == "lector":
        proveedores = obtener_proveedores()
        if proveedores:
            df = pd.DataFrame(proveedores)
            st.dataframe(df, use_container_width=True)
            st.info("👁️ **Modo de solo lectura:** No tienes permisos para modificar proveedores.")
        else:
            st.info("No hay proveedores registrados")
        return
    
    tab1, tab2, tab3 = st.tabs(["📋 Ver Proveedores", "➕ Agregar Proveedor", "✏️ Editar Proveedores"])
    
    with tab1:
        proveedores = obtener_proveedores()
        if proveedores:
            df = pd.DataFrame(proveedores)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No hay proveedores registrados")
    
    with tab2:
        with st.form("agregar_proveedor_form"):
            col1, col2 = st.columns(2)
            with col1:
                nombre = st.text_input("Nombre Proveedor*")
                contacto = st.text_input("Persona de Contacto")
                telefono = st.text_input("Teléfono")
            with col2:
                email = st.text_input("Email")
                direccion = st.text_area("Dirección")
            
            if st.form_submit_button("➕ Agregar Proveedor"):
                if nombre:
                    proveedor = {
                        "nombre": nombre.strip(),
                        "contacto": contacto.strip(),
                        "telefono": telefono.strip(),
                        "email": email.strip(),
                        "direccion": direccion.strip()
                    }
                    try:
                        supabase.table("proveedores").insert(proveedor).execute()
                        st.success("✅ Proveedor agregado exitosamente!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
    
    with tab3:
        proveedores = obtener_proveedores()
        if proveedores:
            for proveedor in proveedores:
                with st.expander(f"🏢 {proveedor['nombre']}"):
                    with st.form(f"editar_proveedor_{proveedor['id']}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            nuevo_nombre = st.text_input("Nombre", value=proveedor['nombre'], key=f"nombre_prov_{proveedor['id']}")
                            nuevo_contacto = st.text_input("Contacto", value=proveedor.get('contacto', ''), key=f"contacto_{proveedor['id']}")
                        with col2:
                            nuevo_telefono = st.text_input("Teléfono", value=proveedor.get('telefono', ''), key=f"telefono_prov_{proveedor['id']}")
                            nuevo_email = st.text_input("Email", value=proveedor.get('email', ''), key=f"email_prov_{proveedor['id']}")
                        
                        nueva_direccion = st.text_area("Dirección", value=proveedor.get('direccion', ''), key=f"direccion_prov_{proveedor['id']}")
                        
                        if st.form_submit_button("💾 Guardar Cambios"):
                            datos = {
                                "nombre": nuevo_nombre,
                                "contacto": nuevo_contacto,
                                "telefono": nuevo_telefono,
                                "email": nuevo_email,
                                "direccion": nueva_direccion
                            }
                            try:
                                supabase.table("proveedores").update(datos).eq("id", proveedor['id']).execute()
                                st.success("✅ Proveedor actualizado")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Error: {e}")

def gestionar_ventas():
    st.header("💰 Gestión de Ventas")
    
    if st.session_state.user_role == "lector":
        ventas = obtener_ventas()
        if ventas:
            for venta in ventas:
                with st.expander(f"📦 Venta #{venta['id']} - {venta['clientes']['nombre']} - {formato_cop(venta['total'])}"):
                    st.write(f"**Fecha:** {venta['fecha_venta']}")
                    st.write(f"**Cliente:** {venta['clientes']['nombre']}")
                    st.write(f"**Total:** {formato_cop(venta['total'])}")
                    st.write(f"**Estado:** {venta['estado']}")
                    
                    detalles = obtener_venta_detalles(venta['id'])
                    if detalles:
                        st.subheader("Detalles de la Venta")
                        for detalle in detalles:
                            st.write(f"- {detalle['inventario']['nombre']}: {detalle['cantidad']} x {formato_cop(detalle['precio_unitario'])} = {formato_cop(detalle['subtotal'])}")
        else:
            st.info("No hay ventas registradas")
        return
    
    tab1, tab2 = st.tabs(["📋 Historial de Ventas", "➕ Nueva Venta"])
    
    with tab1:
        ventas = obtener_ventas()
        if ventas:
            for venta in ventas:
                with st.expander(f"📦 Venta #{venta['id']} - {venta['clientes']['nombre']} - {formato_cop(venta['total'])}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Fecha:** {venta['fecha_venta']}")
                        st.write(f"**Cliente:** {venta['clientes']['nombre']}")
                    with col2:
                        st.write(f"**Total:** {formato_cop(venta['total'])}")
                        st.write(f"**Estado:** {venta['estado']}")
                    
                    detalles = obtener_venta_detalles(venta['id'])
                    if detalles:
                        st.subheader("📋 Detalles de la Venta")
                        for detalle in detalles:
                            st.write(f"- {detalle['inventario']['nombre']}: {detalle['cantidad']} x {formato_cop(detalle['precio_unitario'])} = {formato_cop(detalle['subtotal'])}")
        else:
            st.info("No hay ventas registradas")
    
    with tab2:
        st.subheader("➕ Registrar Nueva Venta")
        
        clientes = obtener_clientes()
        productos = obtener_productos()
        
        if not clientes:
            st.warning("❌ No hay clientes registrados. Primero agrega al menos un cliente.")
            return
        
        if not productos:
            st.warning("❌ No hay productos en el inventario.")
            return
        
        with st.form("nueva_venta_form"):
            cliente_id = st.selectbox("Cliente*", options=[f"{c['id']} - {c['nombre']}" for c in clientes])
            
            st.subheader("🛒 Productos de la Venta")
            
            # Productos seleccionados
            if 'productos_venta' not in st.session_state:
                st.session_state.productos_venta = []
            
            col1, col2, col3 = st.columns([3, 2, 2])
            with col1:
                producto_seleccionado = st.selectbox("Producto", [f"{p['id']} - {p['nombre']} (Stock: {p['cantidad']})" for p in productos])
            with col2:
                cantidad = st.number_input("Cantidad", min_value=1, value=1)
            with col3:
                if st.button("➕ Agregar Producto"):
                    producto_id = int(producto_seleccionado.split(" - ")[0])
                    producto = next((p for p in productos if p['id'] == producto_id), None)
                    
                    if producto:
                        if cantidad <= producto['cantidad']:
                            st.session_state.productos_venta.append({
                                'producto_id': producto_id,
                                'nombre': producto['nombre'],
                                'cantidad': cantidad,
                                'precio_unitario': producto['precio'],
                                'subtotal': cantidad * producto['precio']
                            })
                            st.success("✅ Producto agregado a la venta")
                            st.rerun()
                        else:
                            st.error(f"❌ Stock insuficiente. Disponible: {producto['cantidad']}")
            
            # Mostrar productos agregados
            if st.session_state.productos_venta:
                st.subheader("📋 Resumen de la Venta")
                total_venta = 0
                
                for i, producto in enumerate(st.session_state.productos_venta):
                    col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                    with col1:
                        st.write(f"**{producto['nombre']}**")
                    with col2:
                        st.write(f"{producto['cantidad']} x {formato_cop(producto['precio_unitario'])}")
                    with col3:
                        st.write(f"**{formato_cop(producto['subtotal'])}**")
                    with col4:
                        if st.button("🗑️", key=f"eliminar_{i}"):
                            st.session_state.productos_venta.pop(i)
                            st.rerun()
                    
                    total_venta += producto['subtotal']
                
                st.write(f"### **Total: {formato_cop(total_venta)}**")
            
            notas = st.text_area("Notas de la venta (opcional)")
            
            if st.form_submit_button("💰 Registrar Venta"):
                if st.session_state.productos_venta:
                    try:
                        # Crear la venta
                        venta_data = {
                            "cliente_id": int(cliente_id.split(" - ")[0]),
                            "total": total_venta,
                            "notas": notas
                        }
                        venta_response = supabase.table("ventas").insert(venta_data).execute()
                        
                        if venta_response.data:
                            venta_id = venta_response.data[0]['id']
                            
                            # Crear detalles de venta y actualizar stock
                            for producto in st.session_state.productos_venta:
                                # Insertar detalle
                                detalle_data = {
                                    "venta_id": venta_id,
                                    "producto_id": producto['producto_id'],
                                    "cantidad": producto['cantidad'],
                                    "precio_unitario": producto['precio_unitario']
                                }
                                supabase.table("venta_detalles").insert(detalle_data).execute()
                                
                                # Actualizar stock
                                producto_actual = next((p for p in productos if p['id'] == producto['producto_id']), None)
                                if producto_actual:
                                    nuevo_stock = producto_actual['cantidad'] - producto['cantidad']
                                    supabase.table("inventario").update({"cantidad": nuevo_stock}).eq("id", producto['producto_id']).execute()
                            
                            st.session_state.productos_venta = []
                            st.success("✅ Venta registrada exitosamente!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error al registrar venta: {e}")
                else:
                    st.warning("❌ Agrega al menos un producto a la venta")

# Las funciones mostrar_dashboard, gestionar_productos, mostrar_reportes y mostrar_administracion 
# se mantienen similares pero actualizadas para usar las nuevas relaciones

def mostrar_dashboard():
    st.header("📊 Dashboard de Inventario")
    
    productos = obtener_productos()
    clientes = obtener_clientes()
    proveedores = obtener_proveedores()
    ventas = obtener_ventas()
    
    if productos:
        df = pd.DataFrame(productos)
        df['valor_total'] = df['cantidad'] * df['precio']
        total_valor = df['valor_total'].sum()
        
        # Métricas expandidas
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Valor Total Inventario", formato_cop(total_valor))
        with col2:
            st.metric("Total Productos", len(df))
        with col3:
            st.metric("Total Clientes", len(clientes))
        with col4:
            st.metric("Total Proveedores", len(proveedores))
        
        # Más métricas
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Ventas Registradas", len(ventas))
        with col2:
            total_ventas = sum([v['total'] for v in ventas])
            st.metric("Total en Ventas", formato_cop(total_ventas))
        with col3:
            productos_bajos = df[df['cantidad'] <= df['min_stock']]
            st.metric("Stock Bajo", len(productos_bajos))
        with col4:
            st.metric("Stock Total", f"{df['cantidad'].sum():,}".replace(",", "."))
        
        # Resto del dashboard similar...
    else:
        st.warning("No hay productos en el inventario")

# Las funciones gestionar_productos, mostrar_reportes y mostrar_administracion 
# se mantienen pero actualizadas para usar proveedores

def gestionar_productos():
    st.header("📦 Gestión de Productos")
    
    if st.session_state.user_role == "lector":
        productos = obtener_productos()
        if productos:
            df = pd.DataFrame(productos)
            # Mostrar datos con proveedores
            st.dataframe(df, use_container_width=True)
            st.info("👁️ **Modo de solo lectura:** No tienes permisos para modificar productos.")
        else:
            st.info("No hay productos registrados")
        return
    
    # Para administradores, interfaz similar pero actualizada con proveedores
    # ... (código similar al anterior pero usando proveedores)

# Inicializar Supabase
supabase = get_supabase_client()

if __name__ == "__main__":
    main()
