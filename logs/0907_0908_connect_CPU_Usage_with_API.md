# Lavoisier CPU Usage Collection to SMO InfluxDB

## 1. Purpose

This document records how to collect the CPU usage of the **Lavoisier server (`192.168.8.82`)** and send the data to the **InfluxDB inside the SMO**.

The CPU usage data is collected directly from the Linux server and written to the SMO InfluxDB through the InfluxDB HTTP API.

The current architecture is:

```text
Lavoisier Server
192.168.8.82
      │
      │ Read CPU Usage
      ▼
cpu_usage_collector.py
      │
      │ InfluxDB Write API
      ▼
SMO InfluxDB
192.168.8.69:30138
      │
      ▼
Bucket: cortexdc-server
Measurement: server_cpu_usage
Field: cpu_usage_percent
```

The CPU Usage data can later be combined with CortexDC telemetry data:

```text
CortexDC
   │
   │ REST API
   ▼
CortexDC Collector
   ▼
Local InfluxDB
   │
   │ Bridge
   ▼
SMO InfluxDB
   ▲
   │
CPU Usage Collector
   ▲
   │
Lavoisier
```

---

## 2. Server Information

CPU Usage source server:

```text
Hostname: Lavoisier
IP: 192.168.8.82
User: oai72_su
```

SMO InfluxDB:

```text
SMO IP: 192.168.8.69
InfluxDB Port: 30138
Organization: ravi-ric
Bucket: cortexdc-server
```

CPU Usage data format:

```text
Measurement:
server_cpu_usage

Tag:
server_name=Lavoisier

Field:
cpu_usage_percent
```

Example:

```text
server_cpu_usage,server_name=Lavoisier cpu_usage_percent=3.81
```

---

## 3. Step 1 - Connect to Lavoisier

Connect to the server:

```bash
ssh oai72_su@192.168.8.82
```

Check hostname:

```bash
hostname
```

Expected result:

```text
Lavoisier
```

Check server IP:

```bash
hostname -I
```

Example result:

```text
192.168.8.82 192.168.8.83 ...
```

---

## 4. Step 2 - Test Connection to SMO InfluxDB

Run:

```bash
curl http://192.168.8.69:30138/health
```

Successful result:

```json
{
  "name": "influxdb",
  "message": "ready for queries and writes",
  "status": "pass",
  "version": "v2.7.12"
}
```

The important part is:

```text
"status":"pass"
```

This means:

```text
Lavoisier
    │
    ▼
SMO InfluxDB
    ✅ Network connection successful
```

If it fails, possible results include:

```text
Connection timed out
```

or:

```text
Connection refused
```

This means the connection between Lavoisier and SMO should be checked first.

Possible checks:

```bash
ping 192.168.8.69
```

and:

```bash
curl http://192.168.8.69:30138/health
```

---

## 5. Step 3 - Check CPU Usage Manually

Linux CPU Usage can first be checked using:

```bash
top -bn1 | grep "Cpu(s)"
```

Example result:

```text
%Cpu(s): 0.3 us, 0.8 sy, 0.0 ni, 98.8 id
```

`id` means CPU idle percentage.

Therefore:

```text
CPU Usage = 100 - CPU Idle
```

Example:

```text
Idle = 98.8 %

CPU Usage
= 100 - 98.8
= 1.2 %
```

This command can be used to confirm that CPU usage can be obtained from the server.

---

## 6. Step 4 - Prepare SMO InfluxDB Token

The CPU collector requires an InfluxDB token that has permission to write to:

```text
Bucket: cortexdc-server
```

For the current test environment, the scoped token is stored as:

```text
~/lavoisier_smo_token
```

Check whether the token file exists:

```bash
ls -l ~/lavoisier_smo_token
```

Expected permission:

```text
-rw------- 1 oai72_su oai72_su ...
```

If necessary, set the permission:

```bash
chmod 600 ~/lavoisier_smo_token
```

Do **not** upload this token file to GitHub.

Do not show the token content in screenshots or documentation.

---

## 7. Step 5 - Test Writing One CPU Usage Record

Load the token into an environment variable:

```bash
SMO_TOKEN=$(cat ~/lavoisier_smo_token)
```

Write one test value:

```bash
curl -i \
-X POST \
"http://192.168.8.69:30138/api/v2/write?org=ravi-ric&bucket=cortexdc-server&precision=s" \
-H "Authorization: Token $SMO_TOKEN" \
-H "Content-Type: text/plain" \
--data-binary "server_cpu_usage,server_name=Lavoisier cpu_usage_percent=1.2"
```

Successful result:

```text
HTTP/1.1 204 No Content
```

`204 No Content` means:

```text
CPU Usage data
      │
      ▼
SMO InfluxDB
      ✅ Write successful
```

If the token is incorrect or does not have permission, the result may be:

```text
HTTP/1.1 401 Unauthorized
```

or:

```text
HTTP/1.1 403 Forbidden
```

Check:

```text
1. Token file
2. Bucket name
3. Organization name
4. Token permission
```

---

## 8. Step 6 - Query CPU Usage from SMO

After writing the data, query it from SMO to confirm that the record really exists.

Load the token:

```bash
SMO_TOKEN=$(cat ~/lavoisier_smo_token)
```

Run:

```bash
curl -s \
-H "Authorization: Token $SMO_TOKEN" \
-H "Content-Type: application/vnd.flux" \
-H "Accept: application/csv" \
-X POST \
"http://192.168.8.69:30138/api/v2/query?org=ravi-ric" \
--data 'from(bucket: "cortexdc-server")
  |> range(start: -30m)
  |> filter(fn: (r) => r["_measurement"] == "server_cpu_usage")
  |> filter(fn: (r) => r["_field"] == "cpu_usage_percent")
  |> keep(columns: ["_time", "server_name", "_value"])
  |> sort(columns: ["_time"], desc: true)
  |> limit(n: 10)'
```

Example successful result:

```text
,result,table,_time,_value,server_name
,,result,0,2026-09-07T11:23:13Z,1.2,Lavoisier
```

This confirms:

```text
Measurement = server_cpu_usage
Server      = Lavoisier
CPU Usage   = 1.2 %
```

InfluxDB stores timestamps in UTC.

Taiwan time is UTC+8.

For example:

```text
UTC:
2026-09-07 11:23:13

Taiwan:
2026-09-07 19:23:13
```

---

## 9. Step 7 - CPU Usage Collector Program

The CPU Usage collector program is:

```text
/home/oai72_su/cpu_usage_collector.py
```

Run manually:

```bash
python3 ~/cpu_usage_collector.py
```

Successful output:

```text
Lavoisier CPU Usage Collector started.
Destination: http://192.168.8.69:30138
Bucket: cortexdc-server
Press Ctrl+C to stop.

2026-09-07 19:27:07 CPU Usage = 0.97% HTTP = 204
2026-09-07 19:27:08 CPU Usage = 3.81% HTTP = 204
2026-09-07 19:27:09 CPU Usage = 1.19% HTTP = 204
2026-09-07 19:27:10 CPU Usage = 0.75% HTTP = 204
```

The important result is:

```text
HTTP = 204
```

This means every CPU Usage sample was successfully written into SMO InfluxDB.

To stop the manually executed collector:

```text
Ctrl + C
```

Expected result:

```text
Collector stopped.
```

This is a normal stop and is not an error.

---

## 10. CPU Usage Collector Data Flow

The collector reads CPU statistics directly from:

```text
/proc/stat
```

The program calculates CPU utilization using the CPU idle time.

Conceptually:

```text
CPU Usage
=
100 ×
(
1 -
Idle Time Difference
--------------------
Total Time Difference
)
```

The result is then written into SMO approximately every second.

Example:

```text
19:27:07 → 0.97 %
19:27:08 → 3.81 %
19:27:09 → 1.19 %
19:27:10 → 0.75 %
```

---

## 11. Step 8 - Run CPU Collector as a systemd Service

To avoid manually starting the collector during every experiment, the collector is configured as a Linux systemd service.

Service name:

```text
lavoisier-cpu-usage.service
```

Service file:

```text
/etc/systemd/system/lavoisier-cpu-usage.service
```

Example configuration:

```ini
[Unit]
Description=Lavoisier CPU Usage Collector
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=oai72_su
WorkingDirectory=/home/oai72_su
ExecStart=/usr/bin/python3 -u /home/oai72_su/cpu_usage_collector.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

After creating or modifying the service:

```bash
sudo systemctl daemon-reload
```

Enable automatic startup:

```bash
sudo systemctl enable lavoisier-cpu-usage
```

Start the service:

```bash
sudo systemctl start lavoisier-cpu-usage
```

---

## 12. Check CPU Collector Service Status

Run:

```bash
sudo systemctl status lavoisier-cpu-usage --no-pager
```

Successful result:

```text
Loaded: loaded
Active: active (running)
```

The most important part is:

```text
Active: active (running)
```

This means the CPU Usage collector is running in the background.

A faster check is:

```bash
sudo systemctl is-active lavoisier-cpu-usage
```

Successful result:

```text
active
```

If the result is:

```text
inactive
```

or:

```text
failed
```

check the log:

```bash
sudo journalctl -u lavoisier-cpu-usage -n 50 --no-pager
```

---

## 13. View CPU Collector Logs

View the latest 20 records:

```bash
sudo journalctl -u lavoisier-cpu-usage -n 20 --no-pager
```

Example:

```text
2026-09-08 15:54:29 CPU Usage = 1.00% HTTP = 204
2026-09-08 15:54:30 CPU Usage = 0.69% HTTP = 204
2026-09-08 15:54:31 CPU Usage = 0.72% HTTP = 204
2026-09-08 15:54:32 CPU Usage = 1.31% HTTP = 204
```

View real-time logs:

```bash
sudo journalctl -u lavoisier-cpu-usage -f
```

Exit the log view:

```text
Ctrl + C
```

This only exits the log viewer.

The CPU Usage collector continues running in the background.

---

## 14. Stop / Start / Restart the Collector

Stop:

```bash
sudo systemctl stop lavoisier-cpu-usage
```

Start:

```bash
sudo systemctl start lavoisier-cpu-usage
```

Restart:

```bash
sudo systemctl restart lavoisier-cpu-usage
```

Check status:

```bash
sudo systemctl status lavoisier-cpu-usage --no-pager
```

---

## 15. Error - Too Many Open Files

During one test, the following message appeared:

```text
Failed to allocate directory watch: Too many open files
```

Before changing Linux system settings, first check whether the service is actually running:

```bash
sudo systemctl status lavoisier-cpu-usage --no-pager
```

and:

```bash
sudo systemctl is-active lavoisier-cpu-usage
```

If the result is:

```text
active
```

and the log continues showing:

```text
HTTP = 204
```

the collector is still working correctly.

Do not immediately modify system-wide limits on a shared server.

If the service is really `failed`, check:

```bash
sudo journalctl -u lavoisier-cpu-usage -n 50 --no-pager
```

Possible Linux limits can also be checked using:

```bash
ulimit -n
```

```bash
sysctl fs.inotify.max_user_instances
```

```bash
sysctl fs.inotify.max_user_watches
```

---

## 16. Current Result

The CPU Usage collection pipeline has been successfully verified.

```text
Lavoisier
192.168.8.82
      │
      │ CPU Usage
      ▼
cpu_usage_collector.py
      │
      │ Every ~1 second
      ▼
SMO InfluxDB
192.168.8.69:30138
      │
      ▼
cortexdc-server
      │
      ▼
server_cpu_usage
      │
      ▼
cpu_usage_percent
```

Current status:

```text
Lavoisier → SMO connectivity      PASS
CPU Usage collection              PASS
InfluxDB write                    PASS
InfluxDB query                    PASS
Automatic background collection  PASS
systemd auto-start                ENABLED
```

Example collected data:

```text
CPU Usage = 0.97% → HTTP 204
CPU Usage = 3.81% → HTTP 204
CPU Usage = 1.19% → HTTP 204
CPU Usage = 0.75% → HTTP 204
```

---

## 17. Integration with CortexDC Data

The SMO InfluxDB currently contains CortexDC telemetry such as:

```text
server_temperature
server_fan
server_power
server_cpu
```

The newly added CPU utilization measurement is:

```text
server_cpu_usage
```

Therefore, the SMO can contain:

```text
CPU Usage
CPU Temperature
Fan RPM
Server Power
```

from different data collection paths.

The next step is to synchronize these data based on timestamps and use them for E2E experiments and AI/ML model training.

Expected dataset concept:

```text
Timestamp
CPU Usage Mean
CPU Usage Max
CPU Temperature
Fan RPM
Server Power
```

The high-frequency CPU Usage data can later be aggregated and aligned with the CortexDC telemetry timestamps.

---

## 18. Important Security Notes

Do not upload the following files to GitHub:

```text
lavoisier_smo_token
smo_token
config.env
*.env
```

Do not write an actual InfluxDB token, username, password, or CortexDC password directly into source code.

Recommended `.gitignore`:

```gitignore
# Credentials
*.env
config.env
smo_token
*_token
lavoisier_smo_token

# Python
__pycache__/
*.pyc

# Exported datasets
*.csv
```

For a public GitHub repository, internal IP addresses should also be replaced with placeholders such as:

```text
<SMO_IP>
<SERVER_IP>
<INFLUXDB_PORT>
```
