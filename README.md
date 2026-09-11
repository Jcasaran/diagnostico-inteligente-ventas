# Diagnóstico Inteligente de Ventas

Proyecto de Data Analytics orientado a PYMES y startups B2B que necesitan entender qué está ocurriendo en su pipeline comercial sin comprar una plataforma compleja.

## Problema de negocio

Muchas empresas exportan información de su CRM a Excel o CSV, pero no pueden responder con claridad:

- ¿En qué etapa se están perdiendo más oportunidades?
- ¿Qué negocios llevan demasiado tiempo sin avanzar?
- ¿Qué ejecutivos convierten mejor?
- ¿Cuánto pipeline ponderado existe para los próximos meses?
- ¿Cuáles son los principales motivos de pérdida?

Este proyecto convierte una exportación de CRM en un diagnóstico accionable.

## Qué entrega

- Indicadores de pipeline, tasa de cierre, ticket promedio y ciclo comercial.
- Embudo por etapa y conversión entre etapas.
- Ranking comercial con contexto, no solo volumen vendido.
- Identificación de oportunidades estancadas.
- Forecast ponderado por mes.
- Análisis de motivos de pérdida.
- Recomendaciones automáticas basadas en reglas transparentes.
- Dashboard interactivo en Streamlit.

## Personalización desde el dashboard

La aplicación permite trabajar sin editar el código:

- Agregar ejecutivos al equipo comercial.
- Elegir países desde un catálogo de Latinoamérica y agregar nuevos mercados.
- Registrar oportunidades con monto, etapa, industria, origen y fechas.
- Filtrar los indicadores por ejecutivo y país.
- Descargar el CSV actualizado para conservar los cambios de la sesión.

## Vista rápida

Para usar el proyecto con los datos de demostración:

```bash
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate
pip install -r requirements.txt
python src/generate_sample_data.py
python src/analyze_sales.py
streamlit run app.py
```

El dashboard también permite cargar otro CSV con el mismo esquema.

## Datos

Los datos incluidos son **completamente simulados**. Representan oportunidades B2B de tecnología en México y otros mercados de Latinoamérica. No contienen información de clientes reales.

| Campo | Descripción |
|---|---|
| `opportunity_id` | Identificador único |
| `created_date` | Fecha de creación |
| `expected_close_date` | Fecha esperada de cierre |
| `close_date` | Fecha real de cierre, cuando aplica |
| `stage` | Etapa actual o final |
| `amount_usd` | Valor estimado en USD |
| `sales_rep` | Ejecutivo responsable |
| `industry` | Sector del prospecto |
| `country` | País |
| `lead_source` | Fuente de la oportunidad |
| `last_activity_date` | Última interacción registrada |
| `loss_reason` | Motivo de pérdida |

## Reglas del diagnóstico

- Una oportunidad abierta se considera **estancada** cuando supera 30 días sin actividad.
- El forecast ponderado usa probabilidades explícitas por etapa.
- La tasa de cierre se calcula sobre oportunidades terminadas: ganadas / (ganadas + perdidas).
- El ciclo comercial se calcula únicamente con oportunidades ganadas.

Estas reglas son configurables para adaptarlas al proceso de cada empresa.

## Estructura

```text
.
├── app.py
├── data/
│   └── crm_opportunities.csv
├── outputs/
│   ├── executive_summary.md
│   └── kpis.json
├── src/
│   ├── analyze_sales.py
│   ├── generate_sample_data.py
│   └── sales_diagnostics.py
└── tests/
    └── test_sales_diagnostics.py
```

## Valor comercial

Este repositorio funciona como demostración de un servicio que puede entregarse en tres niveles:

1. **Diagnóstico inicial:** limpieza del archivo, KPIs, embudo y recomendaciones.
2. **Dashboard recurrente:** actualización semanal o mensual con la exportación del CRM.
3. **Analítica avanzada:** scoring de oportunidades, forecast y alertas de riesgo.

## Autor

**Javier Casaran** — experiencia comercial B2B y formación en Data Analytics.

[LinkedIn](https://www.linkedin.com/in/javier-casaran-hurtado-372380204)
