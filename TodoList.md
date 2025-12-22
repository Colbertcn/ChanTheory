# Todo List: 引入真实股市数据与多周期支持

## 1. 准备工作 (Preparation)
- [x] **外部配合**: 确认数据源选择 (默认使用 AkShare，免费且无需注册)
- [x] 安装 Python 依赖库
    - `pip install akshare`

## 2. 代码开发 (Development)
- [x] 创建 `data_fetcher.py`
    - 实现 `fetch_csi300_data` 函数。
    - 使用 AkShare 获取沪深300指数数据。
    - 确保数据清洗并转换为 DataFrame (datetime, open, high, low, close, volume)。
- [x] 修改 `main.py`
    - 导入新的数据获取模块。
    - 替换 `generate_csi300_data` 为新的获取函数。
    - **新增**: 支持循环处理 1分钟、5分钟、30分钟 数据。
- [x] 修改 `visualizer.py`
    - **新增**: 支持传入 `period` 参数，动态生成标题和文件名。
- [x] 创建/修改 `run.bat`
    - 实现一键运行。
    - 运行结束后自动打开生成的图表。

## 3. 测试与验证 (Verification)
- [x] 运行 `main.py` (或 `run.bat`)。
- [x] 验证生成 `chan_chart_1m.png`, `chan_chart_5m.png`, `chan_chart_30m.png`。
- [x] 确认数据时间戳为最新真实时间。
