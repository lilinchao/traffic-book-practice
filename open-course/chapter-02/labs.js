(function() {
  'use strict';
  const C=ClassroomCore,D=OBSERVATIONS,M=C.organize(D.rows);window.CLASSROOM_MODEL=M;
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const fmt=(v,d=0)=>v===null?'缺测':Number(v).toLocaleString('zh-CN',{maximumFractionDigits:d});
  const table=(cols,rows)=>`<div class="table-wrap"><table><thead><tr>${cols.map(x=>`<th scope="col">${esc(x)}</th>`).join('')}</tr></thead><tbody>${rows.map(r=>`<tr>${r.map(v=>`<td>${esc(v)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
  const stats=items=>`<div class="stats">${items.map(([k,v])=>`<div><strong>${esc(v)}</strong><span>${esc(k)}</span></div>`).join('')}</div>`;
  const yearSelect=(selected=2017)=>`<label>资料年份<select name="year">${Array.from({length:7},(_,i)=>2012+i).map(y=>`<option ${y===selected?'selected':''}>${y}</option>`).join('')}</select></label>`;
  const feedback=(text,kind='')=>`<div class="feedback ${kind}" role="status">${esc(text)}</div>`;
  function plot(series,{min=0,max=null,unit='辆/小时',title='交通量对照',bars=false}={}){
    const all=series.flatMap(s=>s.values).filter(v=>v!==null);
    max=max??Math.max(...all,1)*1.12;
    if(max<=min)max=min+1;
    const w=800,h=310,l=72,r=20,t=30,b=45,n=series[0].values.length;
    const x=i=>l+(w-l-r)*(i+.5)/n,y=v=>h-b-(v-min)/(max-min)*(h-t-b);
    const colors=['#087e82','#c27527'];
    let parts=`<text x="${l}" y="16">${esc(unit)}</text>`;
    for(let i=0;i<=4;i++){let val=min+(max-min)*i/4;parts+=`<line class="grid" x1="${l}" x2="${w-r}" y1="${y(val)}" y2="${y(val)}"/><text x="${l-10}" y="${y(val)+4}" text-anchor="end">${fmt(val)}</text>`;}
    series[0].values.forEach((_,i)=>{if(n<=12||i%3===0||i===n-1)parts+=`<text x="${x(i)}" y="${h-17}" text-anchor="middle">${esc(series[0].labels?.[i]??i)}</text>`;});
    for(let s=0;s<series.length;s++){
      const values=series[s].values,col=colors[s%colors.length];
      if(bars){values.forEach((v,i)=>{if(v!==null)parts+=`<rect x="${x(i)-17}" y="${y(v)}" width="34" height="${y(min)-y(v)}" fill="${col}"><title>${esc(series[s].name)}：${fmt(v,2)}</title></rect>`;});}
      else {
        let path='';let started=false;
        values.forEach((v,i)=>{if(v===null){started=false;return;}path+=`${started?'L':'M'}${x(i)},${y(v)} `;started=true;});
        parts+=`<path d="${path}" fill="none" stroke="${col}" stroke-width="3"/>`;
        values.forEach((v,i)=>{if(v!==null)parts+=`<circle cx="${x(i)}" cy="${y(v)}" r="3" fill="${col}"><title>${esc(series[s].name)} ${esc(series[s].labels?.[i]??i)}：${fmt(v,2)}</title></circle>`;});
      }
    }
    return `<div class="chart-box"><svg class="chart" viewBox="0 0 ${w} ${h}" role="img" aria-label="${esc(title)}"><title>${esc(title)}</title>${parts}</svg><div class="legend">${series.map((s,i)=>`<span style="--series:${colors[i%2]}">${esc(s.name)}</span>`).join('')}</div></div>`;
  }
  const SQL_EXAMPLES=[
    ['核对记录与观测单元',`SELECT COUNT(*) AS 原始行, COUNT(DISTINCT date_time) AS 唯一小时\nFROM raw_weather;\n\nSELECT MIN(local_time) AS 开始, MAX(local_time) AS 结束,\n       COUNT(*) AS 小时数, SUM(traffic_volume = 0) AS 已记录零值\nFROM hourly;`],
    ['按钟点比较早高峰',`SELECT substr(local_time,12,2) AS 钟点,\n       COUNT(*) AS 观测小时数,\n       ROUND(AVG(traffic_volume),2) AS 平均交通量_辆每小时\nFROM hourly\nWHERE local_time >= '2017-01-01' AND local_time < '2018-01-01'\n  AND substr(local_time,12,2) IN ('07','08','09')\nGROUP BY 钟点 ORDER BY 钟点;`],
    ['先检查交通量冲突',`SELECT date_time, COUNT(*) AS 天气记录数,\n       COUNT(DISTINCT traffic_volume) AS 交通量取值数\nFROM raw_weather GROUP BY date_time\nHAVING COUNT(DISTINCT traffic_volume) > 1;`],
    ['核对一对多连接',`SELECT COUNT(*) AS 连接后行数, SUM(h.traffic_volume) AS 连接后累计车辆数\nFROM hourly h JOIN raw_weather w ON h.local_time = w.date_time\nWHERE h.local_time >= '2017-01-01' AND h.local_time < '2018-01-01';\n\nSELECT COUNT(*) AS 唯一小时数, SUM(traffic_volume) AS 观测小时累计车辆数\nFROM hourly WHERE local_time >= '2017-01-01' AND local_time < '2018-01-01';`],
    ['验证复合主键约束',`-- 此查询故意尝试重复插入，预期触发主键错误。\n-- 每次运行用原始数据库副本，不会改变下一次实验。\nINSERT INTO hourly SELECT * FROM hourly LIMIT 1;`]
  ];
  const PY_BASE=`import numpy as np\nimport pandas as pd\n\n# records和columns来自本课捆绑的真实CSV；每次运行重新建立raw。\nraw = pd.DataFrame(records, columns=columns)\nraw['time'] = pd.to_datetime(raw['date_time'])\n`;
  const PY_CLEAN=`conflicts = raw.groupby('time')['traffic_volume'].nunique()\nassert not (conflicts > 1).any(), '同小时交通量冲突，停止整编'\nhourly = raw.drop_duplicates('time').sort_values('time').copy()\n`;
  const PY_EXAMPLES=[
    ['一致性检查与整编',PY_BASE+`\nprint(raw[['date_time','traffic_volume','temp']].head())\nprint(raw.dtypes)\n`+PY_CLEAN+`print('原始行:', len(raw), '唯一小时:', len(hourly))\nprint('冲突小时:', int((conflicts > 1).sum()))`],
    ['NumPy单位转换',PY_BASE+`\ntemp_k = raw['temp'].to_numpy(dtype=float)\ntemp_c = temp_k - 273.15\nprint('前5行摄氏温度:', np.round(temp_c[:5], 2))\nprint('低于-60或高于60摄氏度的行:', int(((temp_c < -60) | (temp_c > 60)).sum()))\n# 此范围仅为课堂筛查阈值，不是正式传感器验收标准。`],
    ['Pandas时间骨架审计',PY_BASE+PY_CLEAN+`\nyear = 2017\npart = hourly[hourly['time'].dt.year == year]\nskeleton = pd.date_range(part['time'].min(), part['time'].max(), freq='h')\nmissing = skeleton.difference(part['time'])\nprint('年份:', year, '唯一小时:', len(part))\nprint('首末观测间应有标签:', len(skeleton), '缺口:', len(missing))\nprint('已记录零值:', int(part['traffic_volume'].eq(0).sum()))\nprint('前10个缺口:', missing[:10].tolist())`],
    ['第三章早高峰抽样框',PY_BASE+PY_CLEAN+`\npart = hourly[(hourly['time'].dt.year == 2017) & hourly['time'].dt.hour.isin([7,8,9])]\ndaily = part.groupby(part['time'].dt.date)['traffic_volume'].agg(['count','mean','sum'])\ncomplete = daily[daily['count'] == 3]\nprint('完整日期:', len(complete), '不完整日期:', 365-len(complete))\nprint(complete.head())\nprint('mean单位: 辆/小时；sum单位: 辆/3小时窗口')`]
  ];
  function codeLab(el,kind,record){
    const examples=kind==='sql'?SQL_EXAMPLES:PY_EXAMPLES;
    el.innerHTML=`<div class="controls"><label>实验代码<select name="example">${examples.map(([t],i)=>`<option value="${i}">${esc(t)}</option>`).join('')}</select></label><button data-action="reset">恢复当前示例</button></div><label class="field">${kind==='sql'?'SQL':'Python'}代码（可编辑，最多20,000字符）<textarea class="code-editor" spellcheck="false" maxlength="20000" aria-label="${kind==='sql'?'SQL':'Python'}代码"></textarea></label><div class="controls"><button class="primary" data-action="run">${kind==='sql'?'在本机运行SQL':'加载并运行Python（需联网）'}</button><button data-action="stop" disabled>停止运行</button><button data-action="download">下载当前代码</button></div><p class="subtle">${kind==='sql'?'本机SQLite，原始表raw_weather / 唯一小时表hourly / 站点表station。每次运行使用新数据库副本；每条语句最多展示200行，最多8条语句。':'首次加载需从jsDelivr下载Pyodide 0.29.3及NumPy、Pandas，可能需要1–3分钟。计算在本机执行；取消后可重新加载。离线资料包不包含Python运行时。'} 运行超过20秒会停止。切换教学页会停止未完成的计算。</p><div class="output" aria-live="polite">尚未运行。先阅读代码，再修改一个条件做对照。</div>`;
    const editor=el.querySelector('textarea'),select=el.querySelector('select'),out=el.querySelector('.output'),run=el.querySelector('[data-action=run]'),stop=el.querySelector('[data-action=stop]');
    const reset=()=>editor.value=examples[+select.value][1];reset();select.onchange=reset;
    el.querySelector('[data-action=reset]').onclick=reset;
    el.querySelector('[data-action=download]').onclick=()=>ClassroomApp.download(`ch02-${kind}-experiment.${kind==='sql'?'sql':'py'}`,kind==='sql'?editor.value:`# Put this script beside index.html in the extracted classroom package.\nfrom pathlib import Path\nimport pandas as pd\n_source = pd.read_csv(Path(__file__).resolve().parent / 'data/ch02_raw.csv', keep_default_na=False)\ncolumns = _source.columns.tolist()\nrecords = _source.values.tolist()\n\n${editor.value}`,'text/plain');
    stop.onclick=()=>ClassroomRuntimes.cancel(kind);
    run.onclick=async()=>{
      run.disabled=true;stop.disabled=false;select.disabled=true;
      const code=editor.value,example=examples[+select.value][0];
      try{
        const r=await ClassroomRuntimes.run(kind,code,status=>{out.textContent=status;});
        if(!el.isConnected)return;
        if(kind==='sql')out.innerHTML=r.results.map((res,i)=>`<p>语句${i+1}：${res.columns.length?`${res.rows.length}${res.truncated?'+':''}行展示`:`执行完成，影响${res.changed}行`}</p>${res.columns.length?table(res.columns,res.rows):''}${res.truncated?'<p class="subtle">已截断预览。请通过COUNT或更具体的WHERE条件核查总体，不将200行当作全部结果。</p>':''}`).join('')||'没有可执行语句。';
        else out.innerHTML=`<pre>${esc(r.output)}</pre>`;
        out.insertAdjacentHTML('beforeend',`<p class="subtle">实际执行环境：${esc(r.version)}</p>`);
        record(kind,{example,code},{version:r.version,output:kind==='python'?r.output.slice(0,10000):r.results});
      }catch(e){if(el.isConnected)out.innerHTML=feedback(e.message,'error');}
      finally{if(el.isConnected){run.disabled=false;stop.disabled=true;select.disabled=false;}}
    };
  }
  const labs={
    unit(el,record){
      el.innerHTML=`<h3>一行、一小时、一辆车</h3><div class="controls"><label>traffic_volume=5,545代表什么？<select><option value="">请选择解释</option><option value="row">这一行代表一辆车</option><option value="hour">该断面该小时记录了5,545辆车</option><option value="speed">平均速度为5,545</option><option value="network">全城市当小时出行需求</option></select></label></div>${table(D.columns.slice(5),D.rows.slice(0,4).map(r=>r.slice(5)))}<div class="answer" aria-live="polite"></div>`;
      el.querySelector('select').onchange=e=>{const correct=e.target.value==='hour';el.querySelector('.answer').innerHTML=feedback(correct?'对应断面小时车辆数。将时间窗标准化为每小时后，本课用辆/小时表达；没有车辆个体ID。':'请回到数据字典：对象是I-94西向ATR 301断面，时间尺度为小时。它不是速度、个体轨迹或全城需求。',correct?'':'warn');record('观测单元',{choice:e.target.value},{correct});};
    },
    schema(el,record){
      el.innerHTML=`<h3>选择一个候选主键</h3><div class="schema"><article><b>station · 站点</b><code>station_id → road, direction</code><small>1个站点；课堂补充元数据</small></article><article><b>hourly · 交通观测</b><code>station_id + local_time</code><small>40,575小时；保留交通量与天气行数</small></article><article><b>raw_weather · 原始行</b><code>row_id → date_time, weather...</code><small>48,204行；保留原始九列</small></article></div><div class="controls"><label>在当前原始表中检查<select><option value="time">仅用date_time</option><option value="row">给每行单独编号row_id</option><option value="hour">整编后station_id + local_time</option></select></label></div><div class="result"></div>`;
      const update=()=>{const choice=el.querySelector('select').value;const msg=choice==='time'?`原始${fmt(D.rows.length)}行仅有${fmt(M.hours.length)}个时间标签，附加${fmt(D.rows.length-M.hours.length)}行。不能在原始天气表上强行把时间设为唯一键。`:choice==='row'?'row_id能唯一识别文件中的一行，但不能保证同一交通小时只出现一次；技术编号不是观测单元。':'本快照先核查冲突，再得到40,575个唯一小时。多站点、多方向扩展时要同步调整复合键，不能只靠时间。';el.querySelector('.result').innerHTML=feedback(msg,choice==='time'?'warn':'');record('主键检查',{choice},{message:msg});};el.querySelector('select').onchange=update;update();
    },
    sql:(el,r)=>codeLab(el,'sql',r),python:(el,r)=>codeLab(el,'python',r),
    join(el,record){
      el.innerHTML=`<h3>天气连接后的交通量汇总</h3><div class="controls">${yearSelect()}</div><div class="result"></div>`;
      const update=()=>{const year=+el.querySelector('select').value,rows=M.hours.filter(r=>r.year===year);const correct=rows.reduce((s,r)=>s+r.volume,0),joined=rows.reduce((s,r)=>s+r.volume*r.count,0),n=rows.reduce((s,r)=>s+r.count,0);el.querySelector('.result').innerHTML=stats([['唯一小时',fmt(rows.length)],['连接后行',fmt(n)],['错误汇总多计比例',fmt((joined/correct-1)*100,2)+'%']])+table(['汇总口径','累计车辆数（仅观测小时）'],[['唯一小时表求和',fmt(correct)],['与天气行连接后直接求和',fmt(joined)]])+feedback('两项累计值覆盖同一组已观测小时。差值是重复加权造成的，不是交通增长；不把缺测时段视为0。','warn');record('连接基数',{year},{uniqueHours:rows.length,joinedRows:n,correct,joined});};el.querySelector('select').onchange=update;update();
    },
    document(el,record){
      const examples=[...M.groups].filter(([,r])=>r.length>1&&new Set(r.map(x=>x[5])).size>1).slice(0,6);
      el.innerHTML=`<h3>同一小时的两种表达</h3><div class="controls"><label>选择真实多标签小时<select>${examples.map(([t],i)=>`<option value="${i}">${t}</option>`).join('')}</select></label><label>表达方式<select name="view"><option value="json">JSON文档</option><option value="table">关系表</option></select></label></div><div class="result"></div>`;
      const update=()=>{const [t,rows]=examples[+el.querySelector('select').value],weather=[...new Set(rows.map(r=>r[5]))],view=el.querySelector('[name=view]').value;el.querySelector('.result').innerHTML=view==='json'?`<pre>${esc(JSON.stringify({station_id:'ATR301',local_time:t,traffic_volume:rows[0][8],weather_labels:weather},null,2))}</pre>`:table(['station_id','local_time','weather_label'],weather.map(w=>['ATR301',t,w]));el.querySelector('.result').insertAdjacentHTML('beforeend',feedback(`${rows.length}条原始天气行 → ${weather.length}个不同主标签 → 1个交通小时。JSON仅合并主标签，原始详细描述仍保存在原表。`));record('多标签组织',{time:t,view},{rawRows:rows.length,weather});};el.querySelectorAll('select').forEach(s=>s.onchange=update);update();
    },
    temperature(el,record){
      el.innerHTML=`<h3>同一温度列，三种处理方式</h3><div class="controls"><label>显示方式<select><option value="raw">原始K</option><option value="cast">只转为浮点数</option><option value="convert">向量化减去273.15</option></select></label></div><div class="result"></div><pre>temp_k = raw['temp'].to_numpy(dtype=float)\ntemp_c = temp_k - 273.15\nflag = (temp_c &lt; -60) | (temp_c &gt; 60)</pre>`;
      const update=()=>{const choice=el.querySelector('select').value,flagged=D.rows.filter(r=>r[1]-273.15< -60||r[1]-273.15>60).length;el.querySelector('.result').innerHTML=table(['原始时间','原始温度K',choice==='convert'?'转换温度°C':'输出值（仍为K）'],D.rows.slice(0,5).map(r=>[r[7],r[1],(r[1]-(choice==='convert'?273.15:0)).toFixed(2)]))+feedback(`当前全部原始行中，按−60至60°C课堂筛查范围标记${flagged}行。阈值是教学筛查设置，非正式验收标准；重复天气行也被逐行计入。${choice==='cast'?'只转类型没有改变单位。':''}`,choice==='cast'?'warn':'');record('温度单位',{choice},{flaggedRawRows:flagged});};el.querySelector('select').onchange=update;update();
    },
    audit(el,record){
      el.innerHTML=`<h3>按年重算质量审计</h3><div class="controls">${yearSelect()}<label>应有小时范围<select name="scope"><option value="observed">该年首末观测之间</option><option value="calendar">完整日历年（含未覆盖期）</option></select></label></div><div class="result"></div><button data-export>导出七年质量审计CSV</button>`;
      const update=()=>{const year=+el.querySelector('[name=year]').value,full=el.querySelector('[name=scope]').value==='calendar',a=C.audit(M,year,full);el.querySelector('.result').innerHTML=stats([['原始行',fmt(a.raw)],['唯一小时',fmt(a.unique)],['缺口标签',fmt(a.missing)],['已记录零值',fmt(a.zeros)]])+table(['项目','结果'],[['首个骨架标签',a.start],['最后骨架标签',a.end],['应有标签',a.expected],['重复附加行',a.extra],['同小时交通量冲突',a.conflicts]])+feedback(full?'采用完整日历年分母，未包含在快照中的前后月份也计为覆盖缺口；不能解释为已确认的设备故障。':'采用首末观测之间的连续小时标签骨架。原始值无空单元格，时间序列仍可存在缺口。',full?'warn':'');record('年度质量审计',{year,scope:full?'calendar':'observed'},a);};el.querySelectorAll('select').forEach(s=>s.onchange=update);el.querySelector('[data-export]').onclick=()=>{const full=el.querySelector('[name=scope]').value==='calendar',rows=Array.from({length:7},(_,i)=>C.audit(M,2012+i,full));ClassroomApp.download('ch02-quality-audit.csv',C.csv(Object.keys(rows[0]),rows.map(Object.values)),'text/csv');};update();
    },
    conflict(el,record){
      const original=D.rows.find(r=>M.groups.get(r[7]).length>1);
      el.innerHTML=`<h3>给整编程序做一次失败测试</h3><div class="controls"><label>输入条件<select><option value="real">真实快照，不改动</option><option value="injected">演示副本中注入+100辆冲突</option></select></label></div><div class="result"></div>`;
      const update=()=>{const injected=el.querySelector('select').value==='injected';const demo=M.groups.get(original[7]).map(r=>[r[7],r[8],'真实天气行']);if(injected)demo.push([original[7],original[8]+100,'人为注入，仅作测试']);const values=new Set(demo.map(r=>r[1]));el.querySelector('.result').innerHTML=table(['本地小时','交通量（辆/小时）','记录性质'],demo)+feedback(values.size>1?'检查失败：同小时存在多个交通量，必须停止自动去重并核查。注入记录没有写入真实数据或导出表。':'检查通过：该小时交通量一致。保留一个交通观测，并另行组织天气标签。',values.size>1?'error':'');record('冲突压力测试',{injected,time:original[7]},{distinctValues:values.size,stop:values.size>1});};el.querySelector('select').onchange=update;update();
    },
    weights(el,record){
      el.innerHTML=`<h3>日变化曲线：按行还是按小时？</h3><div class="controls">${yearSelect()}<label>日期范围<select name="days"><option value="all">所有日期</option><option value="weekday">周一至周五（未剔除节假日）</option></select></label></div><div class="result"></div>`;
      const update=()=>{const year=+el.querySelector('[name=year]').value,weekday=el.querySelector('[name=days]').value==='weekday',unique=C.hourlyProfile(M,year,false,weekday),weighted=C.hourlyProfile(M,year,true,weekday);el.querySelector('.result').innerHTML=plot([{name:'唯一小时均值',values:unique.map(r=>r.value)},{name:'原始行加权均值',values:weighted.map(r=>r.value)}])+table(['钟点','唯一小时数','原始行数','小时均值','行均值','差值（行−小时）'],unique.map((r,i)=>[`${r.hour}时`,r.n,weighted[i].n,fmt(r.value,2),fmt(weighted[i].value,2),fmt(weighted[i].value-r.value,2)]));record('日变化口径',{year,weekday},{unique,weighted});};el.querySelectorAll('select').forEach(s=>s.onchange=update);update();
    },
    peak(el,record){
      const excluded=[];
      for(let ms=C.stamp('2017-01-01 00:00:00');ms<C.stamp('2018-01-01 00:00:00');ms+=24*C.HOUR){
        const date=C.label(ms).slice(0,10),slots=C.daySlots(M,date).filter(r=>[7,8,9].includes(r.hour));
        if(slots.some(r=>r.value===null))excluded.push([date,slots.filter(r=>r.value!==null).length,slots.filter(r=>r.value===null).map(r=>r.hour+'时').join('、')]);
      }
      el.innerHTML=`<h3>建立2017年日期级抽样框</h3><div class="controls"><label>日期保留规则<select name="complete"><option value="yes">07、08、09时均有观测</option><option value="no">至少1小时有观测（不同尺度对照）</option></select></label><label>窗口指标<select name="metric"><option value="mean">3小时平均交通量</option><option value="sum">窗口累计车辆数</option></select></label></div><div class="result"></div><button data-export>导出完整日期抽样框</button>`;
      el.insertAdjacentHTML('beforeend',`<details><summary>核查7个不完整日期：6日部分缺测，1日三小时全缺</summary>${table(['日期','已观测小时数','缺失钟点'],excluded)}<p>至少观测1小时的规则纳入364日，而非365日；其中6日窗口不完整。第三章只使用358个完整日期。</p></details>`);
      const update=()=>{const complete=el.querySelector('[name=complete]').value==='yes',sum=el.querySelector('[name=metric]').value==='sum',rows=C.peakDays(M,2017,complete);el.querySelector('.result').innerHTML=stats([['纳入日期',rows.length],['未纳入日期',365-rows.length],['完整三小时日期',C.peakDays(M).length]])+table(['日期','观测小时数',sum?'已观测窗口累计（辆）':'观测小时均值（辆/小时）'],rows.slice(0,12).map(r=>[r.date,r.n,fmt(sum?r.value*r.n:r.value,2)]))+feedback(complete?'此完整性规则与第三章358日主抽样框一致。上表只预览前12日；排除日期的覆盖偏差仍需讨论。':'本对照混入不完整窗口，均值与累计值的含义都会受影响。不能直接替代第三章主抽样框。',''+(!complete?'warn':''));record('早高峰抽样框',{complete,metric:sum?'sum':'mean'},{included:rows.length,excluded:365-rows.length});};el.querySelectorAll('select').forEach(s=>s.onchange=update);el.querySelector('[data-export]').onclick=()=>ClassroomApp.download('ch02-to-ch03-complete-peak-days.csv',C.csv(['date','n_hours','peak_mean','peak_total'],C.peakDays(M).map(r=>[r.date,r.n,r.value,r.value*r.n])),'text/csv');update();
    },
    'chart-choice'(el,record){
      const cases=[['一天24小时的交通量怎样变化？','line','折线图保留时间顺序，并标注单位与缺测。'],['哪些小时没有观测？','heat','时间格子或缺测热力图保留应有标签，缺测与零值分开。'],['事故在哪里聚集？','map','位置散点或地图，需先核查坐标和空间覆盖；聚集不是风险。'],['车辆在路口怎样移动？','track','按时间排序的轨迹，需有位置、时间和身份；不能任意连线。'],['各区域之间的出行联系？','od','需要真实起终点对；本课TLC上车聚合不能生成OD矩阵。']];
      el.innerHTML=`<h3>给交通问题选择表达方式</h3><div class="controls"><label>问题<select name="question">${cases.map(([q],i)=>`<option value="${i}">${q}</option>`).join('')}</select></label><label>图形<select name="answer"><option value="">请选择</option><option value="line">时间折线</option><option value="heat">时间缺测格子</option><option value="map">空间点图</option><option value="track">时序轨迹</option><option value="od">OD矩阵（先补足起终点数据）</option><option value="pie">饼图</option></select></label></div><div class="result" aria-live="polite"></div>`;
      const update=()=>{const q=+el.querySelector('[name=question]').value,a=el.querySelector('[name=answer]').value;if(!a){el.querySelector('.result').textContent='先选择图形，再检查其数据条件。';return;}const correct=a===cases[q][1];el.querySelector('.result').innerHTML=feedback((correct?'选择与问题相符。':'请检查图形是否保留问题所需的结构。')+cases[q][2],correct?'':'warn');record('图形选择',{question:cases[q][0],choice:a},{correct});};el.querySelector('[name=question]').onchange=()=>{el.querySelector('[name=answer]').value='';update();};el.querySelector('[name=answer]').onchange=update;update();
    },
    axis(el,record){
      el.innerHTML=`<h3>同一数据，改变纵轴</h3><div class="controls"><label>纵轴范围<select><option value="zero">从0开始</option><option value="local">局部范围（明确标注）</option></select></label></div><div class="result"></div>`;
      const values=C.hourlyProfile(M,2017).slice(6,11),minValue=Math.min(...values.map(r=>r.value)),maxValue=Math.max(...values.map(r=>r.value));
      const update=()=>{const local=el.querySelector('select').value==='local',min=local?Math.floor(minValue*.9/100)*100:0;el.querySelector('.result').innerHTML=plot([{name:'2017年唯一小时均值',labels:values.map(r=>r.hour+'时'),values:values.map(r=>r.value)}],{min,max:Math.ceil(maxValue*1.08/100)*100,title:'06—10时均值，纵轴'+(local?'局部范围':'从零开始')})+stats([['这5个钟点最大差值',fmt(maxValue-minValue,1)+'辆/小时'],['最大值 / 最小值',fmt(maxValue/minValue,2)+'倍']])+table(['钟点','均值（辆/小时）','观测小时数'],values.map(r=>[r.hour,fmt(r.value,2),r.n]))+feedback(local?`注意：纵轴下界为${min}辆/小时，不是0。视觉斜率变化，但实际差值不变。`:'零起点保留绝对量级；仍需同时观察具体差值和样本数。',local?'warn':'');record('纵轴口径',{local,min},{minValue,maxValue});};el.querySelector('select').onchange=update;update();
    },
    heatmap(el,record){
      const incomplete=C.peakDays(M,2017,false).find(r=>r.n<3)?.date||'2017-01-01';
      const zero=M.hours.find(r=>r.volume===0)?.time.slice(0,10);
      el.innerHTML=`<h3>逐小时检查数据状态</h3><div class="controls"><label>日期<input type="date" min="2012-10-02" max="2018-09-30" value="${incomplete}"></label><button data-zero>查看含0值日期</button><button data-gap>查看缺口日期</button><label>均值处理<select><option value="keep">缺测保持空值</option><option value="zero">错误对照：缺测填0</option></select></label></div><div class="result"></div>`;
      const update=()=>{const date=el.querySelector('input').value;if(!/^\d{4}-\d{2}-\d{2}$/.test(date))return;const rows=C.daySlots(M,date),fill=el.querySelector('select').value==='zero',observed=rows.filter(r=>r.value!==null),values=fill?rows.map(r=>r.value??0):observed.map(r=>r.value),max=Math.max(...observed.map(r=>r.value),1);el.querySelector('.result').innerHTML=`<div class="heatmap">${rows.map(r=>`<div class="heatcell ${r.value===null?'missing':''}" ${r.value!==null?`style="background:hsl(173 35% ${97-r.value/max*37}%)"`:''} title="${r.time}：${r.value===null?'缺测':r.value+'辆/小时'}">${r.hour}时<b>${r.value===null?'缺测':fmt(r.value)}</b></div>`).join('')}</div>`+stats([['有观测小时',observed.length],['缺口',24-observed.length],['按所选规则均值',fmt(C.mean(values),2)]])+feedback(fill?'填0只改变这个错误对照的均值分母与分子，没有修改原数据。它会把无观测误当无交通，不能用于主项目整编。':'格子保留原始质量状态；均值分母为有观测小时数。若不足24小时，它不是完整日均。',fill?'warn':'')+table(['小时','交通量（辆/小时）','状态'],rows.map(r=>[r.hour,r.value??'',r.value===null?'无观测':r.value===0?'已记录0，需核查':'已观测']));record('缺口图',{date,fillZeroDemonstration:fill},{observed:observed.length,missing:24-observed.length,mean:C.mean(values)});};el.querySelector('input').onchange=update;el.querySelector('select').onchange=update;el.querySelector('[data-zero]').onclick=()=>{el.querySelector('input').value=zero;update();};el.querySelector('[data-gap]').onclick=()=>{el.querySelector('input').value=incomplete;update();};update();
    },
    coordinates(el,record){
      el.innerHTML=`<h3>纽约事故坐标检查</h3><div class="controls"><label>坐标顺序<select><option value="correct">横轴经度，纵轴纬度</option><option value="swap">交换经纬度（错误对照）</option></select></label></div><div class="result"></div>`;
      const update=()=>{const swap=el.querySelector('select').value==='swap',points=D.crashes.map(r=>({id:r[0],x:r[swap?2:1],y:r[swap?1:2]})),inside=points.filter(p=>p.x>=-74.3&&p.x<=-73.6&&p.y>=40.45&&p.y<=40.95);const x=v=>70+(v+74.3)/.7*650,y=v=>290-(v-40.45)/.5*250;const svg=`<svg class="chart" viewBox="0 0 800 340" role="img" aria-label="纽约事故经纬度散点示意，不含道路底图"><title>纽约事故坐标检查</title><rect x="70" y="40" width="650" height="250" fill="#f4f6f2" stroke="#bdceca"/>${inside.map(p=>`<circle cx="${x(p.x)}" cy="${y(p.y)}" r="1.6" fill="#087e82" opacity=".45"/>`).join('')}<text x="70" y="315">−74.30</text><text x="650" y="315">−73.60° 经度</text><text x="10" y="48">40.95°</text><text x="10" y="290">40.45°</text><text x="70" y="20">纬度（度）；固定纽约区域视窗</text></svg>`;el.querySelector('.result').innerHTML=stats([['原始事故记录',D.crashTotal],['有效坐标',D.crashes.length],['落入本视窗',inside.length]])+`<div class="chart-box">${svg}</div>`+feedback(swap?'交换后没有点落入固定纽约视窗。值仍可能通过全球范围检查，因此还必须核查区域和轴顺序。':'点云仅为坐标分布示意，未绘制道路或行政边界。474条无有效坐标的事故没有被补造位置。',swap?'warn':'')+table(['事故ID','横轴值','纵轴值'],points.slice(0,5).map(p=>[p.id,p.x,p.y]));record('坐标轴核查',{swap},{valid:D.crashes.length,inside:inside.length,excluded:D.crashTotal-D.crashes.length});};el.querySelector('select').onchange=update;update();
    },
    trajectory(el,record){
      const ids=[...new Set(D.tracks.map(r=>r[0]))];el.innerHTML=`<h3>天津路口轨迹展示</h3><div class="controls"><label>源ID<select name="track">${ids.map(id=>`<option>${id}</option>`).join('')}</select></label><label>采样间隔<select name="step"><option value="1">逐点（约0.1秒）</option><option value="5">每5点</option><option value="10">每10点</option></select></label><label>连线顺序<select name="order"><option value="time">按时间排序</option><option value="swap">相邻记录交换（错误对照）</option></select></label></div><div class="result"></div>`;
      const update=()=>{const id=el.querySelector('[name=track]').value,step=+el.querySelector('[name=step]').value,swap=el.querySelector('[name=order]').value==='swap',full=D.tracks.filter(r=>r[0]===id).sort((a,b)=>a[1]-b[1]);let rows=full.filter((_,i)=>i%step===0);if(swap){rows=[...rows];for(let i=0;i+1<rows.length;i+=2)[rows[i],rows[i+1]]=[rows[i+1],rows[i]];}const xs=full.map(r=>r[2]),ys=full.map(r=>r[3]),xmin=Math.min(...xs)-3,xmax=Math.max(...xs)+3,ymin=Math.min(...ys)-3,ymax=Math.max(...ys)+3,scale=Math.min(660/(xmax-xmin),240/(ymax-ymin)),x=v=>70+(v-xmin)*scale,y=v=>290-(v-ymin)*scale;const path=rows.map((r,i)=>(i?'L':'M')+x(r[2])+','+y(r[3])).join(' '),backwards=rows.slice(1).filter((r,i)=>r[1]<rows[i][1]).length;el.querySelector('.result').innerHTML=`<div class="chart-box"><svg class="chart" viewBox="0 0 800 340" role="img" aria-label="SinD真实轨迹，横纵坐标均为米且同比例"><title>轨迹按${swap?'错误记录顺序':'时间顺序'}连接</title><rect x="65" y="35" width="675" height="260" fill="#f1f5f1"/><path d="${path}" fill="none" stroke="${swap?'#c27527':'#087e82'}" stroke-width="2"/>${rows.filter((_,i)=>i%Math.max(1,Math.floor(rows.length/80))===0).map(r=>`<circle cx="${x(r[2])}" cy="${y(r[3])}" r="2.5" fill="#183d44"><title>${r[1]}秒，(${r[2]}, ${r[3]})米</title></circle>`).join('')}<text x="70" y="20">地面坐标（米），x与y同比例；无道路底图</text><text x="70" y="318">x从${xmin.toFixed(1)}米起；y从${ymin.toFixed(1)}米起</text></svg></div>`+stats([['展示点数',rows.length],['时间倒序连接',backwards],['原轨迹持续时间',fmt(full.at(-1)[1]-full[0][1],1)+'秒']])+feedback(swap?'人为交换只改变连线顺序，没有更改真实位置；折返不是新发现的驾驶行为。速度计算遇到非正时间差应停止或标记。':'本页保留提供方源ID用于展示；不计算检测或跟踪准确率。采样步长增加不意味着道路上真实运动变慢。',swap?'warn':'')+table(['源ID','秒','x（米）','y（米）'],rows.slice(0,8).map(r=>r.slice(0,4)));record('轨迹顺序',{id,step,swap},{points:rows.length,backwards});};el.querySelectorAll('select').forEach(s=>s.onchange=update);update();
    },
    files(el,record){
      const files=[['接收的ch02_raw.csv','raw'],['去重后的hourly.csv','processed'],['整编脚本audit.py','src'],['逐年质量审计quality.csv','outputs'],['人工设备核查记录','raw']];
      el.innerHTML=`<h3>把文件放到合适的位置</h3>${files.map(([name],i)=>`<label class="field">${name}<select data-file="${i}"><option value="">请选择目录</option>${['raw','processed','src','outputs'].map(v=>`<option>${v}</option>`).join('')}</select></label>`).join('')}<button class="primary">检查组织方式</button><div class="result"></div>`;
      el.querySelector('button').onclick=()=>{const selections=[...el.querySelectorAll('select')].map(s=>s.value);el.querySelector('.result').innerHTML=table(['文件','你的选择','建议位置'],files.map(([name,answer],i)=>[name,selections[i]||'未选',answer]))+feedback('原始CSV和人工核查记录属于需保护的输入证据。processed、outputs是由已记录规则生成的成果；质量审计也应随每次整编留档。');record('目录组织',{selections},{recommended:files});};
    },
    report(el){ClassroomApp.renderReport(el);},
    handoff(el){
      const paths=[['02','道路监测数据接收','导出完整小时表和审计，继续完成数据字典与接收说明。','ch02-audit-v1'],['03','早高峰抽样调查','沿用2017年358个完整日期，比较20/60/90日样本及B=1000区间。','ch03-bootstrap-v1'],['04','共享单车服务量估计','换用真实租借数据；时间切分、训练期预处理及无泄漏特征是本章方法的延伸。','ch04-regression-v1'],['05','事故空间排查','保留7,542条总体与7,068个有效点的审计，统一米制距离后比较网格、KDE和DBSCAN。','ch05-spatial-v1'],['06','断面交通量预测','保留连续小时骨架与NaN；四种方法按1/3/6小时预测，在共同2,169个目标时刻评价。','ch06-forecast-v1'],['07','分区运营分析','另用TLC真实上车聚合，建立四区域小时矩阵；不要将上车量伪装成完整OD或需求。','ch07-spatiotemporal-v1'],['08','路口轨迹与影像调查','统一地面米、影像像素、秒和帧；SinD关联与MOT17夜间影像分别组织和核查。','ch08-tracking-v1']];
      el.innerHTML=`<h3>先完成本章，再带着明确的数据条件进入算法项目</h3><div class="controls"><button class="primary" data-clean>导出40,575小时整编CSV</button><a class="button" href="../#project/ch02/code">第二章完整项目</a><a class="button" href="#reproduce">导出本课实验记录</a></div><p class="subtle">整编导出仅包含通过冲突核查的真实小时、交通量和天气主标签。缺口不填0；未修改原始文件。</p>${paths.map(([n,title,text,protocol])=>`<div class="bridge"><p class="eyebrow">CHAPTER ${n} · ${esc(protocol)}</p><h3>${title}</h3><p>${text}</p><a href="../#project/ch${n}/code">进入主实验</a><a href="../#project/ch${n}/cases">阅读交通工程案例</a></div>`).join('')}`;
      el.querySelector('[data-clean]').onclick=()=>{if(M.conflicts.length){alert('存在交通量冲突，停止导出。');return;}ClassroomApp.download('ch02-hourly-40575.csv',C.csv(['station_id','local_time','traffic_volume','weather_rows','weather_labels'],M.hours.map(r=>['ATR301',r.time,r.volume,r.count,JSON.stringify(r.weather)])),'text/csv');};
    }
  };
  window.ClassroomLabs={mount(id,el,record){if(!labs[id])throw Error('未实现课堂实验：'+id);labs[id](el,record);},esc,fmt,table,stats,plot,SQL_EXAMPLES,PY_EXAMPLES};
})();
