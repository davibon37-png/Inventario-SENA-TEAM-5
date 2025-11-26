import streamlit as st
from utils.supabase_client import get_supabase_client
import pandas as pd
from datetime import datetime, timedelta

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
        response = supabase.table("proveedores").select("*").order("id").execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Error al obtener proveedores: {e}")
        return []

def obtener_clientes():
    """Obtener lista de clientes desde la base de datos"""
    try:
        response = supabase.table("clientes").select("*").order("id").execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Error al obtener clientes: {e}")
        return []

def obtener_ventas():
    """Obtener ventas con información de clientes y productos"""
    try:
        response = supabase.table("ventas").select("*, clientes(*), inventario(nombre, categoria)").order("fecha_venta", desc=True).execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Error al obtener ventas: {e}")
        return []

def obtener_movimientos_inventario():
    """Obtener movimientos de inventario"""
    try:
        response = supabase.table("movimientos_inventario").select("*, inventario(nombre)").order("fecha", desc=True).execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Error al obtener movimientos: {e}")
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

def agregar_proveedor(nombre, contacto, telefono, email, direccion):
    """Agregar nuevo proveedor"""
    try:
        proveedor_data = {
            "nombre": nombre.strip(),
            "contacto": contacto.strip(),
            "telefono": telefono.strip(),
            "email": email.strip(),
            "direccion": direccion.strip()
        }
        
        response = supabase.table("proveedores").insert(proveedor_data).execute()
        return bool(response.data)
    except Exception as e:
        st.error(f"Error al agregar proveedor: {e}")
        return False

def agregar_cliente(nombre, tipo_documento, documento, telefono, email, direccion):
    """Agregar nuevo cliente"""
    try:
        cliente_data = {
            "nombre": nombre.strip(),
            "tipo_documento": tipo_documento,
            "documento": documento.strip(),
            "telefono": telefono.strip(),
            "email": email.strip(),
            "direccion": direccion.strip()
        }
        
        response = supabase.table("clientes").insert(cliente_data).execute()
        return bool(response.data)
    except Exception as e:
        st.error(f"Error al agregar cliente: {e}")
        return False

def agregar_venta(cliente_id, producto_id, cantidad, precio_unitario, notas=""):
    """Agregar nueva venta"""
    try:
        total = cantidad * precio_unitario
        
        venta_data = {
            "cliente_id": cliente_id,
            "producto_id": producto_id,
            "cantidad": cantidad,
            "precio_unitario": precio_unitario,
            "total": total,
            "notas": notas.strip()
        }
        
        response = supabase.table("ventas").insert(venta_data).execute()
        
        # Actualizar stock del producto
        producto_actual = supabase.table("inventario").select("cantidad").eq("id", producto_id).execute()
        if producto_actual.data:
            nueva_cantidad = producto_actual.data[0]['cantidad'] - cantidad
            supabase.table("inventario").update({"cantidad": nueva_cantidad}).eq("id", producto_id).execute()
            
            # Registrar movimiento de inventario
            movimiento_data = {
                "producto_id": producto_id,
                "tipo": "salida",
                "cantidad": cantidad,
                "notas": f"Venta registrada - {notas.strip()}" if notas else "Venta registrada"
            }
            supabase.table("movimientos_inventario").insert(movimiento_data).execute()
        
        return bool(response.data)
    except Exception as e:
        st.error(f"Error al agregar venta: {e}")
        return False

def agregar_movimiento(producto_id, tipo, cantidad, notas):
    """Agregar movimiento de inventario"""
    try:
        movimiento_data = {
            "producto_id": producto_id,
            "tipo": tipo,
            "cantidad": cantidad,
            "notas": notas.strip(),
            "fecha": datetime.now().isoformat()
        }
        
        response = supabase.table("movimientos_inventario").insert(movimiento_data).execute()
        
        # Actualizar stock del producto
        producto_actual = supabase.table("inventario").select("cantidad").eq("id", producto_id).execute()
        if producto_actual.data:
            stock_actual = producto_actual.data[0]['cantidad']
            if tipo == "entrada":
                nueva_cantidad = stock_actual + cantidad
            elif tipo == "salida":
                nueva_cantidad = stock_actual - cantidad
            else:  # ajuste
                nueva_cantidad = cantidad
                
            supabase.table("inventario").update({"cantidad": nueva_cantidad}).eq("id", producto_id).execute()
        
        return bool(response.data)
    except Exception as e:
        st.error(f"Error al agregar movimiento: {e}")
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
        opciones = ["📊 Dashboard", "📦 Productos", "👥 Clientes", "🏢 Proveedores", "💰 Ventas", "🔄 Movimientos", "📈 Reportes"]
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
    elif opcion == "👥 Clientes":
        gestionar_clientes()
    elif opcion == "🏢 Proveedores":
        gestionar_proveedores()
    elif opcion == "💰 Ventas":
        gestionar_ventas()
    elif opcion == "🔄 Movimientos":
        gestionar_movimientos()
    elif opcion == "📈 Reportes":
        mostrar_reportes()
    elif opcion == "⚙️ Administración":
        mostrar_administracion()

def mostrar_dashboard():
    st.header("📊 Dashboard de Inventario")
    
    productos = obtener_productos()
    ventas = obtener_ventas()
    
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
    col1.metric("Valor Total Inventario", f"${total_valor:,.0f}".replace(",", "."))
    col2.metric("Total Productos", len(df))
    col3.metric("Stock Total", f"{df['cantidad'].sum():,}".replace(",", "."))
    
    # Ventas del mes
    ventas_mes = 0
    if ventas:
        mes_actual = datetime.now().month
        ventas_mes = sum(v['total'] for v in ventas if datetime.fromisoformat(v['fecha_venta']).month == mes_actual)
    col4.metric("Ventas del Mes", f"${ventas_mes:,.0f}".replace(",", "."))
    
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

def gestionar_clientes():
    st.header("👥 Gestión de Clientes")
    
    tab1, tab2 = st.tabs(["📋 Lista de Clientes", "➕ Agregar Cliente"])
    
    with tab1:
        clientes = obtener_clientes()
        if clientes:
            df = pd.DataFrame(clientes)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No hay clientes registrados")
    
    with tab2:
        st.subheader("Agregar Nuevo Cliente")
        with st.form("agregar_cliente_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                nombre = st.text_input("Nombre/Razón Social*")
                tipo_documento = st.selectbox("Tipo de Documento*", ["CC", "NIT", "CE", "PASAPORTE"])
                documento = st.text_input("Número de Documento*")
            with col2:
                telefono = st.text_input("Teléfono")
                email = st.text_input("Email")
                direccion = st.text_area("Dirección")
            
            if st.form_submit_button("➕ Agregar Cliente"):
                if nombre and tipo_documento and documento:
                    if agregar_cliente(nombre, tipo_documento, documento, telefono, email, direccion):
                        st.success("✅ Cliente agregado exitosamente!")
                        st.rerun()
                else:
                    st.error("❌ Los campos marcados con * son obligatorios")

def gestionar_proveedores():
    st.header("🏢 Gestión de Proveedores")
    
    tab1, tab2 = st.tabs(["📋 Lista de Proveedores", "➕ Agregar Proveedor"])
    
    with tab1:
        proveedores = obtener_proveedores()
        if proveedores:
            df = pd.DataFrame(proveedores)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No hay proveedores registrados")
    
    with tab2:
        st.subheader("Agregar Nuevo Proveedor")
        with st.form("agregar_proveedor_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                nombre = st.text_input("Nombre del Proveedor*")
                contacto = st.text_input("Persona de Contacto")
                telefono = st.text_input("Teléfono")
            with col2:
                email = st.text_input("Email")
                direccion = st.text_area("Dirección")
            
            if st.form_submit_button("➕ Agregar Proveedor"):
                if nombre:
                    if agregar_proveedor(nombre, contacto, telefono, email, direccion):
                        st.success("✅ Proveedor agregado exitosamente!")
                        st.rerun()
                else:
                    st.error("❌ El nombre del proveedor es obligatorio")

def gestionar_ventas():
    st.header("💰 Gestión de Ventas")
    
    tab1, tab2 = st.tabs(["📋 Historial de Ventas", "➕ Nueva Venta"])
    
    with tab1:
        ventas = obtener_ventas()
        if ventas:
            venta_data = []
            for venta in ventas:
                venta_data.append({
                    'ID': venta['id'],
                    'Fecha': venta['fecha_venta'][:19],
                    'Cliente': venta['clientes']['nombre'] if venta['clientes'] else 'N/A',
                    'Producto': venta['inventario']['nombre'] if venta['inventario'] else 'N/A',
                    'Cantidad': venta['cantidad'],
                    'Precio Unitario': f"${venta['precio_unitario']:,.0f}".replace(",", "."),
                    'Total': f"${venta['total']:,.0f}".replace(",", "."),
                    'Estado': venta['estado']
                })
            
            df = pd.DataFrame(venta_data)
            st.dataframe(df, use_container_width=True)
            
            # Métricas rápidas
            total_ventas = sum(v['total'] for v in ventas)
            st.metric("💰 Total en Ventas", f"${total_ventas:,.0f}".replace(",", "."))
        else:
            st.info("No hay ventas registradas")
    
    with tab2:
        st.subheader("Registrar Nueva Venta")
        clientes = obtener_clientes()
        productos = obtener_productos()
        
        with st.form("nueva_venta_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                if clientes:
                    cliente_seleccionado = st.selectbox("Cliente*", 
                                                      options=[f"{c['id']} - {c['nombre']}" for c in clientes])
                    cliente_id = int(cliente_seleccionado.split(" - ")[0]) if cliente_seleccionado else None
                else:
                    st.warning("No hay clientes registrados")
                    cliente_id = None
                
                if productos:
                    # Filtrar productos con stock disponible
                    productos_con_stock = [p for p in productos if p['cantidad'] > 0]
                    if productos_con_stock:
                        producto_seleccionado = st.selectbox("Producto*", 
                                                           options=[f"{p['id']} - {p['nombre']} (Stock: {p['cantidad']})" for p in productos_con_stock])
                        producto_id = int(producto_seleccionado.split(" - ")[0]) if producto_seleccionado else None
                        
                        # Mostrar información del producto seleccionado
                        if producto_seleccionado:
                            producto_info = next((p for p in productos if p['id'] == producto_id), None)
                            if producto_info:
                                st.info(f"💡 **Precio actual:** ${producto_info['precio']:,.0f}".replace(",", "."))
                    else:
                        st.error("❌ No hay productos con stock disponible")
                        producto_id = None
                else:
                    st.warning("No hay productos disponibles")
                    producto_id = None
                
            with col2:
                cantidad = st.number_input("Cantidad*", min_value=1, value=1)
                precio_unitario = st.number_input("Precio Unitario (COP)*", min_value=0, value=0, step=1000)
                notas = st.text_area("Notas/Observaciones")
            
            if st.form_submit_button("💰 Registrar Venta"):
                if cliente_id and producto_id and cantidad > 0 and precio_unitario > 0:
                    # Verificar stock disponible
                    producto_info = next((p for p in productos if p['id'] == producto_id), None)
                    if producto_info and producto_info['cantidad'] >= cantidad:
                        if agregar_venta(cliente_id, producto_id, cantidad, precio_unitario, notas):
                            st.success("✅ Venta registrada exitosamente!")
                            st.rerun()
                    else:
                        stock_disponible = producto_info['cantidad'] if producto_info else 0
                        st.error(f"❌ Stock insuficiente. Stock disponible: {stock_disponible}")
                else:
                    st.error("❌ Complete todos los campos requeridos")

def gestionar_movimientos():
    st.header("🔄 Movimientos de Inventario")
    
    movimientos = obtener_movimientos_inventario()
    if not movimientos:
        st.info("No hay movimientos registrados")
        return
    
    # Filtrar por tipo de movimiento
    tipos = list(set([m['tipo'] for m in movimientos if m.get('tipo')]))
    tipo_seleccionado = st.selectbox("Filtrar por tipo:", ["Todos"] + tipos)
    
    movimientos_filtrados = movimientos
    if tipo_seleccionado != "Todos":
        movimientos_filtrados = [m for m in movimientos if m.get('tipo') == tipo_seleccionado]
    
    # Mostrar movimientos
    movimiento_data = []
    for mov in movimientos_filtrados:
        movimiento_data.append({
            'ID': mov['id'],
            'Fecha': mov['fecha'][:19],
            'Producto': mov['inventario']['nombre'] if mov['inventario'] else 'N/A',
            'Tipo': mov['tipo'],
            'Cantidad': mov['cantidad'],
            'Notas': mov['notas'] or 'Sin notas'
        })
    
    df = pd.DataFrame(movimiento_data)
    st.dataframe(df, use_container_width=True)
    
    # Formulario para agregar movimiento
    if tiene_permiso("admin"):
        st.subheader("➕ Agregar Nuevo Movimiento")
        productos = obtener_productos()
        
        with st.form("agregar_movimiento_form"):
            col1, col2 = st.columns(2)
            with col1:
                if productos:
                    producto_seleccionado = st.selectbox("Producto*", 
                                                       options=[f"{p['id']} - {p['nombre']}" for p in productos],
                                                       key="movimiento_producto")
                    producto_id = int(producto_seleccionado.split(" - ")[0]) if producto_seleccionado else None
                else:
                    st.warning("No hay productos disponibles")
                    producto_id = None
                    
                tipo = st.selectbox("Tipo de Movimiento*", ["entrada", "salida", "ajuste"])
            with col2:
                cantidad = st.number_input("Cantidad*", min_value=1, value=1)
                notas = st.text_area("Notas/Observaciones")
            
            if st.form_submit_button("➕ Agregar Movimiento"):
                if producto_id:
                    if agregar_movimiento(producto_id, tipo, cantidad, notas):
                        st.success("✅ Movimiento agregado exitosamente!")
                        st.rerun()

def mostrar_reportes():
    st.header("📈 Reportes y Análisis")
    
    # Selección de tipo de reporte
    tipo_reporte = st.selectbox("Seleccionar Tipo de Reporte", 
                               ["Inventario", "Ventas", "Movimientos", "Clientes", "Proveedores"])
    
    if tipo_reporte == "Inventario":
        mostrar_reporte_inventario()
    elif tipo_reporte == "Ventas":
        mostrar_reporte_ventas()
    elif tipo_reporte == "Movimientos":
        mostrar_reporte_movimientos()
    elif tipo_reporte == "Clientes":
        mostrar_reporte_clientes()
    elif tipo_reporte == "Proveedores":
        mostrar_reporte_proveedores()

def mostrar_reporte_inventario():
    st.subheader("📊 Reporte de Inventario")
    
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
            'nombre': p.get('nombre', ''),
            'categoria': p.get('categoria', ''),
            'cantidad': p.get('cantidad', 0),
            'precio': p.get('precio', 0),
            'proveedor': proveedor_nombre,
            'valor_total': p.get('cantidad', 0) * p.get('precio', 0)
        })
    df = pd.DataFrame(df_data)
    
    # Resumen
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Valor Total", f"${df['valor_total'].sum():,.0f}".replace(",", "."))
    col2.metric("Productos", len(df))
    col3.metric("Stock Total", df['cantidad'].sum())
    col4.metric("Categorías", df['categoria'].nunique())
    
    # Resumen por categoría
    st.subheader("Resumen por Categoría")
    resumen_categorias = df.groupby('categoria').agg({
        'nombre': 'count',
        'cantidad': 'sum',
        'valor_total': 'sum'
    }).rename(columns={'nombre': 'Cantidad Productos'})
    st.dataframe(resumen_categorias, use_container_width=True)
    
    # Gráficos
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Productos por Categoría")
        conteo_categorias = df['categoria'].value_counts()
        st.bar_chart(conteo_categorias)
    with col2:
        st.subheader("Valor por Categoría")
        valor_por_categoria = df.groupby('categoria')['valor_total'].sum()
        st.bar_chart(valor_por_categoria)
    
    # Exportar reporte
    csv = df.to_csv(index=False)
    st.download_button("📥 Descargar Reporte CSV", csv, "reporte_inventario.csv", "text/csv")

def mostrar_reporte_ventas():
    st.subheader("💰 Reporte de Ventas")
    
    ventas = obtener_ventas()
    if not ventas:
        st.warning("No hay ventas para mostrar")
        return
    
    # Filtrar por fecha
    col1, col2 = st.columns(2)
    with col1:
        fecha_inicio = st.date_input("Fecha de inicio", value=datetime.now() - timedelta(days=30))
    with col2:
        fecha_fin = st.date_input("Fecha de fin", value=datetime.now())
    
    ventas_filtradas = [
        v for v in ventas 
        if fecha_inicio <= datetime.fromisoformat(v['fecha_venta']).date() <= fecha_fin
    ]
    
    if not ventas_filtradas:
        st.info("No hay ventas en el período seleccionado")
        return
    
    # Métricas
    total_ventas = sum(v['total'] for v in ventas_filtradas)
    cantidad_ventas = len(ventas_filtradas)
    venta_promedio = total_ventas / cantidad_ventas if cantidad_ventas > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Ventas", f"${total_ventas:,.0f}".replace(",", "."))
    col2.metric("Cantidad Ventas", cantidad_ventas)
    col3.metric("Venta Promedio", f"${venta_promedio:,.0f}".replace(",", "."))
    
    # Tabla de ventas
    venta_data = []
    for venta in ventas_filtradas:
        venta_data.append({
            'ID': venta['id'],
            'Fecha': venta['fecha_venta'][:10],
            'Cliente': venta['clientes']['nombre'] if venta['clientes'] else 'N/A',
            'Producto': venta['inventario']['nombre'] if venta['inventario'] else 'N/A',
            'Cantidad': venta['cantidad'],
            'Precio Unitario': venta['precio_unitario'],
            'Total': venta['total'],
            'Estado': venta['estado']
        })
    
    df_ventas = pd.DataFrame(venta_data)
    st.dataframe(df_ventas, use_container_width=True)
    
    # Gráfico de ventas por día
    st.subheader("Ventas por Día")
    if ventas_filtradas:
        ventas_por_dia = {}
        for venta in ventas_filtradas:
            fecha = venta['fecha_venta'][:10]
            if fecha not in ventas_por_dia:
                ventas_por_dia[fecha] = 0
            ventas_por_dia[fecha] += venta['total']
        
        df_ventas_dia = pd.DataFrame(list(ventas_por_dia.items()), columns=['Fecha', 'Total'])
        df_ventas_dia = df_ventas_dia.sort_values('Fecha')
        st.line_chart(df_ventas_dia.set_index('Fecha'))
    
    # Exportar reporte
    csv = df_ventas.to_csv(index=False)
    st.download_button("📥 Descargar Reporte CSV", csv, "reporte_ventas.csv", "text/csv")

def mostrar_reporte_movimientos():
    st.subheader("🔄 Reporte de Movimientos")
    
    movimientos = obtener_movimientos_inventario()
    if not movimientos:
        st.warning("No hay movimientos para mostrar")
        return
    
    # Resumen por tipo
    tipos_movimiento = {}
    for mov in movimientos:
        tipo = mov.get('tipo', 'desconocido')
        if tipo not in tipos_movimiento:
            tipos_movimiento[tipo] = 0
        tipos_movimiento[tipo] += mov.get('cantidad', 0)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Movimientos", len(movimientos))
    with col2:
        st.metric("Tipos Diferentes", len(tipos_movimiento))
    
    # Gráfico de movimientos por tipo
    st.subheader("Movimientos por Tipo")
    df_tipos = pd.DataFrame(list(tipos_movimiento.items()), columns=['Tipo', 'Cantidad'])
    st.bar_chart(df_tipos.set_index('Tipo'))
    
    # Tabla detallada
    movimiento_data = []
    for mov in movimientos:
        movimiento_data.append({
            'Fecha': mov['fecha'][:19],
            'Producto': mov['inventario']['nombre'] if mov['inventario'] else 'N/A',
            'Tipo': mov['tipo'],
            'Cantidad': mov['cantidad'],
            'Notas': mov['notas'] or 'Sin notas'
        })
    
    df_movimientos = pd.DataFrame(movimiento_data)
    st.dataframe(df_movimientos, use_container_width=True)
    
    # Exportar reporte
    csv = df_movimientos.to_csv(index=False)
    st.download_button("📥 Descargar Reporte CSV", csv, "reporte_movimientos.csv", "text/csv")

def mostrar_reporte_clientes():
    st.subheader("👥 Reporte de Clientes")
    
    clientes = obtener_clientes()
    if not clientes:
        st.warning("No hay clientes para mostrar")
        return
    
    # Métricas
    total_clientes = len(clientes)
    clientes_activos = sum(1 for c in clientes if c.get('activo', True))
    
    col1, col2 = st.columns(2)
    col1.metric("Total Clientes", total_clientes)
    col2.metric("Clientes Activos", clientes_activos)
    
    # Distribución por tipo de documento
    tipos_documento = {}
    for cliente in clientes:
        tipo = cliente.get('tipo_documento', 'No especificado')
        if tipo not in tipos_documento:
            tipos_documento[tipo] = 0
        tipos_documento[tipo] += 1
    
    st.subheader("Distribución por Tipo de Documento")
    df_tipos = pd.DataFrame(list(tipos_documento.items()), columns=['Tipo Documento', 'Cantidad'])
    st.bar_chart(df_tipos.set_index('Tipo Documento'))
    
    # Tabla de clientes
    df_clientes = pd.DataFrame(clientes)
    st.dataframe(df_clientes, use_container_width=True)
    
    # Exportar reporte
    csv = df_clientes.to_csv(index=False)
    st.download_button("📥 Descargar Reporte CSV", csv, "reporte_clientes.csv", "text/csv")

def mostrar_reporte_proveedores():
    st.subheader("🏢 Reporte de Proveedores")
    
    proveedores = obtener_proveedores()
    if not proveedores:
        st.warning("No hay proveedores para mostrar")
        return
    
    # Métricas
    total_proveedores = len(proveedores)
    proveedores_activos = sum(1 for p in proveedores if p.get('activo', True))
    
    col1, col2 = st.columns(2)
    col1.metric("Total Proveedores", total_proveedores)
    col2.metric("Proveedores Activos", proveedores_activos)
    
    # Productos por proveedor
    productos = obtener_productos()
    productos_por_proveedor = {}
    for producto in productos:
        proveedor_id = producto.get('provedor_id')
        if proveedor_id:
            proveedor_nombre = next((p['nombre'] for p in proveedores if p['id'] == proveedor_id), 'Desconocido')
            if proveedor_nombre not in productos_por_proveedor:
                productos_por_proveedor[proveedor_nombre] = 0
            productos_por_proveedor[proveedor_nombre] += 1
    
    st.subheader("Productos por Proveedor")
    df_productos_proveedor = pd.DataFrame(list(productos_por_proveedor.items()), columns=['Proveedor', 'Cantidad Productos'])
    st.bar_chart(df_productos_proveedor.set_index('Proveedor'))
    
    # Tabla de proveedores
    df_proveedores = pd.DataFrame(proveedores)
    st.dataframe(df_proveedores, use_container_width=True)
    
    # Exportar reporte
    csv = df_proveedores.to_csv(index=False)
    st.download_button("📥 Descargar Reporte CSV", csv, "reporte_proveedores.csv", "text/csv")

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
        if st.button("📊 Generar Reporte Completo"):
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
