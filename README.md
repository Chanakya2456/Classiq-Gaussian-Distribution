# Gaussian State Preparation on Classiq

A compact, repo-ready implementation of a Gaussian state-preparation pipeline designed for the iQuHack 2025 Classiq challenge track.

This project builds a quantum routine that prepares a Gaussian-shaped amplitude distribution over the domain $x \in [-2, 2)$ directly into a qubit register using a recursive, controlled-rotation construction. The implementation supports two operating modes:

- Stage 1: exact discrete Gaussian preparation for small resolutions.
- Stage 2: scalable pruned preparation for larger resolutions using a continuous Gaussian mass model.

The goal is to prepare a valid quantum state that matches the target Gaussian distribution while keeping the circuit tractable as resolution increases.

---

## Overview

State preparation is a foundational subroutine in quantum algorithms. In many applications, we need to initialize a register in a distribution that approximates a desired continuous or discrete probability law. Here, the target distribution is Gaussian:

$$
G(x) = \frac{\exp(-x^2)}{\sum_{x'} \exp(-(x')^2)}
$$

over the interval $[-2, 2)$.

Instead of invoking a black-box state-preparation routine with a fixed generic method, this project implements a custom recursive binary-tree construction that proceeds qubit by qubit. At each step, the algorithm decides how much amplitude should go into the left and right half of the current interval, and it encodes that decision with a controlled `RY` rotation.

This yields a Grover–Rudolph-style state-preparation circuit, but adapted to the actual register and interval structure of the challenge.

---

## Why this approach

The main challenge is not just matching the Gaussian shape; it is doing so without exploding circuit size as the number of qubits grows.

Two regimes are handled explicitly:

1. Small resolutions
   - We can materialize the exact discrete Gaussian probabilities.
   - This preserves exact behavior and gives an accurate target on the specified domain.

2. Larger resolutions
   - We cannot build a full $2^{\text{resolution}}$ probability table.
   - We switch to a continuous Gaussian mass model based on the Gaussian CDF via `erf`.
   - We prune branches whose probability mass is negligible, which keeps the circuit compact.

This is the key to scaling beyond the small simulator regime while keeping the state preparation faithful to the target distribution.

---

## Project structure

```text
.
├── .github/
│   └── workflows/
│       └── ci.yml
├── scripts/
│   └── run_stage_examples.py
├── src/
│   └── classiq_gaussian_state_preparation/
│       ├── __init__.py
│       └── core.py
├── tests/
│   └── test_core.py
├── .gitignore
├── pyproject.toml
├── README.md
└── LICENSE
```

### Main package

- `src/classiq_gaussian_state_preparation/core.py`
  - contains the Gaussian mass logic
  - defines the recursive `prepare_gaussian` routine
  - synthesizes the Classiq program through `create_qprog`

### Example runner

- `scripts/run_stage_examples.py`
  - CLI interface to generate a qprog for Stage 1 or Stage 2

### Validation

- `tests/test_core.py`
  - basic import/structure check to ensure the package loads correctly

---

## Requirements

This project depends on:

- Python 3.10+
- Classiq SDK
- NumPy
- Matplotlib

The package metadata in `pyproject.toml` installs those dependencies automatically.

---

## Installation

Clone the repo:

```bash
git clone <your-repo-url>
cd <repo-folder>
```

Create and activate a virtual environment:

### macOS / Linux

```bash
python -m venv .venv
source .venv/bin/activate
```

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install the project in editable mode:

```bash
python -m pip install --upgrade pip
pip install -e .
```

Optional development dependencies:

```bash
pip install -e .[dev]
```

---

## Quick start

### Python usage

```python
from classiq_gaussian_state_preparation import create_solution, create_qprog

resolution = 8
qprog = create_qprog(create_solution(resolution), resolution, stage=1)
print(qprog)
```

This creates a synthesized Classiq program for the exact Gaussian preparation path.

### Script usage

```bash
python scripts/run_stage_examples.py --stage 1 --resolution 8
```

or

```bash
python scripts/run_stage_examples.py --stage 2 --resolution 64
```

---

## Stage breakdown

### Stage 1 — Exact validation

Stage 1 targets a compact resolution where the full discrete distribution can be built exactly.

- Compute the Gaussian probability mass exactly at each grid point.
- Build the recursive state-preparation circuit using the exact mass values.
- Validate the resulting distribution against the theoretical target.

This is the “gold-standard” stage and is useful for confirming the modeling is correct.

### Stage 2 — Scalable preparation

Stage 2 is designed for larger qubit counts where a naive exact discretization is not practical.

- Use the Gaussian CDF based on `erf`.
- Approximate mass intervals without generating a full probability table.
- Prune low-mass branches to keep circuit growth bounded.

This stage demonstrates that the approach remains compact even when resolution is pushed much higher.

---

## Core implementation notes

The essential quantum idea is:

- walk the register qubit-by-qubit,
- define an interval of the current domain,
- compute the probability mass in the left/right subinterval,
- apply a controlled `RY` rotation to encode that split,
- recurse into the relevant subinterval(s).

This is essentially a recursive, pruned Grover–Rudolph-style strategy, but tailored to a Gaussian target distribution and to the Classiq `QNum` workflow.

At each recursion step, the angle is chosen according to the fraction of mass that lies on one side of the current midpoint. In other words, if the current interval contains mass $m$, and the lower half carries mass $m_0$, then the rotation is set so that the amplitude ratio tracks the correct conditional probability.

This gives a state that encodes the Gaussian distribution directly in the computational basis amplitudes.

---

## Validation workflow

The repository is structured around the core challenge workflow:

1. Build the Gaussian state-preparation function.
2. Synthesize the corresponding quantum program with Classiq.
3. Run Stage 1 validation for exact discrete behavior.
4. Run Stage 2 checks for larger-resolution scaling.
5. Export the generated `.qprog` artifacts for challenge submission.

The exact empirical validation logic includes comparing generated amplitudes against the target Gaussian and reporting circuit metrics such as width, depth, and CX count.

---

## Running tests

```bash
pytest -q
```

This project includes a small smoke test to confirm the package loads correctly and that the state-preparation builder can be created.

---

## CI

This repository includes a GitHub Actions workflow in `.github/workflows/ci.yml` that installs the package and runs the test suite automatically on push and pull request.

---

## Tips for challenge submission

When using this repository as part of a challenge submission:

- Keep the core algorithm in the package module and keep the scripts lean.
- Use Stage 1 for exact correctness checks.
- Use Stage 2 for scaling demonstrations.
- Export the final qprogs with your team name and resolution labels.
- Keep the README clear enough that a reviewer can understand the method without opening the notebook.

---

## License

This project is intended for challenge work and repository-ready experimentation. Replace or extend the license as needed for your team or institutional requirements.

---

## Notes

This repository is designed to be a clean transition from the prototype notebook into a proper GitHub project. The core logic is packaged so it can be imported, tested, and reused without depending on the notebook execution environment.
