# 3GPP Cloud Gaming Traffic Model Implementation in ns-3

## 1. Assignment Objective

The purpose of this assignment is to set up the ns-3 simulator and implement a traffic model based on **3GPP TR 26.926**.

The main tasks include:

- Install and build ns-3
- Study a 3GPP traffic model
- Implement the selected traffic model in ns-3
- Generate traffic and PCAP files
- Verify packet behavior using Wireshark
- Analyze packet size and inter-arrival time using PDF and CDF

---

## 2. Environment

| Item | Setting |
|---|---|
| Operating System | macOS |
| Platform | Apple Silicon MacBook Air |
| ns-3 Version | ns-3.48 |
| Build System | CMake |
| Programming Language | C++ |
| Data Analysis | Python |
| Packet Analysis | Wireshark |


# 3. Selected 3GPP Traffic Model

The selected model is:

**3GPP TR 26.926 Annex B – Cloud Gaming & XR Traffic Model**

For this experiment, **Cloud Gaming Category C** was selected.

Category C represents games with:

> High dynamicity and high complexity

This traffic model was selected because it generates **bursty network traffic**, which is also related to my final project.

My final project studies the relationship between:

```text
Network Traffic
      ↓
System / CPU Workload
      ↓
Power Consumption
      ↓
Server Temperature
```

Therefore, a bursty traffic model is more suitable than a simple Constant Bit Rate (CBR) model for generating dynamic workloads.

---

# 4. Cloud Gaming Category C Parameters

The following parameters are based on 3GPP TR 26.926 Annex B.

| Parameter | Category C |
|---|---|
| Traffic Type | Bursty |
| Packet Format | UDP |
| Frame Rate | 60 fps |
| Average Data Size | 25 KB |
| Data Size STD | 5 KB |
| Maximum Data Size | 70 KB |
| Jitter Distribution | Truncated Gaussian |
| Jitter STD | 4 ms |
| Maximum Jitter | 32 ms |
| Packet Size | approximately 1500 Bytes |
| Traffic Range | approximately 10–30 Mbps |

---

# 5. Traffic Model Implementation

## 5.1 Burst Period

The traffic model uses a frame rate of:


60 fps


Therefore, the nominal period between two bursts is:

T = 1/60 秒

T = 1/60 秒 ≈ 16.67 ms

A new burst is generated approximately every 16.67 ms.

Jitter is added to the burst interval, so the actual interval is not always exactly 16.67 ms.

---

## 5.2 Burst Data Size
<img width="590" height="234" alt="Screenshot 2026-10-08 at 2 21 43 PM" src="https://github.com/user-attachments/assets/f5f28035-b20c-4d15-89cc-68563be6b503" />

The data size of each burst is generated using a truncated Gaussian distribution.

```text
Mean = 25 KB
STD  = 5 KB
Max  = 70 KB
```

Therefore, different bursts contain different amounts of data.

For example:

```text
Burst 1: 23605 Bytes
Burst 2: 26205 Bytes
Burst 3: 21627 Bytes
```

---

## 5.3 Packets per Burst

The target IP packet size is approximately:

```text
1500 Bytes
```

Therefore, a burst with approximately 25 KB of data contains about:

25 × 1024 = 25600 Bytes

25600 / 1500 ≈ 17.1
So one burst contains approximately:

```text
17 packets
```

Since the burst data size changes, the packet count also changes.

Example:

```text
Burst 1 → 16 packets
Burst 2 → 18 packets
Burst 3 → 15 packets
Burst 4 → 16 packets
Burst 5 → 19 packets
```

---

# 6. Packet Transmission inside a Burst

The packet transmission pacing rate is set to:

```text
70 Mbps
```

The transmission interval of a 1500-byte packet is:

t = (1500 × 8) / (70 × 10^6)

t ≈ 0.171 ms
Therefore, packets inside one burst are transmitted very close to each other.

Example:

```text
Burst 1

Packet 1
   ↓ 0.171 ms
Packet 2
   ↓ 0.171 ms
Packet 3
   ↓ 0.171 ms
Packet 4
   ↓
   ...
```

After one burst finishes, there is a longer gap before the next burst starts.

This creates the bursty traffic behavior.

---

# 7. ns-3 Simulation Result

The simulation was successfully executed using:

```bash
./ns3 run scratch/3gpp-cloud-gaming
```

Result:
<img width="992" height="308" alt="image" src="https://github.com/user-attachments/assets/695d075a-592f-4ec4-9388-6a482c3e12c1" />


```text
====================================
3GPP TR 26.926 Annex B
Cloud Gaming Category C
====================================

Total received bytes: 12335360
Average throughput: 12.3354 Mbps
Frame rate: 60 fps
Nominal burst period: 16.67 ms
Target packet size: ~1500 bytes
```

The measured average throughput is:

12.3354 Mbps

This value is within the expected Category C traffic range(10~30 Mbps).

---

# 8. Burst Trace Result

### The simulation generates:
<img width="894" height="370" alt="image" src="https://github.com/user-attachments/assets/d70acd94-3cf0-4f57-8551-07421d3037ad" />

```text
3gpp_burst_trace.csv
```
Example:

```text
burst_id,start_time,data_size_bytes,packet_count,jitter_ms

1,1.000000,23605.017487,16,-1.261558
2,1.015405,26205.480922,18,2.800438
3,1.034878,21627.676096,15,-6.039726
4,1.045505,23683.994850,16,-3.756884
5,1.058415,27637.490772,19,-2.397420
```

Each burst contains different:

- Start time
- Data size
- Packet count
- Jitter

This confirms that the generated traffic is not constant.

---

# 9. Packet Size Distribution

The IP packet size is approximately:

```text
1500 Bytes
```

The application payload is:

```text
1472 Bytes
```

UDP header:

```text
8 Bytes
```

IPv4 header:

```text
20 Bytes
```

Therefore:

1472 + 8 + 20 = 1500 Bytes

The Packet Size PDF is concentrated at 1500 Bytes.
<img width="1920" height="1440" alt="image" src="https://github.com/user-attachments/assets/346c73bd-6511-46c7-a0e0-2879309b7abf" />
The Packet Size CDF immediately increases to 1 at 1500 Bytes because almost all packets have the same size.
<img width="1920" height="1440" alt="image" src="https://github.com/user-attachments/assets/d6113bba-d36e-45c2-9367-85ef656e0a55" />
---

# 10. Packet Inter-arrival Time

The Packet Inter-arrival Time (IAT) is defined as:

IAT = t_i - t_(i-1)

Two types of IAT can be observed.

### Within-Burst IAT

Packets inside the same burst have approximately:

0.171 ms

Therefore, the IAT PDF has a large peak near 0.171 ms.

### Inter-Burst IAT

After one burst finishes, there is a longer gap before the next burst.

The larger IAT values are approximately:

```text
10–20+ ms
```

These values represent:

```text
Last packet of Burst N
          ↓
        GAP
          ↓
First packet of Burst N+1
```

There are fewer large IAT values because each burst contains many short packet intervals but only one inter-burst gap.

Therefore, the IAT distribution clearly shows the bursty behavior.
### Packet Inter-arrival Time PDF

<img width="1920" height="1440" alt="image" src="https://github.com/user-attachments/assets/22d6051c-5577-4d2e-b062-b7e8786fc01e" />

The large peak near 0.171 ms represents packet intervals within the same burst.  
The smaller values around 10–20+ ms represent the longer gap between consecutive bursts.

### Packet Inter-arrival Time CDF
<img width="1920" height="1440" alt="image" src="https://github.com/user-attachments/assets/c504d62b-bb8c-485c-a0d2-975e96c413aa" />

---

# 11. Wireshark Verification

The generated PCAP file is:

```text
3gpp-cloud-gaming-0-0.pcap
```

The traffic was filtered using:

```text
udp.port == 5000
```

The Wireshark result shows:

```text
Source:      10.1.1.1
Destination: 10.1.1.2
Protocol:    UDP
IP Length:   1500 Bytes
```

Wireshark displays:

```text
Frame Length = 1502 Bytes
```

because the Point-to-Point Protocol adds an additional 2-byte header.

Therefore:

1500 + 2 = 1502 Bytes

The IPv4 field still shows:

```text
Total Length: 1500
Protocol: UDP (17)
```

which confirms that the model generates 1500-byte UDP/IP packets correctly.
### Wireshark Packet Verification

<img width="671" height="349" alt="image" src="https://github.com/user-attachments/assets/f273060a-fbe5-402d-af20-96f96f33dcc9" />

The IPv4 total length is 1500 bytes and the transport protocol is UDP.
---

# 12. Wireshark Burst Verification

Example:

```text
0.000000
0.000171
0.000342
0.000514
0.000685
...
0.002571

0.015405
```

Packets inside the same burst are approximately:

```text
0.171 ms apart
```

However, after the last packet of the first burst:

```text
0.002571 s
```

the first packet of the next burst appears at:

```text
0.015405 s
```

Therefore:
0.015405 - 0.002571 = 0.012834 s = 12.834 ms

There are no packets during this gap.

This confirms the bursty traffic behavior:

```text
Burst 1                           Burst 2

P P P P P P P P                 P P P P P P
↔ 0.171 ms ↔

              <--- 12.834 ms --->
                    No packets
```

---

# 13. Generated Files

The experiment generates the following files:


### 3gpp_data_size_pdf.png
Burst data sizes are mainly distributed around the 25 KB mean value.
<img width="1920" height="1440" alt="image" src="https://github.com/user-attachments/assets/d1672c67-3dc6-45ad-9a07-400f7925965f" />

### 3gpp_data_size_cdf.png
Shows the cumulative distribution of burst data size generated by the model.
<img width="1920" height="1440" alt="image" src="https://github.com/user-attachments/assets/07e64726-32eb-4197-b1c4-da387bc20867" />

### 3gpp_burst_length_pdf.png
Most bursts contain about 15–21 packets with varying burst lengths.
<img width="1920" height="1440" alt="image" src="https://github.com/user-attachments/assets/c0ee78a0-8f63-41a6-a828-0c1c36543c7c" />

### 3gpp_burst_length_cdf.png
Shows the cumulative probability of the number of packets per burst.
<img width="1920" height="1440" alt="image" src="https://github.com/user-attachments/assets/e63f4887-d0f5-450b-a109-9dd373cc217b" />

### 3gpp_jitter_pdf.png
Jitter values are mainly distributed around 0 ms with Gaussian behavior.
<img width="1920" height="1440" alt="image" src="https://github.com/user-attachments/assets/a629e31f-4e50-449f-8f7e-484f91bef352" />

### 3gpp_jitter_cdf.png
Shows the cumulative distribution of jitter values between generated bursts.
<img width="1920" height="1440" alt="image" src="https://github.com/user-attachments/assets/20e0994a-5943-4d9b-b9cb-9bd341a322e5" />


---

# 14. Conclusion

In this assignment, the 3GPP TR 26.926 Annex B Cloud Gaming Category C traffic model was implemented successfully in ns-3.

The simulation successfully generated:

- UDP traffic
- Approximately 1500-byte IP packets
- Variable burst sizes
- Variable packet counts
- Gaussian jitter
- Approximately 16.67 ms burst periods
- Bursty packet transmission behavior

The average throughput was approximately:

```text
12.34 Mbps
```

Packet Size PDF/CDF, Inter-arrival Time PDF/CDF, burst traces, and Wireshark PCAP analysis were used to verify the generated traffic.

The Wireshark results also clearly show short packet intervals inside each burst and longer gaps between consecutive bursts.

Therefore, the implemented ns-3 traffic successfully reproduces the main characteristics of the selected 3GPP Cloud Gaming traffic model.
