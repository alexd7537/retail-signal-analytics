import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {Workbook,SpreadsheetFile,FileBlob} from '@oai/artifact-tool';
const out=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const r=JSON.parse(await fs.readFile(path.join(out,'analysis/results.json'),'utf8'));
const wb=Workbook.create();
for(const name of ['Resumen','Filtros','Datos','Validación','Productos','Clientes','Países','Guía'])wb.worksheets.add(name);
const navy='#153C3C',light='#E9F2ED',blue='#167C73',amber='#D76B50';
const money='"£"#,##0.00;[Red]("£"#,##0.00)';
const count='#,##0';
const styles={};
function setup(name,lastRow=45,lastCol='O'){
 const s=wb.worksheets.getItem(name);s.showGridLines=false;
 s.getRange(`A1:${lastCol}${lastRow}`).format={font:{name:'Arial',size:10,color:navy},rowHeight:22,fill:'#F5F3ED',verticalAlignment:'center'};
 s.getRange(`A1:A${lastRow}`).format.columnWidth=3;
 s.getRange(`B1:${lastCol}${lastRow}`).format.columnWidth=14;
 return s;
}
function title(s,t,context){
 s.getRange('B2').values=[['RETAIL / SIGNAL']];
 s.getRange('B2:O2').format.font={name:'Arial',size:10,bold:true,color:blue};
 s.getRange('B3').values=[[t]];s.getRange('B3:O3').format.font={name:'Arial',size:20,bold:true,color:navy};
 s.getRange('B3:O3').format.rowHeight=34;
 s.getRange('B4').values=[[context]];s.getRange('B4:O4').format.font={name:'Arial',size:10,color:'#657674'};
 s.getRange('B4:O4').format.borders={bottom:{style:'thin',color:'#D9E3DB'}};
}
function head(s,addr,labels){s.getRange(addr).values=[labels];s.getRange(addr).format={fill:navy,font:{name:'Arial',size:10,color:'#FFFFFF',bold:true},rowHeight:30,wrapText:true,horizontalAlignment:'center'};}
function write(s,row,col,data){if(data.length)s.getRangeByIndexes(row-1,col-1,data.length,data[0].length).values=data;}
function formula(s,addr,f){s.getRange(addr).formulas=[[f]];}
function chart(s,type,ranges,a,b,t){const c=s.charts.add(type,ranges.map(x=>s.getRange(x)));c.title=t;c.hasLegend=false;c.titleTextStyle.typeface='Arial';c.titleTextStyle.fontSize=13;c.xAxis={axisType:'textAxis',textStyle:{typeface:'Arial',fontSize:10}};c.yAxis={numberFormatCode:type==='line'?'"£"0.0,," M"':'"£"#,##0," k"',numberFormatSourceLinked:false,textStyle:{typeface:'Arial',fontSize:10}};c.setPosition(a,b);for(const z of c.series.items){z.fill=blue;if(type==='line')z.line={fill:blue,style:'solid',width:2};}return c;}
// Core template tabs retain their roles: output, controls, build, independent audit.
const ctrl=setup('Filtros',47);
ctrl.getRange('C4').dataValidation=null;
title(ctrl,'Controles del dashboard','Datos históricos en GBP. Solo las celdas amarillas son controles.');
write(ctrl,5,2,[['Mes'],['País']]);ctrl.getRange('D5').values=[['Todos']];ctrl.getRange('D6').values=[['Todos']];ctrl.getRange('D5:D6').format.fill='#FFF2CC';ctrl.getRange('D5:D6').format.columnWidth=24;
write(ctrl,9,2,[['Alcance: productos con precio positivo y documento con signo válido.'],['Los posibles duplicados se conservan. Validación muestra la sensibilidad.'],['Los filtros controlan Resumen. Productos, Clientes y Países cubren todo el periodo.'],['Los abonos se registran en su fecha; no se asignan a una venta original.'],['Diciembre de 2011 es parcial (1–9). No comparar con un mes completo.'],['Para refrescar: ejecutar src/analyze.py y reconstruir el libro con el script entregado.']]);
ctrl.getRange('J5:K5').values=[['Meses','Países']];
write(ctrl,6,10,['Todos',...r.monthly.map(x=>x.YearMonth)].map(x=>[x]));write(ctrl,6,11,['Todos',...r.countries.map(x=>x.Country).sort()].map(x=>[x]));ctrl.getRange('K5:K45').format.columnWidth=25;
ctrl.getRange('D5').dataValidation={rule:{type:'list',formula1:'Filtros!$J$6:$J$19'},errorAlert:{style:'stop',title:'Mes no válido',message:'Seleccione un mes de la lista.'}};
ctrl.getRange('D6').dataValidation={rule:{type:'list',formula1:`Filtros!$K$6:$K$${6+r.countries.length}`},errorAlert:{style:'stop',title:'País no válido',message:'Seleccione un país de la lista.'}};
const build=setup('Datos',r.cube.length+7,'P');
title(build,'Agregados de ventas','Cada fila se calcula desde las transacciones. No sumar filas con «Todos».');
build.getRange('B4').values=[['Fuente: Online Retail.xlsx (archivo del usuario); UCI https://doi.org/10.24432/C5BW33. Análisis: src/analyze.py.']];
head(build,'B6:P6',['Mes','País','Bruto GBP','Abonos GBP','Neto GBP','Pedidos','Doc. abono','Clientes','Recurrentes','Unidades','Unid. abono','Bruto identificado','Líneas','Ticket GBP','Abonos / bruto']);
write(build,7,2,r.cube.map(x=>[x.YearMonth,x.Country,x.GrossGBP,x.CreditGBP,null,x.Orders,x.CreditDocuments,x.Customers,x.RepeatCustomers,x.Units,x.CreditUnits,x.KnownGrossGBP,x.Rows,null,null]));
const end=r.cube.length+6;
build.getRange(`F7:F${end}`).formulas=r.cube.map((x,i)=>[`=D${i+7}-E${i+7}`]);
build.getRange(`O7:O${end}`).formulas=r.cube.map((x,i)=>[`=IF(G${i+7}=0,"n.a.",D${i+7}/G${i+7})`]);
build.getRange(`P7:P${end}`).formulas=r.cube.map((x,i)=>[`=IF(D${i+7}=0,"n.a.",E${i+7}/D${i+7})`]);
console.log('Cube ready');
build.getRange(`D7:F${end}`).setNumberFormat(money);build.getRange(`G7:L${end}`).setNumberFormat(count);build.getRange(`M7:M${end}`).setNumberFormat(money);build.getRange(`O7:O${end}`).setNumberFormat(money);build.getRange(`P7:P${end}`).setNumberFormat('0.0%');build.getRange(`C6:C${end}`).format.columnWidth=23;build.freezePanes.freezeRows(6);
build.tables.add(`B6:P${end}`,true,'CuboVentas');
const sum=(column,month,country)=>`SUMIFS('Datos'!$${column}$7:$${column}$${end},'Datos'!$B$7:$B$${end},${month},'Datos'!$C$7:$C$${end},${country})`;
const s=setup('Resumen',54);s.tabColor=navy;
title(s,'El pulso de las ventas','Diciembre 2010 – diciembre 2011. Moneda: GBP. Diciembre 2011 es parcial.');
write(s,5,2,[['Mes:']]);formula(s,'C5',"=Filtros!D5");s.getRange('F5').values=[['País:']];formula(s,'G5',"=Filtros!D6");s.getRange('J5').values=[['Cambiar selección en Filtros']];
const cards=[['B7','B8','VENTAS NETAS','F',money],['F7','F8','PEDIDOS','G',count],['J7','J8','TICKET BRUTO','O',money],['B10','B11','ABONOS / BRUTO','P','0.0%'],['F10','F11','CLIENTES IDENTIFICADOS','I',count],['J10','J11','VENTAS BRUTAS','D',money]];
for(const addr of ['B8:D8','F8:H8','J8:L8','B11:D11','F11:H11','J11:L11']){s.getRange(addr).merge();s.getRange(addr).format.horizontalAlignment='left';}
for(const [lab,val,t,col,fmt] of cards){s.getRange(lab).values=[[t]];s.getRange(lab).format.font={size:9,bold:true,color:navy};formula(s,val,'='+sum(col,'Filtros!$D$5','Filtros!$D$6'));s.getRange(val).setNumberFormat(fmt);s.getRange(val).format.font={size:22,bold:true,color:navy};}
// Jerarquía visual: un indicador protagonista y cinco métricas de apoyo.
for(const block of ['B7:D8','F7:H8','J7:L8','B10:D11','F10:H11','J10:L11']){
 s.getRange(block).format.fill='#FFFFFF';
 s.getRange(block).format.borders={top:{style:'medium',color:light}};
}
s.getRange('B7:D8').format.fill=navy;
s.getRange('B7:D8').format.font.color='#FFFFFF';
s.getRange('B8:L8').format.rowHeight=38;s.getRange('B11:L11').format.rowHeight=38;
s.getRange('B10').format.font.color=amber;
s.getRange('B13').values=[['Diciembre 2011: solo días 1–9.']];
s.getRange('B13').format.font={size:10,color:amber};
s.getRange('J13').values=[['Cinco líderes del periodo completo.']];
s.getRange('J13').format.font={size:10,color:blue};
// Ticket/rate: guard no-order slices, preserving unavailable instead of manufactured zeros.
formula(s,'J8','=IF(F8=0,"n.a.",J11/F8)');formula(s,'B11','='+`IF(J11=0,"n.a.",${sum('E','Filtros!$D$5','Filtros!$D$6')}/J11)`);
head(s,'B31:H31',['Mes','Bruto GBP','Abonos GBP','Neto GBP','Pedidos','Ticket GBP','Var. neta MoM']);
for(let i=0;i<r.monthly.length;i++){
 const row=32+i;s.getRange(`B${row}`).values=[[r.monthly[i].YearMonth]];
 for(const [dst,src] of [['C','D'],['D','E'],['E','F'],['F','G']])formula(s,`${dst}${row}`,'='+sum(src,`B${row}`,'Filtros!$D$6'));
 formula(s,`G${row}`,`=IF(F${row}=0,"n.a.",C${row}/F${row})`);
 if(i===0||r.monthly[i].Partial)s.getRange(`H${row}`).values=[['n.a.']];else formula(s,`H${row}`,`=IF(E${row-1}<=0,"n.a.",E${row}/E${row-1}-1)`);
}
s.getRange('C32:E44').setNumberFormat(money);s.getRange('G32:G44').setNumberFormat(money);s.getRange('H32:H44').setNumberFormat('0.0%');s.getRange('F32:F44').setNumberFormat(count);s.getRange('B44:H44').format.fill='#FFF2CC';
head(s,'J31:L31',['País','Neto GBP','Pedidos']);
for(let i=0;i<r.countries.length;i++){const row=32+i;s.getRange(`J${row}`).values=[[r.countries[i].Country]];formula(s,`K${row}`,'='+sum('F','Filtros!$D$5',`J${row}`));formula(s,`L${row}`,'='+sum('G','Filtros!$D$5',`J${row}`));}
s.getRange('J31:J70').format.columnWidth=22;s.getRange('K32:K70').setNumberFormat(money);
chart(s,'line',['B31:B44','E31:E44'],'B14','I29','Ventas netas por mes (país seleccionado)');
chart(s,'bar',['J31:J36','K31:K36'],'J14','P29','5 mercados principales del periodo total');
s.getRange('B47').values=[['La tendencia usa el país; la tabla de países usa el mes. Las tarjetas usan ambos filtros.']];
s.getRange('B48').values=[['El gráfico compara los cinco mayores mercados del periodo total; el grupo se mantiene al cambiar mes.']];
s.getRange('B49').values=[['Clientes distintos y pedidos se calculan por selección: no se suman clientes de meses diferentes.']];
s.getRange('B50').values=[['Datos de entrada y fórmulas: Datos. Decisiones de limpieza y conciliación: Validación.']];
// Full product/customer/country views are deliberately period-wide and have native table filters.
const p=setup('Productos',r.products.length+32,'L');
title(p,'Qué productos mueven el negocio','Periodo completo. Filtros propios en la tabla. Los códigos identifican productos.');
head(p,'B24:K24',['Código','Descripción','Bruto GBP','Abonos GBP','Neto GBP','Unidades','Unid. abono','Pedidos','Abonos / bruto','% neto total']);
write(p,25,2,r.products.map(x=>[x.StockCode,x.Description,x.GrossGBP,x.CreditGBP,null,x.Units,x.CreditUnits,x.Orders,null,null]));
p.getRange(`F25:F${24+r.products.length}`).formulas=r.products.map((x,i)=>[`=D${i+25}-E${i+25}`]);
p.getRange(`J25:J${24+r.products.length}`).formulas=r.products.map((x,i)=>[`=IF(D${i+25}=0,"n.a.",E${i+25}/D${i+25})`]);
p.getRange(`K25:K${24+r.products.length}`).formulas=r.products.map((x,i)=>[`=F${i+25}/'Datos'!$F$7`]);
console.log('Products ready');
p.getRange(`C24:C${24+r.products.length}`).format.columnWidth=44;p.getRange(`D25:F${24+r.products.length}`).setNumberFormat(money);p.getRange(`J25:K${24+r.products.length}`).setNumberFormat('0.0%');p.freezePanes.freezeRows(24);p.tables.add(`B24:K${24+r.products.length}`,true,'ProductosVentas');
chart(p,'bar',['B24:B34','F24:F34'],'B5','G21','Top 10 productos por ventas netas (GBP)');
head(p,'H6:K6',['Código','Abonos GBP','Bruto GBP','Abonos / bruto']);
const pr=[...r.products].sort((a,b)=>b.CreditGBP-a.CreditGBP).slice(0,10);
write(p,7,8,pr.map(x=>[x.StockCode,x.CreditGBP,x.GrossGBP,null]));for(let n=7;n<=16;n++)formula(p,`K${n}`,`=IF(J${n}=0,"n.a.",I${n}/J${n})`);p.getRange('I7:J16').setNumberFormat(money);p.getRange('K7:K16').setNumberFormat('0.0%');p.getRange('H19').values=[['23843 y 23166: grandes ventas y abonos del mismo día.']];
const c=setup('Clientes',r.customers.length+30,'L');title(c,'Quién compra y quién vuelve','Periodo completo. UNKNOWN excluido del conteo y de esta tabla.');
head(c,'B24:I24',['Cliente','Pedidos','Última compra','Segmento','Bruto GBP','Abonos GBP','Neto GBP','Ticket bruto']);
write(c,25,2,r.customers.map(x=>[x.CustomerID,x.Orders,x.LastPurchase?new Date(x.LastPurchase):null,x.Segment,x.GrossGBP,x.CreditGBP,null,null]));
c.getRange(`H25:H${24+r.customers.length}`).formulas=r.customers.map((x,i)=>[`=F${i+25}-G${i+25}`]);
c.getRange(`I25:I${24+r.customers.length}`).formulas=r.customers.map((x,i)=>[`=IF(C${i+25}=0,"n.a.",F${i+25}/C${i+25})`]);
console.log('Customers ready');
c.getRange(`E24:E${24+r.customers.length}`).format.columnWidth=19;c.getRange(`F25:I${24+r.customers.length}`).setNumberFormat(money);c.getRange(`D25:D${24+r.customers.length}`).setNumberFormat('dd/mm/yyyy');c.tables.add(`B24:I${24+r.customers.length}`,true,'ClientesVentas');c.freezePanes.freezeRows(24);
chart(c,'bar',['B24:B34','H24:H34'],'B5','H21','Top 10 clientes por ventas netas (GBP)');
write(c,7,10,[['Clientes compradores',r.overall.Customers],['Recurrentes',r.overall.RepeatCustomers],['Una compra',r.overall.Customers-r.overall.RepeatCustomers],['Recurrencia',null],['Cobertura del bruto',null]]);c.getRange('J7:J11').format.columnWidth=24;formula(c,'K10','=K8/K7');formula(c,'K11',`=${r.overall.KnownGrossGBP}/${r.overall.GrossGBP}`);c.getRange('K10:K11').setNumberFormat('0.0%');
const pa=setup('Países',r.countries.length+30,'L');title(pa,'Mercados internacionales','Periodo completo. El país describe al cliente, no garantiza el destino del envío.');
head(pa,'B24:I24',['País','Bruto GBP','Abonos GBP','Neto GBP','Pedidos','Clientes','Ticket GBP','Abonos / bruto']);
write(pa,25,2,r.countries.map(x=>[x.Country,x.GrossGBP,x.CreditGBP,null,x.Orders,x.Customers,null,null]));
for(let i=0;i<r.countries.length;i++){let row=25+i;formula(pa,`E${row}`,`=C${row}-D${row}`);formula(pa,`H${row}`,`=IF(F${row}=0,"n.a.",C${row}/F${row})`);formula(pa,`I${row}`,`=IF(C${row}=0,"n.a.",D${row}/C${row})`);}
pa.getRange('B24:B70').format.columnWidth=24;pa.getRange('C25:E70').setNumberFormat(money);pa.getRange('H25:H70').setNumberFormat(money);pa.getRange('I25:I70').setNumberFormat('0.0%');pa.tables.add(`B24:I${24+r.countries.length}`,true,'PaísesVentas');pa.freezePanes.freezeRows(24);
chart(pa,'bar',['B26:B35','E26:E35'],'B5','K21','Ventas netas fuera de Reino Unido (GBP)');
const q=setup('Validación',62);title(q,'Los números, bajo la lupa','Alcance fijo: todas las filas del archivo. Los indicadores pueden solaparse.');
head(q,'B6:F6',['Control','Cantidad','Referencia','Diferencia','Resultado']);
for(let i=0;i<r.validations.length;i++){const row=7+i,x=r.validations[i];write(q,row,2,[[x.test,x.actual,x.expected,null,null]]);formula(q,`E${row}`,`=C${row}-D${row}`);formula(q,`F${row}`,`=IF(E${row}=0,"OK","REVISAR")`);}
q.getRange('B6:B61').format.columnWidth=57;q.getRange('C7:E16').setNumberFormat(count);q.getRange('E7:E16').conditionalFormats.add('cellIs',{operator:'notEqual',formula:0,format:{fill:'#FDE9E7',font:{color:'#A52A2A'}}});
head(q,'B20:D20',['Incidencia','Filas','% fuente']);write(q,21,2,r.quality.map(x=>[x.Check,x.Count,null]));for(let i=0;i<r.quality.length;i++)formula(q,`D${21+i}`,`=C${21+i}/$C$21`);q.getRange('C21:C28').setNumberFormat(count);q.getRange('D21:D28').setNumberFormat('0.0%');
head(q,'B32:D32',['Conciliación de importes','GBP','Observación']);
write(q,33,2,[['Importe firmado fuente',r.source.signed_total,'Productos + portes + ajustes + incidencias'],['Ventas netas de productos',r.overall.NetGBP,'Indicador comercial principal'],['Fuera del alcance',r.excluded_total,'Detalle en reconciliation.csv'],['Diferencia',null,'Debe ser cero']]);formula(q,'C36','=ROUND(C33-C34-C35,6)');q.getRange('C33:C36').setNumberFormat('"£"#,##0.000');
head(q,'B40:C40',['Sensibilidad a posibles duplicados','GBP']);write(q,41,2,[['Neto conservando filas idénticas',r.overall.NetGBP],['Neto eliminando repeticiones exactas',r.no_duplicates.NetGBP],['Diferencia',null]]);formula(q,'C43','=C41-C42');q.getRange('C41:C43').setNumberFormat(money);
write(q,47,2,[['Dos pares extremos, venta y abono del mismo día, suman £245.653,20 en cada sentido.'],['Se conservan. Influyen en ventas brutas y tasa de abonos, pero se compensan en el neto.'],['No hay enlace al documento original: abonos/bruto no es una tasa de devoluciones de pedidos.'],['No se calculan margen, beneficio ni rentabilidad porque no hay datos de costos.']]);
const m=setup('Guía',40);title(m,'Guía de uso y métricas','Proyecto de portafolio con datos históricos públicos; no es un encargo de un cliente.');
const notes=[
 ['Inicio','Resumen contiene las tarjetas y tendencias; seleccione mes/país en Filtros.'],
 ['Productos','Códigos normalizados a mayúsculas; todas las líneas se conservan. Tabla completa del periodo total.'],
 ['Clientes','La recurrencia significa dos o más facturas positivas distintas durante el periodo.'],
 ['Bruto','Suma de Quantity × UnitPrice para líneas elegibles positivas de productos.'],
 ['Abonos','Valor positivo del importe de documentos C con cantidad negativa y precio positivo.'],
 ['Neto','Bruto menos abonos; incluye el abono en su fecha y no reexpresa ventas históricas.'],
 ['Pedidos','Facturas distintas con al menos una línea positiva de producto.'],
 ['Ticket','Ventas brutas de productos / pedidos de productos. No incluye envío.'],
 ['Clientes','Clientes identificados con al menos una compra en la selección.'],
 ['Cobertura','Bruto con CustomerID conocido / bruto de productos.'],
 ['Moneda','GBP; se conservan milésimas en los controles, se muestran dos decimales en ventas.'],
 ['Original','541.909 filas. Copia sin modificar en la carpeta original suministrada.'],
 ['Procesamiento','src/analyze.py genera los CSV y analysis/results.json.'],
 ['Libro','Los agregados son una extracción completa. Cambiar filtros recalcula; nueva fuente requiere reconstrucción.'],
 ['Excel','No se incluyen 536.465 líneas en el libro. Están completas en FactTransactions.csv.'],
 ['Power BI','Modelo y reporte editable en powerbi. Consultar las instrucciones de actualización.'],
 ['Verificación','Controles independientes en SQLite y comparación de filtros/fórmulas del libro.'],
 ['Fuente','Daqing Chen (2015), Online Retail, UCI. https://doi.org/10.24432/C5BW33'],
 ['Licencia datos','CC BY 4.0. Se indican modificaciones y se conserva atribución.'],
 ['Límite temporal','2010-12-01 a 2011-12-09; diciembre 2011 incompleto. Un ciclo no prueba estacionalidad.'],
 ['Límite comercial','Los abonos pueden representar cancelación, devolución o corrección; no se conoce la causa.']];
write(m,6,2,notes);m.getRange('B6:B27').format.columnWidth=22;m.getRange('C6:C27').format.columnWidth=115;m.getRange('C6:C27').format.wrapText=true;m.getRange('B6:C27').format.rowHeight=34;
wb.recalculate();
// Verify the selection-dependent values against independently computed Python aggregates.
function near(a,b){return Math.abs(Number(a)-Number(b))<0.00001;}
if(!near(s.getRange('B8').values[0][0],r.overall.NetGBP))throw Error('Global net mismatch');
let baseInput=build.getRange('D7').values[0][0];
build.getRange('D7').values=[[baseInput+1000]];wb.recalculate();
if(!near(s.getRange('B8').values[0][0],r.overall.NetGBP+1000))throw Error('Input recalculation mismatch');
build.getRange('D7').values=[[baseInput]];
ctrl.getRange('D5').values=[['2011-11']];ctrl.getRange('D6').values=[['Germany']];wb.recalculate();
let expected=r.cube.find(x=>x.YearMonth==='2011-11'&&x.Country==='Germany');
if(!near(s.getRange('B8').values[0][0],expected.NetGBP)||s.getRange('F8').values[0][0]!==expected.Orders)throw Error('Filter mismatch');
ctrl.getRange('D5').values=[['Todos']];ctrl.getRange('D6').values=[['Todos']];wb.recalculate();
console.log((await wb.inspect({kind:'table',range:'Resumen!B7:L11',include:'values,formulas',tableMaxRows:5,tableMaxCols:11})).ndjson);
console.log((await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#NUM!|#SPILL!',options:{useRegex:true,maxResults:30}})).ndjson);
await fs.writeFile(path.join(out,'analysis/workbook_validation.json'),JSON.stringify({globalNet:'passed',filterGermanyNovember2011:'passed',inputChange1000GBP:'passed',inputsRestored:true,nativeExcelEngine:'not_executed'},null,2));
await (await SpreadsheetFile.exportXlsx(wb)).save(path.join(out,'Dashboard_Ventas.xlsx'));
for(const [name,range] of [['Resumen','A1:P29'],['Productos','A1:O22'],['Clientes','A1:L21'],['Países','A1:K21'],['Validación','A1:G43'],['Filtros','A1:O19'],['Datos','A1:P16'],['Guía','A1:C27']]){
 try {const blob=await wb.render({sheetName:name,range,scale:1.4,format:'png'});await fs.writeFile(path.join(out,'images',name+'.png'),new Uint8Array(await blob.arrayBuffer()));}
 catch(e){console.log('RENDER FAILURE',name,e.message);}
}
console.log('WORKBOOK COMPLETE');
