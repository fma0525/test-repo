"""作業管理分析：把多次模擬結果整理成 KPI、瓶頸、價值流、產能與成長規劃。"""

from __future__ import annotations

import math
import os
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass

import numpy as np
import pandas as pd

from .config import EQUIP, STAFF, UNIT_BY_TYPE, Config
from .model import (CATEGORIES, DAY, STAGES, WEEK, RunResult, run_once, sample_case,
                    task_minutes)

# 哪些階段用到哪個資源（用來把排隊時間對應回資源）
STAGE_OF_TASK = {
    "reception": "收件", "grossing": "取材", "embedding": "包埋",
    "microtomy_block": "切片", "microtomy_slide": "切片", "qc_case": "品管配片",
    "qc_slide": "品管配片", "scanning": "掃描", "reporting": "判讀", "ihc_report": "特殊染色",
}

# 在製品圖用的階段分組（5 組，對應圖表色票）
WIP_GROUPS = {
    "收件・取材": ["收件", "固定", "取材"],
    "脫水": ["脫水"],
    "包埋・切片": ["包埋", "切片"],
    "染色・品管・掃描": ["染色", "品管配片", "掃描"],
    "判讀・特殊染色": ["判讀", "特殊染色"],
}


# ---------------------------------------------------------------------------
# 執行
# ---------------------------------------------------------------------------
def _job(args) -> RunResult:
    cfg, seed, daily = args
    return run_once(cfg, seed=seed, daily_cases=daily)


def run_many(jobs: list[tuple[Config, int, float | None]], parallel: bool = True,
             progress=None) -> list[RunResult]:
    """平行跑多組 (cfg, seed, daily_cases)。progress(i, n) 用於回報進度。"""
    n = len(jobs)
    workers = min(n, os.cpu_count() or 1)
    if not parallel or workers <= 1:
        out = []
        for i, j in enumerate(jobs):
            out.append(_job(j))
            if progress:
                progress(i + 1, n)
        return out
    out = [None] * n
    with ProcessPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(_job, j): i for i, j in enumerate(jobs)}
        done = 0
        from concurrent.futures import as_completed
        for f in as_completed(futs):
            out[futs[f]] = f.result()
            done += 1
            if progress:
                progress(done, n)
    return out


def replications(cfg: Config, daily: float | None = None, n: int | None = None,
                 seed0: int | None = None) -> list[tuple[Config, int, float | None]]:
    n = int(n or cfg.g("replications"))
    seed0 = int(cfg.g("seed") if seed0 is None else seed0)
    return [(cfg, seed0 + 1000 * i, daily) for i in range(n)]


# ---------------------------------------------------------------------------
# 單一情境的彙整
# ---------------------------------------------------------------------------
@dataclass
class Summary:
    kpi: dict
    cases: pd.DataFrame
    resources: pd.DataFrame
    hourly: pd.DataFrame          # 資源 × 時刻（平日平均使用率）
    stages: pd.DataFrame
    value_stream: pd.DataFrame
    wip_week: pd.DataFrame        # 一週 168 小時 × 階段組的平均在製品
    processor: pd.DataFrame
    little: dict


def summarize(cfg: Config, results: list[RunResult]) -> Summary:
    warn = cfg.g("util_warn")
    targets = {t.code: t.tat_target_h for t in cfg.types}
    names = {t.code: t.name for t in cfg.types}

    frames = []
    for i, r in enumerate(results):
        df = pd.DataFrame(r.cases)
        df["rep"] = i
        frames.append(df)
    cases = pd.concat(frames, ignore_index=True)
    cases["type_name"] = cases["type"].map(names)
    cases["tat_h"] = (cases["done"] - cases["arrival"]) / 60
    cases["lab_tat_h"] = (cases["lab_done"] - cases["arrival"]) / 60
    cases["target_h"] = cases["type"].map(targets)
    cases["met"] = cases["tat_h"] <= cases["target_h"]
    done = cases.dropna(subset=["tat_h"])
    incomplete = int(cases["tat_h"].isna().sum())

    w0, w1 = results[0].window
    weeks = (w1 - w0) / WEEK
    n_rep = len(results)

    # ---- 資源使用率 -------------------------------------------------------
    rows, hourly_rows = [], []
    for name in results[0].resources:
        busy = np.mean([r.resources[name]["busy"] for r in results], axis=0)
        cap = np.mean([r.resources[name]["cap"] for r in results], axis=0)
        kind = results[0].resources[name]["kind"]
        util = busy.sum() / cap.sum() if cap.sum() > 0 else float("nan")
        with np.errstate(divide="ignore", invalid="ignore"):
            hu = np.where(cap > 0, busy / cap, np.nan)
        staffed = hu[~np.isnan(hu)]
        peak = float(np.nanpercentile(staffed, 90)) if staffed.size else float("nan")
        # 平日每小時平均
        hours = np.arange(len(busy))
        abs_t = w0 + hours * 60
        dow = ((abs_t % WEEK) // DAY).astype(int)
        hod = ((abs_t % DAY) // 60).astype(int)
        for h in range(24):
            m = (dow < 5) & (hod == h)
            b, c = busy[m].sum(), cap[m].sum()
            hourly_rows.append({"資源": name, "時": h, "使用率": b / c if c > 0 else np.nan,
                                "平均在班": c / max(m.sum(), 1)})
        rows.append({"資源": name, "類型": kind,
                     "每週可用小時": cap.sum() / weeks, "每週忙碌小時": busy.sum() / weeks,
                     "使用率": util, "尖峰使用率": peak})
    res = pd.DataFrame(rows)

    # 每個資源相關階段的平均排隊時間（小時/件）
    stage_q = {st: done[f"q_{st}"].mean() / 60 for st in STAGES}
    res_stage = {}
    for code, t in cfg.tasks.items():
        for r in (t.staff, t.equip):
            if r:
                res_stage.setdefault(r, set()).add(STAGE_OF_TASK[code])
    res_stage["染色機"] = {"染色"}
    res["相關階段"] = res["資源"].map(lambda r: "、".join(sorted(res_stage.get(r, []),
                                                            key=STAGES.index)))
    res["平均排隊小時"] = res["資源"].map(
        lambda r: sum(stage_q[s] for s in res_stage.get(r, [])) if r in res_stage else np.nan)
    res["瓶頸"] = res["使用率"] >= warn
    res = res.sort_values("使用率", ascending=False).reset_index(drop=True)
    hourly = pd.DataFrame(hourly_rows)

    # ---- 階段時間 ---------------------------------------------------------
    stage_rows = []
    total_tat = done["tat_h"].mean()
    for st in STAGES:
        q = done[f"q_{st}"].mean() / 60
        stage_rows.append({"階段": st, "平均等待小時": q,
                           "佔TAT比例": q / total_tat if total_tat else np.nan})
    stages = pd.DataFrame(stage_rows)

    # ---- 價值流（各類別時間） ---------------------------------------------
    vs_rows = []
    for code, g in done.groupby("type"):
        row = {"檢體類型": names[code]}
        for c in CATEGORIES:
            row[c] = g[f"cat_{c}"].mean() / 60
        vs_rows.append(row)
    row = {"檢體類型": "全部"}
    for c in CATEGORIES:
        row[c] = done[f"cat_{c}"].mean() / 60
    vs_rows.append(row)
    vs = pd.DataFrame(vs_rows)
    vs["總計"] = vs[CATEGORIES].sum(axis=1)
    vs["增值比例"] = (vs["作業"] + vs["設備處理"]) / vs["總計"]

    # ---- 在製品：一週 168 小時的平均輪廓 -----------------------------------
    n_bins = len(results[0].system_wip)
    how = (((w0 + np.arange(n_bins) * 60) % WEEK) // 60).astype(int)
    wip_rows = {}
    for grp, sts in WIP_GROUPS.items():
        arr = np.mean([sum(r.wip[s] for s in sts) for r in results], axis=0)
        wip_rows[grp] = pd.Series(arr).groupby(how).mean().reindex(range(168)).values
    sys_arr = np.mean([r.system_wip for r in results], axis=0)
    wip_rows["全系統"] = pd.Series(sys_arr).groupby(how).mean().reindex(range(168)).values
    wip_week = pd.DataFrame(wip_rows)
    wip_week.index.name = "週內小時"

    # ---- 脫水機 -------------------------------------------------------------
    pr = pd.DataFrame([run for r in results for run in r.processor_runs])
    if len(pr):
        processor = pr.groupby("name").agg(每週次數=("start", lambda s: len(s) / n_rep / weeks),
                                           平均裝載蠟塊=("blocks", "mean"),
                                           容量蠟塊=("capacity", "mean"),
                                           平均件數=("cases", "mean"),
                                           平均未上機件數=("left_behind", "mean")).reset_index()
        processor["滿載率"] = processor["平均裝載蠟塊"] / processor["容量蠟塊"]
        processor = processor.rename(columns={"name": "程序"})
    else:
        processor = pd.DataFrame()

    # ---- Little's Law ------------------------------------------------------
    lam = len(cases) / n_rep / ((w1 - w0) / 60)       # 件/小時
    W = done["tat_h"].mean()                            # 小時
    L = float(sys_arr.mean())
    little = {"到件率_件每小時": lam, "平均TAT_小時": W, "預測WIP": lam * W, "實測WIP": L}

    # ---- KPI ----------------------------------------------------------------
    bott = res[res["類型"] == STAFF].iloc[0] if (res["類型"] == STAFF).any() else res.iloc[0]
    per_type = done.groupby("type_name").agg(平均TAT=("tat_h", "mean"),
                                             P90_TAT=("tat_h", lambda s: s.quantile(0.9)),
                                             達標率=("met", "mean"),
                                             目標小時=("target_h", "first"),
                                             件數=("tat_h", lambda s: len(s) / n_rep))
    kpi = {
        "平日每日件數": float(np.mean([r.meta["daily_cases"] for r in results])),
        "每週件數": len(cases) / n_rep / weeks,
        "平均TAT": W,
        "TAT中位數": done["tat_h"].median(),
        "P90_TAT": done["tat_h"].quantile(0.9),
        "達標率": done["met"].mean(),
        "實驗室TAT": done["lab_tat_h"].mean(),
        "未完成件數": incomplete / n_rep,
        "最忙人力": bott["資源"],
        "最忙人力使用率": bott["使用率"],
        "瓶頸數": int(res["瓶頸"].sum()),
        "錯過脫水機比例": (done["missed_processor"] > 0).mean(),
        "per_type": per_type.reset_index().rename(columns={"type_name": "檢體類型"}),
        "重複次數": n_rep,
    }
    return Summary(kpi=kpi, cases=cases, resources=res, hourly=hourly, stages=stages,
                   value_stream=vs, wip_week=wip_week, processor=processor, little=little)


# ---------------------------------------------------------------------------
# 靜態產能分析（不跑模擬，用期望值算負荷）
# ---------------------------------------------------------------------------
def expected_work(cfg: Config, n: int = 20000, seed: int = 7) -> dict:
    """每件檢體平均需要各資源幾分鐘、平均幾個蠟塊、幾張玻片。"""
    rng = np.random.default_rng(seed)
    per_res: dict[str, float] = {}
    blocks = slides = 0.0
    for _ in range(n):
        spec = sample_case(rng, cfg)
        blocks += spec.blocks
        slides += spec.slides
        for code, t in cfg.tasks.items():
            if code == "scanning" and cfg.g("digital") < 0.5:
                continue
            if code == "ihc_report" and not spec.ihc:
                continue
            m = task_minutes(rng, cfg, code, spec)
            for r in (t.staff, t.equip):
                if r:
                    per_res[r] = per_res.get(r, 0.0) + m
    return {"res": {k: v / n for k, v in per_res.items()}, "blocks": blocks / n,
            "slides": slides / n}


def weekly_cases(cfg: Config, daily: float | None = None) -> float:
    d = cfg.g("daily_cases") if daily is None else daily
    return d * (5 + cfg.g("sat_ratio") + cfg.g("sun_ratio"))


def static_capacity(cfg: Config, daily: float | None = None, ew: dict | None = None) -> pd.DataFrame:
    """各資源的負荷率 = 每週需要的工時 ÷ 每週可用工時；並換算節拍時間。"""
    ew = ew or expected_work(cfg)
    wc = weekly_cases(cfg, daily)
    rows = []
    for name, kind in cfg.resource_kind.items():
        cap_min = cfg.weekly_capacity_minutes(name)
        if name == "染色機":
            need = wc * ew["slides"] / cfg.g("stain_capacity") * cfg.g("stain_minutes")
        else:
            need = wc * ew["res"].get(name, 0.0)
        if need == 0:
            continue
        peak_units = max(max(day[:]) for day in cfg.schedules[name][:5]) if any(
            any(day) for day in cfg.schedules[name][:5]) else max(max(d) for d in cfg.schedules[name])
        rows.append({"資源": name, "類型": kind,
                     "每件工作含量_分": need / wc,
                     "節拍時間_分": cap_min / wc if wc else np.nan,
                     "每週需求小時": need / 60, "每週可用小時": cap_min / 60,
                     "負荷率": need / cap_min if cap_min else np.inf,
                     "平日最多在班": peak_units})
    # 脫水機：每週蠟塊數 vs 每週裝載容量
    cap_blocks = sum(len(r.days) * r.machines * r.capacity_blocks for r in cfg.processor_runs)
    need_blocks = wc * ew["blocks"]
    rows.append({"資源": "脫水機（蠟塊容量）", "類型": EQUIP,
                 "每件工作含量_分": np.nan, "節拍時間_分": np.nan,
                 "每週需求小時": np.nan, "每週可用小時": np.nan,
                 "負荷率": need_blocks / cap_blocks if cap_blocks else np.inf,
                 "平日最多在班": np.nan, "每週蠟塊": need_blocks, "每週容量蠟塊": cap_blocks})
    df = _numeric(pd.DataFrame(rows)).sort_values("負荷率", ascending=False).reset_index(drop=True)
    return df


def _numeric(df: pd.DataFrame) -> pd.DataFrame:
    for c in df.columns:
        if c not in ("資源", "類型"):
            df[c] = pd.to_numeric(df[c], errors="coerce").astype(float)
    return df


def growth_static(cfg: Config, ew: dict | None = None) -> pd.DataFrame:
    """依年成長率推估各資源哪一年超過警戒負荷，以及規劃期末需要增加多少產能。"""
    ew = ew or expected_work(cfg)
    g, years, warn = cfg.g("growth_rate"), int(cfg.g("growth_years")), cfg.g("util_warn")
    base = static_capacity(cfg, ew=ew)
    rows = []
    for _, r in base.iterrows():
        load = r["負荷率"]
        row = {"資源": r["資源"], "類型": r["類型"], "目前負荷率": load}
        for y in range(years + 1):
            row[f"第{y}年"] = load * (1 + g) ** y
        if load >= warn:
            row["超過警戒年"] = 0.0
        elif g > 0:
            row["超過警戒年"] = math.log(warn / load) / math.log(1 + g)
        else:
            row["超過警戒年"] = np.inf
        end_load = load * (1 + g) ** years
        factor = end_load / warn
        row["期末需增加產能"] = max(0.0, factor - 1)
        if not np.isnan(r.get("平日最多在班", np.nan)) and r["平日最多在班"]:
            row["期末約需增加人或台"] = max(0, math.ceil(r["平日最多在班"] * factor - 1e-9)
                                       - int(r["平日最多在班"]))
        else:
            row["期末約需增加人或台"] = np.nan
        rows.append(row)
    return _numeric(pd.DataFrame(rows)).sort_values("超過警戒年").reset_index(drop=True)


# ---------------------------------------------------------------------------
# 情境實驗
# ---------------------------------------------------------------------------
def scenario_kpis(cfg: Config, results: list[RunResult]) -> dict:
    s = summarize(cfg, results)
    staff = s.resources[s.resources["類型"] == STAFF]
    return {"平均TAT": s.kpi["平均TAT"], "P90_TAT": s.kpi["P90_TAT"], "達標率": s.kpi["達標率"],
            "實驗室TAT": s.kpi["實驗室TAT"], "未完成件數": s.kpi["未完成件數"],
            "最忙人力": staff.iloc[0]["資源"] if len(staff) else "",
            "最高人力使用率": staff["使用率"].max() if len(staff) else np.nan}


def growth_simulation(cfg: Config, n_rep: int | None = None, progress=None,
                      parallel: bool = True) -> pd.DataFrame:
    """依年成長率，逐年跑模擬。"""
    g, years = cfg.g("growth_rate"), int(cfg.g("growth_years"))
    n_rep = int(n_rep or cfg.g("replications"))
    jobs, keys = [], []
    for y in range(years + 1):
        daily = cfg.g("daily_cases") * (1 + g) ** y
        for job in replications(cfg, daily=daily, n=n_rep):
            jobs.append(job)
            keys.append(y)
    results = run_many(jobs, parallel=parallel, progress=progress)
    rows = []
    for y in range(years + 1):
        rs = [r for r, k in zip(results, keys) if k == y]
        row = {"年": y, "平日每日件數": cfg.g("daily_cases") * (1 + g) ** y}
        row.update(scenario_kpis(cfg, rs))
        rows.append(row)
    return pd.DataFrame(rows)


def staffing_experiment(cfg: Config, n_rep: int | None = None, progress=None,
                        parallel: bool = True) -> pd.DataFrame:
    """各人力資源「+1 人」（沿用該資源平日主要班別時段），比較 TAT。

    對應 WSC 2024 論文圖 5 的實驗設計。
    """
    n_rep = int(n_rep or cfg.g("replications"))
    scenarios = [("現況", None)] + [(f"+1 {r}", r) for r in cfg.staff_resources()]
    jobs, keys = [], []
    for label, res in scenarios:
        c = cfg
        if res:
            c = cfg.copy()
            c.add_units(res, 1)
        for job in replications(c, n=n_rep):
            jobs.append(job)
            keys.append(label)
    results = run_many(jobs, parallel=parallel, progress=progress)
    rows = []
    for label, res in scenarios:
        rs = [r for r, k in zip(results, keys) if k == label]
        s = summarize(cfg, rs)
        done = s.cases.dropna(subset=["tat_h"])
        rep_means = done.groupby("rep")["tat_h"].mean()
        half = 1.96 * rep_means.std(ddof=1) / math.sqrt(len(rep_means)) if len(rep_means) > 1 else 0
        rows.append({"情境": label, "平均TAT": s.kpi["平均TAT"], "CI半寬": half,
                     "P90_TAT": s.kpi["P90_TAT"], "達標率": s.kpi["達標率"],
                     "實驗室TAT": s.kpi["實驗室TAT"]})
    df = pd.DataFrame(rows)
    base = df.loc[0, "平均TAT"]
    df["TAT變化"] = df["平均TAT"] - base
    return df


# ---------------------------------------------------------------------------
# 自動判讀重點
# ---------------------------------------------------------------------------
def findings(cfg: Config, s: Summary, cap: pd.DataFrame | None = None,
             growth: pd.DataFrame | None = None) -> list[tuple[str, str]]:
    """回傳 (等級, 文字) 清單。等級：critical / warning / good / info。"""
    out = []
    warn = cfg.g("util_warn")
    res = s.resources
    staff = res[res["類型"] == STAFF]

    # 1. 瓶頸
    hot = res[res["使用率"] >= warn]
    if len(hot):
        names = "、".join(f"{r.資源}（{r.使用率:.0%}）" for r in hot.itertuples())
        out.append(("critical", f"使用率超過警戒值 {warn:.0%} 的資源：{names}。"
                                f"這些站點決定整體產出，改善應從這裡開始。"))
    elif len(staff):
        top = staff.iloc[0]
        out.append(("info", f"目前沒有資源超過警戒值 {warn:.0%}。負荷最重的人力是"
                            f"「{top['資源']}」，使用率 {top['使用率']:.0%}，是件數成長時最先出問題的地方。"))

    # 2. 等最久的階段 vs. 使用率：分辨「產能不足」和「時段錯配」
    st = s.stages.sort_values("平均等待小時", ascending=False).iloc[0]
    rel = res[res["相關階段"].str.contains(st["階段"], na=False)]
    if len(rel) and st["平均等待小時"] > 2:
        util = rel["使用率"].max()
        if util < 0.7:
            out.append(("warning",
                        f"等待最久的是「{st['階段']}」，平均每件等 {st['平均等待小時']:.1f} 小時"
                        f"（佔 TAT {st['佔TAT比例']:.0%}），但相關人力使用率只有 {util:.0%}。"
                        f"等待主要來自班表時段和上游批次的時間錯開，不是人手不足："
                        f"調整班別時段或脫水機排程，比加人更有效。可到「時段負荷」頁看每小時的情況。"))
        else:
            out.append(("warning",
                        f"等待最久的是「{st['階段']}」，平均每件等 {st['平均等待小時']:.1f} 小時"
                        f"（佔 TAT {st['佔TAT比例']:.0%}），相關資源使用率 {util:.0%}，屬於產能不足。"))

    # 3. 價值流
    vs = s.value_stream.set_index("檢體類型").loc["全部"]
    out.append(("info", f"每件檢體平均 TAT {vs['總計']:.1f} 小時中，真正在處理（人員作業加設備處理）"
                        f"只佔 {vs['增值比例']:.0%}；排隊等待 {vs['排隊等待']:.1f} 小時、"
                        f"批次等待 {vs['批次等待']:.1f} 小時。縮短 TAT 的空間主要在等待時間。"))

    # 4. 達標
    pt = s.kpi["per_type"]
    worst = pt.sort_values("達標率").iloc[0]
    level = "good" if worst["達標率"] >= 0.9 else ("warning" if worst["達標率"] >= 0.7 else "critical")
    out.append((level, f"達標率最低的是「{worst['檢體類型']}」：{worst['達標率']:.0%} 在 "
                       f"{worst['目標小時']:.0f} 小時內發報告（P90 為 {worst['P90_TAT']:.0f} 小時）。"))

    # 5. 系統是否穩定
    if s.kpi["未完成件數"] > 0:
        out.append(("critical", f"統計期的檢體在收尾期結束時仍有平均 {s.kpi['未完成件數']:.0f} 件沒做完，"
                                f"代表產能跟不上到件量，排隊會越來越長。"))

    # 6. Little's Law 檢查
    lt = s.little
    gap = abs(lt["實測WIP"] - lt["預測WIP"]) / max(lt["預測WIP"], 1e-9)
    out.append(("good" if gap < 0.1 else "warning",
                f"Little's Law 檢查：到件率 {lt['到件率_件每小時']:.1f} 件/小時 × 平均 TAT "
                f"{lt['平均TAT_小時']:.1f} 小時 = 預測在製品 {lt['預測WIP']:.0f} 件，模擬實測 "
                f"{lt['實測WIP']:.0f} 件（差 {gap:.0%}）。"))

    # 7. 成長
    if growth is not None and len(growth):
        g0 = growth.iloc[0]
        yrs = g0["超過警戒年"]
        if yrs <= cfg.g("growth_years"):
            out.append(("warning", f"依年成長率 {cfg.g('growth_rate'):.0%}，「{g0['資源']}」約在第 "
                                   f"{yrs:.1f} 年負荷超過 {warn:.0%}，需要提前規劃增加產能。"))
        else:
            out.append(("good", f"依年成長率 {cfg.g('growth_rate'):.0%}，未來 {cfg.g('growth_years'):.0f} "
                                f"年內沒有資源負荷超過 {warn:.0%}（最先到的是「{g0['資源']}」，約第 {yrs:.1f} 年）。"))
    return out
