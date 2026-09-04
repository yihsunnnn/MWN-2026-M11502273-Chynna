# AIMLFW Hands-on Testing：0904 問題追蹤與下一步

## 1. 0903 遇到的困難

0903 已確認 SMO 上的 `rapp-aiml-training` 能成功呼叫 AIMLFW Training Manager，並建立 Training Job 與 Kubeflow Pipeline Run。

```text
SMO rAPP → AIMLFW Training Manager → Training Job → KF Adapter → Kubeflow Run
   ✅              ✅                    ✅              ✅            ✅
```

Kubeflow Run ID：

```text
<kubeflow-run-id>
```

原先的 DNS 與 `ImagePullBackOff` 問題已處理，但真正執行 Model Training 的 Pod 仍無法啟動。

主要錯誤：

```text
UnexpectedAdmissionError

Allocate failed due to no healthy devices present;
cannot allocate unhealthy devices nvidia.com/gpu
```

當時的 Training Pod 狀態：

```text
READY:  0/2
STATUS: Init:ContainerStatusUnknown
```

雖然 Kubernetes 顯示 GPU Capacity 與 Allocatable 都是 `1`，但 GPU 被判定為 `unhealthy`，因此無法配置給 Training Pod。

---

## 2. 0904 目前遇到的困難

### 2.1 GPU 仍是目前主要 Blocker

0904 的首要工作是確認 0903 的 GPU unhealthy 問題是否仍然存在。目前尚未取得足以證明問題已排除的新結果，因此不能把 Training Job 視為已完成。

```text
GPU Resource Detected       ✅
GPU Resource Allocation     ❌
Training Container          ❌ 尚未確認啟動
TensorFlow Training         ⏳ 尚未確認開始
Trained Model Artifact      ⏳ 尚未產生
```

### 2.2 AIMLFW 狀態可能與 Kubeflow 實際狀態不同步

0903 查詢 AIMLFW 時，該 Training Job 長時間停留在：

```text
TRAINING = IN_PROGRESS
TRAINED_MODEL = NOT_STARTED
```

但 `IN_PROGRESS` 不代表 TensorFlow 已經開始訓練。依照 Pod 錯誤判斷，Pipeline 已建立，但 GPU Training Container 可能仍卡在啟動前。

需要分別確認：

```text
Kubeflow Run 的實際狀態
Training Pod 的實際狀態
AIMLFW 回報的 lifecycle 狀態
```

如果三者不一致，可能還存在 KF Adapter → Training Manager 的狀態回報或同步問題。

### 2.3 尚未產生 Model Artifact

該 Training Job 的欄位仍是：

```text
model_location = ""
model_url = ""
```

在 GPU Training Pod 成功執行並完成訓練前，後續的 Artifact Bridge、Model Deployment 與 Inference Test 都無法進行。

---

## 3. 0904 建議檢查步驟

### 3.1 確認 GPU Node 狀態

目標 Node：

```text
aiml-z790-aorus-elite-ax-w
<gpu-node-ip>
```

```bash
kubectl --kubeconfig /home/ubuntu/aimlfw-kubeconfig.yaml \
  get node aiml-z790-aorus-elite-ax-w -o wide

kubectl --kubeconfig /home/ubuntu/aimlfw-kubeconfig.yaml \
  describe node aiml-z790-aorus-elite-ax-w
```

重點檢查 Node 是否為 `Ready`、`nvidia.com/gpu` Capacity／Allocatable、Node Conditions，以及 Events 中是否仍有 GPU allocation error。

### 3.2 檢查 NVIDIA Device Plugin

```bash
kubectl --kubeconfig /home/ubuntu/aimlfw-kubeconfig.yaml \
  get pods -A -o wide | grep -i nvidia
```

找到 Pod 後查看狀態與紀錄：

```bash
kubectl --kubeconfig /home/ubuntu/aimlfw-kubeconfig.yaml \
  describe pod <nvidia-device-plugin-pod> -n <namespace>

kubectl --kubeconfig /home/ubuntu/aimlfw-kubeconfig.yaml \
  logs <nvidia-device-plugin-pod> -n <namespace> --tail=200
```

重點尋找：

```text
unhealthy
Xid
NVML
device discovery
allocation failed
```

### 3.3 在 GPU Node 上確認 Driver 狀態

登入 GPU Node 後執行：

```bash
nvidia-smi
```

若 `nvidia-smi` 本身失敗，應先修復 NVIDIA Driver 或 GPU 狀態，再檢查 Kubernetes。

### 3.4 重新確認 Training Pod

```bash
kubectl --kubeconfig /home/ubuntu/aimlfw-kubeconfig.yaml \
  get pods -n kubeflow -o wide
```

找到該 Training Job 對應的 Training Pod 後執行：

```bash
kubectl --kubeconfig /home/ubuntu/aimlfw-kubeconfig.yaml \
  describe pod <training-pod> -n kubeflow

kubectl --kubeconfig /home/ubuntu/aimlfw-kubeconfig.yaml \
  logs <training-pod> -n kubeflow --all-containers --tail=200
```

預期修復後應由 `Init:ContainerStatusUnknown` 變成 `Running`，並出現：

```text
Epoch 1/50
Epoch 2/50
...
```

---

## 4. 下一步應該做什麼

1. 執行 `nvidia-smi`，確認 GPU 與 NVIDIA Driver 是否正常。
2. 查看 NVIDIA Device Plugin Pod 與 log，找出 GPU 被標記為 unhealthy 的原因。
3. 查看 GPU Node Events，確認是否仍出現 `UnexpectedAdmissionError`。
4. GPU 恢復 healthy 後，重新觸發一個新的 Training Job。
5. 確認新 Training Pod 進入 `Running`，並看到 `Epoch` 訓練紀錄。
6. 確認 Kubeflow Run 最終為 `Succeeded`。
7. 再查詢 AIMLFW lifecycle 是否更新為 Training Finished。
8. 確認 `model_location` 與 `model_url` 已產生。
9. 完成後才進入 Artifact Bridge、Model Deployment 與 Inference Test。

---

## 5. 0904 Current Status Summary

```text
rAPP → AIMLFW                    ✅ 已驗證
Training Job                    ✅ 已建立
KF Adapter                      ✅ 已驗證
Kubeflow Run                    ✅ 已建立
DNS / ImagePullBackOff          ✅ 已解決

GPU Resource Detected           ✅
GPU Health                      ❌ 仍需確認與修復
GPU Resource Allocation         ❌
Training Container              ⏳ 尚未確認啟動
TensorFlow Training             ⏳ 尚未確認開始
Trained Model Artifact          ⏳ 尚未產生

Current Blocker:
NVIDIA GPU was reported as unhealthy.

Immediate Next Action:
Check nvidia-smi, NVIDIA Device Plugin logs, and GPU Node events.
```
