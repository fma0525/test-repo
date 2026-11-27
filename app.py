"""病理中心作業模擬儀表板。

啟動：streamlit run app.py
"""

from __future__ import annotations

import copy

import pandas as pd
import streamlit as st

from pathlab_sim import analysis as A
from pathlab_sim import charts as C
from pathlab_sim.config import (SHEET_ARRIVAL, SHEET_GENERAL, SHEET_ORDER, SHEET_PROCESSOR,
                                SHEET_SHIFTS, SHEET_TASKS, SHEET_TYPES, STAFF, build_config,
                                default_sheets, excel_bytes, read_excel)

st.set_page_config(page_title="病理中心作業模擬", page_icon="🔬", layout="wide")

st.markdown("""
<style>
  .block-container {padding-top: 1.6rem; max-width: 1400px;}
  [data-testid="stMetricValue"] {font-size: 1.7rem;}
  [data-testid="stMetricLabel"] p {font-size: 0.85rem;}
  .finding {border-radius: 8px; padding: 10px 14px; margin-bottom: 8px; line-height: 1.6;
            border: 1px solid rgba(128,128,128,0.25); border-left-width: 5px;}
  .finding.critical {border-left-color: #dc3c3d;}
  .finding.warning  {border-left-color: #fbb315;}
  .finding.good     {border-left-color: #0aac23;}
  .finding.info     {border-left-color: #257de0;}
  .finding b {margin-right: 6px;}
  .sub {color: rgba(128,128,128,1); font-size: 0.9rem; margin-top: -0.4rem;}
</style>
""", unsafe_allow_html=True)

LEVEL_LABEL = {"critical": "🔴 嚴重", "warning": "🟠 注意", "good": "🟢 良好", "info": "🔵 說明"}
def num(fmt):
    """數字格式；空值顯示為 —（Streamlit 不一定吃 na_rep）。"""
    return lambda v: "—" if v is None or pd.isna(v) else fmt.format(v)


def text_table(df: pd.DataFrame, fmts: dict) -> pd.DataFrame:
    """把數字欄位轉成文字（空值顯示 —），避免表格把 NaN 顯示成 None。"""
    out = df.copy()
    for c, f in fmts.items():
        if c in out:
            out[c] = out[c].map(num(f))
    return out


GEN_KEYS = ["daily_cases", "digital", "replications", "growth_rate", "growth_years", "util_warn"]

# ---------------------------------------------------------------------------
# 狀態
# ---------------------------------------------------------------------------
ss = st.session_state
if "sheets" not in ss:
    ss.sheets = default_sheets()
    ss.source = "預設假設值"
    ss.summary = None
    ss.growth_sim = None
    ss.staffing = None
    ss.run_id = 0


def general_value(sheets, key):
    df = sheets[SHEET_GENERAL]
    return float(df.loc[df["代碼"] == key, "數值"].iloc[0])


def set_general(sheets, key, value):
    df = sheets[SHEET_GENERAL]
    df.loc[df["代碼"] == key, "數值"] = value


def current_config():
    try:
        return build_config(copy.deepcopy(ss.sheets)), None
    except Exception as e:  # 參數錯誤要顯示給使用者
        return None, str(e)


def invalidate():
    ss.summary = None
    ss.growth_sim = None
    ss.staffing = None


# ---------------------------------------------------------------------------
# 側邊欄
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("🔬 病理中心作業模擬")
    st.caption(f"參數來源：{ss.source}")

    up = st.file_uploader("上傳參數 Excel", type=["xlsx"],
                          help="格式同「下載目前參數」的檔案")
    if up is not None and ss.get("uploaded_name") != up.name + str(up.size):
        try:
            ss.sheets = read_excel(up)
            ss.source = f"上傳檔案：{up.name}"
            ss.uploaded_name = up.name + str(up.size)
            invalidate()
            st.success("已載入")
        except Exception as e:
            st.error(f"讀取失敗：{e}")

    c1, c2 = st.columns(2)
    c1.download_button("下載目前參數", excel_bytes(ss.sheets), "病理中心模擬參數.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                       use_container_width=True)
    if c2.button("還原預設", use_container_width=True):
        ss.sheets = default_sheets()
        ss.source = "預設假設值"
        invalidate()
        st.rerun()

    st.divider()
    st.subheader("快速調整")
    daily = st.slider("平日每日檢體數（件）", 20, 600, int(general_value(ss.sheets, "daily_cases")), 5)
    digital = st.toggle("數位掃描流程", value=general_value(ss.sheets, "digital") >= 0.5)
    growth = st.slider("年成長率", 0.0, 0.30, float(general_value(ss.sheets, "growth_rate")), 0.01,
                       format="%.2f")
    years = st.slider("規劃年數", 1, 15, int(general_value(ss.sheets, "growth_years")))
    reps = st.slider("每個情境重複次數", 1, 20, int(general_value(ss.sheets, "replications")),
                     help="次數越多結果越穩定，但越久")
    warn = st.slider("瓶頸警戒使用率", 0.5, 1.0, float(general_value(ss.sheets, "util_warn")), 0.05)
    new_vals = {"daily_cases": daily, "digital": 1 if digital else 0, "growth_rate": growth,
                "growth_years": years, "replications": reps, "util_warn": warn}
    if any(abs(general_value(ss.sheets, k) - float(v)) > 1e-9 for k, v in new_vals.items()):
        for k, v in new_vals.items():
            set_general(ss.sheets, k, v)
        invalidate()

    st.divider()
    run = st.button("▶ 執行模擬", type="primary", use_container_width=True)

cfg, cfg_err = current_config()
if cfg_err:
    st.error(cfg_err)
    st.stop()

if run:
    bar = st.progress(0.0, text="模擬中…")
    results = A.run_many(A.replications(cfg),
                         progress=lambda i, n: bar.progress(i / n, text=f"模擬中…（{i}/{n}）"))
    ss.summary = A.summarize(cfg, results)
    ss.run_id += 1
    bar.empty()

ew = A.expected_work(cfg)
cap = A.static_capacity(cfg, ew=ew)
gs = A.growth_static(cfg, ew=ew)

# ---------------------------------------------------------------------------
# 頁面
# ---------------------------------------------------------------------------
st.title("病理中心作業模擬")
st.markdown(f'<p class="sub">平日每日 {cfg.g("daily_cases"):.0f} 件 · '
            f'{"數位掃描" if cfg.g("digital") >= 0.5 else "玻片直送"} · '
            f'每個情境重複 {cfg.g("replications"):.0f} 次 · 所有參數目前為假設值</p>',
            unsafe_allow_html=True)

tabs = st.tabs(["總覽", "瓶頸與產能", "時段負荷", "價值流", "成長規劃", "增員實驗", "參數設定", "說明"],
               key="main_tabs", on_change="rerun")
s = ss.summary

# ---- 總覽 -------------------------------------------------------------------
with tabs[0]:
    if s is None:
        st.info("左側調整參數後按「▶ 執行模擬」。下面先顯示不需模擬的靜態產能估算。")
        st.dataframe(text_table(cap[["資源", "類型", "負荷率", "每件工作含量_分", "節拍時間_分"]], {"負荷率": "{:.0%}", "每件工作含量_分": "{:.1f}",
                                    "節拍時間_分": "{:.1f}"}),
                     hide_index=True, use_container_width=True, height="content")
    else:
        k = s.kpi
        m = st.columns(6)
        m[0].metric("每週件數", f"{k['每週件數']:.0f}")
        m[1].metric("平均 TAT", f"{k['平均TAT']:.1f} 小時")
        m[2].metric("P90 TAT", f"{k['P90_TAT']:.1f} 小時", help="90% 的檢體在這個時間內發報告")
        m[3].metric("整體達標率", f"{k['達標率']:.0%}", help="依各檢體類型的 TAT 目標")
        m[4].metric("實驗室 TAT", f"{k['實驗室TAT']:.1f} 小時", help="收件到玻片（或影像）可判讀")
        m[5].metric(f"最忙人力 {k['最忙人力使用率']:.0%}", k["最忙人力"],
                    help="使用率最高的人力資源，括號內為使用率")

        st.subheader("重點發現")
        for level, text in A.findings(cfg, s, cap, gs):
            st.markdown(f'<div class="finding {level}"><b>{LEVEL_LABEL[level]}</b>{text}</div>',
                        unsafe_allow_html=True)

        left, right = st.columns([3, 2])
        with left:
            st.subheader("TAT 達標曲線")
            st.caption("每條線表示「多少小時內完成了多少比例」；圓點是各類型的 TAT 目標"
                       "（滑過可看達標率）。曲線呈階梯狀，是因為檢體大多在固定的班別與脫水批次完成。")
            st.plotly_chart(C.tat_ecdf(s.cases, [(t.code, t.name, t.tat_target_h) for t in cfg.types]),
                            use_container_width=True, key=f"ecdf{ss.run_id}")
        with right:
            st.subheader("各檢體類型")
            st.dataframe(k["per_type"].style.format({"平均TAT": "{:.1f}", "P90_TAT": "{:.1f}",
                                                     "達標率": "{:.0%}", "目標小時": "{:.0f}",
                                                     "件數": "{:.0f}"}),
                         hide_index=True, use_container_width=True, height="content")
            st.caption("件數為統計期內每次模擬的平均件數。")

# ---- 瓶頸與產能 -------------------------------------------------------------
with tabs[1]:
    if s is None:
        st.info("請先執行模擬。")
    else:
        left, right = st.columns(2)
        with left:
            st.subheader("資源使用率")
            st.caption("使用率 = 忙碌時間 ÷ 排班（或運轉）時間。人力只算有排班的時段；設備依其可用時段。")
            st.plotly_chart(C.utilization_bars(s.resources, cfg.g("util_warn")),
                            use_container_width=True, key=f"util{ss.run_id}")
        with right:
            st.subheader("各階段平均等待時間")
            st.caption("等待包含排隊等人力或設備，以及等脫水機、染色機開機。括號是佔整體 TAT 的比例。")
            st.plotly_chart(C.stage_wait_bars(s.stages), use_container_width=True,
                            key=f"wait{ss.run_id}")
        st.subheader("資源明細")
        st.dataframe(s.resources.drop(columns=["瓶頸"]).style.format(
            {"每週可用小時": "{:.0f}", "每週忙碌小時": "{:.0f}", "使用率": "{:.0%}",
             "尖峰使用率": num("{:.0%}"), "平均排隊小時": num("{:.2f}")}),
            hide_index=True, use_container_width=True, height="content")
    st.subheader("靜態產能分析（節拍時間與負荷率）")
    st.caption("不跑模擬，用平均值估算。節拍時間 = 每週可用時間 ÷ 每週件數，也就是每件最多能分到的時間；"
               "工作含量 = 每件平均需要的時間。負荷率 = 工作含量 ÷ 節拍時間，超過 100% 代表一定做不完。")
    st.dataframe(text_table(cap, {"每件工作含量_分": "{:.1f}", "節拍時間_分": "{:.1f}",
                                   "每週需求小時": "{:.0f}", "每週可用小時": "{:.0f}",
                                   "負荷率": "{:.0%}", "平日最多在班": "{:.0f}",
                                   "每週蠟塊": "{:.0f}", "每週容量蠟塊": "{:.0f}"}),
                 hide_index=True, use_container_width=True, height="content")

# ---- 時段負荷 ---------------------------------------------------------------
with tabs[2]:
    if s is None:
        st.info("請先執行模擬。")
    else:
        st.subheader("平日每小時使用率")
        st.caption("看班表和工作量有沒有對上：顏色深代表那個時段很忙；整列都淺但等待很久，"
                   "通常是工作在沒人上班的時段到達（時段錯配）。")
        order = s.resources["資源"].tolist()
        st.plotly_chart(C.hourly_heatmap(s.hourly, order), use_container_width=True,
                        key=f"heat{ss.run_id}")
        st.subheader("一週在製品（WIP）")
        st.caption("各階段平均有幾件檢體正在等待或處理。週末堆積、週一早上消化，是常見的型態。")
        st.plotly_chart(C.wip_week(s.wip_week), use_container_width=True, key=f"wip{ss.run_id}")
        lt = s.little
        st.markdown(f"**Little's Law**：平均在製品 = 到件率 × 平均 TAT → "
                    f"{lt['到件率_件每小時']:.2f} 件/小時 × {lt['平均TAT_小時']:.1f} 小時 = "
                    f"**{lt['預測WIP']:.0f} 件**；模擬實測 **{lt['實測WIP']:.0f} 件**。"
                    f"要降低 TAT，就要降低在製品。")

# ---- 價值流 -----------------------------------------------------------------
with tabs[3]:
    if s is None:
        st.info("請先執行模擬。")
    else:
        st.subheader("每件檢體的時間花在哪裡")
        st.caption("作業 = 人員實際處理；設備處理 = 脫水、染色、掃描；排隊等待 = 等人力或設備；"
                   "批次等待 = 等脫水機、染色機開機；必要等待 = 固定、外送特殊染色。")
        st.plotly_chart(C.value_stream_bars(s.value_stream), use_container_width=True,
                        key=f"vs{ss.run_id}")
        st.dataframe(s.value_stream.style.format({c: "{:.1f}" for c in s.value_stream.columns
                                                  if c not in ("檢體類型", "增值比例")}
                                                 | {"增值比例": "{:.0%}"}),
                     hide_index=True, use_container_width=True, height="content")
        st.subheader("脫水機批次")
        st.caption("滿載率低代表可以合併批次或減少開機；未上機件數 > 0 代表容量不夠或排程太少。")
        if len(s.processor):
            st.dataframe(s.processor.style.format({"每週次數": "{:.1f}", "平均裝載蠟塊": "{:.0f}",
                                                   "容量蠟塊": "{:.0f}", "平均件數": "{:.1f}",
                                                   "平均未上機件數": "{:.1f}", "滿載率": "{:.0%}"}),
                         hide_index=True, use_container_width=True, height="content")

# ---- 成長規劃 ---------------------------------------------------------------
with tabs[4]:
    yrs = int(cfg.g("growth_years"))
    st.subheader(f"各資源負荷率推估（年成長 {cfg.g('growth_rate'):.0%}）")
    st.caption("靜態估算：假設班表與設備不變，只有件數成長。⚠ 表示超過警戒值。")
    st.plotly_chart(C.growth_load_heatmap(gs, yrs, cfg.g("util_warn")), use_container_width=True,
                    key="growth_heat")
    show = gs[["資源", "類型", "目前負荷率", "超過警戒年", "期末需增加產能", "期末約需增加人或台"]]
    st.dataframe(text_table(show, {"目前負荷率": "{:.0%}", "超過警戒年": "{:.1f}",
                                    "期末需增加產能": "{:.0%}",
                                    "期末約需增加人或台": "{:.0f}"}),
                 hide_index=True, use_container_width=True, height="content")
    st.caption(f"「期末」指第 {yrs} 年。人或台數以平日尖峰在班數等比例估算，實際仍需搭配班表設計。")

    st.subheader("逐年模擬")
    n_jobs = (yrs + 1) * int(cfg.g("replications"))
    if st.button(f"▶ 跑成長情境（共 {n_jobs} 次模擬）"):
        bar = st.progress(0.0, text="模擬中…")
        ss.growth_sim = A.growth_simulation(
            cfg, progress=lambda i, n: bar.progress(i / n, text=f"模擬中…（{i}/{n}）"))
        bar.empty()
    if ss.growth_sim is not None:
        g = ss.growth_sim
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**P90 TAT（小時）**")
            st.plotly_chart(C.single_line(g, "年", "P90_TAT", "P90 TAT（小時）"),
                            use_container_width=True, key="g_p90")
        with c2:
            st.markdown("**最高人力使用率**")
            st.plotly_chart(C.single_line(g, "年", "最高人力使用率", "使用率", fmt=".0%",
                                          target=cfg.g("util_warn"),
                                          target_label=f"警戒 {cfg.g('util_warn'):.0%}"),
                            use_container_width=True, key="g_util")
        st.dataframe(g.style.format({"平日每日件數": "{:.0f}", "平均TAT": "{:.1f}", "P90_TAT": "{:.1f}",
                                     "達標率": "{:.0%}", "實驗室TAT": "{:.1f}", "未完成件數": "{:.0f}",
                                     "最高人力使用率": "{:.0%}"}),
                     hide_index=True, use_container_width=True, height="content")
        if (g["未完成件數"] > 0).any():
            y0 = int(g.loc[g["未完成件數"] > 0, "年"].iloc[0])
            st.error(f"第 {y0} 年起有檢體在收尾期內做不完，代表產能已跟不上，TAT 會持續惡化。")

# ---- 增員實驗 ---------------------------------------------------------------
with tabs[5]:
    st.subheader("多 1 位人力，加在哪裡最有效？")
    st.caption("每個情境只在一個人力資源多加 1 人（沿用該資源平日主要班別時段），比較平均 TAT。"
               "實驗設計參考劍橋大學 WSC 2024 論文的圖 5。誤差線不重疊才算有明顯差異。")
    n_staff = len(cfg.staff_resources()) + 1
    if st.button(f"▶ 跑增員實驗（共 {n_staff * int(cfg.g('replications'))} 次模擬）"):
        bar = st.progress(0.0, text="模擬中…")
        ss.staffing = A.staffing_experiment(
            cfg, progress=lambda i, n: bar.progress(i / n, text=f"模擬中…（{i}/{n}）"))
        bar.empty()
    if ss.staffing is not None:
        st.plotly_chart(C.staffing_bars(ss.staffing), use_container_width=True, key="staffing")
        st.dataframe(ss.staffing.style.format({"平均TAT": "{:.1f}", "CI半寬": "{:.1f}",
                                               "P90_TAT": "{:.1f}", "達標率": "{:.0%}",
                                               "實驗室TAT": "{:.1f}", "TAT變化": "{:+.1f}"}),
                     hide_index=True, use_container_width=True, height="content")

# ---- 參數設定 ---------------------------------------------------------------
with tabs[6]:
    st.subheader("參數設定")
    st.caption("直接在表格裡修改，按「套用」後重新執行模擬。也可以下載 Excel 修改後再上傳。"
               "「來源」欄請把「假設」改成實際資料出處（例如：2026 年 LIS 統計）。")
    help_text = {
        SHEET_GENERAL: "整體設定。快速調整的滑桿也會改到這裡。",
        SHEET_TYPES: "檢體分類。三個數字一組的欄位是三角分布（最少、最可能、最多）。固定時數從收件起算。",
        SHEET_TASKS: "各作業時間（分鐘）與使用的資源。「依檢體類型」的作業時間在「檢體類型」表設定。",
        SHEET_SHIFTS: "同一資源可以有多列（多個班別），在同一時段會相加。時間格式 HH:MM，空白表示當天不上班。"
                      "結束早於開始代表跨夜。設備請填運轉時段，例如 00:00–24:00。",
        SHEET_PROCESSOR: "脫水機開機排程。星期填「一二三四五」這種寫法；適用檢體代碼以逗號分隔。",
        SHEET_ARRIVAL: "每小時到件的相對權重，只看比例。",
    }
    edited = {}
    for name in SHEET_ORDER:
        with st.expander(name, expanded=(name == SHEET_GENERAL)):
            st.caption(help_text[name])
            edited[name] = st.data_editor(ss.sheets[name], key=f"ed_{name}", hide_index=True,
                                          use_container_width=True,
                                          num_rows="fixed" if name in (SHEET_GENERAL, SHEET_TASKS,
                                                                       SHEET_ARRIVAL) else "dynamic")
    if st.button("套用修改", type="primary"):
        trial = {k: v.copy() for k, v in edited.items()}
        try:
            build_config(copy.deepcopy(trial))
            ss.sheets = trial
            ss.source = ss.source if "（已修改）" in ss.source else ss.source + "（已修改）"
            invalidate()
            st.success("已套用，請重新執行模擬。")
            st.rerun()
        except Exception as e:
            st.error(str(e))

# ---- 說明 -------------------------------------------------------------------
with tabs[7]:
    st.markdown("""
### 這個工具在做什麼
用**離散事件模擬**把病理中心的每一件檢體從收件跑到發報告，考慮人力班表、設備數量、
脫水機和染色機的批次規則，以及急件優先。每個情境用不同亂數跑多次取平均。

**流程**：收件 → 固定（中大型檢體）→ 取材 → 脫水機（批次，依排程開機）→ 包埋 → 切片
→ 染色封片機（湊批）→ 品管配片 → 數位掃描（可關閉）→ 判讀 → 加做特殊染色與補判讀（部分檢體）

### 作業管理概念
| 概念 | 在這裡怎麼看 |
|---|---|
| **使用率與瓶頸** | 「瓶頸與產能」頁。使用率超過警戒值（預設 85%）就是瓶頸；排隊時間會隨使用率非線性暴增 |
| **限制理論（TOC）** | 整體產出由瓶頸決定，在非瓶頸加人沒有用。「增員實驗」頁可以直接驗證 |
| **節拍時間** | 每件檢體在某資源最多能分到的時間。工作含量超過節拍時間，就一定做不完 |
| **Little's Law** | 在製品 = 到件率 × TAT。要縮短 TAT，就要減少在製品 |
| **批次效應** | 脫水機、染色機要湊批，造成等待；「價值流」頁的批次等待就是這部分 |
| **時段錯配** | 工作到達的時段沒有人上班。使用率不高但等待很久，通常就是這個原因 |
| **價值流** | 真正在處理的時間通常只佔 TAT 的一小部分，改善空間在等待 |
| **成長規劃** | 依年成長率推估哪個資源哪一年先超過警戒，提前規劃增人或設備 |

### 目前的簡化與限制
- 所有數字都是**假設值**，請逐步用實際資料取代（「參數設定」的「來源」欄可記錄出處）。
- 人力下班時，進行中的工作會做完才離開（視同延後下班）。
- 站點之間的運送時間、送件人員還沒有模擬（第三階段接平面圖後加入）。
- 同一件檢體的所有蠟塊、玻片一起移動。
- 脫水機沒有「湊滿一台就提早開機」的規則，只依排程開機。
- 沒有區分次專科（例如不同醫師負責不同器官）。

### 參考
- Chan Y-C, et al. *A Process Simulation Model for a Histopathology Laboratory.* WSC 2024.
  摘要見 `docs/papers/`。
""")
