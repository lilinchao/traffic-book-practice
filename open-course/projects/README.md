# 交通数据挖掘：项目实践

本课程以真实问题和成果交付组织实践，教材继续承担理论主线。项目工作台用于探索与记录，完整分析可通过 Python 复现和扩展。

在线入口：https://lilinchao.github.io/traffic-book-practice/open-course/

## 五个项目

| 项目 | 主要任务 | 对应章节 | 建议工作量 |
| --- | --- | --- | --- |
| audit | 数据质量审计与接收结论 | 1、2、3 | 4—6小时 |
| forecast | 公平的交通量预测比较与误差分析 | 2、3、4、6 | 10—14小时 |
| hotspots | 事故坐标审计、网格与空间聚类对照 | 2、4、5 | 8—12小时 |
| taxi | 地区与时间画像、归一化和相似日分析 | 2、5、7 | 8—10小时 |
| counting | 真实轨迹上的通行计数规则与人工审计 | 2、5、8 | 8—12小时 |

工作量不是既定学时或课程要求，教师可以选择性安排。建议2—3人小组，完成 audit 后选一个专题做深入研究。

## 网页与记录

无需注册。改变参数后可保存一次实验，填写四阶段证据和报告，导出CSV、JSON配置与Markdown报告。数据和代码不会上传到服务器。浏览器只保存本机草稿，最多保留每项目最近20次实验，清理浏览器数据会删除记录，应及时导出。

网页没有学习管理系统后台，不自动收作业、不自动评分、不认定学生已经掌握知识。自查标记需要至少20字记录，但字数不代表质量。教师应阅读证据并组织答辩。

## 本地运行

解压 `project-kit.zip`，在解压目录运行：

```sh
python python/analyze.py --project audit
python python/analyze.py --project forecast --config forecast-experiment.json
python -m unittest discover -s tests -p "test_*.py"
```

参考分析仅依赖 Python 3.10 及以上的标准库。它读取随包附带的真实数据快照，在 `outputs` 生成完整结果和配置记录。

重新下载官方数据并训练预测模型：

```sh
python -m pip install -r python/requirements.txt
python python/prepare_data.py --output data
```

需要严格复现本次扩展环境时，可用 `python/requirements-tested.txt`。官网数据可能修订，原始下载SHA-256保存在数据JSON中。SinD使用固定提交与固定文件哈希。NYC事故数据再次提取的总数或字段可能发生变化，应当建立新快照，不能冒充同一数据版本。

## 深入分析

```sh
python python/extensions.py --project hotspots
python python/extensions.py --project taxi
python python/extensions.py --project counting
# 完成独立人工标注后，再评价计数事件
python python/extensions.py --project counting --truth manual-events.csv
```

- 空间扩展比较6组DBSCAN参数，输出点位类别、噪声比例和簇规模。没有自动推断危险路段。
- 时空扩展将31天的地区×小时记录归一化为每日份额，比较2—5类KMeans结果，并输出轮廓系数。该系数属于样本内聚类描述，不是预测准确率。
- 计数扩展比较采样与断点规则。只有提供独立人工事件表后，才输出匹配、漏计和误计统计。人工表字段为 `track_id,time_s,direction`，方向使用 `+x` 或 `-x`。默认审核x=15米、双方向、样本内全部车辆，时间容差1秒。

学生工作本在 `notebooks`，包含任务书、运行起点、对照要求和答辩问题。代码提供参考基线，学生必须增加对照并解释结果，不以直接运行默认程序作为项目完成标准。

## 网页本地预览

如已克隆完整仓库，在仓库根目录运行 `python -m http.server 8000`，打开 `http://localhost:8000/open-course/`。ES模块和JSON请求需要HTTP环境，不支持直接双击新网页的HTML。项目包侧重Python实践，不包含旧工具箱或第一章课件。

## 许可

本次新增的原创程序代码使用 MIT 许可，原创教学文字使用 CC BY-SA 4.0，署名为“交通数据挖掘理论与应用开放课程（lilinchao）”。数据采用各自原始条款，不能套用代码许可。

UCI数据须保留作者与数据集引用。NYC数据遵循原数据条款。SinD样本采用包含禁止商业使用约束的自定义数据条款，原文随包附在 `data/SIND-LICENSE.txt`；本项目仅用于非商业教学，不称其为标准CC0。项目包包含这些不同许可的材料，不能将整个压缩包声明为MIT。

原有小实验保留在 `../methods.html`，其中未充分核验的历史数值已提示不作为正式项目证据。第一章课堂保持在 `../chapter-01/`。
