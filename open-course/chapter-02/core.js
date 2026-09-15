(function(root) {
  'use strict';
  const HOUR = 3600000;
  // UTC is only a timezone-independent arithmetic axis for source-local labels.
  // It does not convert the source's civil times or reconstruct DST.
  const stamp = t => Date.parse(t.replace(' ', 'T') + 'Z');
  const label = ms => new Date(ms).toISOString().slice(0, 19).replace('T', ' ');
  const mean = a => a.length ? a.reduce((s, v) => s + v, 0) / a.length : null;
  function organize(rows) {
    const groups = new Map();
    for (const r of rows) {
      if (!groups.has(r[7])) groups.set(r[7], []);
      groups.get(r[7]).push(r);
    }
    const conflicts = [...groups].filter(([, rs]) => new Set(rs.map(r => r[8])).size > 1).map(([t]) => t);
    const hours = [...groups].sort(([a], [b]) => a.localeCompare(b)).map(([t, rs]) => ({
      time:t, volume:rs[0][8], count:rs.length, weather:[...new Set(rs.map(r => r[5]))],
      year:+t.slice(0,4), hour:+t.slice(11,13), weekday:(new Date(stamp(t)).getUTCDay()+6)%7,
      conflict:conflicts.includes(t)
    }));
    return {groups, conflicts, hours};
  }
  function audit(model, year, fullYear=false) {
    const hours = model.hours.filter(r => r.year === year);
    if (!hours.length) return {year, raw:0, unique:0, extra:0, conflicts:0, missing:0, zeros:0, expected:0};
    const start = fullYear ? `${year}-01-01 00:00:00` : hours[0].time;
    const end = fullYear ? `${year}-12-31 23:00:00` : hours.at(-1).time;
    const expected = Math.round((stamp(end)-stamp(start))/HOUR)+1;
    const raw = hours.reduce((s,r)=>s+r.count,0);
    return {year,start,end,raw,unique:hours.length,extra:raw-hours.length,conflicts:hours.filter(r=>r.conflict).length,
      missing:expected-hours.length,zeros:hours.filter(r=>r.volume===0).length,expected};
  }
  function hourlyProfile(model, year, weighted=false, weekdays=false) {
    return Array.from({length:24},(_,h)=>{
      const selected=model.hours.filter(r=>r.year===year && r.hour===h && (!weekdays || r.weekday<5));
      const n=selected.reduce((s,r)=>s+(weighted?r.count:1),0);
      return {hour:h, n, value:n ? selected.reduce((s,r)=>s+r.volume*(weighted?r.count:1),0)/n : null};
    });
  }
  function peakDays(model, year=2017, requireComplete=true) {
    const days=new Map();
    for(let ms=stamp(`${year}-01-01 00:00:00`);ms<stamp(`${year+1}-01-01 00:00:00`);ms+=24*HOUR) days.set(label(ms).slice(0,10),[]);
    for(const r of model.hours) if(r.year===year && [7,8,9].includes(r.hour)) days.get(r.time.slice(0,10)).push(r.volume);
    return [...days].filter(([,a])=>requireComplete?a.length===3:a.length>0).map(([date,a])=>({date,n:a.length,value:mean(a)}));
  }
  function daySlots(model,date){return Array.from({length:24},(_,h)=>{
    const time=`${date} ${String(h).padStart(2,'0')}:00:00`, group=model.groups.get(time);
    return {hour:h,time,value:group?group[0][8]:null};
  });}
  function csv(columns, rows){return [columns,...rows].map(row=>row.map(v=>`"${String(v??'').replaceAll('"','""')}"`).join(',')).join('\r\n');}
  root.ClassroomCore={HOUR,stamp,label,mean,organize,audit,hourlyProfile,peakDays,daySlots,csv};
})(typeof window==='undefined'?globalThis:window);
