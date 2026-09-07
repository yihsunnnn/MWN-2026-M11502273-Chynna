# O-RAN O2 規格、功能與環境調查筆記

## 1. O2 是什麼

O2 是 O-RAN 架構中，讓 **SMO（Service Management and Orchestration）管理 O-Cloud** 的標準介面。O2 不是單一軟體、單一服務名稱或固定 TCP Port，而是一組由 O-RAN Alliance WG6 定義的 API、資料模型、操作流程與安全要求。

```text
SMO（O2 Client）
        │
        │ O2 API：HTTPS、REST、JSON
        │ OAuth2/JWT，生產環境通常搭配 mTLS
        ▼
O-Cloud Manager（O2 Server）
        ├── O2 IMS：基礎設施管理
        └── O2 DMS：部署管理
                │
                ▼
Kubernetes / OpenShift / VM / Bare Metal / Storage / Network
```

O2 是管理與編排介面，不是毫秒級或 Near-Real-Time 的 RAN 控制介面。

---

## 2. O2 的兩個主要部分

### 2.1 O2 IMS：Infrastructure Management Services

O2 IMS 用於管理與查詢 O-Cloud 基礎設施，主要功能包括：

- 查詢 O-Cloud 基本資料及識別碼。
- 查詢 Location、OCloudSite、Resource Pool 與 Resource。
- 查詢伺服器、CPU、記憶體、儲存及網路資源。
- 查詢 Resource Type 與 Deployment Manager。
- 接收或查詢基礎設施告警。
- 建立資源變更與告警訂閱。
- 視規格版本及實作支援 Performance、Logging、Artifacts、Cluster 與 Provisioning。
- 某些實作可進行裸機配置、叢集建立、韌體更新及 Day-2 管理。

典型資源階層：

```text
Location
└── OCloudSite
    └── ResourcePool
        └── Resource
            ├── Bare-metal server
            ├── CPU
            ├── Memory
            ├── Storage
            └── Network capability
```

常見 API 路徑如下；實際路徑與版本仍須以 Server 的 OpenAPI 文件為準：

```text
GET /o2ims-infrastructureInventory/v2
GET /o2ims-infrastructureInventory/v2/resourceTypes
GET /o2ims-infrastructureInventory/v2/resourcePools
GET /o2ims-infrastructureInventory/v2/resourcePools/{resourcePoolId}/resources
GET /o2ims-infrastructureInventory/v2/deploymentManagers
```

### 2.2 O2 DMS：Deployment Management Services

O2 DMS 用於管理部署在 O-Cloud 上的軟體工作負載生命週期，主要功能包括：

- 查詢可用的 Deployment Manager。
- 上傳或引用部署套件。
- 建立部署。
- 查詢部署狀態。
- 更新、擴縮及刪除部署。
- 管理 O-RAN CNF/VNF 工作負載。

```text
SMO
└── 要求部署 O-DU CNF
    └── O2 DMS
        └── Deployment Manager
            └── Helm / Kubernetes / OpenShift / GitOps
```

O2 DMS 定義標準化的部署管理行為，但不限定底層一定使用 Helm、Operator 或其他特定工具。

---

## 3. O2 能提供的功能

| 類別 | 可能提供的內容 |
| --- | --- |
| Inventory | 伺服器、CPU 型號與核心數、記憶體、磁碟、網卡 |
| Resource Pool | 設備所屬資源池及可配置容量 |
| Deployment Manager | 可使用的 Kubernetes/OpenShift 部署平台 |
| Provisioning | 裸機配置、系統安裝及叢集建立 |
| Monitoring | 基礎設施狀態與事件 |
| Alarm | 伺服器、叢集或資源異常告警 |
| Performance | CPU、記憶體等效能資料；取決於版本與實作 |
| Subscription | 資源或告警改變時通知 SMO 的 Callback 機制 |
| Deployment | 建立、更新、擴縮及刪除 CNF/VNF |
| Lifecycle | 韌體更新、叢集配置、升級及 Day-2 操作 |

---

## 4. CPU 資料與 O2 的關係

### 4.1 CPU 規格與容量

以下資料通常屬於 O2 IMS Inventory/Resource：

- CPU 型號與 Architecture。
- Socket 及 Core 數量。
- 可配置與已配置容量。
- CPU 所屬 Server 或 Resource Pool。

### 4.2 即時 CPU 使用率

例如 `CPU usage = 37%` 屬於 Performance 或 Monitoring 資料。O2 規格可以承載基礎設施效能資訊，但是否能直接取得 CPU 使用率，取決於 O2 Server 的版本和實作完整度。

常見資料流程：

```text
Server / Kubernetes Node
        │
        ▼
Node Exporter / Telegraf / Kubernetes Metrics
        │
        ▼
Prometheus
        ├── O2 Performance/Monitoring API
        └── InfluxDB / Grafana
```

重要限制：

- O2 本身不會自動產生 CPU 數據。
- O2 Server 必須先從 Prometheus 或其他監控來源收集資料。
- 有些 O2 實作只提供 Inventory、Alarm 與 Subscription，沒有完整 Performance API。
- 如果 O2 沒有 Performance API，可直接由 Prometheus、Node Exporter 或 Telegraf 取得 CPU 使用率，再寫入 InfluxDB。

---

## 5. 通訊與安全規格

典型 O2 實作使用：

- HTTPS REST API。
- JSON 資料格式。
- OpenAPI 介面描述。
- TLS Server Certificate。
- OAuth2/JWT Bearer Token。
- 生產環境通常搭配雙向 TLS（mTLS）。
- Subscription 與 Callback URL 傳送資源或告警事件。
- API 版本區隔，例如 `/v1`、`/v2`。
- UUID 作為 O-Cloud、Resource Pool、Resource 與 Subscription 識別碼。
- RBAC、Token scope、audience 與 role 控制操作權限。

正常的生產環境不應允許匿名執行配置、部署或刪除操作。讀取 Inventory 和執行 Provisioning 也可能需要不同權限。

---

## 6. O2 的限制

### 6.1 O2 不是其他 O-RAN 介面

O2 不能取代：

- **E2**：Near-RT RIC 與 E2 Node 間的近即時控制。
- **A1**：Non-RT RIC 與 Near-RT RIC 間的 Policy、Enrichment Information 等功能。
- **O1**：網路元件的 FCAPS 管理。
- **Open Fronthaul M-plane**：O-RU 管理。
- **F1、E1、NG**：RAN 與 Core 的通訊協定。

### 6.2 不保證每套產品功能相同

不同版本或廠商可能只支援 O2 的部分功能：

```text
實作 A：Inventory + Alarm
實作 B：Inventory + Monitoring + DMS
實作 C：Inventory + Provisioning + Cluster lifecycle
```

因此，找到 O2 API 不代表 IMS、DMS、Performance、Logging 與 Provisioning 全部可用。

### 6.3 API 版本與路徑差異

可能看到 `/v1`、`/v2` 或不同命名形式：

```text
/o2ims_infrastructureInventory
/o2ims-infrastructureInventory
```

Client 應先查詢 API version 或 OpenAPI 文件，不能假設不同實作完全相容。

### 6.4 O2 提供抽象資源，不一定暴露所有底層資訊

- 可以提供 CPU 規格，但不一定提供 `/proc/cpuinfo` 全部欄位。
- 可以提供標準告警，但不一定暴露 Prometheus 的全部 metrics。
- 可以管理標準部署生命週期，但不一定允許任意 Kubernetes API 操作。
- O2 能提供哪些資料，仍受底層監控、裸機管理及 Deployment Manager 能力限制。

---

## 7. 如何判定系統真的支援 O2

不能只因為 hostname 或程式名稱包含 `o2ims` 就判定完整支援。至少應確認：

1. 存在可連線的 HTTPS API。
2. 能取得 O2 API 版本資訊。
3. 認證機制為 OAuth2/JWT，必要時支援 mTLS。
4. 能取得 O-Cloud ID。
5. 能列出 Resource Type、Resource Pool 或 Resource。
6. API 回應符合 O2 資料模型。
7. 若聲稱支援 DMS，能列出 Deployment Manager 與部署相關資源。
8. 若聲稱支援 Performance/Monitoring，對應 API 能回傳有效資料。

HTTP 狀態碼可初步判讀：

| 狀態碼 | 意義 |
| --- | --- |
| `200` | API 存在且請求成功 |
| `401` | API 很可能存在，但需要有效認證 |
| `403` | API 存在，但權限、scope、audience 或 mTLS 不符合 |
| `404` | Host 可達，但路徑或版本可能不正確 |
| `000` | TCP/HTTPS 尚未建立，通常是網路、DNS、Ingress 或服務問題 |

---

## 8. 目前實驗環境調查結果

### 8.1 已找到的 O2 IMS 設定

SMO 主機：

```text
192.168.8.69
```

在 `/etc/dnsmasq.d/o2ims.conf` 與 `/etc/hosts` 發現：

```text
192.168.8.210 o2ims.apps.ocloud-vm-okd-aio.lab.internal
```

因此目前推測：

```text
SMO / O2 Client：192.168.8.69
O-Cloud Manager / O2 IMS Server：192.168.8.210
```

### 8.2 網路檢查結果

`192.168.8.69` 的介面與路由：

```text
192.168.8.69/24 dev enp65s0f0np0
192.168.8.0/24 dev enp65s0f0np0
192.168.8.210 dev enp65s0f0np0 src 192.168.8.69
```

路由選擇正確，但鄰居解析結果為：

```text
192.168.8.210 dev enp65s0f0np0 FAILED
```

Ping 結果：

```text
From 192.168.8.69 Destination Host Unreachable
```

HTTPS測試結果：

```text
No route to host
HTTP status: 000
```

### 8.3 目前結論

- SMO 上存在明確的 O2 IMS hostname 設定。
- O2 IMS 被設定為 `192.168.8.210`。
- `.69` 到 `.210` 的 IP 路由正確。
- `.69` 無法取得 `.210` 的 MAC 位址，ARP/Neighbor 狀態為 `FAILED`。
- 問題發生在 HTTPS、O2 API 及帳密驗證之前。
- 尚不能確認 `.210` 的 O2 IMS 實際支援哪些 API。

可能原因：

1. O-Cloud/OKD 主機或 VM 未啟動。
2. `.210` 已是過期的舊位址。
3. `.69` 與 `.210` 位於不同 VLAN。
4. `.210` 的網卡中斷或沒有配置該 IP。
5. 交換器啟用了 Port Isolation、ACL 或 ARP filtering。

### 8.4 後續檢查

恢復 `.210` 網路連線後，先測試：

```bash
curl -vk --connect-timeout 5 \
  https://o2ims.apps.ocloud-vm-okd-aio.lab.internal/o2ims-infrastructureInventory/v2
```

若取得 Token，可繼續測試：

```bash
curl --cacert /path/to/ca-bundle.crt \
  -H "Authorization: Bearer ${MY_TOKEN}" \
  https://o2ims.apps.ocloud-vm-okd-aio.lab.internal/o2ims-infrastructureInventory/v2/resourcePools
```

若環境要求 mTLS：

```bash
curl --cert /path/to/client.crt \
  --key /path/to/client.key \
  --cacert /path/to/ca-bundle.crt \
  -H "Authorization: Bearer ${MY_TOKEN}" \
  https://o2ims.apps.ocloud-vm-okd-aio.lab.internal/o2ims-infrastructureInventory/v2/resourceTypes
```

---

## 9. 參考資料

- [O-RAN Alliance WG6](https://www.o-ran.org/technical-groups/wg6)
- [O-RAN SC O2 API](https://docs.o-ran-sc.org/projects/o-ran-sc-pti-o2/en/stable/oran-o2-api.html)
- [OpenShift O-Cloud Manager / O2 IMS](https://github.com/openshift-kni/oran-o2ims)
- [O2 IMS Environment Setup and Authentication](https://github.com/openshift-kni/oran-o2ims/blob/main/docs/user-guide/environment-setup.md)
- [O2 IMS Server Onboarding](https://github.com/openshift-kni/oran-o2ims/blob/main/docs/user-guide/server-onboarding.md)

