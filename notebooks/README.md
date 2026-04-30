# Notebooks

各章可执行 Notebook。

## 安装依赖

```bash
pip install -r requirements.txt
```

## 第 2 章

数据库操作与 Python 数据处理：

```bash
jupyter notebook notebooks/chapter-02/
```

## 第 4 章

交通事故面板分析：

```bash
jupyter notebook notebooks/chapter-04/traffic_accident_panel_analysis.ipynb
```

## 第 5 章

交通空间分析：

```bash
jupyter notebook notebooks/chapter-05/
```

## 第 6 章

交通时序分析：

```bash
jupyter notebook notebooks/chapter-06/
```

## 第 7 章

交通时空分析：

```bash
jupyter notebook notebooks/chapter-07/
```

## 第 8 章

交通影像分析：

```bash
jupyter notebook notebooks/chapter-08/
```

## 数据刷新

```bash
bash scripts/download_case_data.sh
python scripts/generate_synthetic_flow.py
python scripts/generate_synthetic_network.py
```
