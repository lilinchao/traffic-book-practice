# 交通数据挖掘：八章项目实践

每章对应一个项目，页面包含项目概述、数据、代码、评价、提交与自测、案例、规则七个栏目。另设16个案例的独立案例库。组织形式参考Kaggle的项目页面，但不接入Kaggle账号，不设置奖金、虚构参赛人数或跨学生排行榜。

## 章节项目

| 章节 | 实践项目 | 最终成果 |
| --- | --- | --- |
| 1 绪论 | 为一个交通问题设计数据方案 | 问题、变量、来源与可行性报告 |
| 2 数据组织与分析基础 | 原始交通记录的数据组织与审计 | 清洗CSV、质量报告、处理代码 |
| 3 数理理论基础 | 早高峰交通量抽样估计 | 日级抽样、区间估计与不确定性报告 |
| 4 交通表格型数据分析 | 共享单车小时需求回归 | 预测CSV、回归比较和误差分析 |
| 5 交通位置数据分析 | 纽约交通事故空间排查 | 网格/聚类对照、候选清单与证据 |
| 6 交通时序数据分析 | I-94道路小时交通量预测 | 预测CSV、时间协议与多步对照 |
| 7 交通时空数据分析 | 出租车时空出行画像 | 地区—小时矩阵及模式解释 |
| 8 交通影像数据分析 | 从路口轨迹到通行计数 | 跨线事件、规则审计和人工核验方案 |

每个项目有四阶段任务。章节项目聚焦一条可完成的主线，不声称覆盖教材中的所有方法。第8章重点落在8.7节跟踪后处理与交通参数提取，不把已有平滑轨迹冒充新训练的检测器。

## 资料包结构

下载`chapter-projects.zip`并解压，保持以下两个顶层目录在一起：

```text
chapters/
  notebooks/ch01.ipynb ... ch08.ipynb
  python/ch02_cleaning.py
  python/ch03_inference.py
  python/ch04_regression.py
  data/
  ch01_report.md ... ch08_report.md
  PROJECT_BRIEFS.md
  CASEBOOK.md
  README.md
  DATA_SOURCES.md
projects/
  python/analyze.py
  python/prepare_data.py
  python/extensions.py
  data/
  DATA_SOURCES.md
  LICENSE_CODE.txt
MANIFEST.json
```

`projects`目录复用经过核验的公共分析代码与数据，不再表示课程按五个跨章项目组织。

## 环境与运行

建议Python 3.11或更新版本。在解压后的根目录执行：

```bash
python -m pip install -r projects/python/requirements.txt
python -m pip install notebook
jupyter notebook chapters/notebooks/ch01.ipynb
```

第1章侧重方案设计，不要求模型训练。第2、3章基线脚本和公共`analyze.py`只使用Python标准库。第4章训练及其他扩展分析需要安装依赖。8个工作本可在Jupyter或支持Notebook的编辑器中运行。

```bash
python chapters/python/ch02_cleaning.py
python chapters/python/ch03_inference.py --n 60 --seed 42
python chapters/python/ch04_regression.py --output ch04_outputs
python projects/python/analyze.py --project hotspots
python projects/python/analyze.py --project forecast
python projects/python/extensions.py --project taxi
python projects/python/extensions.py --project counting
```

第4章脚本生成均值、岭回归、泊松回归三份预测CSV；第6章工作本示范1小时任务的标准提交。第7、8章工作本也生成对应CSV。第5章需要在真实网格结果基础上自行填写候选理由。

若需从原始UCI文件重建第2、3、4章数据与基线，可运行`python chapters/python/prepare_chapters.py`。该脚本也重建第6章的1小时提交接口；公共交通量快照的完整上游处理过程在`projects/python/prepare_data.py`。重建会更新本地数据文件，实验时应保留原版本并核对哈希。

## 提交与自测

- 第1章：Markdown中包含“研究问题、数据方案、指标定义、局限与许可”四个标题。网页只检查结构。
- 第2章：完整40,575行`local_time,volume`，与公开参考清洗结果检查一致性。
- 第3章：1行`estimate,lower,upper,n_days`，参数与假设另附报告。
- 第4章：4,376行`id,cnt`，按ID对齐计算RMSE、MAE和有符号偏差。
- 第5章：至少3行`grid_id,reason`，采用全部行政区、固定原点、500米网格，理由需由学生填写。其他尺度另附配置。
- 第6章：1小时任务全部2,190行`id,volume`。3/6小时任务不混入这一提交接口。
- 第7章：168行`borough,hour,value`，固定2024年1月全部日期、全天、每日日均，保留7个源地区标签。
- 第8章：`track_id,time_s,direction`事件表，附计数配置与人工核查方案。格式检查不计算检测/计数准确率。

第4、6章测试标签公开，是学习用自测，不是隐藏测试。网页在本机读取文件，没有服务器收作业、云端Python环境、账号管理、防作弊或全班排名。不要用这些公开标签来调整模型。教师的正式评价还需代码审阅、报告和答辩。

分析记录、案例笔记和最近10条实验/自测记录保存在本机浏览器；请导出报告和记录备份。网页不会索要姓名、学号或个人轨迹。

## 网页运行

完整网页源码在仓库`open-course`目录。需通过HTTP服务访问，不能直接双击HTML。资料包主要用于Python实践，不是完整网页离线镜像。

第一章课件保持原路径`chapter-01/`。历史方法实验保留在`methods.html`；上一版五项目及其本机记录可从`project-archive.html`打开。

## 许可

新增课程代码沿用`projects/LICENSE_CODE.txt`中的MIT许可；任务书与案例文本沿用课程CC BY-SA 4.0许可，署名“交通数据挖掘开放课程”。各原始数据遵循其提供者的许可，不被课程代码或文本许可重新授权。SinD为禁止商业使用的自定义条款，不能称为标准CC0。
