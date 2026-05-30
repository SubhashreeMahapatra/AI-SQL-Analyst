import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import re

# ── Plotly theme ──────────────────────────────────────────────────────────────
COLORS = [
    "#6366f1", "#f59e0b", "#10b981", "#ef4444",
    "#3b82f6", "#8b5cf6", "#ec4899", "#14b8a6",
]

LAYOUT_DEFAULTS = dict(
    font=dict(family="Inter, sans-serif", size=13),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    colorway=COLORS,
    legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="rgba(255,255,255,0.1)", borderwidth=1),
    margin=dict(l=40, r=20, t=50, b=40),
    xaxis=dict(gridcolor="rgba(255,255,255,0.05)", linecolor="rgba(255,255,255,0.1)"),
    yaxis=dict(gridcolor="rgba(255,255,255,0.06)", linecolor="rgba(255,255,255,0.1)"),
)


def _is_date_col(series: pd.Series) -> bool:
    if pd.api.types.is_datetime64_any_dtype(series):
        return True
    if series.dtype == object:
        sample = series.dropna().head(10)
        date_patterns = [
            r"\d{4}-\d{2}-\d{2}",
            r"\d{2}/\d{2}/\d{4}",
            r"Q[1-4]\s+\d{4}",
            r"\d{4}-Q[1-4]",
        ]
        matches = sum(
            1 for v in sample
            if any(re.search(p, str(v)) for p in date_patterns)
        )
        return matches >= len(sample) * 0.7
    return False


class ChartBuilder:
    def auto_chart(self, df: pd.DataFrame, question: str = "", chart_type: str = "auto") -> go.Figure:
        if df is None or df.empty:
            return self._empty_chart("No data returned")

        df = df.copy()

        # Try to parse date columns
        for col in df.columns:
            if _is_date_col(df[col]):
                try:
                    df[col] = pd.to_datetime(df[col])
                except Exception:
                    pass

        numeric_cols = df.select_dtypes(include="number").columns.tolist()
        cat_cols = [c for c in df.columns if not pd.api.types.is_numeric_dtype(df[c])]
        date_cols = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]

        # Auto-detect chart type from query keywords
        if chart_type == "auto":
            q = question.lower()
            if any(w in q for w in ["trend", "over time", "monthly", "weekly", "daily", "quarterly", "q1", "q2", "q3", "q4"]):
                chart_type = "line"
            elif any(w in q for w in ["proportion", "share", "percentage", "breakdown", "distribution"]):
                chart_type = "pie"
            elif any(w in q for w in ["compare", "top", "highest", "lowest", "ranking", "best", "worst"]):
                chart_type = "bar"
            elif any(w in q for w in ["correlation", "relationship", "vs"]):
                chart_type = "scatter"
            elif date_cols and numeric_cols:
                chart_type = "line"
            elif cat_cols and numeric_cols:
                chart_type = "bar"
            elif len(numeric_cols) >= 2:
                chart_type = "scatter"
            else:
                chart_type = "table"

        fig = None

        if chart_type == "line" and date_cols and numeric_cols:
            fig = self._line_chart(df, date_cols[0], numeric_cols, cat_cols)
        elif chart_type == "bar" and cat_cols and numeric_cols:
            fig = self._bar_chart(df, cat_cols[0], numeric_cols[0])
        elif chart_type == "pie" and cat_cols and numeric_cols:
            fig = self._pie_chart(df, cat_cols[0], numeric_cols[0])
        elif chart_type == "scatter" and len(numeric_cols) >= 2:
            fig = self._scatter_chart(df, numeric_cols[0], numeric_cols[1], cat_cols)
        elif chart_type == "area" and date_cols and numeric_cols:
            fig = self._area_chart(df, date_cols[0], numeric_cols[0])
        elif chart_type == "heatmap" and len(cat_cols) >= 2 and numeric_cols:
            fig = self._heatmap(df, cat_cols[0], cat_cols[1], numeric_cols[0])

        # Fallback: bar if cat+num available, else table
        if fig is None:
            if cat_cols and numeric_cols:
                fig = self._bar_chart(df, cat_cols[0], numeric_cols[0])
            else:
                return None  # Let app render raw dataframe

        fig.update_layout(**LAYOUT_DEFAULTS)
        return fig

    # ── Chart Types ───────────────────────────────────────────────────────────

    def _line_chart(self, df, x_col, y_cols, cat_cols):
        if cat_cols and len(df[cat_cols[0]].unique()) <= 8 and len(y_cols) == 1:
            fig = px.line(
                df, x=x_col, y=y_cols[0], color=cat_cols[0],
                markers=True, title=f"{y_cols[0]} over {x_col}"
            )
        else:
            fig = go.Figure()
            for i, y_col in enumerate(y_cols[:4]):
                fig.add_trace(go.Scatter(
                    x=df[x_col], y=df[y_col], mode="lines+markers",
                    name=y_col, line=dict(color=COLORS[i % len(COLORS)], width=2.5),
                    marker=dict(size=5),
                ))
            fig.update_layout(title=f"Trend: {', '.join(y_cols[:4])}")
        return fig

    def _bar_chart(self, df, x_col, y_col):
        # Limit to top 20 for readability
        if len(df) > 20:
            df = df.nlargest(20, y_col)
        fig = px.bar(
            df, x=x_col, y=y_col,
            color=y_col, color_continuous_scale=["#312e81", "#6366f1", "#a5b4fc"],
            title=f"{y_col} by {x_col}",
            text=y_col,
        )
        fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
        fig.update_layout(coloraxis_showscale=False, showlegend=False)
        return fig

    def _pie_chart(self, df, label_col, value_col):
        if len(df) > 8:
            top = df.nlargest(7, value_col)
            others = pd.DataFrame([{label_col: "Others", value_col: df[value_col].sum() - top[value_col].sum()}])
            df = pd.concat([top, others], ignore_index=True)
        fig = px.pie(
            df, names=label_col, values=value_col,
            color_discrete_sequence=COLORS,
            title=f"{value_col} distribution",
            hole=0.4,
        )
        fig.update_traces(textposition="inside", textinfo="percent+label")
        return fig

    def _scatter_chart(self, df, x_col, y_col, cat_cols):
        color = cat_cols[0] if cat_cols and len(df[cat_cols[0]].unique()) <= 10 else None
        fig = px.scatter(
            df, x=x_col, y=y_col, color=color,
            trendline="ols" if color is None else None,
            title=f"{x_col} vs {y_col}",
            color_discrete_sequence=COLORS,
            opacity=0.8,
        )
        return fig

    def _area_chart(self, df, x_col, y_col):
        fig = px.area(
            df, x=x_col, y=y_col,
            title=f"{y_col} area chart",
            color_discrete_sequence=COLORS,
        )
        fig.update_traces(line_color=COLORS[0])
        return fig

    def _heatmap(self, df, x_col, y_col, value_col):
        pivot = df.pivot_table(index=y_col, columns=x_col, values=value_col, aggfunc="sum")
        fig = px.imshow(
            pivot, title=f"{value_col} heatmap",
            color_continuous_scale="Viridis",
            aspect="auto",
        )
        return fig

    def _empty_chart(self, message: str):
        fig = go.Figure()
        fig.add_annotation(text=message, x=0.5, y=0.5, showarrow=False, font=dict(size=16))
        fig.update_layout(**LAYOUT_DEFAULTS, title="No Data")
        return fig
