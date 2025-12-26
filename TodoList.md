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
    - **新增**: 支持日线数据 ('daily') 获取。
- [x] 修改 `main.py`
    - 导入新的数据获取模块。
    - 替换 `generate_csi300_data` 为新的获取函数。
    - **新增**: 支持循环处理 1分钟、5分钟、30分钟 数据。
    - **新增**: 启动 GUI 界面 (`gui_app.py`)。
- [x] 修改 `visualizer.py`
    - **新增**: 支持传入 `period` 参数，动态生成标题和文件名。
    - **新增**: 支持返回 Figure 对象以嵌入 GUI。
- [x] 创建 `gui_app.py`
    - 实现 Tkinter 主界面。
    - **迭代优化**:
        - 移除复杂的 Slider 和 RadioButton。
        - 改为 7 个预设场景按钮 (如 "1 Min / 1 Day", "Daily / 60 Days" 等)。
        - 实现后台多线程异步加载数据，解决启动卡顿问题。
        - 增加加载状态检查，数据未就绪时弹窗提示。

## 4. 独立执行程序 (Custom Runner)
- [x] 修改 `data_fetcher.py`
    - 支持指定 `start_date` 和 `end_date` 精确参数。
- [x] 创建 `custom_runner.py`
    - 实现命令行交互界面。
    - 支持输入 1/5/30 分钟周期。
    - 支持输入起止日期 (MM-DD)，自动补全年份。
    - 获取数据并调用 `plt.show()` 弹窗显示。
- [x] 创建 `run_custom.bat`
    - 实现一键启动自定义程序。

## 5. 测试与验证 (Verification)
- [x] 运行 `run_custom.bat`。
- [x] 验证输入参数能否正确获取对应时间段数据。
- [x] 验证图表显示是否正常。
