"""Análisis reproducible de Online Retail. No modifica el archivo de origen.
Ejemplo: python src/analyze.py --input "C:/ruta/Online Retail.xlsx"
"""
from pathlib import Path
import argparse, hashlib, json, sqlite3
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ADMIN = {'M','D','S','BANK CHARGES','AMAZONFEE','CRUK','B'}
SHIPPING = {'POST','DOT','C2'}
def save_json(p, value):
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str), encoding='utf-8')
def records(df):
    return json.loads(df.to_json(orient='records', date_format='iso'))
def run(path, cache=None):
    for folder in ['data/processed','analysis','report','images','powerbi','sql']:
        (ROOT/folder).mkdir(parents=True, exist_ok=True)
    raw = pd.read_pickle(cache) if cache else pd.read_excel(path)
    required=['InvoiceNo','StockCode','Description','Quantity','InvoiceDate','UnitPrice','CustomerID','Country']
    assert raw.columns.tolist() == required, 'El esquema del archivo cambió.'
    d=raw.copy()
    d['SourceRow']=np.arange(2,len(d)+2)
    d['DuplicateCandidate']=raw.duplicated(keep='first').astype(int)
    d['MissingDescription']=d.Description.isna().astype(int)
    # Auditoría antes de normalizar; no altera la detección de filas idénticas.
    d['StockCodeOriginal']=raw.StockCode.astype(str)
    for col in ['InvoiceNo','StockCode','Country']:
        d[col]=d[col].astype(str).str.strip()
    # Power BI no distingue mayúsculas en sus claves. Aplicar la misma clave
    # a hechos y dimensiones ANTES de agrupar, sin eliminar transacciones.
    d['StockCode']=d.StockCode.str.upper()
    d['Description']=d.Description.fillna('SIN DESCRIPCIÓN').str.strip().str.replace(r'\s+',' ',regex=True)
    d['CustomerID']=d.CustomerID.apply(lambda x: str(int(x)) if pd.notna(x) else 'UNKNOWN')
    d['KnownCustomer']=(d.CustomerID!='UNKNOWN').astype(int)
    code=d.StockCode
    d['RecordClass']=np.select([code.isin(SHIPPING),code.isin(ADMIN),code.str.startswith('GIFT_')],['Envio','Ajuste','Vale'],default='Producto')
    d['TransactionType']=np.select([
        (d.UnitPrice>0)&(d.Quantity>0)&d.InvoiceNo.str.match(r'^\d+$'),
        (d.UnitPrice>0)&(d.Quantity<0)&d.InvoiceNo.str.upper().str.startswith('C')],['Venta','Abono'],default='Revision')
    # Milésimas de GBP: preserva precios como 0.001 y permite conciliación exacta.
    scaled=d.UnitPrice*1000
    assert np.allclose(scaled,scaled.round(),rtol=0,atol=0.000001), 'Más de tres decimales en el precio.'
    d['AmountMilliGBP']=scaled.round().astype('int64')*d.Quantity
    d['AmountGBP']=d.AmountMilliGBP/1000
    d['Date']=d.InvoiceDate.dt.strftime('%Y-%m-%d')
    d['YearMonth']=d.InvoiceDate.dt.strftime('%Y-%m')
    d['Hour']=d.InvoiceDate.dt.hour
    d['Weekday']=d.InvoiceDate.dt.dayofweek
    d['Included']=((d.RecordClass=='Producto')&d.TransactionType.isin(['Venta','Abono'])).astype(int)
    f=d[d.Included==1].copy()
    f['GrossMilli']=f.AmountMilliGBP.clip(lower=0)
    f['CreditMilli']=(-f.AmountMilliGBP).clip(lower=0)
    f['SoldUnits']=f.Quantity.clip(lower=0)
    f['CreditUnits']=(-f.Quantity).clip(lower=0)
    sales=f[f.TransactionType=='Venta']
    credits=f[f.TransactionType=='Abono']
    def metrics(x):
        s=x[x.TransactionType=='Venta']; c=x[x.TransactionType=='Abono']
        known=s[s.CustomerID!='UNKNOWN']
        freq=known.groupby('CustomerID').InvoiceNo.nunique()
        gross=int(x.GrossMilli.sum()); credit=int(x.CreditMilli.sum())
        return dict(GrossGBP=gross/1000,CreditGBP=credit/1000,NetGBP=(gross-credit)/1000,
                    Orders=int(s.InvoiceNo.nunique()),CreditDocuments=int(c.InvoiceNo.nunique()),
                    Customers=int(known.CustomerID.nunique()),RepeatCustomers=int((freq>=2).sum()),
                    Units=int(x.SoldUnits.sum()),CreditUnits=int(x.CreditUnits.sum()),
                    KnownGrossGBP=int(known.GrossMilli.sum())/1000,Rows=len(x))
    overall=metrics(f)
    monthly=[]
    for month,x in f.groupby('YearMonth'):
        monthly.append(dict(YearMonth=month,Partial=int(month=='2011-12'),**metrics(x)))
    countries=[]
    for country,x in f.groupby('Country'):
        countries.append(dict(Country=country,**metrics(x)))
    country_df=pd.DataFrame(countries).sort_values('NetGBP',ascending=False)
    # Cubo para selección Excel. Cada total distinto se calcula desde las líneas.
    cube=[]
    for month in ['Todos']+sorted(f.YearMonth.unique().tolist()):
        sub=f if month=='Todos' else f[f.YearMonth==month]
        for country in ['Todos']+sorted(f.Country.unique().tolist()):
            x=sub if country=='Todos' else sub[sub.Country==country]
            cube.append(dict(YearMonth=month,Country=country,**metrics(x)))
    prod=(f.groupby('StockCode').agg(GrossMilli=('GrossMilli','sum'),CreditMilli=('CreditMilli','sum'),
           NetMilli=('AmountMilliGBP','sum'),Units=('SoldUnits','sum'),CreditUnits=('CreditUnits','sum')))
    # Descripción más frecuente, con desempate alfabético; código como clave estable.
    descriptions=(d[d.Description!='SIN DESCRIPCIÓN'].groupby(['StockCode','Description']).size()
        .reset_index(name='n').sort_values(['StockCode','n','Description'],ascending=[True,False,True])
        .drop_duplicates('StockCode').set_index('StockCode').Description)
    prod['Description']=descriptions.reindex(prod.index).fillna('SIN DESCRIPCIÓN')
    prod['Orders']=sales.groupby('StockCode').InvoiceNo.nunique().reindex(prod.index).fillna(0).astype(int)
    prod['CreditDocuments']=credits.groupby('StockCode').InvoiceNo.nunique().reindex(prod.index).fillna(0).astype(int)
    for col in ['Gross','Credit','Net']: prod[col+'GBP']=prod.pop(col+'Milli')/1000
    prod=prod.reset_index().sort_values(['NetGBP','StockCode'],ascending=[False,True])
    cust=f[f.CustomerID!='UNKNOWN'].groupby('CustomerID').agg(
        GrossMilli=('GrossMilli','sum'),CreditMilli=('CreditMilli','sum'),NetMilli=('AmountMilliGBP','sum'))
    cust['Orders']=sales[sales.CustomerID!='UNKNOWN'].groupby('CustomerID').InvoiceNo.nunique().reindex(cust.index).fillna(0).astype(int)
    cust['LastPurchase']=sales.groupby('CustomerID').Date.max().reindex(cust.index)
    cust['Segment']=np.where(cust.Orders>=2,'Recurrente',np.where(cust.Orders==1,'Una compra','Solo abonos'))
    for col in ['Gross','Credit','Net']:cust[col+'GBP']=cust.pop(col+'Milli')/1000
    cust=cust.reset_index().sort_values(['NetGBP','CustomerID'],ascending=[False,True]).fillna('')
    classes=[]
    for (cl,ty),x in d.groupby(['RecordClass','TransactionType']):
        classes.append(dict(RecordClass=cl,TransactionType=ty,Rows=len(x),AmountGBP=int(x.AmountMilliGBP.sum())/1000,Included=int(x.Included.iloc[0])))
    # Controles mutuamente excluyentes; las incidencias de calidad sí pueden solaparse.
    issues=[dict(Check='Filas fuente',Count=len(d)),dict(Check='Filas incluidas: producto con precio positivo y signo válido',Count=len(f)),
      dict(Check='Filas fuera del alcance',Count=len(d)-len(f)),dict(Check='Filas idénticas posteriores conservadas',Count=int(d.DuplicateCandidate.sum())),
      dict(Check='Cliente desconocido (fuente)',Count=int((d.KnownCustomer==0).sum())),dict(Check='Descripción vacía original',Count=int(d.MissingDescription.sum())),
      dict(Check='Precio cero',Count=int((d.UnitPrice==0).sum())),dict(Check='Precio negativo',Count=int((d.UnitPrice<0).sum()))]
    no_dup=metrics(f[f.DuplicateCandidate==0])
    exclusions=d[d.Included==0]
    row_cols=['SourceRow','InvoiceNo','StockCode','StockCodeOriginal','Description','Quantity','InvoiceDate','UnitPrice','CustomerID','Country',
              'Date','YearMonth','Hour','Weekday','RecordClass','TransactionType','AmountGBP','AmountMilliGBP','DuplicateCandidate','MissingDescription','KnownCustomer','Included']
    clean_path=ROOT/'data/processed'
    d[row_cols].to_csv(clean_path/'transactions_audited.csv',index=False,encoding='utf-8-sig',date_format='%Y-%m-%d %H:%M:%S')
    fact_cols=['SourceRow','InvoiceNo','StockCode','CustomerID','Country','Date','Quantity','UnitPrice','AmountGBP','AmountMilliGBP','TransactionType','DuplicateCandidate']
    f[fact_cols].to_csv(clean_path/'FactTransactions.csv',index=False,encoding='utf-8-sig')
    prod[['StockCode','Description']].to_csv(clean_path/'DimProduct.csv',index=False,encoding='utf-8-sig')
    pd.DataFrame({'CustomerID':sorted(f.CustomerID.unique())}).to_csv(clean_path/'DimCustomer.csv',index=False,encoding='utf-8-sig')
    pd.DataFrame({'Country':sorted(f.Country.unique())}).to_csv(clean_path/'DimCountry.csv',index=False,encoding='utf-8-sig')
    dates=pd.DataFrame({'Date':pd.date_range(d.InvoiceDate.min().normalize(),d.InvoiceDate.max().normalize())})
    dates['YearMonth']=dates.Date.dt.strftime('%Y-%m');dates['Year']=dates.Date.dt.year
    dates['Month']=dates.Date.dt.month;dates['Weekday']=dates.Date.dt.dayofweek+1
    dates['CompleteMonth']=(dates.YearMonth!='2011-12').astype(int)
    dates.to_csv(clean_path/'DimDate.csv',index=False,encoding='utf-8-sig',date_format='%Y-%m-%d')
    for name,df in [('monthly',pd.DataFrame(monthly)),('countries',country_df),('products',prod),('customers',cust),('cube',pd.DataFrame(cube)),('reconciliation',pd.DataFrame(classes))]:
        df.to_csv(clean_path/(name+'.csv'),index=False,encoding='utf-8-sig')
    # SQL independiente sobre importes enteros: comprueba totales y claves.
    conn=sqlite3.connect(ROOT/'analysis/retail.sqlite')
    f[fact_cols].to_sql('FactTransactions',conn,index=False,if_exists='replace')
    sql_totals=conn.execute('SELECT COUNT(*), SUM(AmountMilliGBP), COUNT(DISTINCT CASE WHEN TransactionType="Venta" THEN InvoiceNo END) FROM FactTransactions').fetchone()
    validations=[]
    def check(name,actual,expected):
        ok=actual==expected
        validations.append(dict(test=name,actual=actual,expected=expected,passed=bool(ok)))
        assert ok,(name,actual,expected)
    check('Filas incluidas + excluidas = fuente',len(f)+len(exclusions),len(raw))
    check('Conciliación importe firmado exacto',int(f.AmountMilliGBP.sum()+exclusions.AmountMilliGBP.sum()),int(d.AmountMilliGBP.sum()))
    check('SQL vs pandas: filas',int(sql_totals[0]),len(f))
    check('SQL vs pandas: milésimas GBP',int(sql_totals[1]),int(f.AmountMilliGBP.sum()))
    check('SQL vs pandas: pedidos',int(sql_totals[2]),overall['Orders'])
    check('Claves de fila únicas',int(f.SourceRow.nunique()),len(f))
    check('Cada factura pertenece a un país',int(sales.groupby('InvoiceNo').Country.nunique().max()),1)
    check('Cada factura pertenece a un mes',int(sales.groupby('InvoiceNo').YearMonth.nunique().max()),1)
    check('Producto único sin distinguir mayúsculas',int(prod.StockCode.str.casefold().nunique()),len(prod))
    assert f.StockCode.eq(f.StockCode.str.strip().str.upper()).all()
    assert set(f.StockCode).issubset(set(prod.StockCode))
    check('Calendario sin huecos',len(dates),int((dates.Date.max()-dates.Date.min()).days)+1)
    conn.close()
    hourly=[dict(Hour=int(k),GrossGBP=int(x.GrossMilli.sum())/1000,Orders=int(x.InvoiceNo.nunique())) for k,x in sales.groupby('Hour')]
    weekdays=[dict(Weekday=int(k),GrossGBP=int(x.GrossMilli.sum())/1000,Orders=int(x.InvoiceNo.nunique())) for k,x in sales.groupby('Weekday')]
    large=f.loc[f.AmountGBP.abs()>=50000,['SourceRow','InvoiceNo','StockCode','CustomerID','Date','Quantity','UnitPrice','AmountGBP','TransactionType']]
    results=dict(source=dict(file=path.name,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),rows=len(raw),
       start=str(d.InvoiceDate.min()),end=str(d.InvoiceDate.max()),currency='GBP',signed_total=int(d.AmountMilliGBP.sum())/1000),
       overall=overall,monthly=monthly,countries=records(country_df),products=records(prod),customers=records(cust),cube=cube,
       reconciliation=classes,quality=issues,no_duplicates=no_dup,large_transactions=records(large),hourly=hourly,weekdays=weekdays,
       validations=validations,excluded_total=int(exclusions.AmountMilliGBP.sum())/1000)
    save_json(ROOT/'analysis/results.json',results)
    save_json(ROOT/'analysis/validation.json',validations)
    print(json.dumps({k:results[k] for k in ['overall','no_duplicates','excluded_total','quality','large_transactions']},ensure_ascii=False,indent=2))
    print('TOP MONTHS',pd.DataFrame(monthly).sort_values('NetGBP',ascending=False).head(3).to_string(index=False))
    print('TOP PRODUCTS',prod.head(5).to_string(index=False))
    print('TOP COUNTRIES',country_df.head(5).to_string(index=False))
    print('TOP CUSTOMERS',cust.head(5).to_string(index=False))
    print('CHECKS',len(validations),'passed')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);p.add_argument('--cache',type=Path)
    args=p.parse_args();run(args.input,args.cache)
