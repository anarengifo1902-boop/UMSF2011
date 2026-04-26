import datetime
import io
import os
from datetime import date
from zoneinfo import ZoneInfo

import altair as alt
import pandas as pd
import streamlit as st

DATA_FILE = "registros_volquete.csv"


def peru_now():
    return datetime.datetime.now(ZoneInfo("America/Lima")).replace(microsecond=0)


def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE, dtype=str)
        return df.fillna("")
    return pd.DataFrame(columns=["ID", "PLACA", "EJES", "ZONA", "MATERIAL", "HORA"])


def save_data():
    st.session_state.df.to_csv(DATA_FILE, index=False)


def to_excel_bytes(df: pd.DataFrame) -> bytes:
    buffer = io.BytesIO()
    try:
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Registros")
        return buffer.getvalue()
    except Exception:
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Registros")
        return buffer.getvalue()


def to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def filter_records(df, selected_month, selected_year, date_range):
    df = df.copy()
    df["_DATE"] = pd.to_datetime(df["ID"], errors="coerce")
    month_names = [
        "Todos",
        "Enero",
        "Febrero",
        "Marzo",
        "Abril",
        "Mayo",
        "Junio",
        "Julio",
        "Agosto",
        "Setiembre",
        "Octubre",
        "Noviembre",
        "Diciembre",
    ]
    if selected_month != "Todos":
        month_index = month_names.index(selected_month)
        df = df[df["_DATE"].dt.month == month_index]
    if selected_year != "Todos":
        df = df[df["_DATE"].dt.year == int(selected_year)]
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date = end_date = date_range
    if start_date > end_date:
        start_date, end_date = end_date, start_date
    start_ts = pd.Timestamp(start_date)
    end_ts = pd.Timestamp(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
    df = df[(df["_DATE"] >= start_ts) & (df["_DATE"] <= end_ts)]
    return df.drop(columns=["_DATE"])


if "df" not in st.session_state:
    st.session_state.df = load_data()
    st.session_state.delete_mode = False
    st.session_state.show_close = False

st.set_page_config(page_title="Registro de Volquete", page_icon="🚚", layout="wide", initial_sidebar_state="expanded")

left_col, right_col = st.columns([2, 3])
left_col.markdown("<h1 style='margin-bottom: 0;'>Agregados mamarosa</h1>", unsafe_allow_html=True)
right_col.markdown(
    "<h3 style='text-align: right; margin-bottom: 0;'>Unidad Minera no Metálica Santa Fortunata 2011</h3>",
    unsafe_allow_html=True,
)

st.subheader("REGISTRO DE SALIDA DE MATERIAL")

st.write(
    "Plataforma digital para el registro, control y seguimiento de la salida de material en la cantera Santa Fortunata 2011."
)

month_names = [
    "Todos",
    "Enero",
    "Febrero",
    "Marzo",
    "Abril",
    "Mayo",
    "Junio",
    "Julio",
    "Agosto",
    "Setiembre",
    "Octubre",
    "Noviembre",
    "Diciembre",
]
current_year = datetime.date.today().year
year_options = ["Todos"] + [str(y) for y in range(2026, current_year + 6)]

tabs = st.tabs(["Reporte de volquetes", "Cálculo de ingresos", "Estadísticas"])

with tabs[0]:
    st.header("Reporte de volquetes")
    with st.form("add_volquete_form"):
        placa = st.text_input("PLACA")
        ejes = st.selectbox("EJES", ["2", "3"])
        zona = st.selectbox("ZONA", ["1", "2", "3"])
        material = st.selectbox(
            "MATERIAL",
            [
                "Arena chancada para asfalto",
                "Arena fina",
                "Arena gruesa",
                "Gravilla 1/4”",
                "Material > 6” (**)",
                "Material base",
                "Material sub base (*)",
                "Material para planta (chancado y selección)",
                "Piedra chancada de 1”",
                "Piedra chancada de 1/2”",
                "Piedra chancada de 3/4”",
                "Piedra de 10” a 20”",
                "Piedra de 20” a 60”",
                "Piedra de 8” a 10",
            ],
        )
        submitted = st.form_submit_button("Registrar")

    if submitted:
        fecha = peru_now().date().isoformat()
        hora = peru_now().strftime("%H:%M:%S")
        new_record = {
            "ID": fecha,
            "PLACA": placa,
            "EJES": ejes,
            "ZONA": zona,
            "MATERIAL": material,
            "HORA": hora,
        }
        st.session_state.df = pd.concat(
            [pd.DataFrame([new_record]), st.session_state.df], axis=0,
            ignore_index=True,
        )
        save_data()
        st.success("Volquete registrado correctamente.")
        st.write("**Registro:**")
        st.dataframe(pd.DataFrame([new_record]), width='stretch', hide_index=True)

    filter_col1, filter_col2, filter_col3 = st.columns(3)
    with filter_col1:
        selected_month = st.selectbox("Mes", month_names, key="tab0_month")
    with filter_col2:
        selected_year = st.selectbox("Año", year_options, key="tab0_year")
    with filter_col3:
        range_value = st.date_input(
            "Rango",
            value=(datetime.date(2026, 1, 1), datetime.date.today()),
            min_value=datetime.date(2026, 1, 1),
        )

    filtered_df = filter_records(st.session_state.df, selected_month, selected_year, range_value)

    st.write(f"Número de registros: {len(filtered_df)}")

    if filtered_df.empty:
        st.info("No hay registros en el rango seleccionado.")
        st.session_state.delete_mode = False
    else:
        if not st.session_state.delete_mode:
            st.dataframe(filtered_df, width='stretch', hide_index=True)
            if st.button("🗑️ Eliminar registros", key="open_delete"):
                st.session_state.delete_mode = True
                st.rerun()
            _, download_col = st.columns([3, 1])
            with download_col:
                excel_bytes = to_excel_bytes(filtered_df)
                st.download_button(
                    label="📥",
                    data=excel_bytes,
                    file_name="reporte_volquetes.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="download_report",
                    width='stretch',
                )
        else:
            st.warning("Seleccione los registros a eliminar.")
            delete_df = filtered_df.copy()
            delete_df["ELIMINAR"] = False
            edited_df = st.data_editor(
                delete_df,
                width='stretch',
                hide_index=True,
                column_config={
                    "ELIMINAR": st.column_config.CheckboxColumn(
                        "Eliminar",
                        help="Marque para borrar este registro",
                    )
                },
                disabled=["ID", "PLACA", "EJES", "ZONA", "MATERIAL", "HORA"],
                key="delete_editor",
            )
            col_eliminar, col_cancelar = st.columns([1, 1])
            with col_eliminar:
                if st.button("✓ Eliminar", key="confirm_delete"):
                    ids_to_delete = edited_df.index[edited_df["ELIMINAR"]].tolist()
                    if ids_to_delete:
                        st.session_state.df = st.session_state.df.drop(index=ids_to_delete).reset_index(drop=True)
                        save_data()
                        st.success("Eliminado correctamente.")
                        st.session_state.delete_mode = False
                        st.rerun()
                    else:
                        st.info("No se seleccionó ningún registro para eliminar.")
            with col_cancelar:
                if st.button("✕ Cancelar", key="cancel_delete"):
                    st.session_state.delete_mode = False
                    st.rerun()

with tabs[1]:
    st.header("Cálculo de ingresos")
    if st.session_state.df.empty:
        st.info("No hay registros para calcular ingresos.")
    else:
        date_from = st.date_input("Desde", value=datetime.date.today() - datetime.timedelta(days=30), min_value=datetime.date(2026, 1, 1))
        date_to = st.date_input("Hasta", value=datetime.date.today(), min_value=datetime.date(2026, 1, 1))
        date_range = (date_from, date_to)
        records = filter_records(st.session_state.df, "Todos", "Todos", date_range)

        if records.empty:
            st.info("No hay registros en el rango seleccionado.")
        else:
            materials = sorted(records["MATERIAL"].unique())
            st.write("### Materiales detectados")
            prices = {}
            with st.expander("Ingrese el precio por material"):
                for material in materials:
                    prices[material] = st.number_input(
                        f"Precio para {material}",
                        min_value=0.0,
                        step=0.1,
                        format="%.2f",
                        key=f"price_{material}",
                    )

            st.write("### Seleccione el método de cantidad")
            quantity_method = st.radio(
                "Cantidad por registro",
                ["Opción A (general)", "Opción B (específica)"],
            )

            if quantity_method == "Opción A (general)":
                st.write("#### Establezca la cantidad por eje")
                qty_2_ejes = st.number_input("Cantidad para 2 ejes (m³)", min_value=0.0, step=0.1, value=10.0, format="%.1f")
                qty_3_ejes = st.number_input("Cantidad para 3 ejes (m³)", min_value=0.0, step=0.1, value=15.0, format="%.1f")
                volume_map = {"2": qty_2_ejes, "3": qty_3_ejes}
                records["CANTIDAD"] = records["EJES"].map(volume_map).fillna(0.0)
            else:
                editable_records = records.copy()
                editable_records["CANTIDAD"] = 10.0
                edited_records = st.data_editor(
                    editable_records,
                    width='stretch',
                    hide_index=True,
                    column_config={
                        "CANTIDAD": st.column_config.NumberColumn(
                            "Cantidad (m³)",
                            min_value=0.0,
                            help="Ingrese la cantidad por registro",
                        )
                    },
                    disabled=["ID", "PLACA", "EJES", "ZONA", "MATERIAL", "HORA"],
                    key="qty_editor",
                )
                records = edited_records

            records["PRECIO"] = records["MATERIAL"].map(prices).fillna(0.0)
            records["INGRESO"] = records["PRECIO"] * records["CANTIDAD"]

            st.write("### Detalle de ingresos por registro")
            with st.expander("Filtrar"):
                zona_filter = st.selectbox("Filtrar por zona", ["Todas"] + sorted(records["ZONA"].unique().tolist()), key="zona_filter")
                dia_filter = st.selectbox("Filtrar por día", ["Todos"] + sorted(records["ID"].unique().tolist()), key="dia_filter")
                placa_filter = st.selectbox("Filtrar por placa", ["Todas"] + sorted(records["PLACA"].unique().tolist()), key="placa_filter")
                eje_filter = st.selectbox("Filtrar por eje", ["Todos"] + sorted(records["EJES"].unique().tolist()), key="eje_filter")
                material_filter = st.selectbox("Filtrar por material", ["Todos"] + sorted(records["MATERIAL"].unique().tolist()), key="material_filter")

            filtered_records = records.copy()
            if zona_filter != "Todas":
                filtered_records = filtered_records[filtered_records["ZONA"] == zona_filter]
            if dia_filter != "Todos":
                filtered_records = filtered_records[filtered_records["ID"] == dia_filter]
            if placa_filter != "Todas":
                filtered_records = filtered_records[filtered_records["PLACA"] == placa_filter]
            if eje_filter != "Todos":
                filtered_records = filtered_records[filtered_records["EJES"] == eje_filter]
            if material_filter != "Todos":
                filtered_records = filtered_records[filtered_records["MATERIAL"] == material_filter]

            display_df = filtered_records[["ID", "PLACA", "EJES", "ZONA", "MATERIAL", "CANTIDAD", "PRECIO", "INGRESO"]].copy()
            total_row = pd.DataFrame([{
                "ID": "TOTAL",
                "PLACA": "",
                "EJES": "",
                "ZONA": "",
                "MATERIAL": "",
                "CANTIDAD": pd.NA,
                "PRECIO": pd.NA,
                "INGRESO": filtered_records["INGRESO"].sum()
            }])
            display_df = pd.concat([display_df, total_row], ignore_index=True)
            left_col, right_col = st.columns([3, 1])
            with right_col:
                excel_bytes = to_excel_bytes(display_df)
                st.download_button(
                    label="📥",
                    data=excel_bytes,
                    file_name="detalle_ingresos.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="download_income",
                    width='stretch',
                )
            st.dataframe(display_df, width='stretch', hide_index=True)

with tabs[2]:
    st.header("Estadísticas")
    if st.session_state.df.empty:
        st.info("No hay registros para mostrar estadísticas.")
    else:
        with st.expander("OPCIONES DE FILTRO"):
            stat_month = st.selectbox("Filtrar por mes", month_names, key="stat_month")
            stat_year = st.selectbox("Filtrar por año", year_options, key="stat_year")
            stat_date_range = st.date_input(
                "Buscar por rango de fechas",
                value=(datetime.date(2026, 1, 1), datetime.date.today()),
                min_value=datetime.date(2026, 1, 1),
                key="stat_date_range"
            )
            stat_df = filter_records(st.session_state.df, stat_month, stat_year, stat_date_range)

        zona_counts = stat_df["ZONA"].value_counts().rename_axis("ZONA").reset_index(name="Registros")
        material_counts = stat_df["MATERIAL"].value_counts().rename_axis("MATERIAL").reset_index(name="Registros")

        st.write("### Número de registros por zona")
        if not zona_counts.empty:
            bar_chart = alt.Chart(zona_counts).mark_bar().encode(
                x="ZONA:N",
                y="Registros:Q",
                color=alt.Color("ZONA:N", scale=alt.Scale(scheme="category10")),
                tooltip=["ZONA", "Registros"]
            )
            st.altair_chart(bar_chart, width='stretch')
        else:
            st.info("No hay datos para mostrar.")

        st.write("### Número de registros según material")
        if not material_counts.empty:
            pie_chart = alt.Chart(material_counts).mark_arc().encode(
                theta="Registros:Q",
                color=alt.Color("MATERIAL:N", scale=alt.Scale(scheme="category20")),
                tooltip=["MATERIAL", "Registros"]
            ).properties(height=400)
            st.altair_chart(pie_chart, width='stretch')
        else:
            st.info("No hay datos para mostrar.")
