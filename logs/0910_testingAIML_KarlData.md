# AIMLFW Karl Random Forest 測試紀錄（2026-09-10）

## 測試目的

依照 AIMLFW 手冊 Section 8 的 Karl Random Forest 完整範例，確認既有模型可以經由 KServe 提供線上推論，並比較 KServe API 與 Pod 內模型的離線預測結果。

## Karl 模型資訊

- 模型名稱：`karl-rf-model`
- 模型版本：`5`
- 演算法：Scikit-Learn `RandomForestRegressor`
- Tree 數量：`n_estimators=100`
- 最大深度：`max_depth=12`
- 最小分割樣本數：`min_samples_split=20`
- 輸入維度：32 個 scalar features
- 輸出：2D Cartesian coordinates `(x, y)`，單位為公尺
- 原始資料集：`scratch/position_dataset_local/labphy_env.json`
- 手冊記錄的資料筆數：23,001

## 訓練流程說明

本次測試使用的是先前已訓練並部署完成的 Karl 模型，沒有重新提交 Training Job。

手冊中真正執行訓練的是 Section 8.3 Step 6。Training Manager 收到 training job 後，由 Kubeflow training pod 執行 Random Forest 的訓練邏輯；核心動作為：

```python
model.fit(X_train, y_train)
```

流程中的角色如下：

| 手冊步驟 | 功能 | 是否訓練 |
|---|---|---|
| Step 2 | 將資料寫入 InfluxDB | 否 |
| Step 3 | 將資料抽取至 Cassandra | 否 |
| Step 4 | 驗證 Feature Store 資料筆數 | 否 |
| Step 5 | 註冊 Feature Group、Pipeline 與 Model | 否 |
| Step 6 | 提交 Training Job，由 training pod 執行 `model.fit()` | 是 |
| Step 7 | 將 `model.joblib` bridge 至 SMO MinIO | 否 |
| Step 8 | 透過 ONAP ACM 建立 KServe 部署 | 否 |
| Step 9 | 確認 InferenceService Ready | 否 |
| Step 10 | 呼叫模型 API 取得預測 | 否 |

## KServe 部署狀態

既有 Karl predictor pod：

```text
karl-rf-model-predictor-7479b8774f-5798t
```

InferenceService 驗證結果：

- Namespace：`kserve-test`
- Model format：`sklearn`
- Storage URI：`s3://aimlfw-bucket/models/karl-rf-model/5/model`
- `READY=True`
- Active model state：`Loaded`
- Target model state：`Loaded`
- Transition status：`UpToDate`
- Internal service URL：`http://karl-rf-model-predictor.kserve-test.svc.cluster.local`

## Artifact 驗證

KServe Pod 內實際載入的檔案：

```text
/mnt/models/model/model.joblib
```

檔案大小：

```text
7,199,471 bytes
```

此大小與手冊中記錄的 Karl model artifact 大小一致。

## 線上推論測試

KServe `sklearnserver` 使用內部通用模型名稱 `model`，因此呼叫路徑為：

```text
POST /v1/models/model:predict
```

測試輸入為手冊提供的 32 維 feature sample：

```json
{
  "instances": [
    [
      0.2573, 0.1287, 0.0858, 0.0643,
      0.0515, 0.0429, 0.0368, 0.0322,
      0.0286, 0.0257, 0.0234, 0.0214,
      0.0198, 0.0184, 0.0172, 0.0161,
      0.0151, 0.0143, 0.0135, 0.0129,
      0.0123, 0.0117, 0.0112, 0.0107,
      66.85, 62.10, 58.40, 55.20,
      1.25, -0.85, 60.63, 66.85
    ]
  ]
}
```

線上 API 實際輸出：

```json
{
  "predictions": [
    [-1.7490237154150197, -0.752]
  ]
}
```

## 離線 Fidelity 驗證

為確認 KServe 是否正確執行 MinIO 中的 artifact，在 predictor pod 內直接以 `joblib.load()` 載入同一個 `model.joblib`，並使用相同的 32 維輸入執行 `model.predict()`。

離線實際輸出：

```text
[[-1.74902372 -0.752]]
```

比較結果：

```text
KServe 線上輸出 = Pod 內 artifact 離線輸出
```

因此目前 KServe 部署、模型載入、輸入格式及線上推論流程皆正常，服務忠實執行目前儲存在 MinIO 的 Karl version 5 artifact。

## 與手冊基準值的差異

手冊記錄的預期結果為：

```text
[0.6958257339119541, -1.8404672341244688]
```

本次線上與離線結果皆為：

```text
[-1.7490237154150197, -0.752]
```

所以本次測試結論為：

- KServe API：成功
- InferenceService readiness：成功
- 線上與目前 artifact 的離線一致性：通過
- 與手冊記錄的固定預測值：不一致

可能原因包括：

1. 手冊中的輸入 sample 與預期輸出並非原始的正確配對。
2. 手冊基準值來自另一份 Random Forest artifact。
3. MinIO 同一 version 5 路徑曾重新上傳內容不同、但大小相同的 artifact。
4. 手冊中的預期輸出記錄錯誤。

雖然目前檔案大小與手冊一致，但相同大小不能證明檔案內容完全相同。若沒有手冊基準 artifact 的 SHA-256，現階段無法判定是 artifact 內容改變，還是手冊中的 sample/expected result 配對錯誤。

## 測試期間發現的叢集狀況

測試期間發現 `kube-controller-manager` 與 `kube-scheduler` 在憑證更新後仍使用舊認證，導致：

- Deployment 的 `observedGeneration` 為空。
- ReplicaSet 無法建立。
- Pod 無法排程。
- controller logs 持續出現 `Unauthorized` leader-election 錯誤。

在取得同意後重新啟動相應 static-pod containers，使其載入已更新的 kubeconfig。之後 controller-manager 成功取得 leader lease，Deployment、ReplicaSet 與 Pod reconciliation 恢復。

此控制平面問題屬於叢集基礎設施狀況，不是 Karl 模型或 KServe artifact 的問題。

## 最終結論

Karl Random Forest 的既有模型確實是已訓練模型。本次沒有重新訓練，而是依手冊執行部署狀態確認與線上推論測試。

目前 `karl-rf-model` version 5 已由 KServe 正常載入，API 能接受 32 維輸入並輸出 2D 座標。線上 API 與 Pod 內 `model.joblib` 的離線預測結果一致，證明服務流程正常；但該結果與手冊記錄的固定基準值不同，後續若需確認歷史 artifact 是否一致，應比較原始 SHA-256 或重新取得當時的 reference model。
