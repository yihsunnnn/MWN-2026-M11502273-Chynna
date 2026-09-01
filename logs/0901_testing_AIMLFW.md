# 0901
## short goal
### 1. test AIMLFW
### rAPP AIML Training Business Logic

# rAPP AIML Training Business Logic

## 1. Purpose

`business_logic.py` 是 `rapp-aiml-training` 中負責與 **O-Cloud AIMLFW Training Manager** 溝通的核心程式。

此 rAPP 本身不直接執行 Machine Learning Model Training，而是負責：

1. 接收 Training Request。
2. 將 rAPP 收到的參數轉換成 AIMLFW 所需要的 JSON 格式。
3. 透過 HTTP REST API 將 Training Request 傳送至 AIMLFW Training Manager。
4. 接收 AIMLFW 回傳的 `trainingJobId`。
5. 使用 `trainingJobId` 查詢模型訓練狀態。

整體流程如下：

```text
User / Application
        │
        │ Training Request
        ▼
SMO
└── rapp-aiml-training
        │
        ▼
app/business_logic.py
        │
        ├── Build AIMLFW Training Payload
        │
        └── HTTP POST
        ▼
O-Cloud AIMLFW Training Manager
192.168.8.114:32002
        │
        ▼
Kubeflow Training Pipeline
        │
        ▼
Model Training
```

---

# 2. System Architecture

目前 `rapp-aiml-training` 位於 SMO：

```text
SMO
192.168.8.69
```

AIMLFW Training Manager 位於 O-Cloud：

```text
O-Cloud
192.168.8.114:32002
```

因此 rAPP 與 AIMLFW 的關係為：

```text
SMO
192.168.8.69
│
└── rapp-aiml-training
        │
        │ REST API
        ▼
O-Cloud
192.168.8.114
│
└── AIMLFW Training Manager
        │
        ▼
Training Job
```

其中 `app/config.py` 內設定 AIMLFW Training Manager URL：

```text
http://192.168.8.114:32002
```

---

# 3. Main Program Structure

`rapp-aiml-training` 主要 Python 程式包含：

```text
app/
├── business_logic.py
├── config.py
├── main.py
├── models.py
└── sme_client.py
```

其中：

| File | Function |
|---|---|
| `main.py` | rAPP API Entry Point |
| `models.py` | 定義 Request / Response Data Model |
| `config.py` | 儲存 AIMLFW URL 等系統設定 |
| `business_logic.py` | 將 Training Request 傳送至 AIMLFW |
| `sme_client.py` | 與其他 SMO Service 的相關 Client Logic |

本文件主要分析：

```text
app/business_logic.py
```

---

# 4. Main Imports

程式開頭：

```python
import httpx
import json
from typing import Dict, Any
from .config import Settings
```

---

## 4.1 httpx

```python
import httpx
```

`httpx` 用於 Python 程式發送 HTTP Request。

在此程式中主要使用：

```python
client.post()
```

以及：

```python
client.get()
```

用途分別為：

```text
POST
→ 建立新的 AIMLFW Training Job

GET
→ 查詢 AIMLFW Training Job Status
```

因此流程為：

```text
Python rAPP
    │
    │ httpx
    ▼
HTTP REST API
    │
    ▼
AIMLFW Training Manager
```

---

## 4.2 json

```python
import json
```

主要用途為將 Python Dictionary 轉換成容易閱讀的 JSON 格式。

例如：

```python
json.dumps(payload, indent=2)
```

可以將：

```python
{
    "modelName": "cpu-model",
    "version": "1"
}
```

顯示成：

```json
{
  "modelName": "cpu-model",
  "version": "1"
}
```

主要用途是：

```text
Debug
Log
檢查 Training Payload
```

---

## 4.3 Dict and Any

```python
from typing import Dict, Any
```

用於 Python Type Hint。

例如：

```python
request_data: Dict[str, Any]
```

代表：

```text
request_data 是 Dictionary

Key
→ String

Value
→ 任意資料型態
```

例如：

```python
{
    "modelName": "cpu-temperature-model",
    "epochs": 50
}
```

其中：

```text
modelName
→ String

epochs
→ Integer
```

因此使用：

```python
Dict[str, Any]
```

---

## 4.4 Settings

```python
from .config import Settings
```

代表 `business_logic.py` 會從：

```text
app/config.py
```

取得系統設定。

例如：

```text
AIMLFW_TM_URL
```

目前預設 AIMLFW Training Manager 為：

```text
http://192.168.8.114:32002
```

這樣做的好處是避免將 IP Address 寫死在 Business Logic。

例如不建議直接：

```python
url = "http://192.168.8.114:32002"
```

而是：

```python
url = settings.AIMLFW_TM_URL
```

未來如果 AIMLFW IP 改變，只需要修改：

```text
config.py
```

不需要修改：

```text
business_logic.py
```

---

# 5. trigger_aimlfw_training()

主要 Function：

```python
def trigger_aimlfw_training(
    settings: Settings,
    request_data: Dict[str, Any]
) -> Dict[str, Any]:
```

此 Function 的目的為：

> 將 rAPP 收到的 Training Request 轉換成 AIMLFW Training Manager 所需要的 Training Job Payload，並透過 HTTP POST 建立新的 Training Job。

整體流程：

```text
Training Request
      │
      ▼
trigger_aimlfw_training()
      │
      ├── Read AIMLFW URL
      │
      ├── Build API Endpoint
      │
      ├── Build Training Payload
      │
      └── HTTP POST
      ▼
AIMLFW Training Manager
```

---

# 6. Get AIMLFW Training Manager URL

程式：

```python
tm_url = settings.AIMLFW_TM_URL.rstrip('/')
```

假設：

```text
settings.AIMLFW_TM_URL
=
http://192.168.8.114:32002/
```

使用：

```python
rstrip('/')
```

後：

```text
http://192.168.8.114:32002
```

其目的為避免後續組合 URL 時出現：

```text
//
```

例如：

```text
http://192.168.8.114:32002//ai-ml-model-training/...
```

因此屬於 URL Format 的防呆處理。

---

# 7. Build AIMLFW Training Endpoint

程式：

```python
endpoint = f"{tm_url}/ai-ml-model-training/v1/training-jobs"
```

代入：

```text
tm_url
=
http://192.168.8.114:32002
```

最後 Endpoint：

```text
http://192.168.8.114:32002/ai-ml-model-training/v1/training-jobs
```

此 API 用途為：

```text
Create AIMLFW Training Job
```

因此 HTTP Method 使用：

```text
POST
```

---

# 8. rAPP Input Data

rAPP 接收到的 Training Request 主要包含：

```text
modelName
modelVersion
jobName
featureGroupName
epochs
pipelineName
pipelineVersion
```

例如：

```json
{
  "modelName": "cpu-temperature-model",
  "modelVersion": "1",
  "jobName": "cpu-temperature-training",
  "featureGroupName": "cpu_temperature_feature_group",
  "epochs": 50,
  "pipelineName": "cpu_temperature_xgboost",
  "pipelineVersion": "1"
}
```

rAPP 不會直接把這份 JSON 原封不動傳給 AIMLFW。

而是會將這些參數重新整理成 AIMLFW Training Manager 所要求的格式。

---

# 9. Build AIMLFW Training Payload

程式會建立：

```python
payload = {
    ...
}
```

主要功能是：

```text
rAPP Input
      │
      ▼
Format Conversion
      │
      ▼
AIMLFW Training Job Payload
```

---

# 10. Model ID

程式：

```python
"modelId": {
    "modelName": request_data.get("modelName"),
    "modelVersion": request_data.get("modelVersion")
}
```

用途為告訴 AIMLFW：

```text
要訓練哪一個 Model

以及

這個 Model 是哪一個 Version
```

例如 rAPP Request：

```json
{
  "modelName": "cpu-temperature-model",
  "modelVersion": "1"
}
```

轉換後：

```json
{
  "modelId": {
    "modelName": "cpu-temperature-model",
    "modelVersion": "1"
  }
}
```

---

# 11. Model Location

程式：

```python
"modelLocation": ""
```

目前設定為空值。

原因是建立 Training Job 時：

```text
Model 尚未完成 Training
```

因此目前還不存在 Model Artifact。

Training 完成後才可能產生：

```text
Model.zip
```

或：

```text
model.joblib
```

等 Model Artifact。

---

# 12. Training Configuration

程式：

```python
"trainingConfig": {
    ...
}
```

Training Configuration 主要描述：

```text
此次 Training Job

要使用什麼 Data

要使用哪個 Pipeline

需要哪些 Training Parameters
```

---

# 13. Description

程式：

```python
"description": f"Triggered via {request_data.get('jobName')}"
```

例如：

```json
{
  "jobName": "cpu-temperature-training"
}
```

會建立：

```text
Triggered via cpu-temperature-training
```

用途主要為：

```text
Training Job Description
```

方便辨識 Training Job。

---

# 14. Data Pipeline

程式：

```python
"dataPipeline": {
    "feature_group_name": request_data.get("featureGroupName"),
    "query_filter": "",
    "arguments": {
        "epochs": str(request_data.get("epochs", 50))
    }
}
```

Data Pipeline 主要負責告訴 AIMLFW：

```text
Training Pipeline 要從哪裡取得 Training Data
```

---

# 15. Feature Group Name

程式：

```python
request_data.get("featureGroupName")
```

例如：

```text
cpu_temperature_feature_group
```

Feature Group 可以理解為：

> 已經整理好、可以提供 Machine Learning Model Training 使用的一組 Features。

例如 CPU Temperature Prediction 未來可能包含：

```text
CPU Temperature
CPU Usage
Server Power
Fan RPM
Inlet Temperature
```

資料流程可理解為：

```text
CortexDC Data
      +
CPU Usage Data
      │
      ▼
InfluxDB
      │
      ▼
AIMLFW Data Extraction
      │
      ▼
Cassandra Feature Store
      │
      ▼
Feature Group
      │
      ▼
Training Pipeline
```

---

# 16. Query Filter

程式：

```python
"query_filter": ""
```

目前設定為：

```text
Empty
```

代表目前沒有額外使用 Query Filter 篩選 Feature Group 中的資料。

未來 Query Filter 可能用於：

```text
只選特定時間範圍

只選特定 Server

只選符合特定 Condition 的資料
```

但目前 rAPP 沒有設定額外 Filter。

---

# 17. Epochs

程式：

```python
"epochs": str(request_data.get("epochs", 50))
```

如果 Training Request 有設定：

```json
{
  "epochs": 100
}
```

則使用：

```text
100
```

如果沒有提供：

```text
epochs
```

則使用預設值：

```text
50
```

這是因為：

```python
request_data.get("epochs", 50)
```

其中：

```text
50
```

為 Default Value。

之後：

```python
str(...)
```

會將數值轉成 String。

例如：

```text
50
```

轉成：

```text
"50"
```

目前這個 rAPP 會以 String 型態傳送 Epochs。

---

# 18. Training Pipeline

程式：

```python
"trainingPipeline": {
    "training_pipeline_name": request_data.get("pipelineName"),
    "training_pipeline_version": request_data.get("pipelineVersion"),
    "retraining_pipeline_name": request_data.get("pipelineName"),
    "retraining_pipeline_version": request_data.get("pipelineVersion")
}
```

這一段負責指定：

> AIMLFW Training Manager 應該執行哪一個 Kubeflow Training Pipeline。

例如：

```text
pipelineName
=
cpu_temperature_xgboost
```

以及：

```text
pipelineVersion
=
1
```

因此 AIMLFW 就可以知道要執行：

```text
cpu_temperature_xgboost Version 1
```

---

# 19. Model and Pipeline Difference

Model 與 Pipeline 是兩個不同的概念。

## Pipeline

Pipeline 描述：

```text
如何取得 Data

如何 Preprocess

如何 Train Model

如何 Evaluate Model

如何 Export Model
```

## Model

Model 是 Pipeline 執行完成後產生的 Training Result。

因此關係為：

```text
Training Pipeline
        │
        │ Execute
        ▼
Machine Learning Training
        │
        ▼
Model
```

例如：

```text
Pipeline
cpu_temperature_xgboost
        │
        ▼
Training
        │
        ▼
Model
cpu-temperature-model
```

---

# 20. Retraining Pipeline

程式：

```python
"retraining_pipeline_name": request_data.get("pipelineName"),
"retraining_pipeline_version": request_data.get("pipelineVersion")
```

目前：

```text
Training Pipeline
```

與：

```text
Retraining Pipeline
```

使用同一組 Pipeline。

因此：

```text
Initial Training
      │
      └── Pipeline A

Retraining
      │
      └── Pipeline A
```

未來如果需要，也可以設計成：

```text
Initial Training
→ Pipeline A

Retraining
→ Pipeline B
```

---

# 21. Debug Output

程式：

```python
print(f"[Business Logic] POST {endpoint}")
```

會顯示 Request 送往哪個 AIMLFW Endpoint。

另外：

```python
print(
    f"[Business Logic] Payload: {json.dumps(payload, indent=2)}"
)
```

會將完整 Training Payload 顯示出來。

例如：

```text
[Business Logic] POST
http://192.168.8.114:32002/ai-ml-model-training/v1/training-jobs
```

以及：

```json
{
  "modelId": {
    "modelName": "cpu-temperature-model",
    "modelVersion": "1"
  }
}
```

此功能主要用於 Debug，可以檢查：

```text
AIMLFW URL 是否正確

Model Name 是否正確

Model Version 是否正確

Feature Group 是否正確

Pipeline Name 是否正確

Pipeline Version 是否正確

Payload Format 是否正確
```

---

# 22. Send HTTP POST Request

真正將 Training Request 傳送至 AIMLFW 的程式為：

```python
with httpx.Client() as client:
    response = client.post(
        endpoint,
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=10.0
    )
```

整體流程：

```text
SMO
│
└── rapp-aiml-training
        │
        │ HTTP POST
        │
        │ Content-Type:
        │ application/json
        │
        │ Training Payload
        ▼
AIMLFW Training Manager
192.168.8.114:32002
```

---

# 23. HTTP POST

HTTP：

```text
POST
```

主要代表：

```text
Create New Resource
```

在這裡建立的 Resource 就是：

```text
Training Job
```

因此：

```text
POST /training-jobs
```

可以理解成：

> 請 AIMLFW 建立一個新的 Training Job。

---

# 24. JSON Payload

程式：

```python
json=payload
```

表示將：

```python
payload
```

以 JSON Body 的方式傳送給 AIMLFW Training Manager。

同時 Header：

```python
headers={
    "Content-Type": "application/json"
}
```

告訴 AIMLFW：

```text
Request Body Format
=
JSON
```

---

# 25. Timeout

程式：

```python
timeout=10.0
```

代表 HTTP Request 有 Timeout 限制。

如果：

```text
O-Cloud Network Failure

AIMLFW Training Manager Down

Service 無法回應

Network Routing Error
```

程式不會一直無限等待。

---

# 26. HTTP Status Check

程式：

```python
response.raise_for_status()
```

用於確認 HTTP Response 是否成功。

常見 HTTP Status：

| HTTP Status | Meaning |
|---|---|
| `200` | Success |
| `201` | Created |
| `400` | Bad Request |
| `404` | API Not Found |
| `500` | Server Error |

如果 AIMLFW 回傳 Error：

```python
response.raise_for_status()
```

會產生 Exception。

這樣可以避免程式將 Error Response 當成成功結果繼續執行。

---

# 27. Return AIMLFW Response

程式：

```python
return response.json()
```

代表：

> 將 AIMLFW Training Manager 回傳的 JSON 再傳回給呼叫這個 Function 的程式。

例如 AIMLFW 回傳：

```json
{
  "trainingJobId": "123"
}
```

則 rAPP 可以取得：

```text
trainingJobId = 123
```

完整流程：

```text
rAPP
 │
 │ POST Training Request
 ▼
AIMLFW Training Manager
 │
 │ Create Training Job
 ▼
Training Job ID
 │
 ▼
rAPP
```

---

# 28. Training Job ID

`trainingJobId` 是一個非常重要的識別碼。

例如：

```text
trainingJobId
=
123
```

後續可以利用這個 ID：

```text
查 Training Status

確認 Training 是否完成

取得 Training Result
```

因此：

```text
POST Training Request
        │
        ▼
trainingJobId
        │
        ▼
GET Training Status
```

---

# 29. get_aimlfw_training_status()

第二個主要 Function：

```python
def get_aimlfw_training_status(
    settings: Settings,
    training_job_id: str
) -> Dict[str, Any]:
```

用途為：

> 使用 `trainingJobId` 查詢 AIMLFW Training Job 的執行狀態。

流程：

```text
trainingJobId
      │
      ▼
get_aimlfw_training_status()
      │
      ▼
HTTP GET
      │
      ▼
AIMLFW Training Manager
      │
      ▼
Training Job Status
```

---

# 30. Build Training Status Endpoint

程式：

```python
tm_url = settings.AIMLFW_TM_URL.rstrip('/')
```

然後：

```python
endpoint = f"{tm_url}/ai-ml-model-training/v1/training-jobs/{training_job_id}"
```

例如：

```text
training_job_id
=
123
```

則 Endpoint 為：

```text
http://192.168.8.114:32002/ai-ml-model-training/v1/training-jobs/123
```

---

# 31. HTTP GET Request

程式：

```python
with httpx.Client() as client:
    response = client.get(
        endpoint,
        headers={"Content-Type": "application/json"},
        timeout=10.0
    )
```

與建立 Training Job 不同：

```text
POST
→ 建立新的 Training Job

GET
→ 查詢已存在的 Training Job
```

因此：

```text
POST /training-jobs
```

代表：

```text
Create Training Job
```

而：

```text
GET /training-jobs/{trainingJobId}
```

代表：

```text
Get Training Job Status
```

---

# 32. Training Lifecycle

AIMLFW Training Job 執行期間主要可能包含：

```text
PREPROCESS
     │
     ▼
TRAINING
     │
     ▼
POSTPROCESS
```

例如 Training 執行中：

```text
PREPROCESS   FINISHED

TRAINING     RUNNING

POSTPROCESS  NOT_STARTED
```

Training 完成：

```text
PREPROCESS   FINISHED

TRAINING     FINISHED

POSTPROCESS  FINISHED
```

---

# 33. Why rAPP Does Not Train the Model Directly

`rapp-aiml-training` 的工作不是直接執行 Machine Learning Training。

因此不會直接在 Business Logic 中執行：

```python
model.fit(X_train, y_train)
```

而是將不同系統的責任分開。

---

## rAPP

負責決定：

```text
What Model to Train

Which Model Version

Which Feature Group

Which Training Pipeline

Which Training Parameters
```

---

## AIMLFW Training Manager

負責：

```text
Receive Training Request

Create Training Job

Manage Training Lifecycle

Trigger Training Pipeline
```

---

## Kubeflow Pipeline

負責：

```text
Load Data

Preprocess Data

Run Model Training

Evaluate Model

Export Model Artifact
```

---

## Machine Learning Algorithm

真正執行：

```text
XGBoost

Random Forest

Neural Network

Other ML Models
```

---

# 34. Separation of Responsibilities

整體 Responsibility 可以整理為：

```text
rAPP
│
│ "我要訓練什麼？"
│
▼
AIMLFW Training Manager
│
│ "管理這次 Training Job"
│
▼
Kubeflow Pipeline
│
│ "實際執行 Training Process"
│
▼
Machine Learning Model
```

這樣可以讓：

```text
SMO Application Logic
```

與：

```text
AI/ML Training Infrastructure
```

彼此分離。

---

# 35. Complete Business Logic Flow

完整流程：

```text
1. Receive Training Request
        │
        ▼
2. Read AIMLFW_TM_URL
        │
        ▼
3. Build Training Manager Endpoint
        │
        ▼
4. Read Request Parameters
        │
        ├── modelName
        ├── modelVersion
        ├── jobName
        ├── featureGroupName
        ├── epochs
        ├── pipelineName
        └── pipelineVersion
        │
        ▼
5. Build AIMLFW Training Payload
        │
        ▼
6. HTTP POST
        │
        ▼
7. AIMLFW Training Manager
        │
        ▼
8. Create Training Job
        │
        ▼
9. Return trainingJobId
        │
        ▼
10. HTTP GET with trainingJobId
        │
        ▼
11. Check Training Status
```

---

# 36. Simplified Architecture

```text
User
 │
 │ Training Request
 ▼
SMO
 │
 └── rapp-aiml-training
        │
        └── business_logic.py
                │
                │ HTTP REST API
                ▼
O-Cloud
 │
 └── AIMLFW Training Manager
        │
        ▼
Training Job
        │
        ▼
Kubeflow Pipeline
        │
        ▼
Machine Learning Training
        │
        ▼
Model Artifact
```

---

# 37. CPU Temperature Prediction Application

未來 CPU Temperature Prediction 可以沿用相同的 `rapp-aiml-training` 架構。

主要需要修改的是 Training Request 中的參數，例如：

```text
modelName

modelVersion

jobName

featureGroupName

pipelineName

pipelineVersion

Training Parameters
```

例如：

```json
{
  "modelName": "cpu-temperature-model",
  "modelVersion": "1",
  "jobName": "cpu-temperature-training",
  "featureGroupName": "cpu_temperature_feature_group",
  "epochs": 50,
  "pipelineName": "cpu_temperature_xgboost",
  "pipelineVersion": "1"
}
```

---

# 38. CPU Temperature Prediction Data Flow

未來預計資料流程：

```text
CortexDC
│
├── CPU Temperature
├── Server Power
├── Fan RPM
└── Inlet Temperature

CPU Usage Collector
│
└── CPU Usage
        │
        ▼
Data Integration
        │
        ▼
InfluxDB
        │
        ▼
AIMLFW Data Extraction
        │
        ▼
Cassandra Feature Store
        │
        ▼
CPU Temperature Feature Group
        │
        ▼
SMO rapp-aiml-training
        │
        │ Training Request
        ▼
O-Cloud AIMLFW Training Manager
        │
        ▼
Kubeflow Training Pipeline
        │
        ▼
XGBoost Training
        │
        ▼
CPU Temperature Prediction Model
```

---

# 39. Key Parameters for CPU Temperature Prediction

未來主要需要準備以下參數：

| Parameter | Description | Example |
|---|---|---|
| `modelName` | Model Name | `cpu-temperature-model` |
| `modelVersion` | Model Version | `1` |
| `jobName` | Training Job Name | `cpu-temperature-training` |
| `featureGroupName` | Feature Store Group | `cpu_temperature_feature_group` |
| `epochs` | Training Parameter | `50` |
| `pipelineName` | Kubeflow Training Pipeline | `cpu_temperature_xgboost` |
| `pipelineVersion` | Pipeline Version | `1` |

---

# 40. Important Finding

從 `business_logic.py` 可以確認：

```text
rapp-aiml-training
```

並不在 SMO 本地直接執行 ML Training。

它的主要角色是：

> 將 SMO 端的 Training Request 轉換成 AIMLFW Training Manager 所需要的格式，並透過 REST API 將 Training Job 傳送到 O-Cloud AIMLFW。

因此架構為：

```text
SMO rAPP
     │
     │ Training Request
     ▼
O-Cloud AIMLFW
     │
     ▼
Training Pipeline
     │
     ▼
Model Training
```

---

# 41. Summary

`business_logic.py` 可以簡化成以下六個主要步驟：

```text
1. Receive rAPP Training Request

2. Read AIMLFW Training Manager URL

3. Convert Request into AIMLFW Payload

4. POST Training Request to AIMLFW

5. Receive Training Job ID

6. Use Training Job ID to Check Training Status
```

因此 `rapp-aiml-training` 可以視為：

> **SMO 與 O-Cloud AIMLFW Training Manager 之間的 Training Request Controller。**

它負責控制與觸發 Training，而真正的 Machine Learning Training 則由 AIMLFW 與 Kubeflow Pipeline 執行。
