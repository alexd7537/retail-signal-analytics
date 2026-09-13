"""Genera el proyecto Power BI editable con modelo estrella y cuatro páginas.
Ejecutar después de analyze.py. Volver a ejecutar si cambia la ubicación del proyecto.
"""
from pathlib import Path
import csv,json,uuid
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'powerbi'
DATA=ROOT/'data/processed'
SCHEMA='https://developer.microsoft.com/json-schemas/fabric/item/'
def write(p,x):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
money='£#,##0.00;(£#,##0.00)'
measures=[
 ('Ventas brutas','CALCULATE(SUM(FactTransactions[AmountGBP]), KEEPFILTERS(FactTransactions[TransactionType] = "Venta"))',money),
 ('Abonos','-CALCULATE(SUM(FactTransactions[AmountGBP]), KEEPFILTERS(FactTransactions[TransactionType] = "Abono"))',money),
 ('Ventas netas','[Ventas brutas] - [Abonos]',money),
 ('Pedidos','CALCULATE(DISTINCTCOUNT(FactTransactions[InvoiceNo]), KEEPFILTERS(FactTransactions[TransactionType] = "Venta"))','#,##0'),
 ('Documentos de abono','CALCULATE(DISTINCTCOUNT(FactTransactions[InvoiceNo]), KEEPFILTERS(FactTransactions[TransactionType] = "Abono"))','#,##0'),
 ('Ticket bruto','DIVIDE([Ventas brutas], [Pedidos])',money),
 ('Abonos sobre bruto','DIVIDE([Abonos], [Ventas brutas])','0.0%'),
 ('Unidades vendidas','CALCULATE(SUM(FactTransactions[Quantity]), KEEPFILTERS(FactTransactions[TransactionType] = "Venta"))','#,##0'),
 ('Unidades abonadas','-CALCULATE(SUM(FactTransactions[Quantity]), KEEPFILTERS(FactTransactions[TransactionType] = "Abono"))','#,##0'),
 ('Clientes compradores','CALCULATE(DISTINCTCOUNT(FactTransactions[CustomerID]), KEEPFILTERS(FactTransactions[TransactionType] = "Venta"), KEEPFILTERS(FactTransactions[CustomerID] <> "UNKNOWN"))','#,##0'),
 ('Clientes recurrentes','COUNTROWS(FILTER(VALUES(FactTransactions[CustomerID]), FactTransactions[CustomerID] <> "UNKNOWN" && CALCULATE([Pedidos]) >= 2))','#,##0'),
 ('Recurrencia','DIVIDE([Clientes recurrentes], [Clientes compradores])','0.0%'),
 ('Cobertura de cliente','DIVIDE(CALCULATE([Ventas brutas], KEEPFILTERS(FactTransactions[CustomerID] <> "UNKNOWN")), [Ventas brutas])','0.0%'),
 ('Filas incluidas','COUNTROWS(FactTransactions)','#,##0'),
 ('Posibles duplicados','SUM(FactTransactions[DuplicateCandidate])','#,##0'),
 ('Neto sin duplicados','CALCULATE([Ventas netas], KEEPFILTERS(FactTransactions[DuplicateCandidate] = 0))',money),
 ('Impacto duplicados','[Ventas netas] - [Neto sin duplicados]',money),
 ('Variacion mensual comparable','IF(HASONEVALUE(DimDate[YearMonth]) && MIN(DimDate[CompleteMonth]) = 1, VAR Prev = CALCULATE([Ventas netas], REMOVEFILTERS(DimDate), DATEADD(DimDate[Date], -1, MONTH)) RETURN IF(Prev > 0, DIVIDE([Ventas netas] - Prev, Prev)))','0.0%'),
]
types={
 'FactTransactions':{'SourceRow':'int64','InvoiceNo':'string','StockCode':'string','CustomerID':'string','Country':'string','Date':'dateTime','Quantity':'int64','UnitPrice':'decimal','AmountGBP':'decimal','AmountMilliGBP':'int64','TransactionType':'string','DuplicateCandidate':'int64'},
 'DimProduct':{'StockCode':'string','Description':'string'},'DimCustomer':{'CustomerID':'string'},'DimCountry':{'Country':'string'},
 'DimDate':{'Date':'dateTime','YearMonth':'string','Year':'int64','Month':'int64','Weekday':'int64','CompleteMonth':'int64'},
 'Quality':{'RecordClass':'string','TransactionType':'string','Rows':'int64','AmountGBP':'decimal','Included':'int64'}
}
mt={'int64':'Int64.Type','string':'type text','dateTime':'type date','decimal':'Currency.Type'}
tables=[]
for name,cols in types.items():
    filename='reconciliation.csv' if name=='Quality' else name+'.csv'
    pairs=', '.join('{"'+k+'", '+mt[v]+'}' for k,v in cols.items())
    expr=['let',f'    Source = Csv.Document(File.Contents(DataFolder & "/{filename}"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),',
          '    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),',f'    Typed = Table.TransformColumnTypes(Headers, {{{pairs}}}, "en-US")','in','    Typed']
    columns=[]
    for col,typ in cols.items():
        c={'name':col,'dataType':typ,'sourceColumn':col,'summarizeBy':'none','lineageTag':str(uuid.uuid5(uuid.NAMESPACE_URL,name+'.'+col))}
        if typ=='dateTime':c['formatString']='dd/MM/yyyy'
        if typ=='decimal':c['formatString']=money
        if name=='FactTransactions' and col in ['SourceRow','AmountMilliGBP']:c['isHidden']=True
        columns.append(c)
    t={'name':name,'lineageTag':str(uuid.uuid5(uuid.NAMESPACE_URL,name)),'columns':columns,'partitions':[{'name':name,'mode':'import','source':{'type':'m','expression':expr}}]}
    if name=='FactTransactions':t['measures']=[{'name':n,'expression':e,'formatString':fmt,'displayFolder':'Ventas','description':'Productos. Documentos de abono registrados en su fecha. Ver metodologia.md.'} for n,e,fmt in measures]
    if name=='Quality':t['measures']=[{'name':'Filas fuente','expression':'SUM(Quality[Rows])','formatString':'#,##0'},
      {'name':'Importe fuente','expression':'SUM(Quality[AmountGBP])','formatString':money},
      {'name':'Importe excluido','expression':'CALCULATE(SUM(Quality[AmountGBP]), Quality[Included] = 0)','formatString':money}]
    tables.append(t)
relationships=[{'name':str(uuid.uuid5(uuid.NAMESPACE_URL,'relationship'+dim)),'fromTable':'FactTransactions','fromColumn':col,'toTable':dim,'toColumn':col,'crossFilteringBehavior':'oneDirection','fromCardinality':'many','toCardinality':'one'} for dim,col in [('DimProduct','StockCode'),('DimCustomer','CustomerID'),('DimCountry','Country'),('DimDate','Date')]]
model={'name':'OnlineRetail','compatibilityLevel':1567,'model':{'culture':'en-US','defaultPowerBIDataSourceVersion':'powerBI_V3','sourceQueryCulture':'en-US','tables':tables,'relationships':relationships,
 'expressions':[{'name':'DataFolder','kind':'m','expression':f'"{DATA.as_posix()}" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]'}],
 'annotations':[{'name':'PBI_QueryOrder','value':json.dumps(['DataFolder']+list(types))}]}}
write(OUT/'OnlineRetail.SemanticModel/model.bim',model)
write(OUT/'OnlineRetail.SemanticModel/definition.pbism',{'$schema':SCHEMA+'semanticModel/definitionProperties/1.0.0/schema.json','version':'1.0','settings':{'qnaEnabled':False}})
write(OUT/'OnlineRetail.pbip',{'$schema':'https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json','version':'1.0','artifacts':[{'report':{'path':'OnlineRetail.Report'}}],'settings':{'enableAutoRecovery':True}})
write(OUT/'OnlineRetail.Report/definition.pbir',{'$schema':SCHEMA+'report/definitionProperties/2.0.0/schema.json','version':'4.0','datasetReference':{'byPath':{'path':'../OnlineRetail.SemanticModel'}}})
from design_powerbi import build_design
build_design(ROOT, model, types)
(OUT/'Medidas.dax').write_text('\n\n'.join(n+' =\n'+e for n,e,_ in measures),encoding='utf-8')
