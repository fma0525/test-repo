"""病理中心模擬參數：預設假設值、Excel 讀寫與檢查。

參數全部放在一個 Excel 活頁簿裡，每個工作表一張表。
這個模組定義預設值（全部標示為「假設」），並負責：
- 把預設值寫成 Excel（write_excel）
- 從 Excel 讀回（read_excel）
- 檢查參數是否合理（validate）
"""

from __future__ import annotations

import copy
import io
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

ASSUMED = "假設"

# ---------------------------------------------------------------------------
# 工作表名稱
# ---------------------------------------------------------------------------
SHEET_GENERAL = "一般設定"
SHEET_ARRIVAL = "到件時段"
SHEET_TYPES = "檢體類型"
SHEET_TASKS = "作業時間"
SHEET_SHIFTS = "人力與設備班表"
SHEET_PROCESSOR = "脫水機排程"

SHEET_ORDER = [SHEET_GENERAL, SHEET_TYPES, SHEET_TASKS, SHEET_SHIFTS,
               SHEET_PROCESSOR, SHEET_ARRIVAL]

WEEKDAYS = ["一", "二", "三", "四", "五", "六", "日"]


# ---------------------------------------------------------------------------
# 預設值
# ---------------------------------------------------------------------------
def _general() -> pd.DataFrame:
    rows = [
        # 代碼, 參數, 數值, 單位, 說明
        ("daily_cases", "平日每日檢體數", 120, "件/天",
         "週一到週五每天收到的檢體件數（以件計，一件可有多個蠟塊）"),
        ("sat_ratio", "週六到件比例", 0.3, "倍", "週六件數 = 平日件數 × 此比例"),
        ("sun_ratio", "週日到件比例", 0.0, "倍", "週日件數 = 平日件數 × 此比例"),
        ("digital", "數位掃描流程", 1, "1=是 0=否",
         "1：玻片先掃描再由醫師看影像；0：玻片直接送醫師"),
        ("ihc_prob", "需加做特殊染色比例", 0.15, "比例",
         "判讀後需要加做免疫組織化學或特殊染色的件數比例"),
        ("ihc_delay_h", "特殊染色等待時間", 24, "小時", "加做染色從開單到玻片回到醫師手上的時間"),
        ("stain_capacity", "染色機每批容量", 60, "張玻片", "染色封片機一個批次可放的玻片數"),
        ("stain_minutes", "染色機每批時間", 50, "分鐘", "含染色與封片"),
        ("stain_collect_min", "染色湊批等待上限", 15, "分鐘",
         "玻片不足一批時，最早到的玻片最多等多久就開機"),
        ("util_warn", "瓶頸警戒使用率", 0.85, "比例",
         "使用率超過此值視為瓶頸（作業管理常用 80–85%）"),
        ("warmup_weeks", "暖機週數", 1, "週", "模擬開始時實驗室是空的，前幾週不列入統計"),
        ("sim_weeks", "統計週數", 4, "週", "統計這段期間收到的檢體"),
        ("drain_weeks", "收尾週數", 3, "週", "統計期之後繼續跑，讓統計期的檢體都能做完"),
        ("replications", "重複次數", 5, "次", "每個情境用不同亂數跑幾次，取平均"),
        ("seed", "亂數種子", 42, "", "固定種子可讓結果可重現"),
        ("growth_rate", "年成長率", 0.08, "比例", "成長規劃用：每年件數成長比例"),
        ("growth_years", "規劃年數", 5, "年", "成長規劃看未來幾年"),
    ]
    df = pd.DataFrame(rows, columns=["代碼", "參數", "數值", "單位", "說明"])
    df["來源"] = ASSUMED
    return df


def _arrival() -> pd.DataFrame:
    # 每小時到件權重（相對值）。平日 07–18 點，上午 10–11 點與下午 14–16 點兩個高峰。
    weekday = [0, 0, 0, 0, 0, 0, 0, 2, 6, 10, 14, 12, 6, 8, 12, 12, 10, 6, 2, 0, 0, 0, 0, 0]
    saturday = [0, 0, 0, 0, 0, 0, 0, 0, 6, 10, 10, 8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    sunday = [0] * 24
    return pd.DataFrame({
        "時段": [f"{h:02d}:00" for h in range(24)],
        "平日權重": weekday,
        "週六權重": saturday,
        "週日權重": sunday,
        "來源": ASSUMED,
    })


def _types() -> pd.DataFrame:
    rows = [
        # 代碼, 名稱, 比例, 急件比例, 蠟塊(最少,最可能,最多), 每塊玻片(...), 取材分鐘(...), 判讀分鐘(...), 固定時數, TAT目標
        ("small", "小切片", 0.60, 0.10, 1, 1, 3, 1, 3, 4, 1, 2, 4, 3, 6, 12, 0, 48),
        ("medium", "中型手術檢體", 0.30, 0.05, 1, 3, 6, 1, 1, 2, 4, 8, 15, 6, 12, 25, 6, 72),
        ("large", "大型手術檢體", 0.10, 0.02, 6, 12, 30, 1, 1, 2, 15, 30, 60, 20, 35, 60, 12, 120),
    ]
    cols = ["代碼", "名稱", "比例", "急件比例",
            "蠟塊數_最少", "蠟塊數_最可能", "蠟塊數_最多",
            "每塊玻片_最少", "每塊玻片_最可能", "每塊玻片_最多",
            "取材分鐘_最短", "取材分鐘_最可能", "取材分鐘_最長",
            "判讀分鐘_最短", "判讀分鐘_最可能", "判讀分鐘_最長",
            "固定時數", "TAT目標小時"]
    df = pd.DataFrame(rows, columns=cols)
    df["來源"] = ASSUMED
    return df


# 作業代碼固定，模型依代碼找作業；名稱、時間、資源都可以改。
TASK_CODES = ["reception", "grossing", "embedding", "microtomy_block", "microtomy_slide",
              "qc_case", "qc_slide", "scanning", "reporting", "ihc_report"]

UNIT_CASE = "每件"
UNIT_BLOCK = "每蠟塊"
UNIT_SLIDE = "每玻片"
UNIT_BY_TYPE = "依檢體類型"


def _tasks() -> pd.DataFrame:
    rows = [
        # 代碼, 作業, 計算單位, 最短, 最可能, 最長, 人力資源, 設備資源
        ("reception", "收件登錄", UNIT_CASE, 2, 3, 6, "收件人員", ""),
        ("grossing", "取材", UNIT_BY_TYPE, None, None, None, "取材人員", "取材台"),
        ("embedding", "包埋", UNIT_BLOCK, 0.8, 1.0, 1.5, "包埋技術員", "包埋台"),
        ("microtomy_block", "切片（每蠟塊）", UNIT_BLOCK, 2.0, 2.5, 4.0, "切片技術員", "切片機"),
        ("microtomy_slide", "切片（每張玻片）", UNIT_SLIDE, 0.4, 0.6, 1.0, "切片技術員", "切片機"),
        ("qc_case", "品管配片（每件）", UNIT_CASE, 1.0, 1.5, 3.0, "品管配片人員", ""),
        ("qc_slide", "品管配片（每張玻片）", UNIT_SLIDE, 0.1, 0.2, 0.3, "品管配片人員", ""),
        ("scanning", "數位掃描", UNIT_SLIDE, 1.0, 1.5, 2.5, "", "掃描器"),
        ("reporting", "判讀發報告", UNIT_BY_TYPE, None, None, None, "病理醫師", ""),
        ("ihc_report", "特殊染色後補判讀", UNIT_CASE, 3, 5, 10, "病理醫師", ""),
    ]
    df = pd.DataFrame(rows, columns=["代碼", "作業", "計算單位", "最短分鐘", "最可能分鐘",
                                     "最長分鐘", "人力資源", "設備資源"])
    df["來源"] = ASSUMED
    return df


STAFF = "人力"
EQUIP = "設備"


def _shifts() -> pd.DataFrame:
    allday = ("00:00", "24:00")
    off = ("", "")
    rows = [
        # 資源, 類型, 數量, 平日(起,迄), 週六(起,迄), 週日(起,迄), 備註
        ("收件人員", STAFF, 2, ("07:30", "16:30"), off, off, "平日班"),
        ("收件人員", STAFF, 1, off, ("08:00", "12:00"), off, "週六半天"),
        ("取材人員", STAFF, 4, ("08:00", "17:00"), off, off, "住院醫師或病理助理"),
        ("取材人員", STAFF, 1, off, ("08:00", "12:00"), off, "週六半天"),
        ("取材台", EQUIP, 4, allday, allday, allday, ""),
        ("包埋技術員", STAFF, 2, ("06:00", "15:00"), off, off, "早班，接夜間脫水機"),
        ("包埋台", EQUIP, 2, allday, allday, allday, ""),
        ("切片技術員", STAFF, 4, ("06:30", "15:30"), off, off, "早班"),
        ("切片技術員", STAFF, 1, ("10:00", "19:00"), off, off, "晚班，接日間快速脫水"),
        ("切片機", EQUIP, 6, allday, allday, allday, ""),
        ("染色機", EQUIP, 2, ("06:00", "20:00"), ("06:00", "13:00"), off, "運轉時段（需有人裝卸）"),
        ("品管配片人員", STAFF, 2, ("08:00", "17:00"), off, off, ""),
        ("掃描器", EQUIP, 2, allday, allday, allday, "假設可整夜自動掃描"),
        ("病理醫師", STAFF, 6, ("08:30", "17:30"), off, off, "以實際用於判讀的人力計"),
        ("病理醫師", STAFF, 2, off, ("08:30", "12:00"), off, "週六"),
    ]
    out = []
    for name, kind, n, wk, sat, sun, note in rows:
        out.append({"資源": name, "類型": kind, "數量": n,
                    "平日開始": wk[0], "平日結束": wk[1],
                    "週六開始": sat[0], "週六結束": sat[1],
                    "週日開始": sun[0], "週日結束": sun[1],
                    "備註": note, "來源": ASSUMED})
    return pd.DataFrame(out)


def _processor() -> pd.DataFrame:
    rows = [
        # 名稱, 星期, 開始, 處理時數, 台數, 每台容量, 適用檢體, 急件可用
        ("日間快速 A", "一二三四五", "10:30", 3.5, 1, 150, "small", "是"),
        ("日間快速 B", "一二三四五", "14:30", 3.5, 1, 150, "small", "是"),
        ("夜間常規", "一二三四五", "17:30", 11.5, 3, 300, "small,medium,large", "是"),
        ("週末長程", "六", "12:00", 41.0, 3, 300, "small,medium,large", "是"),
    ]
    df = pd.DataFrame(rows, columns=["名稱", "星期", "開始時間", "處理時數", "台數",
                                     "每台容量蠟塊", "適用檢體代碼", "急件可用"])
    df["來源"] = ASSUMED
    return df


def default_sheets() -> dict[str, pd.DataFrame]:
    return {
        SHEET_GENERAL: _general(),
        SHEET_TYPES: _types(),
        SHEET_TASKS: _tasks(),
        SHEET_SHIFTS: _shifts(),
        SHEET_PROCESSOR: _processor(),
        SHEET_ARRIVAL: _arrival(),
    }


# ---------------------------------------------------------------------------
# Excel 讀寫
# ---------------------------------------------------------------------------
def write_excel(sheets: dict[str, pd.DataFrame], path: str | Path | io.BytesIO) -> None:
    with pd.ExcelWriter(path, engine="openpyxl") as xw:
        for name in SHEET_ORDER:
            sheets[name].to_excel(xw, sheet_name=name, index=False)
        for ws in xw.book.worksheets:
            ws.freeze_panes = "A2"
            for col in ws.columns:
                width = max(len(str(c.value or "")) for c in col)
                ws.column_dimensions[col[0].column_letter].width = min(max(8, width * 1.8), 60)


def excel_bytes(sheets: dict[str, pd.DataFrame]) -> bytes:
    buf = io.BytesIO()
    write_excel(sheets, buf)
    return buf.getvalue()


def read_excel(path) -> dict[str, pd.DataFrame]:
    raw = pd.read_excel(path, sheet_name=None, dtype=object)
    missing = [s for s in SHEET_ORDER if s not in raw]
    if missing:
        raise ValueError(f"Excel 缺少工作表：{'、'.join(missing)}")
    sheets = {}
    for name in SHEET_ORDER:
        df = raw[name].copy()
        df = df.dropna(how="all")
        df = df.astype(object).map(
            lambda v: None if v is None or (isinstance(v, float) and v != v) else v)
        sheets[name] = df.reset_index(drop=True)
    return sheets


# ---------------------------------------------------------------------------
# 解析成模型使用的結構
# ---------------------------------------------------------------------------
def _blank(v) -> bool:
    if v is None:
        return True
    if isinstance(v, str):
        return v.strip() == "" or v.strip().lower() == "nan"
    try:
        return bool(pd.isna(v))
    except (TypeError, ValueError):
        return False


def _text(v) -> str | None:
    return None if _blank(v) else str(v).strip()


def _num(v, default=0.0) -> float:
    if _blank(v):
        return default
    return float(v)


def _hhmm(v) -> int | None:
    """'07:30' -> 450 分鐘；空白 -> None。也接受 Excel 時間物件。"""
    if _blank(v):
        return None
    if hasattr(v, "hour") and hasattr(v, "minute"):
        return v.hour * 60 + v.minute
    s = str(v).strip()
    if s == "" or s.lower() == "nan":
        return None
    if ":" not in s:
        raise ValueError(f"時間格式應為 HH:MM，收到「{s}」")
    h, m = s.split(":")[:2]
    return int(h) * 60 + int(m)


@dataclass
class SpecimenType:
    code: str
    name: str
    share: float
    urgent_share: float
    blocks: tuple[float, float, float]
    slides_per_block: tuple[float, float, float]
    gross_min: tuple[float, float, float]
    report_min: tuple[float, float, float]
    fixation_h: float
    tat_target_h: float


@dataclass
class Task:
    code: str
    name: str
    unit: str
    tri: tuple[float, float, float] | None
    staff: str | None
    equip: str | None


@dataclass
class ProcessorRun:
    name: str
    days: list[int]          # 0=週一
    start_min: int
    hours: float
    machines: int
    capacity_blocks: int
    types: set[str]
    urgent_ok: bool


SLOTS_PER_DAY = 48  # 每 30 分鐘一格
SLOT_MIN = 30


@dataclass
class Config:
    general: dict[str, float]
    types: list[SpecimenType]
    tasks: dict[str, Task]
    # 資源名稱 -> 7×48 的容量表（每 30 分鐘一格）
    schedules: dict[str, list[list[int]]]
    resource_kind: dict[str, str]
    processor_runs: list[ProcessorRun]
    arrival_weights: list[list[float]]  # [平日, 週六, 週日] × 24 小時
    sheets: dict[str, pd.DataFrame] = field(repr=False, default_factory=dict)

    def g(self, key: str) -> float:
        return self.general[key]

    def type_by_code(self, code: str) -> SpecimenType:
        for t in self.types:
            if t.code == code:
                return t
        raise KeyError(code)

    def copy(self) -> "Config":
        return copy.deepcopy(self)

    def staff_resources(self) -> list[str]:
        return [r for r, k in self.resource_kind.items() if k == STAFF]

    def weekly_capacity_minutes(self, resource: str) -> float:
        return sum(sum(day) for day in self.schedules[resource]) * SLOT_MIN

    def add_units(self, resource: str, n: int, day_slots: tuple[int, int] | None = None,
                  days: range = range(5)) -> None:
        """在班表上加人或加設備。day_slots 為 (起始格, 結束格)，預設沿用該資源平日最常見的時段。"""
        sched = self.schedules[resource]
        if day_slots is None:
            row = sched[0]
            on = [i for i, v in enumerate(row) if v > 0]
            day_slots = (min(on), max(on) + 1) if on else (16, 34)
        for d in days:
            for s in range(*day_slots):
                sched[d][s] = max(0, sched[d][s] + n)


def build_config(sheets: dict[str, pd.DataFrame]) -> Config:
    gen_df = sheets[SHEET_GENERAL]
    general = {_text(r["代碼"]): _num(r["數值"]) for _, r in gen_df.iterrows()
               if not _blank(r["代碼"])}
    defaults = {str(r["代碼"]): float(r["數值"]) for _, r in _general().iterrows()}
    for k, v in defaults.items():
        general.setdefault(k, v)

    types = []
    for _, r in sheets[SHEET_TYPES].iterrows():
        if _blank(r["代碼"]):
            continue
        tri = lambda p: tuple(_num(r[f"{p}_{s}"]) for s in ("最少", "最可能", "最多")) \
            if f"{p}_最少" in r else tuple(_num(r[f"{p}_{s}"]) for s in ("最短", "最可能", "最長"))
        types.append(SpecimenType(
            code=str(r["代碼"]).strip(), name=str(r["名稱"]), share=_num(r["比例"]),
            urgent_share=_num(r["急件比例"]),
            blocks=tri("蠟塊數"), slides_per_block=tri("每塊玻片"),
            gross_min=tri("取材分鐘"), report_min=tri("判讀分鐘"),
            fixation_h=_num(r["固定時數"]), tat_target_h=_num(r["TAT目標小時"], 72)))

    tasks = {}
    for _, r in sheets[SHEET_TASKS].iterrows():
        code = _text(r["代碼"])
        if not code:
            continue
        unit = str(r["計算單位"]).strip()
        tri = None
        if unit != UNIT_BY_TYPE:
            tri = (_num(r["最短分鐘"]), _num(r["最可能分鐘"]), _num(r["最長分鐘"]))
        staff, equip = _text(r["人力資源"]), _text(r["設備資源"])
        tasks[code] = Task(code, str(r["作業"]), unit, tri, staff, equip)

    schedules: dict[str, list[list[int]]] = {}
    kinds: dict[str, str] = {}
    for _, r in sheets[SHEET_SHIFTS].iterrows():
        name = _text(r["資源"])
        if not name:
            continue
        kinds[name] = _text(r["類型"]) or STAFF
        sched = schedules.setdefault(name, [[0] * SLOTS_PER_DAY for _ in range(7)])
        n = int(_num(r["數量"]))
        for days, (c0, c1) in (
            (range(0, 5), ("平日開始", "平日結束")),
            (range(5, 6), ("週六開始", "週六結束")),
            (range(6, 7), ("週日開始", "週日結束")),
        ):
            a, b = _hhmm(r[c0]), _hhmm(r[c1])
            if a is None or b is None:
                continue
            if b <= a:  # 跨午夜
                b += 24 * 60
            for d in days:
                for s in range(a // SLOT_MIN, -(-b // SLOT_MIN)):
                    dd, ss = (d + s // SLOTS_PER_DAY) % 7, s % SLOTS_PER_DAY
                    sched[dd][ss] += n

    runs = []
    for _, r in sheets[SHEET_PROCESSOR].iterrows():
        if _blank(r["名稱"]):
            continue
        days = [WEEKDAYS.index(ch) for ch in str(r["星期"]) if ch in WEEKDAYS]
        runs.append(ProcessorRun(
            name=str(r["名稱"]), days=days, start_min=_hhmm(r["開始時間"]) or 0,
            hours=_num(r["處理時數"]), machines=int(_num(r["台數"])),
            capacity_blocks=int(_num(r["每台容量蠟塊"])),
            types={t.strip() for t in str(r["適用檢體代碼"]).split(",") if t.strip()},
            urgent_ok=str(r["急件可用"]).strip() in ("是", "1", "True", "true", "Y", "y")))

    arr = sheets[SHEET_ARRIVAL]
    weights = [[_num(v) for v in arr[c].tolist()] for c in ("平日權重", "週六權重", "週日權重")]

    cfg = Config(general=general, types=types, tasks=tasks, schedules=schedules,
                 resource_kind=kinds, processor_runs=runs, arrival_weights=weights,
                 sheets=sheets)
    errors = validate(cfg)
    if errors:
        raise ValueError("參數有誤：\n- " + "\n- ".join(errors))
    return cfg


def validate(cfg: Config) -> list[str]:
    errs = []
    missing_tasks = [c for c in TASK_CODES if c not in cfg.tasks]
    if missing_tasks:
        errs.append(f"「{SHEET_TASKS}」缺少作業代碼：{', '.join(missing_tasks)}")
    for t in cfg.tasks.values():
        for res in (t.staff, t.equip):
            if res and res not in cfg.schedules:
                errs.append(f"作業「{t.name}」用到的資源「{res}」不在「{SHEET_SHIFTS}」裡")
        if t.tri and not (t.tri[0] <= t.tri[1] <= t.tri[2]):
            errs.append(f"作業「{t.name}」的時間需滿足 最短 ≤ 最可能 ≤ 最長")
    if "染色機" not in cfg.schedules:
        errs.append(f"「{SHEET_SHIFTS}」需要有「染色機」這一列（設定運轉時段與台數）")
    share = sum(t.share for t in cfg.types)
    if abs(share - 1) > 0.01:
        errs.append(f"檢體類型比例加總應為 1，目前是 {share:.2f}")
    for t in cfg.types:
        for label, tri in (("蠟塊數", t.blocks), ("每塊玻片", t.slides_per_block),
                           ("取材分鐘", t.gross_min), ("判讀分鐘", t.report_min)):
            if not (tri[0] <= tri[1] <= tri[2]):
                errs.append(f"檢體類型「{t.name}」的{label}需滿足 最少 ≤ 最可能 ≤ 最多")
        if not any(t.code in r.types for r in cfg.processor_runs):
            errs.append(f"檢體類型「{t.name}」({t.code}) 沒有任何脫水機排程可以處理")
        if t.blocks[0] < 1:
            errs.append(f"檢體類型「{t.name}」蠟塊數最少要 1")
        big = max((r.capacity_blocks for r in cfg.processor_runs if t.code in r.types), default=0)
        if big and t.blocks[2] > big:
            errs.append(f"檢體類型「{t.name}」最多蠟塊數 {t.blocks[2]:.0f} 超過脫水機單台容量 {big}")
    if sum(sum(w) for w in cfg.arrival_weights) <= 0:
        errs.append("到件時段權重全部為 0")
    for i, label in enumerate(("平日", "週六", "週日")):
        ratio = 1 if i == 0 else cfg.g("sat_ratio" if i == 1 else "sun_ratio")
        if ratio > 0 and sum(cfg.arrival_weights[i]) <= 0:
            errs.append(f"{label}有到件，但「{SHEET_ARRIVAL}」的{label}權重全部為 0")
    return errs


def load_default() -> Config:
    return build_config(default_sheets())
