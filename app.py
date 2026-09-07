import streamlit as st
import json
from fpdf import FPDF

st.set_page_config(
    page_title="Cotizador EDOS SpA", layout="centered", page_icon="🚜"
)

st.title("🚜 EDOS SpA - Generador de Presupuestos")
st.markdown("Cálculo operativo, tarifa por m³, condiciones comerciales y propuesta formal.")

# --- 0. DATOS DEL CLIENTE Y OBRA ---
with st.expander("📄 Datos del Mandante y Ubicación", expanded=True):
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        cliente_input = st.text_input("Para (Cliente / Constructora)", value="Constructora Minimal")
    with col_c2:
        ubicacion_input = st.text_input("Ubicación de la Obra", value="Avenida El Salto 2255, Recoleta")

# --- 1. GEOMETRÍA Y VOLÚMENES ---
st.subheader("1. Parámetros Generales y Volúmenes")
col_v1, col_v2, col_v3 = st.columns(3)
with col_v1:
    volumen_corte = st.number_input(
        "Volumen Neto (m³)", min_value=0.0, value=1600.0, step=100.0
    )
with col_v2:
    factor_esponjamiento = st.slider(
        "Factor Esponjamiento", 1.0, 1.5, 1.25, 0.05
    )
with col_v3:
    dias_faena = st.number_input(
        "Duración Faena (días)", min_value=1, value=10, step=1
    )

volumen_suelto = volumen_corte * factor_esponjamiento

# --- 2. EXCAVACIÓN Y EQUIPOS ---
with st.expander("⚙️ Maquinaria de Excavación y Carga (Por Hora)"):
    col_e1, col_e2 = st.columns(2)
    with col_e1:
        n_excavadoras = st.number_input("N° Excavadoras", min_value=0, value=1, step=1)
        tarifa_excavadora = st.number_input("Tarifa Hora Excavadora ($/hr)", value=48000.0, step=1000.0)
    with col_e2:
        precio_petroleo = st.number_input("Precio Petróleo ($/litro)", value=1150.0, step=10.0)
        consumo_maq_hrs = st.number_input("Consumo Excavadora (L/hr)", value=22.0, step=1.0)
    
    horas_jornada_exc = dias_faena * 9
    costo_excavacion = n_excavadoras * tarifa_excavadora * horas_jornada_exc
    costo_combustible_exc = n_excavadoras * horas_jornada_exc * consumo_maq_hrs * precio_petroleo

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
            "Tarifa transporte + botadero autoriz. ($/m³ suelto)", value=3200.0, step=100.0
        )
        costo_transporte_total = volumen_suelto * tarifa_m3_transporte

    elif modalidad_camiones == "Por Hora de Arriendo ($/hr)":
        n_camiones = st.number_input("N° Camiones Tolva", min_value=1, value=4)
        tarifa_camion = st.number_input("Tarifa Hora Camión ($/hr)", value=38000.0)
        horas_camion = dias_faena * 8
        costo_transporte_total = n_camiones * tarifa_camion * horas_camion

    else:
        costo_transporte_total = st.number_input(
            "Valor Total Cerrado (Suma Alzada) ($)", value=18000000.0, step=500000.0
        )

# --- 4. MITIGACIONES Y OTROS COSTOS ---
with st.expander("🚧 Mitigaciones y Partidas Extra"):
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        incluir_aljibe = st.checkbox("Incluir Camión Aljibe (Polución)", value=False)
        costo_aljibe_total = (220000.0 * dias_faena) if incluir_aljibe else 0.0
    with col_m2:
        n_paleteros = st.number_input("N° Paleteros / Banderilleros", 0, 10, 0)
        costo_paleteros_total = n_paleteros * 45000.0 * dias_faena

# --- 5. PERSONAL Y TOPOGRAFÍA ---
with st.expander("👷 Personal Clave y Topografía"):
    incluir_topografo = st.checkbox("Topógrafo dedicado", value=False)
    costo_topografo = (130000.0 * dias_faena) if incluir_topografo else 0.0

# --- 6. CONDICIONES COMERCIALES Y PAGO ---
with st.expander("📜 Condiciones Comerciales y Legales"):
    col_k1, col_k2 = st.columns(2)
    with col_k1:
        validez_oferta = st.number_input("Validez de la Oferta (días)", min_value=1, value=15)
        hrs_minimas_garantizadas = st.number_input("Mínimo de Horas Diarias Garantizadas", min_value=0, value=8)
    with col_k2:
        condicion_pago = st.selectbox(
            "Condición de Pago",
            ["50% Anticipo - 50% al finalizar", "Facturación Quincenal por Avance", "30 días fecha factura", "Contrado al día"]
        )

# --- SUMATORIA COSTO INTERNO ---
costo_total_interno = (
    costo_excavacion
    + costo_combustible_exc
    + costo_transporte_total
    + costo_aljibe_total
    + costo_paleteros_total
    + costo_topografo
)

# --- 7. OFERTA COMERCIAL Y MARGEN ---
st.subheader("7. Oferta Comercial al Mandante")
modo_comercial = st.radio(
    "¿Cómo deseas definir la oferta?",
    (
        "Ingresar Precio Unitario Neto al Mandante ($/m³)",
        "Definir por Porcentaje de Margen (%)",
        "Ingresar Precio Final Neto Objetivo ($)"
    )
)

if modo_comercial == "Ingresar Precio Unitario Neto al Mandante ($/m³)":
    precio_unitario_final = st.number_input(
        "Precio Unitario Final Neto ($/m³)", min_value=0.0, value=16500.0, step=500.0
    )
    monto_neto_mandante = precio_unitario_final * volumen_corte
    margen_mandante = ((monto_neto_mandante - costo_total_interno) / costo_total_interno) * 100 if costo_total_interno > 0 else 0.0

elif modo_comercial == "Definir por Porcentaje de Margen (%)":
    margen_mandante = st.slider(
        "Margen (%)", min_value=0.0, max_value=40.0, value=15.0, step=1.0
    )
    monto_neto_mandante = costo_total_interno * (1 + (margen_mandante / 100))
    precio_unitario_final = monto_neto_mandante / volumen_corte if volumen_corte > 0 else 0

else:
    min_val_obj = float(costo_total_interno)
    val_defecto = float(costo_total_interno * 1.15)
    monto_neto_mandante = st.number_input(
        "Precio Final Total Neto ($)", min_value=min_val_obj, value=max(min_val_obj, val_defecto), step=100000.0
    )
    margen_mandante = ((monto_neto_mandante - costo_total_interno) / costo_total_interno) * 100 if costo_total_interno > 0 else 0.0
    precio_unitario_final = monto_neto_mandante / volumen_corte if volumen_corte > 0 else 0

# Cálculos de IVA y Bruto
monto_iva = monto_neto_mandante * 0.19
monto_bruto = monto_neto_mandante + monto_iva

# --- RESULTADOS FINANCIEROS INTERNOS ---
st.divider()
st.subheader("📊 Resumen Económico e Impuestos")

col_r1, col_r2, col_r3 = st.columns(3)
with col_r1:
    st.metric("Costo Interno (Ejecución)", f"${costo_total_interno:,.0f} CLP")
with col_r2:
    st.metric("Total Neto Oferta", f"${monto_neto_mandante:,.0f} CLP", delta=f"Margen: {margen_mandante:.1f}%")
with col_r3:
    st.metric("Total Bruto (incl. IVA)", f"${monto_bruto:,.0f} CLP")

st.info(f"💡 **Precio Unitario Neto:** ${precio_unitario_final:,.2f} / m³ | **IVA (19%):** ${monto_iva:,.0f} CLP")

# --- VISTA PREVIA PROPUESTA FORMAL ---
st.divider()
st.subheader("📋 Vista Previa de la Propuesta Formal")

propuesta_formal = f"""### **PRESUPUESTO DE SERVICIO DE RETIRO Y MOVIMIENTO DE TIERRAS**

* **Para:** {cliente_input}
* **De:** EDOS SpA
* **Ubicación:** {ubicacion_input}
* **Validez de la Oferta:** {validez_oferta} días corridos

---

#### **1. Detalle del Servicio y Valores**
Retiro de aproximadamente {volumen_corte:,.0f} m³ de material, medidos esponjados sobre camión. Incluye maquinaria, operación y transporte a botadero autorizado.

| Descripción | Cantidad Estimada | P. Unitario Neto | Total Neto Estimado |
| :--- | :---: | :---: | :---: |
| Servicio completo de retiro / excavación | {volumen_corte:,.0f} m³ | ${precio_unitario_final:,.0f} / m³ | ${monto_neto_mandante:,.0f} |

* **Subtotal Neto:** ${monto_neto_mandante:,.0f} CLP
* **IVA (19%):** ${monto_iva:,.0f} CLP
* **Total Bruto:** ${monto_bruto:,.0f} CLP

#### **2. Condiciones de Pago y Ajuste**
* **Forma de Pago:** {condicion_pago}.
* **Control de Volumen:** Los m³ finales se ajustarán estrictamente al volumen extraído controlado mediante vales de carga.
* **Stand-by / Mínimo Diario:** Se establece un mínimo de {hrs_minimas_garantizadas} horas diarias por equipo contratado.

#### **3. Delimitación de Logística y Responsabilidades**
La gestión interna de maquinarias y camiones será según las directrices de la constructora. EDOS SpA queda eximida de responsabilidad ante incidentes derivados de la coordinación logística interna de la obra.

#### **4. Exclusiones**
* Suministro de agua para polución.
* Medidas de mitigación ambiental (Malla Rachel, lavado de ruedas).
* Cierre perimetral y seguridad vial (paleteros).
* Permisos municipales o autorizaciones regulatorias.

---
**Vicente Ortiz Amestelli - EDOS SpA**"""

st.markdown(propuesta_formal)

# --- FUNCIÓN GENERADORA DE PDF ---
def generar_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Encabezado
    pdf.set_font("Arial", "B", 13)
    pdf.cell(0, 8, "PRESUPUESTO DE RETIRO Y MOVIMIENTO DE TIERRAS", ln=True, align="C")
    pdf.set_font("Arial", "I", 10)
    pdf.cell(0, 5, "EDOS SpA - Servicios de Excavacion y Logistica", ln=True, align="C")
    pdf.ln(5)
    
    # Datos
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 5, f"Para: {cliente_input}", ln=True)
    pdf.cell(0, 5, f"Ubicacion: {ubicacion_input}", ln=True)
    pdf.cell(0, 5, f"Validez: {validez_oferta} dias corridos", ln=True)
    pdf.ln(4)
    
    # Tabla
    pdf.set_font("Arial", "B", 9)
    pdf.cell(80, 7, "Descripcion", border=1)
    pdf.cell(30, 7, "Cantidad", border=1, align="C")
    pdf.cell(35, 7, "P. Unit. Neto", border=1, align="C")
    pdf.cell(45, 7, "Total Neto", border=1, align="C")
    pdf.ln()
    
    pdf.set_font("Arial", "", 9)
    pdf.cell(80, 7, "Servicio de retiro / excavacion", border=1)
    pdf.cell(30, 7, f"{volumen_corte:,.0f} m3", border=1, align="C")
    pdf.cell(35, 7, f"${precio_unitario_final:,.0f}", border=1, align="C")
    pdf.cell(45, 7, f"${monto_neto_mandante:,.0f}", border=1, align="C")
    pdf.ln(9)
    
    # Totales
    pdf.set_font("Arial", "B", 9)
    pdf.cell(145, 6, "Subtotal Neto:", align="R")
    pdf.cell(45, 6, f"${monto_neto_mandante:,.0f} CLP", align="R", ln=True)
    pdf.cell(145, 6, "IVA (19%):", align="R")
    pdf.cell(45, 6, f"${monto_iva:,.0f} CLP", align="R", ln=True)
    pdf.cell(145, 6, "Total Bruto:", align="R")
    pdf.cell(45, 6, f"${monto_bruto:,.0f} CLP", align="R", ln=True)
    pdf.ln(6)
    
    # Condiciones
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 6, "2. Condiciones Comerciales", ln=True)
    pdf.set_font("Arial", "", 9)
    pdf.multi_cell(0, 5, f"- Forma de Pago: {condicion_pago}.\n- Cubaje Final: Ajustado a vales de carga reales.\n- Stand-by: Minimo garantizado de {hrs_minimas_garantizadas} hrs/dia por equipo.")
    pdf.ln(4)
    
    # Exclusiones
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 6, "3. Exclusiones", ln=True)
    pdf.set_font("Arial", "", 9)
    pdf.multi_cell(0, 4, "- Suministro de agua, lavado de ruedas y mitigacion de polvo.\n- Permisos municipales, cierres perimetrales y paleteros.")
    pdf.ln(10)
    
    # Firma
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 5, "______________________________________", ln=True)
    pdf.cell(0, 5, "Vicente Ortiz Amestelli - EDOS SpA", ln=True)
    
    return bytes(pdf.output())

# --- EXPORTACIÓN Y BACKUP ---
col_d1, col_d2 = st.columns(2)

with col_d1:
    pdf_bytes = generar_pdf()
    st.download_button(
        label="📄 Descargar Presupuesto PDF",
        data=pdf_bytes,
        file_name=f"Presupuesto_EDOS_{cliente_input.replace(' ', '_')}.pdf",
        mime="application/pdf"
    )

with col_d2:
    # Datos en JSON para importar/guardar
    cotizacion_data = {
        "cliente": cliente_input,
        "ubicacion": ubicacion_input,
        "volumen_corte": volumen_corte,
        "costo_interno": costo_total_interno,
        "monto_neto": monto_neto_mandante,
        "monto_bruto": monto_bruto,
        "precio_m3_neto": precio_unitario_final,
        "condicion_pago": condicion_pago
    }
    json_str = json.dumps(cotizacion_data, indent=4)
    st.download_button(
        label="💾 Guardar Parámetros (JSON)",
        data=json_str,
        file_name=f"Cotizacion_{cliente_input.replace(' ', '_')}.json",
        mime="application/json"
    )
