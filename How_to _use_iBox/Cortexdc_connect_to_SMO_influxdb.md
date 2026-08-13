# Study Note：CortexDC 資料串接至 SMO InfluxDB

## 1. 目標

本次工作的目標為將原本儲存在 CortexDC VM InfluxDB 中的伺服器監控資料，自動同步至 SMO 內的 InfluxDB，供後續 rAPP、AI/ML Training 或其他 SMO 元件使用。

整體資料流如下：

```text
CortexDC
192.168.10.76
      │
      │ REST API
      ▼
srsric VM
192.168.8.48
      │
      ├─ cortexdc-collector.service
      │
      ▼
Local InfluxDB
http://localhost:8086
Org    : bmwlab
Bucket : cortexdc_server
      │
      │ cortexdc-smo-bridge.service
      │ 每 60 秒自動同步
      ▼
SMO
192.168.8.69
      │
      ▼
SMO InfluxDB
http://192.168.8.69:30138
Org    : ravi-ric
Bucket : cortexdc-server
```

---

## 2. SMO InfluxDB 環境確認

登入 SMO：

```bash
ssh ubuntu@192.168.8.69
```

確認 Kubernetes 中的 InfluxDB Pod：

```bash
kubectl get pods -A | grep -i influx
```

找到：

```text
smo    influxdb2-0    1/1    Running
```

確認 Service：

```bash
kubectl get svc -n smo | grep -i influx
```

結果：

```text
influxdb2    NodePort    10.98.20.12    <none>    8086:30138/TCP
```

因此：

```text
Kubernetes 內部：
http://10.98.20.12:8086

SMO 外部 NodePort：
http://192.168.8.69:30138
```

---

## 3. SMO InfluxDB Health Check

測試 NodePort：

```bash
curl http://localhost:30138/health
```

以及：

```bash
curl http://10.98.20.12:8086/health
```

結果：

```json
{
  "name": "influxdb",
  "message": "ready for queries and writes",
  "status": "pass",
  "version": "v2.7.12"
}
```

確認 SMO InfluxDB 正常運作。

---

## 4. SMO InfluxDB Organization 與 Bucket

利用既有 API Token：

```bash
TOKEN=$(kubectl get secret influxdb-api-token -n smo \
-o jsonpath='{.data.token}' | base64 -d)
```

查詢 Organization：

```bash
curl -s \
  -H "Authorization: Token $TOKEN" \
  http://localhost:30138/api/v2/orgs \
  | python3 -m json.tool
```

取得：

```text
Organization : ravi-ric
Org ID       : dc668a9e4792993e
```

查詢現有 Bucket：

```bash
curl -s \
  -H "Authorization: Token $TOKEN" \
  "http://localhost:30138/api/v2/buckets?limit=100" \
  | python3 -m json.tool
```

原本已有：

```text
_monitoring
_tasks
ran-pm-metrics
infra-telemetry
```

`infra-telemetry` 已包含：

```text
ocloud_cpu
ocloud_cstate
ocloud_freq
ocloud_membw
ocloud_perf
ocloud_power
ocloud_thermal
```

為避免 CortexDC 資料與原本 O-Cloud telemetry 混在一起，因此建立獨立 Bucket。

---

## 5. 建立 CortexDC 專用 Bucket

建立：

```text
cortexdc-server
```

執行：

```bash
curl -s \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json" \
  -X POST \
  http://localhost:30138/api/v2/buckets \
  --data '{
    "orgID": "dc668a9e4792993e",
    "name": "cortexdc-server",
    "retentionRules": []
  }' \
  | python3 -m json.tool
```

結果：

```text
Bucket    : cortexdc-server
Bucket ID : 1c7a265b8fe78de7
```

`retentionRules: []` 表示目前不設定自動刪除期限。

---

## 6. SMO 寫入測試

先寫入一筆測試資料：

```bash
curl -i \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: text/plain; charset=utf-8" \
  -X POST \
  "http://localhost:30138/api/v2/write?org=ravi-ric&bucket=cortexdc-server&precision=s" \
  --data-binary \
  'server_temperature,server_name=Lavoisier,sensor_name=CPU\ Temp temperature_c=50.0'
```

成功時：

```text
HTTP/1.1 204 No Content
```

再利用 Flux 查詢確認：

```bash
curl -s \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/vnd.flux" \
  -H "Accept: application/csv" \
  -X POST \
  "http://localhost:30138/api/v2/query?org=ravi-ric" \
  --data 'from(bucket: "cortexdc-server")
    |> range(start: -10m)
    |> filter(fn: (r) => r["_measurement"] == "server_temperature")'
```

成功查到：

```text
server_name  = Lavoisier
sensor_name  = CPU Temp
_field       = temperature_c
_value       = 50
```

---

## 7. CortexDC Source VM

CortexDC 原始資料收集 VM：

```text
VM      : srsric
IP      : 192.168.8.48
OS      : Ubuntu 22.04
```

登入：

```bash
ssh srsric@192.168.8.48
```

Local InfluxDB：

```text
URL    : http://localhost:8086
Org    : bmwlab
Bucket : cortexdc_server
```

確認：

```bash
curl http://localhost:8086/health
```

結果：

```text
status = pass
InfluxDB version = 2.9.1
```

原有 CortexDC Collector：

```bash
sudo systemctl status cortexdc-collector --no-pager
```

結果：

```text
Active: active (running)
```

---

## 8. 確認 Source VM 可連 SMO

在 `srsric VM` 執行：

```bash
curl http://192.168.8.69:30138/health
```

成功：

```text
status = pass
```

因此確認：

```text
srsric VM
192.168.8.48
      │
      │ Network reachable
      ▼
SMO InfluxDB
192.168.8.69:30138
```

---

## 9. 建立 Bridge 專用 Token

為避免使用 SMO 的 Admin Token，建立一組只允許操作 `cortexdc-server` 的 Token。

Authorization：

```text
Description : cortexdc-to-smo-bridge
Bucket      : cortexdc-server
Permission  :
  - read
  - write
```

Token 檔案由 SMO 複製到 Source VM：

```bash
scp ubuntu@192.168.8.69:~/cortexdc_bridge_token \
~/cortexdc_collector/smo_token
```

限制權限：

```bash
chmod 600 ~/cortexdc_collector/smo_token
```

因此 Bridge Token 無法操作：

```text
ran-pm-metrics
infra-telemetry
其他 SMO Bucket
```

---

## 10. CortexDC → SMO Bridge

建立：

```text
~/cortexdc_collector/cortexdc_to_smo.py
```

主要工作：

```text
Source:
http://localhost:8086
bmwlab
cortexdc_server

        ↓

讀取 CortexDC records

        ↓

保留：
_time
_measurement
_field
_value
server_name
sensor_name
sensor_type
asset_id
brand
health
ip_address
model
physical_context
rack_id
...

        ↓

Destination:
http://192.168.8.69:30138
ravi-ric
cortexdc-server
```

第一次測試結果：

```text
Read 958 records from CortexDC.
Wrote 958 records to SMO successfully.
```

表示 CortexDC 真實資料已成功寫入 SMO。

---

## 11. 自動增量同步

Bridge 後續改為每 60 秒自動同步。

使用 Checkpoint：

```text
~/cortexdc_collector/last_sync_time.txt
```

概念：

```text
第一次：
抓最近 10 分鐘

後續：
以上次 checkpoint 為基準
+
往前保留 5 分鐘 safety overlap
```

Safety overlap 的目的為避免 CortexDC 資料延遲寫入造成漏資料。

例如：

```text
上次 checkpoint = 18:00

下一輪：
查詢 17:55 ～ 18:01
```

相同：

```text
measurement
tags
field
timestamp
```

的 Point 會寫回相同時間序列位置，因此不會因 overlap 產生新的 timestamp 資料。

---

## 12. systemd 自動服務

建立：

```text
/etc/systemd/system/cortexdc-smo-bridge.service
```

內容：

```ini
[Unit]
Description=CortexDC to SMO InfluxDB Bridge
After=network-online.target influxdb.service
Wants=network-online.target

[Service]
Type=simple
User=srsric
WorkingDirectory=/home/srsric/cortexdc_collector

ExecStart=/home/srsric/cortexdc_collector/venv/bin/python3 -u /home/srsric/cortexdc_collector/cortexdc_to_smo.py

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

啟動：

```bash
sudo systemctl daemon-reload
sudo systemctl enable cortexdc-smo-bridge
sudo systemctl restart cortexdc-smo-bridge
```

確認：

```bash
sudo systemctl status cortexdc-smo-bridge --no-pager
```

結果：

```text
Active: active (running)
Loaded: enabled
```

---

## 13. 查看同步 Log

```bash
sudo journalctl -u cortexdc-smo-bridge -f
```

實際結果例如：

```text
Read 876 records from CortexDC.
Wrote 876 records to SMO successfully.
Checkpoint updated.

Read 812 records from CortexDC.
Wrote 812 records to SMO successfully.
Checkpoint updated.

Read 796 records from CortexDC.
Wrote 796 records to SMO successfully.
Checkpoint updated.
```

表示每分鐘同步正常執行。

`Ctrl + C` 只會離開 Log，不會停止 Service。

---

## 14. 目前成功同步的 Measurement

查詢：

```flux
import "influxdata/influxdb/schema"

schema.measurements(
    bucket: "cortexdc-server",
    start: -24h
)
```

確認 SMO 中包含：

```text
server_cpu
server_fan
server_power
server_temperature
```

---

## 15. 最近 24 小時已確認的 Field

### server_temperature

```text
temperature_c
health_score
lower_threshold_critical
upper_threshold_critical
upper_threshold_fatal
```

其中：

```text
temperature_c              : 33,536 records
health_score               : 33,536 records
lower_threshold_critical   : 22,817 records
upper_threshold_critical   : 31,784 records
upper_threshold_fatal      : 16,462 records
```

---

### server_fan

```text
fan_rpm
health_score
```

其中：

```text
fan_rpm       : 14,107 records
health_score  : 14,107 records
```

---

### server_power

目前確認：

```text
average_consumed_watts
max_consumed_watts
min_consumed_watts
power_consumed_watts
power_available_watts
power_capacity_watts
power_limit_watts
```

例如：

```text
average_consumed_watts : 2,553 records
max_consumed_watts     : 2,553 records
min_consumed_watts     : 2,553 records
power_consumed_watts   : 2,553 records
power_available_watts  : 850 records
power_capacity_watts   : 2,260 records
power_limit_watts      : 850 records
```

---

### server_cpu

目前確認：

```text
max_speed_mhz
total_cores
total_threads
```

各約：

```text
48 records
```

目前 `server_cpu` 中尚未看到：

```text
CPU Usage %
CPU Utilization
```

因此目前 CortexDC 的 `server_cpu` 主要為 CPU hardware information，而非即時 CPU utilization。

---

## 16. 已確認的 Temperature Sensor 範例

例如 Lavoisier 已成功同步：

```text
CPU Temp
CPU_VRMHV Temp
CPU_VRMIN Temp
CPU_VRMON Temp
Memory Temp
PCH Temp
Peripheral Temp
System Temp
```

資料格式例如：

```text
_measurement = server_temperature
_field       = temperature_c
server_name  = Lavoisier
sensor_name  = CPU Temp
_value       = 36
```

---

## 17. 目前兩個 Service 的角色

### cortexdc-collector.service

```text
CortexDC
   ↓
Local InfluxDB
```

負責：

```text
CortexDC → srsric VM InfluxDB
```

---

### cortexdc-smo-bridge.service

```text
Local InfluxDB
   ↓
SMO InfluxDB
```

負責：

```text
srsric VM → SMO
```

兩個 Service 為獨立運作。

因此即使 SMO 暫時無法連線：

```text
CortexDC → Local InfluxDB
```

仍可以繼續收集資料。

---

## 18. 常用指令

查看 CortexDC Collector：

```bash
sudo systemctl status cortexdc-collector --no-pager
```

查看 Bridge：

```bash
sudo systemctl status cortexdc-smo-bridge --no-pager
```

查看即時 Bridge Log：

```bash
sudo journalctl -u cortexdc-smo-bridge -f
```

重新啟動 Bridge：

```bash
sudo systemctl restart cortexdc-smo-bridge
```

停止 Bridge：

```bash
sudo systemctl stop cortexdc-smo-bridge
```

查看 Checkpoint：

```bash
cat ~/cortexdc_collector/last_sync_time.txt
```

確認 SMO Health：

```bash
curl http://192.168.8.69:30138/health
```

---

## 19. 最終結果

目前已完成：

```text
✅ CortexDC 原始資料收集
✅ Local InfluxDB
✅ SMO InfluxDB 建立 cortexdc-server Bucket
✅ SMO 專用 Bridge Token
✅ CortexDC → SMO 真實資料傳輸
✅ Timestamp / Measurement / Field / Tag 保留
✅ 每 60 秒自動同步
✅ 5 分鐘 Safety Overlap
✅ Checkpoint 增量同步
✅ systemd 開機自動執行
✅ server_temperature 同步
✅ server_fan 同步
✅ server_power 同步
✅ server_cpu 同步
```

目前完整資料鏈：

```text
CortexDC
   ↓
CortexDC Collector
   ↓
Local InfluxDB
   ↓
CortexDC-to-SMO Bridge
   ↓
SMO InfluxDB
   ↓
cortexdc-server
   ↓
Future:
ES rAPP / Training rAPP / AI Model
```

此架構可作為後續 O-RAN / O-Cloud server telemetry 與 AI/ML 應用整合之資料來源。
