# Experiment 01–10 Relationship Summary

## Model Input and Experimental Settings

### Experiment 01

- Experiment 01 used 1-minute sampled data.
- The model input features were:
  - `CPU temperature`
  - `Inlet temperature`
  - `Fan RPM`
  - `Server power`

---

### Experiment 02 to Experiment 06

- From Experiment 02 to Experiment 06, the data was changed to fixed 5-minute sampling.
- The model input features were kept the same as Experiment 01:
  - `CPU temperature`
  - `Inlet temperature`
  - `Fan RPM`
  - `Server power`

- If multiple sensors of the same type existed at the same timestamp, the average value was used as the representative input value.

---

### Experiment 07

- Experiment 07 compared two CPU temperature aggregation methods:
  - `CPU temperature mean`
  - `CPU temperature max`

- The purpose was to compare whether using the average CPU temperature or the maximum CPU temperature was more suitable for CPU temperature prediction.

- Other input features were kept the same:
  - `Inlet temperature`
  - `Fan RPM`
  - `Server power`

- The data was fixed 5-minute sampled data.

---

### Experiment 08 and Experiment 09

- Experiment 08 and Experiment 09 focused on a single server, `Lavoisier`.
- Lavoisier was selected because it had larger CPU temperature variation.
- Both experiments used fixed 5-minute sampled data.
- The selected input features were:
  - `CPU temperature`
  - `Fan RPM`
  - `Server power`

- `Inlet temperature` was not included in Experiment 08 and Experiment 09 because the available Lavoisier dataset did not contain usable inlet temperature data.

---

### Data Split

- All experiments used the same data split ratio:
  - 70% training set
  - 15% validation set
  - 15% test set

- The split was performed according to time order to avoid data leakage.

---

### Evaluation Metrics

- All experiments were evaluated using the same metrics:
  - `MAE`
  - `RMSE`
  - `Max Error`
## Overall Experiment Logic

The experimental flow of this study was designed step by step, starting from data preprocessing and model construction, then moving toward baseline comparison, feature analysis, lag analysis, server selection, and finally increasing the data log length. Each experiment was designed based on the result of the previous experiment, so the experiments are not independent but logically connected.

---

## 1. Overall Experiment Relationship Table

| Relationship | Comparison Purpose | Result | Decision for Next Step |
|---|---|---|---|
| Exp01 → Exp02 | Compare irregular valid observations with fixed 5-minute sampling | Fixed 5-minute sampling achieved lower error and clearer time meaning | Use fixed 5-minute sampling for the following experiments |
| Exp02 → Exp03 | Compare different prediction horizons | Longer horizons produced higher prediction errors | Keep 5 / 10 / 15 minutes as prediction horizons |
| Exp03 → Exp04 | Compare different input features | CPU temperature lag was the most important feature | Use CPU temperature as the main feature and add power / fan when needed |
| Exp04 → Exp05 | Compare XGBoost with Persistence baseline | Persistence clearly outperformed XGBoost | All following models should be compared with Persistence baseline |
| Exp05 → Exp06 | Test whether increasing lag length improves the model | Increasing lag length did not improve the model | Use a shorter lag setting such as `t`, `t-1`, `t-2` |
| Exp06 → Exp07 | Compare CPU temperature mean and max | CPU mean was more stable than CPU max | Use CPU mean as the main CPU temperature value |
| Exp07 → Exp08 | Select a server with larger temperature variation | Lavoisier had the largest temperature variation | Use Lavoisier as the single-server case study |
| Exp08 → Exp09 | Increase Lavoisier log length | 2-day data significantly improved XGBoost performance | Data length is likely an important factor for XGBoost |
| Exp09 → Exp10 | Further increase log length | XGBoost started to outperform Persistence in 15-minute RMSE | Next step is to test 5-day or 7-day logs |

---

# 2. Experiment-by-Experiment Comparison

## Exp01 vs Exp02: Confirming that Fixed 5-Minute Sampling Is More Suitable

### Comparison Purpose

Exp01 used the original valid observations for training. However, because the time interval between observations was not fixed, `shift(-10)` only represented the 10th future valid observation, not necessarily the actual CPU temperature 10 minutes later.

Exp02 converted the data into fixed 5-minute sampling, so each data point had a clear time meaning.

### Result Table

| Experiment | Sampling Method | Target Meaning | Samples | MAE | RMSE | Max Error |
|---|---|---|---:|---:|---:|---:|
| Exp01 | Valid observations | 10th future valid observation | 2585 | 1.008°C | 1.369°C | 4.630°C |
| Exp02 | 5-minute resample | Actual 10 minutes later | 2252 | 0.624°C | 0.903°C | 3.977°C |

### Conclusion

After converting the data to fixed 5-minute sampling, the prediction error decreased and the target became more meaningful in time. Therefore, all following experiments used fixed 5-minute sampling as the model input.

---

## Exp02 vs Exp03: Effect of Different Prediction Horizons

### Comparison Purpose

Exp02 only predicted CPU temperature 10 minutes later. Exp03 further tested 5-minute, 10-minute, and 15-minute prediction horizons to observe whether a longer horizon increases prediction difficulty.

### Result Table

| Horizon | Samples | Train | Validation | Test | MAE | RMSE | Max Error |
|---|---:|---:|---:|---:|---:|---:|---:|
| 5 min | 2260 | 1582 | 339 | 339 | 0.482°C | 0.674°C | 2.651°C |
| 10 min | 2252 | 1576 | 338 | 338 | 0.624°C | 0.903°C | 3.977°C |
| 15 min | 2244 | 1570 | 337 | 337 | 0.744°C | 1.094°C | 4.370°C |

### Conclusion

The prediction error generally increased as the prediction horizon became longer. The 5-minute prediction was the easiest, while the 15-minute prediction was more difficult. Therefore, the following experiments kept 5 / 10 / 15 minutes as the main prediction horizons.

---

## Exp03 vs Exp04: Checking Whether Input Features Are Actually Helpful

### Comparison Purpose

Exp03 used all features, including `cpu_temp`, `inlet_temp`, `server_power`, and `fan_rpm`. Exp04 used feature ablation to test different feature combinations and determine which features were truly useful for prediction.

### Result Table

| Feature Set | Features | Input Feature Count | MAE | RMSE | Max Error | Ranking |
|---|---|---:|---:|---:|---:|---:|
| F0 | `cpu_temp` | 3 | 0.532°C | 0.727°C | 2.675°C | 1 |
| F1 | `cpu_temp`, `server_power` | 6 | 0.571°C | 0.794°C | 3.919°C | 2 |
| F3 | `cpu_temp`, `inlet_temp` | 6 | 0.606°C | 0.871°C | 3.383°C | 3 |
| F4 | `cpu_temp`, `server_power`, `fan_rpm`, `inlet_temp` | 12 | 0.637°C | 0.933°C | 4.253°C | 4 |
| F2 | `cpu_temp`, `fan_rpm` | 6 | 0.678°C | 0.980°C | 4.274°C | 5 |

### Conclusion

In the 24-hour all-server dataset, using only historical CPU temperature achieved the best performance. Adding power, fan speed, or inlet temperature did not improve the model. This may be because the data was relatively stable, and CPU temperature itself already contained the main predictive information. Other features may have introduced noise or missing-value effects.

Therefore, CPU temperature lag was identified as the most important input feature for short-term CPU temperature prediction.

---

## Exp04 vs Exp05: Checking Whether XGBoost Truly Outperforms a Simple Baseline

### Comparison Purpose

Exp04 showed that CPU-only XGBoost achieved the best result among the feature combinations. However, this did not prove that the machine learning model was truly useful. Therefore, Exp05 introduced the Persistence baseline.

The idea of Persistence baseline is:

```text
Future temperature = Current temperature
```

### Result Table

| Horizon | XGBoost MAE | Persistence MAE | XGBoost RMSE | Persistence RMSE | Better Method |
|---|---:|---:|---:|---:|---|
| 5 min | 0.482°C | 0.367°C | 0.674°C | 0.588°C | Persistence |
| 10 min | 0.624°C | 0.442°C | 0.903°C | 0.657°C | Persistence |
| 15 min | 0.744°C | 0.483°C | 1.094°C | 0.714°C | Persistence |

### Conclusion

Persistence baseline clearly outperformed XGBoost. This indicates that CPU temperature in the current dataset was highly stable in the short term and had strong temporal inertia.

This also shows that a model should not only be evaluated by its absolute error. It must be compared with a simple baseline to determine whether it truly learns additional useful information.

---

## Exp05 vs Exp06: Testing Whether Increasing Lag Length Improves XGBoost

### Comparison Purpose

Since Persistence performed well, the current temperature was clearly important. Therefore, Exp06 tested whether adding more historical lag features could help XGBoost learn a more complete temperature trend.

### Result Table

| Lag Setting | Lags | History Length | Input Feature Count | MAE | RMSE | Max Error |
|---|---|---|---:|---:|---:|---:|
| L0 | `[0]` | Current only | 4 | 0.555°C | 0.810°C | 3.801°C |
| L1 | `[0, 1]` | Current + 5 min | 8 | 0.581°C | 0.830°C | 3.802°C |
| L2 | `[0, 1, 2]` | Current + 10 min | 12 | 0.624°C | 0.903°C | 3.977°C |
| L3 | `[0, 1, 2, 3]` | Current + 15 min | 16 | 0.643°C | 0.932°C | 3.860°C |
| L4 | `[0, 1, 2, 3, 6]` | Current + 30 min | 20 | 0.658°C | 0.953°C | 3.800°C |
| L5 | `[0, 1, 2, 3, 6, 12]` | Current + 60 min | 24 | 0.625°C | 0.906°C | 3.789°C |

### Conclusion

Increasing the lag length did not improve XGBoost. Instead, the error increased in most cases. This means that longer historical information did not provide clear additional benefit in the current dataset. Short-term prediction still mainly depended on the current temperature.

Therefore, the following experiments used a shorter lag setting, such as `t`, `t-1`, and `t-2`, to avoid introducing too much noise.

---

## Exp06 vs Exp07: Comparing CPU Temperature Aggregation Methods

### Comparison Purpose

In CortexDC, one server may have multiple CPU temperature sensors. Exp07 compared using the mean and max of multiple CPU temperature sensors to determine which aggregation method was more suitable for prediction.

### Result Table

| CPU Temperature Method | Samples | Input Feature Count | MAE | RMSE | Max Error |
|---|---:|---:|---:|---:|---:|
| Mean of CPU sensors | 2252 | 12 | 0.624°C | 0.903°C | 3.977°C |
| Max of CPU sensors | 2252 | 12 | 0.730°C | 0.999°C | 4.125°C |

### Conclusion

Using the mean of CPU sensors achieved better prediction performance. This suggests that the mean value is more stable and more suitable for general CPU temperature prediction.

Although CPU max can reflect hotspot or overheating risk, it is more sensitive to fluctuations and may not be ideal for general temperature prediction. Therefore, the following experiments mainly used CPU mean as the CPU temperature value.

---

## Exp07 vs Exp08: Selecting a Server with Larger Temperature Variation

### Comparison Purpose

The previous all-server dataset was generally stable, which made Persistence baseline very strong. Therefore, Exp08 searched for the server with the largest CPU temperature variation to test whether XGBoost would have more advantage under larger temperature changes.

### Server Variation Table

| Server | Count | Mean | Std | Min | Max | Range |
|---|---:|---:|---:|---:|---:|---:|
| Lavoisier | 287 | 33.635°C | 2.992°C | 26.0°C | 39.0°C | 13.0°C |
| Quine | 288 | 46.942°C | 1.591°C | 44.0°C | 52.0°C | 8.0°C |
| Maxwell | 287 | 50.564°C | 0.947°C | 49.0°C | 53.0°C | 4.0°C |
| Inoue | 284 | 66.288°C | 0.894°C | 64.5°C | 68.5°C | 4.0°C |
| Kepler | 283 | 38.696°C | 0.887°C | 37.0°C | 41.0°C | 4.0°C |
| Joule | 282 | 36.554°C | 0.815°C | 34.5°C | 39.0°C | 4.5°C |
| Newton | 284 | 41.911°C | 0.766°C | 40.0°C | 44.0°C | 4.0°C |
| Davinci | 273 | 55.743°C | 0.211°C | 55.5°C | 57.0°C | 1.5°C |

### Conclusion

Lavoisier had the largest temperature variation, so it was selected as the single-server case study.

This changed the research direction from an all-server average case to a high-variation single-server case. The purpose was to observe whether XGBoost could learn more useful patterns when the temperature variation became more obvious.

---

## Exp08 vs Exp09: Checking Whether Increasing Single-Server Data Length Improves the Model

### Comparison Purpose

Although Exp08 selected Lavoisier, the dataset only contained 24 hours of data, and the number of training samples was too small. As a result, XGBoost performed poorly. Therefore, Exp09 increased the Lavoisier data length to 2 days to observe whether the model improved.

### Result Table

| Dataset | Server | Horizon | Samples | Train | Validation | Test | XGBoost MAE | XGBoost RMSE | Max Error |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| 24-hour | Lavoisier | 10 min | 285 | 199 | 43 | 43 | 2.468°C | 2.978°C | 5.316°C |
| 2-day | Lavoisier | 10 min | 513 | 359 | 77 | 77 | 0.762°C | 0.990°C | 2.726°C |

### Conclusion

When the Lavoisier data length increased from 24 hours to 2 days, the MAE and RMSE of XGBoost decreased significantly. This suggests that the poor XGBoost performance in the previous single-server experiment was likely caused by insufficient data, rather than the model being unable to learn temperature patterns.

Therefore, for single-server prediction, increasing log length is important for improving XGBoost model stability.

---

## Exp09: Lavoisier 2-day XGBoost vs Persistence

### Comparison Purpose

Although XGBoost improved significantly on the Lavoisier 2-day dataset, it still needed to be compared with Persistence baseline to verify whether the model truly outperformed a simple method.

### Result Table

| Horizon | XGBoost MAE | Persistence MAE | Better MAE | XGBoost RMSE | Persistence RMSE | Better RMSE | XGBoost Max Error | Persistence Max Error |
|---|---:|---:|---|---:|---:|---|---:|---:|
| 5 min | 0.701°C | 0.658°C | Persistence | 0.933°C | 0.866°C | Persistence | 2.951°C | 2.333°C |
| 10 min | 0.762°C | 0.589°C | Persistence | 0.990°C | 0.850°C | Persistence | 2.726°C | 3.000°C |
| 15 min | 0.643°C | 0.613°C | Persistence | 0.861°C | 0.918°C | XGBoost | 2.554°C | 3.000°C |

### Conclusion

Persistence still achieved lower MAE, which means that Lavoisier CPU temperature still had strong short-term temporal inertia.

However, in the 15-minute prediction, XGBoost achieved lower RMSE and lower Max Error. This means that although its average error was still slightly higher, XGBoost started to reduce larger prediction errors.

This suggests that XGBoost may have started learning the influence of `server_power`, `fan_rpm`, and historical temperature trends for longer prediction horizons.

---

## Exp09 → Exp10: Why the Next Step Should Increase Log Length

### Comparison Purpose

From Exp08 to Exp09, increasing the Lavoisier data length significantly improved XGBoost performance. Therefore, Exp10 should further increase the log length to observe whether the model continues to improve.

### Evidence Table

| Dataset | Log Length | Samples | XGBoost MAE | XGBoost RMSE |
|---|---:|---:|---:|---:|
| Lavoisier 24-hour | 1 day | 285 | 2.468°C | 2.978°C |
| Lavoisier 2-day | 2 days | 513 | 0.762°C | 0.990°C |

### 15-minute Result Evidence

| Horizon | XGBoost RMSE | Persistence RMSE | Better RMSE |
|---|---:|---:|---|
| 15 min | 0.861°C | 0.918°C | XGBoost |

### Exp10 Suggested Design

| Item | Setting |
|---|---|
| Server | Lavoisier |
| Sampling interval | 5 minutes |
| Features | `cpu_temp`, `server_power`, `fan_rpm` |
| Lag setting | `t`, `t-1`, `t-2` |
| Prediction horizons | 5 / 10 / 15 minutes |
| Model | XGBoost Regressor |
| Baseline | Persistence |
| Data split | 70% train / 15% validation / 15% test |

### Suggested Log Length

| Experiment | Log Length | Purpose |
|---|---:|---|
| Exp10-A | 3 days | Check whether the model continues to improve |
| Exp10-B | 5 days | Increase data amount and observe model stability |
| Exp10-C | 7 days | Check whether the model can learn a more complete temperature trend |

### Conclusion

The current results suggest that XGBoost has started to learn some useful feature information, but the data length is still not enough for it to consistently outperform Persistence in MAE.

Therefore, Exp10 should increase the log length to 5 days or 7 days while keeping the server, features, lag setting, model parameters, and data split fixed. Only the data length should be changed to observe whether XGBoost can further improve with more training data.

---

# 3. Final Integrated Conclusion Table

| Finding | Related Experiments | Evidence | Meaning |
|---|---|---|---|
| Fixed 5-minute sampling is more suitable | Exp01 vs Exp02 | MAE decreased from 1.008°C to 0.624°C | Fixed sampling gives a clearer target time and better model performance |
| Longer horizon is harder to predict | Exp02 vs Exp03 | 5-min MAE = 0.482°C, 15-min MAE = 0.744°C | Prediction uncertainty increases as horizon becomes longer |
| CPU temperature is the most important feature | Exp03 vs Exp04 | CPU-only MAE = 0.532°C, all-features MAE = 0.637°C | Short-term temperature is mainly determined by historical CPU temperature |
| Persistence baseline is very strong | Exp04 vs Exp05 | Persistence outperformed XGBoost for 5 / 10 / 15 min | CPU temperature has strong short-term temporal inertia |
| Increasing lag length does not improve the model | Exp05 vs Exp06 | L0 MAE = 0.555°C, L4 MAE = 0.658°C | Too many historical features may introduce noise |
| CPU mean is better than CPU max | Exp06 vs Exp07 | CPU mean MAE = 0.624°C, CPU max MAE = 0.730°C | Mean is more stable and better for general temperature prediction |
| Lavoisier is the high-variation server | Exp07 vs Exp08 | Lavoisier range = 13.0°C, std = 2.992°C | Lavoisier is suitable for single-server case study |
| Single-server data length affects XGBoost | Exp08 vs Exp09 | 24-hour MAE = 2.468°C, 2-day MAE = 0.762°C | Increasing data length significantly improves model stability |
| XGBoost starts reducing large errors | Exp09 | 15-min RMSE: XGBoost = 0.861°C, Persistence = 0.918°C | XGBoost may be learning power, fan, and lag trends |
| Next step should increase log length | Exp09 → Exp10 | 2-day data greatly improved over 24-hour data | 5-day or 7-day data should be tested next |

---

# 4. Final Summary
- Fixed 5-minute sampling is more suitable for CPU temperature prediction.
  - It gives the prediction target a clear time meaning.
  - It also reduces model error compared with irregular valid observations.

- Longer prediction horizons are more difficult.
  - 5-minute prediction has the lowest error.
  - 15-minute prediction has higher uncertainty.

- CPU temperature lag is the most important input feature.
  - Adding server power, fan speed, or inlet temperature did not improve the 24-hour all-server model.
  - This may be because the data was too stable.

- Persistence baseline outperformed XGBoost in most short-term predictions.
  - This shows that CPU temperature has strong temporal inertia.
  - The current temperature is already a strong predictor of near-future temperature.

- Increasing lag length did not improve XGBoost.
  - Longer historical windows may introduce noise.
  - A shorter lag setting such as `t`, `t-1`, and `t-2` is more suitable.

- Lavoisier was selected as the high-variation server.
  - It had the largest CPU temperature range among the tested servers.
  - Therefore, it was used for the single-server case study.

- The 24-hour Lavoisier XGBoost result was poor.
  - This was likely caused by insufficient single-server data.

- Increasing the Lavoisier log length to 2 days significantly improved XGBoost.
  - For 10-minute prediction, MAE decreased from 2.468°C to 0.762°C.
  - This shows that increasing log length can improve model stability.

- XGBoost still did not fully outperform Persistence in MAE.
  - However, in the 15-minute prediction, XGBoost achieved lower RMSE and Max Error.
  - This suggests that XGBoost may have started learning useful trends from server power, fan speed, and historical temperature data.

- The next step is to increase the Lavoisier log length to 5 or 7 days.
  - Preprocessing, features, lag setting, model parameters, and data split should remain fixed.
  - Only the data length should be changed.
  - This can verify whether XGBoost continues to improve with more data and eventually approaches or outperforms Persistence baseline.
