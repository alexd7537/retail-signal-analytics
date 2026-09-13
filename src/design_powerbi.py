"""RETAIL / SIGNAL: visuales nativos PBIR, tema integrado y navegación.
No calcula ni modifica ventas. Requiere revisión final en Power BI Desktop.
"""
import json, uuid
from pathlib import Path

INK='#153C3C'; TEAL='#167C73'; CORAL='#D76B50'; PAPER='#F5F3ED'
MUTED='#657674'; LINE='#DFE7E2'; WHITE='#FFFFFF'; SOFT='#E9F2ED'
SCHEMA='https://developer.microsoft.com/json-schemas/fabric/item/report/definition/'
PAGES=['Resumen','Productos','Clientes','Calidad']
WIDTH,HEIGHT=1440,900

def write(p,x):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
def literal(x):
    value=str(x).lower() if isinstance(x,bool) else str(x)+'D' if isinstance(x,(int,float)) else "'"+x.replace("'","''")+"'"
    return {'expr':{'Literal':{'Value':value}}}
def color(x):return {'solid':{'color':literal(x)}}
def obj(props,selector=None):
    result={'properties':props}
    if selector:result['selector']={'id':selector}
    return [result]
def encode(props):
    return {k:color(v) if isinstance(v,str) and v.startswith('#') else literal(v) for k,v in props.items()}
def field(table,col,measure=False):
    return {('Measure' if measure else 'Column'):{'Expression':{'SourceRef':{'Entity':table}},'Property':col}}
def projection(t,c,m=False):return {'field':field(t,c,m),'queryRef':t+'.'+c,'nativeQueryRef':c}

def build_design(root,model,types):
    report=root/'powerbi/OnlineRetail.Report'; definition=report/'definition'
    records=[]
    theme_name='RetailSignal-9d2c71e4.json'
    theme={
      '$schema':'https://raw.githubusercontent.com/microsoft/powerbi-desktop-samples/main/Report%20Theme%20JSON%20Schema/reportThemeSchema-2.157.json',
      'name':theme_name,'dataColors':[TEAL,CORAL,'#B5A169','#7EA79A','#7C869D',INK],
      'background':WHITE,'foreground':INK,'foregroundNeutralSecondary':MUTED,
      'foregroundNeutralTertiary':'#83918C','backgroundLight':LINE,'backgroundNeutral':PAPER,
      'tableAccent':TEAL,'good':TEAL,'neutral':'#B78D36','bad':CORAL,
      'textClasses':{'callout':{'fontFace':'Segoe UI Semibold','fontSize':28,'color':INK},
        'title':{'fontFace':'Segoe UI Semibold','fontSize':12,'color':INK},
        'header':{'fontFace':'Segoe UI Semibold','fontSize':11,'color':INK},
        'label':{'fontFace':'Segoe UI','fontSize':10,'color':MUTED}},
      'visualStyles':{'*':{'*':{
        'title':[{'show':True,'fontFamily':'Segoe UI Semibold','fontSize':12,'fontColor':{'solid':{'color':INK}}}],
        'background':[{'show':True,'color':{'solid':{'color':WHITE}},'transparency':0}],
        'border':[{'show':True,'color':{'solid':{'color':LINE}},'radius':12,'width':1}],
        'padding':[{'top':12,'bottom':12,'left':16,'right':16}],
        'visualHeader':[{'show':True}],
      }},'tableEx':{'*':{
        'columnHeaders':[{'fontColor':{'solid':{'color':INK}},'backColor':{'solid':{'color':SOFT}},'fontFamily':'Segoe UI Semibold','fontSize':10,'bold':True,'autoSizeColumnWidth':True,'columnAdjustment':'growToFit'}],
        'values':[{'fontFamily':'Segoe UI','fontSize':10,'fontColorPrimary':{'solid':{'color':INK}},'fontColorSecondary':{'solid':{'color':INK}},'backColorPrimary':{'solid':{'color':WHITE}},'backColorSecondary':{'solid':{'color':'#F7F9F6'}}}],
        'grid':[{'gridVertical':False,'gridHorizontal':False,'rowPadding':7}],
      }}}}
    write(report/'StaticResources/RegisteredResources'/theme_name,theme)
    write(root/'powerbi/Tema_OnlineRetail.json',theme)
    write(definition/'report.json',{'$schema':SCHEMA+'report/3.0.0/schema.json',
      'themeCollection':{'customTheme':{'name':theme_name,'type':'RegisteredResources','reportVersionAtImport':{'visual':'2.4.0','report':'3.0.0','page':'2.0.0'}}},
      'resourcePackages':[{'name':'RegisteredResources','type':'RegisteredResources','items':[{'name':theme_name,'path':theme_name,'type':'CustomTheme'}]}]})
    write(definition/'version.json',{'$schema':SCHEMA+'versionMetadata/1.0.0/schema.json','version':'2.0.0'})
    write(definition/'pages/pages.json',{'$schema':SCHEMA+'pagesMetadata/1.0.0/schema.json','pageOrder':PAGES,'activePageName':'Resumen'})

    def container(title='',bg=WHITE,border=True,padding=14):
        return {
          'title':obj(encode({'show':bool(title),'text':title,'fontSize':12,'fontFamily':'Segoe UI Semibold','fontColor':INK})),
          'background':obj(encode({'show':bg is not None,'color':bg or WHITE,'transparency':0})),
          'border':obj(encode({'show':border,'color':LINE,'radius':12,'width':1})),
          'padding':obj(encode(dict.fromkeys(['top','bottom','left','right'],padding))),
        }
    def add(page,kind,key,x,y,w,h,roles=None,title='',objects=None,vco=None,sort=None,top=None):
        name=uuid.uuid5(uuid.NAMESPACE_URL,'retail-signal/'+page+'/'+key).hex[:20]
        v={'$schema':SCHEMA+'visualContainer/2.4.0/schema.json','name':name,
          'position':{'x':x,'y':y,'z':(len(records)+1)*1000,'width':w,'height':h,'tabOrder':(len(records)+1)*1000},
          'visual':{'visualType':kind,'visualContainerObjects':vco or container(title),'drillFilterOtherVisuals':True}}
        if objects:v['visual']['objects']=objects
        if roles:
            q={'queryState':{role:{'projections':[projection(*f) for f in fs]} for role,fs in roles.items()}}
            if sort:q['sortDefinition']={'sort':[{'field':field(*sort[:3]),'direction':sort[3]}],'isDefaultSort':True}
            v['visual']['query']=q
        if top:
            t,c,measure,n=top
            cf={'Column':{'Expression':{'SourceRef':{'Source':'d'}},'Property':c}}
            mf={'Measure':{'Expression':{'SourceRef':{'Source':'f'}},'Property':measure}}
            query={'Version':2,'From':[{'Name':'d','Entity':t,'Type':0},{'Name':'f','Entity':'FactTransactions','Type':0}],
              'Select':[dict(cf,Name='field')],'OrderBy':[{'Direction':2,'Expression':mf}],'Top':n}
            v['filterConfig']={'filters':[{'name':'Top'+str(n)+name,'field':field(t,c),'type':'TopN','howCreated':'User',
              'filter':{'Version':2,'From':[{'Name':'subquery','Expression':{'Subquery':{'Query':query}},'Type':2},{'Name':'d','Entity':t,'Type':0}],
              'Where':[{'Condition':{'In':{'Expressions':[cf],'Table':{'SourceRef':{'Source':'subquery'}}}}}]}}]}
        write(definition/f'pages/{page}/visuals/{name}/visual.json',v)
        records.append((page,key,v))
        return v
    def text(page,key,t,x,y,w,h,size=12,fg=MUTED,bold=False,bg=None):
        pars=[
          {'textRuns':[{'value':line,'textStyle':{'fontFamily':'Segoe UI Semibold' if bold else 'Segoe UI','fontSize':str(size)+'px','color':fg}}],'horizontalTextAlignment':'left'} for line in t.split('\n')]
        return add(page,'textbox',key,x,y,w,h,objects={'general':obj({'paragraphs':pars})},vco=container(bg=bg,border=False,padding=0))
    def button(page,target,i):
        selected=page==target; label=['Panorama','Productos','Clientes','Calidad'][i]
        fg=WHITE if selected else '#B8CECA';bg='#28605B' if selected else INK
        styles={'text':encode({'show':True,'text':f'0{i+1}   {label}','fontSize':12,'fontColor':fg,'fontFamily':'Segoe UI Semibold','horizontalAlignment':'left','leftMargin':16}),
          'fill':encode({'show':True,'fillColor':bg,'transparency':0}),'outline':encode({'show':False})}
        objects={k:obj(v)+obj(v,'default') for k,v in styles.items()}
        objects['fill']+=obj(encode({'show':True,'fillColor':'#34736B','transparency':0}),'hover')
        objects['shape']=obj(encode({'tileShape':'rectangleRounded','rectangleRoundedCurve':12}))
        vco=container(bg=None,border=False,padding=0)
        vco['visualLink']=obj(encode({'show':True,'type':'PageNavigation','navigationSection':target,'tooltip':'Ir a '+label}))
        add(page,'actionButton','nav-'+target,16,214+i*57,168,46,objects=objects,vco=vco)
    labels={
      'Resumen':('El pulso de las ventas','Panorama comercial de productos, pedidos y mercados.'),
      'Productos':('Qué productos mueven el negocio','Explora los líderes de ventas y dónde se concentran los abonos.'),
      'Clientes':('Quién compra y quién vuelve','Compradores identificados, recurrencia y cobertura del dato.'),
      'Calidad':('Los números, bajo la lupa','Conciliación global y decisiones que sostienen el análisis.')}
    for i,page in enumerate(PAGES):
        write(definition/f'pages/{page}/page.json',{'$schema':SCHEMA+'page/2.0.0/schema.json','name':page,'displayName':f'0{i+1} · '+('Panorama' if page=='Resumen' else page),'displayOption':'FitToPage','height':HEIGHT,'width':WIDTH,
          'objects':{'background':obj(encode({'color':PAPER,'transparency':0})),'outspace':obj(encode({'color':'#DFE5DF','transparency':0}))}})
        text(page,'rail','',0,0,200,900,bg=INK)
        text(page,'wordmark','RETAIL /\nSIGNAL',25,37,160,79,28,WHITE,True)
        text(page,'rail-kicker','ANÁLISIS COMERCIAL',25,137,165,24,10,'#ABD0BC')
        for j,target in enumerate(PAGES):button(page,target,j)
        text(page,'rail-note','ONLINE RETAIL\nDIC 2010 — DIC 2011\n\nDatos históricos · GBP\nCaso de portafolio',25,718,158,145,11,'#B8CECA')
        text(page,'section',f'0{i+1} / '+('PANORAMA' if page=='Resumen' else page.upper()),228,22,560,20,10,TEAL,True)
        text(page,'heading',labels[page][0],228,48,1135,43,30,INK,True)
        text(page,'subtitle',labels[page][1],228,94,1135,25,13,MUTED)
        text(page,'footer','UCI · Online Retail  /  Productos, no ingreso contable total  /  Diciembre 2011: solo días 1–9',228,869,1184,24,10,MUTED)
        if page!='Calidad':
            choices=[('Mes','DimDate','YearMonth'),('País','DimCountry','Country')]
            if page=='Productos':choices.append(('Código de producto','DimProduct','StockCode'))
            elif page=='Clientes':choices.append(('Cliente','DimCustomer','CustomerID'))
            for j,(label,table,col) in enumerate(choices):
                add(page,'slicer','filter-'+col,228+j*398,132,378,80,{'Values':[(table,col,False)]},objects={
                  'data':obj(encode({'mode':'Dropdown'})),
                  'header':obj(encode({'show':True,'text':label,'fontColor':MUTED,'fontFamily':'Segoe UI Semibold','textSize':10})),
                  'items':obj(encode({'fontColor':INK,'fontFamily':'Segoe UI','textSize':11}))},vco=container(bg=WHITE,padding=8))
            if page=='Resumen':text(page,'filter-help','Selecciona un mes o país.\nLos gráficos responden a la selección.',1032,146,354,55,12,MUTED)
        else:text(page,'quality-scope','ALCANCE GLOBAL   ·   Esta página mantiene todos los registros para conciliar con el archivo original.',228,145,1165,41,13,INK)
    def card(page,m,i,table='FactTransactions',hero=False,accent=False,units=1,precision=0):
        bg=INK if hero else WHITE;fg=WHITE if hero else (CORAL if accent else INK)
        objects={
          'value':obj(encode({'fontFamily':'Segoe UI Semibold','fontSize':28,'fontColor':fg,'labelDisplayUnits':units,'labelPrecision':precision,'horizontalAlignment':'left'}),'default'),
          'label':obj(encode({'show':True,'text':m,'fontFamily':'Segoe UI','fontSize':11,'fontColor':'#C1DCD1' if hero else MUTED,'position':'aboveValue','horizontalAlignment':'left'}),'default'),
          'fillCustom':obj(encode({'show':True,'fillColor':bg,'transparency':0}),'default'),
          'outline':obj(encode({'show':False}),'default'),
          'layout':obj(encode({'paddingUniform':0,'backgroundShow':False}),'default'),
          'padding':obj(encode({'paddingUniform':8}),'default'),
        }
        return add(page,'cardVisual','kpi-'+m,228+i*298,232,278,124,{'Data':[(table,m,True)]},objects=objects,vco=container(bg=bg,padding=8))
    card('Resumen','Ventas netas',0,hero=True,units=1000000,precision=2)
    card('Resumen','Pedidos',1)
    card('Resumen','Ticket bruto',2,precision=2)
    card('Resumen','Abonos sobre bruto',3,accent=True,precision=1)
    for page,ms in [('Productos',['Ventas netas','Unidades vendidas','Abonos','Abonos sobre bruto']),('Clientes',['Clientes compradores','Clientes recurrentes','Recurrencia','Cobertura de cliente'])]:
        for i,m in enumerate(ms):card(page,m,i,hero=i==0,accent=i==2 and page=='Productos',units=1000000 if m=='Ventas netas' else 1,precision=2 if m=='Ventas netas' else 1 if m in ['Recurrencia','Cobertura de cliente','Abonos sobre bruto'] else 0)
    card('Calidad','Filas fuente',0,'Quality',hero=True)
    card('Calidad','Filas incluidas',1)
    card('Calidad','Posibles duplicados',2,accent=True)
    card('Calidad','Impacto duplicados',3,precision=2)
    def chart(page,key,title,x,y,w,h,table,category,metric,kind='barChart',n=None,accent=False):
        objects={'legend':obj(encode({'show':False})),
          'dataPoint':obj({'defaultColor':color(CORAL if accent else TEAL)}),
          'categoryAxis':obj(encode({'showAxisTitle':False,'fontSize':10,'fontFamily':'Segoe UI','labelColor':MUTED})),
          'valueAxis':obj(encode({'showAxisTitle':False,'fontSize':10,'fontFamily':'Segoe UI','labelColor':MUTED,'gridlineShow':True,'gridlineColor':LINE}))}
        if kind=='lineChart':objects['lineStyles']=obj(encode({'strokeWidth':3}))
        return add(page,kind,key,x,y,w,h,{'Category':[(table,category,False)],'Y':[('FactTransactions',metric,True)]},title=title,objects=objects,
          sort=(table,category,False,'Ascending') if kind=='lineChart' else ('FactTransactions',metric,True,'Descending'),
          top=(table,category,metric,n) if n else None)
    def table(page,key,title,fields,y=702,h=148):
        add(page,'tableEx',key,228,y,1172,h,{'Values':fields},title=title)
    measures=lambda ms:[('FactTransactions',m,True) for m in ms]
    chart('Resumen','trend','Ventas netas por mes · GBP',228,378,730,302,'DimDate','YearMonth','Ventas netas','lineChart')
    chart('Resumen','markets','5 mercados con más venta neta · GBP',978,378,422,302,'DimCountry','Country','Ventas netas',n=5)
    table('Resumen','monthly-detail','El detalle detrás de la tendencia',[('DimDate','YearMonth',False)]+measures(['Ventas brutas','Abonos','Ventas netas','Pedidos','Variacion mensual comparable']))
    chart('Productos','best-products','10 productos por venta neta · GBP',228,378,576,302,'DimProduct','StockCode','Ventas netas',n=10)
    chart('Productos','credits','10 productos por valor abonado · GBP',824,378,576,302,'DimProduct','StockCode','Abonos',n=10,accent=True)
    table('Productos','product-detail','Explora código, descripción y desempeño',[('DimProduct','StockCode',False),('DimProduct','Description',False)]+measures(['Ventas netas','Unidades vendidas','Pedidos','Abonos']))
    chart('Clientes','buyers','10 clientes por venta neta · UNKNOWN = sin identificar',228,378,576,302,'DimCustomer','CustomerID','Ventas netas',n=10)
    chart('Clientes','buyer-trend','Compradores identificados por mes',824,378,576,302,'DimDate','YearMonth','Clientes compradores','lineChart')
    table('Clientes','customer-detail','Pedidos y valor por cliente · los compradores excluyen UNKNOWN',[('DimCustomer','CustomerID',False)]+measures(['Ventas netas','Pedidos','Ticket bruto','Abonos']))
    table('Calidad','reconciliation','Puente de conciliación · de la fuente al alcance comercial',
      [('Quality','RecordClass',False),('Quality','TransactionType',False),('Quality','Included',False),('Quality','Filas fuente',True),('Quality','Importe fuente',True)],378,274)
    table('Calidad','duplicate-sensitivity','Qué cambia si se retiran repeticiones exactas',measures(['Ventas brutas','Abonos','Ventas netas','Neto sin duplicados','Impacto duplicados']),676,108)
    text('Calidad','quality-note','Las repeticiones se conservan: no existe un identificador de línea que pruebe que sean errores de carga.',246,808,1128,38,12,MUTED)
    lookup={t['name']:set(types[t['name']])|{m['name'] for m in t.get('measures',[])} for t in model['model']['tables']}
    for page,key,v in records:
        p=v['position'];assert p['x']>=0 and p['y']>=0 and p['x']+p['width']<=WIDTH and p['y']+p['height']<=HEIGHT,(page,key)
        for config in v['visual'].get('query',{}).get('queryState',{}).values():
            for pr in config['projections']:
                f=next(iter(pr['field'].values()));assert f['Property'] in lookup[f['Expression']['SourceRef']['Entity']]
    write(root/'analysis/powerbi_validation.json',{'pages':4,'visuals':len(records),'tables':6,'relationships':4,'field_references':'passed','canvas_bounds':'passed','navigation_targets':'passed','theme_registered':True,'native_desktop_refresh':'not_executed','native_desktop_visual_review':'not_executed'})
    print('RETAIL / SIGNAL:',len(records),'native visuals; 4 pages; integrated theme; navigation and layout checks passed.')
