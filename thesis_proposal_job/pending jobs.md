## Pending Jobs

1. **Thesis Proposal**
   - 完成並修改 Thesis Proposal。
   - 明確定義研究問題、研究動機、Research Gap 與 Contribution。
   - 整理研究方法、系統架構與初步實驗結果。

2. **修改 O-RAN 系統架構**
   - 根據 O-RAN 標準修改系統架構圖。
   - 釐清 CortexDC、InfluxDB、rApps、Non-RT RIC 與 Near-RT RIC 之間的連接方式。
   - 加入 R1、A1 Interface，並將 gNB 拆分為 O-CU、O-DU 與 O-RU。

3. **收集 CPU Usage 資料**
   - 在 5G End-to-End 實驗中加入 CPU Usage 資料收集。
   - 同步收集 CPU Usage、CPU Temperature、Fan RPM 與 Server Power。
   - 對齊不同資料來源的 Timestamp。

4. **收集更多高變化資料**
   - 利用 5G End-to-End Workload 產生不同的 CPU Load。
   - 收集 CPU Temperature 變化較明顯的資料。
   - 延長資料收集時間，增加模型訓練資料量。

5. **CPU Temperature Prediction 實驗**
   - 比較 Persistence 與 XGBoost 模型。
   - 預測未來 1、5、15 分鐘的 CPU Temperature。
   - 比較加入 CPU Usage 前後的模型預測結果。
   - 測試不同 Lag Length 與 Feature Combination。
   - 使用 MAE、RMSE 與 Max Error 評估模型。
