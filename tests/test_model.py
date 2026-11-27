"""模擬模型的基本檢查。"""

import math

import numpy as np
import pandas as pd
import pytest

from pathlab_sim import analysis as A
from pathlab_sim.config import (SHEET_GENERAL, SHEET_SHIFTS, build_config, default_sheets,
                                excel_bytes, load_default, read_excel)
from pathlab_sim.model import CATEGORIES, run_once


def small_cfg(**overrides):
    sheets = default_sheets()
    g = sheets[SHEET_GENERAL]
    vals = {"sim_weeks": 2, "warmup_weeks": 1, "drain_weeks": 2, "daily_cases": 60}
    vals.update(overrides)
    for k, v in vals.items():
        g.loc[g["代碼"] == k, "數值"] = v
    return build_config(sheets)


@pytest.fixture(scope="module")
def result():
    cfg = small_cfg()
    return cfg, run_once(cfg, seed=3)


def test_all_cases_complete_and_time_adds_up(result):
    cfg, r = result
    df = pd.DataFrame(r.cases)
    assert len(df) > 0
    assert df["done"].notna().all()
    tat = df["done"] - df["arrival"]
    parts = df[[f"cat_{c}" for c in CATEGORIES]].sum(axis=1)
    # 每件檢體的各類時間加總應等於 TAT（流程中沒有遺漏的時段）
    assert np.allclose(tat, parts, atol=1e-6)


def test_utilization_is_bounded(result):
    cfg, r = result
    for name, v in r.resources.items():
        if v["cap"].sum() > 0:
            u = v["busy"].sum() / v["cap"].sum()
            assert 0 <= u <= 1.05, name  # 允許下班時把手上工作做完的少量超出


def test_littles_law(result):
    cfg, r = result
    s = A.summarize(cfg, [r])
    lt = s.little
    assert abs(lt["實測WIP"] - lt["預測WIP"]) / lt["預測WIP"] < 0.15


def test_processor_never_overfilled(result):
    cfg, r = result
    for run in r.processor_runs:
        assert run["blocks"] <= run["capacity"]


def test_reproducible():
    cfg = small_cfg(sim_weeks=1, drain_weeks=1)
    a = pd.DataFrame(run_once(cfg, seed=11).cases)
    b = pd.DataFrame(run_once(cfg, seed=11).cases)
    pd.testing.assert_frame_equal(a, b)


def test_more_volume_means_higher_load():
    cfg = load_default()
    ew = A.expected_work(cfg, n=3000)
    lo = A.static_capacity(cfg, daily=100, ew=ew).set_index("資源")["負荷率"]
    hi = A.static_capacity(cfg, daily=200, ew=ew).set_index("資源")["負荷率"]
    assert (hi > lo).all()
    assert math.isclose(hi["切片技術員"] / lo["切片技術員"], 2.0, rel_tol=1e-6)


def test_static_matches_simulated_utilization(result):
    cfg, r = result
    s = A.summarize(cfg, [r])
    sim_u = s.resources.set_index("資源")["使用率"]["切片技術員"]
    stat_u = A.static_capacity(cfg).set_index("資源")["負荷率"]["切片技術員"]
    assert abs(sim_u - stat_u) < 0.1


def test_excel_roundtrip(tmp_path):
    p = tmp_path / "c.xlsx"
    p.write_bytes(excel_bytes(default_sheets()))
    cfg = build_config(read_excel(p))
    assert cfg.g("daily_cases") == 120
    assert cfg.weekly_capacity_minutes("切片技術員") == load_default().weekly_capacity_minutes("切片技術員")


def test_validation_catches_unknown_resource():
    sheets = default_sheets()
    sheets[SHEET_SHIFTS] = sheets[SHEET_SHIFTS][sheets[SHEET_SHIFTS]["資源"] != "切片機"]
    with pytest.raises(ValueError, match="切片機"):
        build_config(sheets)


def test_overnight_shift_wraps_midnight():
    sheets = default_sheets()
    df = sheets[SHEET_SHIFTS]
    df.loc[len(df)] = {"資源": "夜班", "類型": "人力", "數量": 1, "平日開始": "22:00",
                       "平日結束": "06:00", "週六開始": "", "週六結束": "", "週日開始": "",
                       "週日結束": "", "備註": "", "來源": "測試"}
    cfg = build_config(sheets)
    s = cfg.schedules["夜班"]
    assert s[0][44] == 1 and s[1][0] == 1 and s[1][11] == 1 and s[1][12] == 0
    assert cfg.weekly_capacity_minutes("夜班") == 5 * 8 * 60
