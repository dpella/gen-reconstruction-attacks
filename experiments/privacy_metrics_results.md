# Privacy-metric results on the decoy-augmented datasets

Every row: 10 % reconstructable core + 90 % decoys. All metrics rate the releases as low-risk even though `M·s = b` recovers every core record exactly.

| Schema | n core | n total | Anonymeter risk | attack | control | synthcity XGB | synthcity Ident. | Privacy Meter MRE | R² | ±5 % succ. |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `sdtm_vs` | 16 | 160 | 0.0000 | 0.903 | 0.903 | 0.0000 | 1.0000 | 446.9% | 0.817 | 12.5% |
| `adam_adsl` | 32 | 320 | 0.0000 | 0.946 | 0.946 | 0.0000 | 1.0000 | 76.6% | 0.828 | 15.6% |
| `adam_adlb` | 64 | 640 | 0.0000 | 0.972 | 0.972 | 0.0154 | 1.0000 | 44.9% | 0.826 | 17.2% |
| `adam_adpc` | 128 | 1280 | 0.0000 | 0.985 | 0.985 | 0.1550 | 1.0000 | 118.8% | 0.854 | 13.3% |
| `adam_adpc_extended` | 256 | 2560 | 0.0000 | 0.993 | 0.993 | 0.0584 | 1.0000 | 51.5% | 0.843 | 13.7% |
| `hr_open_n256` | 256 | 2560 | 0.0000 | 0.993 | 0.993 | 0.0000 | 1.0000 | 53.2% | 0.839 | 13.3% |
| `hr_open_n512` | 512 | 5120 | 0.0000 | 0.996 | 0.996 | 0.0000 | 1.0000 | 100.5% | 0.825 | 12.7% |
| `eurostat_silc_n128` | 128 | 1280 | 0.0000 | 0.985 | 0.985 | 0.0000 | 1.0000 | 125.9% | 0.840 | 10.2% |
| `eurostat_silc_n512` | 512 | 5120 | 0.0000 | 0.996 | 0.996 | 0.0000 | 1.0000 | 104.2% | 0.821 | 10.9% |
