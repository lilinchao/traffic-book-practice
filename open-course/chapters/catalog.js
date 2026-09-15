import {PROJECTS as PREVIOUS,CHAPTERS} from '../projects/catalog.js';
import {applyProjectProtocol} from './project-protocols.js';
export {CHAPTERS};
const source=(title,url,license)=>({title,url,license});
const uci=source('UCI I-94 小时交通量','https://archive.ics.uci.edu/dataset/492/metro+interstate+traffic+volume','CC BY 4.0 · John Hogue (2019)');
const prior=id=>PREVIOUS.find(p=>p.id===id);
const base=(chapter,id,extra)=>{const p=prior(id);return {...p,id:`ch${String(chapter).padStart(2,'0')}`,chapter,chapterName:CHAPTERS[chapter-1],engine:id,tasks:p.stages.map(s=>[s[1].slice(3),s[3],s[4]]),...extra};};
export const PROJECTS=[
 {id:'ch01',chapter:1,chapterName:CHAPTERS[0],title:'为一个交通问题设计数据方案',subtitle:'从“哪里堵”走向可以验证的研究问题',question:'数据很多，是否就能回答你真正关心的交通问题？',level:'方案设计',time:'3—4小时',engine:'design',file:null,dataset:'4类真实开放数据源',source:source('4类数据的官方来源汇总','https://lilinchao.github.io/traffic-book-practice/open-course/chapters/DATA_SOURCES.md','各源遵循原始许可；SinD含禁止商业使用的自定义条款'),
  commission:'你所在的小组需要为交通管理部门提出一项可验证的分析任务。请从道路运行、事故排查、出行画像、路口计数四个情境中选择一个，界定服务对象、空间与时间范围，再选择能够支持问题的数据。最终交付的是数据分析方案，不是先挑一个算法。',
  deliverables:['一页交通问题定义','问题—变量—数据对应表','数据获取与许可清单','可行性及限制说明'],
  boundaries:['观测记录不自动等于需求、风险或因果证据。','不同城市、时期和交通方式的数据不可无条件拼接。','所有源均为真实开放资源；选题需尊重各自许可。'],
  tasks:[['界定任务','选定一个交通场景，明确服务对象和待支持的决策。把“改善交通”改为可回答的研究问题。','问题、对象、范围、预期输出。'],['选择数据','比较4种来源的观测单元、时间覆盖、空间定位和访问条件。','至少两种备选来源的适配比较。'],['建立证据链','将研究问题拆为变量和指标，说明哪些信息可以直接观测，哪些只能近似。','问题—指标—字段对应表。'],['可行性审查','指出现有数据不能支撑的结论，提出一个最低可行方案。','可行性、隐私许可与补充数据清单。']],
  acceptance:['明确交通对象与时空范围。','至少一项指标能回到真实字段。','包含至少一项数据无法回答的问题。'],extensions:['将问题缩小到本校周边路口，列出合规的数据采集方案。','交换方案，尝试找到无法由现有数据支持的结论。']},
 base(2,'audit',{title:'把原始交通记录整理成可靠的数据表',subtitle:'数据组织、时间索引与质量审计',level:'数据工程'}),
 {id:'ch03',chapter:3,chapterName:CHAPTERS[2],title:'估计早高峰交通量，并说明不确定性',subtitle:'以日期为抽样单位，理解均值、方差与区间估计',question:'只观察60天，能否概括一年的早高峰交通量？',level:'统计推断',time:'5—7小时',engine:'inference',file:'ch03',dataset:'I-94 2017年358个完整日期',source:uci,
  commission:'监测部门希望了解早高峰平均交通量，但希望先用较少的日期做初步估计。你需要定义早高峰统计口径，从真实观测日期中抽样，估计均值并构造日级Bootstrap百分位区间，比较抽样规模、随机种子和日期类型带来的变化。',
  deliverables:['抽样总体与单位说明','均值和区间结果CSV','至少3组抽样对照','不确定性解释短报告'],
  boundaries:['本项目早高峰定义为07、08、09时三个小时，单位为辆/小时。','仅保留三个小时均有记录的日期；358天不等于完整365天。','以日期为块保留同日关系，但不能完全解决相邻日期的相关性。','95%百分位区间依赖抽样与近似独立假设，不是“真实均值有95%概率落在这次区间”的证明。'],
  tasks:[['定义统计量','解释小时流量、日内早高峰均值和年度日期均值的区别。核查7个被排除日期。','观测单元和排除规则。'],['抽样与估计','固定随机种子，对比20、60天样本的均值。','至少两种样本量的CSV及参数。'],['区间与分组','构造日级Bootstrap区间，再比较平日与周末。样本量和异质性分别影响什么？','区间宽度与分组解释。'],['推断边界','区分样本波动、系统性缺失和长期趋势，说明为什么不能外推至其他道路。','假设清单及多日区块Bootstrap拓展方案。']],
  acceptance:['给出抽样单位、样本量、种子与重复次数。','区间与均值单位一致。','未将抽样不确定性当成所有数据偏差。'],extensions:['改为按月份分层抽样，对比分层前后区间。','使用连续多日区块重采样，检验序列相关性的影响。']},
 {id:'ch04',chapter:4,chapterName:CHAPTERS[3],title:'共享单车小时租借量估计',subtitle:'面向高峰服务准备的回归建模与误差诊断',question:'知道天气与日历条件，能否估计这一小时的租借量？',level:'回归建模',time:'8—12小时',engine:'bike',file:'ch04',dataset:'Capital Bikeshare · 17,379小时',
  source:source('UCI Bike Sharing','https://archive.ics.uci.edu/dataset/275/bike+sharing+dataset','CC BY 4.0 · Hadi Fanaee-T (2013)'),
  commission:'你要为共享单车运营分析建立小时租借量回归模型。使用2011年数据训练、2012年上半年选择参数，生成2012年下半年的逐小时估计。对比训练均值、岭回归和泊松回归，提交格式统一的预测文件，并解释时段误差与跨年分布变化。',
  deliverables:['数据与特征审计','训练和验证记录','id,cnt 格式的预测CSV','模型比较与误差报告'],
  boundaries:['casual 与 registered 相加即为标签 cnt，不得作为特征。','这里使用给定的实测天气做条件回归，不是已经实现天气未知时的提前预测。','2011与2012可能存在需求增长等分布差异，不能把误差都归因于天气。','练习测试标签公开，浏览器自测不是隐藏测试或正式比赛成绩。'],
  tasks:[['审查字段','识别字段类型、计数标签与泄漏变量，明确实测天气的可获得性。','字段字典与排除清单。'],['建立基线','先运行训练均值，再对比岭回归与泊松回归；所有预处理仅在训练集拟合。','三类模型及训练/验证记录。'],['生成提交','为4376个测试ID生成非负租借量，在提交页检查格式和误差。','完整预测CSV及生成代码。'],['解释结果','比较白天、夜间和极端误差，讨论跨年变化与模型假设。','失败样本、误差分组和结论边界。']],
  acceptance:['训练、验证、练习测试用途清晰。','没有使用标签分量或测试标签训练。','CSV包含所有测试ID且无重复、空值和负数。'],extensions:['保持相同时间协议，引入负二项模型或梯度提升作对照。','检查计数过度离散，区分预测误差评价和参数解释。']},
 base(5,'hotspots',{title:'纽约交通事故空间排查',subtitle:'从坐标质量到网格、聚类与候选地点',level:'空间分析'}),
 base(6,'forecast',{title:'I-94道路小时交通量预测',subtitle:'按时间验证模型，比较多步预测与周期基线',level:'时序预测'}),
 base(7,'taxi',{title:'出租车时空出行画像',subtitle:'将行程记录组织成地区—日期—小时矩阵',level:'时空分析'}),
 base(8,'counting',{title:'从路口轨迹到通行计数',subtitle:'审计影像分析的跟踪后处理与交通参数提取',level:'影像后处理'}),
];
const specifications={
 ch01:{metric:'方案与证据审查',sections:'1.1—1.4：交通数据、问题与分析流程',format:'Markdown 报告',header:null,sample:'# 研究问题\n\n# 数据方案\n\n# 指标定义\n\n# 局限与许可\n',code:null,notebook:'ch01'},
 ch02:{metric:'处理规则与数据一致性',sections:'第2章：数据组织、清洗与质量核查',format:'CSV · local_time,volume',header:['local_time','volume'],sample:'local_time,volume\n2012-10-02T09:00,5545\n2012-10-02T10:00,4516\n',code:'chapters/python/ch02_cleaning.py',notebook:'ch02'},
 ch03:{metric:'抽样设计与区间解释',sections:'3.2 概率论基础；3.5 建模与评价',format:'CSV · estimate,lower,upper,n_days',header:['estimate','lower','upper','n_days'],sample:'estimate,lower,upper,n_days\n4697.95,4240.01625,5095.003056,60\n',code:'chapters/python/ch03_inference.py',notebook:'ch03'},
 ch04:{metric:'RMSE（次/小时）· 越低越好',sections:'4.2 预处理；4.3 连续回归；4.5 计数回归；4.7 解释',format:'CSV · id,cnt',header:['id','cnt'],sample:null,code:'chapters/python/ch04_regression.py',notebook:'ch04'},
 ch05:{metric:'空间敏感性与候选清单',sections:'第5章：坐标、空间聚合与密度聚类',format:'CSV · grid_id,reason',header:['grid_id','reason'],sample:'grid_id,reason\n请填工作台网格ID,请说明选择依据\n',code:'projects/python/extensions.py',notebook:'ch05'},
 ch06:{metric:'RMSE / MAE（辆/小时）',sections:'第6章：时间划分、基线与多步预测',format:'CSV · id,volume（1小时任务）',header:['id','volume'],sample:null,code:'projects/python/prepare_data.py',notebook:'ch06'},
 ch07:{metric:'时空口径与对照分析',sections:'第7章：时空矩阵、归一化与模式分析',format:'CSV · borough,hour,value',header:['borough','hour','value'],sample:'borough,hour,value\nManhattan,0,请填真实结果\n',code:'projects/python/extensions.py',notebook:'ch07'},
 ch08:{metric:'事件核查与参数敏感性',sections:'8.1 影像数据；8.7 目标跟踪与交通参数提取',format:'CSV · track_id,time_s,direction',header:['track_id','time_s','direction'],sample:'track_id,time_s,direction\n请填真实ID,请填秒数,+x\n',code:'projects/python/analyze.py',notebook:'ch08'},
};
for(const p of PROJECTS){Object.assign(p,specifications[p.id]);applyProjectProtocol(p);p.color=['#296b99','#087f8c','#7952a3','#25816e','#b96937','#3e66ad','#986786','#b5782d'][p.chapter-1];}
export const CASES=[
 {id:'records-demand',chapter:1,type:'出租车服务规划',title:'纽约绿出租车服务覆盖诊断与补充调查设计',lead:'围绕地区服务差异与夜间出行保障，识别已实现服务、潜在需求和运力配置之间的证据缺口。',question:'哪些地区与时段应优先开展出租车服务调查，现有上车记录能为运力配置提供哪些依据？',target:'ch07',source:'https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page'},
 {id:'problem-metric',chapter:1,type:'道路交通安全',title:'面向道路安全治理的事故排查任务与指标体系设计',lead:'以事故频次和伤者负担建立候选区域清单，衔接路网筛查、现场诊断与治理评价。',question:'在缺少交通暴露量的条件下，如何提出可执行的道路安全排查任务，而不是直接宣布“最危险路口”？',target:'ch05',source:'https://data.cityofnewyork.us/Public-Safety/Motor-Vehicle-Collisions-Crashes/h9gi-nx95'},
 {id:'duplicate-hours',chapter:2,type:'交通运行监测',title:'I-94断面交通量监测数据整编与日变化曲线偏差分析',lead:'从检测断面的观测口径出发，分析天气多标签关联如何影响小时交通量与运行报表。',question:'如何将多行来源记录还原为可靠的断面小时交通量，并量化整编规则对日变化曲线的影响？',target:'ch02',source:uci.url},
 {id:'missing-time',chapter:2,type:'交通调查质量',title:'连续监测缺测条件下的早高峰交通量样本重建',lead:'为早高峰调查与年度对照建立完整日期样本，评价观测中断带来的代表性问题。',question:'监测时间覆盖不完整时，怎样构建口径一致的早高峰样本，并说明其适用范围？',target:'ch03',source:uci.url},
 {id:'sample-size',chapter:3,type:'交通调查设计',title:'面向调查成本与精度平衡的道路早高峰抽样方案',lead:'以20、60、90天观测方案为对照，研究断面早高峰交通量估计精度与调查工作量。',question:'在固定道路和统计目标下，增加调查日期能改善多少估计精度，如何形成有依据的调查方案？',target:'ch03',source:uci.url},
 {id:'daily-blocks',chapter:3,type:'交通需求时变性',title:'平日与周末早高峰差异及分类型交通调查方案',lead:'识别断面交通量的日期类型差异，讨论为何不能用混合日期均值替代工作日运行基准。',question:'若调查目标是通勤相关时段的运行特征，应如何定义日期总体与抽样单元？',target:'ch03',source:uci.url},
 {id:'bike-leakage',chapter:4,type:'共享单车运营',title:'面向共享单车运力准备的小时租借量估计与信息可用性研究',lead:'以Capital Bikeshare为例，分析高峰租借活动、运营决策时点、可用特征与总量估计的应用边界。',question:'运营人员能否依据日历与天气估计小时租借量，为高峰服务准备提供依据，而不使用事后才知道的租借记录？',target:'ch04',source:'https://archive.ics.uci.edu/dataset/275/bike+sharing+dataset'},
 {id:'poisson-ridge',chapter:4,type:'高峰服务保障',title:'共享单车高峰租借量低估诊断与回归模型适用性比较',lead:'将岭回归与泊松回归评价落到早晚重点时段，比较绝对误差、系统偏差与未抵消低估量，讨论服务准备风险。',question:'总体误差较低的模型，能否同时减轻高峰租借量低估，为运营准备提供更可靠的参考？',target:'ch04',source:'https://archive.ics.uci.edu/dataset/275/bike+sharing+dataset'},
 {id:'grid-size',chapter:5,type:'事故空间排查',title:'纽约道路事故集中区域识别与多尺度排查范围确定',lead:'对同一事故点集进行250、500、1000米聚合，区分片区初筛与具体道路设施诊断。',question:'有限排查资源下，怎样选择事故筛查尺度，避免把大网格的高计数误当作某个路口的高风险？',target:'ch05',source:'https://data.cityofnewyork.us/Public-Safety/Motor-Vehicle-Collisions-Crashes/h9gi-nx95'},
 {id:'no-coordinates',chapter:5,type:'道路安全数据治理',title:'事故定位缺失对区域安全排查覆盖的影响',lead:'研究未能落图的事故在地区间是否均匀分布，为事故补定位和排查覆盖审查确定优先顺序。',question:'哪些区域的事故更容易被地图遗漏，应如何组织补定位与现场核查，避免排查资源随数据完整性偏移？',target:'ch05',source:'https://data.cityofnewyork.us/Public-Safety/Motor-Vehicle-Collisions-Crashes/h9gi-nx95'},
 {id:'simple-baseline',chapter:6,type:'道路运行预测',title:'I-94断面小时交通量预测及高峰运行监测适用性评价',lead:'以周期交通规律为参照，比较岭回归与同期基线在总体和重点运行时段的预测表现。',question:'复杂模型是否真正改善了道路断面预测，哪些时段仍需要人工复核或更充分的运行信息？',target:'ch06',source:uci.url},
 {id:'forecast-origin',chapter:6,type:'运行管理时效',title:'面向分级运行准备的1—6小时交通量预测时效研究',lead:'围绕临近监测与提前准备的不同信息条件，比较共同目标时刻上的多提前量预测。',question:'若管理任务需要提前1、3或6小时掌握断面交通量，信息边界与误差应怎样共同评价？',target:'ch06',source:uci.url},
 {id:'weekday-denominator',chapter:7,type:'出租车分时运营',title:'皇后区出租车平日通勤时段与周末夜间服务活动对比',lead:'将月度总量分解为日期与小时结构，识别被全天均值掩盖的夜间运营差异。',question:'平日与周末日均上车总量接近，是否意味着可以使用相同的分时运营准备方案？',target:'ch07',source:'https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page'},
 {id:'similar-days',chapter:7,type:'典型日运营分析',title:'基于地区—小时画像的出租车典型服务日识别',lead:'从31天实际上车活动中提取候选日型，联合考察服务时空形态、总量与跨日稳定性。',question:'能否将日型作为运营复盘的组织方式，同时避免把相似形态误解为相同运力需要？',target:'ch07',source:'https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page'},
 {id:'crossing-rule',chapter:8,type:'交叉口交通调查',title:'天津交叉口虚拟检测线通行统计与采样敏感性分析',lead:'用真实车辆轨迹生成分方向、分时段通行事件，分析抽帧和防抖规则对交通调查结果的影响。',question:'如何从重复出现的车辆轨迹中提取可复核的断面通行事件，并判断采样简化损失了哪些信息？',target:'ch08',source:'https://github.com/SOTIF-AVLab/SinD'},
 {id:'trajectory-not-video',chapter:8,type:'交通检测系统评价',title:'面向交叉口流量调查的视频计数系统核验方案',lead:'围绕交通调查成果的可信度，贯通目标检测、身份关联、通行事件与独立人工核验。',question:'一套视频计数系统需要提供哪些独立证据，才能说明其结果适合交叉口交通量调查？',target:'ch08',source:'https://github.com/SOTIF-AVLab/SinD'},
];
export const TABS=[['overview','项目概述'],['data','数据'],['code','代码'],['evaluation','评价'],['submission','提交与自测'],['cases','案例'],['rules','规则']];
export const ALIASES={audit:'ch02',forecast:'ch06',hotspots:'ch05',taxi:'ch07',counting:'ch08'};
export const SOURCE_CARDS=[
 ['道路运行','UCI I-94','小时交通量、天气标签','单个断面；本地时间标签','交通量不等于车速，不能直接判断拥堵等级',uci.url],
 ['事故排查','NYC 事故记录','事故事件、位置、伤者人数','2024年1月；有无法落图记录','没有暴露量分母，不能直接排名风险','https://data.cityofnewyork.us/Public-Safety/Motor-Vehicle-Collisions-Crashes/h9gi-nx95'],
 ['出行画像','NYC TLC','已发生的出租车上车记录','绿出租车；课程仅发布聚合数据','不包含未满足需求或所有交通方式','https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page'],
 ['路口计数','SinD 天津样本','轨迹ID、时间、地面坐标','前120秒车辆平滑轨迹','不是原视频；遵循禁止商业使用的自定义数据许可','https://github.com/SOTIF-AVLab/SinD'],
];
