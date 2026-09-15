/* MIT. Calculations stay local. Videos connect only after consent. */
(() => {
  'use strict';
  const L=window.LESSON,D=window.COURSE_DATA,M=window.METRO,T=window.TAXI,C=window.TRAFFIC_CLASSROOM;
  const $=(q,r=document)=>r.querySelector(q), $$=(q,r=document)=>[...r.querySelectorAll(q)];
  const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const fmt=(n,d=0)=>n==null||!Number.isFinite(n)?'无记录':n.toLocaleString('zh-CN',{maximumFractionDigits:d,minimumFractionDigits:d});
  const source=k=>L.sources[k];
  let section='start',present=false,slideIndex=0,cleanups=[];
  const store={get(k){try{return JSON.parse(localStorage.getItem(k)||'null');}catch{return null;}},set(k,v){try{localStorage.setItem(k,JSON.stringify(v));}catch{}},remove(k){try{localStorage.removeItem(k);}catch{}}};
  const cite=keys=>(keys||[]).length?`<p class="citation">资料依据：${keys.map(k=>source(k).url?`<a target="_blank" rel="noopener noreferrer" href="${source(k).url}">${esc(source(k).title)}</a>`:esc(source(k).title)).join(' ')}</p>`:'';
  function table(values){return `<div class="table-wrap"><table><thead><tr>${values[0].map(v=>`<th scope="col">${esc(v)}</th>`).join('')}</tr></thead><tbody>${values.slice(1).map(row=>`<tr>${row.map(v=>`<td>${esc(v)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;}
  function graph(host,{labels,series,unit='辆/小时',bars=false,title='数据图'}){
    const w=840,h=330,p={l:75,r:20,t:25,b:55},iw=w-p.l-p.r,ih=h-p.t-p.b;
    const vals=series.flatMap(s=>s.values).filter(v=>v!=null&&Number.isFinite(v));
    const raw=Math.max(...vals,1),power=10**Math.floor(Math.log10(raw)), ymax=Math.ceil(raw/power*1.12)*power;
    const x=i=>p.l+(labels.length<=1?iw/2:i*iw/(labels.length-1)), y=v=>p.t+ih*(1-v/ymax);
    let svg=`<svg class="chart" viewBox="0 0 ${w} ${h}" role="img" aria-label="${esc(title)}"><title>${esc(title)}</title><text x="${p.l}" y="15">${esc(unit)}</text>`;
    for(let j=0;j<=4;j++){const v=ymax*j/4;svg+=`<line class="grid" x1="${p.l}" x2="${w-p.r}" y1="${y(v)}" y2="${y(v)}"/><text x="${p.l-10}" y="${y(v)+5}" text-anchor="end">${fmt(v)}</text>`;}
    const step=labels.length>12?3:1;
    labels.forEach((l,i)=>{if(i%step===0||i===labels.length-1)svg+=`<text x="${bars?p.l+iw*(i+.5)/labels.length:x(i)}" y="${h-20}" text-anchor="middle">${esc(l)}</text>`;});
    series.forEach((s,si)=>{
      if(bars){const slot=iw/labels.length,bw=Math.min(70,slot*.7/series.length);s.values.forEach((v,i)=>{if(v==null)return;const xx=p.l+slot*(i+.5)+(si-series.length/2)*bw;svg+=`<rect x="${xx}" y="${y(v)}" width="${bw-3}" height="${p.t+ih-y(v)}" fill="${s.color}"><title>${esc(labels[i])} ${esc(s.name)}：${fmt(v,1)} ${esc(unit)}</title></rect>`;});}
      else {let path='',last=false;s.values.forEach((v,i)=>{if(v==null){last=false;return;}path+=`${last?'L':'M'}${x(i)},${y(v)} `;last=true;});svg+=`<path d="${path}" fill="none" stroke="${s.color}" stroke-width="3"/>`;s.values.forEach((v,i)=>{if(v!=null)svg+=`<circle cx="${x(i)}" cy="${y(v)}" r="3" fill="${s.color}"><title>${esc(labels[i])} ${esc(s.name)}：${fmt(v,1)} ${esc(unit)}</title></circle>`;});}
    });svg+='</svg>';
    host.innerHTML=`<div class="legend">${series.map(s=>`<span style="--series:${s.color}">${esc(s.name)}</span>`).join('')}</div><div class="chart-box">${svg}</div>`;
  }
  const hourLabels=Array.from({length:24},(_,i)=>i+'时');
  const controls=items=>`<div class="controls">${items.join('')}</div>`;
  const select=(name,label,options,selected)=>`<label>${label}<select name="${name}">${options.map(([v,t])=>`<option value="${v}"${v===selected?' selected':''}>${t}</option>`).join('')}</select></label>`;
  const months=[['all','所有可用月份'],...Array.from({length:12},(_,i)=>[String(i+1),(i+1)+'月'])];
  const days=[['all','全部'],['weekday','平日（周一至周五）'],['weekend','周末（周六、周日）']];
  const weathers=[['all','全部'],['Clear','晴朗 Clear'],['Clouds','多云 Clouds'],['Rain','降雨 Rain'],['Snow','降雪 Snow'],['Mist','薄雾 Mist'],['Thunderstorm','雷暴 Thunderstorm']];
  const state=root=>Object.fromEntries($$('select',root).map(e=>[e.name,e.value]));
  const feedback=(root,text,type='')=>{const e=$('.feedback',root);e.textContent=text;e.className='feedback '+type;};
  const labHeader=(title,real=true)=>`<span class="lab-label">${real?'真实数据 / 固定快照':'课堂练习 / 教学示例'}</span><h3>${title}</h3>`;
  function metroLab(root){
    root.innerHTML=labHeader('探索一天的交通节律')+controls([select('year','年份',['2012','2013','2014','2015','2016','2017','2018'].map(x=>[x,x]),'2018'),select('month','月份',months,'all'),select('day','日期类型',days,'all'),select('weather','天气标签',weathers,'all')])+`<div class="stats"></div><div class="plot"></div><p class="subtle">曲线为每个钟点的平均交通量。平日未剔除节假日。不同天气组可重叠，不做因果解释。</p><div class="feedback" role="status"></div><details><summary>核对每小时数值与样本数</summary><div class="data-table"></div></details><a href="data/metro-2018.csv" download>下载2018年清洁小时数据 CSV</a>`;
    function draw(){const f=state(root),rows=D.filter(M.rows,f),h=D.hourly(rows);let series;
      if(f.day==='all')series=[{name:'平日',color:'#087e82',values:D.hourly(rows.filter(r=>r.day<5)).map(r=>r.value)},{name:'周末',color:'#c07824',values:D.hourly(rows.filter(r=>r.day>=5)).map(r=>r.value)}];
      else series=[{name:f.day==='weekday'?'平日':'周末',color:'#087e82',values:h.map(r=>r.value)}];
      graph($('.plot',root),{labels:hourLabels,series,title:'逐小时平均交通量'});
      $('.stats',root).innerHTML=`<span>有效小时<strong>${fmt(rows.length)}</strong></span><span>均值<strong>${fmt(D.mean(rows.map(r=>r.volume)),1)}</strong>辆/小时</span>`;
      $('.data-table',root).innerHTML=table([['小时','样本数','全部所选样本均值（辆/小时）'],...h.map(r=>[r.hour+':00',r.n,fmt(r.value,1)])]);
      feedback(root,rows.length?`当前筛选实际覆盖 ${rows[0].time} 至 ${rows.at(-1).time}。不补齐缺失小时。2018年只覆盖1至9月，2012年从10月开始。`:'该组合没有记录，请调整月份或天气。空缺不代表流量为零。',rows.length?'':'warn');
    }root.addEventListener('change',draw);draw();
  }
  function weatherLab(root){
    root.innerHTML=labHeader('同一小时再比较天气')+controls([select('month','月份',months,'all'),select('day','日期类型',days,'weekday'),select('hour','钟点',[['all','所有钟点'],...hourLabels.map((x,i)=>[String(i),x])],'all')])+`<div class="plot"></div><div class="stats"></div><div class="feedback" role="status"></div>`;
    function draw(){const f=state(root),r=D.filter(M.rows,{...f,year:'2018'}), groups=['Clear','Rain','Snow'].map(k=>r.filter(x=>x.weather.includes(k)));
      graph($('.plot',root),{labels:['晴朗','降雨','降雪'],series:[{name:'分组均值',color:'#087e82',values:groups.map(g=>D.mean(g.map(x=>x.volume)))}],bars:true,title:'所选时段不同天气的平均流量'});
      $('.stats',root).textContent=groups.map((g,i)=>['晴朗','降雨','降雪'][i]+'：'+g.length+'个小时').join('；');
      feedback(root,'这是条件分组后的描述。它仍未控制全部因素，也没有证明降雨的因果作用。天气标签可以重叠，缺失组保持为空。'+(groups.some(g=>g.length<30)?' 注意：至少一组不足30个小时，结果可能不稳定。':''),groups.some(g=>g.length<30)?'warn':'');
    }root.addEventListener('change',draw);draw();
  }
  function taxiLab(root){
    const names={Bronx:'布朗克斯',Brooklyn:'布鲁克林',Manhattan:'曼哈顿',Queens:'皇后区','Staten Island':'斯塔滕岛',EWR:'EWR机场',Unknown:'未知'};
    root.innerHTML=labHeader('谁出现在绿出租车记录中？')+controls([select('day','日期类型',[['all','全部'],['平日','平日'],['周末','周末']],'all'),select('period','上车时段',[['all','全天'],['night','夜间22:00至次日5:59'],['day','日间6:00至21:59']],'all')])+`<div class="plot"></div><div class="stats"></div><div class="feedback">这里统计行程记录，不能外推为全体居民需求。夜间组按钟点筛选，未拼接成连续“夜晚”。</div><details><summary>查看全部地区与计数</summary><div class="data-table"></div></details><a href="data/taxi-2024-01-aggregated.csv" download>下载汇总数据 CSV</a>`;
    function draw(){const f=state(root),g=new Map(Object.keys(names).map(k=>[k,0]));for(const r of T.rows){const night=r.hour>=22||r.hour<6;if((f.day==='all'||r.daytype===f.day)&&(f.period==='all'||(f.period==='night'?night:!night)))g.set(r.Borough,(g.get(r.Borough)||0)+r.count);}
      const all=[...g].sort((a,b)=>b[1]-a[1]);graph($('.plot',root),{labels:all.slice(0,5).map(([k])=>names[k]),series:[{name:'行程记录数',color:'#087e82',values:all.slice(0,5).map(x=>x[1])}],bars:true,unit:'条',title:'各上车地区的行程记录数（前5位）'});
      $('.stats',root).textContent=`当前筛选 ${fmt(all.reduce((s,r)=>s+r[1],0))} 条记录。图中显示前5位，完整地区见下表。`;
      $('.data-table',root).innerHTML=table([['上车地区','记录数'],...all.map(([k,v])=>[names[k]||k,v])]);
    }root.addEventListener('change',draw);draw();
  }
  function riskLab(root){
    root.innerHTML=labHeader('补充分母，重新比较',false)+controls(['<label>道路A事故数（起/年）<input name="a" type="number" min="0" max="10000" value="20"></label>','<label>A暴露量（万车公里/年）<input name="ae" type="number" min="1" max="100000" value="1000"></label>','<label>道路B事故数（起/年）<input name="b" type="number" min="0" max="10000" value="10"></label>','<label>B暴露量（万车公里/年）<input name="be" type="number" min="1" max="100000" value="200"></label>'])+'<div class="plot"></div><div class="feedback" role="status"></div><p class="subtle">每百万车公里事故数 = 事故数 ÷ 暴露量（万车公里）×100。相同观察期；比率不代表统计显著差异。</p>';
    function draw(){const inputs=$$('input',root);if(inputs.some(e=>e.value===''||!e.checkValidity())){feedback(root,'请填写非负事故数与大于零的暴露量。','error');$('.plot',root).innerHTML='';return;}
      const [a,ae,b,be]=inputs.map(e=>+e.value),ra=a/ae*100,rb=b/be*100;
      graph($('.plot',root),{labels:['道路A','道路B'],series:[{name:'暴露量标准化比率',values:[ra,rb],color:'#c07824'}],bars:true,unit:'起/百万车公里',title:'教学示例事故比率'});
      feedback(root,`A：${fmt(ra,2)}，B：${fmt(rb,2)} 起/百万车公里。${ra===rb?'两者比率相等。':(ra>rb?'A':'B')+'的比率较高。'}这些是教学输入值，不对应实际道路。事故口径、路段环境与小样本不确定性仍需核对。`);
    }root.addEventListener('input',draw);draw();
  }
  function leakageLab(root){
    const items=[['7:55已接收的道路速度',true,'预测时已经可获得。'],['事故发生于7:50，但8:40才上报',false,'8:00系统尚未收到上报，不能作为当时输入。'],['7:30发布的8:30天气预报',true,'这是当时已知的预报，不是未来实测。'],['事后补录的8:30实际降雨',false,'预测时尚未观察到。'],['截至前一天生成的星期几标签',true,'日历信息可以事先确定。']];
    root.innerHTML=labHeader('选择8:00时可以使用的输入',false)+items.map(([s],i)=>`<div class="question-row"><label><input type="checkbox" value="${i}">${s}</label></div>`).join('')+'<button class="primary check">检查选择</button><div class="feedback" role="status" hidden></div>';
    $('.check',root).onclick=()=>{const chosen=new Set($$('input:checked',root).map(e=>+e.value));let n=0;const detail=items.map(([s,v,e],i)=>{const ok=chosen.has(i)===v;n+=+ok;return (ok?'正确：':'需调整：')+s+'。'+e;});$('.feedback',root).hidden=false;feedback(root,`判断正确 ${n}/${items.length}。`+detail.join(' '),n===items.length?'':'warn');};
  }
  function tasksLab(root){
    const items=[['统计昨日排队次数','描述与发现'],['判断当前是否存在行人','分类与识别'],['预测明早进口流量','回归与预测'],['给全天流量曲线分组','聚类'],['选择满足行人过街约束的信号时长','优化与决策']];
    const opts=['请选择','描述与发现','分类与识别','回归与预测','聚类','优化与决策'];
    root.innerHTML=labHeader('任务与输出配对',false)+items.map(([q],i)=>`<div class="question-row"><label for="task-${i}">${i+1}. ${q}</label><select id="task-${i}">${opts.map(x=>`<option>${x}</option>`).join('')}</select></div>`).join('')+'<button class="primary check">核对任务</button><div class="feedback" role="status" hidden></div>';
    $('.check',root).onclick=()=>{const choices=$$('select',root).map(e=>e.value),n=items.filter((r,i)=>r[1]===choices[i]).length;$('.feedback',root).hidden=false;feedback(root,`正确 ${n}/${items.length}。`+items.map(([q,a])=>q+'：'+a).join('；'),n===items.length?'':'warn');};
  }
  function aggregationLab(root){
    root.innerHTML=labHeader('同一天，换一种时间粒度')+controls(['<label>日期（2018年1月至9月）<input type="date" name="date" min="2018-01-01" max="2018-09-30" value="2018-09-10"></label>',select('bin','聚合宽度',[['1','1小时'],['3','3小时'],['6','6小时']],'1')])+'<div class="plot"></div><div class="feedback" role="status"></div>';
    function draw(){const date=$('input',root).value,bin=+$('select',root).value,rs=M.rows.filter(r=>r.time.startsWith(date+' ')),hourly=new Map(rs.map(r=>[r.hour,r.volume]));const avg=[];for(let start=0;start<24;start+=bin){const g=rs.filter(r=>r.hour>=start&&r.hour<start+bin);avg.push(g.length===bin?D.mean(g.map(r=>r.volume)):null);}
      graph($('.plot',root),{labels:hourLabels,series:[{name:'原始小时量',color:'#98b5b1',values:hourLabels.map((_,i)=>hourly.get(i)??null)},{name:bin+'小时窗口均值',color:'#087e82',values:hourLabels.map((_,i)=>avg[Math.floor(i/bin)])}],title:'真实小时交通量按窗口聚合'});
      feedback(root,`所选日期有 ${rs.length}/24 个小时标签。仅当窗口内全部小时齐备时计算均值。均值单位仍为辆/小时，不是窗口车辆总量。窗口越宽，短时变化通常越不明显。原数据为小时记录，不能据此恢复分钟级变化。`,rs.length===24?'':'warn');
    }root.addEventListener('change',draw);draw();
  }
  function baselineLab(root){C.mount(root,'baseline',{graph,table,fmt,cleanups});}
  function datasetLab(root){
    const rows=[['高速公路车辆轨迹','对象与道路环境不匹配。可以研究车辆运动，但无法直接回答校园行人夜间过街。'],['白天街景语义分割','能提供静态语义信息，但缺少夜间条件和连续行为信息。'],['MOT17夜间街道视频与独立标注','可检验夜间检测、关联和通行计数，但不是校园过街样本。不能直接解释校园冲突风险。需要另行定义校园断面、时段、行人与车辆冲突资料。'],['SinD天津地面轨迹','可练习车辆跟踪与跨线规则；这是平滑地面轨迹，不是原始视频，不用于评价YOLOX检测精度。']];
    root.innerHTML=labHeader('选择候选数据，说明还缺什么',false)+controls([select('data','候选数据',rows.map((r,i)=>[String(i),r[0]]),'0')])+'<div class="feedback" role="status"></div>';
    function draw(){feedback(root,rows[+$('select',root).value][1]);}root.addEventListener('change',draw);draw();
  }
  function countingLab(root){
    let f=0;const frames=[[{id:'A',x:160,y:90}],[{id:'A',x:310,y:90}],[{id:'A',x:510,y:90},{id:'B',x:210,y:180}]];
    root.innerHTML=labHeader('逐帧观察：跨线事件与重复框',false)+controls(['<button class="prev">上一帧</button>','<button class="next-frame">下一帧</button>','<button class="reset-frame">重置</button>'])+'<canvas width="760" height="260" aria-label="三帧车辆坐标教学示意">A从计数线左侧移动到右侧，B尚未跨线。</canvas><div class="stats" role="status"></div><div class="feedback">计数线位于x=400。规则：同一身份从左向右跨线，计1次。只出现于画面内并不代表已经通行。此处不运行检测模型。</div>';
    function draw(){const ctx=$('canvas',root).getContext('2d');ctx.clearRect(0,0,760,260);ctx.fillStyle='#f0f4f1';ctx.fillRect(20,25,720,210);ctx.strokeStyle='#bd6b23';ctx.setLineDash([7,5]);ctx.beginPath();ctx.moveTo(400,25);ctx.lineTo(400,235);ctx.stroke();ctx.setLineDash([]);ctx.font='18px Microsoft YaHei';ctx.fillStyle='#8c4e19';ctx.fillText('计数线',415,48);for(const p of frames[f]){ctx.fillStyle=p.id==='A'?'#087e82':'#cc852b';ctx.fillRect(p.x-35,p.y-22,70,44);ctx.fillStyle='white';ctx.fillText(p.id,p.x-6,p.y+6);}
      const n=frames.slice(0,f+1).reduce((s,v)=>s+v.length,0),ids=new Set(frames.slice(0,f+1).flat().map(p=>p.id)).size,cross=f===2?1:0;
      $('.stats',root).innerHTML=`<span>第<strong>${f+1}</strong>帧</span><span>累计框数<strong>${n}</strong></span><span>出现过的身份<strong>${ids}</strong></span><span>已跨线车辆<strong>${cross}</strong></span>`;$('.prev',root).disabled=f===0;$('.next-frame',root).disabled=f===2;
    }$('.prev',root).onclick=()=>{f=Math.max(0,f-1);draw();};$('.next-frame',root).onclick=()=>{f=Math.min(2,f+1);draw();};$('.reset-frame',root).onclick=()=>{f=0;draw();};draw();
  }
  function waveLab(root){
    root.innerHTML=labHeader('观察移动的减速区域',false)+controls(['<label>演示波幅<input name="amp" type="range" min="0" max="100" value="65"></label>','<button class="pause">开始动画</button>','<button class="restart">重置</button>'])+'<canvas width="760" height="350" aria-label="环道减速波概念动画">车辆顺时针运动，减速区域逆时针传播。</canvas><p class="subtle">预设移动波的概念动画，非实测轨迹或经过标定的交通模型。滑块控制图示波幅，不估计真实反应时间和通行能力。</p><div class="feedback">观察：车辆顺时针前进，而橙色的减速区域向相反方向传播。把波幅设为0，比较颜色和间距。</div>';
    const ctx=$('canvas',root).getContext('2d');let t=0,running=false,last=0,handle;
    function draw(){ctx.clearRect(0,0,760,350);const cx=380,cy=175,rx=220,ry=117;ctx.strokeStyle='#d4dfd9';ctx.lineWidth=40;ctx.beginPath();ctx.ellipse(cx,cy,rx,ry,0,0,2*Math.PI);ctx.stroke();const amp=+$('input',root).value/100;
      for(let i=0;i<24;i++){const base=i/24*2*Math.PI+t*.24,wave=base+t*.5,angle=base-amp*.22*Math.sin(wave),slow=(1+Math.cos(wave))/2*amp;ctx.fillStyle=slow>.45?'#c07824':'#087e82';ctx.beginPath();ctx.arc(cx+rx*Math.cos(angle),cy+ry*Math.sin(angle),8,0,2*Math.PI);ctx.fill();}
      ctx.fillStyle='#153b43';ctx.font='20px Microsoft YaHei';ctx.textAlign='center';ctx.fillText('车辆：顺时针',cx,cy-12);ctx.fillText('减速区域：逆时针',cx,cy+24);ctx.textAlign='left';
    }
    function tick(now){if(running){t+=Math.min((now-last)/1000,.05);draw();}last=now;handle=requestAnimationFrame(tick);}
    $('.pause',root).onclick=()=>{running=!running;$('.pause',root).textContent=running?'暂停动画':'开始动画';};$('.restart',root).onclick=()=>{t=0;running=false;$('.pause',root).textContent='开始动画';draw();};$('input',root).oninput=draw;draw();handle=requestAnimationFrame(tick);cleanups.push(()=>cancelAnimationFrame(handle));
  }
  function quizLab(root){
    const saved=store.get('traffic-ch1-quiz-v1')||{};
    root.innerHTML=labHeader('8题课堂自测',false)+L.quiz.map((q,i)=>`<div class="quiz-item"><fieldset><legend>${i+1}. ${q.q}</legend>${q.a.map((a,j)=>`<label><input type="radio" name="quiz-${i}" value="${j}"${saved[i]===j?' checked':''}>${a}</label>`).join('')}</fieldset><div class="feedback" hidden></div></div>`).join('')+'<div class="quiz-actions"><button class="primary submit">提交并查看解释</button><button class="reset-quiz">清除本机答案</button></div><div class="feedback score" role="status" hidden></div><p class="subtle">只在本浏览器保存选择。不会发送给老师，也不构成正式考试成绩。</p>';
    root.addEventListener('change',()=>{const a={};L.quiz.forEach((_,i)=>{const r=$(`input[name="quiz-${i}"]:checked`,root);if(r)a[i]=+r.value;});store.set('traffic-ch1-quiz-v1',a);});
    $('.submit',root).onclick=()=>{let n=0,answered=0;$$('.quiz-item',root).forEach((e,i)=>{const r=$('input:checked',e),ok=r&&+r.value===L.quiz[i].correct;n+=+!!ok;answered+=+!!r;const f=$('.feedback',e);f.hidden=false;f.className='feedback '+(ok?'':'warn');f.textContent=(ok?'回答正确。':r?'还需调整。':'尚未作答。')+' '+L.quiz[i].explain;});const f=$('.score',root);f.hidden=false;f.textContent=`已作答 ${answered}/8，正确 ${n}/8。请优先复习带提示的题目。`;};
    $('.reset-quiz',root).onclick=()=>{store.remove('traffic-ch1-quiz-v1');$$('input',root).forEach(e=>e.checked=false);$$('.feedback',root).forEach(e=>e.hidden=true);};
  }
  const labs={metro:metroLab,weather:weatherLab,taxi:taxiLab,risk:riskLab,leakage:leakageLab,tasks:tasksLab,aggregation:aggregationLab,baseline:baselineLab,dataset:datasetLab,counting:countingLab,wave:waveLab,quiz:quizLab};
  C.labNames.forEach(key=>{labs[key]=root=>C.mount(root,key,{graph,table,fmt,cleanups});});
  function videoHTML(i){const v=L.videos[i];return `<div class="video-box" data-video="${i}"><h3>${v.title}</h3><p>${v.budget}。${v.prompt}</p><button class="load-video">同意连接YouTube并加载视频</button><div class="video-links"><a href="https://www.youtube.com/watch?v=${v.id}" target="_blank" rel="noopener noreferrer">在官方平台打开</a><a href="${source(v.source).url}" target="_blank" rel="noopener noreferrer">机构原始发布页</a></div><p class="small">未加载前不会连接视频平台。播放可能受校园网络或平台嵌入限制。</p></div><details><summary>无法播放时的课堂备用讲解</summary><p>${v.fallback}</p></details>`;}
  function staticChart(root,key){if(key==='night'){const rs=D.filter(M.rows),h=[0,1,2,3,4,5];graph(root,{labels:h.map(i=>i+'时'),series:[{name:'平日',color:'#087e82',values:D.hourly(rs.filter(r=>r.day<5)).slice(0,6).map(r=>r.value)},{name:'周末',color:'#c07824',values:D.hourly(rs.filter(r=>r.day>=5)).slice(0,6).map(r=>r.value)}],title:'凌晨0至5时平日与周末的平均交通量'});}}
  function article(s,i){return `<article class="lesson-article" id="slide-${i}" data-slide="${i}"><div class="case-label">${s.case?esc(s.case):'CHAPTER 01 / '+esc(s.section==='start'?'导览':s.section)}</div><h2>${esc(s.title)}</h2>${s.lead?`<p class="lead">${esc(s.lead)}</p>`:''}${s.numbers?`<div class="numbers">${s.numbers.map(([v,l])=>`<div><strong>${v}</strong><span>${l}</span></div>`).join('')}</div>`:''}${s.table?table(s.table):''}${s.body?`<div class="body-lines">${s.body.map((v,j)=>`<p class="body-line">${['rows','steps','closing'].includes(s.kind)?`<span class="index">0${j+1}</span>`:''}${esc(v)}</p>`).join('')}</div>`:''}${s.kind==='video'?videoHTML(s.video):''}${s.chart==='night'?'<div data-static-chart="night"></div>':''}${s.lab?`<div class="lab" data-lab="${s.lab}"></div>`:''}${s.link?`<p><a href="${source(s.link).url}" target="_blank" rel="noopener noreferrer">打开${esc(source(s.link).title)}</a></p>`:''}${s.takeaway?`<div class="takeaway">${esc(s.takeaway)}</div>`:''}${cite(s.sources)}${s.projects?C.bridge(s.projects,s.nextTask||''):''}<details class="teacher-note"><summary>教师提示与课堂追问</summary><p>${esc(s.notes||'')}</p></details></article>`;}
  function home(){return `<section class="hero"><p class="eyebrow">交通运输工程 / 第1章开放课堂</p><h1>从交通问题<br>走向可验证的实践</h1><p>怎样调查早高峰？<br>如何准备出行服务？<br>哪些地点需要现场核查？</p><span class="caption">概念插画，非实际地点影像</span></section><div class="intro-line"><span><strong>5</strong>类交通任务</span><span><strong>8</strong>章实践衔接</span><span><strong>${L.slides.length}</strong>页课堂讲义</span></div><p>沿教材1.1至1.6建立问题意识：先明确交通对象、指标与工程用途，再进入章节算法。90分钟可按道路监测主线讲授，并选一类任务深入；其他分支留作课后探索。</p><div class="controls"><a class="download" href="#1.1">开始概念课堂</a><a href="offline-course.zip" download>下载新版离线课堂</a><a href="chapter-01.pptx" download>基础PPT（原版）</a></div><p class="subtle">本轮更新交互网页与离线课堂；基础PPT保留原版，不含新增项目衔接。已有项目和个人笔记不变。</p>${C.home()}${article(L.slides[1],1)}<section class="lesson-article"><p class="eyebrow">课堂问题索引</p><h2>观察、计算与交通解释</h2><div class="case-list">${L.slides.map((s,i)=>s.case?`<a href="#s${i}"><span>${esc(s.case.split(' ')[0])}</span>${esc(s.title)}</a>`:'').join('')}</div></section><p class="subtle">道路和出租车基础交互可离线使用；共享单车与时序模型评价读取与主项目一致的真实计算快照。真实夜间视频及完整章节实践需联网。概念动画不冒充交通仿真或实测结果。</p>`;}
  function render(){cleanups.forEach(f=>f());cleanups=[];
    document.body.classList.toggle('present',present);$('.present-nav').hidden=!present;
    $('#chapter-nav').innerHTML=L.sections.map(([id,t,time])=>`<a class="chapter-link${section===id?' active':''}" href="#${id}"${section===id?' aria-current="page"':''}><b>${id==='start'?'导览':id} ${t}</b><small>${time}</small></a>`).join('');
    const sec=L.sections.find(s=>s[0]===section)||L.sections[0];
    if(present){const s=L.slides[slideIndex];$('#content').innerHTML=slideIndex===0?`<section class="hero"><p class="eyebrow">第1章 / 绪论</p><h1>交通数据挖掘</h1><p>交通问题如何变成<br>可检验的数据分析任务</p><span class="caption">概念插画</span></section>`:article(s,slideIndex);$('#page-label').textContent=`${slideIndex+1} / ${L.slides.length}`;$('#previous').disabled=slideIndex===0;$('#next').disabled=slideIndex===L.slides.length-1;}
    else if(section==='start')$('#content').innerHTML=home();
    else {const pos=L.sections.findIndex(s=>s[0]===section),items=L.slides.map((s,i)=>[s,i]).filter(([s])=>s.section===section);$('#content').innerHTML=`<header class="section-title"><p class="eyebrow">第一章 / ${section}</p><h1>${sec[1]}</h1><p>建议 ${sec[2]}。可展开教师提示，或进入课堂投影逐页讲授。</p></header>`+items.map(([s,i])=>article(s,i)).join('')+`<nav class="next-chapter" aria-label="相邻小节"><a href="#${L.sections[pos-1][0]}">上一节：${L.sections[pos-1][1]}</a>${pos<L.sections.length-1?`<a href="#${L.sections[pos+1][0]}">下一节：${L.sections[pos+1][1]}</a>`:'<a href="#start">返回导览</a>'}</nav>`;}
    $$('[data-lab]').forEach(e=>labs[e.dataset.lab](e));$$('[data-static-chart]').forEach(e=>staticChart(e,e.dataset.staticChart));
    $$('.load-video').forEach(b=>b.onclick=()=>{const box=b.closest('[data-video]'),v=L.videos[+box.dataset.video];b.remove();const frame=document.createElement('iframe');frame.src=`https://www.youtube-nocookie.com/embed/${v.id}`;frame.title=v.title;frame.allow='fullscreen; picture-in-picture';frame.allowFullscreen=true;frame.referrerPolicy='strict-origin-when-cross-origin';box.prepend(frame);});
    if(location.protocol==='file:'){
      $$('a[href="offline-course.zip"]').forEach(a=>a.hidden=true);
      $$('a[href="../"]').forEach(a=>a.href='https://lilinchao.github.io/traffic-book-practice/open-course/');
    }
  }
  function route(){let h;try{h=decodeURIComponent(location.hash.slice(1));}catch{h='start';}if(h==='plan')h='s'+L.slides.findIndex(s=>s.lab==='brief');if(h==='pathways')h='s'+L.slides.findIndex(s=>s.lab==='pathways');let target=null;if(/^s\d+$/.test(h)){target=Math.min(L.slides.length-1,+h.slice(1));slideIndex=target;section=L.slides[target].section;}else if(L.sections.some(s=>s[0]===h)){section=h;slideIndex=L.slides.findIndex(s=>s.section===section);}else {section='start';slideIndex=0;}
    render();if(target!=null&&!present)setTimeout(()=>$(`#slide-${target}`)?.scrollIntoView({block:'start',behavior:'instant'}),0);else window.scrollTo({top:0,behavior:'instant'});
  }
  function setPresent(v){present=v;if(v&&section==='start')slideIndex=0;render();window.scrollTo({top:0,behavior:'instant'});$('#present-toggle').textContent=v?'退出投影':'课堂投影';}
  function move(n){slideIndex=Math.max(0,Math.min(L.slides.length-1,slideIndex+n));section=L.slides[slideIndex].section;history.replaceState(null,'','#s'+slideIndex);render();window.scrollTo({top:0,behavior:'instant'});}
  $('#present-toggle').onclick=()=>setPresent(!present);$('#leave-present').onclick=()=>setPresent(false);$('#previous').onclick=()=>move(-1);$('#next').onclick=()=>move(1);
  document.addEventListener('keydown',e=>{if(!present||$('#source-dialog').open||/INPUT|SELECT|TEXTAREA|BUTTON/.test(e.target.tagName))return;if(e.key==='ArrowRight'||e.key==='PageDown'){e.preventDefault();move(1);}if(e.key==='ArrowLeft'||e.key==='PageUp'){e.preventDefault();move(-1);}if(e.key==='Escape')setPresent(false);});
  $('#source-body').innerHTML=`<p>本课件基于用户提供的《交通数据挖掘理论与应用》最新清洁合稿第一章。基础数据整理于2026年9月14日，交通任务衔接版更新于9月15日。通过project-protocols.js与章节真实计算结果生成证据快照；第6章采用共同2169目标，不混用旧6533小时口径。</p><p><strong>代码 MIT；原创课程文字 CC BY-SA 4.0。</strong>第三方数据、论文和视频遵循各自条款，不能因本课程开源而视为可任意再分发。</p>${Object.values(L.sources).map(s=>`<div class="source-item"><strong>${s.url?`<a href="${s.url}" target="_blank" rel="noopener noreferrer">${esc(s.title)}</a>`:esc(s.title)}</strong><p>${esc(s.note)}</p></div>`).join('')}<h3>数据处理记录</h3><p>I-94：原始 ${M.meta.rawRows} 行，合并为 ${M.meta.hours} 个不同本地小时标签，未发现同小时交通量冲突。原始时区按来源说明理解，本课件不重建UTC时间轴。2018年截至9月30日，且存在少量时间缺口。</p><p>TLC：${T.meta.rawRows} 条原始行程，剔除上车时间不在2024年1月的2条，保留 ${T.meta.retainedRows} 条。未依据乘客人数、车费、距离做清洗。网页只发布地区、日类型与小时的计数汇总。</p><p>封面由内置图像工具生成：蓝调夜色城市路口俯视概念插画。文件为cover.png，不作为实证资料。完整提示词与许可说明见<a href="README.md">课程说明</a>。</p><p>MOT17夜间视频采用课程服务器上的许可播放副本，需联网；来源、标注和许可见夜间实验说明。其余研究视频采用官方发布入口，嵌入失败时可打开机构原始页面。无法联网时可使用各视频后的文字提问与概念动画。网页不上传学生数据，答题选择只保存到当前浏览器。</p><p><a href="practice/reproduce.py" download>下载基础数据整理脚本（含旧版基线，勿与新主实验混排）</a> · <a href="data/metro-2018.csv" download>下载I-94样本</a> · <a href="data/taxi-2024-01-aggregated.csv" download>下载TLC汇总</a></p>`;
  $('#sources-toggle').onclick=()=>$('#source-dialog').showModal();$('#close-sources').onclick=()=>$('#source-dialog').close();window.addEventListener('hashchange',route);route();
})();
