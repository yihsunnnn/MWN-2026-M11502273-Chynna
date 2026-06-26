# Understanding PDU Data in InfluxDB

## Current Query Conditions

### Bucket

```text
cortexdc_pdu
```

### Measurement

```text
✓ pdu_inlet
✓ pdu_outlet
```

### Field

```text
✓ active_power
```

This query means:

> Retrieve the **active power** of both the **PDU Inlet** and **all PDU Outlets**.

Therefore, InfluxDB returns:

```
Inlet 1
Outlet 1
Outlet 2
Outlet 3
...
Outlet 12
```

Each of these is an independent sensor.

---

# Why are there so many values at the same timestamp?

For example:

```
2026-06-26 18:05:30
```

InfluxDB is actually showing:

| Time | Sensor | Active Power (W) |
|------|---------|-----------------:|
|18:05:30|Inlet 1|944.9|
|18:05:30|Outlet 10|239.5|
|18:05:30|Outlet 8|191.4|
|18:05:30|Outlet 5|114.3|
|18:05:30|Outlet 4|107.8|
|18:05:30|Outlet 9|88.6|
|18:05:30|Outlet 11|67.9|
|18:05:30|Outlet 7|66.2|
|18:05:30|Outlet 2|30.7|
|18:05:30|Outlet 1|30.5|
|18:05:30|Outlet 6|2.46|
|18:05:30|Outlet 12|2.30|
|18:05:30|Outlet 3|0|

---

## Important Concept

It is **NOT** that one device has many different power values.

Instead,

> At the same timestamp, **each Outlet reports its own power consumption**.

Every Outlet is an independent measurement point.

---

# Which value represents the RU power?

The key question is:

> **Which PDU Outlet is connected to the RU (Radio Unit)?**

For example,

```
RU
│
└── PDU Outlet 10
```

Then,

```
Outlet 10 = RU Power Consumption
```

If instead,

```
RU
│
└── PDU Outlet 5
```

Then,

```
Outlet 5 = 114.3 W
```

is the power consumption of the RU.

Therefore,

> The RU power is **not** the Inlet power.
>
> It is the active power of the Outlet where the RU is connected.

---

# Why does the graph contain many colors?

InfluxDB treats each **sensor_name** as an independent Time Series.

For example:

```
Blue    → Inlet 1

Red     → Outlet 10

Purple  → Outlet 8

Yellow  → Outlet 5

...
```

Therefore, one graph may contain many colored lines.

---

# Recommendation

Instead of displaying all Outlets simultaneously,

add another filter:

```
sensor_name
```

Then select only one Outlet, for example:

```
Outlet 10
```

The graph will display only one Time Series.

This makes it much easier to observe the power variation of the connected device (e.g., the RU).

---

# Summary

- Bucket: `cortexdc_pdu`
- Measurement: `pdu_inlet` and `pdu_outlet`
- Field: `active_power`
- Each Outlet is an independent power sensor.
- The same timestamp contains multiple values because multiple sensors report simultaneously.
- The RU power equals the active power of the Outlet connected to the RU.
- Filtering by `sensor_name` allows you to monitor a single Outlet clearly.<img width="1920" height="1200" alt="螢幕擷取畫面 2026-06-26 180733" src="https://github.com/user-attachments/assets/76324a91-4e9b-45e7-ae5f-abd50aaa7c1d" />

# PDU Inlet 與 Outlet 功率說明

## 為什麼 Inlet 的功率比 Outlet 高？

在 CortexDC / InfluxDB 中查詢 PDU 的 `active_power` 時，常會看到：

| Sensor | Active Power (W) |
|---------|-----------------:|
| Inlet 1 | 944.9 |
| Outlet 10 | 239.5 |
| Outlet 8 | 191.4 |
| Outlet 5 | 114.3 |
| Outlet 4 | 107.8 |
| Outlet 9 | 88.6 |
| Outlet 11 | 67.9 |
| Outlet 7 | 66.2 |
| Outlet 2 | 30.7 |
| Outlet 1 | 30.5 |
| Outlet 6 | 2.46 |
| Outlet 12 | 2.30 |
| Outlet 3 | 0 |

第一次看到會疑惑：

> 為什麼 Inlet 的功率遠大於每一個 Outlet？

---

# PDU 架構

PDU (Power Distribution Unit) 可以想像成一個智慧型延長線。

```
          Utility Power
               │
               ▼
         PDU Inlet
      (Total Input Power)
               │
      ┌────────────────┐
      │      PDU       │
      └────────────────┘
       │   │   │   │
       ▼   ▼   ▼   ▼
   Outlet1 ... Outlet12
```

其中：

- **Inlet**：PDU 從市電或 UPS 接收到的總輸入功率。
- **Outlet**：PDU 分配給各設備（Server、RU、Switch...）的輸出功率。

---

# Inlet 與 Outlet 的關係

理論上：

\[
P_{\text{Inlet}}
\approx
\sum_{i=1}^{N} P_{\text{Outlet}_i}
\]

也就是：

> **Inlet 功率 ≈ 所有 Outlet 功率總和**

---

# 以目前資料為例

所有 Outlet 加總：

```
239.5
+191.4
+114.3
+107.8
+88.6
+67.9
+66.2
+30.7
+30.5
+2.46
+2.30
≈941.7 W
```

而：

```
Inlet = 944.9 W
```

兩者只相差約 **3 W**。

此差異通常來自：

- PDU 本身耗電
- 量測解析度
- 感測器更新時間差
- 四捨五入誤差

因此屬於正常現象。

---

# 為什麼同一個時間有很多數值？

InfluxDB 會同時顯示：

```
18:05:30

Inlet 1
Outlet 1
Outlet 2
Outlet 3
...
Outlet 12
```

因此在同一時間會看到許多不同的功率值。

例如：

| Time | Sensor | Active Power |
|------|---------|-------------:|
|18:05:30|Inlet 1|944.9 W|
|18:05:30|Outlet 10|239.5 W|
|18:05:30|Outlet 8|191.4 W|
|18:05:30|Outlet 5|114.3 W|
|...|...|...|

並不是一個設備有很多數值，

而是：

> **不同 Sensor 在同一時間各自回報自己的功率。**

---

# 為什麼 Graph 有很多顏色？

InfluxDB 會把每一個 `sensor_name` 當作一條 Time Series。

例如：

```
藍色   → Inlet 1

紅色   → Outlet 10

紫色   → Outlet 8

黃色   → Outlet 5

...
```

因此圖上會同時出現許多不同顏色。

---

# RU 功率要看哪裡？

如果研究目的是：

> **量測 RU (Radio Unit) 的功率**

則**不是看 Inlet**。

而是先確認：

```
RU
│
└── 接到哪一個 PDU Outlet？
```

例如：

```
RU
│
└── Outlet 10
```

則：

```
Outlet 10 = RU Power Consumption
```

例如：

```
Outlet 10 = 239.5 W
```

就是 RU 的即時功率。

---

# 重點整理

- Inlet = 整台 PDU 的總輸入功率。
- Outlet = 每個插座對應設備的功率。
- Inlet 功率約等於所有 Outlet 功率總和。
- Graph 出現很多顏色是因為每個 Sensor 都是一條獨立的 Time Series。
- 若要量測 RU 功耗，應確認 RU 所連接的 Outlet，再查看該 Outlet 的 `active_power`。
