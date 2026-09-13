"""Crea informe de cinco páginas y documentación a partir de resultados verificados."""
from pathlib import Path
import json,html
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib import colors
from reportlab.platypus import Paragraph,Table,TableStyle
from reportlab.lib.styles import ParagraphStyle
ROOT=Path(__file__).resolve().parents[1]
r=json.loads((ROOT/'analysis/results.json').read_text(encoding='utf-8'))
o=r['overall'];gross=o['GrossGBP'];net=o['NetGBP'];credits=o['CreditGBP']
def n(v,d=0):return f'{v:,.{d}f}'.replace(',','X').replace('.',',').replace('X','.')
def gbp(v):return '£'+n(v,2)
def pc(v):return n(v*100,1)+'%'
uk=r['countries'][0]['NetGBP']/net
top10p=sum(x['NetGBP'] for x in r['products'][:10])/net
knownnet=sum(x['NetGBP'] for x in r['customers'])
top10c=sum(x['NetGBP'] for x in r['customers'][:10])/knownnet
nov=next(x for x in r['monthly'] if x['YearMonth']=='2011-11');octo=next(x for x in r['monthly'] if x['YearMonth']=='2011-10')
pair=sum(x['AmountGBP'] for x in r['large_transactions'] if x['AmountGBP']>0)
nd=r['no_duplicates'];diff=net-nd['NetGBP']
W,H=842,595;navy=colors.HexColor('#153C3C');blue=colors.HexColor('#167C73');pale=colors.HexColor('#E9F2ED');gray=colors.HexColor('#657674');amber=colors.HexColor('#D76B50')
c=Canvas(str(ROOT/'Informe_Ejecutivo.pdf'),pagesize=(W,H));c.setTitle('Online Retail - Informe ejecutivo de ventas');c.setAuthor('Proyecto de portafolio')
def text(t,x,y,width=740,size=11,color=navy,bold=False):
    style=ParagraphStyle('p',fontName='Helvetica-Bold' if bold else 'Helvetica',fontSize=size,leading=size*1.45,textColor=color)
    p=Paragraph(t,style);_,h=p.wrap(width,1000);p.drawOn(c,x,y-h);return h
def page(num,title,kicker):
    c.setFillColor(colors.HexColor('#F5F3ED'));c.rect(0,0,W,H,fill=1,stroke=0)
    text('RETAIL / SIGNAL',36,H-23,600,10,blue,True)
    text('ONLINE RETAIL  /  INFORME COMERCIAL',559,H-24,265,8,gray)
    text(title,36,H-52,770,25,navy,True)
    c.setStrokeColor(amber);c.setLineWidth(2);c.line(36,H-100,78,H-100)
    text(kicker,36,H-113,770,10,gray)
    c.setStrokeColor(pale);c.line(36,34,W-36,34)
    text('Datos: Online Retail, UCI. 01/12/2010 - 09/12/2011. GBP. Caso de portafolio.',36,27,720,8,gray)
    c.setFillColor(gray);c.setFont('Helvetica',9);c.drawRightString(W-36,17,f'{num} / 5')
def table(rows,x,y,widths):
    ps=ParagraphStyle('t',fontName='Helvetica',fontSize=9,leading=13,textColor=navy)
    data=[[Paragraph(html.escape(str(z)),ps) for z in row] for row in rows]
    t=Table(data,colWidths=widths,hAlign='LEFT');t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),pale),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),('LINEBELOW',(0,0),(-1,0),1,navy),('LINEBELOW',(0,1),(-1,-1),0.4,pale)]))
    _,h=t.wrap(sum(widths),1000);t.drawOn(c,x,y-h);return h
def bars(items,x,y,w,h,formatter=gbp,labelwidth=158):
    maxv=max(v for _,v in items)*1.05;row=h/len(items);barw=w-labelwidth-95
    for i,(label,v) in enumerate(items):
        yy=y-i*row
        text(html.escape(label),x,yy,labelwidth-8,9)
        c.setFillColor(blue);c.rect(x+labelwidth,yy-13,barw*v/maxv,13,fill=1,stroke=0)
        text(formatter(v),x+labelwidth+barw+8,yy,95,9)
page(1,'El negocio en una mirada','Ventas de productos por £9,79 millones. La lectura separa portes, ajustes y abonos.')
for i,(lab,val) in enumerate([('Ventas netas',gbp(net)),('Pedidos',n(o['Orders'])),('Ticket bruto',gbp(gross/o['Orders'])),('Abonos / bruto',pc(credits/gross))]):
    x=36+i*194;c.setFillColor(navy if i==0 else colors.white);c.roundRect(x,342,184,86,9,fill=1,stroke=0)
    text(lab,x+14,416,158,10,colors.white if i==0 else gray)
    text(val,x+14,391,158,19,colors.white if i==0 else amber if i==3 else navy,True)
text('Tres decisiones que el análisis ayuda a tomar',36,314,770,15,navy,True)
text(f'<b>Preparar el periodo de mayor demanda.</b> Noviembre de 2011 alcanzó {gbp(nov["NetGBP"])}, un {pc(nov["NetGBP"]/octo["NetGBP"]-1)} por encima de octubre. Este único ciclo no prueba un patrón estacional recurrente.',36,282,770,11)
text(f'<b>Revisar los abonos antes de actuar.</b> Dos pares extremos de venta y abono del mismo día suman {gbp(pair)} en cada sentido y explican {pc(pair/credits)} del valor abonado.',36,213,770,11)
text(f'<b>Mejorar la identificación del comprador.</b> {pc(1-o["KnownGrossGBP"]/gross)} de las ventas brutas carece de cliente identificado. Esto limita el análisis de recurrencia y campañas.',36,151,770,11)
c.showPage()
page(2,'Evolución de ventas y mercados','Todos los resultados comerciales de este informe corresponden únicamente a productos.')
# Vector time chart with separate incomplete observation.
x0,y0,cw,ch=68,238,410,174;mx=1600000
c.setStrokeColor(pale);c.setFillColor(gray);c.setFont('Helvetica',8)
for tick in [0,500000,1000000,1500000]:
    y=y0+ch*tick/mx;c.line(x0,y,x0+cw,y);c.drawRightString(x0-8,y-3,'£'+n(tick/1e6,1)+' M')
pts=[(x0+i*cw/12,y0+ch*x['NetGBP']/mx) for i,x in enumerate(r['monthly'])]
c.setLineWidth(2);c.setStrokeColor(blue)
for a,b in zip(pts[:11],pts[1:12]):c.line(*a,*b)
c.setStrokeColor(amber);c.setDash(4,3);c.line(*pts[11],*pts[12]);c.setDash()
for i,(x,y) in enumerate(pts):
    c.setFillColor(amber if i==12 else blue);c.circle(x,y,2.5,fill=1,stroke=0)
    if i%2==0:c.setFillColor(gray);c.setFont('Helvetica',7);c.drawCentredString(x,y0-17,r['monthly'][i]['YearMonth'])
text('Línea discontinua: diciembre 2011, solo días 1 al 9.',56,207,438,9,amber)
text('Mercados principales (neto)',520,434,280,12,navy,True)
table([['País','Ventas netas']]+[[z['Country'],gbp(z['NetGBP'])] for z in r['countries'][:5]],520,409,[150,125])
text(f'Reino Unido concentra <b>{pc(uk)}</b> del neto. Países Bajos lidera el exterior con {gbp(r["countries"][1]["NetGBP"])} y solo {r["countries"][1]["Customers"]} compradores identificados.',36,174,770,11)
text('Acción propuesta: planificar inventario para la demanda observada y revisar la dependencia de compradores mayoristas antes de ampliar mercados. Se necesitan datos de stock, margen y costos de envío para decidir una inversión.',36,111,770,10)
c.showPage()
page(3,'Productos y concentración de clientes','Los rankings se basan en ventas netas del periodo completo.')
text('Cinco productos con mayor venta neta',36,440,480,13,navy,True)
bars([(z['StockCode']+' '+z['Description'],z['NetGBP']) for z in r['products'][:5]],36,409,760,155,labelwidth=315)
text(f'Los diez primeros productos representan <b>{pc(top10p)}</b> del neto. El código 22423 lidera con {gbp(r["products"][0]["NetGBP"])}.',36,236,770,11)
table([['Indicador de clientes','Resultado','Interpretación'],['Compradores identificados',n(o['Customers']),'Clientes con al menos una factura positiva'],['Compradores recurrentes',f'{n(o["RepeatCustomers"])} ({pc(o["RepeatCustomers"]/o["Customers"])})','Dos o más facturas positivas en la ventana observada'],['Top 10 clientes',pc(top10c)+' del neto identificado','El denominador excluye ventas sin CustomerID']],36,191,[235,195,340])
text('Acción propuesta: revisar disponibilidad de productos líderes y diseñar un seguimiento de los principales compradores. La recurrencia observada no equivale a retención ni a valor de vida del cliente.',36,76,770,9)
c.showPage()
page(4,'Calidad de datos y límites del análisis','Las filas originales se conservan y cada transacción mantiene su número de fila de origen.')
table([['Control','Resultado','Tratamiento'],['Archivo original',n(r['source']['rows'])+' filas','No modificado'],['Productos elegibles',n(o['Rows'])+' filas','Precio positivo; venta numérica o abono C con signo válido'],['Fuera del alcance','5.444 filas','Portes, ajustes, vales y registros que requieren revisión'],['Posibles duplicados exactos','5.268 filas posteriores','Conservados; se ofrece una alternativa sin repeticiones'],['Cliente sin identificar','135.080 filas fuente','Se conserva para ventas; no se cuenta como comprador'],['Diciembre de 2011','Del 1 al 9','No se calcula crecimiento contra un mes completo']],36,435,[215,150,405])
text('Conciliación de importes firmados',36,204,770,13,navy,True)
text(f'{gbp(net)} en productos + ({gbp(r["excluded_total"])}) fuera del alcance = {gbp(r["source"]["signed_total"])} en la fuente. La comprobación exacta utiliza milésimas de GBP.',36,177,770,10)
text(f'Eliminar las repeticiones exactas reduciría el neto en <b>{gbp(diff)}</b> ({pc(diff/net)}). Se necesita confirmación del sistema de origen para decidir si son errores.',36,128,770,10)
text('Los abonos no incluyen causa ni vínculo verificable con el pedido original. No hay costos para calcular utilidad o margen. No se atribuye una mejora comercial a este proyecto.',36,80,770,9)
c.showPage()
page(5,'Plan de acción y entrega al cliente','Las acciones son propuestas para validación; no se presentan como mejoras ya obtenidas.')
table([['Prioridad','Acción propuesta','Responsable sugerido','Cómo medir'],['1','Investigar los dos pares extremos y registrar motivos de abono','Administración / operaciones','Abonos con causa documentada; correcciones identificadas'],['2','Mejorar la captura de CustomerID en las ventas','Comercial / sistemas','Porcentaje de bruto con cliente identificado'],['3','Revisar disponibilidad de los productos líderes','Compras / inventario','Quiebres de stock y ventas no atendidas; requiere inventario'],['4','Revisar dependencia de grandes compradores por mercado','Dirección comercial','Participación de los 10 principales compradores'],['5','Resolver la política de duplicados con el propietario del sistema','Sistemas / analista','Regla aprobada y conciliación de la nueva extracción']],36,435,[65,330,160,215])
text('Entregables',36,206,770,13,navy,True)
text('Dashboard Excel con filtros, proyecto Power BI editable, CSV completos, SQL, código de procesamiento, pruebas y guía para presentar el caso. Power BI requiere abrir el proyecto y actualizar los datos en Desktop; esa ejecución nativa no se verificó en este entorno.',36,178,770,10)
text('Fuente y atribución',36,116,770,12,navy,True)
text('Chen, D. (2015). Online Retail. UCI Machine Learning Repository. DOI: 10.24432/C5BW33. Datos bajo CC BY 4.0. Modificaciones: normalización, clasificación, métricas y agregados. El archivo original lo proporcionó el usuario.',36,92,770,9)
c.save()

from build_readme import build_readme
build_readme(ROOT)
print('RETAIL / SIGNAL: PDF and README generated')
