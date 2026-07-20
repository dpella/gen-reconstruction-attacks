# Anonymeter risk on the decoy-augmented datasets

Each row: 10 % reconstructable core + 90 % decoys. `risk_value` is `(attack_rate − control_rate) / (1 − control_rate)`; `ci` is Anonymeter's 95 % confidence interval. Anonymeter reports a risk statistically indistinguishable from 0 in every schema, even though M·s = b reconstructs every core record exactly.

| Schema | core | total | risk (95 % CI) | attack | control | verdict |
|---|---:|---:|---|---:|---:|---|
| `sdtm_vs` | 16 | 160 | 0.0000  [0.0000, 1.0000] | 0.903 | 0.903 | indistinguishable from 0 |
| `adam_adsl` | 32 | 320 | 0.0000  [0.0000, 1.0000] | 0.946 | 0.946 | indistinguishable from 0 |
| `adam_adlb` | 64 | 640 | 0.0000  [0.0000, 1.0000] | 0.972 | 0.972 | indistinguishable from 0 |
| `adam_adpc` | 128 | 1280 | 0.0000  [0.0000, 1.0000] | 0.985 | 0.985 | indistinguishable from 0 |
| `adam_adpc_extended` | 256 | 2560 | 0.0000  [0.0000, 1.0000] | 0.993 | 0.993 | indistinguishable from 0 |
| `hr_open_n256` | 256 | 2560 | 0.0000  [0.0000, 1.0000] | 0.993 | 0.993 | indistinguishable from 0 |
| `hr_open_n512` | 512 | 5120 | 0.0000  [0.0000, 1.0000] | 0.996 | 0.996 | indistinguishable from 0 |
| `eurostat_silc_n128` | 128 | 1280 | 0.0000  [0.0000, 1.0000] | 0.985 | 0.985 | indistinguishable from 0 |
| `eurostat_silc_n512` | 512 | 5120 | 0.0000  [0.0000, 1.0000] | 0.996 | 0.996 | indistinguishable from 0 |
