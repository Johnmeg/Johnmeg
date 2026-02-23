# SAC Planning - Arquitecturas de Implementación por Escenario

> **Best Practices SAP** | Fecha: 2026-02-23
> Documento de referencia técnica para la implementación de SAP Analytics Cloud Planning

---

## Tabla de Contenido

1. [Escenario 1: Solo S/4HANA](#escenario-1-solo-s4hana)
2. [Escenario 2: S/4HANA + SAP Datasphere](#escenario-2-s4hana--sap-datasphere)
3. [Escenario 3: S/4HANA + BW/4HANA](#escenario-3-s4hana--bw4hana)
4. [Escenario 4: Solo SAP ECC](#escenario-4-solo-sap-ecc)
5. [Tabla Comparativa](#tabla-comparativa)
6. [Consideraciones Generales de Seguridad y Gobernanza](#consideraciones-generales)

---

## Escenario 1: Solo S/4HANA

### Descripción General

En este escenario, SAC Planning se conecta directamente a S/4HANA aprovechando las capacidades de **Embedded Analytics** y la arquitectura HANA nativa. Es la integración más simple y directa dentro del ecosistema SAP moderno.

### Diagrama de Arquitectura

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          SAP CLOUD (SaaS)                                    │
│                                                                               │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                SAP Analytics Cloud (SAC)                              │   │
│  │                                                                        │   │
│  │  ┌─────────────────────┐    ┌─────────────────────────────────────┐  │   │
│  │  │  Planning Models     │    │       Story / Dashboards            │  │   │
│  │  │  ┌───────────────┐  │    │  ┌─────────┐  ┌─────────────────┐  │  │   │
│  │  │  │ Multi-Action  │  │    │  │ Reports │  │  Input Schedule │  │  │   │
│  │  │  │ Sequences     │  │    │  └─────────┘  └─────────────────┘  │  │   │
│  │  │  └───────────────┘  │    └─────────────────────────────────────┘  │   │
│  │  │  ┌───────────────┐  │                                              │   │
│  │  │  │  Data Actions │  │    ┌─────────────────────────────────────┐  │   │
│  │  │  └───────────────┘  │    │   Business Content Packages          │  │   │
│  │  └─────────────────────┘    └─────────────────────────────────────┘  │   │
│  └──────────────────────┬───────────────────────────────────────────────┘   │
│                          │                                                    │
│         ┌────────────────▼──────────────────┐                               │
│         │      SAP Integration Suite         │                               │
│         │  (SAP Cloud Connector / BTP)       │                               │
│         └────────────────┬──────────────────┘                               │
└──────────────────────────┼──────────────────────────────────────────────────┘
                           │ Live Data Connection
                           │ (HTTPS / OData)
┌──────────────────────────┼──────────────────────────────────────────────────┐
│                 ON-PREMISE / PRIVATE CLOUD                                    │
│                                                                               │
│  ┌───────────────────────▼─────────────────────────────────────────────┐    │
│  │                    S/4HANA (On-Premise / PCE)                         │    │
│  │                                                                        │    │
│  │  ┌──────────────────┐   ┌─────────────────┐   ┌──────────────────┐  │    │
│  │  │  BW Embedded     │   │  CDS Views       │   │  Fiori Apps      │  │    │
│  │  │  (BW/4HANA       │   │  (Analytical,    │   │  (Planning       │  │    │
│  │  │   Embedded)      │   │  Calculation)    │   │   Integration)   │  │    │
│  │  └────────┬─────────┘   └────────┬────────┘   └──────────────────┘  │    │
│  │           │                      │                                    │    │
│  │  ┌────────▼──────────────────────▼────────────────────────────────┐  │    │
│  │  │              SAP HANA (In-Memory Database)                       │  │    │
│  │  │   ┌────────────┐  ┌─────────────┐  ┌───────────────────────┐   │  │    │
│  │  │   │ Actuals    │  │  Master Data│  │  Planning Data        │   │  │    │
│  │  │   │ (CO/FI/SD) │  │  (0MATERIAL │  │  (Write-back via      │   │  │    │
│  │  │   │            │  │   0COSTCTR) │  │   Data Actions)       │   │  │    │
│  │  │   └────────────┘  └─────────────┘  └───────────────────────┘   │  │    │
│  │  └───────────────────────────────────────────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │               SAP Cloud Connector (SCC)                               │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└───────────────────────────────────────────────────────────────────────────────┘
```

### Flujo de Datos

```
S/4HANA Actuals ──────► CDS Views / BW Embedded ──────► SAC Live Connection
                                                                   │
                                                     ┌─────────────▼──────────────┐
                                                     │   SAC Planning Model        │
                                                     │   (Import/Live Connection)  │
                                                     └─────────────┬──────────────┘
                                                                   │
                                              Input Schedule ──────┤ Planners
                                              Data Actions  ──────►│ (Write-back)
                                                                   │
                                                     ┌─────────────▼──────────────┐
                                                     │  S/4HANA Planning Table     │
                                                     │  (via OData Write-back)     │
                                                     └────────────────────────────┘
```

### Componentes Técnicos

| Componente | Detalle | Propósito |
|---|---|---|
| **Live Data Connection** | HANA Live / BW Live | Acceso en tiempo real a datos de S/4HANA |
| **CDS Views** | Analytical CDS (ABAP) | Capa semántica para datos de actuals |
| **BW Embedded** | BW/4HANA Embedded in S/4 | Modelos InfoProvider para planning |
| **SAP Cloud Connector** | SCC 2.x | Túnel seguro On-Premise ↔ Cloud |
| **OData Write-back** | OData v2/v4 | Retorno de datos de planning a S/4HANA |
| **Data Actions** | SAC Planning Engine | Lógica de cálculo y distribución |

### Tipos de Conexión Recomendados

```
OPCION A: Live Data Connection (Preferida para datos actuales)
  SAC ──[HTTPS/443]──► SCC ──[RFC/HTTP]──► S/4HANA (HANA DB)
  Ventaja: Datos en tiempo real, sin replicación
  Limitación: Rendimiento depende de red y HANA

OPCION B: Import Connection (Preferida para grandes volúmenes de planning)
  S/4HANA ──► Export/OData ──► SAC Import Job ──► SAC Planning Model
  Ventaja: Mejor rendimiento para planificación masiva
  Limitación: Datos no en tiempo real
```

### Best Practices - Escenario 1

- Utilizar **CDS Views con anotaciones Analytics** para exponer datos de actuals
- Habilitar **ODP (Operational Data Provisioning)** para extracciones delta
- Implementar **SAP BW Embedded** para modelos de planning complejos (CB models)
- Usar **Import Data Connection** para Planning Models en producción
- Mantener **Live Connection** solo para reporting y análisis ad-hoc
- Configurar **SAP Cloud Connector** con certificados de alta disponibilidad
- Usar **Multi-Action** para secuenciar el write-back a S/4HANA
- Aplicar **Restricciones de Acceso de Datos (DAC)** en SAC para control granular

---

## Escenario 2: S/4HANA + SAP Datasphere

### Descripción General

SAP Datasphere actúa como **capa de integración y semántica empresarial**, federando datos de S/4HANA y otras fuentes. SAC Planning consume desde Datasphere a través de conexiones Live, permitiendo una capa analítica unificada.

### Diagrama de Arquitectura

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          SAP CLOUD (SaaS)                                    │
│                                                                               │
│  ┌────────────────────────────┐    ┌─────────────────────────────────────┐  │
│  │  SAP Analytics Cloud (SAC) │    │        SAP Datasphere                │  │
│  │                            │    │                                       │  │
│  │  ┌──────────────────────┐  │    │  ┌──────────────┐  ┌─────────────┐  │  │
│  │  │   Planning Models    │◄─┼────┼─►│  Business     │  │  Data       │  │  │
│  │  │   (SAC Models with   │  │    │  │  Layer (BL)   │  │  Flows      │  │  │
│  │  │    Datasphere Live   │  │    │  │  Perspectives │  │  (Pipelines)│  │  │
│  │  │    Connection)       │  │    │  └──────┬───────┘  └──────┬──────┘  │  │
│  │  └──────────────────────┘  │    │         │                 │          │  │
│  │  ┌──────────────────────┐  │    │  ┌──────▼───────┐  ┌─────▼──────┐  │  │
│  │  │   Stories /          │  │    │  │  Analytic    │  │  Replication│  │  │
│  │  │   Dashboards         │  │    │  │  Models      │  │  Flows     │  │  │
│  │  └──────────────────────┘  │    │  └──────┬───────┘  └──────┬──────┘  │  │
│  └────────────────────────────┘    │         │                 │          │  │
│                                     │  ┌──────▼─────────────────▼──────┐  │  │
│                                     │  │    SAP HANA Cloud (HDC)         │  │  │
│                                     │  │    (Persistence Layer)          │  │  │
│                                     │  │  ┌──────────┐  ┌────────────┐  │  │  │
│                                     │  │  │  Spaces   │  │  Virtual   │  │  │  │
│                                     │  │  │  (Finance,│  │  Tables    │  │  │  │
│                                     │  │  │   HR,     │  │  (Remote   │  │  │  │
│                                     │  │  │   Sales)  │  │   Tables)  │  │  │  │
│                                     │  │  └──────────┘  └────────────┘  │  │  │
│                                     │  └───────────────────────────────┘  │  │
│                                     └─────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────────────────┘
                             │
              ┌──────────────▼──────────────┐
              │    SAP Integration Suite     │
              │    (BTP / Cloud Connector)   │
              └──────────────┬──────────────┘
                             │
┌────────────────────────────┼────────────────────────────────────────────────┐
│           ON-PREMISE / PRIVATE CLOUD                                         │
│                            │                                                  │
│  ┌─────────────────────────▼─────────────────────────────────────────────┐  │
│  │                       S/4HANA                                           │  │
│  │                                                                          │  │
│  │  ┌─────────────┐   ┌─────────────┐   ┌──────────────┐                  │  │
│  │  │  FI / CO    │   │  CDS Views  │   │  ODP / SLT   │                  │  │
│  │  │  Actuals    │──►│  (Exposed   │──►│  (Replication│                  │  │
│  │  │             │   │   for ODP)  │   │   to DS)     │                  │  │
│  │  └─────────────┘   └─────────────┘   └──────────────┘                  │  │
│  │  ┌─────────────┐                                                         │  │
│  │  │  Master Data│───────────────────────────────────────► Datasphere      │  │
│  │  │  (Cost Ctr, │   (via Replication Flow)                                │  │
│  │  │   Profit Ctr│                                                         │  │
│  │  │   WBS)      │                                                         │  │
│  │  └─────────────┘                                                         │  │
│  └─────────────────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────────────────────┘
```

### Flujo de Datos Detallado

```
FLUJO DE DATOS ACTUALES (Actuals):
S/4HANA ──[ODP/SLT]──► Datasphere Replication Flow ──► HANA Cloud (Persisted)
                                                              │
                                                    Datasphere Analytic Model
                                                              │
                                                    SAC Live Connection (LDC)
                                                              │
                                                    SAC Planning Model

FLUJO DE DATOS MAESTROS (Master Data):
S/4HANA MDG ──[Replication Flow]──► Datasphere Space ──► Business Layer
                                                               │
                                                    SAC Planning Dimensions

FLUJO DE WRITE-BACK (Planning → S/4HANA):
SAC Planning ──[Data Action]──► Datasphere ──[OData/API]──► S/4HANA
                                    │
                          (Opcional: Persiste en HANA Cloud
                           para consolidación multiempresa)
```

### Arquitectura de Spaces en Datasphere

```
┌─────────────────────────────────────────────────────────────┐
│                 SAP Datasphere Tenant                         │
│                                                               │
│  ┌──────────────────┐  ┌──────────────────┐                 │
│  │  SPACE: Finance  │  │  SPACE: Shared   │                 │
│  │  ┌────────────┐  │  │  ┌────────────┐  │                 │
│  │  │ Replication│  │  │  │ Master Data│  │                 │
│  │  │ Tables     │  │  │  │ Dimensions │  │                 │
│  │  │(S4 Actuals)│  │  │  │(Cost Ctr,  │  │                 │
│  │  └────────────┘  │  │  │ Profit Ctr)│  │                 │
│  │  ┌────────────┐  │  │  └────────────┘  │                 │
│  │  │ Analytic   │  │  └──────────────────┘                 │
│  │  │ Model      │  │                                        │
│  │  │(for SAC)   │  │  ┌──────────────────┐                 │
│  │  └────────────┘  │  │  SPACE: Planning  │                 │
│  └──────────────────┘  │  ┌────────────┐  │                 │
│                         │  │ Planning   │  │                 │
│                         │  │ Write-back │  │                 │
│                         │  │ Tables     │  │                 │
│                         │  └────────────┘  │                 │
│                         └──────────────────┘                 │
└─────────────────────────────────────────────────────────────┘
```

### Best Practices - Escenario 2

- Organizar **Datasphere Spaces** por dominio funcional (Finance, HR, Sales)
- Usar **Replication Flows** (no Data Flows) para carga inicial y delta de S/4HANA
- Modelar en la **Business Layer** de Datasphere usando dimensiones y facts reutilizables
- Activar **Data Access Controls** en Datasphere para heredar seguridad desde S/4HANA
- SAC conecta a Datasphere via **Live Data Connection** tipo "SAP Datasphere"
- Para Planning write-back: usar **OData API** de Datasphere o escribir directo en HANA Cloud
- Implementar **Impact and Lineage Analysis** en Datasphere para trazabilidad
- Usar **Intelligent Lookup** en Datasphere para enriquecer datos de planning

---

## Escenario 3: S/4HANA + BW/4HANA

### Descripción General

Arquitectura clásica y robusta donde BW/4HANA sirve como **Data Warehouse empresarial** y capa de persistencia para planning. SAC Planning usa conexiones BW Live para acceder a InfoProviders y modelos de planning de BW.

### Diagrama de Arquitectura

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                           SAP CLOUD (SaaS)                                    │
│                                                                                │
│  ┌──────────────────────────────────────────────────────────────────────┐    │
│  │                   SAP Analytics Cloud (SAC)                            │    │
│  │                                                                         │    │
│  │  ┌────────────────────────┐    ┌────────────────────────────────────┐ │    │
│  │  │  SAC Planning Models    │    │     SAC Reporting / Stories        │ │    │
│  │  │                         │    │                                     │ │    │
│  │  │  ┌──────────────────┐   │    │  ┌──────────┐  ┌───────────────┐  │ │    │
│  │  │  │ Import Planning  │   │    │  │ Embedded │  │  Input        │  │ │    │
│  │  │  │ Model (from BW   │   │    │  │ Reporting│  │  Schedules    │  │ │    │
│  │  │  │ InfoProvider)    │   │    │  └──────────┘  └───────────────┘  │ │    │
│  │  │  └──────────────────┘   │    └────────────────────────────────────┘ │    │
│  │  │  ┌──────────────────┐   │                                            │    │
│  │  │  │ Allocation Rules │   │    ┌────────────────────────────────────┐ │    │
│  │  │  │ Data Actions     │   │    │  SAC Integrated Business Planning  │ │    │
│  │  │  │ Value Driver     │   │    │  (IBP) - Opcional                  │ │    │
│  │  │  │ Trees            │   │    └────────────────────────────────────┘ │    │
│  │  │  └──────────────────┘   │                                            │    │
│  │  └────────────────────────┘                                             │    │
│  └──────────────────────┬───────────────────────────────────────────────┘    │
│                          │ BW Live Connection                                  │
│                          │ (HTTPS via SCC)                                     │
└──────────────────────────┼──────────────────────────────────────────────────-─┘
                           │
              ┌────────────▼───────────┐
              │   SAP Cloud Connector  │
              └────────────┬───────────┘
                           │
┌──────────────────────────┼───────────────────────────────────────────────────┐
│              ON-PREMISE / PRIVATE CLOUD                                        │
│                          │                                                     │
│  ┌───────────────────────▼──────────────────────────────────────────────┐    │
│  │                    BW/4HANA                                            │    │
│  │                                                                         │    │
│  │  ┌────────────────┐  ┌────────────────┐  ┌──────────────────────────┐ │    │
│  │  │  InfoProviders  │  │  CompositeProvs │  │  BW Planning (BPS/IP)  │ │    │
│  │  │  ┌──────────┐  │  │  (aCompositeP) │  │  ┌──────────────────┐  │ │    │
│  │  │  │ aDSO     │  │  │                │  │  │  Real-time Info  │  │ │    │
│  │  │  │ (Write-  │  │  │  ┌──────────┐  │  │  │  Cube (RT-Cube)  │  │ │    │
│  │  │  │  enabled)│  │  │  │ InfoCube │  │  │  └──────────────────┘  │ │    │
│  │  │  └──────────┘  │  │  └──────────┘  │  │  ┌──────────────────┐  │ │    │
│  │  └────────────────┘  └────────────────┘  │  │  Planning Functions│ │ │    │
│  │                                            │  └──────────────────┘  │ │    │
│  │  ┌────────────────────────────────────┐   └──────────────────────────┘ │    │
│  │  │   BW Process Chain / DTP           │                                 │    │
│  │  │   (Data Transfer Process)          │                                 │    │
│  │  └────────────────────────────────────┘                                 │    │
│  │                                                                          │    │
│  │  ┌────────────────────────────────────────────────────────────────────┐ │    │
│  │  │                    SAP HANA                                          │ │    │
│  │  └────────────────────────────────────────────────────────────────────┘ │    │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                           ▲                                                      │
│                           │ ODP / SLT / Extractor                               │
│  ┌────────────────────────┴─────────────────────────────────────────────────┐   │
│  │                       S/4HANA                                              │   │
│  │                                                                             │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐                   │   │
│  │  │  FI Actuals  │  │  CO Actuals  │  │  SD / MM      │                   │   │
│  │  │  (0FI_GL_4,  │  │  (0CO_PA_1, │  │  Transactional│                   │   │
│  │  │  0FI_AR_4)   │  │   0CO_OM_*) │  │  Data         │                   │   │
│  │  └──────────────┘  └──────────────┘  └───────────────┘                   │   │
│  │  ┌──────────────────────────────────────────────────────────────────┐    │   │
│  │  │  ODP Extractors / CDS Views (for ODP)                              │    │   │
│  │  └──────────────────────────────────────────────────────────────────┘    │   │
│  └───────────────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────────────┘
```

### Flujo de Datos

```
EXTRACCION (S/4HANA → BW/4HANA):
S/4HANA Extractors ──[ODP Delta]──► BW/4HANA DTP ──► aDSO ──► CompositeProvider
   (0FI_GL_4, etc.)                   (Process Chain)

MODELADO (BW/4HANA):
aDSO (Write-enabled) ──► CompositeProvider ──► SAC BW Live Connection
                                                        │
                                              SAC Planning Model

PLANNING (SAC → BW/4HANA):
SAC Input Schedule ──► SAC Data Action ──► Write-back ──► BW/4HANA aDSO
                                                                │
                                                   S/4HANA (opcional retorno)
```

### Modelo de Datos BW/4HANA para Planning

```
┌─────────────────────────────────────────────────────────────┐
│              BW/4HANA Data Architecture                      │
│                                                               │
│  CAPA 1: RAW (Staging)                                       │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  DataSource (ODP) → PSA Layer → aDSO (Inbound)       │    │
│  └─────────────────────────────────────────────────────┘    │
│                        │                                      │
│  CAPA 2: HARMONIZED                                           │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  aDSO (Corporate Memory / Write-enabled for Plan)    │    │
│  │  ┌──────────────┐    ┌──────────────────────────┐   │    │
│  │  │   Actuals     │    │  Planning Data            │   │    │
│  │  │   (Read-only) │    │  (Write-enabled DSO)     │   │    │
│  │  └──────────────┘    └──────────────────────────┘   │    │
│  └─────────────────────────────────────────────────────┘    │
│                        │                                      │
│  CAPA 3: ANALYTICAL                                           │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  CompositeProvider (Actuals + Plan en un solo objeto)│    │
│  │  → Expuesto vía BW Live Connection a SAC             │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Opciones de Conexión SAC ↔ BW/4HANA

```
OPCION A: BW Live Connection (Recomendada)
  SAC ──[HTTPS]──► SCC ──[RFC/HTTP]──► BW/4HANA
  Ventaja: Acceso a InfoProviders y modelos en tiempo real
  Uso: Reporting y análisis de actuals vs plan

OPCION B: Import Data Connection (Planning)
  BW/4HANA ──[OData/BAPI]──► SAC Import Job ──► SAC Planning Model
  Ventaja: Mejor rendimiento para planning masivo
  Uso: Procesos de planning con grandes volúmenes

OPCION C: Hybrid (Best Practice)
  - Live para actuals (reporting)
  - Import para planning (performance)
  - Write-back via OData a BW Write-enabled aDSO
```

### Best Practices - Escenario 3

- Mantener **aDSO Write-enabled** separados para plan vs actuals en BW/4HANA
- Usar **CompositeProvider** para unificar actuals y plan en un solo proveedor
- Activar **ODP (Operational Data Provisioning)** en S/4HANA para delta eficiente
- Configurar **Process Chains** con alertas para monitoreo de cargas
- En SAC: usar **Import Connection** para Planning Models de alto volumen
- Utilizar **BW Transformations** para lógica de negocio antes de SAC
- Implementar **Authorization Objects** en BW (S_RS_AUTH) sincronizados con SAC DAC
- Considerar **SAP BW Bridge** si hay planes de migración hacia Datasphere

---

## Escenario 4: Solo SAP ECC

### Descripción General

SAP ECC no soporta conexiones Live nativas con SAC. La arquitectura requiere una **capa de integración explícita**, ya sea mediante SAP BW (Classic), extractores ABAP, o servicios OData habilitados en ECC. Se recomienda además planificar la **hoja de ruta hacia S/4HANA**.

### Diagrama de Arquitectura

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                           SAP CLOUD (SaaS)                                    │
│                                                                                │
│  ┌──────────────────────────────────────────────────────────────────────┐    │
│  │                   SAP Analytics Cloud (SAC)                            │    │
│  │                                                                         │    │
│  │  ┌────────────────────────┐    ┌─────────────────────────────────┐    │    │
│  │  │  SAC Planning Models    │    │   SAC Stories / Dashboards       │    │    │
│  │  │  (Import-based ONLY)    │    │                                   │    │    │
│  │  │                         │    │  ┌───────────┐  ┌────────────┐  │    │    │
│  │  │  ┌──────────────────┐   │    │  │ Actual vs │  │  Input     │  │    │    │
│  │  │  │ Private Dimension│   │    │  │ Plan      │  │  Schedules │  │    │    │
│  │  │  │ (Master Data     │   │    │  │ Reports   │  │            │  │    │    │
│  │  │  │  from ECC)       │   │    │  └───────────┘  └────────────┘  │    │    │
│  │  │  └──────────────────┘   │    └─────────────────────────────────┘    │    │
│  │  │  ┌──────────────────┐   │                                            │    │
│  │  │  │ Fact Data        │   │                                            │    │
│  │  │  │ (Imported from   │   │                                            │    │
│  │  │  │  BW / Files)     │   │                                            │    │
│  │  │  └──────────────────┘   │                                            │    │
│  │  └────────────────────────┘                                             │    │
│  └──────────────────────┬───────────────────────────────────────────────┘    │
│                          │ Import Data Connection                              │
│                          │ (Scheduled Jobs)                                    │
└──────────────────────────┼────────────────────────────────────────────────────┘
                           │
              ┌────────────▼───────────┐
              │   SAP Cloud Connector  │
              │   + SAP Integration    │
              │   Suite (opcional)     │
              └────────────┬───────────┘
                           │
┌──────────────────────────┼───────────────────────────────────────────────────┐
│              ON-PREMISE                                                        │
│                          │                                                     │
│            ┌─────────────┴──────────────────────┐                             │
│            │                                      │                             │
│  ┌─────────▼────────────┐    ┌───────────────────▼──────────────────────┐    │
│  │  OPCION A:           │    │  OPCION B: BW (Classic / 7.x)             │    │
│  │  SAP ABAP RFC / BAPI │    │                                            │    │
│  │  + OData (ICM)       │    │  ┌──────────────┐   ┌──────────────────┐  │    │
│  │                       │    │  │  InfoProviders│   │  BEx Queries     │  │    │
│  │  ┌─────────────────┐  │    │  │  (InfoCubes, │   │  (usado para     │  │    │
│  │  │ OData Services  │  │    │  │   DSO)       │   │   SAC Import)   │  │    │
│  │  │ activados via   │  │    │  └──────────────┘   └──────────────────┘  │    │
│  │  │ SICF (ECC)      │  │    │  ┌──────────────────────────────────┐    │    │
│  │  └─────────────────┘  │    │  │  Process Chains                   │    │    │
│  └──────────────────────┘    │  │  (ETL Automation)                 │    │    │
│                               │  └──────────────────────────────────┘    │    │
│                               └──────────────────────────────────────────┘    │
│                                              ▲                                  │
│                                              │ Extractors / ODP (si BW 7.5+)  │
│  ┌───────────────────────────────────────────┴──────────────────────────┐    │
│  │                         SAP ECC (6.0 / EHP7/8)                        │    │
│  │                                                                         │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                 │    │
│  │  │  FI Module   │  │  CO Module   │  │  SD / MM     │                 │    │
│  │  │  (Classic GL)│  │  (Cost Ctr,  │  │  Transact.  │                 │    │
│  │  │              │  │   Profit Ctr)│  │  Data        │                 │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘                 │    │
│  │  ┌──────────────────────────────────────────────────────────────────┐  │    │
│  │  │  BC Extractors (0FI_GL_4, 0CO_OM_OPA_1, etc.)                   │  │    │
│  │  │  RFC-enabled Function Modules / BAPI                              │  │    │
│  │  │  ABAP Reports (ALV) → File export opcional                        │  │    │
│  │  └──────────────────────────────────────────────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────────────┘
```

### Opciones de Integración ECC → SAC

```
┌─────────────────────────────────────────────────────────────────────────────┐
│           OPCIONES DE CONEXION ECC → SAC (de menor a mayor complejidad)      │
│                                                                               │
│  OPCION 1: File Import (Mínima infraestructura)                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  ECC ALV/Report ──► Export CSV/Excel ──► SAC File Upload               │ │
│  │  Ventaja: Sin infraestructura adicional                                  │ │
│  │  Desventaja: Manual, no escalable, sin tiempo real                       │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
│  OPCION 2: OData Services desde ECC (Recomendada mínima)                    │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  ECC OData (SEGW) ──[SCC]──► SAC Import Connection (OData)             │ │
│  │  Ventaja: Automatizable, sin BW adicional                                │ │
│  │  Desventaja: Requiere desarrollo ABAP, rendimiento limitado              │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
│  OPCION 3: SAP BW 7.x como capa intermedia (Recomendada estándar)           │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  ECC Extractors ──► BW 7.x ──[BW Live/Import]──► SAC Planning          │ │
│  │  Ventaja: ETL robusto, modelos reutilizables, InfoObjects estándar       │ │
│  │  Desventaja: Infraestructura adicional (BW server)                       │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
│  OPCION 4: SAP Integration Suite / CPI (Moderna)                            │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  ECC RFC/BAPI ──► SAP Integration Suite (CPI) ──► SAC via API          │ │
│  │  Ventaja: Cloud-native, orquestación avanzada                            │ │
│  │  Desventaja: Licencia CPI adicional, complejidad de implementación       │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Flujo de Datos ECC → SAC Planning (Opción Recomendada con BW)

```
ECC Extractores           BW 7.x                    SAC
─────────────────         ─────────────────────     ──────────────────────
0FI_GL_4 (GL)    ──►    DataSource ──► DSO ──►   Import Connection
0CO_OM_OPA_1     ──►    InfoCube        │        (Scheduled Daily)
0SD_C03 (Sales)  ──►    InfoObject  ◄───┘              │
                         (0COSTCENTER,             SAC Planning Model
                          0PROFIT_CTR)                  │
                              │                    Planning Cycles
                         BEx Query                 (Input Schedules)
                         (for SAC Import)               │
                                                   Write-back via File
                                                   / OData to ECC
                                                   (Manual Process)
```

### Write-back Limitations en ECC

```
IMPORTANTE: ECC no soporta write-back nativo desde SAC.
Las opciones son:

1. Export desde SAC (CSV) ──► Manual import en ECC
   via LSMW / BAPI / IDoc

2. SAP Integration Suite ──► BAPI_ACC_GL_POSTING
   (automatizado, requiere desarrollo)

3. SAP Data Services ──► ETL hacia ECC Tables
   (complejo, no recomendado)

4. [MEJOR PRACTICA]: Usar SAC Planning como sistema
   de planning standalone, exportar resultados
   a ECC solo para posting de journals finales.
```

### Hoja de Ruta Recomendada (ECC)

```
FASE 1 (Corto plazo): Implementar SAC con ECC via BW 7.x / OData
FASE 2 (Mediano plazo): Migrar BW 7.x a BW/4HANA (escenario 3)
FASE 3 (Largo plazo): Migrar ECC a S/4HANA (escenario 1 o 2)

Esto protege la inversión en SAC Planning y habilita
capacidades avanzadas de forma incremental.
```

### Best Practices - Escenario 4

- **No usar Live Connection** con ECC (no soportado nativamente)
- Implementar **SAP BW 7.x** como capa intermedia si no existe
- Usar **Extractores de Negocio estándar** (0FI_*, 0CO_*, 0SD_*)
- Programar **Import Jobs en SAC** durante ventanas de no-producción
- Implementar **Slowly Changing Dimensions (SCD)** para master data en BW
- Definir **Planning Scope** claro: SAC no puede leer/escribir tablas ECC directamente
- Documentar proceso de **retorno de datos de planning a ECC** (manual o via BAPI)
- Planificar la **migración hacia S/4HANA** en el roadmap tecnológico

---

## Tabla Comparativa

| Criterio | Escenario 1 (S/4HANA) | Escenario 2 (S/4HANA + DS) | Escenario 3 (S/4HANA + BW/4) | Escenario 4 (ECC) |
|---|---|---|---|---|
| **Tipo de Conexión** | Live / Import | Live (Datasphere) | BW Live / Import | Import solo |
| **Latencia de datos** | Tiempo real | Casi real (replicación) | Near-real (BW Load) | Batch (diario) |
| **Write-back nativo** | Si (OData) | Si (Datasphere API) | Si (BW aDSO) | Limitado (manual) |
| **Complejidad setup** | Baja | Media | Media-Alta | Alta |
| **Escalabilidad** | Alta | Muy Alta | Alta | Baja-Media |
| **Gobernanza de datos** | Media | Alta | Alta | Baja |
| **Costo infraestructura** | Bajo | Medio | Medio | Alto |
| **Recomendación SAP** | Preferida moderna | Preferida enterprise | Preferida DW | Transitoria |

---

## Consideraciones Generales

### Seguridad y Gobernanza

```
Todos los escenarios deben implementar:

1. AUTENTICACION
   - SSO via SAP IDP / Azure AD / Okta
   - OAuth 2.0 para conexiones de sistema
   - Certificate-based para SCC

2. AUTORIZACION
   - DAC (Data Access Controls) en SAC
   - Roles de Planning (Owner, Reviewer, Contributor)
   - Sincronización con roles de S/4HANA / BW / ECC

3. RED
   - SAP Cloud Connector en HA (Maestro + Esclavo)
   - Whitelist de IPs para SAC endpoints
   - TLS 1.2+ en todas las conexiones

4. DATOS
   - Clasificación de datos sensibles (GDPR/compliance)
   - Enmascaramiento en entornos de no-producción
   - Audit log habilitado en SAC y sistemas fuente
```

### Gestión de Landscapes

```
LANDSCAPE RECOMENDADO (3 sistemas):

DEV ──► QA/TEST ──► PRODUCTION

SAC:    DEV Tenant ──► QA Tenant ──► PROD Tenant
S/4:    S4D ──────► S4Q ─────► S4P
BW4:    BWD ──────► BWQ ─────► BWP
DS:     DS DEV ───► DS TEST ──► DS PROD

Transporte: SAC Content Network para modelos y stories
            SAP Transport para objetos BW/S4
            Datasphere: Packages (export/import)
```

### Recomendaciones de Modeling en SAC Planning

```
ESTRUCTURA DEL MODELO SAC PLANNING:

1. Dimensiones Privadas vs Públicas
   - Usar dimensiones PUBLICAS para master data compartido
   - Dimensiones privadas solo para datos exclusivos del modelo

2. Granularidad
   - Definir nivel más bajo de planning (Cost Center, mes)
   - Agregar niveles para rollup automático

3. Versiones
   - Actual (desde fuente, read-only)
   - Budget (plan oficial, locked post-aprobación)
   - Forecast (rolling, actualizable)
   - Simulation (sandbox para escenarios)

4. Calendarios
   - Alinear con fiscal year variant de S/4HANA / ECC
   - Considerar Week/Period según proceso de negocio
```

---

*Documento generado con base en SAP Best Practices para SAC Planning 2025/2026*
*Referencia: SAP Help Portal - SAC Planning Documentation*
*Aplica a: SAC 2024.x y superior*
