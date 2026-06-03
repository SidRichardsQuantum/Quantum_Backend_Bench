# Cirq Smoke Reference Results

Generated on 2026-06-03 in a Linux Codespaces-style environment with Python 3.11.

These files are small reference artifacts for the fastest public onboarding path:
install the package with the Cirq extra, run one GHZ benchmark, then run the smoke
suite. They are examples of the JSON and CSV schema, not stable performance
claims.

## Commands

```bash
python -m pip install "quantum-backend-bench[cirq]"
quantum-bench run ghz \
  --backend cirq \
  --n-qubits 3 \
  --shots 128 \
  --summary \
  --save-json examples/reference_results/cirq_smoke_2026-06-03/ghz_cirq.json \
  --save-csv examples/reference_results/cirq_smoke_2026-06-03/ghz_cirq.csv
quantum-bench suite smoke \
  --backends cirq \
  --shots 128 \
  --summary \
  --save-json examples/reference_results/cirq_smoke_2026-06-03/smoke_suite_cirq.json \
  --save-csv examples/reference_results/cirq_smoke_2026-06-03/smoke_suite_cirq.csv
```

## Files

- `ghz_cirq.json` and `ghz_cirq.csv`: one GHZ benchmark on Cirq.
- `smoke_suite_cirq.json` and `smoke_suite_cirq.csv`: GHZ, Bernstein-Vazirani,
  and Grover smoke cases on Cirq.

## Interpretation

Runtime values depend on the local machine, installed SDK versions, Python version,
and current system load. Use these files to inspect result shape and metadata. For
fresh comparisons, regenerate the bundle in the target environment.
