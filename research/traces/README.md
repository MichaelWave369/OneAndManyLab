# Measured capacity trace excerpt (CC BY 4.0)

`chorus_cellular_airport_excerpt.csv` reproduces the first 51 timestamp/bandwidth rows (0–10 seconds inclusive) of `bw_traces/downlink-cellular_airport.csv` from:

Gerui Lv et al. (2024), **Chorus: Coordinating Mobile Multipath Scheduling and Adaptive Video Streaming**, ACM MobiCom 2024, DOI: https://doi.org/10.1145/3636534.3649359.

Original measured data and credit: https://github.com/GreenLv/Chorus/blob/main/bw_traces/downlink-cellular_airport.csv
License: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), as documented by the Chorus repository. This shortened excerpt is redistributed with attribution. The original bandwidth values are unchanged. The source describes the data as real-world cellular bandwidth measurements. **They are not packet loss recordings.** Our simulator uses measured throughput samples only as *link service capacity*; all erasures, feedback controls, and payload observations remain synthetic.

The time series is deliberately short for an auditable initial benchmark; the code also supports a user-supplied CSV with the same two columns, e.g. `--trace custom.csv`.
