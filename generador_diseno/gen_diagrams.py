#!/usr/bin/env python3
import flowcharts as F
from flowcharts import box, header_box, arrow, new_canvas, finish, stage_label
from flowcharts import NAVY, BLUE, BLUE_D, LBLUE, RED, LRED, GREEN, LGREEN, GREY, LGREY, WHITE, AMBER, LAMBER
import os
OUT = "img"
os.makedirs(OUT, exist_ok=True)

# ----------------------------------------------------------------------
# 0. Programa SAP BUILD — visión general (portada de la sección común)
# ----------------------------------------------------------------------
def program_overview():
    fig, ax, top = new_canvas(h=6.4,
        title="Programa SAP BUILD — Modelos de Planeación en SAP Analytics Cloud",
        subtitle="Grupo Fanalca · Un patrón de diseño común aplicado a tres sociedades")
    midy = (top - 7) / 2 + 1
    # banda superior
    box(ax, 50, top - 10.5, 70, 6.2,
        "Grupo Fanalca · Programa SAP BUILD   (SAP S/4HANA + SAP Analytics Cloud + SAP DataSphere)",
        fc=NAVY, ec=NAVY, tc=WHITE, bold=True, fs=10.5, wrap=70)
    clients = [
        ("Fanalca S.A.", "Automotriz y metalmecánico.\nMetalmecánica · Honda Supermotos · Honda Autos.\nMigración desde SAP BPC.", BLUE, LBLUE),
        ("Ciudad Limpia", "Servicios de aseo urbano.\nBogotá · Neiva · Huila · CGS · RH.\nIngresos ordinarios + P×Q residuos.", GREEN, LGREEN),
        ("Transprensa S.A.S.", "Logística y transporte de carga.\n21 regionales · 46 CRM.\nP×Q por kg movilizado.", RED, LRED),
    ]
    xs = [21, 50, 79]
    for x, (name, desc, ec, fc) in zip(xs, clients):
        arrow(ax, (50, top - 13.6), (x, midy + 9), color=NAVY, lw=1.6,
              rad=0.0 if x == 50 else (0.05 if x > 50 else -0.05))
        header_box(ax, x, midy + 3.5, 26, 16, name, desc, hc=ec, ec=ec, fs=8.4, wrap=34)
        box(ax, x, midy - 12.5, 26, 9.5,
            "Ingresos  +  Costos/Gastos\n↓  Data Actions  ↓\nEEFF (P&G · Balance · Flujo)",
            fc=fc, ec=ec, fs=8.2, wrap=30)
        arrow(ax, (x, midy - 4.5), (x, midy - 7.6), color=ec, lw=1.8)
    ax.text(2, 1.4,
            "Patrón común: tres modelos de planeación (Ingresos y Costos/Gastos que consolidan en EEFF), "
            "dimensiones compartidas, integración vía SAP DataSphere y trazabilidad mediante la dimensión AUDITORIA.",
            ha="left", va="center", fontsize=8.2, color=GREY, style="italic")
    finish(fig, f"{OUT}/00_programa_overview.png")

# ----------------------------------------------------------------------
# FANALCA
# ----------------------------------------------------------------------
def fanalca():
    F.architecture(
        f"{OUT}/fanalca_arq.png", "Fanalca S.A.",
        sources=["SAP S/4HANA\n(FI · CO · SD · MM)", "Excel / Plantillas"],
        integration="SAP DataSphere\n\nVirtualización y\nmaestros",
        dims="SOCIEDAD · CEBES\nCECOS · CUENTA\nMONEDA · AUDITORIA\nVersion · Date\nREFERENCIA · CLIENTES\nRATIO",
        ingresos_label="Modelo de Ingresos\n9 dim · P×Q · cartera · inventario",
        costos_label="Modelo de Costos y Gastos\n8 dim · nómina · CIF · OPEX",
        outputs=["Stories y dashboards", "P&G · Balance · Flujo de Caja",
                 "Plan Bancos (5 años)", "Excel Add-in (key users)"],
        models_note="Migración SAP BPC → SAC: cada script/paquete se replica como Data Action. "
                    "El script T01 (motos + autos) se separa en dos Data Actions independientes para evitar sobreescritura.")
    F.dataflow(
        f"{OUT}/fanalca_flujo.png", "Fanalca S.A.",
        ingresos_items="• P×Q por referencia (moto / auto / autoparte)\n"
                       "• Juego de cartera (saldo inicial + facturación con IVA − recaudo)\n"
                       "• Juego de inventarios (unidades y pesos)",
        costos_items="• Nómina y CIF por CECO\n• Gastos OPEX importados desde UNOE\n"
                     "• Distribución de CECOS transversales (PDB 97/3 · PPC por %)",
        eeff_items="• Estado de Resultados: P&G «sábana» y P&G NIT\n"
                   "• Balance General\n• Flujo de Caja directo\n"
                   "• Capital de trabajo y costo de oportunidad (IBR / SOFR)",
        ingresos_engine="Data Actions: T01 motos · T01 autos · autopartes · tubería ×2 · ambiental",
        costos_engine="Paquete UNOE → Gastos\n+ alícuotas de transversales",
        subtitle="Los modelos de Ingresos y Costos/Gastos consolidan en el EEFF mediante Data Actions (migrados de los paquetes SAP BPC).")
    F.pxq_flow(
        f"{OUT}/fanalca_pxq.png", "Fanalca S.A.",
        steps=["Unidades de venta × Precio (PVU) por referencia",
               "Aplicar IVA 19% / imp. consumo 8% y recuperación de fletes",
               "Costo = FOB × factor de internamiento × TRM",
               "Juego de cartera: saldo inicial + facturación − recaudo",
               "Juego de inventarios: inicial + compras − despachos"],
        result="Ingresos, costo de ventas e inventario → EEFF",
        subtitle="Aplica a motos (HMC / CBU), autos (HAC / agencias / talleres) y líneas de Metalmecánica.")

# ----------------------------------------------------------------------
# CIUDAD LIMPIA
# ----------------------------------------------------------------------
def ciudad():
    F.architecture(
        f"{OUT}/ciudad_arq.png", "Ciudad Limpia",
        sources=["SAP S/4HANA\n(ACDOCA · SKA1 · CEPC · CSKS · T001)",
                 "Resumen Jefe de Tarifas\n(ingresos ordinarios)",
                 "Áreas CGS / RH\n(P×Q de residuos)",
                 "Excel / Plantillas\nestándar por categoría"],
        integration="Conexión nativa\nSAC ↔ S/4HANA\n\nCDS Views\n(carga diaria)",
        dims="SOCIEDAD_CL\nCEBE_CL (componentes)\nCECO_CL · CUENTA\nMONEDA · AUDITORIA\nVersion · Date · CLIENTE",
        ingresos_label="Modelo de Ingresos\nordinarios + P×Q (CGS / RH)",
        costos_label="Modelo de Gastos / Costos\nplantilla genérica · flota",
        outputs=["Dashboards por sociedad y área",
                 "EEFF: P&G · Balance · Flujo",
                 "KPIs: ton · km · usuarios · árboles",
                 "Reportes internos (gerencia / junta)"],
        models_note="Las licencias SAC se asignan únicamente a Planeación Financiera; las áreas operativas entregan plantillas "
                    "Excel que el equipo consolida y carga (opción de carga: Reemplazar con el dato definitivo).")
    F.dataflow(
        f"{OUT}/ciudad_flujo.png", "Ciudad Limpia",
        ingresos_items="• Ingresos ordinarios: valor total por componente\n  (Recolección, Barrido, Corte, Poda)\n"
                       "• P×Q CGS/RH: tarifa × toneladas/kilos por cliente y residuo",
        costos_items="• Mano de obra (modelo de personal)\n• Mantenimiento de flota (1 CECO por vehículo)\n"
                     "• Plantilla genérica: depreciaciones, TIC, servicios,\n  seguros, dotación, arrendamientos",
        eeff_items="• Estado de Resultados (P&G) — flujo automático\n"
                   "• Balance: cuentas de resultado + cuentas propias\n  (carga manual / S/4HANA)\n"
                   "• Flujo de Caja (P&G + balance + carga manual)\n• Depreciaciones acumuladas",
        ingresos_engine="Carga por plantilla\n+ cálculo P×Q (CGS / RH)",
        costos_engine="Consolidación de plantillas por área (Planeación Financiera)",
        subtitle="El P&G fluye automáticamente desde Ingresos y Gastos; las cuentas propias de balance y flujo se cargan de S/4HANA o manualmente.")
    F.pxq_flow(
        f"{OUT}/ciudad_pxq.png", "Ciudad Limpia (CGS / RH)",
        steps=["Toneladas / kilos por cliente y tipo de residuo",
               "Tarifa unitaria por tipo de residuo",
               "Importe = Cantidad × Tarifa",
               "Carga por sociedad y componente (CEBE_CL)"],
        result="Ingresos CGS / RH → EEFF",
        subtitle="CL Bogotá / Neiva / Huila cargan el valor total por componente; CGS y RH aplican P×Q sobre cantidades.")

# ----------------------------------------------------------------------
# TRANSPRENSA
# ----------------------------------------------------------------------
def transprensa():
    F.architecture(
        f"{OUT}/transprensa_arq.png", "Transprensa S.A.S.",
        sources=["SAP S/4HANA\n(SKA1 · CEPC · CSKS · ACDOCA)",
                 "Silotrans / Silotrack\n(kg · remesas · tarifas)",
                 "SIESA\n(P&G y nómina, transitorio)",
                 "Excel / Power BI\n(proceso actual)"],
        integration="SAP DataSphere\n\nIntegración,\nvirtualización\ny maestros",
        dims="SOCIEDAD_TRANS\nCEBE_TRANS (regional)\nCECOS_TRANS · CUENTA\nSERVICIO · CLIENTE\nMONEDA · AUDITORIA\nVersion · Date",
        ingresos_label="Modelo de Ingresos\nP×Q por regional y servicio",
        costos_label="Modelo de Gastos y Costos\nfletes · personal variable",
        outputs=["Stories: ejecución presupuestal",
                 "P&G y EBITDA por regional",
                 "Presupuesto Comercial vs. Financiero",
                 "Dashboards de seguimiento"],
        models_note="Presupuesto multi-versión (Comercial y Financiero). Los modelos de Talento Humano y Flujo de Caja "
                    "Diario se encuentran en diseño (fuera del alcance actual).")
    F.dataflow(
        f"{OUT}/transprensa_flujo.png", "Transprensa S.A.S.",
        ingresos_items="• P×Q: kg proyectados × tarifa ($/kg) por regional\n"
                       "• Crédito (B2B) vs. Contado / contraentrega (CRM)\n"
                       "• Clientes especiales (Ingreso, T1, Soy Más)\n"
                       "• Estacionalidad mensual (histórico N-1)",
        costos_items="• Fletes de expedición / reexpedición (Silotrans)\n"
                     "• Personal temporal variable (índice persona/kg)\n"
                     "• Comisiones CRM y fuerza de ventas\n"
                     "• Arrendamientos (IPC) y gastos fijos",
        eeff_items="• Estado de Resultados (P&G administrativo – PCGA)\n"
                   "• Apertura por regional\n• EBITDA por centro de beneficio\n"
                   "• Balance y Flujo de Caja",
        ingresos_engine="Data Action P×Q (kg × tarifa)\n+ estacionalidad",
        costos_engine="Data Action personal temporal (ajuste por kg) + fletes",
        subtitle="Los modelos de Ingresos y Costos alimentan el EEFF con P&G y EBITDA por regional.")
    F.pxq_flow(
        f"{OUT}/transprensa_pxq.png", "Transprensa S.A.S.",
        steps=["Base histórica N-1: kg y pesos por regional (Silotrans)",
               "Crecimiento en volumen (% kg por regional)",
               "Crecimiento en tarifa ($/kg · IPC + mercado)",
               "Distribución CRM (contado) vs. Crédito (B2B)",
               "Estacionalidad mensual + clientes especiales"],
        result="Presupuesto de ingresos por regional × servicio × mes",
        subtitle="Metodología P×Q: kilogramos movilizados × tarifa por kilogramo, por regional y tipo de servicio.")

if __name__ == "__main__":
    program_overview()
    fanalca()
    ciudad()
    transprensa()
    print("ALL DIAGRAMS DONE")
