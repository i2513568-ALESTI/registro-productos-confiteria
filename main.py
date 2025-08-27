import os
import pandas as pd
import streamlit as st
from datetime import datetime
from supabase import create_client

# ------------------------------------------
# Conexión a supabase
# ------------------------------------------
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

TABLE_NAME = "confiteria_duicino"

# Categorías permitidas
ALLOWED_CATEGORIES = [
    "Chocolates", "Caramelos", "Mashmelos", "Galletas", "Salados", "Gomas de mascar"
]

# ------------------------------------------
# Utilidades
# ------------------------------------------
def categorias_to_list(categorias_str: str) -> list[str]:
    """Convierte string 'A;B;C' a lista ['A','B','C'] de forma segura."""
    if not isinstance(categorias_str, str):
        return []
    return [cat.strip() for cat in categorias_str.split(";") if cat.strip()]

def categorias_to_string(categorias_list: list[str]) -> str:
    """Convierte lista ['A','B'] a string 'A;B'."""
    return ";".join(categorias_list or [])

def validar(nombre: str, precio: float, categorias: list[str]) -> str | None:
    if not nombre or len(nombre.strip()) == 0 or len(nombre.strip()) > 20:
        return "El nombre es obligatorio y debe de tener <= 20 caracteres."
    try:
        p = float(precio)
    except Exception:
        return "Por favor verifique el campo precio."
    if not (0 < p < 999):
        return "El precio debe ser mayor a 0 y menor a 999"
    if not categorias:
        return "Debe elegir al menos una categoría"
    for c in categorias:
        if c not in ALLOWED_CATEGORIES:
            return f"Categoría inválida: {c}"
    return None

# ------------------------------------------
# Funciones CRUD
# ------------------------------------------
def format_time_ago(timestamp_str):
    """Convierte timestamp a formato relativo legible"""
    try:
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        ts = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        
        diff = now - ts
        
        if diff.days > 0:
            if diff.days == 1:
                return "Ayer"
            elif diff.days < 7:
                return f"Hace {diff.days} días"
            else:
                return ts.strftime('%d/%m/%Y')
        elif diff.seconds >= 3600:
            hours = diff.seconds // 3600
            if hours == 1:
                return "Hace 1 hora"
            else:
                return f"Hace {hours} horas"
        elif diff.seconds >= 60:
            minutes = diff.seconds // 60
            if minutes == 1:
                return "Hace 1 minuto"
            else:
                return f"Hace {minutes} minutos"
        else:
            return "Ahora mismo"
    except:
        return timestamp_str

def sb_list() -> pd.DataFrame:
    res = (
        supabase.table(TABLE_NAME)
        .select("id_product,nombre,precio,categorias,en_venta,ts")
        .order("ts", desc=True)
        .execute()
    )
    df = pd.DataFrame(res.data or [])
    
    # Convertir timestamp a formato legible
    if not df.empty and 'ts' in df.columns:
        df['registrado'] = df['ts'].apply(format_time_ago)
        df = df.drop(columns=['ts'])
    
    return df

def sb_insert(nombre: str, precio: float, categorias: list, en_venta: bool):
    payload = {
        "nombre": nombre,
        "precio": precio,
        "categorias": categorias_to_string(categorias),
        "en_venta": en_venta,
        "ts": datetime.utcnow().isoformat()
    }
    supabase.table(TABLE_NAME).insert(payload).execute()

def sb_update(id_: int, nombre: str, precio: float, categorias: list, en_venta: bool):
    payload = {
        "nombre": nombre,
        "precio": precio,
        "categorias": categorias_to_string(categorias),
        "en_venta": en_venta,
    }
    supabase.table(TABLE_NAME).update(payload).eq("id_product", id_).execute()

def sb_delete(id_: int):
    supabase.table(TABLE_NAME).delete().eq("id_product", id_).execute()

#------------------------------------- UI -----------------------------------
st.title("Confitería Dulcino - Registro de productos")

# ------- Crear Producto -------
st.header("Agregar Producto")
with st.form("form-add", clear_on_submit=True):
    nombre = st.text_input("Nombre de producto")
    precio = st.number_input("Precio (S/)", min_value=0.01, max_value=998.99, step=0.10)
    categorias = st.multiselect("Categorias", ALLOWED_CATEGORIES)
    en_venta = st.radio("¿En Venta?", ["Sí", "No"], horizontal=True) == "Sí"
    submitted = st.form_submit_button("Guardar")

if submitted:
    err = validar(nombre, precio, categorias)
    if err:
        if "precio" in err.lower():
            st.error("Por favor verifique el campo precio")
        else:
            st.error("Lo sentimos no pudo crear este producto")
        st.info(err)
    else:
        sb_insert(nombre.strip(), float(precio), categorias, en_venta)
        st.success("Felicidades su producto se agregó")
        st.rerun()

st.divider()

# ----------------- Listar / Filtrar / Paginación / Editar / Borrar -----------------------
st.header("Productos registrados")

# --- Sidebar: paginación y filtros (con keys) ---
ITEMS_PER_PAGE = st.sidebar.selectbox(
    "Productos por página",
    [5, 10, 20, 50],
    index=1,
    key="items_per_page",
    help="Selecciona cuántos productos mostrar por página"
)

st.sidebar.header("🔍 Filtros")
search_term = st.sidebar.text_input(
    "Buscar por nombre",
    placeholder="Ej: Chocolate",
    key="search_term",
    help="Filtra productos por nombre"
)

category_filter = st.sidebar.multiselect(
    "Filtrar por categoría",
    ALLOWED_CATEGORIES,
    key="category_filter",
    help="Selecciona categorías para filtrar"
)

# Función para limpiar filtros usando session_state
def clear_filters():
    st.session_state["search_term"] = ""
    st.session_state["category_filter"] = []
    st.session_state["current_page"] = 1

st.sidebar.button("🧹 Limpiar filtros", type="secondary", on_click=clear_filters)

# --- Cargar data ---
df = sb_list()

# Preprocesar una columna lista para filtrar por categorías
df["categorias_list"] = df["categorias"].apply(categorias_to_list)

# --- Aplicar filtros ---
if search_term:
    df = df[df["nombre"].str.contains(search_term, case=False, na=False)]

if category_filter:
    df = df[df["categorias_list"].apply(lambda lst: any(cat in lst for cat in category_filter))]

# --- Mostrar resultados o vacío ---
if df.empty:
    if search_term or category_filter:
        st.info("No se encontraron productos con los filtros aplicados. Intenta con otros criterios de búsqueda.")
    else:
        st.info("No hay productos aún.")
else:
    # --- Paginación ---
    total_items = len(df)
    total_pages = (total_items + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE

    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        current_page = st.selectbox(
            "Página",
            options=list(range(1, total_pages + 1)) if total_pages > 0 else [1],
            index=0,
            key="current_page",
            format_func=lambda x: f"Página {x} de {total_pages}" if total_pages > 0 else "Página 1 de 1",
        )
    with col2:
        if search_term or category_filter:
            st.write(f"**{total_items} productos encontrados** (filtros aplicados)")
        else:
            st.write(f"**{total_items} productos**")
    with col3:
        if total_pages > 1:
            st.write(f"**{ITEMS_PER_PAGE} por página**")

    start_idx = (current_page - 1) * ITEMS_PER_PAGE
    end_idx = min(start_idx + ITEMS_PER_PAGE, total_items)
    df_page = df.iloc[start_idx:end_idx].copy()

    # Mostrar tabla paginada (con campos bonitos)
    df_page_view = df_page.drop(columns=["categorias_list"])
    
    # Renombrar columnas para mejor visualización
    df_page_view = df_page_view.rename(columns={
        'id_product': 'ID',
        'nombre': 'Producto',
        'precio': 'Precio (S/)',
        'categorias': 'Categorías',
        'en_venta': 'En Venta',
        'registrado': 'Registrado'
    })
    
    # Formatear precio y en_venta
    df_page_view['Precio (S/)'] = df_page_view['Precio (S/)'].apply(lambda x: f"S/ {x:.2f}")
    df_page_view['En Venta'] = df_page_view['En Venta'].apply(lambda x: "✅ Sí" if x else "❌ No")
    
    st.dataframe(df_page_view, use_container_width=True)
    if total_pages > 1:
        st.caption(f"Mostrando productos {start_idx + 1} a {end_idx} de {total_items}")

    # Validar que exista id_product
    if "id_product" not in df.columns:
        st.error(
            "No se encontró la columna 'id_product' en los datos. "
            f"Verifique la estructura de la tabla '{TABLE_NAME}' y las políticas RLS en Supabase."
        )
    else:
        # Selector del producto (solo de la página actual)
        opciones = {
            f"{r['id_product']} | {r['nombre']} (S/{r['precio']})": r["id_product"]
            for _, r in df_page.iterrows()
        }

        if opciones:
            etiqueta = st.selectbox("Selecciona para editar/eliminar", list(opciones.keys()))
            producto_id = int(opciones[etiqueta])
            fila = df[df["id_product"] == producto_id].iloc[0]

            with st.form("form-edit"):
                c1, c2 = st.columns([2, 1])
                with c1:
                    ed_nombre = st.text_input("Nombre", value=fila["nombre"])
                with c2:
                    ed_precio = st.number_input(
                        "precio (S/)", value=float(fila["precio"]),
                        min_value=0.0, max_value=998.99, step=0.10, format="%.2f"
                    )

                # Default SOLO con categorías válidas para evitar errores por typos en BD
                default_cats = [c for c in categorias_to_list(fila["categorias"]) if c in ALLOWED_CATEGORIES]
                ed_categorias = st.multiselect("Categorías", ALLOWED_CATEGORIES, default=default_cats)
                ed_en_venta = st.radio(
                    "¿En venta?", ["Sí", "No"],
                    index=0 if fila["en_venta"] else 1,
                    horizontal=True
                ) == "Sí"

                colu1, colu2 = st.columns(2)
                with colu1:
                    btn_update = st.form_submit_button("Guardar Cambios")
                with colu2:
                    btn_delete = st.form_submit_button("Eliminar", type="primary")

                if btn_update:
                    err = validar(ed_nombre, ed_precio, ed_categorias)
                    if err:
                        if "precio" in err.lower():
                            st.error("Por favor verifique el campo precio.")
                        else:
                            st.error("Lo sentimos no pudo actualizar este producto.")
                        st.info(err)
                    else:
                        sb_update(producto_id, ed_nombre.strip(), float(ed_precio), ed_categorias, ed_en_venta)
                        st.success("Producto Actualizado.")
                        st.rerun()

                if btn_delete:
                    sb_delete(producto_id)
                    st.success("Producto Eliminado")
                    st.rerun()
        else:
            st.info("No hay productos en esta página con los filtros actuales.")
