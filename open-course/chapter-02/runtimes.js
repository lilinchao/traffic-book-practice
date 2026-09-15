(function() {
  'use strict';
  function sqlWorker() {
    let SQL, pristine;
    self.onmessage=async ({data:m})=>{
      try {
        if(m.type==='init') {
          SQL=await initSqlJs();
          const db=new SQL.Database();
          db.run(`PRAGMA foreign_keys=ON;
            CREATE TABLE station(station_id TEXT PRIMARY KEY NOT NULL,road TEXT,direction TEXT,unit TEXT);
            INSERT INTO station VALUES('ATR301','I-94','westbound','vehicles/hour');
            CREATE TABLE raw_weather(row_id INTEGER PRIMARY KEY,holiday TEXT,temp REAL,rain_1h REAL,snow_1h REAL,clouds_all REAL,weather_main TEXT,weather_description TEXT,date_time TEXT,traffic_volume INTEGER);
            CREATE TABLE hourly(station_id TEXT NOT NULL REFERENCES station(station_id),local_time TEXT NOT NULL,traffic_volume INTEGER NOT NULL CHECK(traffic_volume>=0),weather_rows INTEGER NOT NULL CHECK(weather_rows>0),PRIMARY KEY(station_id,local_time));`);
          db.run('BEGIN');
          const raw=db.prepare('INSERT INTO raw_weather VALUES(?,?,?,?,?,?,?,?,?,?)');
          for(let i=0;i<m.rows.length;i++) raw.run([i+1,...m.rows[i]]);
          raw.free();
          const hours=db.prepare('INSERT INTO hourly VALUES(?,?,?,?)');
          for(const r of m.hours) hours.run(['ATR301',r.time,r.volume,r.count]);
          hours.free();
          db.run('CREATE INDEX weather_time ON raw_weather(date_time); COMMIT;');
          pristine=db.export();db.close();
          postMessage({id:m.id,ready:true,version:'sql.js 1.14.2 / SQLite'});
        } else {
          const db=new SQL.Database(pristine), results=[];
          db.run('PRAGMA foreign_keys=ON');
          try {
            for(const statement of db.iterateStatements(m.code)) {
              if(results.length>=8) throw Error('每次最多执行8条SQL语句，请分批运行。');
              const columns=statement.getColumnNames(),rows=[];
              let truncated=false;
              while(statement.step()) {
                if(rows.length>=200){truncated=true;break;}
                rows.push(statement.get().map(v=>typeof v==='string'?v.slice(0,4096):v));
              }
              results.push({columns,rows,truncated,changed:db.getRowsModified()});
            }
            postMessage({id:m.id,results,version:'sql.js 1.14.2 / SQLite'});
          } finally {db.close();}
        }
      } catch(error){postMessage({id:m.id,error:String(error.message||error)});}
    };
  }
  function pythonWorker() {
    let py, records, columns, output;
    const capture=line=>{if(output.length<60000) output+=(line+'\n').slice(0,60000-output.length);};
    self.onmessage=async ({data:m})=>{
      try {
        if(m.type==='init') {
          importScripts('https://cdn.jsdelivr.net/pyodide/v0.29.3/full/pyodide.js');
          py=await loadPyodide({indexURL:'https://cdn.jsdelivr.net/pyodide/v0.29.3/full/'});
          await py.loadPackage(['numpy','pandas']);
          records=JSON.stringify(m.rows); columns=JSON.stringify(m.columns);
          py.setStdout({batched:capture});py.setStderr({batched:capture});
          postMessage({id:m.id,ready:true,version:'Pyodide '+py.version});
        } else {
          output='';
          const dict=py.globals.get('dict'), ns=dict(); dict.destroy();
          ns.set('_records_json',records);ns.set('_columns_json',columns);
          try {
            await py.runPythonAsync(`import json\nrecords = json.loads(_records_json)\ncolumns = json.loads(_columns_json)\n`,{globals:ns});
            await py.runPythonAsync(m.code,{globals:ns});
            const version=py.runPython('import sys, numpy, pandas\n"Python " + sys.version.split()[0] + " / NumPy " + numpy.__version__ + " / Pandas " + pandas.__version__');
            postMessage({id:m.id,output:output || '执行完成。请用print(...)显示需要观察的结果。',version});
          } catch(error){postMessage({id:m.id,error:String(error.message||error),output});}
          finally{ns.destroy();}
        }
      } catch(error){postMessage({id:m.id,error:String(error.message||error)});}
    };
  }
  const engines=new Map();let counter=0;
  function engine(kind){
    if(engines.has(kind))return engines.get(kind);
    const source=(kind==='sql'?window.SQL_ENGINE_SOURCE+'\n':'')+`(${(kind==='sql'?sqlWorker:pythonWorker).toString()})();`;
    const url=URL.createObjectURL(new Blob([source],{type:'text/javascript'}));
    const worker=new Worker(url);URL.revokeObjectURL(url);
    const state={worker,ready:false,pending:null};engines.set(kind,state);
    worker.onmessage=({data:r})=>{
      if(!state.pending || state.pending.id!==r.id)return;
      const p=state.pending;state.pending=null;clearTimeout(p.timer);
      if(r.error){const err=new Error((r.output||'')+r.error);p.reject(err);}
      else {if(r.ready)state.ready=true;p.resolve(r);}
    };
    worker.onerror=e=>cancel(kind,e.message||'计算环境未能启动，请检查浏览器和网络后重试。');
    return state;
  }
  function request(state,message,timeout,kind){
    return new Promise((resolve,reject)=>{
      const id=++counter;
      state.pending={id,resolve,reject,timer:setTimeout(()=>cancel(kind,'已超过运行时限，计算已停止；请缩小查询或检查循环后重试。'),timeout)};
      state.worker.postMessage({...message,id});
    });
  }
  function cancel(kind,reason='已停止运行。再次点击运行可重新建立环境。'){
    const state=engines.get(kind);if(!state)return;
    state.worker.terminate();engines.delete(kind);
    if(state.pending){clearTimeout(state.pending.timer);state.pending.reject(new Error(reason));state.pending=null;}
  }
  async function run(kind,code,onStatus){
    const state=engine(kind);
    if(state.pending)throw Error('当前环境仍在运行，请先停止或等待完成。');
    if(!state.ready){
      onStatus(kind==='sql'?'正在本机建立SQLite数据表…':'正在联网加载Python、NumPy与Pandas；首次加载可能需要1–3分钟…');
      try {await request(state,{type:'init',rows:OBSERVATIONS.rows,columns:OBSERVATIONS.columns,hours:window.CLASSROOM_MODEL.hours},kind==='sql'?60000:180000,kind);}
      catch(e){cancel(kind);throw e;}
    }
    if(engines.get(kind)!==state)throw Error('计算已停止。');
    onStatus('正在本机执行，可随时停止…');
    return request(state,{type:'run',code},20000,kind);
  }
  window.ClassroomRuntimes={run,cancel,cancelBusy(){for(const [kind,s] of engines)if(s.pending)cancel(kind);}};
})();
