"""Presentación pública del caso; métricas tomadas del análisis, no inventadas."""
from pathlib import Path
import json

def build_readme(root):
    r=json.loads((root/'analysis/results.json').read_text(encoding='utf-8'))
    def number(v,d=0):return f'{v:,.{d}f}'.replace(',','X').replace('.',',').replace('X','.')
    o=r['overall']
    readme=f'''# RETAIL / SIGNAL

### De registros de venta a decisiones comerciales.

![RETAIL / SIGNAL: caso de análisis comercial de Online Retail](images/portada.png)

Un proyecto de análisis de datos de principio a fin: **Python · SQL · Power BI · Excel**.
Datos públicos de Online Retail, una tienda minorista online. Periodo: diciembre de 2010 a diciembre de 2011; importes en GBP.

Este es un caso de portafolio, no un encargo real de la empresa. RETAIL / SIGNAL es la identidad visual del proyecto.

## La pregunta

¿Cuánto vende realmente el negocio, qué productos y clientes explican sus resultados y qué registros requieren revisión?

El archivo mezcla ventas, abonos, portes y ajustes. Antes de diseñar el dashboard, hay que decidir qué entra en cada indicador y poder justificarlo. La unidad de análisis es una línea de documento, no un pedido.

## En una mirada

| Ventas netas de productos | Pedidos distintos | Compradores identificados |
|---:|---:|---:|
| £{number(o['NetGBP'],2)} | {number(o['Orders'])} | {number(o['Customers'])} |

**{number(r['source']['rows'])} filas de origen → {number(o['Rows'])} líneas comerciales → {number(len(r['products']))} productos únicos.**

El neto comercial excluye portes, ajustes, vales y registros en revisión. No representa beneficio ni ingreso contable total.

## Qué permite explorar

| Vista de Power BI | Para qué sirve |
|---|---|
| 01 · Panorama | Ventas, pedidos, ticket y abonos; evolución mensual y cinco mercados líderes. |
| 02 · Productos | Diez productos líderes, principales abonos y detalle por código. |
| 03 · Clientes | Compradores, recurrencia, cobertura de identificación y detalle por cliente. |
| 04 · Calidad | Conciliación global y sensibilidad a posibles duplicados. |

El informe tiene navegación lateral, filtros desplegables y un tema integrado. Las tarjetas y rankings responden a los filtros de su página. La vista de calidad conserva el alcance global.

### Vista del Excel

![Vista renderizada del dashboard Excel](images/Resumen.png)

*Imagen renderizada del archivo Excel, no captura de Power BI. La portada es una composición editorial con las métricas calculadas del proyecto.*

## Tres hallazgos para conversar con un cliente

1. **La demanda se concentra al final del año.** Noviembre de 2011 alcanzó £1.432.734,99 netos, 34,8% más que octubre. Es un solo ciclo: describe lo observado, no demuestra estacionalidad recurrente.
2. **Reino Unido concentra el negocio.** Aporta el 84,8% del neto. Países Bajos lidera los mercados exteriores, con pocos compradores identificados.
3. **Los abonos necesitan contexto.** Dos pares extremos de venta y abono suman £245.653,20 en cada sentido, el 51,3% del valor abonado. No hay una clave que permita afirmar su causa.

El [informe ejecutivo](Informe_Ejecutivo.pdf) conecta estos hallazgos con acciones propuestas, responsables y límites de interpretación.

## Decisiones técnicas que importan

- **Claves consistentes.** StockCode se normaliza a mayúsculas antes de crear hechos y dimensiones. La unicidad se comprueba sin distinguir mayúsculas para evitar colisiones en Power BI. El valor original se conserva en la auditoría.
- **Trazabilidad.** Cada transacción mantiene su fila de origen. No se elimina ninguna venta por compartir código con otra.
- **Duplicados con criterio.** Las 5.268 repeticiones exactas candidatas se conservan; falta un identificador de línea que pruebe que sean errores de carga. La alternativa se presenta por separado.
- **Precisión.** Los importes se concilian en milésimas enteras de GBP, tanto en pandas como en SQLite.
- **Clientes desconocidos.** Sus ventas se incluyen; no se cuentan como compradores identificados.
- **Comparaciones justas.** Diciembre de 2011 tiene solo nueve días y no se compara como mes completo.

Más detalle en [metodología](report/Metodologia.md) y [diccionario de datos](report/Diccionario_Datos.md).

## Cómo está construido

![Flujo de preparación y entrega](images/flujo.svg)

```text
src/          Limpieza, generación y configuración local
sql/          Consultas de análisis sobre SQLite
powerbi/      Modelo estrella, reporte PBIR, DAX y tema visual
report/       Metodología, diccionario y guion de presentación
tests/        Pruebas estructurales del proyecto Power BI
images/       Portada y vistas del Excel
data/         Instrucciones de origen; los CSV completos se generan localmente
analysis/     Resultados y controles; la base completa se genera localmente
```

## Abrir y reproducir

### Explorar la entrega local

1. Abrir **Dashboard_Ventas.xlsx**. Cambiar mes y país en **Filtros**, celdas D5 y D6. La hoja **Resumen** muestra las tarjetas; Productos, Clientes y Países cubren el periodo completo.
2. Leer **Informe_Ejecutivo.pdf** para entender las conclusiones.
3. Abrir **powerbi/OnlineRetail.pbip**. Confirmar `DataFolder` y pulsar **Inicio → Actualizar**. Si aparece la conversión a TMDL, no es necesaria: elegir **No actualizar**. Consultar [la guía de Power BI](powerbi/LEEME.md).

### Reproducir desde el repositorio

El repositorio no incluye los datos completos ni rutas personales. Descargar Online Retail desde [UCI](https://doi.org/10.24432/C5BW33) y conservar el XLSX fuera del repositorio, o en `data/raw/` (ignorado por Git).

```bash
python -m pip install -r requirements.txt
python src/analyze.py --input "RUTA/Online Retail.xlsx"
python src/configure_data.py --folder "RUTA/retail-signal/data/processed"
python -m unittest discover -s tests -v
```

Después, abrir el PBIP y actualizar. `configure_data.py` cambia solo la ruta de los CSV; conserva el diseño y las medidas.

Para reconstruir los artefactos:

```bash
python src/build_report.py
python src/build_powerbi.py
```

**Atención:** `build_powerbi.py` regenera modelo y diseño; no ejecutarlo sobre personalizaciones sin una copia de seguridad. El Excel y la portada se reconstruyen con sus scripts JS, que requieren `@oai/artifact-tool` y `sharp` del entorno de autoría. No dependen de una plantilla privada, pero no se promete su ejecución en un Node sin esas dependencias. El XLSX entregado se puede usar sin ellas.

## Qué está comprobado y qué falta

- Conteos, importes, claves y conciliación Python/SQLite.
- Unicidad de dimensiones e integridad de relaciones.
- Fórmulas y escenarios de filtro del Excel; revisión de todas sus hojas y del PDF.
- Estructura PBIR, campos, navegación, lienzo y registro del tema; validación contra esquemas oficiales de Microsoft.
- **Pendiente:** comprobar carga, DAX, interacciones y apariencia dentro de Power BI Desktop. Las verificaciones de archivos no sustituyen esa revisión nativa. No se entrega una captura de Power BI ni un PBIX validado.

## Repositorio y mantenimiento

Repositorio: [alexd7537/retail-signal-analytics](https://github.com/alexd7537/retail-signal-analytics). La guía [PUBLICAR_EN_GITHUB.md](PUBLICAR_EN_GITHUB.md) explica qué incluye esta copia y cómo mantenerla sin cachés, datos completos ni rutas personales.

## Fuente y alcance

Chen, D. (2015). [Online Retail — UCI Machine Learning Repository](https://doi.org/10.24432/C5BW33). Datos bajo **CC BY 4.0**. Transformaciones: normalización, clasificación, métricas y agregación. No se inventaron costos, margen, causas de abono ni resultados comerciales implementados.

El proyecto se desarrolló con asistencia de IA. Las decisiones y limitaciones están documentadas para poder revisarlas y explicarlas.

SHA-256 del XLSX de origen: `{r['source']['sha256']}`.
'''
    (root/'README.md').write_text(readme,encoding='utf-8')
if __name__=='__main__':build_readme(Path(__file__).resolve().parents[1])
