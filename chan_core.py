from enum import Enum
import pandas as pd
from typing import List, Optional

# =================================================================================================
# 缠论核心逻辑库 (Chan Theory Core Library)
#
# 本文件实现了缠论标准作业程序的前三个阶段：
# 1. K线包含处理 (K-Line Inclusion Processing)
# 2. 顶底分型识别 (Top/Bottom FenXing Identification)
# 3. 笔的绘制 (Bi/Stroke Drawing) - 包含严格的5K原则和回溯逻辑
# =================================================================================================

class Direction(Enum):
    """趋势方向枚举 / Trend Direction Enum"""
    UP = 1    # 向上
    DOWN = -1 # 向下

class ChanKLine:
    """
    缠论标准K线类 (Standard Chan K-Line)
    
    用于存储包含处理后的K线数据。
    包含处理后的K线可能由多根原始K线合并而成。
    """
    def __init__(self, index, datetime, open_price, high, low, close, volume, original_klines=None):
        self.index = index
        self.datetime = datetime
        self.open = open_price
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume
        # List of original KLines this standard KLine is composed of (for traceability)
        # 构成这根标准K线的原始K线列表（用于溯源）
        self.original_klines = original_klines if original_klines else []

    def __repr__(self):
        return f"KLine(dt={self.datetime}, H={self.high}, L={self.low})"

class FenXingType(Enum):
    """分型类型枚举 / FenXing Type Enum"""
    TOP = 1    # 顶分型
    BOTTOM = -1 # 底分型

class FenXing:
    """
    分型类 (Fractal/FenXing)
    
    记录分型的关键信息：类型（顶/底）、时间、极值点。
    """
    def __init__(self, k_line: ChanKLine, type: FenXingType):
        self.k_line = k_line # 分型中间的那根K线
        self.type = type
        self.datetime = k_line.datetime
        self.high = k_line.high
        self.low = k_line.low

    def __repr__(self):
        t = "TOP" if self.type == FenXingType.TOP else "BOTTOM"
        return f"{t}(dt={self.datetime}, H={self.high}, L={self.low})"

class Bi:
    """
    笔类 (Stroke/Bi)
    
    连接顶分型和底分型的线段。
    Direction.UP: 底 -> 顶 (向上笔)
    Direction.DOWN: 顶 -> 底 (向下笔)
    """
    def __init__(self, start_fx: FenXing, end_fx: FenXing):
        self.start_fx = start_fx
        self.end_fx = end_fx
        self.direction = Direction.UP if end_fx.high > start_fx.high else Direction.DOWN
        self.high = max(start_fx.high, end_fx.high)
        self.low = min(start_fx.low, end_fx.low)

    def __repr__(self):
        d = "UP" if self.direction == Direction.UP else "DOWN"
        return f"Bi({d}, {self.start_fx.datetime} -> {self.end_fx.datetime})"

class ChanEngine:
    """
    缠论计算引擎 (Chan Calculation Engine)
    
    输入原始K线DataFrame，执行包含处理、分型识别、画笔等操作。
    """
    def __init__(self, df: pd.DataFrame):
        self.raw_klines = []
        # 将DataFrame转换为ChanKLine对象列表
        for i, row in df.iterrows():
            k = ChanKLine(
                index=i,
                datetime=row['datetime'],
                open_price=row['open'],
                high=row['high'],
                low=row['low'],
                close=row['close'],
                volume=row['volume'],
                original_klines=[] # Will populate this if needed, but for now it's self
            )
            k.original_klines.append(k)
            self.raw_klines.append(k)
            
        self.standard_klines = [] # 存储包含处理后的K线
        self.fenxings = []        # 存储识别出的分型
        self.bis = []             # 存储最终生成的笔

    def process_inclusion(self):
        """
        阶段 1: K线包含处理 (Step 1: K-line Inclusion Processing)
        
        规则：
        1. 若相邻两根K线存在包含关系（一根的高低点完全在另一根范围内），则进行合并。
        2. 合并方向取决于当前的趋势方向：
           - 向上趋势（UP）：高点取较大值（High-High），低点取较大值（High-Low） -> GG-DG
           - 向下趋势（DOWN）：高点取较小值（Low-High），低点取较小值（Low-Low） -> GD-DD
        """
        if not self.raw_klines:
            return

        # Start with the first two K-lines
        processed = []
        
        # We need at least 2 K-lines to start
        if len(self.raw_klines) < 2:
            self.standard_klines = self.raw_klines
            return

        # Initialize with the first K-line
        current_k = self.raw_klines[0]
        processed.append(current_k)
        
        # 初始趋势判断
        # 如果前两根K线就有包含关系，通常需要参考前一个趋势，或者默认。
        # 这里简化处理：默认向上。在循环中会动态判断。
        last_direction = Direction.UP 
        
        # 重构后的包含处理逻辑：
        # 维护一个结果列表 result，每次拿新的 raw_kline 与 result[-1] 比较
        
        result = [self.raw_klines[0]]
        
        for i in range(1, len(self.raw_klines)):
            next_k = self.raw_klines[i]
            last_k = result[-1]
            
            # Check inclusion / 检查包含关系
            is_included = False
            
            # Case 1: last_k contains next_k (左包右)
            if last_k.high >= next_k.high and last_k.low <= next_k.low:
                is_included = True
            # Case 2: next_k contains last_k (右包左)
            elif next_k.high >= last_k.high and next_k.low <= last_k.low:
                is_included = True
                
            if is_included:
                # 存在包含关系，需要合并。
                # 首先确定当前的临时趋势方向，用于决定合并方式。
                # 趋势方向由 last_k 和 result[-2] 的高点关系决定。
                
                current_direction = Direction.UP
                if len(result) >= 2:
                    prev_k = result[-2]
                    if last_k.high > prev_k.high:
                        current_direction = Direction.UP
                    elif last_k.high < prev_k.high:
                        current_direction = Direction.DOWN
                    # If equal, keep previous direction (omitted for simplicity, assume UP or keep)
                else:
                     # 对于第一对K线，无法参考前值，默认向上
                     pass
                     
                # Merge / 合并处理
                new_high = 0.0
                new_low = 0.0
                
                if current_direction == Direction.UP:
                    # 向上趋势：取高点中的最大值，低点中的最大值 (GG-DG)
                    new_high = max(last_k.high, next_k.high)
                    new_low = max(last_k.low, next_k.low)
                else:
                    # 向下趋势：取高点中的最小值，低点中的最小值 (GD-DD)
                    new_high = min(last_k.high, next_k.high)
                    new_low = min(last_k.low, next_k.low)
                
                # 创建新的合并后K线
                # 时间通常沿用后一根K线的时间（next_k），因为它代表了这段时间的最终状态
                merged_k = ChanKLine(
                    index=next_k.index, # Use the later index
                    datetime=next_k.datetime,
                    open_price=last_k.open, # 开盘价参考前一根（视觉上）
                    high=new_high,
                    low=new_low,
                    close=next_k.close,
                    volume=last_k.volume + next_k.volume,
                    original_klines=last_k.original_klines + next_k.original_klines
                )
                
                # Replace the last one in result with this merged one / 用合并后的K线替换列表末尾元素
                result[-1] = merged_k
                
            else:
                # No inclusion, just append / 无包含关系，直接加入结果列表
                result.append(next_k)
                
        self.standard_klines = result

    def find_fenxing(self):
        """
        阶段 2: 顶底分型识别 (Step 2: Identify Top/Bottom Fenxing)
        
        在包含处理后的K线序列中寻找顶分型和底分型。
        顶分型：中间K线高点最高，低点最高。
        底分型：中间K线高点最低，低点最低。
        """
        self.fenxings = []
        if len(self.standard_klines) < 3:
            return

        # 遍历标准K线，窗口大小为3
        i = 1
        while i < len(self.standard_klines) - 1:
            k1 = self.standard_klines[i-1]
            k2 = self.standard_klines[i]
            k3 = self.standard_klines[i+1]
            
            # Top Fenxing: k2 high is highest, k2 low is highest / 顶分型判断
            is_top = (k2.high > k1.high and k2.high > k3.high) and \
                     (k2.low > k1.low and k2.low > k3.low)
                     
            # Bottom Fenxing: k2 high is lowest, k2 low is lowest / 底分型判断
            is_bottom = (k2.high < k1.high and k2.high < k3.high) and \
                        (k2.low < k1.low and k2.low < k3.low)
            
            if is_top:
                self.fenxings.append(FenXing(k2, FenXingType.TOP))
                # 这里我们先找出所有可能的物理分型，后续在画笔阶段（Step 3）进行严格过滤
            
            if is_bottom:
                self.fenxings.append(FenXing(k2, FenXingType.BOTTOM))
                
            i += 1
            
    def draw_bi(self):
        """
        阶段 3: 笔的绘制 (Step 3: Draw Bi / Stroke)
        
        核心逻辑：
        1. 顶底分型必须交替出现。
        2. **5K原则**：顶分型与底分型之间至少需要有一根独立的K线，即索引差 >= 4。
        3. 值的验证：
           - 向下笔：顶的高点 > 底的高点，顶的低点 > 底的低点。
           - 向上笔：底的低点 < 顶的低点，底的高点 < 顶的高点。
        4. 回溯与更新：
           - 如果遇到同向分型且更极端（如顶更高），则更新起点。
           - 如果距离不足（违反5K原则），则跳过该候选终点，继续寻找。
        """
        self.bis = []
        if not self.fenxings:
            return

        # 当前笔的起点候选
        current_bi_start = self.fenxings[0]
        
        # 辅助函数：获取分型在标准K线列表中的索引
        def get_std_index(fx):
            return self.standard_klines.index(fx.k_line)

        i = 1
        while i < len(self.fenxings):
            next_fx = self.fenxings[i]
            
            # 1. Check if same type (Extension / Update Start)
            # 如果下一个分型类型与当前起点相同（例如都是顶分型）
            if next_fx.type == current_bi_start.type:
                # 如果我们找到了一个更极端的点，就更新起点
                # Top: Higher is better. Bottom: Lower is better.
                update_start = False
                if current_bi_start.type == FenXingType.TOP:
                    if next_fx.high >= current_bi_start.high: # Allow equal to move forward
                        update_start = True
                else: # BOTTOM
                    if next_fx.low <= current_bi_start.low:
                        update_start = True
                
                if update_start:
                    current_bi_start = next_fx
                    # 如果这个点已经是上一笔的终点，我们需要更新上一笔的终点到这个新位置
                    if self.bis:
                        prev_bi_start = self.bis[-1].start_fx
                        # 更新上一笔
                        self.bis[-1] = Bi(prev_bi_start, next_fx)
                
                i += 1
                continue
                
            # 2. Different Type: Candidate for Bi / 类型不同，可能是笔的终点
            start_idx = get_std_index(current_bi_start)
            end_idx = get_std_index(next_fx)
            
            # A. 5K Principle (Index Difference >= 4) / 5K原则检查
            # Top(i) ... Bottom(i+4) -> 中间隔了3根K线，总共涉及5根K线
            has_enough_bars = (end_idx - start_idx) >= 4
            
            # B. Value Check (Strict) / 数值力度检查
            # 向下笔: 顶必须高于底
            # 向上笔: 底必须低于顶
            value_check = False
            if current_bi_start.type == FenXingType.TOP:
                if current_bi_start.high > next_fx.high and current_bi_start.low > next_fx.low:
                    value_check = True
            else:
                if current_bi_start.low < next_fx.low and current_bi_start.high < next_fx.high:
                    value_check = True
            
            if has_enough_bars and value_check:
                # VALID BI FOUND / 找到有效笔
                new_bi = Bi(current_bi_start, next_fx)
                self.bis.append(new_bi)
                
                # Update start to this new end / 将当前终点设为下一笔的起点
                current_bi_start = next_fx
                
                # Move to next
                i += 1
            else:
                # INVALID BI / 无效笔
                # 忽略这个 next_fx，继续往后找。
                # 此时保留 current_bi_start 不变。
                i += 1

