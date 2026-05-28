# <div align="center">0527~0529 Study Notes - Rack-Level Thermal Prediction Framework</div>
---

# 1. Research Objective

The goal of this research is to develop a rack-level thermal prediction framework for data centers using:

- Redfish server monitoring data
- PDU power monitoring data
- Rack spatial metadata

The framework aims to predict:

- Rack average temperature
- Rack hotspot temperature
- Future thermal behavior

for cooling optimization and thermal-aware management.

---

# 2. Motivation

Modern data centers consume large amounts of power, and most electrical power is eventually converted into heat.

Traditional cooling systems often:

- react too slowly
- lack rack-level visibility
- cannot identify thermal hotspots early

Therefore, thermal prediction becomes important for:

- cooling optimization
- energy reduction
- thermal risk prevention
- workload scheduling

---

# 3. Proposed Rack-Level Framework

```text
Redfish Data Collection
(server power / CPU temp / fan speed)
        │
        ├── Server-level thermal features
        │
PDU Monitoring
(total load / outlet power / voltage)
        │
        ├── Rack-level power features
        │
Rack Metadata
(U position / rack ID / server status)
        │
        ├── Spatial placement features
        ↓
Feature Engineering
        ↓
XGBoost / LightGBM
        ↓
Rack-Level Temperature Prediction
        ↓
Thermal Warning / Cooling Optimization
```
---
# 4.  Data Input Layer
## 4.1 Redfish Data
```text
Input:
- Server current power
- Server average power
- CPU average temperature
- Air intake temperature
- Fan speed
- Server health status
- Power state
Purpose:
描述單台 server 的發熱狀態
```
---
## 4.2 PDU Data
```text
Input:
- Rack total load
- Outlet power
- Voltage
- Current
- Power factor
- Energy consumption

Purpose:
描述整個 rack 的總耗電與總熱源
```
---
## 4.3 Rack Metadata
```text
Input:
- Rack ID
- Server name
- U position
- U size
- Server online/offline status
- Server placement order

Purpose:
描述 server 在 rack 中的空間位置
```
---
# 5. Feature Engineering Layer

The raw monitoring data is transformed into rack-level thermal features.

## 5.1 Rack-Level Features

- `total_rack_power`
- `average_server_power`
- `maximum_server_power`
- `number_of_active_servers`

## 5.2 Spatial Features

- `upper_rack_power`
- `middle_rack_power`
- `lower_rack_power`
- `weighted_U_position`

## 5.3 Thermal Features

- `average_CPU_temperature`
- `maximum_CPU_temperature`
- `average_intake_temperature`
- `temperature_change_rate`

---

# 6. Prediction Layer: XGBoost / LightGBM

## 6.1 Model Input

### Power Features

- PDU total load
- Server power
- Outlet power

### Thermal Features

- CPU temperature
- Intake temperature
- Fan speed

### Spatial Features

- U position
- Rack ID
- Server distribution

## 6.2 Model Output

- `rack_average_temperature`
- `rack_maximum_temperature`
- `hotspot_risk_score`
- `next_5min_temperature`

---

# 7. Rack-Level Prediction Output

The prediction layer estimates the thermal condition of the entire rack.

## 7.1 Example Outputs

| Output | Description |
|---|---|
| Rack Avg Temp | Average rack temperature |
| Rack Max Temp | Highest rack temperature |
| Hotspot Risk | Potential overheating area |
| Future Temp | Future rack thermal trend |
