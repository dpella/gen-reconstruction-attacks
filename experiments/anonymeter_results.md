# Anonymeter risk on the decoy-augmented datasets

Each row: 10 % reconstructable core + 90 % decoys. `risk_value` is `(attack_rate − control_rate) / (1 − control_rate)`; `ci` is Anonymeter's 95 % confidence interval. Anonymeter reports a risk statistically indistinguishable from 0 in every schema, even though M·s = b reconstructs every core record exactly.

| Schema | core | total | risk (95 % CI) | attack | control | verdict |
|---|---:|---:|---|---:|---:|---|
| `sdtm_vs` | 16 | 160 | 0.0000  [0.0000, 0.2745] | 0.114 | 0.281 | indistinguishable from 0 |
| `adam_adsl` | 32 | 320 | 0.0000  [0.0000, 0.1305] | 0.064 | 0.195 | indistinguishable from 0 |
| `adam_adlb` | 64 | 640 | 0.0000  [0.0000, 0.0577] | 0.034 | 0.121 | indistinguishable from 0 |
| `adam_adpc` | 128 | 1280 | 0.0000  [0.0000, 0.0254] | 0.018 | 0.067 | indistinguishable from 0 |
| `adam_adpc_extended` | 256 | 2560 | 0.0000  [0.0000, 0.0117] | 0.009 | 0.035 | indistinguishable from 0 |
| `hr_open_n256` | 256 | 2560 | 0.0000  [0.0000, 0.0117] | 0.009 | 0.035 | indistinguishable from 0 |
| `hr_open_n512` | 512 | 5120 | 0.0000  [0.0000, 0.0056] | 0.005 | 0.018 | indistinguishable from 0 |
| `eurostat_silc_n128` | 128 | 1280 | 0.0000  [0.0000, 0.0254] | 0.018 | 0.067 | indistinguishable from 0 |
| `eurostat_silc_n512` | 512 | 5120 | 0.0000  [0.0000, 0.0056] | 0.005 | 0.018 | indistinguishable from 0 |
