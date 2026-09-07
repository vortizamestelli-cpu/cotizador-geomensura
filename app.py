import streamlit as st

st.set_page_config(
    page_title="Cotizador Pro - Movimiento de Tierras", layout="centered"
)

st.title("🚜 Cotizador Integral con Tarifas Mixtas")
st.markdown("Permite alternar entre cobro por hora, por volumen y suma alzada.")

# --- 1. GEOMETRÍA Y VOLÚMENES ---
st.subheader("1. Parámetros Generales y Volúmenes")
volumen_corte = st.number_input(
    "Volumen de Corte Neto (m³)", min_value=0.0, value=5000.0, step=100.0
)
factor_esponjamiento = st.slider(
    "Factor de Esponjamiento (Abundamiento)", 1.0, 1.5, 1.25, 0.05
)
dias_faena = st.number_input(
    "Duración Estimada de la Faena (días)", min_value=1, value=12, step=1
)

volumen_suelto = volumen_corte * factor_esponjamiento

# --- 2. EXCAVACIÓN (Por Hora) ---
with st.expander("⚙️ Maquinaria de Excavación y Carga (Por Hora)", expanded=True):
    n_excavadoras = st.number_input(
        "N° Excavadoras / Creadoras", min_value=0, value=1, step=1
    )
    tarifa_excavadora = st.number_input(
        "Tarifa Hora Excavadora ($/hr)", value=48000.0, step=1000.0
    )
    horas_jornada_exc = dias_faena * 9  # 9 horas efectivas de excavación
    costo_excavacion = n_excavadoras * tarifa_excavadora * horas_jornada_exc

    precio_petroleo = st.number_input(
        "Precio Referencial Petróleo ($/litro)", value=1150.0, step=10.0
    )
    consumo_maq_hrs = st.number_input(
        "Consumo estimado excavadora (litros/hr)", value=22.0, step=1.0
    )
    costo_combustible_exc = horas_jornada_exc * consumo_maq_hrs * precio_petroleo

# --- 3. TRANSPORTE Y BOTADERO (Selector de Modalidad) ---
with st.expander(
    "🚛 Transporte y Botadero (Seleccionar Modalidad Camiones)"
):
    modalidad_camiones = st.radio(
        "¿Cómo se calculan los camiones tolva?",
        (
            "Por Metro Cúbico Transportado ($/m³)",
            "Por Hora de Arriendo ($/hr)",
            "Suma Alzada (Global)",
        ),
    )

    if modalidad_camiones == "Por Metro Cúbico Transportado ($/m³)":
        tarifa_m3_transporte = st.number_input(
            "Tarifa transporte + botadero autoriz. ($/m³ suelto)",
            value=3200.0,
            step=100.0,
        )
        costo_transporte_total = volumen_suelto * tarifa_m3_transporte

    elif modalidad_camiones == "Por Hora de Arriendo ($/hr)":
        n_camiones = st.number_input("N° Camiones Tolva", min_value=1, value=4)
        tarifa_camion = st.number_input(
            "Tarifa Hora Camión Tolva ($/hr)", value=38000.0
        )
        horas_camion = dias_faena * 8
        costo_transporte_total = n_camiones * tarifa_camion * horas_camion

    else:  # Suma Alzada Camiones/Botadero
        costo_transporte_total = st.number_input(
            "Valor Total Cerrado (Suma Alzada) para Camiones y Botadero ($)",
            value=18000000.0,
            step=500000.0,
        )

# --- 4. MITIGACIONES Y OTROS COSTOS ---
with st.expander("🚧 Mitigaciones, Peajes y Partidas a Suma Alzada"):
    # Ejemplo de ítem opcional cerrado a suma alzada
    usar_suma_alzada_general = st.checkbox(
        "Incluir otro servicio externo a Suma Alzada (Ej. Cerco provisorio / Aseo)"
    )
    monto_suma_alzada_extra = (
        st.number_input("Monto Cerrado Extra ($)", value=1500000.0)
        if usar_suma_alzada_general
        else 0.0
    )

    incluir_aljibe = st.checkbox(
        "Incluir Camión Aljibe (Mitigación de Polvo)", value=True
    )
    tarifa_aljibe_dia = (
        st.number_input("Costo diario Camión Aljibe ($/día)", value=220000.0)
        if incluir_aljibe
        else 0.0
    )
    costo_aljibe_total = tarifa_aljibe_dia * dias_faena

    n_paleteros = st.number_input("N° de Paleteros / Banderilleros", 0, 10, 2)
    tarifa_paletero_dia = st.number_input(
        "Costo diario por Paletero ($)", value=45000.0
    )
    costo_paleteros_total = n_paleteros * tarifa_paletero_dia * dias_faena

# --- 5. PERSONAL Y TOPOGRAFÍA ---
with st.expander("👷 Personal Clave y Topografía"):
    incluir_topografo = st.checkbox("Topógrafo dedicado", value=True)
    costo_topografo = (
        (130000.0 * dias_faena) if incluir_topografo else 0.0
    )

# --- SUMATORIA GENERAL ---
costo_total_proyecto = (
    costo_excavacion
    + costo_combustible_exc
    + costo_transporte_total
    + costo_aljibe_total
    + costo_paleteros_total
    + costo_topografo
    + monto_suma_alzada_extra
)

costo_unitario = (
    costo_total_proyecto / volumen_corte if volumen_corte > 0 else 0
)

# --- RESULTADOS ---
st.divider()
st.subheader("📊 Resumen Económico del Proyecto")

m1, m2 = st.columns(2)
m1.metric("Costo Total", f"${costo_total_proyecto:,.0f} CLP")
m2.metric("Costo Unitario", f"${costo_unitario:,.2f} CLP/m³")

if st.button("📋 Copiar Resumen para Cliente"):
    st.code(
        f"""*Presupuesto Movimiento de Tierras*
- Volumen Neto: {volumen_corte:,.0f} m³ ({volumen_suelto:,.0f} m³ sueltos)
- Plazo: {dias_faena} días
- Modalidad Camiones: {modalidad_camiones}
- *VALOR TOTAL:* ${costo_total_proyecto:,.0f} CLP
- *Costo Unitario:* ${costo_unitario:,.2f} CLP/m³""",
        language="markdown",
    )