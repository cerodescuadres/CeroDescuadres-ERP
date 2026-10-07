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


def calcular_metricas(registros: pd.DataFrame) -> tuple[float, float, float]:
    """Return actual cash, pending receivables, and pending payables."""
    if registros.empty:
        return 0.0, 0.0, 0.0

    importes = pd.to_numeric(registros["Importe"], errors="raise")
    ingresos = registros["Tipo"].eq("Ingreso")
    gastos = registros["Tipo"].eq("Gasto")
    cobrados_pagados = registros["Estado"].eq("Cobrado/Pagado")
    pendientes = registros["Estado"].eq("Pendiente")

    caja_real = (
        importes[ingresos & cobrados_pagados].sum()
        - importes[gastos & cobrados_pagados].sum()
    )
    por_cobrar = importes[ingresos & pendientes].sum()
    por_pagar = importes[gastos & pendientes].sum()
    return float(caja_real), float(por_cobrar), float(por_pagar)


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
    caja_real, por_cobrar, por_pagar = calcular_metricas(registros)
    columna_caja, columna_cobrar, columna_pagar = st.columns(3)
    columna_caja.metric("Caja Real", caja_real)
    columna_cobrar.metric("Por Cobrar (Pendiente)", por_cobrar)
    columna_pagar.metric("Por Pagar (Deuda)", por_pagar)

    if registros.empty:
        st.info("Todavía no hay registros. Añade una operación desde la barra lateral.")
    else:
        registros_recientes = registros.assign(
            _fecha_orden=pd.to_datetime(registros["Fecha"], errors="raise")
        )
        registros_recientes = (
            registros_recientes.sort_values(
                "_fecha_orden",
                ascending=False,
                kind="stable",
            )
            .drop(columns="_fecha_orden")
            .reset_index(drop=True)
        )
        st.dataframe(registros_recientes, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
