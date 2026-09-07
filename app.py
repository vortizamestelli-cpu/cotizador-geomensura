import streamlit as st
from fpdf import FPDF
import json

# Configuración de página
st.set_page_config(
    page_title="Cotizador EDOS SpA",
    page_icon="🚜",
    layout="wide"
)

# Título Principal
st.title("🚜 EDOS SpA - Generador de Presupuestos")
st.caption("Cálculo operativo, tarifa por m³, condiciones comerciales y propuesta formal.")

st.markdown("---")

# ---------------------------------------------------------
# DATOS DE LA OBRA Y MANDANTE
# ---------------------------------------------------------
st.subheader("📄 Datos del Mandante y Ubicación")
col_m1, col_m2 = st.columns(2)
with col_m1:
    cliente_nombre = st.text_input("Para (Cliente / Constructora)", "Constructora Minimal")
with col_m2:
    ubicacion_obra = st.text_input("Ubicación de la Obra", "Avenida El Salto 2255, Recoleta")

st.markdown("---")

# ---------------------------------------------------------
# 1. PARÁMETROS GENERALES Y MODALIDAD
# ---------------------------------------------------------
st.subheader("1. Parámetros Generales y Volúmenes")

modalidad_ejecucion = st.radio(
    "Modalidad de Operación Interna",
    [
        "Desglosada (Gestión propia de Maquinaria, Petróleo y Transporte)",
        "Subcontrato Completo / Todo Incluido (Tarifa cerrada por m³)"
    ],
    index=0
)

col_v1, col_v2, col_v3 = st.columns(3)
with col_v1:
    volumen_neto = st.number_input("Volumen Neto en Banco (m³)", min_value=1.0, value=1942.67, step=10.0)
with col_v2:
    factor_esponjamiento = st.number_input("Factor Esponjamiento", min_value=1.0, max_value=2.0, value=1.50, step=0.05)
with col_v3:
    duracion_dias = st.number_input("Duración Estimada de Faena (días)", min_value=1, value=5, step=1)

volumen_esponjado = volumen_neto * factor_esponjamiento

# Variables por defecto
costo_maquinaria = 0.0
costo_combustible = 0.0
costo_transporte = 0.0
costo_paleteros = 0.0
costo_aljibe = 0.0
costo_topografia = 0.0
costo_subcontrato_total = 0.0

if modalidad_ejecucion == "Subcontrato Completo / Todo Incluido (Tarifa cerrada por m³)":
    st.info("💡 En esta modalidad, el subcontratista asume toda la maquinaria, transporte y botadero. Solo debes indicar cuánto te cobra por m³ esponjado.")
    costo_subcontrato_m3 = st.number_input(
        "Costo del Subcontrato por m³ esponjado ($/m³)",
        min_value=0.0,
        value=3200.0,
        step=100.0
    )
    costo_interno_total = volumen_esponjado * costo_subcontrato_m3

else:
    # ---------------------------------------------------------
    # MODALIDAD DESGLOSADA (MAQUINARIA, TRANSPORTE, MITIGACIONES)
    # ---------------------------------------------------------
    with st.expander("⚙️ Maquinaria de Excavación y Carga", expanded=True):
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        with col_m1:
            num_excavadoras = st.number_input("N° Excavadoras", min_value=1, value=1, step=1)
        with col_m2:
            tarifa_excavadora_hr = st.number_input("Tarifa Hora Excavadora ($/hr)", min_value=0.0, value=48000.0, step=1000.0)
        with col_m3:
            precio_petroleo = st.number_input("Precio Petróleo ($/litro)", min_value=0.0, value=1150.0, step=10.0)
        with col_m4:
            consumo_l_hr = st.number_input("Consumo Excavadora (L/hr)", min_value=0.0, value=22.0, step=1.0)

        horas_diarias_est = st.number_input("Horas operativas estimadas por día", min_value=1, value=8, step=1)
        horas_totales_maquinaria = duracion_dias * horas_diarias_est * num_excavadoras

        costo_maquinaria = horas_totales_maquinaria * tarifa_excavadora_hr
        costo_combustible = horas_totales_maquinaria * consumo_l_hr * precio_petroleo

    with st.expander("🚛 Transporte y Botadero", expanded=True):
        tarifa_transporte_m3 = st.number_input(
            "Tarifa transporte + botadero autorizado ($/m³ esponjado)",
            min_value=0.0,
            value=3200.0,
            step=100.0
        )
        costo_transporte = volumen_esponjado * tarifa_transporte_m3

    with st.expander("🚧 Mitigaciones, Personal y Topografía"):
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            incluye_aljibe = st.checkbox("Incluir Camión Aljibe (Polución)")
            num_paleteros = st.number_input("N° Paleteros / Banderilleros", min_value=0, value=0, step=1)
            valor_dia_paletero = st.number_input("Costo diario por paletero ($/día)", min_value=0.0, value=35000.0, step=1000.0)
        with col_p2:
            incluye_topografia = st.checkbox("Incluir Topógrafo dedicado")
            costo_topografia_global = st.number_input("Costo global de topografía ($)", min_value=0.0, value=150000.0, step=10000.0)

        if incluye_aljibe:
            costo_aljibe = duracion_dias * 120000.0  # Estimación diaria
        if num_paleteros > 0:
            costo_paleteros = num_paleteros * duracion_dias * valor_dia_paletero
        if incluye_topografia:
            costo_topografia = costo_topografia_global

    costo_interno_total = (
        costo_maquinaria +
        costo_combustible +
        costo_transporte +
        costo_aljibe +
        costo_paleteros +
        costo_topografia
    )

st.markdown("---")

# ---------------------------------------------------------
# CONDICIONES COMERCIALES
# ---------------------------------------------------------
st.subheader("📜 Condiciones Comerciales y Legales")
col_c1, col_c2, col_c3 = st.columns(3)
with col_c1:
    validez_oferta = st.number_input("Validez de la Oferta (días)", min_value=1, value=15)
with col_c2:
    minimo_horas = st.number_input("Mínimo de Horas Diarias Garantizadas", min_value=1, value=8)
with col_c3:
    condicion_pago = st.text_input("Condición de Pago", "50% Anticipo - 50% al finalizar")

st.markdown("---")

# ---------------------------------------------------------
# OFERTA COMERCIAL AL MANDANTE
# ---------------------------------------------------------
st.subheader("7. Oferta Comercial al Mandante")

tipo_oferta = st.radio(
    "¿Cómo deseas definir la oferta?",
    [
        "Ingresar Precio Unitario Neto al Mandante ($/m³)",
        "Definir por porcentaje de margen (%)",
        "Ingresar Precio Final Neto Objetivo ($)"
    ]
)

if tipo_oferta == "Ingresar Precio Unitario Neto al Mandante ($/m³)":
    pu_neto_mandante = st.number_input("Precio Unitario Final Neto ($/m³)", min_value=0.0, value=16500.0, step=500.0)
    oferta_total_neto = volumen_esponjado * pu_neto_mandante

elif tipo_oferta == "Definir por porcentaje de margen (%)":
    margen_pct = st.number_input("Porcentaje de Margen Deseado (%)", min_value=0.0, value=35.0, step=5.0)
    oferta_total_neto = costo_interno_total * (1 + (margen_pct / 100.0))
    pu_neto_mandante = oferta_total_neto / volumen_esponjado if volumen_esponjado > 0 else 0.0

else:
    oferta_total_neto = st.number_input("Precio Final Neto Objetivo ($)", min_value=0.0, value=48081000.0, step=100000.0)
    pu_neto_mandante = oferta_total_neto / volumen_esponjado if volumen_esponjado > 0 else 0.0

# Cálculos Finales
iva_monto = oferta_total_neto * 0.19
total_bruto = oferta_total_neto + iva_monto
margen_monto = oferta_total_neto - costo_interno_total
margen_porcentaje = (margen_monto / costo_interno_total * 100.0) if costo_interno_total > 0 else 0.0

st.markdown("---")

# ---------------------------------------------------------
# RESUMEN ECONÓMICO
# ---------------------------------------------------------
st.subheader("📊 Resumen Económico e Impuestos")

col_r1, col_r2, col_r3 = st.columns(3)
col_r1.metric("Costo Interno (Ejecución)", f"${costo_interno_total:,.0f} CLP".replace(",", "."))
col_r2.metric(
    "Oferta Total Neto",
    f"${oferta_total_neto:,.0f} CLP".replace(",", "."),
    delta=f"Margen: {margen_porcentaje:.1f}%"
)
col_r3.metric("Total Bruto (incl. IVA)", f"${total_bruto:,.0f} CLP".replace(",", "."))

st.info(f"💡 **Precio Unitario Neto:** ${pu_neto_mandante:,.2f} / m³ | **IVA (19%):** ${iva_monto:,.0f} CLP".replace(",", "."))

st.markdown("---")

# ---------------------------------------------------------
# VISTA PREVIA Y PDF
# ---------------------------------------------------------
st.subheader("📋 Vista Previa de la Propuesta Formal")

texto_descripcion_servicio = (
    f"Retiro de aproximadamente {volumen_esponjado:,.0f} m³ de material, medidos esponjados sobre camión. "
    f"Incluye gestión operativa, maquinaria y transporte a botadero autorizado."
).replace(",", ".")

st.markdown("### PRESUPUESTO DE SERVICIO DE RETIRO Y MOVIMIENTO DE TIERRAS")
st.markdown(f"- **Para:** {cliente_nombre}")
st.markdown("- **De:** EDOS SpA")
st.markdown(f"- **Ubicación:** {ubicacion_obra}")
st.markdown(f"- **Validez de la Oferta:** {validez_oferta} días corridos")

st.markdown("#### 1. Detalle del Servicio y Valores")
st.write(texto_descripcion_servicio)

st.table([
    {
        "Descripción": "Servicio completo de retiro / excavación",
        "Cantidad Estimada": f"{volumen_esponjado:,.0f} m³".replace(",", "."),
        "P. Unitario Neto": f"${pu_neto_mandante:,.0f} / m³".replace(",", "."),
        "Total Neto Estimado": f"${oferta_total_neto:,.0f}".replace(",", ".")
    }
])

st.markdown(f"* **Subtotal neto:** ${oferta_total_neto:,.0f} CLP".replace(",", "."))
st.markdown(f"* **IVA (19%):** ${iva_monto:,.0f} CLP".replace(",", "."))
st.markdown(f"* **Bruto total:** ${total_bruto:,.0f} CLP".replace(",", "."))

st.markdown("#### 2. Condiciones de Pago y Ajuste")
st.markdown(f"- **Forma de Pago:** {condicion_pago}.")
st.markdown("- **Control de Volumen:** Los m³ finales se ajustarán estrictamente al volumen extraído controlado mediante cubicación de terreno o cubicaje sobre camión.")
st.markdown(f"- **Stand-by / Mínimo Diario:** Se establece un mínimo de {minimo_horas} horas diarias por equipo contratado.")

st.markdown("#### 3. Delimitación de Logística y Responsabilidades")
st.markdown("La gestión interna de maquinarias y camiones será según las directrices de la obra. EDOS SpA queda eximida de responsabilidad ante incidentes derivados de la coordinación logística interna de la constructora.")

st.markdown("#### 4. Exclusiones")
st.markdown("- Camión aljibe para mitigación de polución (salvo acuerdo explícito).")
st.markdown("- Medidas de mitigación ambiental adicionales (Malla Rachel, lavador de ruedas).")
st.markdown("- Cierre perimetral y seguridad vial externa (paleteros).")
st.markdown("- Permisos municipales, cortes de calle o autorizaciones regulatorias.")

st.caption("*Vicente Ortiz Amestelli - EDOS SpA*")

# ---------------------------------------------------------
# GENERACIÓN DE PDF
# ---------------------------------------------------------
class PDFPresupuesto(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 14)
        self.cell(0, 8, 'EDOS SpA - Servicios de Geomensura y Movimiento de Tierras', 0, 1, 'C')
        self.set_font('Arial', 'I', 9)
        self.cell(0, 5, 'Propuesta Técnica y Comercial', 0, 1, 'C')
        self.line(10, 23, 200, 23)
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

def generar_pdf():
    pdf = PDFPresupuesto()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Encabezado
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 7, "PRESUPUESTO DE RETIRO Y MOVIMIENTO DE TIERRAS", 0, 1, "L")
    pdf.ln(2)

    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 6, f"Para: {cliente_nombre}", 0, 1)
    pdf.cell(0, 6, "De: EDOS SpA", 0, 1)
    pdf.cell(0, 6, f"Ubicacion: {ubicacion_obra}", 0, 1)
    pdf.cell(0, 6, f"Validez de la Oferta: {validez_oferta} dias corridos", 0, 1)
    pdf.ln(4)

    # 1. Detalle
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 7, "1. Detalle del Servicio y Valores", 0, 1)
    pdf.set_font("Arial", "", 9)
    pdf.multi_cell(0, 5, texto_descripcion_servicio.encode('latin-1', 'replace').decode('latin-1'))
    pdf.ln(3)

    # Tabla
    pdf.set_font("Arial", "B", 9)
    pdf.cell(85, 6, "Descripcion", 1, 0, "C")
    pdf.cell(30, 6, "Cantidad", 1, 0, "C")
    pdf.cell(35, 6, "P. Unitario Neto", 1, 0, "C")
    pdf.cell(40, 6, "Total Neto", 1, 1, "C")

    pdf.set_font("Arial", "", 9)
    pdf.cell(85, 6, "Servicio completo de retiro / excavacion", 1, 0, "L")
    pdf.cell(30, 6, f"{volumen_esponjado:,.0f} m3".replace(",", "."), 1, 0, "C")
    pdf.cell(35, 6, f"${pu_neto_mandante:,.0f} / m3".replace(",", "."), 1, 0, "R")
    pdf.cell(40, 6, f"${oferta_total_neto:,.0f}".replace(",", "."), 1, 1, "R")
    pdf.ln(4)

    # Totales
    pdf.set_font("Arial", "", 10)
    pdf.cell(120, 6, "", 0, 0)
    pdf.cell(30, 6, "Subtotal Neto:", 0, 0, "R")
    pdf.cell(40, 6, f"${oferta_total_neto:,.0f} CLP".replace(",", "."), 0, 1, "R")

    pdf.cell(120, 6, "", 0, 0)
    pdf.cell(30, 6, "IVA (19%):", 0, 0, "R")
    pdf.cell(40, 6, f"${iva_monto:,.0f} CLP".replace(",", "."), 0, 1, "R")

    pdf.set_font("Arial", "B", 10)
    pdf.cell(120, 6, "", 0, 0)
    pdf.cell(30, 6, "Total Bruto:", 0, 0, "R")
    pdf.cell(40, 6, f"${total_bruto:,.0f} CLP".replace(",", "."), 0, 1, "R")
    pdf.ln(6)

    # 2. Condiciones
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 7, "2. Condiciones de Pago y Ajuste", 0, 1)
    pdf.set_font("Arial", "", 9)
    pdf.cell(0, 5, f"- Forma de Pago: {condicion_pago}.", 0, 1)
    pdf.cell(0, 5, "- Control de Volumen: Los m3 finales se ajustaran al volumen real extraido.", 0, 1)
    pdf.cell(0, 5, f"- Stand-by / Minimo Diario: {minimo_horas} horas diarias garantizadas por equipo.", 0, 1)
    pdf.ln(4)

    # 3. Delimitación
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 7, "3. Delimitacion de Logistica y Responsabilidades", 0, 1)
    pdf.set_font("Arial", "", 9)
    pdf.multi_cell(0, 5, "La gestion interna de maquinarias y camiones sera segun las directrices de la obra. EDOS SpA queda eximida de responsabilidad ante incidentes derivados de la coordinacion logistica interna de la constructora.")
    pdf.ln(4)

    # 4. Exclusiones
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 7, "4. Exclusiones", 0, 1)
    pdf.set_font("Arial", "", 9)
    pdf.cell(0, 5, "- Camion aljibe para mitigacion de polucion.", 0, 1)
    pdf.cell(0, 5, "- Medidas de mitigacion ambiental (Malla Rachel, lavado de ruedas).", 0, 1)
    pdf.cell(0, 5, "- Cierre perimetral y seguridad vial (paleteros).", 0, 1)
    pdf.cell(0, 5, "- Permisos municipales o autorizaciones regulatorias.", 0, 1)
    pdf.ln(10)

    # Firma
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 6, "Vicente Ortiz Amestelli", 0, 1, "R")
    pdf.set_font("Arial", "", 9)
    pdf.cell(0, 5, "EDOS SpA", 0, 1, "R")

    return pdf.output(dest='S').encode('latin-1', 'replace')

col_bot1, col_bot2 = st.columns(2)
with col_bot1:
    pdf_bytes = generar_pdf()
    st.download_button(
        label="📄 Descargar Presupuesto PDF",
        data=pdf_bytes,
        file_name=f"Presupuesto_EDOS_{cliente_nombre.replace(' ', '_')}.pdf",
        mime="application/pdf"
    )

with col_bot2:
    datos_json = {
        "cliente": cliente_nombre,
        "ubicacion": ubicacion_obra,
        "modalidad": modalidad_ejecucion,
        "volumen_neto": volumen_neto,
        "volumen_esponjado": volumen_esponjado,
        "costo_interno_total": costo_interno_total,
        "pu_neto_mandante": pu_neto_mandante,
        "oferta_total_neto": oferta_total_neto,
        "total_bruto": total_bruto
    }
    st.download_button(
        label="💾 Guardar parámetros (JSON)",
        data=json.dumps(datos_json, indent=4),
        file_name="parametros_cotizacion.json",
        mime="application/json"
    )
