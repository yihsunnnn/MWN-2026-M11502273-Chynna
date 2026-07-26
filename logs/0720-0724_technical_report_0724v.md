# CortexDC Weekly Progress

**Date:** 2026/07/20–2026/07/24  
**Topic:** Data Center Temperature, Power, and Rack Capacity Analysis

## 1. Weekly Objectives

- 整理資料中心溫度預測、功率監控與機櫃容量相關文獻。
- 驗證 CortexDC、Redfish API 與 BMC Web UI 的資料一致性。
- 分析伺服器溫度、風扇、功率及機櫃容量資料。
- 檢查取樣頻率、缺值與異常資料問題。
- 規劃 CortexDC 的 CPU 溫度預測流程與模型架構。

## 2. Literature Review

本週完成溫度預測與能源管理相關文獻整理，方法涵蓋物理熱模型、Machine Learning、Deep Learning 與功率控制。比較結果顯示：

- 物理模型具有較高可解釋性，但需要完整的熱傳、氣流與硬體參數。
- XGBoost 適合結構化、多感測器且資料量有限的監測資料，並可進行特徵重要性分析。
- GRU／LSTM 可學習較長期的時間相依性，但需要較長時間與更多樣化的訓練資料。
- 多數研究缺乏真實異質伺服器、感測器映射、缺值處理與長期部署驗證。

因此，第一階段建議以 **Baseline Model 與 XGBoost-lag** 為主要比較模型，待資料量增加後，再加入 GRU／LSTM。

## 3. CortexDC Data Verification

以 Quine 伺服器同步比較以下三個資料來源：

1. Supermicro BMC Web UI
2. Redfish API
3. CortexDC InfluxDB

共完成 7 次比對。CPU 溫度有 5 次完全一致，另外 2 次僅相差 1°C；其他進氣溫度、系統溫度及 VRM 溫度皆一致。結果顯示 CortexDC 可正確取得 Redfish 所提供的 BMC 感測器資料，少量差異主要來自採集時間未完全對齊。

需要注意的是，CortexDC 的 CPU 溫度為 BMC／Redfish 提供的代表性 CPU 感測器，無法直接對應 Linux hwmon 中的 Tctl 或 Tccd 通道。

## 4. Sampling Interval and Missing Data

CortexDC 可設定最短 1 分鐘取樣，但實際測試顯示不同伺服器的資料取得能力不同：

- Quine 約每 1–2 分鐘可取得一筆有效資料。
- 多數伺服器在 1 分鐘設定下無法穩定完成每輪採集，實際有效資料間隔接近 5 分鐘。
- 以 1 分鐘目標頻率計算時，部分伺服器缺漏率約為 77%–81%，代表實際取得頻率未達設定目標，不代表所有感測器皆發生故障。
- 將資料統一為 5 分鐘時間窗後，多數伺服器缺漏率明顯降低，但仍存在局部中斷、取樣不一致與欄位缺失。

後續模型訓練前須先進行時間對齊、缺值標記、異常值檢查與資料清理。

## 5. Thermal Analysis

分析期間為 2026/07/17 01:00 至 2026/07/18 01:00，共納入 8 台伺服器。

### 5.1 CPU Temperature

- Inoue 平均 CPU 溫度最高，約為 **69.12°C**，且整體變化較平穩。
- Lavoisier 平均溫度較低，但標準差最高，部分時段出現短時間明顯波動。
- 其餘伺服器大多維持於約 37–53°C。

Inoue 的進氣溫度與同機櫃 Kepler 相近，但 CPU 溫度明顯較高，表示其高溫無法僅由平均進氣溫度解釋。由於尚未完整控制 CPU 型號、實際工作負載、感測器位置、內部氣流及 BMC 風扇策略，目前僅將 Inoue 列為優先觀察與檢查對象，不直接判定為散熱故障。

### 5.2 Fan and Temperature Relationship

- Kepler 與 Newton 的風扇轉速與 CPU 溫度呈較明顯的同步變化。
- Inoue 的風扇轉速變化範圍較小，與 CPU 溫度的即時線性關係不明顯。
- Quine 呈現分段跳檔式風扇控制，而非連續調節。

不同伺服器的風扇控制邏輯差異明顯，因此模型不能假設所有伺服器具有相同的散熱回應。

## 6. Power Analysis

本週完成下列五項分析：

1. 伺服器功率變化趨勢分析
2. 各伺服器平均及最大功率分析
3. PDU Outlet Power 分析
4. 機櫃總功率分析
5. 功率與 CPU 溫度關係分析

主要結果如下：

- Davinci 平均功率最高，約為 **385.71 W**，最大功率為 **449 W**。
- Quine 的平均功率不算最高，但最大功率明顯增加，顯示存在尖峰負載。
- PDU 平均總有效功率約為 **949.16 W**，24 小時耗電量約為 **22.78 kWh**。
- 功率與 CPU 溫度的關係因伺服器而異，不能僅依功率高低判斷溫度狀態。

由於目前 PDU 跨 New-Rack 與 Old-Rack 供電，PDU Total Active Power 應視為該 PDU 的整體供電功率，不能直接代表單一機櫃的總功率。

## 7. Rack Capacity Analysis

CortexDC 目前包含兩座 42U 機櫃：

| Rack | Used | Available | Utilization |
|---|---:|---:|---:|
| BMW New-Rack | 9U | 33U | 21.43% |
| BMW Old-Rack | 18U | 24U | 42.86% |
| Total | 27U | 57U | 32.14% |

若僅考量 U 位，New-Rack 較適合新增設備；但實際容量規劃仍須同時考量 PDU 容量、Outlet 負載、設備功率、進氣溫度、設備重量及相鄰設備配置。

## 8. AI Temperature Prediction Plan

本研究的主要 AI 強化目標為預測未來 CPU 溫度，使 CortexDC 由被動監控進一步具備預測式警示能力。

### Input Features

- BMC／Redfish CPU temperature
- Redfish server power
- Fan speed
- Inlet temperature
- CPU model and CPU count
- Rack／server information
- Historical and lag features

CPU 使用率、記憶體、儲存與網路資料目前無法由所有伺服器穩定取得，因此暫不列為第一階段必要輸入。

### Prediction Targets

- Future CPU temperature
- Prediction horizons: 1, 5, and 15 minutes

### Model Comparison

- Persistence／simple regression baseline
- XGBoost-lag
- GRU／LSTM

模型評估將採時間順序切分與 rolling validation，並使用 MAE、RMSE、R²、溫升事件召回率及推論時間作為指標。

## 9. Current Issues

- 不同伺服器的實際取樣頻率不一致。
- 感測器名稱、數量與物理位置不同。
- 部分欄位缺失或顯示固定異常值。
- PDU Outlet 與伺服器對應仍需進一步確認。
- 工作負載與 CPU 使用率資訊尚未完整。
- 目前僅有 24 小時資料，不足以直接建立穩定的深度學習模型。

## 10. Next Steps

- 延長 CortexDC 資料收集時間。
- 建立 server、sensor、rack 與 PDU Outlet 欄位字典。
- 完成 5 分鐘重新取樣、缺值標記及異常值處理流程。
- 統一不同伺服器的感測器名稱與物理意義。
- 建立 lag、rolling statistics、temperature difference 等特徵。
- 先完成 baseline 與 XGBoost-lag 小規模 PoC。
- 待資料量充足後，再加入 GRU／LSTM 進行時序模型比較。
