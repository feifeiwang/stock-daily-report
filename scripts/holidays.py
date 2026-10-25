# -*- coding: utf-8 -*-
"""
交易日历模块：判断 A股（沪/深/北）与港股（HKEX）某日是否开市。

规则：
- A股：周一至周五开市，法定节假日（含因调休而休市的周末补班日）休市。
  - 调休补班日（如 2026-02-14 周六）A股同样休市 —— 由“周六/周日一律休市”自然覆盖。
- 港股：周一至周五开市，香港公众假期休市；半日市（新年前夕等）仍算开市。

数据来源（按优先级）：
1. 动态：NateScarlet/holiday-cn（自动抓取国务院公告，经 jsDelivr 分发）——A股
2. 静态兜底：本文件内嵌的官方数据（2026 全年已官方确认；2027 为预估/已知数据）
"""
import json
import urllib.request
import urllib.error

# ---------------------------------------------------------------------------
# 静态兜底数据
# ---------------------------------------------------------------------------

# A股 2026 全天休市日（沪深北交易所官方公告，2025-12-22 发布）
SH_HOLIDAYS_2026 = {
    # 元旦
    "2026-01-01", "2026-01-02", "2026-01-03",
    # 春节（2/15-2/23）
    "2026-02-15", "2026-02-16", "2026-02-17", "2026-02-18", "2026-02-19",
    "2026-02-20", "2026-02-21", "2026-02-22", "2026-02-23",
    # 清明节（4/4-4/6）
    "2026-04-04", "2026-04-05", "2026-04-06",
    # 劳动节（5/1-5/5）
    "2026-05-01", "2026-05-02", "2026-05-03", "2026-05-04", "2026-05-05",
    # 端午节（6/19-6/21）
    "2026-06-19", "2026-06-20", "2026-06-21",
    # 中秋节（9/25-9/27）
    "2026-09-25", "2026-09-26", "2026-09-27",
    # 国庆节（10/1-10/7）
    "2026-10-01", "2026-10-02", "2026-10-03", "2026-10-04", "2026-10-05",
    "2026-10-06", "2026-10-07",
}

# A股 2027 预估（官方尚未发布，按农历日期与历年惯例预估，待官方公告后修正）
SH_HOLIDAYS_2027 = {
    "2027-01-01",                                    # 元旦（周五）
    "2027-02-05", "2027-02-08", "2027-02-09",        # 春节（预估，初一 2/6 为周六）
    "2027-02-10", "2027-02-11", "2027-02-12",
    "2027-04-05",                                    # 清明节（周一）
    "2027-05-03", "2027-05-04", "2027-05-05",        # 劳动节（预估）
    "2027-06-09",                                    # 端午节（周三）
    "2027-09-15",                                    # 中秋节（周三，预估）
    "2027-10-01", "2027-10-04", "2027-10-05",        # 国庆节（预估）
    "2027-10-06", "2027-10-07",
}

# 港股 2026 证券市场休市日（港交所 2025 年第 075 号通告，官方确认）
HK_HOLIDAYS_2026 = {
    "2026-01-01",                        # 一月一日
    "2026-02-17", "2026-02-18", "2026-02-19",   # 农历年初一/二/三
    "2026-04-03",                        # 耶稣受难节
    "2026-04-06",                        # 清明节翌日
    "2026-04-07",                        # 复活节星期一翌日
    "2026-05-01",                        # 劳动节
    "2026-05-25",                        # 佛诞翌日
    "2026-06-19",                        # 端午节
    "2026-07-01",                        # 香港特别行政区成立纪念日
    "2026-10-01",                        # 国庆日
    "2026-10-19",                        # 重阳节翌日
    "2026-12-25",                        # 圣诞节
}

# 港股 2026 半日市（仍开市，仅提前收市）
HK_HALF_DAYS_2026 = {"2026-02-16", "2026-12-24", "2026-12-31"}

# 港股 2027 休市日（据 HKEX 交易日历 / publicholidays.hk 已知日期）
HK_HOLIDAYS_2027 = {
    "2027-01-01",                        # 一月一日（周五）
    "2027-02-08", "2027-02-09",          # 农历年初三、初四（初一/初二适逢周末）
    "2027-03-26",                        # 耶稣受难节
    "2027-03-29",                        # 复活节星期一
    "2027-04-05",                        # 清明节
    "2027-05-13",                        # 佛诞
    "2027-06-09",                        # 端午节
    "2027-07-01",                        # 香港特别行政区成立纪念日
    "2027-09-16",                        # 中秋节翌日
    "2027-10-01",                        # 国庆日
    "2027-10-08",                        # 重阳节
    "2027-12-27",                        # 圣诞节后第一个周日
}

# 港股 2027 半日市
HK_HALF_DAYS_2027 = {"2027-02-05", "2027-12-24", "2027-12-31"}

# 未收录年份（2028+）的已知中国主要法定节假日（月初固定部分），作为保守兜底
# 说明：仅用于避免误判，误差容忍（错过一天不生成报告好过节假日生成报告）
SH_FALLBACK_HOLIDAYS = {
    "2028-01-01", "2028-01-03",
    "2028-05-01", "2028-05-02", "2028-05-03",
    "2028-07-01", "2028-10-01", "2028-10-02", "2028-10-03",
    "2028-10-04", "2028-10-05", "2028-12-25",
}

_CN_HOLIDAY_CACHE = {}


def _fetch_cn_holidays(year: int):
    """从 holiday-cn 仓库动态获取某年中国大陆法定节假日（休息日）。失败返回 None。"""
    if year in _CN_HOLIDAY_CACHE:
        return _CN_HOLIDAY_CACHE[year]
    urls = [
        f"https://cdn.jsdelivr.net/gh/NateScarlet/holiday-cn@master/{year}.json",
        f"https://raw.githubusercontent.com/NateScarlet/holiday-cn/master/{year}.json",
    ]
    result = None
    for url in urls:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            off = {d["date"] for d in data.get("days", []) if d.get("isOffDay")}
            if off:
                result = off
                break
        except Exception:
            continue
    _CN_HOLIDAY_CACHE[year] = result
    return result


def sh_holidays(year: int):
    """A股全年全天休市日集合（静态兜底 + 动态数据）。"""
    static = {}
    if year == 2026:
        static = SH_HOLIDAYS_2026
    elif year == 2027:
        static = SH_HOLIDAYS_2027
    elif year >= 2028:
        static = SH_FALLBACK_HOLIDAYS
    dynamic = _fetch_cn_holidays(year)
    return set(static) | (dynamic or set())


def hk_holidays(year: int):
    """港股全年全天休市日集合。"""
    if year == 2026:
        return set(HK_HOLIDAYS_2026)
    if year == 2027:
        return set(HK_HOLIDAYS_2027)
    # 2028+ 保守兜底：固定西方/香港节日 + 大陆国庆（两地交集）
    return {f"{year}-01-01", f"{year}-12-25"}


def hk_half_days(year: int):
    """港股半日市（仍开市）。"""
    if year == 2026:
        return set(HK_HALF_DAYS_2026)
    if year == 2027:
        return set(HK_HALF_DAYS_2027)
    return set()


def _is_trading_day(date, holidays: set, half_days: set):
    if date.weekday() >= 5:  # 周六、周日一律休市（含调休补班日）
        return False
    iso = date.isoformat()
    if iso in holidays:
        return False
    return True  # 半日市仍算开市


def sh_trading_day(date):
    return _is_trading_day(date, sh_holidays(date.year), set())


def hk_trading_day(date):
    return _is_trading_day(date, hk_holidays(date.year), hk_half_days(date.year))


def is_hk_half_day(date):
    return date.isoformat() in hk_half_days(date.year)


def holiday_source(date):
    """返回某日休市原因（用于报告展示，A股）。"""
    iso = date.isoformat()
    if date.weekday() >= 5:
        return "周末休市"
    if iso in sh_holidays(date.year):
        return "法定节假日"
    return None


def hk_holiday_source(date):
    """返回港股休市原因（用于报告展示）。"""
    iso = date.isoformat()
    if date.weekday() >= 5:
        return "周末休市"
    if iso in hk_holidays(date.year):
        return "香港公众假期"
    return None


if __name__ == "__main__":
    # CLI: python3 holidays.py [YYYY-MM-DD]（缺省今天，本地时区）
    # 输出: {日期} A股=开市/休市 港股=开市/休市（附半日市与休市原因）
    import sys as _sys
    from datetime import date as _date
    _arg = _sys.argv[1] if len(_sys.argv) > 1 else None
    _d = _date.fromisoformat(_arg) if _arg else _date.today()
    _sh, _hk = sh_trading_day(_d), hk_trading_day(_d)
    print(f"{_d.isoformat()} A股={'开市' if _sh else '休市'} 港股={'开市' if _hk else '休市'}")
    if _hk and is_hk_half_day(_d):
        print("  港股半日市（12:00 收市，仍算开市）")
    if not _sh:
        print(f"  A股休市原因：{holiday_source(_d) or '非交易日'}")
    if not _hk:
        print(f"  港股休市原因：{hk_holiday_source(_d) or '非交易日'}")
    if not (_sh or _hk):
        print("SKIP: 今日两地均休市，不执行")
