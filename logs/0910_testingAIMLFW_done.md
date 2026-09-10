# AIMLFW 成功測試紀錄（2026-09-10）

## 測試摘要

本次測試完成 AIMLFW Job 107 的訓練結果確認、TensorFlow SavedModel artifact 搬移、KServe ACM payload 產生，以及獨立 Evaluation Pod 評估。整體流程已成功走通。

## 測試環境

- Kubernetes namespace：`kubeflow`
- Kubeconfig：`/home/ubuntu/aimlfw-kubeconfig.yaml`
- Training Manager：`192.168.8.114:32002`
- GPU worker：`192.168.8.44`
- GPU：NVIDIA GeForce RTX 4080
- TensorFlow image：`tensorflow/tensorflow:2.17.0-gpu`
- Evaluation service account：`pipeline-runner`

## Job 107 訓練結果

- Job ID：`107`
- Model name：`qoe_model_gpu_v2`
- Model version：`1`
- Artifact version：`1.0.0`
- Feature group：`qoe_fg_107`
- Pipeline：`qoe_pipeline_GPU_v2`
- Workflow：`qoe-pipeline-ll4gn`
- 訓練狀態：完成
- Early stopping：第 18 epoch 停止，還原第 13 epoch 的最佳權重
- 模型參數量：453,302

模型結構：

1. LSTM 150 units，`return_sequences=True`
2. LSTM 150 units，`return_sequences=True`
3. LSTM 150 units
4. Dense 2 outputs

訓練設定：

- Optimizer：Adam
- Loss：MSE
- Batch size：10
- Validation split：20%
- EarlyStopping monitor：`val_loss`
- Patience：5
- Restore best weights：啟用

## 輸入資料確認

Feature Store 回傳：

- 原始 shape：`(121545, 2)`
- 欄位：`pdcpBytesDl`、`pdcpBytesUl`
- 原始 dtype：`object`
- 缺失值：兩欄皆為 0
- 轉換後 dtype：兩欄皆為 `float32`

滑動時間窗設定：

- Past window：10
- Future window：1
- 模型輸入 `X`：`(121535, 10, 2)`，`float32`
- 預測目標 `y`：`(121535, 2)`，`float32`
- 有效 sequence samples：121,535

資料摘要（兩欄輸出相同）：

| 統計量 | pdcpBytesDl | pdcpBytesUl |
|---|---:|---:|
| Count | 121,545 | 121,545 |
| Mean | 430.136993 | 430.136993 |
| Std | 838.483582 | 838.483582 |
| Min | 0.000000 | 0.000000 |
| 25% | 0.000000 | 0.000000 |
| 50% | 0.000000 | 0.000000 |
| 75% | 434.175995 | 434.175995 |
| Max | 4115.885742 | 4115.885742 |

注意：兩個欄位的摘要統計與已觀察到的前幾筆資料完全相同，後續應確認兩欄是否全部相等，以及 Feature Store 欄位 mapping 是否符合預期。

## TensorFlow Artifact Bridge

Job 107 的 `Model.zip` 已成功下載並驗證 SavedModel，隨後上傳至 SMO MinIO。

- 來源：`http://192.168.8.114:32002/model/qoe_model_gpu_v2/1/1.0.0/Model.zip`
- Storage URI：`s3://aimlfw-bucket/models/qoe_model_gpu_v2/1/model`

成功上傳：

- `models/qoe_model_gpu_v2/1/model/1/fingerprint.pb`
- `models/qoe_model_gpu_v2/1/model/1/saved_model.pb`
- `models/qoe_model_gpu_v2/1/model/1/variables/variables.index`
- `models/qoe_model_gpu_v2/1/model/1/variables/variables.data-00000-of-00001`

SavedModel serving signature：

- Input：`keras_tensor`，shape `(None, 10, 2)`，dtype `float32`
- Output：`output_0`，shape `(None, 2)`，dtype `float32`

## KServe ACM Payload 測試

已成功以 `ChainedLifecycleConnector` 產生 TensorFlow KServe ACM payload：

- Training Job ID：`107`
- ACM instance name：`kserve-107`
- InferenceService name：`qoe-model-gpu-v2`
- Namespace：`kserve-test`
- Model format：`tensorflow`
- Storage URI：`s3://aimlfw-bucket/models/qoe_model_gpu_v2/1/model`

本項測試確認 payload 可以正確產生；本紀錄未宣告已向 ACM 實際送出部署請求。

## Evaluation Pod 結果

- Pod：`job107-evaluator-v2`
- 評估樣本數：121,535
- 輸出元素數：243,070

| 指標 | Overall | pdcpBytesDl | pdcpBytesUl |
|---|---:|---:|---:|
| MAE | 78.57840827 | 78.58536895 | 78.57144758 |
| RMSE | 239.28550075 | 239.29567443 | 239.27532663 |
| R² | 0.91856318 | 0.91855625 | 0.91857010 |

額外指標：

- `WithinTolerance5 = 0.55188629`
- 約 55.19% 的單一輸出元素，其絕對誤差小於 5。

原 Pipeline 上傳的指標名稱是 `Accuracy`：

```text
Accuracy = 0.5518204632410417
```

其實際公式為：

```python
np.mean(np.abs(y_true - y_pred) < 5)
```

因此這不是分類 Accuracy，建議將指標名稱改為 `WithinTolerance5`。Evaluation Pod 的結果與原 Pipeline 數值極為接近，確認模型載入、特徵資料與推論流程一致。

## 結果判讀

- MAE 約 78.58，表示每個輸出值的平均絕對誤差約為 78.58。
- RMSE 約 239.29，明顯高於 MAE，表示資料中存在少數較大的預測誤差。
- R² 約 0.9186，代表模型對本次評估資料約可解釋 91.86% 的變異。
- 約 55.19% 的輸出元素，其絕對誤差小於 5。

## 評估限制與後續事項

目前 Evaluation Pod 為了重現原 Pipeline 邏輯，使用全部 121,535 個滑動視窗進行推論。這些資料大部分曾參與訓練，而最後 20% 也曾用於 EarlyStopping validation，因此目前數值屬於流程驗證與 in-sample 評估，不能視為完全獨立的 test-set 成績。

建議後續：

1. 依時間順序保留完全不參與訓練與 EarlyStopping 的 test set。
2. 分別上傳 `MAE`、`RMSE`、`R2` 與 `WithinTolerance5` 至 Model Metrics Service。
3. 檢查 `pdcpBytesDl` 與 `pdcpBytesUl` 是否逐筆完全相等。
4. 確認 Feature Store 欄位 mapping 是否正確。
5. 完成 ACM POST 與 KServe InferenceService 部署後，再記錄線上推論測試結果。

## 結論

Job 107 已成功完成 GPU 訓練、SavedModel 匯出、artifact bridge、MinIO 上傳、ACM KServe payload 產生與獨立 Evaluation Pod 驗證。模型可正常載入並接受 `(None, 10, 2)` 的輸入，評估結果可正確重現原 Pipeline 的 tolerance 指標。
