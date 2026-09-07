import streamlit as st

st.set_page_config(
    page_title="Cotizador EDOS SpA", layout="centered"
)

st.title("🚜 EDOS SpA - Generador de Presupuestos")
st.markdown("Cálculo operativo, margen comercial y formato de propuesta formal.")

# --- 0. DATOS DEL CLIENTE Y OBRA ---
with st.expander("📄 Datos del Mandante y Ubicación", expanded=True):
    cliente_input = st.text_input("Para (Cliente / Constructora)", value="Constructora Minimal")
    ubicacion_input = st.text_input("Ubicación de la Obra", value="Avenida El Salto 2255, Recoleta")

# --- 1. GEOMETRÍA Y VOLÚMENES ---
st.subheader("1. Parámetros Generales y Volúmenes")
volumen_corte = st.number_input(
    "Volumen Neto a Extraer (m³)", min_value=0.0, value=1600.0, step=100.0
)
factor_esponjamiento = st.slider(
    "Factor de Esponjamiento (Abundamiento)", 1.0, 1.5, 1.25, 0.05
)
dias_faena = st.number_input(
    "Duración Estimada de la Faena (días)", min_value=1, value=10, step=1
)

volumen_suelto = volumen_corte * factor_esponjamiento

# --- 2. EXCAVACIÓN (Por Hora) ---
with st.expander("⚙️ Maquinaria de Excavación y Carga (Por Hora)"):
    n_excavadoras = st.number_input(
        "N° Excavadoras / Martillo Demoledor", min_value=0, value=1, step=1
    )
    tarifa_excavadora = st.number_input(
        "Tarifa Hora Excavadora ($/hr)", value=48000.0, step=1000.0
    )
    horas_jornada_exc = dias_faena * 9
    costo_excavacion = n_excavadoras * tarifa_excavadora * horas_jornada_exc

    precio_petroleo = st.number_input(
        "Precio Referencial Petróleo ($/litro)", value=1150.0, step=10.0
    )
    consumo_maq_hrs = st.number_input(
        "Consumo estimado excavadora (litros/hr)", value=22.0, step=1.0
    )
    costo_combustible_exc = horas_jornada_exc * consumo_maq_hrs * precio_petroleo

# --- 3. TRANSPORTE Y BOTADERO ---
with st.expander("🚛 Transporte y Botadero"):
    modalidad_camiones = st.radio(
        "Modalidad de Camiones",
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

    else:
        costo_transporte_total = st.number_input(
            "Valor Total Cerrado (Suma Alzada) ($)",
            value=18000000.0,
            step=500000.0,
        )

# --- 4. MITIGACIONES Y OTROS COSTOS ---
with st.expander("🚧 Mitigaciones y Partidas Extra"):
    incluir_aljibe = st.checkbox("Incluir Camión Aljibe (Mitigación de Polvo)", value=False)
    costo_aljibe_total = (220000.0 * dias_faena) if incluir_aljibe else 0.0

    n_paleteros = st.number_input("N° de Paleteros / Banderilleros", 0, 10, 0)
    costo_paleteros_total = n_paleteros * 45000.0 * dias_faena

# --- 5. PERSONAL Y TOPOGRAFÍA ---
with st.expander("👷 Personal Clave y Topografía"):
    incluir_topografo = st.checkbox("Topógrafo dedicado", value=False)
    costo_topografo = (130000.0 * dias_faena) if incluir_topografo else 0.0

# --- SUMATORIA COSTO INTERNO ---
costo_total_interno = (
    costo_excavacion
    + costo_combustible_exc
    + costo_transporte_total
    + costo_aljibe_total
    + costo_paleteros_total
    + costo_topografo
)

# --- 6. OFERTA COMERCIAL AL MANDANTE ---
st.subheader("6. Margen Comercial y Oferta Final")
margen_mandante = st.slider(
    "Margen por Responsabilidad y Firma de Contrato (%)",
    min_value=0.0,
    max_value=40.0,
    value=15.0,
    step=1.0,
)

precio_final_mandante = costo_total_interno * (1 + (margen_mandante / 100))
precio_unitario_final = precio_final_mandante / volumen_corte if volumen_corte > 0 else 0

# --- RESULTADOS ---
st.divider()
st.subheader("📊 Resumen Económico")

col1, col2 = st.columns(2)
with col1:
    st.metric("Costo Interno", f"${costo_total_interno:,.0f} CLP")
with col2:
    st.metric("Total Oferta Mandante", f"${precio_final_mandante:,.0f} CLP", delta=f"+{margen_mandante}%")

st.info(f"💡 **Precio Unitario Calculado para el Mandante:** ${precio_unitario_final:,.2f} / m³")

# --- GENERADOR DE DOCUMENTO OFICIAL EDOS SPA ---
st.divider()
if st.button("📋 Generar Propuesta Formal Estilo EDOS SpA"):
    propuesta_formal = f"""### **PRESUPUESTO DE SERVICIO DE RETIRO / MOVIMIENTO DE TIERRA**

* **Para:** {cliente_input}
* **De:** EDOS SpA
* **Ubicación:** {ubicacion_input}[cite: 1]

---

#### **1. Detalle del Servicio y Valores**[cite: 1]
Retiro de aproximadamente {volumen_corte:,.0f} metros cúbicos de material, medidos esponjados sobre camión[cite: 1]. El servicio incluye el uso de maquinaria y el transporte correspondiente a un botadero autorizado[cite: 1].

| Descripción | Cantidad Estimada | Precio Unitario Neto | Total Neto Estimado |
| :--- | :---: | :---: | :---: |
| Servicio completo de retiro / excavación | {volumen_corte:,.0f} $m^3$[cite: 1] | ${precio_unitario_final:,.0f} / m^3$[cite: 1] | ${precio_final_mandante:,.0f}[cite: 1] |

#### **2. Condición de Ajuste**[cite: 1]
Los metros cúbicos finales se ajustarán estrictamente al volumen real extraído en terreno, el cual será debidamente controlado mediante los vales de carga emitidos[cite: 1].

#### **3. Delimitación de Logística y Responsabilidades**[cite: 1]
La gestión de las maquinarias y el flujo de los camiones en el interior de la obra se realizará siguiendo exclusivamente las directrices y bajo la planificación logística de la constructora[cite: 1]. EDOS SpA ejecutará el servicio acatando las instrucciones específicas (tales como frentes de inicio), quedando eximida de toda responsabilidad ante eventuales incidentes o accidentes que ocurran dentro de la faena derivados de dicha coordinación interna[cite: 1].

#### **4. Exclusiones y Obligaciones de la Constructora**[cite: 1]
El presente presupuesto contempla únicamente la disposición de la maquinaria y los camiones de transporte[cite: 1]. Quedan expresamente excluidos de la responsabilidad de EDOS SpA y bajo cargo directo de la constructora los siguientes conceptos[cite: 1]:
* Suministro de agua para el control de polución y mitigación ambiental[cite: 1].
* Implementación y mantención de medidas de control de contaminación (Malla Rachel, lavado y limpieza de ruedas)[cite: 1].
* Cierre perimetral de seguridad de la obra[cite: 1].
* Personal de seguridad vial y control de tránsito (paleteros)[cite: 1].
* Permisos municipales, autorizaciones regulatorias y derechos asociados[cite: 1].

---
**Vicente Ortiz Amestelli - EDOS SpA**[cite: 1]"""

    st.code(propuesta_formal, language="markdown")
