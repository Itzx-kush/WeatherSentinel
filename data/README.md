# Data directories

- `examples`: small, explicitly labelled reproducible inputs committed with the project
- `raw`: local source data; ignored except `.gitkeep`
- `processed`: generated feature JSONL; ignored except `.gitkeep`
- `synthetic`: future generated clean data with seed metadata
- `fault_injection`: future injected copies and immutable ground truth

`aws_synthetic_normal.csv` is a controlled synthetic normal-weather sequence. It is not an IMD measurement and contains no asserted sensor fault.
