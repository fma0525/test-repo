"""病理中心離散事件模擬模型（salabim）。

時間單位：分鐘。t = 0 為第一週週一 00:00。

每件檢體依序經過：
收件 → (固定等待) → 取材 → 脫水機(批次) → 包埋 → 切片 → 染色機(批次)
→ 品管配片 → (數位掃描) → 判讀 → (加做特殊染色 → 補判讀) → 發報告

每一段時間都歸到一種類別（價值流分析用）：
- 作業：人員實際在處理
- 設備處理：機器在跑（脫水、染色、掃描）
- 排隊等待：等人力或設備
- 批次等待：等脫水機或染色機開機
- 必要等待：固定、外送特殊染色等流程上必須的等待
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
import salabim as sim

from .config import (SLOT_MIN, SLOTS_PER_DAY, UNIT_BLOCK, UNIT_CASE, UNIT_SLIDE, Config,
                     SpecimenType)

sim.yieldless(True)

DAY = 24 * 60
WEEK = 7 * DAY

CAT_WORK = "作業"
CAT_MACHINE = "設備處理"
CAT_QUEUE = "排隊等待"
CAT_BATCH = "批次等待"
CAT_REQUIRED = "必要等待"
CATEGORIES = [CAT_WORK, CAT_MACHINE, CAT_QUEUE, CAT_BATCH, CAT_REQUIRED]

# 階段名稱（依流程順序）
ST_RECEPTION = "收件"
ST_FIXATION = "固定"
ST_GROSSING = "取材"
ST_PROCESSING = "脫水"
ST_EMBEDDING = "包埋"
ST_MICROTOMY = "切片"
ST_STAINING = "染色"
ST_QC = "品管配片"
ST_SCANNING = "掃描"
ST_REPORTING = "判讀"
ST_IHC = "特殊染色"
STAGES = [ST_RECEPTION, ST_FIXATION, ST_GROSSING, ST_PROCESSING, ST_EMBEDDING, ST_MICROTOMY,
          ST_STAINING, ST_QC, ST_SCANNING, ST_REPORTING, ST_IHC]


# ---------------------------------------------------------------------------
# 抽樣
# ---------------------------------------------------------------------------
def tri(rng: np.random.Generator, t: tuple[float, float, float]) -> float:
    a, m, b = t
    if b <= a:
        return float(a)
    return float(rng.triangular(a, min(max(m, a), b), b))


@dataclass
class CaseSpec:
    """一件檢體的屬性（與模擬引擎無關，靜態產能分析也會用）。"""
    type_code: str
    urgent: bool
    blocks: int
    slides: int
    ihc: bool


def sample_case(rng: np.random.Generator, cfg: Config, stype: SpecimenType | None = None) -> CaseSpec:
    if stype is None:
        shares = np.array([t.share for t in cfg.types], dtype=float)
        stype = cfg.types[int(rng.choice(len(shares), p=shares / shares.sum()))]
    blocks = max(1, int(round(tri(rng, stype.blocks))))
    a, m, b = stype.slides_per_block
    if b <= a:
        per = np.full(blocks, a)
    else:
        per = rng.triangular(a, min(max(m, a), b), b, size=blocks)
    slides = int(np.maximum(1, np.round(per)).sum())
    return CaseSpec(type_code=stype.code, urgent=bool(rng.random() < stype.urgent_share),
                    blocks=blocks, slides=slides, ihc=bool(rng.random() < cfg.g("ihc_prob")))


def task_minutes(rng: np.random.Generator, cfg: Config, code: str, spec: CaseSpec) -> float:
    t = cfg.tasks[code]
    if code == "grossing":
        return tri(rng, cfg.type_by_code(spec.type_code).gross_min)
    if code == "reporting":
        return tri(rng, cfg.type_by_code(spec.type_code).report_min)
    n = {UNIT_CASE: 1, UNIT_BLOCK: spec.blocks, UNIT_SLIDE: spec.slides}.get(t.unit, 1)
    if n == 1:
        return tri(rng, t.tri)
    # 多個單位：逐一抽樣再加總（論文 4.4 節的做法）
    a, m, b = t.tri
    if b <= a:
        return a * n
    return float(rng.triangular(a, min(max(m, a), b), b, size=n).sum())


def arrival_times(rng: np.random.Generator, cfg: Config, daily_cases: float, days: int) -> np.ndarray:
    """非齊次 Poisson 到件：每小時的期望件數 = 當天件數 × 該小時權重比例。"""
    ratios = [1.0, cfg.g("sat_ratio"), cfg.g("sun_ratio")]
    times = []
    for d in range(days):
        wd = d % 7
        kind = 0 if wd < 5 else (1 if wd == 5 else 2)
        w = np.asarray(cfg.arrival_weights[kind], dtype=float)
        if w.sum() <= 0 or ratios[kind] <= 0:
            continue
        lam = daily_cases * ratios[kind] * w / w.sum()
        counts = rng.poisson(lam)
        for h, c in enumerate(counts):
            if c:
                times.append(d * DAY + h * 60 + rng.random(c) * 60)
    if not times:
        return np.array([])
    return np.sort(np.concatenate(times))


# ---------------------------------------------------------------------------
# 模型
# ---------------------------------------------------------------------------
@dataclass
class RunResult:
    cases: list[dict]
    wip: dict[str, np.ndarray]     # 階段 -> 每小時平均在製品件數
    system_wip: np.ndarray         # 全系統每小時平均在製品件數
    resources: dict[str, dict]     # 名稱 -> {kind, busy, cap}（每小時忙碌/可用單位數）
    processor_runs: list[dict]
    stain_runs: list[dict]
    window: tuple[float, float]
    end_time: float
    meta: dict = field(default_factory=dict)


class PathLabModel:
    def __init__(self, cfg: Config, seed: int = 0, daily_cases: float | None = None):
        self.cfg = cfg
        self.rng = np.random.default_rng(seed)
        self.daily = cfg.g("daily_cases") if daily_cases is None else daily_cases
        g = cfg.g
        self.warm = g("warmup_weeks") * WEEK
        self.window = (self.warm, self.warm + g("sim_weeks") * WEEK)
        self.horizon = self.window[1] + g("drain_weeks") * WEEK
        self.digital = g("digital") >= 0.5

        self.env = sim.Environment(trace=False, random_seed=seed)
        self.resources: dict[str, sim.Resource] = {}
        for name, kind in cfg.resource_kind.items():
            if name == "染色機":
                continue
            self.resources[name] = sim.Resource(name, capacity=0, env=self.env)

        self.cases: list[Case] = []
        self.segments: list[tuple] = []
        self.processor_queue: list[Case] = []
        self.processor_runs: list[dict] = []
        self.stain_queue: list[Case] = []
        self.stain_runs: list[dict] = []
        self.stainers: list[Stainer] = []

    # -- 建構 ---------------------------------------------------------------
    def build(self) -> None:
        env = self.env
        for name, res in self.resources.items():
            ShiftController(env=env, model=self, resource=res, schedule=self.cfg.schedules[name])
        n_stainers = max(max(day) for day in self.cfg.schedules["染色機"])
        for i in range(n_stainers):
            self.stainers.append(Stainer(env=env, model=self, index=i))
        ProcessorScheduler(env=env, model=self)
        times = arrival_times(self.rng, self.cfg, self.daily, int(math.ceil(self.horizon / DAY)))
        for i, t in enumerate(times):
            if t >= self.horizon:
                break
            spec = sample_case(self.rng, self.cfg)
            c = Case(env=env, model=self, cid=i, spec=spec, at=float(t))
            self.cases.append(c)

    def run(self) -> RunResult:
        self.build()
        self.env.run(till=self.horizon)
        return self._collect()

    # -- 工具 ---------------------------------------------------------------
    def staffed_slot_capacity(self, schedule, t: float) -> int:
        slot = int((t % WEEK) // SLOT_MIN)
        return schedule[slot // SLOTS_PER_DAY][slot % SLOTS_PER_DAY]

    def notify_stainers(self) -> None:
        for s in self.stainers:
            if s.ispassive():
                s.activate()

    # -- 收集結果 -------------------------------------------------------------
    def _collect(self) -> RunResult:
        w0, w1 = self.window
        cases = []
        cohort_ids = set()
        for c in self.cases:
            if not (w0 <= c.arrival < w1):
                continue
            cohort_ids.add(c.cid)
            tot = {k: 0.0 for k in CATEGORIES}
            stage_q = {}
            for (_, st, cat, a, b) in c.segs:
                tot[cat] += b - a
                if cat in (CAT_QUEUE, CAT_BATCH):
                    stage_q[st] = stage_q.get(st, 0.0) + (b - a)
            row = {
                "id": c.cid, "type": c.spec.type_code, "urgent": c.spec.urgent,
                "blocks": c.spec.blocks, "slides": c.spec.slides, "ihc": c.spec.ihc,
                "arrival": c.arrival, "done": c.done_time, "lab_done": c.lab_done,
                "first_report": c.first_report,
                "missed_processor": c.missed_processor,
            }
            for k in CATEGORIES:
                row[f"cat_{k}"] = tot[k]
            for st in STAGES:
                row[f"q_{st}"] = stage_q.get(st, 0.0)
            cases.append(row)

        # 在製品（WIP）：統計期內每小時平均有幾件在各階段（含暖機期進來的檢體）
        n_bins = int((w1 - w0) // 60)
        wip = {st: np.zeros(n_bins) for st in STAGES}
        system = np.zeros(n_bins)
        for (_, st, _cat, a, b) in self.segments:
            if b > w0 and a < w1:
                _add_interval(wip[st], a, b, w0)
        for c in self.cases:
            if c.arrival is None:
                continue
            end = c.done_time if c.done_time is not None else self.env.now()
            if end > w0 and c.arrival < w1:
                _add_interval(system, c.arrival, end, w0)

        res_out = {}
        for name, r in self.resources.items():
            busy = _bin_level(r.claimed_quantity, w0, w1, self.env.now())
            cap = _bin_level(r.capacity, w0, w1, self.env.now())
            res_out[name] = {"kind": self.cfg.resource_kind[name], "busy": busy, "cap": cap}
        # 染色機：由批次紀錄換算
        busy = np.zeros(n_bins)
        for run in self.stain_runs:
            _add_interval(busy, run["start"], run["end"], w0)
        cap = np.zeros(n_bins)
        sched = self.cfg.schedules["染色機"]
        for i in range(n_bins):
            t = w0 + i * 60
            cap[i] = (self.staffed_slot_capacity(sched, t) + self.staffed_slot_capacity(sched, t + 30)) / 2
        res_out["染色機"] = {"kind": self.cfg.resource_kind["染色機"], "busy": busy, "cap": cap}

        return RunResult(cases=cases, wip=wip, system_wip=system, resources=res_out,
                         processor_runs=[r for r in self.processor_runs if w0 <= r["start"] < w1],
                         stain_runs=[r for r in self.stain_runs if w0 <= r["start"] < w1],
                         window=self.window, end_time=self.env.now(),
                         meta={"daily_cases": self.daily})


def _add_interval(bins: np.ndarray, a: float, b: float, t0: float) -> None:
    """把 [a, b) 的忙碌時間（小時）加到每小時的格子。"""
    a, b = max(a, t0), min(b, t0 + len(bins) * 60)
    while a < b:
        i = int((a - t0) // 60)
        nxt = min(b, t0 + (i + 1) * 60)
        bins[i] += (nxt - a) / 60
        a = nxt


def _bin_level(monitor: sim.Monitor, t0: float, t1: float, now: float) -> np.ndarray:
    """把 level monitor 在 [t0, t1) 的時間加權平均值，切成每小時一格。"""
    x, t = monitor.xt()
    x = np.asarray(x, dtype=float)
    t = np.asarray(t, dtype=float)
    n = int((t1 - t0) // 60)
    edges = t0 + np.arange(n + 1) * 60
    # 每段 [t_k, t_{k+1}) 的值為 x_k
    seg_end = np.append(t[1:], max(now, t1))
    out = np.zeros(n)
    for xk, a, b in zip(x, t, seg_end):
        if b <= t0 or a >= t1 or xk == 0:
            continue
        a, b = max(a, t0), min(b, t1)
        i0, i1 = int((a - t0) // 60), int(math.ceil((b - t0) / 60))
        for i in range(i0, min(i1, n)):
            lo, hi = max(a, edges[i]), min(b, edges[i + 1])
            if hi > lo:
                out[i] += xk * (hi - lo) / 60
    return out


# ---------------------------------------------------------------------------
# 元件
# ---------------------------------------------------------------------------
class ShiftController(sim.Component):
    """依班表每 30 分鐘調整資源容量。容量下降時，進行中的工作會做完（視同延後下班）。"""

    def setup(self, model: PathLabModel, resource: sim.Resource, schedule):
        self.model = model
        self.res = resource
        self.sched = schedule

    def process(self):
        flat = [v for day in self.sched for v in day]
        n = len(flat)
        # 只在容量改變的時間點醒來
        changes = [i for i in range(n) if flat[i] != flat[i - 1]]
        self.res.set_capacity(flat[0])
        if not changes:
            return
        week = 0
        while True:
            for i in changes:
                t = week * WEEK + i * SLOT_MIN
                if t < self.env.now():
                    continue
                self.hold(till=t)
                self.res.set_capacity(flat[i])
            week += 1


class Case(sim.Component):
    def setup(self, model: PathLabModel, cid: int, spec: CaseSpec):
        self.model = model
        self.cid = cid
        self.spec = spec
        self.prio = 0 if spec.urgent else 1
        self.arrival = None
        self.done_time = None
        self.lab_done = None
        self.first_report = None
        self.missed_processor = 0
        self.segs: list[tuple] = []
        self.batch_wait_start = None

    def seg(self, stage, cat, a, b):
        if b > a:
            s = (self.cid, stage, cat, a, b)
            self.segs.append(s)
            self.model.segments.append(s)

    def task(self, stage: str, code: str):
        m = self.model
        t = m.cfg.tasks[code]
        res = [m.resources[r] for r in (t.staff, t.equip) if r]
        minutes = task_minutes(m.rng, m.cfg, code, self.spec)
        t0 = self.env.now()
        if res:
            self.request(*res, request_priority=self.prio)
        t1 = self.env.now()
        self.seg(stage, CAT_QUEUE, t0, t1)
        self.hold(minutes)
        self.seg(stage, CAT_MACHINE if not t.staff else CAT_WORK, t1, self.env.now())
        if res:
            self.release()

    def process(self):
        m = self.model
        self.arrival = self.env.now()
        self.task(ST_RECEPTION, "reception")

        fix_until = self.arrival + m.cfg.type_by_code(self.spec.type_code).fixation_h * 60
        if self.env.now() < fix_until:
            t0 = self.env.now()
            self.hold(till=fix_until)
            self.seg(ST_FIXATION, CAT_REQUIRED, t0, self.env.now())

        self.task(ST_GROSSING, "grossing")

        # 脫水機：等排程開機（批次）
        self.batch_wait_start = self.env.now()
        m.processor_queue.append(self)
        self.passivate()  # 由 ProcessorScheduler 裝載並在程序結束時喚醒

        self.task(ST_EMBEDDING, "embedding")
        # 切片：每蠟塊時間 + 每張玻片時間，同一位技術員連續完成
        self._microtomy()

        # 染色機（批次）
        self.batch_wait_start = self.env.now()
        m.stain_queue.append(self)
        m.notify_stainers()
        self.passivate()

        self.task(ST_QC, "qc_case")  # 每件部分
        self._extra_minutes(ST_QC, "qc_slide")
        if m.digital:
            self.task(ST_SCANNING, "scanning")
        self.lab_done = self.env.now()

        self.task(ST_REPORTING, "reporting")
        self.first_report = self.env.now()
        if self.spec.ihc:
            t0 = self.env.now()
            self.hold(m.cfg.g("ihc_delay_h") * 60)
            self.seg(ST_IHC, CAT_REQUIRED, t0, self.env.now())
            self.task(ST_IHC, "ihc_report")
        self.done_time = self.env.now()

    def _microtomy(self):
        m = self.model
        t = m.cfg.tasks["microtomy_block"]
        res = [m.resources[r] for r in (t.staff, t.equip) if r]
        minutes = (task_minutes(m.rng, m.cfg, "microtomy_block", self.spec)
                   + task_minutes(m.rng, m.cfg, "microtomy_slide", self.spec))
        t0 = self.env.now()
        self.request(*res, request_priority=self.prio)
        t1 = self.env.now()
        self.seg(ST_MICROTOMY, CAT_QUEUE, t0, t1)
        self.hold(minutes)
        self.seg(ST_MICROTOMY, CAT_WORK, t1, self.env.now())
        self.release()

    def _extra_minutes(self, stage, code):
        """同一資源接著做的追加作業（例如品管每張玻片），不重新排隊。"""
        m = self.model
        t = m.cfg.tasks[code]
        res = [m.resources[r] for r in (t.staff, t.equip) if r]
        if not res:
            return
        t0 = self.env.now()
        self.request(*res, request_priority=-1)  # 已在手上的工作，優先完成
        t1 = self.env.now()
        self.seg(stage, CAT_QUEUE, t0, t1)
        self.hold(task_minutes(m.rng, m.cfg, code, self.spec))
        self.seg(stage, CAT_WORK, t1, self.env.now())
        self.release()


class ProcessorScheduler(sim.Component):
    """依「脫水機排程」在指定時間開機，裝載等候中的檢體。

    裝載規則（參考 WSC 2024 論文 4.3 節）：
    - 同一件檢體的蠟塊不拆批
    - 急件優先，其餘先到先裝
    - 只裝適用此程序的檢體；裝不下的等下一次
    """

    def setup(self, model: PathLabModel):
        self.model = model
        events = []
        for run in model.cfg.processor_runs:
            for d in run.days:
                events.append((d * DAY + run.start_min, run))
        self.week_events = sorted(events, key=lambda e: e[0])

    def process(self):
        m = self.model
        week = 0
        while True:
            for offset, run in self.week_events:
                t = week * WEEK + offset
                if t >= m.horizon:
                    return
                if t > self.env.now():
                    self.hold(till=t)
                self._start(run)
            week += 1

    def _start(self, run):
        m = self.model
        now = self.env.now()
        cap_total = run.machines * run.capacity_blocks
        eligible = [c for c in m.processor_queue
                    if c.spec.type_code in run.types and (run.urgent_ok or not c.spec.urgent)]
        eligible.sort(key=lambda c: (c.prio, c.batch_wait_start))
        loaded, used = [], 0
        for c in eligible:
            if used + c.spec.blocks <= cap_total:
                loaded.append(c)
                used += c.spec.blocks
        for c in m.processor_queue:
            if c not in loaded and c.spec.type_code in run.types:
                c.missed_processor += 1
        ids = {id(c) for c in loaded}
        m.processor_queue = [c for c in m.processor_queue if id(c) not in ids]
        end = now + run.hours * 60
        for c in loaded:
            c.seg(ST_PROCESSING, CAT_BATCH, c.batch_wait_start, now)
            c.seg(ST_PROCESSING, CAT_MACHINE, now, end)
            c.activate(at=end)
        m.processor_runs.append({"name": run.name, "start": now, "end": end,
                                 "blocks": used, "capacity": cap_total, "cases": len(loaded),
                                 "left_behind": sum(1 for c in m.processor_queue
                                                    if c.spec.type_code in run.types)})


class Stainer(sim.Component):
    """一台染色封片機。運轉時段內有玻片就湊批開機。"""

    def setup(self, model: PathLabModel, index: int):
        self.model = model
        self.index = index

    def _on_duty(self, t) -> bool:
        m = self.model
        return self.index < m.staffed_slot_capacity(m.cfg.schedules["染色機"], t)

    def process(self):
        m = self.model
        g = m.cfg.g
        cap = int(g("stain_capacity"))
        run_min = g("stain_minutes")
        collect = g("stain_collect_min")
        while True:
            now = self.env.now()
            if not self._on_duty(now):
                self.hold(SLOT_MIN - (now % SLOT_MIN) if now % SLOT_MIN else SLOT_MIN)
                continue
            if not m.stain_queue:
                self.passivate()
                continue
            queued = sum(c.spec.slides for c in m.stain_queue)
            oldest = min(c.batch_wait_start for c in m.stain_queue)
            if queued < cap and now < oldest + collect:
                # 還沒湊滿，等到最早的玻片等滿上限（期間有新玻片會被喚醒重算）
                self.hold(till=oldest + collect)
                continue
            q = sorted(m.stain_queue, key=lambda c: (c.prio, c.batch_wait_start))
            batch, used = [], 0
            for c in q:
                if used + c.spec.slides <= cap or not batch:
                    batch.append(c)
                    used += c.spec.slides
            ids = {id(c) for c in batch}
            m.stain_queue = [c for c in m.stain_queue if id(c) not in ids]
            # 一件玻片超過一批容量時，視為多跑幾批
            dur = run_min * max(1, math.ceil(used / cap))
            end = now + dur
            for c in batch:
                c.seg(ST_STAINING, CAT_BATCH, c.batch_wait_start, now)
                c.seg(ST_STAINING, CAT_MACHINE, now, end)
            m.stain_runs.append({"machine": self.index, "start": now, "end": end,
                                 "slides": used, "capacity": cap * max(1, math.ceil(used / cap))})
            self.hold(dur)
            for c in batch:
                c.activate()


def run_once(cfg: Config, seed: int = 0, daily_cases: float | None = None) -> RunResult:
    return PathLabModel(cfg, seed=seed, daily_cases=daily_cases).run()
