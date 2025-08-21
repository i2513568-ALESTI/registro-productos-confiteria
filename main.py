import os
import pandas as pd
import streamlit as st
from datetime import datetime

DATA_DIR = "datos_sinteticos"
CSV_PATH = os.path.join(DATA_DIR, "products.csv")

ALLOWED_CATEGORIES = [
    "Chocolates", "Caramelos", "Mashmelos", "Galletas", "Salamos", "Gomas de mascar"
]

def ensure_dir():
    os.makedirs(DATA_DIR, exist_ok=True)

def load_df() -> pd.DataFrame:
    if os.path.exists(CSV_PATH):
        return pd.read_csv(CSV_PATH, encoding="utf-8")
    return pd.DataFrame(columns=["id_product", "nombre", "precio", "categorias", "en_venta", "ts"])

def save_df(df: pd.DataFrame):
    ensure_dir()
    df.to_csv(CSV_PATH, index=False, encoding="utf-8")

def validate(nombre: str, precio, categorias: list, en_venta_label: str):
    if len(nombre.strip()) == 0 or len(nombre.strip()) > 20:
        raise ValueError("El nombre no puede estar vacío ni superar 20 caracteres.")
    if precio is None:
        raise ValueError("Por favor verifique el campo del precio")
    try:
        p = float(precio)
    except Exception:
        raise ValueError("Por favor verifique el campo precio")
    if not (0 < p < 999):
        raise ValueError("El precio debe ser mayor a 0 y menor a 999.")
    if not categorias:
        raise ValueError("Debe elegir al menos una categoría.")
    for c in categorias:
        if c not in ALLOWED_CATEGORIES:
            raise ValueError(f"Categoría inválida: {c}")
    if en_venta_label not in ["Si", "No"]:
        raise ValueError("Valor inválido para ¿está en venta?")
    return (
        nombre.strip(),
        round(p, 2),
        sorted(list(set(categorias))),
        (en_venta_label == "Si"),
    )

#----------------------------------------------- UI ------------------------------------------------------

st.title("Confitería Duicino - Registro de productos")

# Cargar base
df = load_df()

# Formulario para agregar producto
with st.form("form-producto", clear_on_submit=True):
    col1, col2 = st.columns([2,1])
    with col1:
        nombre = st.text_input("Nombre del Producto")
    with col2:
        precio = st.number_input("Precio (S/)", min_value=0.0, max_value=998.99, step=0.10, format="%.2f")
    categorias = st.multiselect("Categorías", ALLOWED_CATEGORIES)
    en_venta_label = st.radio("¿El producto está en venta?", options=["Si","No"], horizontal=True)

    submitted = st.form_submit_button("Guardar")

    if submitted:
        try:
            nombre, precio, categorias, en_venta = validate(nombre, precio, categorias, en_venta_label)

            # Generar nuevo id
            new_id = 1 if df.empty else df["id_product"].max() + 1

            nuevo = pd.DataFrame([{
                "id_product": new_id,
                "nombre": nombre,
                "precio": precio,
                "categorias": ";".join(categorias),
                "en_venta": en_venta,
                "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }])
            df = pd.concat([df, nuevo], ignore_index=True)
            save_df(df)
            st.success("✅ Producto guardado correctamente")
        except Exception as e:
            st.error(f"❌ {str(e)}")

# Mostrar tabla con opciones
st.subheader("📋 Lista de productos registrados")

if not df.empty:
    for i, row in df.iterrows():
        with st.expander(f"🟢 {row['nombre']} (S/{row['precio']})"):
            st.write(f"**ID:** {row['id_product']}")
            st.write(f"**Categorías:** {row['categorias']}")
            st.write(f"**En venta:** {'✅ Sí' if row['en_venta'] else '❌ No'}")
            st.write(f"**Fecha registro:** {row['ts']}")

            col1, col2 = st.columns(2)
            # Botón eliminar
            if col1.button("🗑️ Eliminar", key=f"delete-{row['id_product']}"):
                df = df[df["id_product"] != row["id_product"]]
                save_df(df)
                st.rerun()

            # Botón editar
            if col2.button("✏️ Editar", key=f"edit-{row['id_product']}"):
                st.session_state["edit_id"] = row["id_product"]

    # Si se selecciona editar
    if "edit_id" in st.session_state:
        edit_id = st.session_state["edit_id"]
        row = df[df["id_product"] == edit_id].iloc[0]
        st.subheader(f"✏️ Editar producto: {row['nombre']}")
        with st.form("form-editar", clear_on_submit=False):
            new_nombre = st.text_input("Nuevo nombre", value=row["nombre"])
            new_precio = st.number_input("Nuevo precio", value=float(row["precio"]), min_value=0.0, max_value=998.99, step=0.10)
            new_categorias = st.multiselect("Nuevas categorías", ALLOWED_CATEGORIES, default=row["categorias"].split(";"))
            new_en_venta = st.radio("¿En venta?", ["Si","No"], index=0 if row["en_venta"] else 1, horizontal=True)
            
            actualizar = st.form_submit_button("💾 Actualizar")
            if actualizar:
                try:
                    nombre, precio, categorias, en_venta = validate(new_nombre, new_precio, new_categorias, new_en_venta)
                    df.loc[df["id_product"] == edit_id, ["nombre","precio","categorias","en_venta","ts"]] = [
                        nombre, precio, ";".join(categorias), en_venta, datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    ]
                    save_df(df)
                    st.success("✅ Producto actualizado correctamente")
                    del st.session_state["edit_id"]
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ {str(e)}")

    # Botón para borrar todo
    if st.button("⚠️ Borrar toda la tabla de productos"):
        df = pd.DataFrame(columns=["id_product", "nombre", "precio", "categorias", "en_venta", "ts"])
        save_df(df)
        st.warning("⚠️ Toda la data ha sido eliminada")
        st.rerun()

    # Botón para descargar
    st.download_button(
        label="📥 Descargar CSV",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name="products.csv",
        mime="text/csv",
    )
else:
    st.info("⚠️ No hay productos registrados todavía.")
