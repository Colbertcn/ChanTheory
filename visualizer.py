import mplfinance as mpf
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from chan_core import ChanEngine, Direction, FenXingType

# =================================================================================================
# 可视化模块 (Visualizer)
#
# 使用 mplfinance 库绘制K线图。
# 包含两个子图，上下对齐坐标轴：
# 1. 原始K线图 (Raw K-Lines)
# 2. 缠论标准K线图 (Chan Standard K-Lines)
#    - 使用自定义矩形绘制，宽度反映包含的K线数量
#    - 无上下影线 (实体柱)
#    - 叠加笔 (Bi)
# =================================================================================================

def plot_chan(df: pd.DataFrame, engine: ChanEngine, period: str = '15'):
    """
    绘制K线和缠论笔。
    Plots the K-lines and Chan Bi.
    
    参数:
        df: 原始K线数据DataFrame
        engine: 计算完毕的ChanEngine对象，包含笔的数据
        period: K线周期 (如 '1', '5', '15', '30')
    """
    # Ensure index is DatetimeIndex
    if 'datetime' in df.columns:
        df['datetime'] = pd.to_datetime(df['datetime'])
        df.set_index('datetime', inplace=True)
    
    # -------------------------------------------------------------------------
    # 1. 绘图设置 (Setup)
    # -------------------------------------------------------------------------
    s = mpf.make_mpf_style(base_mpf_style='charles', rc={'font.family': 'SimHei'})
    
    # 使用 mplfinance 获取 figure 和 axes，以便完全控制
    # 我们先在 ax1 画原始K线，这样 mplfinance 会自动处理日期索引的映射（0, 1, 2...）
    
    # 重新构建：手动创建 Figure 和 Axes
    fig = plt.figure(figsize=(24, 16))
    
    # 创建两个共享 X 轴的 subplot
    # GridSpec 允许我们控制比例
    gs = fig.add_gridspec(2, 1, height_ratios=[1, 1])
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[1, 0], sharex=ax1)
    
    # 画 Panel 1: 原始K线
    # ax=ax1 让 mpf 在指定轴上画图
    mpf.plot(df, type='candle', style=s, ax=ax1,
             ylabel='Raw Price',
             warn_too_much_data=len(df),
             axtitle=f'Raw K-Lines ({period} Min)')

    # -------------------------------------------------------------------------
    # 2. 画 Panel 2: 缠论标准K线 (Custom Drawing on ax2)
    # -------------------------------------------------------------------------
    # 为了保持 X 轴对齐，我们需要在 ax2 上使用与 ax1 相同的 X 坐标系统。
    # mplfinance 将 DataFrame 的行索引映射为 0, 1, 2 ... len(df)-1。
    # 因此，我们需要计算每个 Standard K-Line 对应的原始索引范围。
    
    # 为了让 ax2 拥有正确的 X 轴范围和刻度，我们在 ax2 上画一个透明的原始K线图
    # 这样可以初始化 X 轴
    mpf.plot(df, type='line', style=s, ax=ax2, 
             linecolor='none', # 不可见
             ylabel='Chan Price',
             warn_too_much_data=len(df),
             axtitle='Chan Standard K-Lines (Variable Width) + Bi')

    # 现在手动在 ax2 上添加矩形 (Standard K-Lines)
    # 颜色定义
    # s 是一个字典，但 structure 可能不同，通常 mplfinance style object 是 dict
    # 如果 make_mpf_style 返回的是 dict，我们需要检查 key
    # 'charles' style: up is green, down is red usually (in China red is up, green is down)
    # mplfinance 默认 'charles': up=green, down=red.
    # 但我们想要 红涨绿跌。
    # 我们可以直接指定颜色。
    
    # 手动定义红涨绿跌
    up_color = 'red'
    down_color = 'green'
    edge_up = 'red'
    edge_down = 'green'
    
    # 遍历标准K线
    for k in engine.standard_klines:
        # 获取该标准K线包含的原始K线索引范围
        raw_indices = [rk.index for rk in k.original_klines]
        if not raw_indices:
            continue
            
        start_idx = min(raw_indices)
        end_idx = max(raw_indices)
        
        # 计算绘制参数
        # 宽度：覆盖的原始K线数量 + 间隙
        # 规则：(1 + Merged_Count) * Unit_Width + Merged_Count * Gap
        # 在 mplfinance 的坐标系中，Gap 是 1 (index difference)。Unit_Width 通常是 0.6-0.8。
        # 我们可以简化理解：
        # 一个原始K线占据 X 轴长度为 1 (例如 index 5 到 6)
        # 包含处理后的K线，如果跨越了 indices [5, 6, 7]，那么它的逻辑宽度应该是 3。
        # 我们希望它的视觉宽度填满这 3 个单位。
        # 稍微留一点缝隙，比如每个单位 0.8。
        # 那么总宽度 = count * 0.8 (如果按比例) 或者 count - 0.2 (如果想填满整个区间)
        # 用户需求： "每包含了另一根K线后，这根K线都应该增加一个单位宽度"
        # 假设 1根K线宽 0.8。
        # 2根K线宽 0.8 + 1 + 0.2 (Gap?) = 2.0?
        # 其实最简单的逻辑是：该标准K线代表了原始数据中的 start_idx 到 end_idx。
        # 我们就让这个矩形覆盖从 start_idx - 0.4 到 end_idx + 0.4 的范围。
        # 这样它就完美对齐了上面对应的原始K线区域。
        
        # 原始K线的中心是 idx (整数)。宽度一般是 0.6 或 0.8。
        # 假设宽度 0.8，则范围是 [idx - 0.4, idx + 0.4]。
        # 如果包含 [5, 6, 7]，则覆盖范围是 [5-0.4, 7+0.4] = [4.6, 7.4]。
        # 宽度 = 7.4 - 4.6 = 2.8。
        # 中心 = (4.6 + 7.4) / 2 = 6.0。
        
        # 这种算法完美符合 "宽度随包含数量增加" 的直觉。
        
        count = end_idx - start_idx + 1
        bar_width_unit = 0.8 # 原始单根K线的视觉宽度
        total_width = (count - 1) * 1.0 + bar_width_unit # (N-1)*步长 + 最后一根的宽度
        
        # 矩形中心计算
        # start_idx 的左边缘: start_idx - bar_width_unit/2
        # end_idx 的右边缘: end_idx + bar_width_unit/2
        # 中心 = (左 + 右) / 2 = (start_idx + end_idx) / 2
        
        width = total_width
        x_center = (start_idx + end_idx) / 2.0
        
        # 高度和底部
        # 无影线：只画实体，从 Low 到 High
        height = k.high - k.low
        bottom = k.low
        
        # 颜色
        is_up = k.close >= k.open # 这里的 Open/Close 是包含处理后的逻辑方向
        face_color = up_color if is_up else down_color
        edge_color = edge_up if is_up else edge_down
        
        # 绘制矩形
        rect = patches.Rectangle(
            (x_center - width/2, bottom), # (left, bottom)
            width, 
            height,
            linewidth=1,
            edgecolor=edge_color,
            facecolor=face_color
        )
        ax2.add_patch(rect)

    # -------------------------------------------------------------------------
    # 3. 画笔 (Bi) on Panel 2
    # -------------------------------------------------------------------------
    # 笔连接的是分型点。我们需要找到分型点对应的 X 坐标。
    # 最好使用标准K线的中心坐标。
    
    def get_k_center(k_line):
        raw_indices = [rk.index for rk in k_line.original_klines]
        if not raw_indices:
            return k_line.index # Fallback
        return (min(raw_indices) + max(raw_indices)) / 2.0

    for bi in engine.bis:
        start_k = bi.start_fx.k_line
        end_k = bi.end_fx.k_line
        
        x1 = get_k_center(start_k)
        x2 = get_k_center(end_k)
        
        y1 = 0.0
        y2 = 0.0
        
        color = ''
        if bi.direction == Direction.DOWN:
            y1 = bi.start_fx.high
            y2 = bi.end_fx.low
            color = 'green'
        else:
            y1 = bi.start_fx.low
            y2 = bi.end_fx.high
            color = 'red'
            
        ax2.plot([x1, x2], [y1, y2], color=color, linewidth=2)

    # 保存图片
    filename = f'chan_chart_{period}m.png'
    fig.savefig(filename, bbox_inches='tight')
    print(f"Chart saved to {filename}")

