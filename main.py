import streamlit as st
import pandas as pd
import requests
from datetime import date

st.set_page_config(page_title="CeroDescuadres Comercial", layout="wide")

# 1. Configuración de API Directa (Sin usar la librería conflictiva de Supabase)
URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]

def get_headers(token=None):
    h = {"apikey": KEY, "Content-Type": "application/json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h

# 2. Pantalla de Seguridad (Login / Registro)
if 'user_token' not in st.session_state:
    st.session_state.user_token = None
    st.session_state.user_email = None
    st.session_state.user_id = None

if st.session_state.user_token is None:
    st.title("🔒 CeroDescuadres - Acceso Clientes")

    # Creamos las pestañas (la primera es la que sale por defecto)
    tab_login, tab_registro = st.tabs(["🔑 Iniciar Sesión", "📝 Crear nueva cuenta"])

    with tab_login:
        st.subheader("Acceso a tu cuenta")
        email_login = st.text_input("Correo electrónico", key="log_email")
        pass_login = st.text_input("Contraseña", type="password", key="log_pass")
        if st.button("Entrar"):
            res = requests.post(
                f"{URL}/auth/v1/token?grant_type=password",
                json={"email": email_login, "password": pass_login},
                headers=get_headers()
            )
            if res.status_code == 200:
                data = res.json()
                st.session_state.user_token = data['access_token']
                st.session_state.user_id = data['user']['id']
                st.session_state.user_email = data['user']['email']
                st.rerun()
            else:
                st.error("Credenciales incorrectas.")

    with tab_registro:
        st.subheader("Nuevo Cliente")
        email_reg = st.text_input("Correo electrónico", key="reg_email")
        pass_reg = st.text_input("Contraseña", type="password", key="reg_pass")
        if st.button("Crear Cuenta"):
            res = requests.post(
                f"{URL}/auth/v1/signup",
                json={"email": email_reg, "password": pass_reg},
                headers=get_headers()
            )
            if res.status_code == 200:
                st.success("Cuenta creada con éxito. Ve a la pestaña 'Iniciar Sesión' para entrar.")
            else:
                st.error(f"Error del servidor: {res.text}")
    st.stop() # Bloquea el resto de la app si no hay sesión

# --- A PARTIR DE AQUÍ: EL USUARIO ESTÁ DENTRO DE SU CUENTA ---

st.sidebar.success(f"👤 {st.session_state.user_email}")
if st.sidebar.button("Cerrar Sesión"):
    st.session_state.user_token = None
    st.rerun()

st.title("CeroDescuadres - Panel de Control PRO")

# 3. Cargar datos desde la nube
def cargar_datos():
    res = requests.get(
        f"{URL}/rest/v1/movimientos?select=*",
        headers=get_headers(st.session_state.user_token)
    )
    if res.status_code == 200 and len(res.json()) > 0:
        return pd.DataFrame(res.json())
    else:
        return pd.DataFrame(columns=["id", "fecha", "cliente_proveedor", "concepto", "tipo", "categoria", "estado", "importe", "fecha_vencimiento"])

df = cargar_datos()

# Dashboard Métricas
if not df.empty:
    df['importe'] = pd.to_numeric(df['importe'], errors='coerce').fillna(0)
    ingresos = df[(df['tipo'] == 'Ingreso') & (df['estado'] == 'Cobrado/Pagado')]['importe'].sum()
    gastos = df[(df['tipo'] == 'Gasto') & (df['estado'] == 'Cobrado/Pagado')]['importe'].sum()
    aperturas = df[(df['tipo'] == 'Apertura') & (df['estado'] == 'Cobrado/Pagado')]['importe'].sum()
    cierres = df[(df['tipo'] == 'Cierre') & (df['estado'] == 'Cobrado/Pagado')]['importe'].sum()

    caja_real = (ingresos + aperturas) - (gastos + cierres)
    por_cobrar = df[(df['tipo'] == 'Ingreso') & (df['estado'] == 'Pendiente')]['importe'].sum()
    por_pagar = df[(df['tipo'] == 'Gasto') & (df['estado'] == 'Pendiente')]['importe'].sum()
else:
    caja_real = por_cobrar = por_pagar = 0

col1, col2, col3 = st.columns(3)
col1.metric("💰 Caja Real", f"{caja_real:,.2f} €")
col2.metric("🟢 Por Cobrar", f"{por_cobrar:,.2f} €")
col3.metric("🔴 Por Pagar", f"{por_pagar:,.2f} €")
st.divider()

# Barra Lateral: Nuevo Registro
st.sidebar.header("Nueva Operación")
fecha = st.sidebar.date_input("Fecha", date.today())
cliente_final = st.sidebar.text_input("Cliente / Proveedor")
concepto = st.sidebar.text_input("Concepto")
tipo = st.sidebar.selectbox("Tipo", ["Ingreso", "Gasto", "Apertura", "Cierre"])
categoria = st.sidebar.selectbox("Categoría", ["Ventas", "Suministros", "Nóminas", "Impuestos", "Servicios", "Otros"])
estado = st.sidebar.selectbox("Estado", ["Pendiente", "Cobrado/Pagado"])
importe = st.sidebar.number_input("Importe (€)", min_value=0.0, format="%.2f", step=1.0)
vencimiento_final = ""
if st.sidebar.checkbox("📅 Fecha límite"):
    vencimiento_final = st.sidebar.date_input("Vencimiento", date.today())

if st.sidebar.button("Registrar en la Nube ✅"):
    if cliente_final.strip() != "":
        nuevo_registro = {
            "user_id": st.session_state.user_id,
            "fecha": str(fecha),
            "cliente_proveedor": cliente_final.strip(),
            "concepto": concepto,
            "tipo": tipo,
            "categoria": categoria,
            "estado": estado,
            "importe": importe,
            "fecha_vencimiento": str(vencimiento_final)
        }

        headers_post = get_headers(st.session_state.user_token)
        headers_post["Prefer"] = "return=minimal"

        requests.post(
            f"{URL}/rest/v1/movimientos",
            json=nuevo_registro,
            headers=headers_post
        )
        st.rerun()

# Exportar
if not df.empty:
    st.sidebar.divider()
    csv = df.drop(columns=['id', 'user_id'], errors='ignore').to_csv(index=False, sep=';', decimal=',').encode('utf-8-sig')
    st.sidebar.download_button("📥 Descargar CSV", data=csv, file_name="Cuentas.csv", mime="text/csv")

# Historial
st.subheader("Libro Mayor")
if not df.empty:
    df_mostrar = df.drop(columns=['id', 'user_id'], errors='ignore').iloc[::-1].reset_index(drop=True)
    st.dataframe(df_mostrar, use_container_width=True, hide_index=True)
else:
    st.info("No hay datos en tu cuenta. Haz tu primer registro.")