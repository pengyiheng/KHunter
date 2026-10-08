# -*- coding: utf-8 -*-
"""阻力位突破策略 - 识别"窄幅震荡后放量长阳突破平台高点"的信号

<<<<<<< HEAD
策略原理：
1. 阻力位识别：计算前60日最高价作为阻力位
2. 放量长阳突破：在最近3天内搜索涨幅>9%且放量的突破日
3. 回踩支撑：从突破日到今天，不跌破阻力位的98%
4. 均线多头排列：确保股价处于上升趋势中

选股条件：
- 突破日收盘价 >= 前60日最高价（100%突破）
- 突破日涨幅 >= 9%（放量长阳）
- 突破日成交量 >= 前5日均量 × 2.2
- 从突破日到今天，所有天最低价不跌破阻力位的98%
- 长阳日与阻力高点日相隔不少于30个交易日
- 均线多头排列：MA5 > MA10 > MA20
=======
策略原理（2026-09-12 按需求重构）：
1. **突破日即为选股日**：只在"今天"判定，不再回看最近 N 日（不再有回踩环节）
2. **平台条件**：前 70 日**窄幅震荡**——区间最高价与最低价的距离（振幅）≤ 25%
3. **突破条件**：今日**收盘 > 前 70 日最高价**（严格 100% 突破）
4. **力度条件**：今日涨幅 > 5%
5. **量能条件**：今日成交量 ≥ 前 5 日均量 × 1.8（放量确认）
6. **高点陈旧**：平台最高点（阻力位）距今 ≥ 10 个交易日——排除"近日已冲高/已突破"的股票

选股条件（全部满足）：
- C0 高点陈旧：平台最高点距今 ≥ min_peak_days(10) 个交易日
- C1 平台振幅：前 lookback_days(70) 日 (最高价 - 最低价) / 最低价 ≤ max_range_pct(25%)
- C2 突破：今日收盘价 > 前 lookback_days(70) 日最高价（100% 突破）
- C3 涨幅：今日涨幅 > min_change_pct(5%)
- C4 放量：今日成交量 ≥ 前 volume_ma_period(5) 日均量 × volume_ratio(1.8)
- C5 均线多头排列（可选，默认关闭）：MA5 > MA10 > MA20

⚠️ 数据方向：本策略的 `select_stocks` 统一按 date 升序（最旧在前、最新在后）处理，
不依赖调用方传入的顺序；`calculate_indicators` 始终返回正序。
>>>>>>> 9b2e8f0b179c4c897fac899673bf9c0751b5507e
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))
from strategy.base_strategy import BaseStrategy


class ResistanceBreakoutStrategy(BaseStrategy):
    """阻力位突破策略 - 窄幅震荡平台 + 今日放量长阳突破"""

    def __init__(self, params=None):
        """初始化策略参数"""
        default_params = {
<<<<<<< HEAD
            'lookback_days': 60,              # 回溯天数
            'breakout_ratio': 0.0,             # 突破阈值（0表示100%）
            'min_change_pct': 0.09,            # 最小涨幅（9%）
            'volume_ratio': 2.2,               # 成交量倍数
            'volume_ma_period': 5,             # 成交量均值周期
            'max_search_days': 3,              # 最大搜索天数（修改为3天）
            'ma_short_period': 5,              # 短期均线周期
            'ma_mid_period': 10,               # 中期均线周期
            'ma_long_period': 20,              # 长期均线周期
        }

=======
            'lookback_days': 70,          # 平台（阻力位）回溯天数（70 个交易日）
            'min_peak_days': 10,          # 【C0】平台最高点距今日最少交易日数（0=不限制）
            'max_range_pct': 25.0,        # 【C1】前 N 日振幅上限（%），低点到高点的距离
            'breakout_ratio': 0.0,        # 【C2】突破阈值：0 = 严格 100% 突破；-0.02 = 允许到 98%
            'min_change_pct': 0.05,       # 【C3】今日最小涨幅（> 5%）
            'volume_ratio': 1.8,          # 【C4】今日成交量 / 前 N 日均量
            'volume_ma_period': 5,        # 【C4】成交量均值周期
            'enable_ma_bullish': False,   # 【C5】是否要求均线多头排列（与窄幅震荡冲突，默认关闭）
            'ma_short_period': 5,
            'ma_mid_period': 10,
            'ma_long_period': 20,
        }
>>>>>>> 9b2e8f0b179c4c897fac899673bf9c0751b5507e
        if params:
            default_params.update(params)

        super().__init__("阻力位突破策略", default_params)

    # ------------------------------------------------------------------ #
    # 数据方向
    # ------------------------------------------------------------------ #
    @staticmethod
    def _to_ascending(df: pd.DataFrame) -> pd.DataFrame:
        """统一转为正序（最旧在前、最新在后），自动识别方向"""
        if df is None or df.empty or 'date' not in df.columns:
            return df
        d = df.reset_index(drop=True)
        if len(d) > 1 and str(d['date'].iloc[0]) > str(d['date'].iloc[-1]):
            d = d.iloc[::-1].reset_index(drop=True)
        return d

    # ------------------------------------------------------------------ #
    # 指标
    # ------------------------------------------------------------------ #
    def calculate_indicators(self, df) -> pd.DataFrame:
<<<<<<< HEAD
        """计算指标"""
        result = df.copy()

        # 数据可能是倒序排列，需要转为正序计算指标
        is_descending = False
        if len(result) > 1 and result['date'].iloc[0] > result['date'].iloc[1]:
            is_descending = True
            result = result.iloc[::-1].reset_index(drop=True)

        # 计算阻力位（前N日最高价）
        lookback_days = self.params['lookback_days']
        result['resistance_level'] = result['high'].rolling(window=lookback_days).max()

        # 计算成交量均线
        volume_ma_period = self.params['volume_ma_period']
        result['volume_ma'] = result['volume'].rolling(window=volume_ma_period).mean()

        # 计算成交量比
=======
        """计算指标（始终返回**正序**）"""
        result = self._to_ascending(df).copy()

        lookback_days = int(self.params['lookback_days'])
        vol_period = int(self.params['volume_ma_period'])

        # 平台/阻力位：前 N 日最高价（含当日，用于展示）
        result['resistance_level'] = result['high'].rolling(
            window=lookback_days, min_periods=1).max()
        # 平台区间最低价
        result['platform_low'] = result['low'].rolling(
            window=lookback_days, min_periods=1).min()
        # 成交量均线 / 量比
        result['volume_ma'] = result['volume'].rolling(
            window=vol_period, min_periods=1).mean()
>>>>>>> 9b2e8f0b179c4c897fac899673bf9c0751b5507e
        result['volume_ratio'] = result['volume'] / result['volume_ma']
        # 均线
        result['ma_short'] = result['close'].rolling(
            window=int(self.params['ma_short_period']), min_periods=1).mean()
        result['ma_mid'] = result['close'].rolling(
            window=int(self.params['ma_mid_period']), min_periods=1).mean()
        result['ma_long'] = result['close'].rolling(
            window=int(self.params['ma_long_period']), min_periods=1).mean()

<<<<<<< HEAD
        # 计算均线（用于多头排列判断）
        ma_short_period = self.params['ma_short_period']
        ma_mid_period = self.params['ma_mid_period']
        ma_long_period = self.params['ma_long_period']
        result['ma_short'] = result['close'].rolling(window=ma_short_period).mean()
        result['ma_mid'] = result['close'].rolling(window=ma_mid_period).mean()
        result['ma_long'] = result['close'].rolling(window=ma_long_period).mean()

        # 始终返回正序数据
=======
>>>>>>> 9b2e8f0b179c4c897fac899673bf9c0751b5507e
        return result

    # ------------------------------------------------------------------ #
    # 条件描述
    # ------------------------------------------------------------------ #
    def get_selection_criteria(self):
<<<<<<< HEAD
        """获取选股条件描述"""
        criteria = []
        min_change_pct = self.params['min_change_pct'] * 100
        volume_ratio = self.params['volume_ratio']
        volume_ma_period = self.params['volume_ma_period']
        max_search_days = self.params['max_search_days']
        lookback_days = self.params['lookback_days']
        breakout_ratio = self.params['breakout_ratio'] * 100
        
        ma_short = self.params['ma_short_period']
        ma_mid = self.params['ma_mid_period']
        ma_long = self.params['ma_long_period']
        
        criteria.append(f"1. 放量长阳日：最近{max_search_days}个交易日内出现涨幅>={min_change_pct:.0f}%的阳线，且成交量是前{volume_ma_period}日均量的{volume_ratio:.1f}倍以上")
        criteria.append(f"2. 阻力位突破：长阳日收盘价突破该日前{lookback_days}日最高价的{100+breakout_ratio:.0f}%以上")
        criteria.append(f"3. 高点间隔：长阳日与阻力高点日相隔不少于30个交易日")
        criteria.append(f"4. 回踩支撑：从长阳日到今天，所有天的最低价不跌破长阳日收盘价的95%")
        criteria.append(f"5. 均线多头排列：MA{ma_short} > MA{ma_mid} > MA{ma_long}")
        
        return criteria

    def quick_filter(self, df) -> bool:
        """快速过滤"""
        if df is None or df.empty or len(df) < 5:
            return False
        
        max_search_days = self.params['max_search_days']
        # df 是倒序的（最新在前），所以使用 head() 获取最近的数据
        recent_df = df.head(max_search_days + 1)
        
        # 计算涨跌幅（倒序数据，所以使用 pct_change(-1)）
        pct_change = recent_df['close'].pct_change(-1)
        min_change_pct = self.params['min_change_pct']
        
        return bool((pct_change >= min_change_pct).any())

    def select_stocks(self, df, stock_name='') -> list:
        """选股逻辑"""
        # 数据检查
        if df is None or df.empty or len(df) < 70:
            return []

        # 检查数据是否过时（最新数据距今超过5年）
        try:
            from datetime import datetime
            latest_date_str = str(df.iloc[-1]['date']).split()[0]  # 只取日期部分
            latest_date = datetime.strptime(latest_date_str, '%Y-%m-%d')
            current_date = datetime.now()
            days_diff = (current_date - latest_date).days
            # 如果最新数据超过5年前，认为是已退市股票
            if days_diff > 365 * 5:
                return []
        except Exception:
            pass

        # 快速预检查：检查是否有放量长阳线
        max_search_days = self.params['max_search_days']
        # df 是正序的（最新在最后），所以使用 tail() 获取最近的数据
        recent_df = df.tail(max_search_days + 1)
        
        # 计算涨跌幅
        pct_change = recent_df['close'].pct_change()
        min_change_pct = self.params['min_change_pct']
        if not (pct_change >= min_change_pct).any():
            return []
        
        # 检查成交量是否放大
        volume_ma_period = self.params['volume_ma_period']
        recent_df_copy = recent_df.copy()
        # recent_df 已经是正序的，直接计算均线
        recent_df_copy['volume_ma'] = recent_df_copy['volume'].rolling(window=volume_ma_period, min_periods=1).mean()
        
        volume_ratio = recent_df_copy['volume'] / recent_df_copy['volume_ma']
        volume_ratio_threshold = self.params['volume_ratio']
        if not (volume_ratio >= volume_ratio_threshold).any():
            return []

        # 获取最新数据
        latest = df.iloc[-1]
        if latest['volume'] <= 0 or pd.isna(latest['close']):
            return []

        # 检查均线多头排列
        if not self._check_ma_bullish(df):
            return []

        # 搜索放量长阳突破日
        breakout_pos = self._find_breakout_day(df)
        if breakout_pos is None:
            return []

        # 检查回踩支撑
        if not self._check_pullback(df, breakout_pos):
            return []

        # 生成选股信号
        signal = self._generate_signal(df, latest, breakout_pos)
        return [signal]

    def _find_breakout_day(self, df):
        """搜索放量长阳突破日"""
        lookback = self.params['lookback_days']
        ratio = self.params['breakout_ratio']
        min_chg = self.params['min_change_pct']
        vol_ratio = self.params['volume_ratio']
        vol_period = self.params['volume_ma_period']
        max_search = self.params['max_search_days']
        n = len(df)
        
        # 新增：阻力高点间隔天数
        min_resistance_gap = 30

        # 搜索范围：最近max_search_days天
        latest_candidate = n - 1
        earliest_candidate = max(lookback, n - max_search)

        # 从最近的候选日往前搜索
        for idx in range(latest_candidate, earliest_candidate - 1, -1):
            day_close = df['close'].iloc[idx]

            # 条件1：涨幅 >= min_change_pct
            if idx < 1:
                continue
            prev_close = df['close'].iloc[idx - 1]
            if prev_close <= 0 or pd.isna(prev_close):
                continue
            change_pct = (day_close - prev_close) / prev_close
            if change_pct < min_chg:
                continue

            # 条件2：放量
            vol_start = idx - vol_period
            if vol_start < 0:
                continue
            day_vol = df['volume'].iloc[idx]
            vol_ma = df['volume'].iloc[vol_start:idx].mean()
            if vol_ma <= 0 or day_vol < vol_ma * vol_ratio:
                continue

            # 条件3：突破阻力位
            res_start = idx - lookback
            if res_start < 0:
                continue
            resistance = df['high'].iloc[res_start:idx].max()
            if resistance <= 0:
                continue
            if day_close < resistance * (1 + ratio):
                continue
            
            # 条件4：长阳日与阻力高点日相隔不少于min_resistance_gap交易日
            # 找到前lookback日内最高价出现的位置
            resistance_high_idx = df['high'].iloc[res_start:idx].idxmax()
            gap_days = idx - resistance_high_idx
            if gap_days < min_resistance_gap:
                continue

            # 找到突破日
            return idx

        return None

    def _check_ma_bullish(self, df) -> bool:
        """检查均线多头排列：MA短期 > MA中期 > MA长期"""
        try:
            # 获取均线周期参数
            ma_short_period = self.params['ma_short_period']
            ma_mid_period = self.params['ma_mid_period']
            ma_long_period = self.params['ma_long_period']
            
            # 计算均线（确保数据是正序的）
            df_copy = df.copy()
            if len(df_copy) > 1 and df_copy['date'].iloc[0] > df_copy['date'].iloc[-1]:
                df_copy = df_copy.iloc[::-1].reset_index(drop=True)
            
            # 计算均线
            ma_short = df_copy['close'].rolling(window=ma_short_period).mean().iloc[-1]
            ma_mid = df_copy['close'].rolling(window=ma_mid_period).mean().iloc[-1]
            ma_long = df_copy['close'].rolling(window=ma_long_period).mean().iloc[-1]
            
            # 检查是否存在NaN值
            if pd.isna(ma_short) or pd.isna(ma_mid) or pd.isna(ma_long):
                return False
            
            # 检查多头排列：MA短期 > MA中期 > MA长期
            return ma_short > ma_mid > ma_long
        
        except Exception as e:
            return False

    def _check_pullback(self, df, breakout_pos) -> bool:
        """检查回踩支撑"""
        n = len(df)

        # 阻力位（突破前lookback日内最高点）的98%作为支撑位（允许回调不超过2%）
        lookback = self.params['lookback_days']
        res_start = breakout_pos - lookback
        if res_start < 0:
            res_start = 0
        resistance = df['high'].iloc[res_start:breakout_pos].max()
        support_level = resistance * 0.98
        if resistance <= 0 or pd.isna(resistance):
            return False

        # 如果突破日就是最后一天，无需检查回踩
        if breakout_pos >= n - 1:
            return True
=======
        p = self.params
        criteria = [
            f"1. 平台高点陈旧：平台（阻力位）最高点距今 ≥ {int(p['min_peak_days'])} 个"
            f"交易日（排除近 {int(p['min_peak_days'])} 日内已冲高/已突破的股票）",
            f"2. 平台窄幅震荡：前 {int(p['lookback_days'])} 日（最高价-最低价）/最低价 ≤ "
            f"{p['max_range_pct']}%",
            f"3. 突破平台高点：今日收盘价 > 前 {int(p['lookback_days'])} 日最高价"
            f"（{100 + p['breakout_ratio'] * 100:.0f}%）",
            f"4. 当日长阳：今日涨幅 > {p['min_change_pct'] * 100:.0f}%",
            f"5. 放量确认：今日成交量 ≥ 前 {int(p['volume_ma_period'])} 日均量 × "
            f"{p['volume_ratio']}",
        ]
        if p.get('enable_ma_bullish', False):
            criteria.append(
                f"{len(criteria) + 1}. 均线多头排列：MA{p['ma_short_period']} > "
                f"MA{p['ma_mid_period']} > MA{p['ma_long_period']}")
        criteria.append(f"{len(criteria) + 1}. 选股日 = 突破日（当日判定，不含回踩环节）")
        return criteria

    # ------------------------------------------------------------------ #
    # 快速过滤
    # ------------------------------------------------------------------ #
    def quick_filter(self, df) -> bool:
        """快速过滤：最新一日是否为大阳线（涨幅 > 阈值）

        与 `select_stocks` 一致，内部自动识别数据方向。
        """
        if df is None or df.empty or len(df) < 2:
            return False
        d = self._to_ascending(df)
        try:
            last = d.iloc[-1]
            prev = d.iloc[-2]
            if float(prev['close']) <= 0:
                return False
            change = (float(last['close']) - float(prev['close'])) / float(prev['close'])
            return bool(change > float(self.params['min_change_pct']))
        except Exception:
            return False

    # ------------------------------------------------------------------ #
    # 选股主逻辑
    # ------------------------------------------------------------------ #
    def select_stocks(self, df, stock_name='') -> list:
        """选股逻辑：**突破日即为选股日**"""
        if df is None or df.empty:
            return []
>>>>>>> 9b2e8f0b179c4c897fac899673bf9c0751b5507e

        p = self.params
        lookback = int(p['lookback_days'])
        min_len = max(lookback + 1, int(p['volume_ma_period']) + 1, 25)
        if len(df) < min_len:
            return []

<<<<<<< HEAD
        # 最低价不能跌破阻力位的98%
        return bool(min_low >= support_level)

    def _generate_signal(self, df, latest, breakout_pos) -> dict:
        """生成选股信号"""
        lookback = self.params['lookback_days']
        
        # 计算突破日的阻力位
        res_start = breakout_pos - lookback
        resistance = df['high'].iloc[res_start:breakout_pos].max()
        breakout_day = df.iloc[breakout_pos]
=======
        # 统一正序
        d = self._to_ascending(df).reset_index(drop=True)
        if len(d) < min_len:
            return []

        # 退市检查：最新数据距今超过 5 年 → 视为已退市
        try:
            from datetime import datetime
            latest_date = datetime.strptime(str(d['date'].iloc[-1])[:10], '%Y-%m-%d')
            if (datetime.now() - latest_date).days > 365 * 5:
                return []
        except Exception:
            pass

        today = d.iloc[-1]
        try:
            close_today = float(today['close'])
            high_today = float(today['high'])
            low_today = float(today['low'])
            vol_today = float(today['volume'])
            prev_close = float(d['close'].iloc[-2])
        except Exception:
            return []
        if close_today <= 0 or prev_close <= 0 or vol_today <= 0:
            return []
        if pd.isna(close_today) or pd.isna(vol_today):
            return []
>>>>>>> 9b2e8f0b179c4c897fac899673bf9c0751b5507e

        # 平台窗口：今日之前 lookback 日（不含今日）
        win = d.iloc[-(lookback + 1):-1]
        if len(win) < lookback:
            return []
        win_high = float(win['high'].max())
        win_low = float(win['low'].min())
        if win_high <= 0 or win_low <= 0:
            return []

<<<<<<< HEAD
        # 突破幅度
        br = (breakout_day['close'] - resistance) / resistance
=======
        # ---- C0 平台最高点须"陈旧"：近 N 日内不得已有最高点 ----
        #   若平台最高点落在最近 min_peak_days 日内，说明这个"高点"本身就是近日冲高
        #   /放量突破留下的，属"突破后的连续拉升"，不是首次突破 → 排除。
        #   例：600830 香溢融通 2026-09-01 已放量涨停突破（收 9.23，平台前高仅 8.53），
        #   09-02 算出的"阻力位" 9.23 就是 09-01 自己的高点，再判定命中即为追高。
        peak_min_days = int(p.get('min_peak_days', 10))
        peak_pos = int(win['high'].astype(float).idxmax())
        days_since_peak = len(d) - 1 - peak_pos
        if peak_min_days > 0 and days_since_peak < peak_min_days:
            return []

        # ---- C1 平台振幅（低点 → 高点距离）----
        max_range = float(p['max_range_pct'])
        range_pct = (win_high - win_low) / win_low * 100
        if max_range > 0 and range_pct > max_range:
            return []
>>>>>>> 9b2e8f0b179c4c897fac899673bf9c0751b5507e

        # ---- C2 突破平台高点（严格 100%，除非 breakout_ratio < 0）----
        ratio = float(p['breakout_ratio'])
        if close_today < win_high * (1 + ratio):
            return []

<<<<<<< HEAD
        # 关键日期：突破日
        key_date = breakout_day['date']
        if hasattr(key_date, 'strftime'):
            key_date_str = key_date.strftime('%Y-%m-%d')
        else:
            key_date_str = str(key_date)[:10]
        
        # 构建选股信号
        signal_info = {
            'key_date': key_date_str,
            'key_date_type': '阻力位突破日',
            'price': float(latest['close']),
            'resistance': float(resistance),
            'breakout_ratio': float(br),
            'days_since_breakout': int(days_since),
            'reasons': reasons
        }
        return signal_info

    def _generate_reasons(self, df, breakout_pos) -> list:
        """生成选股原因列表"""
        reasons = []
        lookback = self.params['lookback_days']
        vol_period = self.params['volume_ma_period']

        # 突破日数据和阻力位
        res_start = breakout_pos - lookback
        resistance = df['high'].iloc[res_start:breakout_pos].max()
        bd = df.iloc[breakout_pos]

        # 原因1：放量长阳突破阻力位
        bd_idx = breakout_pos
        if bd_idx >= 1:
            prev_close = df['close'].iloc[bd_idx - 1]
            change_pct = (bd['close'] - prev_close) / prev_close * 100
        else:
            change_pct = 0
        reasons.append(
            f"放量长阳突破{lookback}日阻力位{resistance:.2f}，涨幅{change_pct:.1f}%"
        )

        # 原因2：突破日成交量放大
        vs = breakout_pos - vol_period
        if vs >= 0:
            vma = df['volume'].iloc[vs:breakout_pos].mean()
            if vma > 0:
                vr = bd['volume'] / vma
                reasons.append(f"突破日成交量放大{vr:.1f}倍")

        # 原因3：回踩不破支撑位（阻力位的98%）
        days_since = len(df) - 1 - breakout_pos
        if days_since > 0:
            rmin = df['low'].iloc[breakout_pos + 1:].min()
            # 阻力位（突破前lookback日内最高点）的98%作为支撑位
            support_level = resistance * 0.98
            reasons.append(
                f"突破后{days_since}天回踩最低{rmin:.2f}，未破支撑位{support_level:.2f}"
            )
        else:
            reasons.append(f"今日放量长阳突破，收盘价{bd['close']:.2f}")

        return reasons
=======
        # ---- C3 今日涨幅 ----
        change_pct = (close_today - prev_close) / prev_close * 100
        if change_pct <= float(p['min_change_pct']) * 100:
            return []

        # ---- C4 放量：今日量 ≥ 前 N 日均量 × 倍数 ----
        vol_period = int(p['volume_ma_period'])
        vol_window = d['volume'].iloc[-(vol_period + 1):-1]
        if len(vol_window) < vol_period:
            return []
        vol_ma = float(vol_window.mean())
        vol_ratio = float(p['volume_ratio'])
        if vol_ma <= 0:
            return []
        vr = vol_today / vol_ma
        if vr < vol_ratio:
            return []

        # ---- C5 均线多头排列（可选）----
        ma_info = None
        if p.get('enable_ma_bullish', False):
            ma_s = d['close'].rolling(int(p['ma_short_period'])).mean().iloc[-1]
            ma_m = d['close'].rolling(int(p['ma_mid_period'])).mean().iloc[-1]
            ma_l = d['close'].rolling(int(p['ma_long_period'])).mean().iloc[-1]
            if pd.isna(ma_s) or pd.isna(ma_m) or pd.isna(ma_l):
                return []
            if not (ma_s > ma_m > ma_l):
                return []
            ma_info = (float(ma_s), float(ma_m), float(ma_l))

        # ---- 生成信号 ----
        key_date = str(d['date'].iloc[-1])[:10]
        reasons = [
            f"平台最高点{win_high:.2f}距今{days_since_peak}个交易日"
            f"（≥{peak_min_days}，排除近日已冲高/已突破）",
            f"平台窄幅震荡：前{lookback}日高低区间 {win_low:.2f}~{win_high:.2f}，"
            f"振幅{range_pct:.1f}%（≤{max_range}%）",
            f"今日突破平台高点 {win_high:.2f}：收盘{close_today:.2f}"
            f"（{100 + ratio * 100:.0f}% 口径），涨幅{change_pct:.1f}%",
            f"放量确认：量比{vr:.2f}（≥{vol_ratio}）",
        ]
        if ma_info:
            reasons.append(f"均线多头排列：MA{int(p['ma_short_period'])}"
                           f"{ma_info[0]:.2f} > MA{int(p['ma_mid_period'])}"
                           f"{ma_info[1]:.2f} > MA{int(p['ma_long_period'])}"
                           f"{ma_info[2]:.2f}")

        return [{
            'code': '',
            'name': stock_name,
            'key_date': key_date,
            'key_date_type': '阻力位突破日',
            'price': round(close_today, 2),
            'resistance': round(win_high, 2),          # 平台高点（阻力位）
            'platform_low': round(win_low, 2),         # 平台低点
            'days_since_peak': days_since_peak,        # 平台最高点距今交易日数
            'range_pct': round(range_pct, 2),          # 平台振幅
            'change_pct': round(change_pct, 2),        # 今日涨幅
            'volume_ratio': round(vr, 2),              # 量比
            'breakout_ratio': round((close_today - win_high) / win_high, 4),
            'days_since_breakout': 0,                  # 突破日即为选股日
            'reasons': reasons,
            'strategy_type': 'ResistanceBreakoutStrategy',
        }]
>>>>>>> 9b2e8f0b179c4c897fac899673bf9c0751b5507e
