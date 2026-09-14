# 交通数据挖掘开放课程

《交通数据挖掘理论与应用》的静态开放课程网站。主入口以五个跨章节项目组织实践，覆盖数据审计、预测评估、事故空间分析、出租车时空画像与真实轨迹计数审计。

发布地址：`https://lilinchao.github.io/traffic-book-practice/open-course/`

## 本地预览

```powershell
python -m http.server 8000
```

在本目录启动时打开 `http://localhost:8000`；在仓库根目录启动时打开 `http://localhost:8000/open-course/`。新项目页使用ES模块，需要HTTP环境，不能直接双击HTML。

## 内容

- 5个项目任务书，20个阶段里程碑，跨章节映射与建议工作量
- 真实数据快照、来源哈希、字段口径、许可与处理代码
- 参数分析工作台、实验对照、本机草稿与CSV、JSON、报告导出
- Python参考分析、深入比较、5份学生工作本和教师实施指南
- 第一章独立教学课件与交互课堂：`chapter-01/`
- 历史方法示例及原有脚本保留在 `methods.html` 和 `practice/`，不作为新项目默认验收依据
- 桌面端和移动端响应式布局

新项目的浏览器工作台用JavaScript计算，预测项目重算已冻结预测的误差，Python训练通过项目包在本地进行。不要把参数筛选称作浏览器模型训练。新项目记录仅存本机，不提供账号、后台收作业或自动评分。历史工具箱仍保留Pyodide运行方式。

详细说明、数据条款和下载内容见 [项目实践README](projects/README.md)。

## GitHub Pages

本页面作为现有 `traffic-book-practice` 站点的 `open-course/` 子页面发布。

## 开放许可

- 页面与实践代码：MIT License
- 原创课程文字与图表：CC BY-SA 4.0
- 第三方数据集：遵循各数据源自己的许可与使用条款
