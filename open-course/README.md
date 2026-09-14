# 交通数据挖掘开放课程

《交通数据挖掘理论与应用》的静态开放课程网站。主入口按教材八章组织为八个实践项目，采用中文项目概述、数据、代码、评价、提交与自测、案例、规则栏目；另设16个案例的独立案例库。

发布地址：`https://lilinchao.github.io/traffic-book-practice/open-course/`

## 本地预览

```powershell
python -m http.server 8000
```

在本目录启动时打开 `http://localhost:8000`；在仓库根目录启动时打开 `http://localhost:8000/open-course/`。新项目页使用ES模块，需要HTTP环境，不能直接双击HTML。

## 内容

- 8个章节项目、32个阶段任务、16个配套案例与建议工作量
- 真实数据快照、来源哈希、字段口径、许可与处理代码
- 参数分析工作台、实验对照、本机草稿与CSV、JSON、报告导出
- Python参考分析、深入比较、8份学生工作本、任务书和案例册
- 第4、6章预测CSV本机自测；其他章节按项目契约检查文件组织并由教师审阅
- 第一章独立教学课件与交互课堂：`chapter-01/`
- 历史方法示例及原有脚本保留在 `methods.html` 和 `practice/`，不作为新项目默认验收依据
- 桌面端和移动端响应式布局

浏览器工作台用JavaScript计算，预测项目重算已冻结预测的误差，Python训练通过资料包在本地进行。预测标签公开，自测不是隐藏测试或正式课程成绩。记录仅存本机，不提供账号、后台收作业或全班排名。历史工具箱仍保留Pyodide运行方式；上一版项目与本机记录可通过`project-archive.html`访问。

详细说明、数据条款和下载内容见 [章节实践README](chapters/README.md)。

## GitHub Pages

本页面作为现有 `traffic-book-practice` 站点的 `open-course/` 子页面发布。

## 开放许可

- 页面与实践代码：MIT License
- 原创课程文字与图表：CC BY-SA 4.0
- 第三方数据集：遵循各数据源自己的许可与使用条款
