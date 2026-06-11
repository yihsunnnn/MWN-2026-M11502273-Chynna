# PAPER REVIEW 
# Table of Contents

1. [Neural Network-Based Reconstruction of Steady-State Temperature Systems](#paper-review-neural-network-based-reconstruction-of-steady-state-temperature-systems-with-unknown-material-composition-2024)
   - [Reference](#reference)
   - [1. Research Problem](#1-research-problem)
   - [2. Motivation and Challenges](#2-motivation-and-challenges)
   - [3. Assumptions](#3-assumptions)
   - [4. Proposed Solution](#4-proposed-solution)
   - [5. Input and Output](#5-input-and-output)
   - [6. Training Data and Data Source](#6-training-data-and-data-source)
   - [7. Evaluation Environment](#7-evaluation-environment)
   - [8. Evaluation Metrics](#8-evaluation-metrics)
   - [9. Experimental Results](#9-experimental-results)
   - [10. Limitations](#10-limitations)
   - [11. Summary of the Problem](#11-summary-of-the-problem)
   - [12. Relation to Our Framework](#12-relation-to-our-framework)

2. [A Deep Learning Method Based on Partition Modeling for Reconstructing Temperature Field](#paper-review--a-deep-learning-method-based-on-partition-modeling-for-reconstructing-temperature-field2022)
   - [Reference](#reference-1)
   - [1. Research Problem](#1-research-problem-1)
   - [2. Motivation and Challenges](#2-motivation-and-challenges-1)
   - [3. Reconstruction Method](#3-reconstruction-method)
   - [4. Input and Output](#4-input-and-output)
   - [5. Training Data and Data Source](#5-training-data-and-data-source)
   - [6. Evaluation Metrics](#6-evaluation-metrics)
   - [7. Experimental Results](#7-experimental-results)
   - [8. Limitations](#8-limitations)
   - [9. Relation to Our Framework](#9-relation-to-our-framework)

3. [Continuous Field Reconstruction from Sparse Observations with Implicit Neural Networks](#paper-review-continuous-field-reconstruction-from-sparse-observations-with-implicit-neural-networks2024)
   - [Reference](#reference-2)
   - [1. Research Problem](#1-research-problem-2)
   - [2. Motivation and Challenges](#2-motivation-and-challenges-2)
   - [3. Reconstruction Method](#3-reconstruction-method-1)
   - [4. Input and Output](#4-input-and-output-1)
   - [5. Training Data and Data Source](#5-training-data-and-data-source-1)
   - [6. Evaluation Metrics](#6-evaluation-metrics-1)
   - [7. Experimental Results](#7-experimental-results-1)
   - [8. Limitations](#8-limitations-1)
   - [9. Relation to Our Framework](#9-relation-to-our-framework-1)

4. [Leakage-Aware Cooling Management for Improving Server Energy Efficiency](#paper-review-zapater-et-al-2015)
   - [Reference](#reference-3)
   - [1. Application Domain](#1-application-domain)
   - [2. Challenge](#2-challenge)
   - [3. Assumption](#3-assumption)
   - [4. Proposed Solution](#4-proposed-solution-1)
   - [5. Evaluation Environment](#5-evaluation-environment)
   - [6. Key Result](#6-key-result)
   - [7. Relevance to Proposed Framework](#7-relevance-to-proposed-framework)
   - [8. Limitation](#8-limitation)
   - [9. Takeaway](#9-takeaway)
   
# Paper Review: Neural Network-Based Reconstruction of Steady-State Temperature Systems with Unknown Material Composition (2024)

## Reference

Sabathiel, Silvester, et al. "Neural network-based reconstruction of steady-state temperature systems with unknown material composition." *Scientific Reports*, 2024.

| Item              | Description                                                                                                 |
| ----------------- | ----------------------------------------------------------------------------------------------------------- |
| **Paper**         | *Neural Network-Based Reconstruction of Steady-State Temperature Systems with Unknown Material Composition* |
| **Main Focus**    | Reconstructing complete steady-state temperature fields from sparse temperature observations                |
| **Main Method**   | Physics-informed fully convolutional autoencoder with a spatial propagator module                           |
| **Target System** | 2D thermal systems and PCB-based thermal measurement systems                                                |
| **DOI**           | 10.1038/s41598-024-73380-1                                                                                  |

### 1. Research Problem

This paper aims to reconstruct a complete steady-state temperature field from only partial temperature observations.

The key problem is that the material composition, heat source distribution, and boundary conditions are unknown.

In our case, this can be related to reconstructing a full rack-level thermal map from limited Server / iBox / PDU data.

---

### 2. Motivation and Challenges

Thermal field reconstruction is difficult because temperature sensors are usually limited, and complete temperature measurements are hard to obtain.

The challenge becomes harder when the internal material distribution, heat source positions, heat source values, and boundary conditions are unknown.

This is similar to data center environments, where sensors are limited and the internal thermal behavior of racks is difficult to observe directly.

---

### 3. Assumptions

The paper assumes that the system can be approximated as a 2D steady-state thermal system.

The model only receives sparse temperature observations as input.

The model does not require additional information about:

* Material distribution
* Heat source position
* Heat source value
* Boundary conditions

This setting is called blind virtual sensing.

---

### 4. Proposed Solution

The paper proposes a neural-network-based reconstruction method.

The architecture includes:

* Spatial propagator module
* Fully convolutional autoencoder
* U-Net-like encoder-decoder structure
* Physics-informed loss function

The spatial propagator first spreads the known temperature information into the missing regions.

Then, the autoencoder reconstructs the complete temperature field.

The physics-informed loss helps the model produce smoother and more physically reasonable temperature fields.

---

### 5. Input and Output

**Input:**

* Sparse temperature observations
* Mask information showing known and unknown temperature positions

The paper tests three sampling methods:

* Scattered sampling
* Ring sampling
* Grid-edge sampling

For our framework, the input can be:

* Server temperature
* Server power
* iBox inlet temperature
* PDU power data
* Rack position information

**Output:**

* Reconstructed complete 2D temperature field
* Full thermal map

---

### 6. Training Data and Data Source

The training data are generated using FEM simulation.

Each system is converted into a 50 × 50 temperature image.

This means each temperature map contains:

```text
50 × 50 = 2500 temperature points
```

The original dataset contains 775 thermal systems.

After data augmentation using rotation, the dataset becomes 3100 systems.

The paper also uses real PCB thermal measurement data for experimental validation.

---

### 7. Evaluation Environment

The paper evaluates the method using both simulation and experiment.

**Simulation environment:**

* 2D steady-state thermal systems
* FEM-generated temperature fields
* Random material distribution
* Random heat source distribution
* Random boundary conditions

**Experimental environment:**

* PCB board
* SMD resistors as heat sources
* Thermal camera measurement
* Real temperature field reconstruction

This shows that the model is not only tested on simulated data but also validated with real thermal measurement data.

---

### 8. Evaluation Metrics

The main evaluation metric is average relative error.

The paper compares the reconstructed temperature field with the ground truth temperature field.

The result shows that the reconstruction error is below about 1.15% in most cases.

For the most challenging grid-edge sampling case, the model can still reconstruct the full temperature field with about 1.1% relative average error.

---

### 9. Experimental Results

The proposed method performs well under sparse sampling conditions.

Scattered sampling gives the best reconstruction result because the sensors are distributed across the whole field.

Ring sampling and grid-edge sampling are more difficult because the model only observes boundary information.

However, even with grid-edge sampling and only about 3.12% sampling ratio, the model can still reconstruct the full temperature field with low error.

The neural network also outperforms Kriging, especially in estimating maximum temperature and handling sparse observations.

---

### 10. Limitations

The paper has several limitations:

* The main model is trained for 2D systems, while real thermal systems are often 3D.
* The model may fail to detect very localized hotspots.
* If heat does not propagate to the sensor region, boundary sensors may not provide enough information.
* The model depends on whether the training data can represent the real target system.
* The real PCB experiment still has 3D effects, convection, radiation, and thickness-direction heat dissipation that are not fully modeled.

---

### 11. Summary of the Problem

This paper addresses the problem of reconstructing a complete temperature field from sparse temperature measurements when the material composition, heat source distribution, and boundary conditions are unknown.

The main idea is to use a physics-informed neural network to learn the possible thermal distribution from limited sensor data.

---

### 12. Relation to Our Framework

This paper can support the thermal map reconstruction part of our framework.

We can refer to the following ideas:

* Sparse temperature sensing to full thermal map reconstruction
* Using a U-Net-like model for temperature field reconstruction
* Using physics-informed loss to improve physical consistency
* Handling unknown material and heat source distributions
* Validating reconstruction with both simulation and real thermal data

Possible connection:

```mermaid
flowchart TB

    A["Server / iBox / PDU Data"]

    B["Sparse Thermal Observation"]

    C["XGBoost Temperature Prediction"]

    D["U-Net / Thermal Map Reconstruction"]

    E["Rack-Level Thermal Map"]

    F["Cooling Decision"]

    A --> B
    B --> C
    C --> D
    D --> E
    E --> F
```


# Paper Review : A Deep Learning Method Based on Partition Modeling for Reconstructing Temperature Field(2022)

## Reference: 
Xingwen Peng,et al."A deep learning method based on partition modeling for reconstructing temperature field.",International Journal of Thermal Sciences,Volume 182,2022.


| Item              | Description                                                                               |
| ----------------- | ----------------------------------------------------------------------------------------- |
| **Paper**         | *A Deep Learning Method Based on Partition Modeling for Reconstructing Temperature Field* |
| **Main Focus**    | Temperature field reconstruction from limited temperature observations                    |
| **Main Method**   | Partition modeling framework with Adaptive UNet and shallow MLP                           |
| **Target System** | Electronic equipment thermal field reconstruction                                         |

---

### 1. Research Problem

This paper aims to reconstruct the complete temperature field of electronic equipment from limited temperature observation points.

In our case, this is related to reconstructing a full rack-level thermal map from limited Server / iBox / PDU data.

---

### 2. Motivation and Challenges

Thermal field reconstruction is difficult because only limited temperature sensors can be deployed in real systems.

Also, temperature fields may have complex spatial distributions, especially near heat sources or heatsinks where large temperature gradients appear.

This is similar to data center environments, where sensors are limited and the thermal behavior may vary depending on rack layout, server placement, and power distribution.

---

### 3. Reconstruction Method

The paper proposes a partition modeling framework consisting of:

* Adaptive UNet
* Shallow MLP

The Adaptive UNet is used to reconstruct the overall temperature field.

The shallow MLP is used to improve the reconstruction accuracy in large-gradient regions, especially near the heatsink.

---

### 4. Input and Output

**Input:**

* Sparse temperature observation points
* Observation point locations

For our framework, the input can be:

* Server temperature / power
* iBox inlet temperature
* PDU power data
* Rack position information

**Output:**

* Reconstructed full temperature field
* Full thermal map of the system

---

### 5. Training Data and Data Source

The paper uses finite element simulation data generated by FEM.

The temperature field is generated from different heat source layouts and power intensities.

This means the method is mainly validated using simulation data, not real hardware measurement data.

---

### 6. Evaluation Metrics

The paper uses several metrics to evaluate reconstruction performance:

* MAE: Mean Absolute Error
* CMAE: Component-constrained Mean Absolute Error
* MaxAE: Maximum Absolute Error
* MT-AE: Absolute Error of Maximum Temperature

These metrics evaluate both the overall reconstruction error and the hotspot-related error.

---

### 7. Experimental Results

The proposed method can accurately reconstruct the temperature field from limited observation points.

The results show that Adaptive UNet can reconstruct the overall thermal map, while the additional MLP improves the accuracy in large-gradient regions.

The paper also shows that only 16 observation points can still achieve good reconstruction performance.

---

### 8. Limitations

The method is mainly tested using simulation data.

It focuses on steady-state temperature field reconstruction, not real-time or time-series thermal prediction.

Also, the target system is electronic equipment, not directly a data center or rack-level cooling environment.

---

### 9. Relation to Our Framework

This paper can support the thermal map reconstruction part of our framework.

We can refer to the following ideas:

* Sparse sensor input to full thermal map reconstruction
* CNN / U-Net-based thermal reconstruction
* Partition modeling for large-gradient region refinement
* Hybrid architecture using UNet + MLP
* Sensor placement strategy
* Hotspot estimation
* Potential connection to Digital Twin thermal monitoring

Possible connection:

```mermaid
flowchart TB

    A["Server / iBox / PDU Data"]

    B["Sparse Thermal Observation"]

    C["XGBoost Temperature Prediction"]

    D["U-Net / Thermal Map Reconstruction"]

    E["Rack-Level Thermal Map"]

    F["Cooling Decision"]

    A --> B
    B --> C
    C --> D
    D --> E
    E --> F
```

This paper is highly related to the “U-Net / Thermal Map Reconstruction” layer in our framework. It supports the idea that limited sensor data can be used to reconstruct a complete thermal distribution, which is useful for rack-level thermal monitoring and future cooling optimization.


# Paper Review: Continuous Field Reconstruction from Sparse Observations with Implicit Neural Networks(2024)
## Reference: Luo, Xihaier, et al. "Continuous field reconstruction from sparse observations with implicit neural networks."International Conference on Learning Representations. Vol. 2024.

| Item              | Description |
| ----------------- | ----------- |
| **Paper**         | *Continuous Field Reconstruction from Sparse Observations with Implicit Neural Networks* |
| **Main Focus**    | Continuous physical field reconstruction from sparse observations |
| **Main Method**   | Implicit Neural Representation (INR) with MMGN and latent code-based reconstruction |
| **Target System** | Scientific physical fields, including climate simulation and satellite-based sea surface temperature fields |
| **DOI**           | Not specified in the paper |
### 1. Research Problem
This paper aims to reconstruct a complete continuous physical field from sparse observations.

In our case, this can be related to reconstructing a full thermal map from limited Server / iBox / PDU data.

---

### 2. Motivation and Challenges
Thermal field reconstruction is difficult because sensor data are usually sparse, sensor locations may be irregular, and the thermal field can have complex spatial variations.

This is similar to data center environments, where sensors are limited and rack layouts are different.

---

### 3. Reconstruction Method
The paper proposes an INR-based method called MMGN.

Instead of reconstructing a fixed image only, the model learns a continuous field representation using spatial coordinates and latent information.

---

### 4. Input and Output
**Input:**
- Sparse observation values
- Spatial coordinates

For our framework, the input can be:
- Server temperature / power
- iBox inlet temperature
- PDU power data
- Rack position information

**Output:**
- Reconstructed continuous thermal map

---

### 5. Training Data and Data Source
The paper uses both simulation-based climate data and satellite-based sea surface temperature data.

This shows that the method can work with simulated data and real-world observation data.

---

### 6. Evaluation Metrics
The paper mainly uses MSE to evaluate reconstruction error.

It also discusses PSNR and SSIM for evaluating reconstruction quality and structural similarity.

---

### 7. Experimental Results
The proposed MMGN method outperforms several INR baseline models, especially when the observation data are very sparse.

This supports the idea that sparse sensor data can still be used to reconstruct a reliable full field.

---

### 8. Limitations
The method is not directly designed for data center thermal management.

Also, the paper mainly focuses on reconstruction, not cooling control or long-term thermal forecasting.

---

### 9. Relation to Our Framework
This paper can support the thermal map reconstruction part of our framework.

We can refer to the following ideas:

- Sparse observation to full thermal map reconstruction
- Using latent code to represent the overall thermal state
- Using spatial coordinates to reconstruct a continuous thermal field
- Handling different sensor numbers and sensor locations
- Extending Server / iBox / PDU data into a full rack-level thermal map

Possible connection:
```mermaid
flowchart TB

    A["Server / iBox / PDU Data"]

    B["Sparse Thermal Observation"]

    C["Latent Representation"]

    D["INR / MMGN / U-Net Reconstruction"]

    E["Rack-Level Thermal Map"]

    F["Cooling Decision"]

    A --> B
    B --> C
    C --> D
    D --> E
    E --> F
```
# Paper Review: Leakage-Aware Cooling Management for Improving Server Energy Efficiency. (2015)
## Reference:
M. Zapater,et al,"Leakage-Aware Cooling Management for Improving Server Energy Efficiency," IEEE Transactions on Parallel and Distributed Systems, vol. 26, no. 10, pp. 2764-2777, Oct. 1, 2015.

<div align="justify">

| Item              | Description                                                                                                    |
| ----------------- | -------------------------------------------------------------------------------------------------------------- |
| **Paper**         | *Leakage-Aware Cooling Management for Improving Server Energy Efficiency*                                      |                                                                                                           |
| **Main Focus**    | Leakage-aware cooling management for improving server energy efficiency                                        |
| **Main Method**   | Empirical power and temperature modeling with proactive fan speed control                                      |
| **Target System** | Enterprise server and data center cooling environment                                                          |
| **DOI**           | 10.1109/TPDS.2014.2361519                                                                                      |

</div>

---

### 1. Application Domain

<div align="justify">

This paper focuses on **server-level cooling management and energy optimization** in data centers. The main goal is to reduce server energy consumption by considering the interaction among computational power, temperature, leakage power, fan power, and workload allocation.

Instead of treating cooling control as a simple temperature regulation problem, this paper argues that cooling decisions should consider both:

* **Fan power**, which increases when the fan speed becomes higher
* **CPU leakage power**, which increases when the chip temperature becomes higher

Therefore, the best cooling condition is not necessarily the lowest fan speed or the lowest temperature. The goal is to find the fan speed that minimizes the total energy cost caused by both leakage power and fan power.

</div>

---

### 2. Challenge

<div align="justify">

The main challenge addressed in this paper is the trade-off between **cooling power** and **leakage power**.

If the fan speed is too high, the server temperature decreases, but the fan consumes more power. If the fan speed is too low, fan power decreases, but CPU temperature increases, which causes higher leakage power. Therefore, cooling control must find an optimal balance between fan power and leakage power.

Another challenge is that different workloads create different power and temperature behaviors. A CPU-intensive workload and a memory-intensive workload may require different optimal fan speeds. This means that a fixed fan speed policy cannot always provide the best energy efficiency.

Workload allocation also creates another challenge. If workloads are clustered on a small number of cores or sockets, some CPUs may become hotter than others. If workloads are distributed across more cores, the thermal profile may become more balanced, but more active cores may also increase power consumption. Therefore, fan control should be robust to different workload allocation policies.

Finally, the paper points out that simple metrics such as CPU utilization or IPC are not sufficient to estimate dynamic CPU power accurately. The same utilization level can correspond to different CPU power values depending on the workload characteristics.

</div>

---

### 3. Assumption

<div align="justify">

This paper makes several important assumptions for modeling and control.

First, the authors assume that the temperature-dependent leakage power of the server is mainly caused by the CPUs. Other components such as memory, disk, and network devices also consume power, but their temperature-dependent leakage contribution is less significant in this study.

Second, memory power is assumed to be mainly related to the memory access rate rather than temperature. Therefore, memory dynamic power can be modeled using the number of read/write memory accesses per second.

Third, CPU steady-state temperature is assumed to be predictable from CPU dynamic power and fan speed. Under a fixed fan speed, a higher CPU dynamic power generally leads to a higher steady-state CPU temperature.

Fourth, the authors assume that temperature changes more slowly than power changes. Since thermal time constants are in the order of minutes, the fan speed does not need to change every second. This helps avoid unnecessary fan speed oscillation and improves fan reliability.

</div>

---

### 4. Proposed Solution

<div align="justify">

The paper proposes a **leakage-aware proactive fan control policy**. The purpose of this policy is to dynamically choose the fan speed that minimizes the sum of CPU leakage power and fan power.

The optimization target can be expressed as:

```text
Minimize: Leakage Power + Fan Power
```

The proposed solution includes three main modeling steps and one control step.

#### 4.1 Server Power Model

The total server power is divided into three parts:
```math
P_{\text{server}} = P_{\text{static}} + P_{\text{dynamic}} + P_{\text{fan}}
```

| Term        | Meaning                                                                    |
| ----------- | -------------------------------------------------------------------------- |
|`P_static`  | Static power, including idle power and temperature-dependent leakage power |
| `P_dynamic` | Dynamic power caused by workload execution                                 |
| `P_fan`     | Cooling power consumed by server fans                                      |

The dynamic power is further divided into:

```math
P_{\text{dynamic}} = P_{\text{CPU,dyn}} + P_{\text{mem,dyn}} + P_{\text{other,dyn}}
```
This decomposition allows the system to separately analyze CPU power, memory power, other component power, and fan power.

#### 4.2 CPU Leakage Model

The CPU power is modeled as:

```math
P_{\text{CPU}} = P_{\text{CPU,idle}} + P_{\text{CPU,leakT}} + P_{\text{CPU,dyn}}
```

| Term          | Meaning                                        |
| ------------- | ---------------------------------------------- |
| `P_CPU,idle`  | CPU idle power                                 |
| `P_CPU,leakT` | Temperature-dependent CPU leakage power        |
| `P_CPU,dyn`   | Dynamic CPU power caused by workload execution |

Since leakage power increases with temperature, the authors use CPU temperature to estimate temperature-dependent leakage power.

#### 4.3 CPU Temperature Model

The paper also builds a CPU temperature model to estimate the steady-state CPU temperature under different fan speeds. The model predicts the temperature that a workload may reach based on CPU dynamic power and fan speed.

This is important because the fan controller needs to know what the temperature and leakage power would be if a different fan speed were selected.

#### 4.4 Proactive Fan Control Policy

The proactive fan control policy works as follows:

```mermaid
flowchart TB
    A["Measure CPU temperature and CPU power"] --> B["Estimate CPU leakage power"]
    B --> C["Estimate CPU dynamic power"]
    C --> D["Predict CPU temperature under each fan speed"]
    D --> E["Estimate leakage power and fan power for each fan speed"]
    E --> F["Select the fan speed with minimum leakage + fan power"]
```

The policy does not wait until a thermal emergency occurs. Instead, it predicts the effect of each possible fan speed and proactively selects the best one.

</div>

---

#### 5. Evaluation Environment

<div align="justify">

The evaluation is mainly based on **real experiments** using a commercial enterprise server.

| Component                   | Description                            |
| --------------------------- | -------------------------------------- |
| **Processor**               | Two SPARC T3 processors                |
| **Hardware Threads**        | 256 hardware threads                   |
| **Memory**                  | 32 × 8 GB DIMMs                        |
| **Storage**                 | Two hard drives                        |
| **Fan Speed Range**         | 1800 RPM to 4200 RPM                   |
| **Sensor Polling Interval** | 1 second                               |
| **Fan Control Method**      | External Agilent E3644A power supplies |

The collected telemetry data includes:

* CPU temperature
* Memory temperature
* Per-CPU voltage
* Per-CPU current
* Total server power
* Fan speed
* Workload-related hardware counters

For model training, the paper uses two synthetic workloads:

| Workload    | Purpose                                               |
| ----------- | ----------------------------------------------------- |
| **LoadGen** | Generates controllable CPU utilization and CPU stress |
| **RandMem** | Generates controllable memory access behavior         |

For validation and policy evaluation, the paper uses real benchmark suites:

| Benchmark              | Purpose                                            |
| ---------------------- | -------------------------------------------------- |
| **SPEC Power_ssj2008** | Evaluates server power and performance             |
| **SPEC CPU2006**       | Tests CPU-intensive and memory-intensive workloads |
| **PARSEC**             | Tests multi-threaded workload behavior             |

The paper also includes a larger-scale trace-based evaluation using power traces from a real data center cluster at the Madrid Supercomputing and Visualization Center. This part evaluates how the proposed policy may perform in a broader data center environment.

</div>

---

#### 6. Key Result

<div align="justify">

The experimental results show that the proposed proactive fan control policy can reduce energy consumption without performance loss.

The main results are summarized below:

| Result                             | Description                                                                       |
| ---------------------------------- | --------------------------------------------------------------------------------- |
| **Leakage + fan energy reduction** | Up to 6% compared with existing policies                                          |
| **CPU energy reduction**           | More than 9% compared with the default server control policy                      |
| **Workload allocation benefit**    | Up to 15% energy saving when using the best energy-delay product allocation       |
| **Data center trace result**       | Around 2.5% CPU power reduction for the whole cluster at 27°C ambient temperature |
| **Performance impact**             | No performance penalty reported                                                   |

The results show that considering leakage power is important for energy-efficient cooling control. The proposed policy performs better than fixed fan speed, TAPO, bang-bang control, and LUT-based fan control because it directly estimates the leakage and fan power trade-off.

</div>

---

#### 7. Relevance to Proposed Framework

<div align="justify">

This paper is highly relevant to the **optimization layer** of the proposed data center thermal prediction and power optimization framework.

The proposed framework can be connected to this paper as follows:

```mermaid
flowchart TB
    A["Redfish / PDU / iBox Telemetry"] --> B["XGBoost / LightGBM Prediction Layer"]
    B --> C["Server-Level or Rack-Level Temperature Prediction"]
    C --> D["Thermal State Estimation"]
    D --> E["Cooling Optimization Layer"]
    E --> F["Fan Speed / Cooling Setpoint / Workload Placement Decision"]
```

This paper supports several important ideas in the proposed framework:

| Proposed Framework Part            | Support from This Paper                                                                                   |
| ---------------------------------- | --------------------------------------------------------------------------------------------------------- |
| **Server telemetry features**      | CPU temperature, server power, fan speed, and workload counters are useful for thermal and power modeling |
| **Power-temperature relationship** | Server energy depends on the interaction among power, temperature, leakage, and cooling                   |
| **Cooling optimization**           | Fan speed can be selected dynamically to reduce energy consumption                                        |
| **Workload-aware management**      | Different workload allocation policies change temperature and leakage behavior                            |
| **Energy-aware objective**         | Optimization should consider not only hotspot prevention but also leakage power and fan power             |

This paper can be used to support the idea that thermal prediction should not stop at temperature estimation. The prediction result should be connected to cooling control and energy optimization decisions.

</div>

---

#### 8. Limitation

<div align="justify">

Although this paper provides a strong server-level cooling optimization method, it still has several limitations with respect to the proposed rack-level thermal prediction framework.

First, the paper focuses mainly on **single-server-level fan control**. It does not directly reconstruct rack-level or room-level thermal maps.

Second, the paper does not use XGBoost, LightGBM, U-Net, or other deep learning models. Instead, it uses empirical power and temperature models.

Third, the output of the system is an optimized fan speed, not a spatial thermal heatmap. Therefore, it does not directly provide hotspot location or room-level thermal distribution.

Fourth, the method assumes that fan speed can be directly controlled. In a real data center, direct fan control may not always be available depending on server management permissions and hardware constraints.

Fifth, the paper does not consider rack metadata such as U position, rack placement, PDU outlet-level power, or spatial server arrangement. These factors are important for rack-level thermal prediction.

</div>

---

#### 9. Takeaway

<div align="justify">

Zapater et al. supports the **cooling optimization layer** of the proposed framework.

The key idea of this paper is that cooling management should not only minimize temperature. Instead, it should balance:

* Fan power
* CPU leakage power
* Workload behavior
* Workload allocation
* Server performance

For the proposed framework, this paper can be used as evidence that temperature prediction should be connected to energy-aware control actions. It is especially useful for supporting fan speed control, cooling setpoint adjustment, and workload-aware thermal optimization.

</div>

> [!NOTE]
> **Takeaway**
>
> This paper supports the idea that prediction alone is not enough. A complete thermal management framework should connect temperature prediction with leakage-aware cooling control and energy optimization.

---

#### Reference

Zapater, M., Tuncer, O., Ayala, J. L., Moya, J. M., Vaidyanathan, K., Gross, K., & Coskun, A. K. (2015). *Leakage-Aware Cooling Management for Improving Server Energy Efficiency*. IEEE Transactions on Parallel and Distributed Systems, 26(10), 2764-2777. DOI: 10.1109/TPDS.2014.2361519.
