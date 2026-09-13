import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import sharp from 'sharp';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const r=JSON.parse(await fs.readFile(path.join(root,'analysis/results.json'),'utf8'));
const out=path.join(root,'images');
const ink='#153C3C',teal='#167C73',coral='#D76B50',paper='#F5F3ED',muted='#657674';
const esc=x=>String(x).replaceAll('&','&amp;').replaceAll('<','&lt;');
const num=x=>new Intl.NumberFormat('es-ES',{maximumFractionDigits:0}).format(x);
const txt=(x,y,t,size=18,color=ink,weight=400)=>`<text x="${x}" y="${y}" font-family="Arial,sans-serif" font-size="${size}" fill="${color}" font-weight="${weight}">${esc(t)}</text>`;
let b=[`<svg xmlns="http://www.w3.org/2000/svg" width="1440" height="860" viewBox="0 0 1440 860"><rect width="1440" height="860" fill="${paper}"/><rect width="484" height="860" fill="${ink}"/>`];
b.push(`<path d="M64 131v-24m18 24V89m18 42V70" fill="none" stroke="#AFCFB8" stroke-width="10" stroke-linecap="round"/>`);
b.push(txt(62,269,'RETAIL /',57,'#FFFFFF',700),txt(60,353,'SIGNAL',77,'#FFFFFF',700));
b.push(`<path d="M63 393h87" stroke="${coral}" stroke-width="5"/>`);
b.push(txt(63,460,`De ${num(r.source.rows)} registros`,24,'#E0ECE4'),txt(63,497,'a decisiones comerciales.',24,'#E0ECE4'));
b.push(txt(63,726,'PORTAFOLIO DE ANÁLISIS DE DATOS',12,'#AACFC0',700),txt(63,762,'Ventas · productos · clientes · calidad',17,'#E0ECE4'));
b.push(txt(540,91,'ONLINE RETAIL     /     CASO DE ESTUDIO 01',13,teal,700),txt(540,159,'Las ventas, en perspectiva.',40,ink,700));
b.push(txt(540,199,'Datos históricos de comercio minorista. Diciembre 2010 – diciembre 2011.',16,muted));
for(const [x,w,label,value,accent] of [[540,372,'VENTAS NETAS DE PRODUCTOS','£'+(r.overall.NetGBP/1e6).toFixed(2).replace('.',',')+' M',true],[932,220,'PEDIDOS',num(r.overall.Orders),false],[1172,216,'COMPRADORES',num(r.overall.Customers),false]]){
 b.push(`<rect x="${x}" y="247" width="${w}" height="116" rx="16" fill="${accent?teal:'#FFFFFF'}"/>`,txt(x+24,280,label,11,accent?'#D3E8DE':muted,700),txt(x+24,331,value,36,accent?'#FFFFFF':ink,700));
}
b.push(`<rect x="540" y="392" width="848" height="323" rx="18" fill="#FFFFFF"/>`,txt(566,432,'Evolución de las ventas netas',20,ink,700),txt(566,458,'GBP · meses completos y último mes parcial',13,muted));
const pts=r.monthly.map((m,i)=>[614+i*59.5,655-m.NetGBP/1600000*158]);
for(const [val,label] of [[0,'£0'],[750000,'£0,75 M'],[1500000,'£1,5 M']]){const y=655-val/1600000*158;b.push(`<path d="M614 ${y}H1330" stroke="#E9EEEA"/>`,txt(566,y+4,label,10,muted));}
b.push(`<path d="M${pts.slice(0,12).map(p=>p.join(',')).join(' L')}" fill="none" stroke="${teal}" stroke-width="3" stroke-linecap="round"/>`);
b.push(`<path d="M${pts[11]} L${pts[12]}" fill="none" stroke="${coral}" stroke-width="3" stroke-dasharray="6 5"/>`);
pts.forEach(([x,y],i)=>{b.push(`<circle cx="${x}" cy="${y}" r="4" fill="${i===12?coral:teal}"/>`);if(i%3===0)b.push(txt(x-19,681,['dic 10','mar 11','jun 11','sep 11','dic 11'][i/3],11,muted));});
b.push(txt(540,755,'PYTHON   /   SQL   /   POWER BI   /   EXCEL',13,teal,700),txt(540,792,'Fuente: UCI · CC BY 4.0. Diciembre de 2011 incluye solo los días 1–9.',13,muted));
b.push('</svg>');
await fs.writeFile(path.join(out,'portada.svg'),b.join(''));
await sharp(Buffer.from(b.join(''))).png().toFile(path.join(out,'portada.png'));
let diagram=[`<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="340" viewBox="0 0 1200 340"><rect width="1200" height="340" rx="16" fill="${paper}"/>`];
const node=(x,y,w,label,sub,dark=false)=>{
 diagram.push(`<rect x="${x}" y="${y}" width="${w}" height="76" rx="12" fill="${dark?ink:'#FFFFFF'}"/>`,txt(x+18,y+31,label,17,dark?'#FFFFFF':ink,700),txt(x+18,y+55,sub,12,dark?'#C8DED1':muted));
};
diagram.push(txt(30,40,'DE LA FUENTE A LA DECISIÓN',13,teal,700));
diagram.push(`<path d="M242 165H278 M490 165H522 M754 165H800 M640 165V271H800" fill="none" stroke="${teal}" stroke-width="2"/>`);
node(30,126,212,'Excel original','541.909 líneas · UCI');node(278,126,212,'Python','Limpieza, reglas y controles',true);
node(522,126,232,'Datos preparados','CSV · agregados · SQLite');node(800,83,364,'Power BI + Excel','Exploración de ventas y calidad');
diagram.push(`<path d="M785 165V121H800" fill="none" stroke="${teal}" stroke-width="2"/>`);
node(800,232,364,'Informe ejecutivo','Hallazgos, límites y acciones');
diagram.push('</svg>');await fs.writeFile(path.join(out,'flujo.svg'),diagram.join(''));
console.log('Editorial cover and reproducible pipeline diagram generated. Not Power BI screenshots.');
