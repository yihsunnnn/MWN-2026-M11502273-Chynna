# AIMLFW Hands-on Testing and SMO rAPP Integration Progress

## 1. Project Objective

The purpose of this work is to verify whether the `rapp-aiml-training` deployed on the SMO can successfully trigger the O-Cloud AI/ML Framework (AIMLFW) Training Manager and start an actual Kubeflow training pipeline.

The current verification flow is:

```text
User
  ↓
SMO rAPP
  ↓
AIMLFW Training Manager
  ↓
KF Adapter
  ↓
Kubeflow Pipeline
  ↓
Model Training
```

At the current stage, an existing QoE training configuration is used first to validate the AIMLFW training workflow before integrating the CortexDC and CPU usage dataset.

---

## 2. Test Environment

### 2.1 SMO

```text
IP Address: 192.168.8.69
Host Name: zhongkui
```

The SMO Kubernetes environment was verified using:

```bash
kubectl cluster-info
kubectl get nodes
```

Verified result:

```text
Kubernetes Control Plane:
https://192.168.8.69:6443

Node:
zhongkui

Status:
Ready
```

---

### 2.2 O-Cloud AIMLFW

```text
O-Cloud IP:
192.168.8.114

AIMLFW Training Manager:
http://192.168.8.114:32002

Kubernetes API Server:
https://192.168.8.114:6443
```

The main AIMLFW components are deployed in:

```text
Namespace:
traininghost
```

---

## 3. SMO rAPP Deployment

The AI/ML training rAPP is deployed on the SMO Kubernetes cluster.

Namespace:

```text
nonrtric
```

The rAPP Pod is:

```text
rapp-aiml-training-rapp-rapp-aiml-training-chart-...
```

Service configuration:

```text
Container Port:
8000

NodePort:
31322
```

Swagger UI:

```text
http://192.168.8.69:31322/docs
```

Available APIs:

```text
GET  /
GET  /health
POST /train
GET  /train/{training_job_id}/status
```

---

## 4. Verify rAPP Health

Command:

```bash
curl -i http://192.168.8.69:31322/health
```

Response:

```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

Result:

```text
rAPP Service:
Healthy
```

This confirms that the `rapp-aiml-training` service is running normally on the SMO.

---

## 5. rAPP Source Code Structure

The rAPP source code is located at:

```text
~/joshevan/servicemanager-preload/rapp-aiml-training
```

Important files:

```text
app/
├── main.py
├── business_logic.py
├── models.py
├── config.py
└── sme_client.py
```

The current training request flow is:

```text
POST /train
   ↓
main.py
   ↓
business_logic.py
   ↓
HTTP POST
   ↓
AIMLFW Training Manager
192.168.8.114:32002
```

The rAPP sends the training request to:

```text
POST /ai-ml-model-training/v1/training-jobs
```

---

## 6. Trigger Training from SMO rAPP

The following request was sent to the rAPP:

```bash
curl -i -X POST http://192.168.8.69:31322/train \
  -H "Content-Type: application/json" \
  -d '{
    "jobName": "qoe_gpu_test",
    "modelName": "qoe_model_gpu_v2",
    "modelVersion": "1",
    "pipelineName": "qoe_pipeline_GPU_v2",
    "pipelineVersion": "5",
    "featureGroupName": "qoe_fg",
    "epochs": 50
  }'
```

Response:

```text
HTTP/1.1 201 Created
```

Response body:

```json
{
  "status": "success",
  "message": "Training job triggered successfully",
  "training_job_id": "qoe_gpu_test"
}
```

This confirms that the SMO rAPP successfully sent a training request to the AIMLFW Training Manager.

---

## 7. Training Job ID Issue Found in rAPP

The rAPP response returned:

```text
training_job_id:
qoe_gpu_test
```

However, the actual AIMLFW Training Job ID is:

```text
105
```

The current rAPP implementation extracts the job ID using:

```python
result.get("trainingjob_name", request.jobName)
```

Therefore the rAPP falls back to:

```text
qoe_gpu_test
```

which is only the request job name and not the actual AIMLFW numeric Training Job ID.

The correct Training Job created by AIMLFW is:

```text
Training Job ID:
105
```

This is one issue that should be fixed later in the rAPP implementation.

---

## 8. Verify AIMLFW Training Job 105

Command:

```bash
curl -sS \
http://192.168.8.114:32002/ai-ml-model-training/v1/training-jobs/105 \
| python3 -m json.tool
```

The Training Job information is:

```json
{
  "id": 105,
  "modelId": {
    "id": 11,
    "modelname": "qoe_model_gpu_v2",
    "modelversion": "1"
  },
  "model_location": "",
  "model_url": "",
  "training_config": {
    "dataPipeline": {
      "arguments": {
        "epochs": "50"
      },
      "feature_group_name": "qoe_fg",
      "query_filter": ""
    },
    "description": "Triggered via qoe_gpu_test",
    "trainingPipeline": {
      "retraining_pipeline_name": "qoe_pipeline_GPU_v2",
      "retraining_pipeline_version": "5",
      "training_pipeline_name": "qoe_pipeline_GPU_v2",
      "training_pipeline_version": "5"
    }
  }
}
```

Verified training configuration:

```text
Training Job ID:
105

Model:
qoe_model_gpu_v2

Model Version:
1

Feature Group:
qoe_fg

Training Pipeline:
qoe_pipeline_GPU_v2

Pipeline Version:
5

Epochs:
50
```

This confirms that the rAPP-created request was correctly registered in AIMLFW.

---

## 9. Check AIMLFW Training Status

The actual AIMLFW lifecycle status endpoint is:

```text
GET /ai-ml-model-training/v1/training-jobs/{id}/status
```

Command:

```bash
curl -sS \
http://192.168.8.114:32002/ai-ml-model-training/v1/training-jobs/105/status \
| python3 -m json.tool
```

Observed result:

```json
{
  "DATA_EXTRACTION": "FINISHED",
  "DATA_EXTRACTION_AND_TRAINING": "FINISHED",
  "TRAINED_MODEL": "NOT_STARTED",
  "TRAINING": "IN_PROGRESS",
  "TRAINING_AND_TRAINED_MODEL": "NOT_STARTED"
}
```

Current lifecycle:

```text
DATA_EXTRACTION
    ✅ FINISHED

TRAINING
    ⚠ IN_PROGRESS

TRAINED_MODEL
    ⏳ NOT_STARTED
```

The training status remained at:

```text
TRAINING = IN_PROGRESS
```

for a long period, so further investigation was required.

---

## 10. rAPP Training Status API Issue

The current rAPP provides:

```text
GET /train/{training_job_id}/status
```

For example:

```bash
curl -sS \
http://192.168.8.69:31322/train/105/status \
| python3 -m json.tool
```

However, the current implementation queries:

```text
GET /training-jobs/{id}
```

instead of:

```text
GET /training-jobs/{id}/status
```

Therefore the current rAPP `/status` endpoint returns Training Job metadata rather than the real lifecycle status.

This is another issue that should be fixed later.

---

## 11. Obtain O-Cloud kubeconfig Access

A dedicated O-Cloud AIMLFW kubeconfig was obtained:

```text
aimlfw-kubeconfig.yaml
```

The kubeconfig points to:

```text
https://192.168.8.114:6443
```

The file was transferred to the SMO host:

```text
/home/ubuntu/aimlfw-kubeconfig.yaml
```

Example usage:

```bash
kubectl \
  --kubeconfig /home/ubuntu/aimlfw-kubeconfig.yaml \
  get nodes -o wide
```

---

## 12. Verify O-Cloud Kubernetes Nodes

The O-Cloud cluster was successfully accessed using the new kubeconfig.

Observed nodes included:

```text
aiml-z790-aorus-elite-ax-w
lavoisier
o-cloud-master
worker-nonrt-00
```

Observed status:

```text
Ready
```

Important O-Cloud nodes:

```text
o-cloud-master
Internal IP: 192.168.8.114

worker-nonrt-00
Internal IP: 192.168.8.74
```

This confirms that the kubeconfig successfully provides access to the O-Cloud Kubernetes cluster.

---

## 13. Verify AIMLFW Pods

Command:

```bash
kubectl \
  --kubeconfig /home/ubuntu/aimlfw-kubeconfig.yaml \
  get pods -n traininghost -o wide
```

Observed AIMLFW components:

```text
aiml-dashboard
aiml-notebook
aimlfw-intent-consumer
cassandra-0
data-extraction
kfadapter
modelmgmtservice
mv-release-influxdb
tm
tm-db-postgresql
```

All major AIMLFW components were:

```text
Running
```

Therefore the Training Manager and core AIMLFW services were not down.

---

## 14. Kubernetes RBAC Permission Check

The current kubeconfig cannot list Pods across all namespaces.

Command:

```bash
kubectl \
  --kubeconfig /home/ubuntu/aimlfw-kubeconfig.yaml \
  get pods -A
```

Result:

```text
Forbidden
```

The current Kubernetes user is:

```text
aimlfw@example.com
```

The account does not have cluster-wide permission to list Pods.

However, it has strong permissions in:

```text
traininghost
```

Permission check:

```bash
kubectl \
  --kubeconfig /home/ubuntu/aimlfw-kubeconfig.yaml \
  auth can-i --list -n traininghost
```

The account has broad permissions inside `traininghost`.

Because this is a shared environment, only read-only commands were intentionally used during debugging.

---

## 15. Training Manager Deployment Investigation

Command:

```bash
kubectl \
  --kubeconfig /home/ubuntu/aimlfw-kubeconfig.yaml \
  describe deployment tm -n traininghost
```

The Training Manager container uses configuration from:

```text
tm-configmap
```

and also mounts:

```text
tm-agent-patch
```

The patch replaces:

```text
/usr/local/lib/python3.10/site-packages/trainingmgr/service/agent_service.py
```

This indicates that the Training Manager has a customized agent implementation.

---

## 16. Training Manager ConfigMap

Command:

```bash
kubectl \
  --kubeconfig /home/ubuntu/aimlfw-kubeconfig.yaml \
  get configmap tm-configmap -n traininghost -o yaml
```

Important configuration:

```text
KF_ADAPTER_IP:
kfadapter.traininghost

KF_ADAPTER_PORT:
5001
```

Other important services include:

```text
DATA_EXTRACTION_API_IP:
data-extraction.traininghost

DATA_EXTRACTION_API_PORT:
32000

MODEL_MANAGEMENT_SERVICE_IP:
modelmgmtservice.traininghost

MODEL_MANAGEMENT_SERVICE_PORT:
8082

TRAINING_MANAGER_IP:
tm.traininghost

TRAINING_MANAGER_PORT:
32000
```

Therefore, the actual AIMLFW training flow includes:

```text
Training Manager
      ↓
KF Adapter
kfadapter.traininghost:5001
```

---

## 17. Verify KF Adapter Service

Command:

```bash
kubectl \
  --kubeconfig /home/ubuntu/aimlfw-kubeconfig.yaml \
  get svc kfadapter -n traininghost -o wide
```

Observed result:

```text
Service:
kfadapter

Type:
ClusterIP

Cluster IP:
10.107.57.75

Port:
5001/TCP
```

Endpoint check:

```bash
kubectl \
  --kubeconfig /home/ubuntu/aimlfw-kubeconfig.yaml \
  get endpoints kfadapter -n traininghost -o wide
```

Observed endpoint:

```text
10.0.6.252:5001
```

Therefore:

```text
Training Manager
      ↓
kfadapter.traininghost:5001
      ↓
Service 10.107.57.75:5001
      ↓
Pod 10.0.6.252:5001
```

The KF Adapter Service routing is correctly configured.

---

## 18. KF Adapter Deployment

Command:

```bash
kubectl \
  --kubeconfig /home/ubuntu/aimlfw-kubeconfig.yaml \
  describe deployment kfadapter -n traininghost
```

The KF Adapter container executes:

```text
python3
kfadapter_main.py
```

The configuration is loaded from:

```text
kfadapter-configmap
```

---

## 19. KF Adapter ConfigMap

Command:

```bash
kubectl \
  --kubeconfig /home/ubuntu/aimlfw-kubeconfig.yaml \
  get configmap kfadapter-configmap -n traininghost -o yaml
```

Important configuration:

```text
KF_ADAPTER_PORT:
5001

KF_NAMESPACE:
ric

KUBEFLOW_HOST:
ml-pipeline-ui.kubeflow

KUBEFLOW_PORT:
80

TRAININGMGR_HOST:
tm.traininghost

TRAININGMGR_PORT:
32002
```

Therefore the architecture is:

```text
SMO rAPP
   ↓
Training Manager
tm.traininghost
   ↓
KF Adapter
kfadapter.traininghost:5001
   ↓
Kubeflow Pipeline API
ml-pipeline-ui.kubeflow:80
```

---

## 20. Investigate KF_NAMESPACE

The KF Adapter ConfigMap contains:

```text
KF_NAMESPACE = ric
```

The source code reads this value using:

```python
self.kf_dict['kfdefaultns'] = getenv('KF_NAMESPACE')
```

The source code documentation indicates that this parameter represents the namespace in which the pipeline is associated or executed.

However, checking the namespace:

```bash
kubectl \
  --kubeconfig /home/ubuntu/aimlfw-kubeconfig.yaml \
  get namespace ric
```

returned:

```text
Error from server (NotFound):
namespaces "ric" not found
```

Initially this was suspected as a possible cause of the training issue.

However, later KF Adapter execution logs showed:

```text
namespace: None
```

and the actual Kubeflow Pipeline Run was successfully created.

Therefore:

```text
KF_NAMESPACE = ric
```

is still an unusual configuration item but is currently not confirmed as the direct cause of Job 105 remaining in `IN_PROGRESS`.

No namespace was created and no ConfigMap was modified.

---

## 21. Inspect KF Adapter Source Code

The KF Adapter source is located inside the container at:

```text
/home/app/kfadapter/
```

Important files include:

```text
kfadapter_conf.py
kfadapter_kfconnect.py
kfadapter_main.py
kfadapter_util.py
```

The configuration code contains:

```python
self.kf_dict['kfhostname'] = getenv('KUBEFLOW_HOST')
self.kf_dict['kfport'] = getenv('KUBEFLOW_PORT')
self.kf_dict['kfdefaultns'] = getenv('KF_NAMESPACE')
self.appport = getenv('KF_ADAPTER_PORT')
```

The value `kfdefaultns` is then passed to Kubeflow-related functions such as:

```python
get_kf_experiment_details(...)
```

```python
get_kf_list_experiments(...)
```

and:

```python
get_kf_list_runs(...)
```

This confirms that the KF Adapter directly communicates with Kubeflow.

---

## 22. KF Adapter Log Location

Normal:

```bash
kubectl logs
```

did not show useful KF Adapter logs.

Further investigation showed that the KF Adapter writes logs directly into:

```text
/home/app/kfadapter/kfconnector.log
```

Command:

```bash
kubectl \
  --kubeconfig /home/ubuntu/aimlfw-kubeconfig.yaml \
  exec -n traininghost deploy/kfadapter -- \
  sh -c 'ls -lh /home/app/kfadapter/*.log'
```

Observed:

```text
/home/app/kfadapter/kfconnector.log
```

Therefore debugging was continued using this file.

---

## 23. Confirm Job 105 Reached KF Adapter

The KF Adapter log contains:

```text
run_pipeline for 105
```

The request received by KF Adapter includes:

```text
pipeline_name:
qoe_pipeline_GPU_v2

experiment_name:
Default

epochs:
50

trainingjob_id:
105

featuregroup_name:
qoe_fg

modelName:
qoe_model_gpu_v2

modelVersion:
1

pipelineVersion:
5
```

This confirms:

```text
Training Manager
      ↓
KF Adapter
```

successfully processed Training Job 105.

---

## 24. Confirm Job 105 Triggered Kubeflow Pipeline

The KF Adapter log contains:

```text
Running pipeline
```

followed by:

```text
run_kf_pipeline Entered
```

Arguments passed to Kubeflow:

```text
featurepath:
qoe_fg_105

epochs:
50

modelname:
qoe_model_gpu_v2

modelversion:
1
```

The function then completed:

```text
run_kf_pipeline Exited
```

This confirms that the KF Adapter successfully called the Kubeflow Pipeline API.

---

## 25. Identify Kubeflow Pipeline ID

The KF Adapter log shows:

```text
Pipeline ID:
196dfd1e-6aa4-4068-a154-de5c014fe5c9
```

This corresponds to:

```text
qoe_pipeline_GPU_v2
```

---

## 26. Identify Pipeline Version ID

The log also shows:

```text
Pipeline Version ID:
10822233-2539-44f4-965c-f5d208c10f23
```

This corresponds to the pipeline version used by Job 105.

---

## 27. Identify Kubeflow Run ID

The most important result obtained from the KF Adapter log is:

```text
Kubeflow Run ID:
e1c53d0f-7f18-406c-a162-26b709e09b40
```

The complete Job 105 execution sequence is:

```text
run_pipeline for 105
        ↓
Get Experiment Details
        ↓
Get Pipeline ID
        ↓
Get Pipeline Version ID
        ↓
Running pipeline
        ↓
run_kf_pipeline Entered
        ↓
run_kf_pipeline Exited
        ↓
Run ID generated
```

Kubeflow Run ID:

```text
e1c53d0f-7f18-406c-a162-26b709e09b40
```

The KF Adapter also reported:

```text
POST /trainingjobs/105/execution HTTP/1.1 200
```

Therefore the Kubeflow Pipeline Run was successfully created.

---

## 28. Verified End-to-End Training Trigger Path

At this point, the following path has been verified:

```text
SMO rAPP
    ↓
AIMLFW Training Manager
    ↓
Training Job 105
    ↓
KF Adapter
    ↓
qoe_pipeline_GPU_v2
    ↓
Kubeflow Pipeline Run
```

Verified identifiers:

```text
Training Job ID:
105

Pipeline:
qoe_pipeline_GPU_v2

Pipeline ID:
196dfd1e-6aa4-4068-a154-de5c014fe5c9

Pipeline Version:
5

Pipeline Version ID:
10822233-2539-44f4-965c-f5d208c10f23

Kubeflow Run ID:
e1c53d0f-7f18-406c-a162-26b709e09b40
```

---

## 29. Current Training Status

Despite the successful creation of a Kubeflow Run, AIMLFW still reports:

```json
{
  "DATA_EXTRACTION": "FINISHED",
  "DATA_EXTRACTION_AND_TRAINING": "FINISHED",
  "TRAINED_MODEL": "NOT_STARTED",
  "TRAINING": "IN_PROGRESS",
  "TRAINING_AND_TRAINED_MODEL": "NOT_STARTED"
}
```

Therefore:

```text
Kubeflow Run creation:
✅ SUCCESS

AIMLFW Training lifecycle:
⚠ TRAINING = IN_PROGRESS

Trained Model:
⏳ NOT_STARTED
```

The actual Kubeflow Run status still needs to be checked.

---

## 30. Current Model Artifact Status

Training Job metadata currently shows:

```text
model_location = ""
model_url = ""
```

This means that the final trained model artifact has not yet been confirmed.

The next objective is to determine whether:

```text
Kubeflow Run
```

is:

```text
Running
Succeeded
Failed
Error
```

---

## 31. Possible Status Synchronization Issue

Older KF Adapter logs showed entries related to previous jobs such as:

```text
pipelineNotification
```

and:

```text
Response [500]
```

This suggests that there may be a status synchronization problem between:

```text
Kubeflow
   ↓
KF Adapter
   ↓
Training Manager
```

A possible scenario is:

```text
Kubeflow Pipeline finishes
        ↓
KF Adapter sends status notification
        ↓
Training Manager notification fails
        ↓
AIMLFW Training Job remains IN_PROGRESS
```

However, this has not yet been confirmed for Job 105.

Further investigation is required.

---

## 32. Current Progress Summary

| Item | Status |
|---|---|
| Connect to SMO Kubernetes | ✅ Done |
| Verify `rapp-aiml-training` deployment | ✅ Done |
| Verify rAPP `/health` | ✅ Done |
| Trigger training through SMO rAPP | ✅ Done |
| Create AIMLFW Training Job | ✅ Done |
| Identify actual AIMLFW Training Job ID | ✅ Job 105 |
| Verify Training Job configuration | ✅ Done |
| Verify Data Extraction | ✅ FINISHED |
| Obtain O-Cloud kubeconfig | ✅ Done |
| Access O-Cloud Kubernetes | ✅ Done |
| Verify O-Cloud nodes | ✅ Ready |
| Verify AIMLFW Pods | ✅ Running |
| Verify Training Manager | ✅ Running |
| Verify KF Adapter | ✅ Running |
| Identify TM → KF Adapter configuration | ✅ Done |
| Verify KF Adapter Service | ✅ Done |
| Identify KF Adapter → Kubeflow endpoint | ✅ Done |
| Inspect KF Adapter source code | ✅ Done |
| Locate KF Adapter logs | ✅ Done |
| Confirm Job 105 reached KF Adapter | ✅ Done |
| Confirm Kubeflow Pipeline was triggered | ✅ Done |
| Identify Pipeline ID | ✅ Done |
| Identify Pipeline Version ID | ✅ Done |
| Identify Kubeflow Run ID | ✅ Done |
| Confirm actual Kubeflow Run status | ⏳ Pending |
| Confirm AIMLFW Training completion | ⏳ Pending |
| Confirm trained model artifact | ⏳ Pending |
| Bridge model artifact to SMO MinIO | ⏳ Not started |
| Deploy through ONAP ACM | ⏳ Not started |
| Verify KServe InferenceService | ⏳ Not started |
| Test online inference | ⏳ Not started |
| Integrate CortexDC dataset | ⏳ Future work |
| Integrate CPU usage dataset | ⏳ Future work |

---

## 33. Known rAPP Issue 1: Incorrect Training Job ID

Current response:

```text
training_job_id:
qoe_gpu_test
```

Expected:

```text
training_job_id:
105
```

Current implementation:

```python
job_id = result.get("trainingjob_name", request.jobName)
```

A possible improved implementation is:

```python
job_id = (
    result.get("trainingJobId")
    or result.get("id")
    or result.get("trainingjob_name")
    or request.jobName
)
```

This should be verified against the actual Training Manager POST response before applying the change.

---

## 34. Known rAPP Issue 2: Incorrect Status Endpoint

Current implementation queries:

```text
GET /training-jobs/{id}
```

This endpoint returns Training Job metadata.

The actual training lifecycle endpoint is:

```text
GET /training-jobs/{id}/status
```

Therefore the current rAPP status function should eventually be changed from:

```python
endpoint = (
    f"{tm_url}/ai-ml-model-training/v1/"
    f"training-jobs/{training_job_id}"
)
```

to:

```python
endpoint = (
    f"{tm_url}/ai-ml-model-training/v1/"
    f"training-jobs/{training_job_id}/status"
)
```

This change has not yet been applied.

---

## 35. Current Architecture

```text
                          User
                            │
                            │ POST /train
                            ▼
                  SMO rapp-aiml-training
                       192.168.8.69
                       NodePort 31322
                            │
                            │ REST API
                            ▼
                AIMLFW Training Manager
                       tm.traininghost
                  192.168.8.114:32002
                            │
                            │ Training Job 105
                            ▼
                       KF Adapter
               kfadapter.traininghost:5001
                            │
                            │ Kubeflow Pipeline API
                            ▼
                ml-pipeline-ui.kubeflow:80
                            │
                            ▼
                  qoe_pipeline_GPU_v2
                         Version 5
                            │
                            ▼
                    Kubeflow Run

Training Job ID:
105

Pipeline ID:
196dfd1e-6aa4-4068-a154-de5c014fe5c9

Pipeline Version ID:
10822233-2539-44f4-965c-f5d208c10f23

Kubeflow Run ID:
e1c53d0f-7f18-406c-a162-26b709e09b40

Current AIMLFW Status:
TRAINING = IN_PROGRESS
```

---

## 36. Safety Notes

The O-Cloud and SMO environments are shared lab environments.

During this investigation, only read-oriented debugging operations were intentionally used, including:

```text
kubectl get
kubectl describe
kubectl logs
kubectl exec with grep / cat / ls
kubectl auth can-i
curl GET
```

No shared resource was intentionally modified using:

```text
kubectl delete
kubectl edit
kubectl patch
kubectl apply
kubectl scale
kubectl rollout restart
```

The existing QoE model, feature group, pipeline, and other shared resources were not intentionally modified.

---

## 37. kubeconfig Security

The following file contains Kubernetes authentication information:

```text
aimlfw-kubeconfig.yaml
```

This file should NOT be committed to GitHub.

Recommended `.gitignore`:

```gitignore
# Kubernetes credentials
*kubeconfig*
*.kubeconfig
aimlfw-kubeconfig.yaml
```

Passwords, tokens, certificates, and kubeconfig contents should never be uploaded to the repository.

---

## 38. Current Conclusion

The AIMLFW hands-on test has successfully verified that the SMO `rapp-aiml-training` can trigger a real training workflow on the O-Cloud AIMLFW environment.

The following path has been experimentally verified:

```text
SMO rAPP
→ AIMLFW Training Manager
→ Training Job
→ KF Adapter
→ Kubeflow Pipeline
→ Kubeflow Run
```

The actual Training Job created by the test is:

```text
Training Job ID:
105
```

and the actual Kubeflow execution is:

```text
Run ID:
e1c53d0f-7f18-406c-a162-26b709e09b40
```

Therefore, the current result proves that the rAPP is not only able to communicate with the Training Manager, but can also cause AIMLFW to create an actual Kubeflow Pipeline Run.

The remaining work is to verify the final Kubeflow Run status, determine why AIMLFW continues to report:

```text
TRAINING = IN_PROGRESS
```

and confirm whether the trained model artifact is eventually generated.

---

## 39. Next Steps

The next investigation will focus on:

1. Check the actual status of Kubeflow Run:

```text
e1c53d0f-7f18-406c-a162-26b709e09b40
```

2. Determine whether the Run is:

```text
Running
Succeeded
Failed
Error
```

3. Compare the real Kubeflow state with:

```text
AIMLFW:
TRAINING = IN_PROGRESS
```

4. Investigate KF Adapter → Training Manager status notification if the two states are inconsistent.

5. Confirm whether:

```text
model_url
model_location
```

are populated after training.

6. After successful training, evaluate the model artifact bridge to SMO MinIO.

7. Later integrate the user's own:

```text
CortexDC server data
+
CPU usage data
```

into the AIMLFW training workflow.

---

## 40. Final Progress Status

```text
AIMLFW Hands-on Testing
        │
        ├── SMO rAPP Deployment              ✅
        ├── rAPP Health Check                ✅
        ├── rAPP → Training Manager          ✅
        ├── Training Job Creation            ✅
        ├── Job 105 Identification           ✅
        ├── O-Cloud kubeconfig Access        ✅
        ├── AIMLFW Service Health            ✅
        ├── Training Manager Investigation   ✅
        ├── KF Adapter Investigation         ✅
        ├── Kubeflow Pipeline Trigger        ✅
        ├── Pipeline ID Identification       ✅
        ├── Kubeflow Run ID Identification  ✅
        ├── Kubeflow Final Run Status        ⏳
        ├── Trained Model Artifact           ⏳
        ├── Artifact Bridge                  ⏳
        ├── KServe Deployment                ⏳
        └── CortexDC + CPU Data Integration  ⏳
```
