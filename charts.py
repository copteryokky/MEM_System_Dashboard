import pandas as pd
import altair as alt

STATUS_ORDER = [
    "พร้อมใช้งาน",
    "ตรวจไม่พบ",
    "ชำรุด(ซ่อมแซมได้)",
    "ชำรุด(ซ่อมแซมไม่ได้)",
    "ไม่ทราบสถานะ",
]

STATUS_COLOR_MAP = {
    "พร้อมใช้งาน": "#22c55e",
    "ตรวจไม่พบ": "#9ca3af",
    "ชำรุด(ซ่อมแซมได้)": "#fb923c",
    "ชำรุด(ซ่อมแซมไม่ได้)": "#ef4444",
    "ไม่ทราบสถานะ": "#60a5fa",
}

def pie_status_chart(df: pd.DataFrame, status_col: str = "สถานะ"):
    if status_col not in df.columns:
        return alt.Chart(pd.DataFrame({"สถานะ": [], "count": []})).mark_text(
            text="ไม่มีข้อมูลสถานะ"
        )

    counts = (
        df.groupby(status_col)
        .size()
        .reset_index(name="count")
    )
    counts[status_col] = pd.Categorical(
        counts[status_col], STATUS_ORDER, ordered=True
    )
    counts = counts.sort_values(status_col)

    if counts.empty:
        return alt.Chart(pd.DataFrame({"ข้อความ": ["ไม่มีข้อมูลสถานะ"]})).mark_text(
            text="ไม่มีข้อมูลสถานะ"
        )

    total = counts["count"].sum()
    counts["label"] = counts.apply(
        lambda r: f"{r[status_col]} {r['count']} ({r['count'] / total * 100:.1f}%)",
        axis=1,
    )

    chart = (
        alt.Chart(counts)
        .mark_arc(innerRadius=70, outerRadius=120, stroke="white")
        .encode(
            theta="count:Q",
            color=alt.Color(
                f"{status_col}:N",
                scale=alt.Scale(
                    domain=STATUS_ORDER,
                    range=[STATUS_COLOR_MAP.get(s, "#e5e7eb") for s in STATUS_ORDER],
                ),
                legend=alt.Legend(title="สถานะ"),
            ),
            tooltip=[status_col, "count"],
        )
    )

    labels = (
        alt.Chart(counts)
        .mark_text(radius=140, size=14)
        .encode(
            theta="count:Q",
            text=alt.Text("label:N"),
            color=alt.value("#111827"),
        )
    )

    return chart + labels

def bar_status_chart(df: pd.DataFrame, status_col: str = "สถานะ"):
    if status_col not in df.columns:
        return alt.Chart(pd.DataFrame({"สถานะ": [], "count": []})).mark_bar()

    counts = (
        df.groupby(status_col)
        .size()
        .reset_index(name="count")
    )
    counts[status_col] = pd.Categorical(
        counts[status_col], STATUS_ORDER, ordered=True
    )
    counts = counts.sort_values(status_col)

    chart = (
        alt.Chart(counts)
        .mark_bar()
        .encode(
            x=alt.X("count:Q", title="จำนวน (รายการ)"),
            y=alt.Y(f"{status_col}:N", sort=STATUS_ORDER, title=None),
            color=alt.Color(
                f"{status_col}:N",
                scale=alt.Scale(
                    domain=STATUS_ORDER,
                    range=[STATUS_COLOR_MAP.get(s, "#e5e7eb") for s in STATUS_ORDER],
                ),
                legend=None,
            ),
            tooltip=[status_col, "count"],
        )
    )

    text = (
        alt.Chart(counts)
        .mark_text(align="left", dx=4, dy=0)
        .encode(
            x="count:Q",
            y=alt.Y(f"{status_col}:N", sort=STATUS_ORDER),
            text="count:Q",
            color=alt.value("#111827"),
        )
    )

    return chart + text

def bar_location_chart(
    df: pd.DataFrame,
    location_col: str = "สถานที่ใช้งาน (ปัจจุบัน)",
    status_col: str = "สถานะ",
):
    if location_col not in df.columns:
        return alt.Chart(pd.DataFrame({"สถานที่ใช้งาน": [], "count": []})).mark_bar()

    counts = (
        df.groupby(location_col)
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=True)
    )

    chart = (
        alt.Chart(counts)
        .mark_bar()
        .encode(
            x=alt.X("count:Q", title="จำนวน (รายการ)"),
            y=alt.Y(f"{location_col}:N", sort="-x", title="สถานที่ใช้งาน (ปัจจุบัน)"),
            color=alt.value("#3b82f6"),
            tooltip=[location_col, "count"],
        )
    )

    text = (
        alt.Chart(counts)
        .mark_text(align="left", dx=4)
        .encode(
            x="count:Q",
            y=alt.Y(f"{location_col}:N", sort="-x"),
            text="count:Q",
            color=alt.value("#111827"),
        )
    )

    return chart + text
