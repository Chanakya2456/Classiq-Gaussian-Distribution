import math
from collections import defaultdict

import numpy as np
from classiq import *
from classiq.execution import *
from classiq.qmod.symbolic import *

EXACT_THRESHOLD = 8
STAGE1_PRUNE_BOUND = 1e-6
STAGE2_PRUNE_BOUND = 5e-3


def _exact_mass_fn(resolution):
    n = 2 ** resolution
    step = 4.0 / n
    xs = -2.0 + step * np.arange(n)
    weights = np.exp(-xs ** 2)
    probs = weights / weights.sum()
    cum = np.concatenate(([0.0], np.cumsum(probs)))

    def mass(lo, hi):
        idx_lo = int(round((lo + 2.0) / step))
        idx_hi = int(round((hi + 2.0) / step))
        idx_lo = max(0, min(n, idx_lo))
        idx_hi = max(0, min(n, idx_hi))
        return float(cum[idx_hi] - cum[idx_lo])

    return mass


def _continuous_mass_fn():
    norm = math.erf(2.0) - math.erf(-2.0)

    def mass(lo, hi):
        return (math.erf(hi) - math.erf(lo)) / norm

    return mass


def create_solution(resolution: int):
    fraction_digits = resolution - 2
    EXP_RATE = 1

    if resolution <= EXACT_THRESHOLD:
        mass = _exact_mass_fn(resolution)
        prune_bound = STAGE1_PRUNE_BOUND
    else:
        mass = _continuous_mass_fn()
        prune_bound = STAGE2_PRUNE_BOUND
    total_mass = mass(-2.0, 2.0)

    @qfunc
    def prepare_gaussian(x: QNum):
        x_arr = QArray("x_arr")
        bind(x, x_arr)

        def recurse(depth, lo, hi, ctrl_qubits, ctrl_values):
            if depth == resolution:
                return

            m = mass(lo, hi)
            if m <= 0.0:
                return

            mid = (lo + hi) / 2.0
            qubit_idx = resolution - 1 - depth
            target = x_arr[qubit_idx]

            if depth == 0:
                m0, branch0, branch1 = mass(mid, hi), (mid, hi), (lo, mid)
            else:
                m0, branch0, branch1 = mass(lo, mid), (lo, mid), (mid, hi)

            p0 = max(0.0, min(1.0, m0 / m))
            theta = 2.0 * math.acos(math.sqrt(p0))

            flipped = [q for q, v in zip(ctrl_qubits, ctrl_values) if v == 0]
            for q in flipped:
                X(q)

            if ctrl_qubits:
                control(ctrl_qubits, lambda: RY(theta, target))
            else:
                RY(theta, target)

            for q in flipped:
                X(q)

            for value, (b_lo, b_hi) in ((0, branch0), (1, branch1)):
                branch_mass = mass(b_lo, b_hi)
                if branch_mass / total_mass < prune_bound:
                    continue
                recurse(depth + 1, b_lo, b_hi, ctrl_qubits + [target], ctrl_values + [value])

        recurse(0, -2.0, 2.0, [], [])
        bind(x_arr, x)

    return prepare_gaussian


def create_qprog(prepare_gaussian_function, resolution: int, num_shots: int = 1, optimization_parameter: str = "CX", stage: int = 1):
    fraction_digits = resolution - 2

    @qfunc
    def main(x: Output[QNum[resolution, SIGNED, fraction_digits]]):
        allocate(x.size, x)
        prepare_gaussian_function(x)

    backend_preferences = ClassiqBackendPreferences(
        backend_name=ClassiqSimulatorBackendNames.SIMULATOR_STATEVECTOR
    )

    if stage == 1:
        qmod = create_model(
            main,
            execution_preferences=ExecutionPreferences(
                num_shots=num_shots, backend_preferences=backend_preferences
            ),
            constraints=Constraints(
                max_width=18, optimization_parameter=optimization_parameter
            ),
        )
    elif stage == 2:
        qmod = create_model(
            main,
            preferences=Preferences(timeout_seconds=1000),
            execution_preferences=ExecutionPreferences(
                num_shots=num_shots, backend_preferences=backend_preferences
            ),
            constraints=Constraints(
                max_width=127, optimization_parameter=optimization_parameter
            ),
        )
    else:
        raise ValueError("The `stage` variable should be set to either 1 or 2")

    return synthesize(qmod)


def scatter_aggregated_amplitudes_with_theory(parsed_state_vector, resolution: int, should_plot: bool = True):
    fraction_digits = resolution - 2
    exp_rate = 1

    amplitude_sums = defaultdict(int)
    for state in parsed_state_vector:
        amplitude_sums[state.state['x']] += np.abs(state.amplitude) ** 2

    x_values = sorted(amplitude_sums)
    summed_squared_norms = [amplitude_sums[x] for x in x_values]

    grid = np.linspace(-2 ** (resolution - fraction_digits - 1), 2 ** (resolution - fraction_digits - 1) - 2 ** (-fraction_digits), 2 ** resolution)
    theoretical_gaussian = np.exp(-exp_rate * grid ** 2)
    theoretical_gaussian /= np.sum(theoretical_gaussian)

    interp_func = np.interp(x_values, grid, theoretical_gaussian)
    mse = np.mean((np.array(summed_squared_norms) - interp_func) ** 2)
    print("Mean Squared Error (MSE):", mse)

    if should_plot:
        plt.figure(figsize=(8, 6))
        plt.scatter(x_values, summed_squared_norms, color='blue', alpha=0.7, label='Measured (Summed Squared Norms)')
        plt.plot(grid, theoretical_gaussian, color='red', linewidth=2, label='Theoretical Gaussian')
        plt.xlabel('x')
        plt.ylabel('Probability')
        plt.title('Measured vs Theoretical Gaussian')
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.legend()
        plt.tight_layout()
        plt.show()

    return mse


def get_metrics(qprog):
    circuit = QuantumProgram.from_qprog(qprog)
    metrics = {
        "depth": circuit.transpiled_circuit.depth,
        "width": circuit.data.width,
        "cx_count": circuit.transpiled_circuit.count_ops.get('cx', 0),
    }
    return metrics
