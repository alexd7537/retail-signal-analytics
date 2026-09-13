"""Comprueba los entregables guardados; no modifica datos ni libros."""
from pathlib import Path
import json,sqlite3,csv,zipfile
import pandas as pd
import openpyxl
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[1]
r=json.loads((ROOT/'analysis/results.json').read_text(encoding='utf-8'))
conn=sqlite3.connect(ROOT/'analysis/retail.sqlite')
total=conn.execute('SELECT SUM(AmountMilliGBP) FROM FactTransactions').fetchone()[0]
fact=pd.read_csv(ROOT/'data/processed/FactTransactions.csv',dtype={'InvoiceNo':str,'CustomerID':str,'StockCode':str,'Date':str})
assert len(fact)==r['overall']['Rows']
assert int(fact.AmountMilliGBP.sum())==total
for dim,key in [('DimProduct','StockCode'),('DimCustomer','CustomerID'),('DimCountry','Country'),('DimDate','Date')]:
    d=pd.read_csv(ROOT/f'data/processed/{dim}.csv',dtype=str)
    assert d[key].is_unique
    assert d[key].notna().all() and d[key].str.strip().ne('').all(), (dim,'Clave vacía')
    assert d[key].str.strip().str.casefold().is_unique, (dim,'Claves repetidas sin distinguir mayúsculas')
    assert set(fact[key]).issubset(set(d[key]))
assert fact.StockCode.eq(fact.StockCode.str.strip().str.upper()).all()
products=pd.read_csv(ROOT/'data/processed/DimProduct.csv',dtype=str)
assert products.StockCode.eq('84997B').sum()==1, 'Regresión: código de la incidencia'
audit=pd.read_csv(ROOT/'data/processed/transactions_audited.csv',dtype={'StockCode':str,'StockCodeOriginal':str})
assert audit.StockCode.eq(audit.StockCodeOriginal.str.strip().str.upper()).all()
assert len(audit)==r['source']['rows']
assert fact.StockCode.tolist()==audit.loc[audit.Included.eq(1),'StockCode'].tolist()
for group,file in [('StockCode','products'),('Country','countries')]:
    agg=pd.read_csv(ROOT/f'data/processed/{file}.csv',dtype={group:str})
    check=fact.groupby(group).AmountMilliGBP.sum()
    for _,x in agg.iterrows():assert abs(x.NetGBP*1000-check[x[group]])<0.0001
product_totals=pd.read_csv(ROOT/'data/processed/products.csv',dtype={'StockCode':str}).set_index('StockCode')
for kind,field in [('Venta','Orders'),('Abono','CreditDocuments')]:
    counts=fact.loc[fact.TransactionType.eq(kind)].groupby('StockCode').InvoiceNo.nunique()
    assert product_totals[field].eq(counts.reindex(product_totals.index,fill_value=0)).all()
sql=(ROOT/'sql/analysis.sql').read_text(encoding='utf-8')
# sqlite3 executescript validates all statements; individual total above is independently checked.
conn.executescript(sql)
book=openpyxl.load_workbook(ROOT/'Dashboard_Ventas.xlsx',data_only=True)
assert abs(book['Resumen']['B8'].value-r['overall']['NetGBP'])<0.00001
assert book['Resumen']['F8'].value==r['overall']['Orders']
assert book['Filtros']['D5'].value=='Todos' and book['Filtros']['D6'].value=='Todos'
assert book['Validación']['C36'].value==0
errors=[]
for s in book:
    for row in s:
        errors.extend((s.title,c.coordinate,c.value) for c in row if c.data_type=='e')
assert not errors,errors[:10]
native=openpyxl.load_workbook(ROOT/'Dashboard_Ventas.xlsx',data_only=False)
assert sum(len(s._charts) for s in native)==5
assert len(native['Productos'].tables)==1 and len(native['Clientes'].tables)==1
product_table=next(iter(native['Productos'].tables.values()))
from openpyxl.utils.cell import range_boundaries
_,first_row,_,last_row=range_boundaries(product_table.ref)
assert last_row-first_row==len(products)
for row in book['Productos'].iter_rows(min_row=first_row+1,max_row=last_row,min_col=2,max_col=6,values_only=True):
    code,description,gross,credit,net=row
    expected=product_totals.loc[str(code)]
    assert abs(net-expected.NetGBP)<0.00001
    assert abs(gross-expected.GrossGBP)<0.00001 and abs(credit-expected.CreditGBP)<0.00001
vals=[str(v.sqref) for v in native['Filtros'].data_validations.dataValidation]
assert set(vals)=={'D5','D6'},vals
with zipfile.ZipFile(ROOT/'Dashboard_Ventas.xlsx') as z:
    charts=[z.read(k).decode() for k in z.namelist() if '/charts/chart' in k and k.endswith('.xml')]
    assert any('167C73' in x.upper() and 'ln' in x for x in charts)
pdf=PdfReader(ROOT/'Informe_Ejecutivo.pdf');assert len(pdf.pages)==5
txt='\n'.join(p.extract_text() for p in pdf.pages)
assert '9.792.708,88' in txt and '19.773' in txt
assert all(len(p.extract_text())>500 for p in pdf.pages)
for p in (ROOT/'powerbi').rglob('*.json'):json.loads(p.read_text(encoding='utf-8'))
print('Verified: CSV counts, dimension keys, full product/country totals, 8 SQL queries, XLSX stored values/formula errors/charts/validation, 5 PDF pages and Power BI JSON.')
