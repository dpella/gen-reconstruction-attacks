# Privacy-metric results on the decoy-augmented datasets

Every row: 10 % reconstructable core + 90 % decoys. All metrics rate the releases as low-risk even though `M·s = b` recovers every core record exactly.

| Schema | n core | n total | Anonymeter risk | attack | control | synthcity XGB | synthcity Ident. | Privacy Meter MRE | R² | ±5 % succ. | ±5 % control |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `sdtm_vs` | 16 | 160 | 0.0000 | 0.114 | 0.281 | n/a | 1.0000 | 100.0% | -3.797 | 0.0% | 0.0% |
| `adam_adsl` | 32 | 320 | 0.0000 | 0.064 | 0.195 | n/a | 1.0000 | 100.0% | -2.988 | 0.0% | 0.0% |
| `adam_adlb` | 64 | 640 | 0.0000 | 0.034 | 0.121 | n/a | 1.0000 | 100.0% | -3.438 | 0.0% | 0.0% |
| `adam_adpc` | 128 | 1280 | 0.0000 | 0.018 | 0.067 | n/a | 1.0000 | 100.0% | -3.533 | 0.0% | 0.0% |
| `adam_adpc_extended` | 256 | 2560 | 0.0000 | 0.009 | 0.035 | n/a | 1.0000 | 100.0% | -3.393 | 0.0% | 0.0% |
| `hr_open_n256` | 256 | 2560 | 0.0000 | 0.009 | 0.035 | n/a | 1.0000 | 100.0% | -3.393 | 0.0% | 0.0% |
| `hr_open_n512` | 512 | 5120 | 0.0000 | 0.005 | 0.018 | n/a | 1.0000 | 100.0% | -2.966 | 0.0% | 0.0% |
| `eurostat_silc_n128` | 128 | 1280 | 0.0000 | 0.018 | 0.067 | n/a | 1.0000 | 100.0% | -3.533 | 0.0% | 0.0% |
| `eurostat_silc_n512` | 512 | 5120 | 0.0000 | 0.005 | 0.018 | n/a | 1.0000 | 100.0% | -2.966 | 0.0% | 0.0% |
