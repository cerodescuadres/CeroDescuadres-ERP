"""Streamlit app for tracking cash flow records."""

from pathlib import Path

import pandas as pd
import streamlit as st


CSV_PATH = Path(__file__).with_name("datos.csv")
COLUMNAS = [
    "Fecha",
    "Cliente/Proveedor",
    "Concepto",
    "Tipo",
    "Estado",
    "Importe",
]


def cargar_registros() -> pd.DataFrame:
    """Load saved records, or return an empty table for a new project."""
    if not CSV_PATH.exists() or CSV_PATH.stat().st_size == 0:
        return pd.DataFrame(columns=COLUMNAS)

    registros = pd.read_csv(CSV_PATH)
    columnas_faltantes = [columna for columna in COLUMNAS if columna not in registros.columns]
    if columnas_faltantes:
        raise ValueError(
            "El archivo datos.csv no contiene las columnas esperadas: "
            + ", ".join(columnas_faltantes)
        )

    return registros.loc[:, COLUMNAS]


def guardar_registro(registro: dict[str, object]) -> None:
    """Append one record to the local CSV file."""
    nuevo_registro = pd.DataFrame([registro], columns=COLUMNAS)
    nuevo_registro.to_csv(
        CSV_PATH,
        mode="a",
        header=not CSV_PATH.exists() or CSV_PATH.stat().st_size == 0,
        index=False,
        encoding="utf-8",
    )


def main() -> None:
    st.set_page_config(page_title="CeroDescuadres - Flujo de Caja")
    st.title("CeroDescuadres - Flujo de Caja")

    with st.sidebar:
        st.header("Registrar operación")
        with st.form("formulario_registro"):
            fecha = st.date_input("Fecha")
            cliente_proveedor = st.text_input("Cliente/Proveedor")
            concepto = st.text_input("Concepto")
            tipo = st.selectbox("Tipo", ["Ingreso", "Gasto"])
            estado = st.selectbox("Estado", ["Pendiente", "Cobrado/Pagado"])
            importe = st.number_input(
                "Importe",
                min_value=0.0,
                value=0.0,
                step=0.01,
                format="%.2f",
            )
            guardar = st.form_submit_button("Guardar Registro")

        if guardar:
            guardar_registro(
                {
                    "Fecha": fecha.isoformat(),
                    "Cliente/Proveedor": cliente_proveedor,
                    "Concepto": concepto,
                    "Tipo": tipo,
                    "Estado": estado,
                    "Importe": importe,
                }
            )
            st.success("Registro guardado en datos.csv.")

    registros = cargar_registros()
    if registros.empty:
        st.info("Todavía no hay registros. Añade una operación desde la barra lateral.")
    else:
        st.dataframe(registros, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
