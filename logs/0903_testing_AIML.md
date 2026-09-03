# AIMLFW Hands-on Testing：已處理問題與目前問題

## 1. 已處理完成的問題

### 1.1 SMO rAPP → AIMLFW Training Manager

目前已確認 SMO 上的 `rapp-aiml-training` 可以成功呼叫 O-Cloud AIMLFW Training Manager。

```text
SMO rAPP
   ↓
AIMLFW Training Manager
   ↓
Training Job 105
```

狀態：

```text
✅ 已完成
```

---

### 1.2 Training Job 105 成功建立

目前已成功建立：

```text
Training Job ID:
105
```

使用設定：

```text
Model:
qoe_model_gpu_v2

Feature Group:
qoe_fg

Pipeline:
qoe_pipeline_GPU_v2

Pipeline Version:
5

Epochs:
50
```

狀態：

```text
✅ 已完成
```

---

### 1.3 Kubeflow Pipeline Run 成功建立

Training Job 105 已成功進入 Kubeflow。

```text
Kubeflow Run ID:
e1c53d0f-7f18-406c-a162-26b709e09b40
```

流程：

```text
Training Manager
   ↓
KF Adapter
   ↓
Kubeflow Pipeline
   ↓
Kubeflow Run
```

狀態：

```text
✅ 已完成
```

---

### 1.4 DNS / ImagePullBackOff 問題已處理

原本 Kubeflow Pod 無法從：

```text
quay.io
```

下載 Argo Executor Image，錯誤為：

```text
lookup quay.io on 192.168.122.1:53
i/o timeout
```

造成：

```text
Init:ImagePullBackOff
```

在 DNS / Registry Access 修復後，原本的 Pipeline 已可以繼續往下執行。

目前：

```text
root-driver = SUCCEEDED
container-driver = Completed
dag-driver = Completed
```

狀態：

```text
✅ DNS / ImagePullBackOff 問題已解除
```

---

### 1.5 kubeflow Namespace 權限已取得

原本帳號：

```text
aimlfw@example.com
```

沒有權限查看：

```text
kubeflow
```

Namespace 中的 Pod。

目前已確認：

```text
list pods = yes
get pods = yes
```

因此現在可以自行使用：

```bash
kubectl get pods
kubectl describe pod
kubectl logs
```

檢查 Kubeflow Training Pipeline。

狀態：

```text
✅ 已處理
```

---

## 2. 目前問題

### 2.1 Training Container 尚未真正啟動

目前真正執行 Model Training 的 Pod：

```text
qoe-pipeline-t77qs-system-container-impl-3369370648
```

目前狀態：

```text
READY:
0/2

STATUS:
Init:ContainerStatusUnknown
```

Pod 已排程至：

```text
Node:
aiml-z790-aorus-elite-ax-w

IP:
192.168.8.44
```

但 Training Container 尚未開始執行。

---

### 2.2 GPU Device 為 Unhealthy

目前最主要的錯誤為：

```text
UnexpectedAdmissionError
```

詳細訊息：

```text
Allocate failed due to no healthy devices present;
cannot allocate unhealthy devices nvidia.com/gpu
```

代表：

```text
Kubernetes 可以偵測到 GPU
        ↓
GPU Resource 已註冊
        ↓
但 GPU 被判定為 unhealthy
        ↓
無法配置給 Training Pod
```

目前 GPU Node 顯示：

```text
Capacity GPU:
1

Allocatable GPU:
1
```

因此 GPU 數量有成功被 Kubernetes 偵測，但目前無法正常分配給 Pod。

---

## 3. 目前 Training 狀態

目前流程位置：

```text
SMO rAPP
   ✅
   ↓
AIMLFW Training Manager
   ✅
   ↓
Training Job 105
   ✅
   ↓
KF Adapter
   ✅
   ↓
Kubeflow Pipeline
   ✅
   ↓
DNS / Image Pull
   ✅
   ↓
GPU Training Pod
   ❌ GPU unhealthy
   ↓
TensorFlow Training
   ⏳ 尚未開始
```

目前並不是模型正在訓練很久，而是：

```text
TensorFlow Training 尚未真正開始
```

---

## 4. 目前 Blocker

目前主要 Blocker：

```text
GPU Worker / NVIDIA Device 問題
```

目前錯誤：

```text
cannot allocate unhealthy devices nvidia.com/gpu
```

因此下一步需要檢查：

```text
NVIDIA Driver
NVIDIA Device Plugin
NVIDIA Container Runtime
containerd
kubelet
GPU Health Status
```

---

## 5. 下一步

目前先檢查 GPU Node：

```text
aiml-z790-aorus-elite-ax-w
192.168.8.44
```

確認 NVIDIA Device Plugin 與 GPU 狀態正常。

預期修復後，Training Pod 應由：

```text
Init:ContainerStatusUnknown
```

變成：

```text
Running
```

之後再確認 Training Log：

```text
Epoch 1/50
Epoch 2/50
...
```

直到 Kubeflow Run 最終變成：

```text
SUCCEEDED
```

再進行下一階段：

```text
確認 AIMLFW TRAINING = FINISHED
        ↓
確認 Model Artifact
        ↓
Artifact Bridge
        ↓
Model Deployment
        ↓
Inference Test
```

---

## 6. Current Status Summary

```text
rAPP → AIMLFW                    ✅
Training Job 105                ✅
KF Adapter                      ✅
Kubeflow Run                    ✅
DNS / ImagePullBackOff          ✅ 已解決
kubeflow Pod Read Permission    ✅ 已取得

GPU Resource Detected           ✅
GPU Resource Allocation         ❌
Training Container              ❌ 尚未啟動
TensorFlow Training             ⏳ 尚未開始

Current Blocker:
NVIDIA GPU is reported as unhealthy.
```
