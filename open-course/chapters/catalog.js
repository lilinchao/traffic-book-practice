import {PROJECTS as PREVIOUS,CHAPTERS} from '../projects/catalog.js';
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
 {id:'ch04',chapter:4,chapterName:CHAPTERS[3],title:'共享单车小时需求回归',subtitle:'完成一份可自测的预测CSV，比较连续与计数模型',question:'知道天气与日历条件，能否估计这一小时的租借量？',level:'回归建模',time:'8—12小时',engine:'bike',file:'ch04',dataset:'Capital Bikeshare · 17,379小时',
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
for(const p of PROJECTS){Object.assign(p,specifications[p.id]);p.color=['#296b99','#087f8c','#7952a3','#25816e','#b96937','#3e66ad','#986786','#b5782d'][p.chapter-1];}
export const CASES=[
 {id:'records-demand',chapter:1,type:'概念辨析',title:'有上车记录，为什么仍不知道真实需求？',lead:'从纽约绿出租车数据区分已发生出行与未满足需求。',question:'如果某地区上车量很少，是否可以建议减少车辆？',evidence:'本课程TLC快照保留2024年1月的56,549条绿出租车上车记录。它记录了已经完成上车的活动，没有记录等不到车而放弃出行的人。',method:'先明确观测的是“上车事件”，再列出未满足需求、其他交通方式、供给限制等未观测因素。将增减车辆的建议改写为需要进一步验证的运营假设。',conclusion:'上车量可以支持样本内活动画像，不能单独决定增车或减车数量。',exercise:'写出验证“低上车量来自低需求”至少还需要的两种数据。',target:'ch07',source:'https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page'},
 {id:'problem-metric',chapter:1,type:'问题设计',title:'“事故多”与“事故风险高”是同一个问题吗？',lead:'同一份事故表，能支持数量排查，却未必能支持风险比较。',question:'怎样把“找最危险的路口”改写成当前数据可以回答的问题？',evidence:'2024年1月纽约事故快照有7,542条记录，但课程数据没有给出各路口通过车辆数、行人暴露量或完整道路长度。',method:'把任务先界定为事故记录的空间排查，输出需现场核查的候选区域。若需要比较单位暴露风险，再收集同一时空范围的分母。',conclusion:'更换研究问题比强行为现有数据套一个“风险模型”更重要。',exercise:'各写一句数量问题、风险问题和治理效果问题，列出它们的数据差别。',target:'ch05',source:'https://data.cityofnewyork.us/Public-Safety/Motor-Vehicle-Collisions-Crashes/h9gi-nx95'},
 {id:'duplicate-hours',chapter:2,type:'数据陷阱',title:'48,204行，为什么不是48,204个小时？',lead:'多行天气标签可能属于同一小时交通观测。',question:'同一时间出现两行记录，应当相加、平均还是保留一行？',evidence:'UCI I-94原始文件有48,204行，只包含40,575个不同小时标签。重复行共7,629条，核查未发现同小时交通量冲突。',method:'先按时间检查交通量是否一致，再将交通量按小时组织。保留原行数权重，比较直接对原始行取均值与按小时去重后的结果。',conclusion:'这里可以按小时合并相同交通量，但不能把同小时重复行的交通量相加。',exercise:'找一个去重前后小时均值差异较大的时段，解释权重变化。',target:'ch02',source:uci.url},
 {id:'missing-time',chapter:2,type:'质量审计',title:'字段没有空值，时间序列就完整了吗？',lead:'表内空值与应有时间标签缺失是两种质量问题。',question:'完整的365天为何只得到358个可用早高峰日期？',evidence:'将2017年07、08、09时交通量按日期组合后，只保留三小时均有观测的358天，7天无法形成完整的三小时组合。',method:'先生成应有的日期—小时索引，再与观测记录对齐。对缺口单独记录，不把缺测填成0，也不在划分训练和测试之前无条件插值。',conclusion:'缺失字段检查不能替代时间覆盖审计。',exercise:'给出缺测、真实零流量和设备异常各自可能需要的核查证据。',target:'ch03',source:uci.url},
 {id:'sample-size',chapter:3,type:'统计实验',title:'抽样20天与60天，哪个估计更稳定？',lead:'用固定随机种子比较均值和Bootstrap区间。',question:'样本量扩大后，某一次估计一定更接近参考均值吗？',evidence:'358个完整日期的早高峰均值约为4,652辆/小时。种子42、抽样60天、500次日级重采样时，样本均值约4,698，95%百分位区间约为[4,240,5,095]。',method:'固定条件比较20、60天，再改变随机种子重复实验。既观察区间宽度，也检查不同抽样的均值变化。',conclusion:'更大样本通常降低抽样波动，但不能保证每一次估计都更接近参考值，也不能消除系统性偏差。',exercise:'保存3个随机种子的结果，区分“单次更准确”和“总体更稳定”。',target:'ch03',source:uci.url},
 {id:'daily-blocks',chapter:3,type:'方法选择',title:'为何不把同一天的三个小时当作三个独立样本？',lead:'抽样单位改变了不确定性的解释。',question:'逐小时打乱抽样，会遗漏什么关系？',evidence:'本项目每个日期的统计量由07、08、09时共同形成。同日交通状态可能共享工作日、天气和出行结构等背景。',method:'先计算日期均值，再以日期为单位重采样，保留日内关系。继续检查平日/周末差异；若相邻日期也相关，应考虑多日区块或分层方案。',conclusion:'日级重采样改善了抽样单位定义，但不是对所有时间相关性的完整修正。',exercise:'说明按小时、按日与连续7日区块抽样各自在保留什么结构。',target:'ch03',source:uci.url},
 {id:'bike-leakage',chapter:4,type:'数据泄漏',title:'模型接近零误差，可能只是看到了答案',lead:'共享单车字段 casual 和 registered 不能用于预测 cnt。',question:'为什么两个看起来合理的用户特征会让结果失真？',evidence:'UCI Bike Sharing定义cnt为casual与registered之和。本项目从特征表中排除了这两个字段，保留独立的日历与天气条件。',method:'训练前绘制目标与字段关系表，检查标签分量、事后统计量和重复编码。若把标签拆分字段加入特征，即使测试误差很小也不代表有预测能力。',conclusion:'先审查特征在任务时点是否可知，再讨论模型分数。',exercise:'再举一种交通预测中可能泄漏标签的事后字段，并解释原因。',target:'ch04',source:'https://archive.ics.uci.edu/dataset/275/bike+sharing+dataset'},
 {id:'poisson-ridge',chapter:4,type:'模型对照',title:'计数目标一定要用泊松回归吗？',lead:'比较模型假设、误差与解释用途。',question:'如何评价岭回归和泊松回归在同一数据上的差别？',evidence:'按本项目时间切分，练习测试RMSE约为：均值245.82、岭回归168.84、泊松回归158.54次/小时。参数只用验证集选择；完整记录可在评价页查看。',method:'保持特征、样本和切分一致，比较RMSE、MAE、有符号误差。再检查计数的离散程度，以及分布跨年变化是否造成系统性低估。',conclusion:'这里的结果支持在这套协议下比较预测表现，不能证明某个模型对所有计数任务都最好。',exercise:'为什么“泊松模型误差更低”并不等于所有泊松分布假设都得到验证？',target:'ch04',source:'https://archive.ics.uci.edu/dataset/275/bike+sharing+dataset'},
 {id:'grid-size',chapter:5,type:'空间尺度',title:'网格从250米变成1000米，热点为什么换了？',lead:'聚合尺度改变了空间问题本身。',question:'候选区域顺序变化是程序错误吗？',evidence:'事故项目提供250、500、1000米三种近似米制网格。相同点集会在不同尺度下被组合为不同的单元。',method:'固定月份、行政区、网格原点与权重，只改变边长。比较同一地区是否被拆分或合并，不直接把不同大小单元的次数当作同一指标。',conclusion:'尺度敏感性应当成为报告证据，而不是选择一张“最好看”的图后省略。',exercise:'在两种尺度中各选3个候选网格，解释它们的对应关系。',target:'ch05',source:'https://data.cityofnewyork.us/Public-Safety/Motor-Vehicle-Collisions-Crashes/h9gi-nx95'},
 {id:'no-coordinates',chapter:5,type:'样本偏差',title:'474条无法落图的事故，能否直接忽略？',lead:'地图上没有显示，不等于现实中没有发生。',question:'空间结果应该使用哪个记录数作为分母？',evidence:'课程事故快照中7,542条记录有7,068条通过坐标边界检查，474条未进入空间聚合。',method:'在每次筛选后报告原始记录数与可落图数，核查排除原因和行政区未知情况。对“未落图是否随机”保持谨慎。',conclusion:'空间图只代表通过坐标检查的子集，缺失分布可能影响排查结论。',exercise:'设计一张坐标审计表，让读者看见被地图隐藏的记录。',target:'ch05',source:'https://data.cityofnewyork.us/Public-Safety/Motor-Vehicle-Collisions-Crashes/h9gi-nx95'},
 {id:'simple-baseline',chapter:6,type:'失败分析',title:'为什么岭回归输给了周期均值？',lead:'保留失败结果，检查特征和评估协议。',question:'模型更复杂，为什么没有带来更好的预测？',evidence:'1小时任务在共同的2,190个练习测试样本上，星期—小时均值MAE约218.04辆/小时，岭回归约461.01辆/小时。',method:'检查周期特征是否充分表达规律、滞后量是否稳定、预测跨度是否匹配。按高峰与非高峰拆分误差，不能靠换测试集让模型取胜。',conclusion:'简单基线是模型价值的参照，不是可以省略的步骤。',exercise:'提出一种不触碰测试标签的模型改进，并写出验证方式。',target:'ch06',source:uci.url},
 {id:'forecast-origin',chapter:6,type:'评估协议',title:'预测未来1小时和6小时，哪些信息不能共享？',lead:'特征可用性由预测起点决定。',question:'目标时刻相同，预测跨度不同，输入信息是否也相同？',evidence:'工作台提供1、3、6小时任务。每组预测按对应起点构建滞后特征，并在组内对齐各模型的有效样本。',method:'用时间轴标出起点、目标时刻和各滞后位置。区分逐时滚动预测与一次性预测未来数月，不把未来实测天气当成已知输入。',conclusion:'预测跨度是任务定义的一部分，不只是界面上的一个参数。',exercise:'画出6小时任务可用的三项滞后特征，并标注时间。',target:'ch06',source:uci.url},
 {id:'weekday-denominator',chapter:7,type:'统计口径',title:'平日总量更高，可能只是因为天数更多',lead:'比较23个平日和8个周末日之前，先对齐分母。',question:'总量排名可以直接当作典型日期的活动强度吗？',evidence:'2024年1月按周一至周五分组有23天，周六至周日有8天；本项目的“平日”并未排除节假日。',method:'同时展示累计总量与每日日均，用相同地区与时段对照。明确每个矩阵单元是累计次数还是次/日。',conclusion:'归一化改变了问题：一个回答总贡献，另一个回答平均日期的活动。',exercise:'保存同一组数据的总量与日均两份结果，解释差别而不是只比较颜色。',target:'ch07',source:'https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page'},
 {id:'similar-days',chapter:7,type:'模式探索',title:'31天聚出4类，能称为四种稳定出行模式吗？',lead:'日画像聚类是探索性证据，不是预测准确率。',question:'归一化后相似的日期，原始上车总量也相似吗？',evidence:'扩展代码对31个日期的地区×小时向量做日内总量归一化，再比较2至5类KMeans结果与轮廓系数。',method:'同时查看原始总量、标准化画像和类别变化。改变类别数与种子后核对稳定性，不把单月聚类直接当成全年规律。',conclusion:'相似形状和相似规模是两件事；小样本探索需要后续月份复核。',exercise:'找两个画像相近但总量不同的日期，说明运营解读有何不同。',target:'ch07',source:'https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page'},
 {id:'crossing-rule',chapter:8,type:'计数规则',title:'同一段轨迹，为什么会出现不同的通行数量？',lead:'虚拟线、死区与采样间隔共同定义跨线事件。',question:'把每帧检测到的车辆数量相加，得到的是交通量吗？',evidence:'本项目使用SinD天津公开样本前120秒的11,531个平滑轨迹点，涉及77个轨迹ID。工作台保留逐条跨线事件。',method:'固定线位置，逐一改变方向、采样间隔和断点阈值。选择ID回看跨线前后，解释重复检测、跨线事件和唯一通行车辆的区别。',conclusion:'交通量提取需要事件定义，不能直接对检测框或轨迹点求和。',exercise:'选择3个ID人工核对事件时间与方向，记录含糊情况。',target:'ch08',source:'https://github.com/SOTIF-AVLab/SinD'},
 {id:'trajectory-not-video',chapter:8,type:'系统评价',title:'轨迹回放流畅，是否说明视频检测准确？',lead:'明确检测、跟踪和计数三个评价层次。',question:'这段回放能用来证明YOLO或DeepSORT的效果吗？',evidence:'课程加载的是数据提供方发布的平滑车辆轨迹，不是课程新训练检测器的输出；当前样本不含原视频或独立人工计数真值。',method:'将图像检测框、跨帧ID和交通事件分别列为评价对象。完整视觉系统需要授权视频、对应人工标注以及分模块和最终交通指标。',conclusion:'当前可验证后处理规则与参数敏感性，不能据此报告新检测器的精度。',exercise:'设计一个完整视觉计数系统的核验表，注明每项指标需要的真值。',target:'ch08',source:'https://github.com/SOTIF-AVLab/SinD'},
];
export const TABS=[['overview','项目概述'],['data','数据'],['code','代码'],['evaluation','评价'],['submission','提交与自测'],['cases','案例'],['rules','规则']];
export const ALIASES={audit:'ch02',forecast:'ch06',hotspots:'ch05',taxi:'ch07',counting:'ch08'};
export const SOURCE_CARDS=[
 ['道路运行','UCI I-94','小时交通量、天气标签','单个断面；本地时间标签','交通量不等于车速，不能直接判断拥堵等级',uci.url],
 ['事故排查','NYC 事故记录','事故事件、位置、伤者人数','2024年1月；有无法落图记录','没有暴露量分母，不能直接排名风险','https://data.cityofnewyork.us/Public-Safety/Motor-Vehicle-Collisions-Crashes/h9gi-nx95'],
 ['出行画像','NYC TLC','已发生的出租车上车记录','绿出租车；课程仅发布聚合数据','不包含未满足需求或所有交通方式','https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page'],
 ['路口计数','SinD 天津样本','轨迹ID、时间、地面坐标','前120秒车辆平滑轨迹','不是原视频；遵循禁止商业使用的自定义数据许可','https://github.com/SOTIF-AVLab/SinD'],
];
