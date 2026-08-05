import json as _json

from pydantic import BaseModel


class AnalysisResult(BaseModel):
    mean: float | None = None
    median: float | None = None
    stddev: float | None = None
    min_val: float | None = None
    max_val: float | None = None
    count: int = 0
    summary: str = ""
    error: str | None = None


class ChartResult(BaseModel):
    chart_type: str = ""
    chart_data_base64: str = ""
    title: str = ""
    error: str | None = None


_ANALYSIS_TEMPLATE = r"""
import json
import statistics

data = json.loads(DATA_JSON_PLACEHOLDER)

if not data:
    print(json.dumps({"error": "no data provided"}))
    exit(0)

values = [float(x) for x in data if x is not None]
if not values:
    print(json.dumps({"error": "no numeric values"}))
    exit(0)

result = {
    "mean": statistics.mean(values),
    "median": statistics.median(values),
    "stddev": statistics.stdev(values) if len(values) > 1 else 0,
    "min_val": min(values),
    "max_val": max(values),
    "count": len(values),
    "summary": f"n={len(values)}, mean={statistics.mean(values):.2f}, "
    f"median={statistics.median(values):.2f}, "
    f"range=[{min(values):.2f}, {max(values):.2f}]"
}

trend = "stable"
if len(values) >= 4:
    recent = values[-10:]
    n = len(recent)
    if n >= 4:
        x_mean = (n - 1) / 2
        y_mean = statistics.mean(recent)
        num = sum((i - x_mean) * (recent[i] - y_mean) for i in range(n))
        den = sum((i - x_mean) ** 2 for i in range(n))
        if den > 0:
            slope = num / den
            trend_range = (max(recent) - min(recent)) / 100 if max(recent) != min(recent) else 0.01
            if slope > trend_range:
                trend = "increasing"
            elif slope < -trend_range:
                trend = "decreasing"
    result["trend"] = trend

print(json.dumps(result))
"""


_CHART_TEMPLATE = r"""
import json
import base64
import io

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

data = json.loads(DATA_JSON_PLACEHOLDER)
chart_type = CHART_TYPE_PLACEHOLDER
title = TITLE_PLACEHOLDER
x_label = X_LABEL_PLACEHOLDER
y_label = Y_LABEL_PLACEHOLDER

labels = [str(d.get("label", d.get("name", i))) for i, d in enumerate(data)]
values = [float(d.get("value", d.get("score", 0))) for d in data]

fig, ax = plt.subplots(figsize=(10, 5))
if chart_type == "bar":
    ax.bar(labels, values, color="#2563eb")
elif chart_type == "line":
    ax.plot(labels, values, marker="o", color="#2563eb", linewidth=2)
elif chart_type == "scatter":
    ax.scatter(range(len(values)), values, color="#2563eb")
elif chart_type == "pie":
    ax.pie(values, labels=labels, autopct="%1.1f%%", startangle=90)
elif chart_type == "histogram":
    ax.hist(values, bins=10, color="#2563eb", edgecolor="white")
else:
    ax.bar(labels, values, color="#2563eb")

ax.set_title(title)
if x_label:
    ax.set_xlabel(x_label)
if y_label:
    ax.set_ylabel(y_label)
plt.xticks(rotation=45, ha="right")
plt.tight_layout()

buf = io.BytesIO()
fig.savefig(buf, format="png", dpi=100)
plt.close(fig)
buf.seek(0)

result = {
    "chart_type": chart_type,
    "chart_data_base64": base64.b64encode(buf.read()).decode("utf-8"),
    "title": title
}
print(json.dumps(result))
"""


def build_analysis_code(values: list[float]) -> str:
    return _ANALYSIS_TEMPLATE.replace("DATA_JSON_PLACEHOLDER", _json.dumps(values))


def build_chart_code(
    data: list[dict],
    chart_type: str = "bar",
    title: str = "Chart",
    x_label: str = "",
    y_label: str = "",
) -> str:
    code = _CHART_TEMPLATE.replace("DATA_JSON_PLACEHOLDER", _json.dumps(data))
    code = code.replace("CHART_TYPE_PLACEHOLDER", _json.dumps(chart_type))
    code = code.replace("TITLE_PLACEHOLDER", _json.dumps(title))
    code = code.replace("X_LABEL_PLACEHOLDER", _json.dumps(x_label))
    code = code.replace("Y_LABEL_PLACEHOLDER", _json.dumps(y_label))
    return code
