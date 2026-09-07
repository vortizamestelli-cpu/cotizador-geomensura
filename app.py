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
# 1. PARÁMETROS GENERALES Y CUBICACIÓN
# ---------------------------------------------------------
st.subheader("1. Parámetros Generales y Cubicaciones")

modalidad_ejecucion = st.radio(
    "Modalidad de Operación Interna",
    [
        "Desglosada (Gestión propia de Maquinaria, Petróleo y Transporte)",
        "Subcontrato Completo / Todo Incluido (Tarifa cerrada por m³)"
    ],
    index=1
)

col_v1, col_v2, col_v3 = st.columns(3)
with col_v1:
    volumen_banco = st.number_input("Volumen Geométrico en Banco (m³)", min_value=1.0, value=2914.00, step=10.0)
with col_v2:
    factor_esponjamiento = st.number_input("Factor de Esponjamiento", min_value=1.0, max_value=2.0, value=1.00, step=0.05)
with col_v3:
    duracion_dias = st.number_input("Duración Estimada de Faena (días)", min_value=1, value=8, step=1)

# Cálculo de volumen a cobrar según esponjamiento
volumen_cobrar = volumen_banco * factor_esponjamiento

if factor_esponjamiento == 1.00:
    unidad_medicion = "m³ geométricos (en banco / topografía)"
    texto_esponjamiento_nota = "Cobro en base a volumen geométrico medido mediante topografía en banco (Factor 1.00)."
else:
    unidad_medicion = "m³ esponjados (sobre camión)"
    texto_esponjamiento_nota = f"Cobro en base a volumen esponjado sobre camión (Factor {factor_esponjamiento:.2f})."

st.info(f"💡 **Criterio de Medición:** {texto_esponjamiento_nota}")

# Variables por defecto
costo_maquinaria = 0.0
costo_combustible = 0.0
costo_transporte = 0.0
costo_paleteros = 0.0
costo_aljibe = 0.0
costo_topografia = 0.0

if modalidad_ejecucion == "Subcontrato Completo / Todo Incluido (Tarifa cerrada por m³)":
    costo_subcontrato_m3 = st.number_input(
        f"Costo del Subcontrato por {unidad_medicion} ($/m³)", 
        min_value=0.0, 
        value=13875.0, 
        step=100.0
    )
    costo_interno_total = volumen_cobrar * costo_subcontrato_m3
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
            f"Tarifa transporte + botadero autorizado ($/{unidad_medicion})", 
            min_value=0.0, 
            value=3200.0, 
            step=100.0
        )
        costo_transporte = volumen_cobrar * tarifa_transporte_m3

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
            costo_aljibe = duracion_dias * 120000.0
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
    pu_neto_mandante = st.number_input(f"Precio Unitario Final Neto ($/{unidad_medicion})", min_value=0.0, value=15750.0, step=250.0)
    oferta_total_neto = volumen_cobrar * pu_neto_mandante

elif tipo_oferta == "Definir por porcentaje de margen (%)":
    margen_pct = st.number_input("Porcentaje de Margen Deseado (%)", min_value=0.0, value=13.5, step=0.5)
    oferta_total_neto = costo_interno_total * (1 + (margen_pct / 100.0))
    pu_neto_mandante = oferta_total_neto / volumen_cobrar if volumen_cobrar > 0 else 0.0

else:
    oferta_total_neto = st.number_input("Precio Final Neto Objetivo ($)", min_value=0.0, value=45895500.0, step=100000.0)
    pu_neto_mandante = oferta_total_neto / volumen_cobrar if volumen_cobrar > 0 else 0.0

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

# Visualización gráfica simple de desglose
if total_bruto > 0:
    pct_costo = (costo_interno_total / total_bruto) * 100
    pct_margen = (margen_monto / total_bruto) * 100
    pct_iva = (iva_monto / total_bruto) * 100
    st.caption(f"Distribución del Total Bruto: **Costo Operativo ({pct_costo:.1f}%)** | **Margen Neto ({pct_margen:.1f}%)** | **IVA ({pct_iva:.1f}%)**")
    st.progress(int(pct_costo + pct_margen))

st.markdown("---")

# ---------------------------------------------------------
# VISTA PREVIA Y PDF
# ---------------------------------------------------------
st.subheader("📋 Vista Previa de la Propuesta Formal")

if factor_esponjamiento == 1.00:
    texto_descripcion_servicio = (
        f"Retiro de aproximadamente {volumen_cobrar:,.0f} m³ de material, medidos en volumen geométrico (en banco / terreno) "
        f"mediante levantamiento topográfico. Incluye gestión operativa, maquinaria y transporte a botadero autorizado."
    ).replace(",", ".")
    texto_control_volumen = "Los m³ finales se ajustarán estrictamente mediante cubicación topográfica de terreno (volumen geométrico en banco)."
else:
    texto_descripcion_servicio = (
        f"Retiro de aproximadamente {volumen_cobrar:,.0f} m³ de material, medidos esponjados sobre camión (Factor {factor_esponjamiento:.2f}). "
        f"Incluye gestión operativa, maquinaria y transporte a botadero autorizado."
    ).replace(",", ".")
    texto_control_volumen = "Los m³ finales se ajustarán mediante conteo y cubicaje sobre camión (volumen esponjado)."

st.markdown("### PRESUPUESTO DE SERVICIO DE RETIRO Y MOVIMIENTO DE TIERRAS")
st.markdown(f"- **Para:** {cliente_nombre}")
st.markdown("- **De:** EDOS SpA")
st.markdown(f"- **Ubicación:** {ubicacion_obra}")
st.markdown(f"- **Validez de la Oferta:** {validez_oferta} días corridos")

st.markdown("#### 1. Detalle del Servicio y Valores")
st.write(texto_descripcion_servicio)

st.table([
    {
        "Descripción": f"Servicio completo de retiro / excavación ({unidad_medicion})",
        "Cantidad Estimada": f"{volumen_cobrar:,.0f} m³".replace(",", "."),
        "P. Unitario Neto": f"${pu_neto_mandante:,.0f} / m³".replace(",", "."),
        "Total Neto Estimado": f"${oferta_total_neto:,.0f}".replace(",", ".")
    }
])

# Totales vinculados dinámicamente
st.markdown(f"* **Subtotal neto:** ${oferta_total_neto:,.0f} CLP".replace(",", "."))
st.markdown(f"* **IVA (19%):** ${iva_monto:,.0f} CLP".replace(",", "."))
st.markdown(f"* **Bruto total:** ${total_bruto:,.0f} CLP".replace(",", "."))

st.markdown("#### 2. Condiciones de Pago y Ajuste")
st.markdown(f"- **Forma de Pago:** {condicion_pago}.")
st.markdown(f"- **Control de Volumen:** {texto_control_volumen}")
st.markdown(f"- **Stand-by / Mínimo Diario:** Se establece un mínimo de {minimo_horas} horas diarias garantizadas por equipo contratado.")

st.markdown("#### 3. Protocolo de Mediciones y Control Topográfico")
st.markdown("- **Respaldo Topográfico:** En modalidad geométrica, las mediciones se respaldarán con plano de avance cota inicial y final.")
st.markdown("- **Control de Vales:** En modalidad sobre camión, cada viaje será validado mediante vale firmado por la inspección técnica (ITO).")

st.markdown("#### 4. Material Diferenciado e Imprevistos")
st.markdown("- **Terreno Común:** Las tarifas aplican a terreno de fácil o mediana excavación. La presencia de roca, napa freática, escombros no previstos o cimentaciones requerirá cotización adicional.")
st.markdown("- **Stand-by Imputable:** Paralizaciones atribuibles a la obra mantendrán la tarifa de arriendo diario garantizado.")

st.markdown("#### 5. Exclusiones")
st.markdown("- Camión aljibe para mitigación de polución (salvo acuerdo explícito).")
st.markdown("- Medidas de mitigación ambiental adicionales (Malla Rachel, lavador de ruedas).")
st.markdown("- Cierre perimetral y seguridad vial externa (paleteros).")
st.markdown("- Permisos municipales, cortes de calle o autorizaciones regulatorias.")

st.caption("*Vicente Ortiz Amestelli - EDOS SpA*")

# ---------------------------------------------------------
# GENERACIÓN DE PDF (VERTICAL / PORTRAIT OBLIGATORIO)
# ---------------------------------------------------------
class PDFPresupuesto(FPDF):
    def __init__(self):
        # 'P' = Portrait (Vertical), 'mm' = milímetros, 'A4' = tamaño de página
        super().__init__(orientation='P', unit='mm', format='A4')

    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 7, 'EDOS SpA - Servicios de Geomensura y Movimiento de Tierras', 0, 1, 'C')
        self.set_font('Arial', 'I', 8)
        self.cell(0, 4, 'Propuesta Técnica y Comercial', 0, 1, 'C')
        self.line(10, 21, 200, 21)
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

def generar_pdf():
    pdf = PDFPresupuesto()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Encabezado
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 6, "PRESUPUESTO DE RETIRO Y MOVIMIENTO DE TIERRAS", 0, 1, "L")
    pdf.ln(2)

    pdf.set_font("Arial", "", 9)
    pdf.cell(0, 5, f"Para: {cliente_nombre}", 0, 1)
    pdf.cell(0, 5, "De: EDOS SpA", 0, 1)
    pdf.cell(0, 5, f"Ubicacion: {ubicacion_obra}", 0, 1)
    pdf.cell(0, 5, f"Validez de la Oferta: {validez_oferta} dias corridos", 0, 1)
    pdf.ln(3)

    # 1. Detalle
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 6, "1. Detalle del Servicio y Valores", 0, 1)
    pdf.set_font("Arial", "", 8)
    pdf.multi_cell(0, 4, texto_descripcion_servicio.encode('latin-1', 'replace').decode('latin-1'))
    pdf.ln(2)

    # Tabla en vertical (Suma total de anchos = 190 mm)
    pdf.set_font("Arial", "B", 8)
    pdf.cell(80, 6, "Descripcion", 1, 0, "C")
    pdf.cell(30, 6, "Cantidad", 1, 0, "C")
    pdf.cell(40, 6, "P. Unitario Neto", 1, 0, "C")
    pdf.cell(40, 6, "Total Neto", 1, 1, "C")

    pdf.set_font("Arial", "", 8)
    pdf.cell(80, 6, "Servicio completo de retiro / excavacion", 1, 0, "L")
    pdf.cell(30, 6, f"{volumen_cobrar:,.0f} m3".replace(",", "."), 1, 0, "C")
    pdf.cell(40, 6, f"${pu_neto_mandante:,.0f} / m3".replace(",", "."), 1, 0, "R")
    pdf.cell(40, 6, f"${oferta_total_neto:,.0f}".replace(",", "."), 1, 1, "R")
    pdf.ln(3)

    # Totales
    pdf.set_font("Arial", "", 9)
    pdf.cell(110, 5, "", 0, 0)
    pdf.cell(40, 5, "Subtotal Neto:", 0, 0, "R")
    pdf.cell(40, 5, f"${oferta_total_neto:,.0f} CLP".replace(",", "."), 0, 1, "R")

    pdf.cell(110, 5, "", 0, 0)
    pdf.cell(40, 5, "IVA (19%):", 0, 0, "R")
    pdf.cell(40, 5, f"${iva_monto:,.0f} CLP".replace(",", "."), 0, 1, "R")

    pdf.set_font("Arial", "B", 9)
    pdf.cell(110, 5, "", 0, 0)
    pdf.cell(40, 5, "Total Bruto:", 0, 0, "R")
    pdf.cell(40, 5, f"${total_bruto:,.0f} CLP".replace(",", "."), 0, 1, "R")
    pdf.ln(4)

    # 2. Condiciones
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 6, "2. Condiciones de Pago y Ajuste", 0, 1)
    pdf.set_font("Arial", "", 8)
    pdf.cell(0, 4, f"- Forma de Pago: {condicion_pago}.", 0, 1)
    pdf.multi_cell(0, 4, f"- Control de Volumen: {texto_control_volumen}".encode('latin-1', 'replace').decode('latin-1'))
    pdf.cell(0, 4, f"- Stand-by / Minimo Diario: {minimo_horas} horas diarias garantizadas por equipo.", 0, 1)
    pdf.ln(3)

    # 3. Protocolos
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 6, "3. Protocolo de Mediciones y Control Topografico", 0, 1)
    pdf.set_font("Arial", "", 8)
    pdf.cell(0, 4, "- Mediciones respaldadas segun levantamiento inicial/final o vales de camion firmados.", 0, 1)
    pdf.ln(3)

    # 4. Imprevistos y Exclusiones
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 6, "4. Material Diferenciado y Exclusiones", 0, 1)
    pdf.set_font("Arial", "", 8)
    pdf.cell(0, 4, "- Tarifa para terreno comun (roca o napa requeriran cotizacion adicional).", 0, 1)
    pdf.cell(0, 4, "- Excluye camion aljibe, mitigacion ambiental adicional y permisos municipales.", 0, 1)
    pdf.ln(8)

    # Firma
    pdf.set_font("Arial", "B", 9)
    pdf.cell(0, 5, "Vicente Ortiz Amestelli", 0, 1, "R")
    pdf.set_font("Arial", "", 8)
    pdf.cell(0, 4, "EDOS SpA", 0, 1, "R")

    # Retorno de bytes compatible con fpdf2
    pdf_output = pdf.output()
    if isinstance(pdf_output, str):
        return pdf_output.encode('latin-1', 'replace')
    return bytes(pdf_output)

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
        "volumen_banco": volumen_banco,
        "factor_esponjamiento": factor_esponjamiento,
        "volumen_cobrar": volumen_cobrar,
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
