export const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export const fmt=v=>v==null?'无数据':typeof v==='number'?(v!==0&&Math.abs(v)<.01?v.toExponential(3):v.toLocaleString('zh-CN',{maximumFractionDigits:3})):esc(v);
export function table(columns,rows,limit=100){return `<div class="table-scroll"><table><thead><tr>${columns.map(c=>`<th scope="col">${esc(c)}</th>`).join('')}</tr></thead><tbody>${rows.slice(0,limit).map(r=>`<tr>${r.map(v=>`<td>${fmt(v)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>${rows.length>limit?`<p class="small">预览${limit}行，完整${rows.length}行请导出。</p>`:''}`;}
const colors=['#087e82','#b66c24','#7855a2','#3572b0','#9d4141','#688928'];
export function plot(c){
 if(!c)return '';
 const interval=c.type==='interval',vals=interval?c.points.flatMap(p=>[p.lower,p.upper]).concat(c.reference):c.series.flatMap(s=>s.values).filter(Number.isFinite);
 if(!vals.length)return '<p>无可绘制数据。</p>';
 const W=860,H=365,L=90,R=20,T=28,B=75,lo=interval?Math.min(...vals):Math.min(0,...vals),hi=Math.max(...vals),gap=(hi-lo||1)*.08,min=lo-(interval?gap:0),max=hi+gap;
 const y=v=>H-B-(v-min)/(max-min)*(H-T-B),x=i=>L+i*(W-L-R)/Math.max(1,c.labels.length-1),tx=v=>L+(v-min)/(max-min)*(W-L-R),ry=i=>T+30+i*(H-T-B-45)/Math.max(1,c.labels.length-1);
 let content='';
 if(interval){
  content+=c.points.map((p,i)=>`<text x="${L-8}" y="${ry(i)+5}" text-anchor="end">${esc(c.labels[i])}</text><line x1="${tx(p.lower)}" x2="${tx(p.upper)}" y1="${ry(i)}" y2="${ry(i)}" stroke="${colors[0]}" stroke-width="5"/><circle cx="${tx(p.estimate)}" cy="${ry(i)}" r="6" fill="${colors[0]}"><title>${fmt(p.estimate)} [${fmt(p.lower)}, ${fmt(p.upper)}]</title></circle>`).join('');
  content+=`<line x1="${tx(c.reference)}" x2="${tx(c.reference)}" y1="${T}" y2="${H-B}" stroke="${colors[1]}" stroke-dasharray="5 4"/>`;
  for(let i=0;i<5;i++){const v=min+(max-min)*i/4;content+=`<text x="${tx(v)}" y="${H-B+27}" text-anchor="middle">${fmt(Number(v.toPrecision(3)))}</text>`;}
 }else{
  for(let i=0;i<5;i++){const v=min+(max-min)*i/4;content+=`<line x1="${L}" x2="${W-R}" y1="${y(v)}" y2="${y(v)}" stroke="#dce4e1"/><text x="${L-10}" y="${y(v)+5}" text-anchor="end">${fmt(Number(v.toPrecision(3)))}</text>`;}
  const step=(W-L-R)/c.labels.length;
  c.series.forEach((s,j)=>{
   if(c.type==='bars'){const bw=step*.76/c.series.length;content+=s.values.map((v,i)=>v==null?'':`<rect x="${L+i*step+step*.12+j*bw}" y="${y(Math.max(v,0))}" width="${Math.max(.5,bw-1)}" height="${Math.abs(y(v)-y(0))}" fill="${colors[j%colors.length]}"><title>${esc(c.labels[i])} ${esc(s.name)} ${fmt(v)}</title></rect>`).join('');}
   else{let active=false;content+=`<path fill="none" stroke="${colors[j%colors.length]}" stroke-width="2.8" d="${s.values.map((v,i)=>{if(v==null){active=false;return '';}const op=active?'L':'M';active=true;return `${op}${x(i)},${y(v)}`;}).join(' ')}"/>`;}
  });
  const ticks=new Set(Array.from({length:Math.min(8,c.labels.length)},(_,i)=>Math.round(i*(c.labels.length-1)/Math.max(1,Math.min(8,c.labels.length)-1))));content+=c.labels.map((v,i)=>!ticks.has(i)?'':`<text x="${c.type==='bars'?L+(i+.5)*step:x(i)}" y="${H-B+27}" text-anchor="${i===0?'start':i===c.labels.length-1?'end':'middle'}">${esc(v)}</text>`).join('');
 }
 return `<figure><figcaption>${esc(c.unit)}</figcaption><div class="plot-scroll"><svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(c.unit)}；精确结果见数据表"><title>${esc(c.unit)}</title>${content}</svg></div><div class="legend">${interval?'<span>圆点：样本均值；横线：95%区间；虚线：文件参考均值</span>':c.series.map((s,i)=>`<span style="color:${colors[i%colors.length]}">${esc(s.name)}</span>`).join('')}</div></figure>`;
}
export function mapPlot(r){
 if(!r.map)return '';
 const pts=r.map,W=860,H=400,L=70,B=52,T=16,R=20,xs=pts.map(p=>p[0]),ys=pts.map(p=>p[1]),x0=Math.min(...xs),x1=Math.max(...xs),y0=Math.min(...ys),y1=Math.max(...ys),k=Math.min((W-L-R)/(x1-x0||1),(H-B-T)/(y1-y0||1));
 const x=a=>L+(a-x0)*k,y=b=>H-B-(b-y0)*k,max=Math.max(...pts.map(p=>p[2]));
 let svg=pts.map(([a,b,v])=>`<circle cx="${x(a)}" cy="${y(b)}" r="${r.mapMode==='density'?3:1.8}" fill="${r.mapMode==='density'?colors[0]:v===-1?'#a6afad':colors[v%colors.length]}" opacity="${r.mapMode==='density'?.1+.9*v/max:.6}"><title>x=${fmt(a)}, y=${fmt(b)}, 值=${fmt(v)}</title></circle>`).join('');
 if(Number.isFinite(r.line)&&r.line>=x0&&r.line<=x1)svg+=`<line x1="${x(r.line)}" x2="${x(r.line)}" y1="${y(y1)}" y2="${y(y0)}" stroke="#b66c24" stroke-width="3" stroke-dasharray="6 4"/>`;
 for(let i=0;i<5;i++){const a=x0+(x1-x0)*i/4,b=y0+(y1-y0)*i/4;svg+=`<text x="${x(a)}" y="${H-B+25}" text-anchor="middle">${fmt(+a.toFixed(1))}</text><text x="${L-8}" y="${y(b)+4}" text-anchor="end">${fmt(+b.toFixed(1))}</text>`;}
 return `<figure><figcaption>${esc(r.mapLabel)}</figcaption><div class="plot-scroll"><svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(r.mapLabel)}"><title>${esc(r.mapLabel)}</title>${svg}</svg></div><p class="small">${r.mapMode==='density'?'颜色深浅在本次结果内归一化，跨带宽请比较数值表。':'颜色循环表示标签，灰色表示噪声；不同颜色不代表风险等级。'} 横纵轴保持等比例。</p></figure>`;
}
