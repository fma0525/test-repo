"""儀表板圖表（plotly）。

配色依 dataviz 參考色票：
- 類別色固定順序，不循環
- 數量用單一藍色由淺到深
- 狀態色（瓶頸警示）只在代表好壞時使用，並搭配文字標籤
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from .model import CATEGORIES

SERIES = ["#257de0", "#f47230", "#00b894", "#f2a600", "#ee7fac", "#008a17", "#6a4ce2", "#ec4647"]
SEQ_BLUE = ["#cce3fd", "#9dc8f7", "#6aabf1", "#338ced", "#2370cd", "#1757ac", "#0e3d7e"]
STATUS = {"good": "#0aac23", "warning": "#fbb315", "serious": "#f18a59", "critical": "#dc3c3d"}
INK_2 = "#666666"
GRID = "#e7e7e7"
AXIS = "#c2c2c2"
FONT = 'system-ui, -apple-system, "Segoe UI", "Noto Sans TC", "PingFang TC", "Microsoft JhengHei", sans-serif'

# 價值流類別顏色（固定對應，不隨篩選改變）
CAT_COLORS = dict(zip(CATEGORIES, SERIES[:len(CATEGORIES)]))


def _base(fig: go.Figure, height: int = 360, legend: bool = True) -> go.Figure:
    fig.update_layout(
        height=height, margin=dict(l=8, r=16, t=16, b=8),
        font=dict(family=FONT, size=13),
        hoverlabel=dict(font=dict(family=FONT)),
        showlegend=legend,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
                    title_text=""),
        bargap=0.35,
    )
    fig.update_xaxes(gridcolor=GRID, linecolor=AXIS, zeroline=False, tickfont=dict(color=INK_2))
    fig.update_yaxes(gridcolor=GRID, linecolor=AXIS, zeroline=False, tickfont=dict(color=INK_2))
    return fig


def utilization_bars(res: pd.DataFrame, warn: float) -> go.Figure:
    """資源使用率（橫條）。超過警戒值的條用狀態色並加上「⚠ 瓶頸」文字。"""
    df = res.sort_values("使用率")
    colors = [STATUS["critical"] if u >= warn else (STATUS["serious"] if u >= warn - 0.1 else SERIES[0])
              for u in df["使用率"]]
    labels = [f"{u:.0%}  ⚠ 瓶頸" if u >= warn else (f"{u:.0%}  接近警戒" if u >= warn - 0.1 else f"{u:.0%}")
              for u in df["使用率"]]
    ylab = [f"{r}（{k}）" for r, k in zip(df["資源"], df["類型"])]
    fig = go.Figure(go.Bar(
        x=df["使用率"], y=ylab, orientation="h", marker=dict(color=colors, cornerradius=4),
        text=labels, textposition="outside", cliponaxis=False,
        customdata=np.stack([df["每週忙碌小時"], df["每週可用小時"], df["尖峰使用率"]], axis=1),
        hovertemplate="%{y}<br>使用率 %{x:.1%}<br>每週忙碌 %{customdata[0]:.0f} 小時 / "
                      "可用 %{customdata[1]:.0f} 小時<br>尖峰時段使用率 %{customdata[2]:.0%}<extra></extra>",
    ))
    fig.add_vline(x=warn, line=dict(color=INK_2, dash="dash", width=1))
    fig.add_annotation(x=warn, y=1.02, yref="paper", text=f"警戒 {warn:.0%}", showarrow=False,
                       font=dict(color=INK_2, size=12), xanchor="left")
    fig.update_xaxes(tickformat=".0%", range=[0, max(1.05, df["使用率"].max() * 1.25)])
    return _base(fig, height=max(320, 34 * len(df) + 60), legend=False)


def stage_wait_bars(stages: pd.DataFrame) -> go.Figure:
    df = stages[stages["平均等待小時"] > 0.01].sort_values("平均等待小時")
    fig = go.Figure(go.Bar(
        x=df["平均等待小時"], y=df["階段"], orientation="h",
        marker=dict(color=SERIES[0], cornerradius=4),
        text=[f"{h:.1f} 小時（{p:.0%}）" for h, p in zip(df["平均等待小時"], df["佔TAT比例"])],
        textposition="outside", cliponaxis=False,
        hovertemplate="%{y}<br>平均每件等待 %{x:.2f} 小時<extra></extra>",
    ))
    fig.update_xaxes(title_text="平均每件等待（小時，含排隊與批次等待）",
                     range=[0, df["平均等待小時"].max() * 1.35 if len(df) else 1])
    return _base(fig, height=max(280, 34 * len(df) + 60), legend=False)


def value_stream_bars(vs: pd.DataFrame) -> go.Figure:
    """各檢體類型的時間組成（堆疊橫條）。"""
    df = vs.iloc[::-1]
    fig = go.Figure()
    for cat in CATEGORIES:
        fig.add_trace(go.Bar(
            x=df[cat], y=df["檢體類型"], orientation="h", name=cat,
            marker=dict(color=CAT_COLORS[cat], line=dict(color="rgba(255,255,255,1)", width=2)),
            hovertemplate=f"%{{y}}<br>{cat} %{{x:.1f}} 小時<extra></extra>",
        ))
    for _, r in df.iterrows():
        fig.add_annotation(x=r["總計"], y=r["檢體類型"], text=f"  {r['總計']:.0f} 小時",
                           showarrow=False, xanchor="left", font=dict(color=INK_2, size=12))
    fig.update_layout(barmode="stack", legend_traceorder="normal")
    fig.update_xaxes(title_text="平均每件時間（小時）", range=[0, df["總計"].max() * 1.15])
    return _base(fig, height=300)


def tat_ecdf(cases: pd.DataFrame, types: list[tuple[str, str, float]]) -> go.Figure:
    """累積完成比例：X 小時內完成的比例。types = [(code, name, target_h)]"""
    fig = go.Figure()
    done = cases.dropna(subset=["tat_h"])
    for i, (code, name, target) in enumerate(types):
        x = np.sort(done.loc[done["type"] == code, "tat_h"].values)
        if not len(x):
            continue
        y = np.arange(1, len(x) + 1) / len(x)
        color = SERIES[i]
        fig.add_trace(go.Scatter(x=x, y=y, mode="lines", name=name, line=dict(color=color, width=2),
                                 hovertemplate=f"{name}<br>%{{x:.0f}} 小時內完成 %{{y:.0%}}<extra></extra>"))
        met = (x <= target).mean()
        fig.add_trace(go.Scatter(x=[target], y=[met], mode="markers", showlegend=False,
                                 marker=dict(color=color, size=9, line=dict(color="white", width=2)),
                                 hovertemplate=f"{name} 目標 {target:.0f} 小時<br>達標 {met:.0%}<extra></extra>"))
    fig.update_xaxes(title_text="收件到發報告（小時）")
    fig.update_yaxes(title_text="已完成比例", tickformat=".0%", range=[0, 1.02])
    fig.update_layout(hovermode="closest")
    return _base(fig, height=380)


def hourly_heatmap(hourly: pd.DataFrame, order: list[str]) -> go.Figure:
    """資源 × 時刻（平日平均）使用率熱圖；沒排班的時段留白。"""
    piv = hourly.pivot(index="資源", columns="時", values="使用率").reindex(order[::-1])
    on = hourly.pivot(index="資源", columns="時", values="平均在班").reindex(order[::-1])
    scale = [[i / (len(SEQ_BLUE) - 1), c] for i, c in enumerate(SEQ_BLUE)]
    fig = go.Figure(go.Heatmap(
        z=piv.values, x=[f"{h:02d}" for h in piv.columns], y=piv.index, zmin=0, zmax=1,
        colorscale=scale, xgap=2, ygap=2, customdata=on.values,
        colorbar=dict(title="使用率", tickformat=".0%", thickness=12),
        hovertemplate="%{y}　%{x}:00<br>使用率 %{z:.0%}<br>平均在班 %{customdata:.1f}<extra></extra>",
        hoverongaps=False,
    ))
    fig.update_xaxes(title_text="平日時刻（空白＝沒有排班）", showgrid=False)
    fig.update_yaxes(showgrid=False)
    return _base(fig, height=max(320, 30 * len(piv) + 80), legend=False)


def wip_week(wip: pd.DataFrame) -> go.Figure:
    """一週的在製品輪廓（各階段組）。"""
    days = ["一", "二", "三", "四", "五", "六", "日"]
    x = np.arange(168)
    fig = go.Figure()
    groups = [c for c in wip.columns if c != "全系統"]
    for i, g in enumerate(groups):
        fig.add_trace(go.Scatter(x=x, y=wip[g], mode="lines", name=g,
                                 line=dict(color=SERIES[i], width=2),
                                 hovertemplate=f"{g}<br>%{{y:.0f}} 件<extra></extra>"))
    fig.update_xaxes(tickvals=list(range(0, 168, 24)), ticktext=[f"週{d}" for d in days],
                     title_text="一週時間（統計期平均）", range=[0, 167])
    fig.update_yaxes(title_text="在製品（件）", rangemode="tozero")
    fig.update_layout(hovermode="x unified")
    return _base(fig, height=380)


def growth_load_heatmap(gs: pd.DataFrame, years: int, warn: float) -> go.Figure:
    cols = [f"第{y}年" for y in range(years + 1)]
    df = gs.set_index("資源")[cols].iloc[::-1]
    text = np.vectorize(lambda v: f"{v:.0%}{' ⚠' if v >= warn else ''}")(df.values)
    scale = [[i / (len(SEQ_BLUE) - 1), c] for i, c in enumerate(SEQ_BLUE)]
    fig = go.Figure(go.Heatmap(
        z=df.values, x=cols, y=df.index, zmin=0, zmax=max(1.0, float(df.values.max())),
        colorscale=scale, xgap=2, ygap=2, text=text, texttemplate="%{text}",
        colorbar=dict(title="負荷率", tickformat=".0%", thickness=12),
        hovertemplate="%{y}　%{x}<br>負荷率 %{z:.0%}<extra></extra>",
    ))
    fig.update_xaxes(showgrid=False, side="top")
    fig.update_yaxes(showgrid=False)
    return _base(fig, height=max(320, 32 * len(df) + 80), legend=False)


def single_line(df: pd.DataFrame, x: str, y: str, ytitle: str, fmt: str = ".1f",
                target: float | None = None, target_label: str = "") -> go.Figure:
    fig = go.Figure(go.Scatter(
        x=df[x], y=df[y], mode="lines+markers", line=dict(color=SERIES[0], width=2),
        marker=dict(size=8, color=SERIES[0], line=dict(color="white", width=2)),
        hovertemplate=f"第 %{{x}} 年<br>{ytitle} %{{y:{fmt}}}<extra></extra>",
    ))
    if target is not None:
        fig.add_hline(y=target, line=dict(color=INK_2, dash="dash", width=1))
        fig.add_annotation(x=df[x].iloc[0], y=target, text=target_label, showarrow=False,
                           yanchor="bottom", xanchor="left", font=dict(color=INK_2, size=12))
    fig.update_xaxes(title_text="年", dtick=1)
    fig.update_yaxes(title_text=ytitle, rangemode="tozero",
                     tickformat=".0%" if fmt.endswith("%") else None)
    return _base(fig, height=300, legend=False)


def staffing_bars(df: pd.DataFrame) -> go.Figure:
    d = df.iloc[::-1]
    base = df.iloc[0]["平均TAT"]
    colors = [AXIS if s == "現況" else SERIES[0] for s in d["情境"]]
    fig = go.Figure(go.Bar(
        x=d["平均TAT"], y=d["情境"], orientation="h",
        marker=dict(color=colors, cornerradius=4),
        error_x=dict(type="data", array=d["CI半寬"], color=INK_2, thickness=1.2, width=4),
        hovertemplate="%{y}<br>平均 TAT %{x:.1f} 小時<extra></extra>",
    ))
    for _, r in d.iterrows():
        label = "基準" if r["情境"] == "現況" else f"{r['TAT變化']:+.1f} 小時"
        fig.add_annotation(x=r["平均TAT"] + r["CI半寬"], y=r["情境"], text=label, showarrow=False,
                           xanchor="left", xshift=8, font=dict(color=INK_2, size=12))
    fig.add_vline(x=base, line=dict(color=INK_2, dash="dash", width=1))
    lo = max(0, (d["平均TAT"] - d["CI半寬"]).min() * 0.9)
    fig.update_xaxes(title_text="平均 TAT（小時，誤差線為 95% 信賴區間）",
                     range=[lo, (d["平均TAT"] + d["CI半寬"]).max() * 1.12])
    return _base(fig, height=max(300, 36 * len(d) + 60), legend=False)
