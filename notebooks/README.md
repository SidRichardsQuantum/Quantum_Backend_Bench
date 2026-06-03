# Tutorial Notebooks

These notebooks are succinct package-client examples. They use the public package
API to run local, credential-free quantum simulator benchmarks and print readable
verification tables.

## Notebooks

- `01_quickstart_cirq.ipynb`: run GHZ and a tiny smoke suite on Cirq.
- `02_compare_local_simulators.ipynb`: compare installed local simulator SDKs on
  GHZ and QFT.
- `03_hamiltonian_simulation_case_study.ipynb`: vary qubits, evolution time,
  and Trotter steps for a small Ising-style Hamiltonian simulation study.

## Suggested Install

```bash
python -m pip install -e ".[cirq,plot,notebooks]"
```

For the broader local comparison notebook, install the optional SDK extras you want
to compare, for example:

```bash
python -m pip install -e ".[all,notebooks]"
```
