/* MIT */
window.COURSE_DATA = (() => {
  const mean=a=>a.length?a.reduce((s,v)=>s+v,0)/a.length:null;
  const hourly=rows=>Array.from({length:24},(_,hour)=>{
    const a=rows.filter(r=>r.hour===hour);
    return {hour,n:a.length,value:mean(a.map(r=>r.volume))};
  });
  const filter=(rows,{year='2018',month='all',day='all',weather='all',hour='all'}={})=>rows.filter(r=>
    (year==='all'||r.year===+year)&&(month==='all'||r.month===+month)&&
    (day==='all'||(day==='weekday'?r.day<5:r.day>=5))&&
    (weather==='all'||r.weather.includes(weather))&&(hour==='all'||r.hour===+hour));
  function baselines(rows){
    const train=rows.filter(r=>r.year===2017), test=rows.filter(r=>r.year===2018), groups=new Map();
    const global=mean(train.map(r=>r.volume));
    for(const r of train){const k=r.day+'-'+r.hour;if(!groups.has(k))groups.set(k,[]);groups.get(k).push(r.volume);}
    const averages=new Map([...groups].map(([k,v])=>[k,mean(v)]));
    const predictions=test.map(r=>({...r,global,periodic:averages.get(r.day+'-'+r.hour)??global}));
    return {train:train.length,test:test.length,predictions,globalMAE:mean(predictions.map(r=>Math.abs(r.volume-r.global))),periodicMAE:mean(predictions.map(r=>Math.abs(r.volume-r.periodic)))};
  }
  return {mean,hourly,filter,baselines};
})();
