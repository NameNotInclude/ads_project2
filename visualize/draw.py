#!/usr/bin/env python3
"""
draw.py — 背包算法实验作图（polars 处理数据 + altair 绘图，输出 PDF）

运行环境（conda）:
    conda run -n visual python visualize/draw.py
    # 或
    ~/miniconda3/envs/visual/bin/python visualize/draw.py

数据来源: result/{base,dominance,bound}.csv
    列: file,num_of_item,capacity,iter,tot_time,aver_time   (单位 ms)

输出: visualize/figs/*.pdf
    fig1_base_vs_nc.pdf        DP-1 耗时 vs n·c（双对数 + 拟合斜率）
    fig2_same_n_diff_c.pdf     相同 n、不同 c 下三种算法对比（tier07 vs tier08, tier03 vs tier09）
    fig3_correlation.pdf       p/w 相关性（数据族）对耗时的影响
    fig4_speedup.pdf           两种改进算法相对 DP-1 的提升/减弱率（按 n、c）
"""

from pathlib import Path

import altair as alt
import polars as pl

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "result"
OUT = Path(__file__).resolve().parent / "figs"
OUT.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------- 常量
ALGO = {                                   # csv 名 -> 图例名
    "base": "DP-1 (base)",
    "dominance": "DP-with-Lists (3.4)",
    "bound": "DP+Upper-Bound (3.5)",
}
ALGO_ORDER = list(ALGO.values())
ALGO_COLOR = alt.Scale(
    domain=ALGO_ORDER,
    range=["#4C78A8", "#F58518", "#54A24B"],
)
FAMILY = {                                 # 文件名前缀 -> 图例名
    "a_uncorr": "uncorrelated",
    "b_weakcorr": "weakly correlated",
    "c_strong": "strongly correlated",
    "d_subsetsum": "subset sum (p=w)",
    "e_smallprofit": "small profit (Ep << c)",
}
FAMILY_ORDER = list(FAMILY.values())
COMMON_FAMILIES = ["a_uncorr", "b_weakcorr", "c_strong"]

TITLE_FONT = 15
LABEL_FONT = 12


# ---------------------------------------------------------------- 读数据
def load() -> pl.DataFrame:
    frames = []
    for key, label in ALGO.items():
        path = RES / f"{key}.csv"
        if not path.exists():
            print(f"[warn] 缺少 {path}")
            continue
        frames.append(
            pl.read_csv(path).with_columns(
                pl.lit(key).alias("algo"),
                pl.lit(label).alias("algo_label"),
            )
        )
    if not frames:
        raise SystemExit("result/*.csv 不存在，先跑 ./sh/compile_run.sh")

    df = pl.concat(frames)

    # 从路径里解析 tier / family
    pat = r"testdata/(?<tier>tier\d+)_n(?<n_dir>\d+)_c(?<c_dir>\d+)/(?<family>[a-z]+_[a-z]+)\.txt"
    df = df.with_columns(pl.col("file").str.extract_groups(pat)).unnest("file")

    df = df.with_columns(
        pl.col("family").replace_strict(FAMILY, default="other").alias("family_label"),
        (pl.col("num_of_item") * pl.col("capacity")).alias("nc"),
        # 归一化代价：每 10^6 个 DP 格子花多少 ms，便于跨规模比较
        (pl.col("aver_time") * 1e6 / (pl.col("num_of_item") * pl.col("capacity"))).alias("us_per_mcell"),
        (
            "n=" + pl.col("num_of_item").cast(pl.Utf8)
            + ", c=" + pl.col("capacity").cast(pl.Utf8)
        ).alias("size_label"),
    )
    return df


# ---------------------------------------------------------------- 工具
def loglog_fit(d: pl.DataFrame, xcol: str, ycol: str) -> tuple[float, float, pl.DataFrame]:
    """对 log10(y) ~ log10(x) 做最小二乘，返回 (斜率, 截距, 拟合线数据)"""
    dd = d.with_columns(pl.col(xcol).log10().alias("lx"), pl.col(ycol).log10().alias("ly"))
    mx, my = dd["lx"].mean(), dd["ly"].mean()
    slope = ((dd["lx"] - mx) * (dd["ly"] - my)).sum() / ((dd["lx"] - mx) ** 2).sum()
    intercept = my - slope * mx

    x0, x1 = dd[xcol].min(), dd[xcol].max()
    line = pl.DataFrame({"nc": [x0, x1]}).with_columns(
        pl.col("nc").cast(pl.Float64),
        (10 ** (intercept + slope * pl.col("nc").cast(pl.Float64).log10())).alias("ms"),
    )
    return slope, intercept, line


def with_title(ch: alt.Chart, title: str, subtitle: str = "") -> alt.Chart:
    """给（可能是 layered / faceted 的）图加总标题"""
    return ch.properties(
        title=alt.TitleParams(text=title, subtitle=subtitle, fontSize=TITLE_FONT, anchor="start")
    )


def style(ch: alt.Chart) -> alt.Chart:
    return ch.configure_axis(labelFontSize=LABEL_FONT, titleFontSize=LABEL_FONT).configure_legend(
        labelFontSize=LABEL_FONT, titleFontSize=LABEL_FONT
    )


def style_config(ch):
    """统一的字体大小设置（只能在最顶层加一次 config）"""
    return ch.configure_axis(labelFontSize=LABEL_FONT, titleFontSize=LABEL_FONT).configure_legend(
        labelFontSize=LABEL_FONT, titleFontSize=LABEL_FONT
    )


def save_pdf(ch: alt.Chart, name: str) -> None:
    path = OUT / f"{name}.pdf"
    style_config(ch).save(path)
    print(f"  -> {path.relative_to(ROOT)}")


def save_html(charts: list[alt.Chart], subtitle: str, name: str = "figs") -> None:
    """把四张图拼成一页交互式 HTML（悬停显示数值），JS 内联，可离线打开"""
    page = alt.vconcat(*charts, spacing=30).properties(
        title=alt.TitleParams(
            text="Knapsack experiment — interactive figures",
            subtitle=[
                "hover any mark to see the exact numbers; drag to pan, scroll to zoom",
                subtitle,
            ],
            fontSize=TITLE_FONT + 3,
            subtitleFontSize=LABEL_FONT,
            anchor="start",
        )
    )
    page = style_config(page)
    path = OUT / f"{name}.html"
    page.save(path, inline=True)
    size_mb = path.stat().st_size / 1e6
    print(f"  -> {path.relative_to(ROOT)}   ({size_mb:.1f} MB, tooltip 可交互)")


# ---------------------------------------------------------------- 图 1
def fig1_base_vs_nc(df: pl.DataFrame) -> None:
    """DP-1 的耗时与 n·c 的关系：若是 Θ(nc)，双对数上斜率应 ≈ 1"""
    d = (
        df.filter(pl.col("algo") == "base")
        .group_by(["num_of_item", "capacity", "nc"])
        .agg(pl.col("aver_time").median().alias("ms"))
        .sort("nc")
    )
    slope, _, line = loglog_fit(d, "nc", "ms")

    points = (
        alt.Chart(d)
        .mark_circle(size=110, opacity=0.85, color="#4C78A8")
        .encode(
            x=alt.X("nc:Q", scale=alt.Scale(type="log"), title="n · c  (number of DP cells)"),
            y=alt.Y("ms:Q", scale=alt.Scale(type="log"), title="time (ms, median)"),
            tooltip=[
                alt.Tooltip("num_of_item:Q", title="n"),
                alt.Tooltip("capacity:Q", title="c"),
                alt.Tooltip("nc:Q", title="n·c"),
                alt.Tooltip("ms:Q", title="ms", format=".3f"),
            ],
        )
    )
    fit = (
        alt.Chart(line)
        .mark_line(strokeDash=[6, 3], color="#E45756", strokeWidth=2)
        .encode(x="nc:Q", y="ms:Q")
    )
    note = (
        alt.Chart(pl.DataFrame({"nc": [d["nc"].min()], "ms": [d["ms"].max()]}))
        .mark_text(align="left", dx=6, dy=-8, fontSize=LABEL_FONT + 1, color="#E45756")
        .encode(x="nc:Q", y="ms:Q", text=alt.value(f"log-log fit slope = {slope:.2f}"))
    )

    ch = (points + fit + note).properties(width=560, height=380)
    return with_title(
        ch,
        "Fig.1  DP-1 runtime vs. n·c",
        f"median over 3 data families; fitted slope {slope:.2f} (≈1 means Θ(nc))",
    )


# ---------------------------------------------------------------- 图 2
def fig2_same_n_diff_c(df: pl.DataFrame) -> None:
    """固定 n，比较不同 c：tier08(c=2k) vs tier07(c=50k)，以及 tier03 vs tier09"""
    tiers = ["tier07", "tier08", "tier03", "tier09"]

    d = (
        df.filter(
            pl.col("tier").is_in(tiers)
            & pl.col("family").is_in(COMMON_FAMILIES)      # 只用三族共有的数据，保证可比
        )
        .group_by(["num_of_item", "capacity", "algo", "algo_label"])
        .agg(pl.col("aver_time").median().alias("ms"))
        .with_columns(
            ("n = " + pl.col("num_of_item").cast(pl.Utf8)).alias("panel")
        )
    )

    # 对数 y 轴不能用 mark_bar（柱子从 0 起，log(0) 无法绘制），改折线+点
    lines = (
        alt.Chart(d)
        .mark_line(point=alt.OverlayMarkDef(size=90, filled=True), strokeWidth=2)
        .encode(
            x=alt.X("capacity:Q", scale=alt.Scale(type="log", domain=[1500, 260000]),
                    title="capacity c (log scale)"),
            y=alt.Y("ms:Q", scale=alt.Scale(type="log"), title="time (ms, median, log scale)"),
            color=alt.Color("algo_label:N", scale=ALGO_COLOR, sort=ALGO_ORDER, title=None),
            tooltip=[
                alt.Tooltip("panel:N", title="size"),
                alt.Tooltip("capacity:Q", title="c"),
                alt.Tooltip("algo_label:N", title="algorithm"),
                alt.Tooltip("ms:Q", title="ms", format=".3f"),
            ],
        )
    )
    ch = lines.properties(width=300, height=330).facet(
        column=alt.Column("panel:N", title=None, sort=["n = 100", "n = 2000"])
    ).resolve_scale(y="shared")

    return with_title(
        ch,
        "Fig.2  Same n, different c: three algorithms",
        "left: n=100 (c=2000 vs c=200000); right: n=2000 (c=2000 vs c=50000); median over 3 data families",
    )


# ---------------------------------------------------------------- 图 3
def fig3_correlation(df: pl.DataFrame) -> None:
    """p/w 相关性对耗时的影响"""
    # (a) 归一化代价（每 1e6 个 DP 格子）：跨规模可比，只看数据族的效应
    d_cost = (
        df.filter(pl.col("family").is_in(COMMON_FAMILIES))
        .group_by(["family_label", "algo_label"])
        .agg(pl.col("us_per_mcell").median().alias("us_per_mcell"))
    )
    cost_bars = (
        alt.Chart(d_cost)
        .mark_bar()
        .encode(
            x=alt.X("family_label:N", title="p/w correlation family", sort=FAMILY_ORDER),
            y=alt.Y("us_per_mcell:Q", title="time per 10^6 DP cells (ms, median)"),
            color=alt.Color("algo_label:N", scale=ALGO_COLOR, sort=ALGO_ORDER, title=None),
            xOffset=alt.XOffset("algo_label:N", sort=ALGO_ORDER),
            tooltip=[
                alt.Tooltip("family_label:N", title="family"),
                alt.Tooltip("algo_label:N", title="algorithm"),
                alt.Tooltip("us_per_mcell:Q", title="ms / 1e6 cells", format=".1f"),
            ],
        )
    ).properties(width=520, height=320, title=alt.TitleParams(
        text="(a) normalized cost across sizes (DP-1 is data independent)",
        fontSize=LABEL_FONT + 1, anchor="start"))

    # (b) tier09（5 个族都有）的绝对耗时
    d_abs = (
        df.filter(pl.col("tier") == "tier09")
        .group_by(["family_label", "algo_label"])
        .agg(pl.col("aver_time").median().alias("ms"))
    )
    # 对数 y 轴：用点图而不是柱状图
    abs_bars = (
        alt.Chart(d_abs)
        .mark_point(size=170, filled=True)
        .encode(
            x=alt.X("family_label:N", title="data family", sort=FAMILY_ORDER, axis=alt.Axis(labelAngle=-25)),
            y=alt.Y("ms:Q", scale=alt.Scale(type="log"), title="time (ms, log scale)"),
            color=alt.Color("algo_label:N", scale=ALGO_COLOR, sort=ALGO_ORDER, title=None),
            xOffset=alt.XOffset("algo_label:N", sort=ALGO_ORDER),
            tooltip=[
                alt.Tooltip("family_label:N", title="family"),
                alt.Tooltip("algo_label:N", title="algorithm"),
                alt.Tooltip("ms:Q", title="ms", format=".3f"),
            ],
        )
    ).properties(width=520, height=320, title=alt.TitleParams(
        text="(b) tier09 (n=100, c=200000), all 5 families",
        fontSize=LABEL_FONT + 1, anchor="start"))

    return with_title(
        (cost_bars & abs_bars),
        "Fig.3  Effect of p/w correlation on runtime",
        "strongly correlated instances keep many incomparable states: dominance prunes little and the bound stays loose",
    )


# ---------------------------------------------------------------- 图 4
def fig4_speedup(df: pl.DataFrame) -> None:
    """改进算法相对 DP-1 的提升率：>1 更快，<1 更慢"""
    wide = (
        df.group_by(["tier", "family", "num_of_item", "capacity", "nc", "algo"])
        .agg(pl.col("aver_time").median().alias("ms"))
        .pivot(on="algo", index=["tier", "family", "num_of_item", "capacity", "nc"], values="ms")
    )
    wide = wide.filter(
        pl.col("base").is_not_null()
        & pl.col("dominance").is_not_null()
        & pl.col("bound").is_not_null()
    ).with_columns(
        (pl.col("base") / pl.col("dominance")).alias("DP-with-Lists (3.4)"),
        (pl.col("base") / pl.col("bound")).alias("DP+Upper-Bound (3.5)"),
    )

    long = wide.unpivot(
        on=["DP-with-Lists (3.4)", "DP+Upper-Bound (3.5)"],
        index=["tier", "family", "num_of_item", "capacity", "nc"],
        variable_name="algo_label",
        value_name="speedup",
    )

    by_tier = (
        long.group_by(["tier", "num_of_item", "capacity", "algo_label"])
        .agg(pl.col("speedup").median().alias("speedup"))
        .with_columns(
            (
                "n=" + pl.col("num_of_item").cast(pl.Utf8)
                + ", c=" + pl.col("capacity").cast(pl.Utf8)
            ).alias("size_label")
        )
        .sort(["num_of_item", "capacity"])
    )
    size_order = by_tier["size_label"].unique(maintain_order=True).to_list()

    # 对数 y 轴：点图（柱状图无法在对数轴上从 0 起画）
    bars = (
        alt.Chart(by_tier)
        .mark_point(size=150, filled=True)
        .encode(
            x=alt.X("size_label:N", title="instance size (n, c)", sort=size_order,
                    axis=alt.Axis(labelAngle=-35)),
            y=alt.Y("speedup:Q", scale=alt.Scale(type="log"), title="speed-up vs DP-1  (>1 = faster)"),
            color=alt.Color("algo_label:N", sort=ALGO_ORDER, title=None,
                            scale=alt.Scale(domain=ALGO_ORDER[1:], range=["#F58518", "#54A24B"])),
            xOffset=alt.XOffset("algo_label:N", sort=ALGO_ORDER),
            tooltip=[
                alt.Tooltip("tier:N", title="tier"),
                alt.Tooltip("algo_label:N", title="algorithm"),
                alt.Tooltip("speedup:Q", title="×", format=".2f"),
            ],
        )
    ).properties(width=640, height=330)

    ref = (
        alt.Chart(pl.DataFrame({"y": [1.0]}))
        .mark_rule(strokeDash=[5, 4], color="#777777")
        .encode(y="y:Q")
    )

    # 提升率 vs n·c（散点，每个 (tier, family) 一个点）
    scat = (
        alt.Chart(long)
        .mark_circle(size=70, opacity=0.7)
        .encode(
            x=alt.X("nc:Q", scale=alt.Scale(type="log"), title="n · c"),
            y=alt.Y("speedup:Q", scale=alt.Scale(type="log"), title="speed-up vs DP-1"),
            color=alt.Color("algo_label:N", sort=ALGO_ORDER, title=None,
                            scale=alt.Scale(domain=ALGO_ORDER[1:], range=["#F58518", "#54A24B"])),
            tooltip=[
                alt.Tooltip("tier:N"), alt.Tooltip("family:N"),
                alt.Tooltip("speedup:Q", format=".2f"),
            ],
        )
    ).properties(width=640, height=280)

    ch = (bars + ref) & (scat + alt.Chart(pl.DataFrame({"y": [1.0]})).mark_rule(
        strokeDash=[5, 4], color="#777777").encode(y="y:Q"))

    return with_title(
        ch,
        "Fig.4  Improvement over DP-1 (median over data families)",
        "3.5 wins on almost every instance; 3.4 loses when the frontier stays as large as c (strong correlation / subset sum)",
    )


# ---------------------------------------------------------------- 图 5
def fig5_tier09(df: pl.DataFrame) -> alt.Chart:
    """tier09（n=100, c=200000）五组数据上三种算法的对比"""
    d = df.filter(pl.col("tier") == "tier09")

    # (a) 平行坐标：横轴是算法，每条折线是一个数据族（对数 y）
    prof = (
        d.group_by(["family_label", "algo_label"])
        .agg(pl.col("aver_time").median().alias("ms"))
    )
    fam_scale = alt.Scale(domain=FAMILY_ORDER,
                          range=["#4C78A8", "#F58518", "#E45756", "#72B7B2", "#54A24B"])
    lines = (
        alt.Chart(prof)
        .mark_line(point=alt.OverlayMarkDef(size=110, filled=True), strokeWidth=2.2)
        .encode(
            x=alt.X("algo_label:N", sort=ALGO_ORDER, title=None,
                    axis=alt.Axis(labelAngle=-12)),
            y=alt.Y("ms:Q", scale=alt.Scale(type="log"), title="time (ms, median, log scale)"),
            color=alt.Color("family_label:N", scale=fam_scale, sort=FAMILY_ORDER, title="data family"),
            # 蓝/绿（uncorr 与 small profit）、红/青（strong 与 subset sum）几乎重合，用虚线型区分
            strokeDash=alt.StrokeDash(
                "family_label:N",
                scale=alt.Scale(domain=FAMILY_ORDER,
                                range=[[1, 0], [5, 3], [1, 2], [7, 3], [2, 4]]),
                sort=FAMILY_ORDER,
                legend=None,
            ),
            detail="family_label:N",
            tooltip=[
                alt.Tooltip("family_label:N", title="family"),
                alt.Tooltip("algo_label:N", title="algorithm"),
                alt.Tooltip("ms:Q", title="ms", format=".4f"),
            ],
        )
        .properties(width=520, height=350, title=alt.TitleParams(
            text="(a) absolute runtime on the 5 tier09 families", fontSize=LABEL_FONT + 1, anchor="start")))

    # (b) 相对 DP-1 的提升率（>1 更快），同一批数据
    wide = (
        d.group_by(["family", "family_label", "algo"])
        .agg(pl.col("aver_time").median().alias("ms"))
        .pivot(on="algo", index=["family", "family_label"], values="ms")
    )
    wide = wide.with_columns(
        (pl.col("base") / pl.col("dominance")).alias("DP-with-Lists (3.4)"),
        (pl.col("base") / pl.col("bound")).alias("DP+Upper-Bound (3.5)"),
    )
    speed = wide.unpivot(
        on=["DP-with-Lists (3.4)", "DP+Upper-Bound (3.5)"],
        index=["family", "family_label"],
        variable_name="algo_label",
        value_name="speedup",
    )
    dots = (
        alt.Chart(speed)
        .mark_point(size=170, filled=True)
        .encode(
            x=alt.X("family_label:N", sort=FAMILY_ORDER, title=None,
                    axis=alt.Axis(labelAngle=-22)),
            y=alt.Y("speedup:Q", scale=alt.Scale(type="log"),
                    title="speed-up vs DP-1   (>1 = faster)"),
            color=alt.Color("algo_label:N", sort=ALGO_ORDER[1:], title=None,
                            scale=alt.Scale(domain=ALGO_ORDER[1:], range=["#F58518", "#54A24B"])),
            xOffset=alt.XOffset("algo_label:N", sort=ALGO_ORDER[1:]),
            tooltip=[
                alt.Tooltip("family_label:N", title="family"),
                alt.Tooltip("algo_label:N", title="algorithm"),
                alt.Tooltip("speedup:Q", title="×", format=".2f"),
            ],
        )
    )
    ref = alt.Chart(pl.DataFrame({"y": [1.0]})).mark_rule(
        strokeDash=[5, 4], color="#777777").encode(y="y:Q")
    panel_b = (dots + ref).properties(
        width=520, height=350, title=alt.TitleParams(
            text="(b) speed-up vs DP-1 (1 = same, <1 = slower)",
            fontSize=LABEL_FONT + 1, anchor="start"))

    # color 必须 independent：否则两个面板的色标会被合并，圆点颜色和左边折线撞色
    ch = (lines | panel_b).resolve_scale(y="independent", color="independent")
    return with_title(
        ch,
        "Fig.5  tier09 (n=100, c=200000): the five data families, three algorithms",
        "same n and c in every panel; only the p/w relation changes  "
        "(uncorrelated / weak / strong / subset-sum p=w / small profit)",
    )


# ---------------------------------------------------------------- main
def main() -> None:
    df = load()
    print(f"loaded {df.height} rows: {df['tier'].n_unique()} tiers, {df['family'].n_unique()} families")
    print()

    charts = {
        "fig1_base_vs_nc": fig1_base_vs_nc(df),
        "fig2_same_n_diff_c": fig2_same_n_diff_c(df),
        "fig3_correlation": fig3_correlation(df),
        "fig4_speedup": fig4_speedup(df),
        "fig5_tier09": fig5_tier09(df),
    }

    for name, ch in charts.items():
        save_pdf(ch, name)

    import datetime
    save_html(
        list(charts.values()),
        subtitle=(
            f"source: result/*.csv  ·  {df.height} rows, {df['tier'].n_unique()} tiers, "
            f"{df['family'].n_unique()} families  ·  generated {datetime.datetime.now():%Y-%m-%d %H:%M}"
        ),
    )

    # 数值摘要，方便写报告
    wide = (
        df.group_by(["tier", "num_of_item", "capacity", "algo"])
        .agg(pl.col("aver_time").median().alias("ms"))
        .pivot(on="algo", index=["tier", "num_of_item", "capacity"], values="ms")
        .with_columns(
            (pl.col("base") / pl.col("dominance")).alias("x_34"),
            (pl.col("base") / pl.col("bound")).alias("x_35"),
        )
        .sort("num_of_item", "capacity")
    )
    print("per-instance medians (ms) and speed-up vs DP-1:")
    print(wide)
    print()
    print(f"3.4 speed-up: min {wide['x_34'].min():.2f}x, max {wide['x_34'].max():.2f}x")
    print(f"3.5 speed-up: min {wide['x_35'].min():.2f}x, max {wide['x_35'].max():.2f}x")


if __name__ == "__main__":
    main()
