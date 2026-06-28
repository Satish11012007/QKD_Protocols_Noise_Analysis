import json
from pathlib import Path


PROJECT = Path("BB84_QKD_Project")


COMMON_IMPORTS = """# Common imports used in this notebook
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, pauli_error, depolarizing_error, amplitude_damping_error

np.random.seed(42)
plt.style.use("seaborn-v0_8-whitegrid")
"""


HELPERS = """# BB84 helper functions
def random_bits(n):
    \"\"\"Generate n random classical bits.\"\"\"
    return np.random.randint(0, 2, size=n)


def random_bases(n):
    \"\"\"Generate n random bases: 0 means Z basis, 1 means X basis.\"\"\"
    return np.random.randint(0, 2, size=n)


def prepare_bb84_qubit(bit, basis):
    \"\"\"Create one BB84 qubit circuit.

    bit=0/1 is the secret bit.
    basis=0 prepares in Z basis; basis=1 prepares in X basis.
    \"\"\"
    qc = QuantumCircuit(1, 1)
    if bit == 1:
        qc.x(0)
    if basis == 1:
        qc.h(0)
    return qc


def measure_bb84_qubit(qc, basis):
    \"\"\"Measure the qubit in Bob's selected basis.\"\"\"
    if basis == 1:
        qc.h(0)
    qc.measure(0, 0)
    return qc


def run_single_shot(qc, simulator=None, noise_model=None):
    \"\"\"Run one circuit once and return measured bit as an integer.\"\"\"
    simulator = simulator or AerSimulator(noise_model=noise_model)
    compiled = transpile(qc, simulator)
    result = simulator.run(compiled, shots=1).result()
    counts = result.get_counts()
    return int(max(counts, key=counts.get))


def sift_key(alice_bits, alice_bases, bob_bases, bob_bits):
    \"\"\"Keep only positions where Alice and Bob used the same basis.\"\"\"
    mask = alice_bases == bob_bases
    return alice_bits[mask], bob_bits[mask], mask


def qber(alice_key, bob_key):
    \"\"\"Quantum Bit Error Rate: fraction of mismatched sifted bits.\"\"\"
    if len(alice_key) == 0:
        return 0.0
    return float(np.mean(alice_key != bob_key))


def simulate_bb84(n=256, noise_model=None, eve=False):
    \"\"\"Simulate BB84 with optional noise and optional intercept-resend Eve attack.\"\"\"
    alice_bits = random_bits(n)
    alice_bases = random_bases(n)
    bob_bases = random_bases(n)
    bob_bits = []
    simulator = AerSimulator(noise_model=noise_model)

    for bit, alice_basis, bob_basis in zip(alice_bits, alice_bases, bob_bases):
        qc = prepare_bb84_qubit(int(bit), int(alice_basis))

        if eve:
            # Eve randomly measures and resends the qubit, which disturbs states
            # whenever she chooses the wrong basis.
            eve_basis = int(random_bases(1)[0])
            qc = measure_bb84_qubit(qc, eve_basis)
            eve_bit = run_single_shot(qc, simulator=simulator)
            qc = prepare_bb84_qubit(eve_bit, eve_basis)

        qc = measure_bb84_qubit(qc, int(bob_basis))
        bob_bits.append(run_single_shot(qc, simulator=simulator))

    bob_bits = np.array(bob_bits)
    alice_key, bob_key, mask = sift_key(alice_bits, alice_bases, bob_bases, bob_bits)
    return {
        "alice_bits": alice_bits,
        "alice_bases": alice_bases,
        "bob_bases": bob_bases,
        "bob_bits": bob_bits,
        "alice_key": alice_key,
        "bob_key": bob_key,
        "sift_mask": mask,
        "sifted_key_length": int(mask.sum()),
        "qber": qber(alice_key, bob_key),
    }
"""


def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": text.strip().splitlines(True)}


def code(text):
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": text.strip().splitlines(True),
    }


def notebook(title, theory, extra_code, conclusion):
    cells = [
        md(f"# {title}\n\n## Theory\n{theory}"),
        code(COMMON_IMPORTS),
        code(HELPERS),
        code(extra_code),
        md(f"## Conclusion\n{conclusion}"),
    ]
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "pygments_lexer": "ipython3"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


NOTEBOOKS = [
    (
        "01_BB84_Noise_Free.ipynb",
        "01 BB84 Noise Free",
        "BB84 is a quantum key distribution protocol where Alice sends random bits encoded in random bases. Bob measures in random bases. After transmission, they publicly compare bases and keep only matching positions. In an ideal noise-free channel, the sifted keys should match exactly and QBER should be close to 0.",
        """# Run a clean BB84 simulation
result = simulate_bb84(n=512)

# Build a compact result table
summary = pd.DataFrame({
    "Metric": ["Total qubits", "Sifted key length", "QBER", "First 20 Alice key bits", "First 20 Bob key bits"],
    "Value": [512, result["sifted_key_length"], result["qber"], result["alice_key"][:20].tolist(), result["bob_key"][:20].tolist()],
})
display(summary)

# Plot Alice and Bob sifted keys for the first positions
m = min(40, len(result["alice_key"]))
plt.figure(figsize=(10, 3))
plt.step(range(m), result["alice_key"][:m], where="mid", label="Alice sifted key")
plt.step(range(m), result["bob_key"][:m], where="mid", linestyle="--", label="Bob sifted key")
plt.yticks([0, 1])
plt.xlabel("Sifted bit index")
plt.ylabel("Bit value")
plt.title("Noise-free BB84 sifted key comparison")
plt.legend()
plt.show()
""",
        "In the ideal channel, Alice and Bob keep only matching-basis measurements. The resulting sifted keys should be identical, giving QBER near 0 and demonstrating the basic BB84 workflow.",
    ),
    (
        "02_BitFlip_Noise.ipynb",
        "02 BitFlip Noise",
        "Bit-flip noise applies an X error with probability p. It changes |0> to |1> and |1> to |0>, directly causing bit mismatches when Alice and Bob use the same basis.",
        """# Create a bit-flip noise model
def bit_flip_noise_model(p):
    noise = NoiseModel()
    error = pauli_error([("X", p), ("I", 1 - p)])
    noise.add_all_qubit_quantum_error(error, ["x", "h", "measure"])
    return noise

probabilities = np.linspace(0, 0.25, 6)
rows = []
for p in probabilities:
    result = simulate_bb84(n=512, noise_model=bit_flip_noise_model(float(p)))
    rows.append({"Bit flip probability": p, "Sifted key length": result["sifted_key_length"], "QBER": result["qber"]})

table = pd.DataFrame(rows)
display(table)

plt.figure(figsize=(7, 4))
plt.plot(table["Bit flip probability"], table["QBER"], marker="o")
plt.xlabel("Bit-flip probability")
plt.ylabel("QBER")
plt.title("QBER under bit-flip noise")
plt.show()
""",
        "As bit-flip probability increases, the mismatch rate generally increases. This shows how classical-looking bit errors weaken the shared key.",
    ),
    (
        "03_PhaseFlip_Noise.ipynb",
        "03 PhaseFlip Noise",
        "Phase-flip noise applies a Z error with probability p. In the Z basis it does not change measured bit values, but in the X basis it can flip measurement outcomes, so BB84 still detects it through QBER.",
        """# Create a phase-flip noise model
def phase_flip_noise_model(p):
    noise = NoiseModel()
    error = pauli_error([("Z", p), ("I", 1 - p)])
    noise.add_all_qubit_quantum_error(error, ["x", "h", "measure"])
    return noise

probabilities = np.linspace(0, 0.30, 7)
rows = []
for p in probabilities:
    result = simulate_bb84(n=512, noise_model=phase_flip_noise_model(float(p)))
    rows.append({"Phase flip probability": p, "Sifted key length": result["sifted_key_length"], "QBER": result["qber"]})

table = pd.DataFrame(rows)
display(table)

plt.figure(figsize=(7, 4))
plt.plot(table["Phase flip probability"], table["QBER"], marker="o", color="purple")
plt.xlabel("Phase-flip probability")
plt.ylabel("QBER")
plt.title("QBER under phase-flip noise")
plt.show()
""",
        "Phase errors are not always visible in the computational basis, but BB84 uses two bases, so phase noise becomes measurable as key disagreement.",
    ),
    (
        "04_Depolarizing_Noise.ipynb",
        "04 Depolarizing Noise",
        "Depolarizing noise replaces the qubit state with a randomly disturbed state with probability p. It represents a broad channel error model combining X, Y, and Z effects.",
        """# Create a depolarizing noise model
def depolarizing_noise_model(p):
    noise = NoiseModel()
    error = depolarizing_error(p, 1)
    noise.add_all_qubit_quantum_error(error, ["x", "h", "measure"])
    return noise

probabilities = np.linspace(0, 0.40, 9)
rows = []
for p in probabilities:
    result = simulate_bb84(n=512, noise_model=depolarizing_noise_model(float(p)))
    rows.append({"Depolarizing probability": p, "Sifted key length": result["sifted_key_length"], "QBER": result["qber"]})

table = pd.DataFrame(rows)
display(table)

plt.figure(figsize=(7, 4))
plt.plot(table["Depolarizing probability"], table["QBER"], marker="o", color="crimson")
plt.xlabel("Depolarizing probability")
plt.ylabel("QBER")
plt.title("QBER under depolarizing noise")
plt.show()
""",
        "Depolarizing noise produces stronger, more general disturbance than a single Pauli error. Increasing noise raises QBER and reduces confidence in the final key.",
    ),
    (
        "05_Amplitude_Damping.ipynb",
        "05 Amplitude Damping",
        "Amplitude damping models energy loss, such as decay from |1> to |0>. In optical or hardware-inspired channels, this is useful for studying loss-like physical noise.",
        """# Create an amplitude damping noise model
def amplitude_damping_noise_model(gamma):
    noise = NoiseModel()
    error = amplitude_damping_error(gamma)
    noise.add_all_qubit_quantum_error(error, ["x", "h", "measure"])
    return noise

gammas = np.linspace(0, 0.40, 9)
rows = []
for gamma in gammas:
    result = simulate_bb84(n=512, noise_model=amplitude_damping_noise_model(float(gamma)))
    rows.append({"Damping gamma": gamma, "Sifted key length": result["sifted_key_length"], "QBER": result["qber"]})

table = pd.DataFrame(rows)
display(table)

plt.figure(figsize=(7, 4))
plt.plot(table["Damping gamma"], table["QBER"], marker="o", color="darkgreen")
plt.xlabel("Amplitude damping gamma")
plt.ylabel("QBER")
plt.title("QBER under amplitude damping")
plt.show()
""",
        "Amplitude damping biases outcomes toward 0 and introduces detectable mismatches. Higher damping makes the BB84 key less reliable.",
    ),
    (
        "06_QBER_vs_Noise.ipynb",
        "06 QBER vs Noise",
        "QBER is the fraction of mismatched bits in the sifted key. Comparing QBER across noise models helps identify which channel behavior damages BB84 most severely.",
        """# Compare QBER across several noise models
levels = np.linspace(0, 0.30, 7)
models = {
    "Bit flip": lambda p: bit_flip_noise_model(p),
    "Phase flip": lambda p: phase_flip_noise_model(p),
    "Depolarizing": lambda p: depolarizing_noise_model(p),
    "Amplitude damping": lambda p: amplitude_damping_noise_model(p),
}

def bit_flip_noise_model(p):
    noise = NoiseModel()
    noise.add_all_qubit_quantum_error(pauli_error([("X", p), ("I", 1 - p)]), ["x", "h", "measure"])
    return noise

def phase_flip_noise_model(p):
    noise = NoiseModel()
    noise.add_all_qubit_quantum_error(pauli_error([("Z", p), ("I", 1 - p)]), ["x", "h", "measure"])
    return noise

def depolarizing_noise_model(p):
    noise = NoiseModel()
    noise.add_all_qubit_quantum_error(depolarizing_error(p, 1), ["x", "h", "measure"])
    return noise

def amplitude_damping_noise_model(p):
    noise = NoiseModel()
    noise.add_all_qubit_quantum_error(amplitude_damping_error(p), ["x", "h", "measure"])
    return noise

rows = []
for name, builder in models.items():
    for level in levels:
        result = simulate_bb84(n=512, noise_model=builder(float(level)))
        rows.append({"Noise model": name, "Noise level": level, "QBER": result["qber"]})

table = pd.DataFrame(rows)
display(table.pivot(index="Noise level", columns="Noise model", values="QBER"))

plt.figure(figsize=(8, 5))
for name in models:
    subset = table[table["Noise model"] == name]
    plt.plot(subset["Noise level"], subset["QBER"], marker="o", label=name)
plt.xlabel("Noise level")
plt.ylabel("QBER")
plt.title("QBER comparison across noise models")
plt.legend()
plt.show()
""",
        "The comparison makes QBER the central security diagnostic. When QBER becomes too high, the key must be rejected or heavily corrected and compressed.",
    ),
    (
        "07_Key_Agreement_Rate.ipynb",
        "07 Key Agreement Rate",
        "Key agreement rate measures how much of the transmitted quantum data becomes matching sifted key material. In BB84, about half the bits survive basis reconciliation before errors are considered.",
        """# Estimate key agreement rate under changing noise
levels = np.linspace(0, 0.30, 7)
rows = []
for level in levels:
    noise = depolarizing_noise_model(float(level))
    result = simulate_bb84(n=1024, noise_model=noise)
    agreement = np.mean(result["alice_key"] == result["bob_key"]) if result["sifted_key_length"] else 0
    rate = result["sifted_key_length"] * agreement / 1024
    rows.append({"Noise level": level, "Sifted fraction": result["sifted_key_length"] / 1024, "Agreement rate": rate, "QBER": result["qber"]})

table = pd.DataFrame(rows)
display(table)

plt.figure(figsize=(8, 4))
plt.plot(table["Noise level"], table["Agreement rate"], marker="o", label="Agreement rate")
plt.plot(table["Noise level"], table["Sifted fraction"], marker="s", label="Sifted fraction")
plt.xlabel("Depolarizing noise level")
plt.ylabel("Rate")
plt.title("Key agreement rate")
plt.legend()
plt.show()
""",
        "Basis reconciliation keeps roughly half the transmissions. Noise reduces the fraction of those sifted bits that Alice and Bob can actually agree on.",
    ),
    (
        "08_Efficiency_Rate.ipynb",
        "08 Efficiency Rate",
        "Efficiency rate compares useful final key bits with total transmitted qubits. It includes sifting loss and an estimated penalty for error correction/privacy amplification.",
        """# Estimate protocol efficiency after simple security penalty
levels = np.linspace(0, 0.30, 7)
rows = []
for level in levels:
    noise = depolarizing_noise_model(float(level))
    result = simulate_bb84(n=1024, noise_model=noise)
    # A simple teaching estimate: final fraction falls as QBER rises.
    security_penalty = max(0, 1 - 2 * result["qber"])
    efficiency = (result["sifted_key_length"] / 1024) * security_penalty
    rows.append({"Noise level": level, "QBER": result["qber"], "Security penalty": security_penalty, "Estimated efficiency": efficiency})

table = pd.DataFrame(rows)
display(table)

plt.figure(figsize=(8, 4))
plt.bar(table["Noise level"].round(2).astype(str), table["Estimated efficiency"], color="steelblue")
plt.xlabel("Depolarizing noise level")
plt.ylabel("Estimated final-key efficiency")
plt.title("BB84 efficiency estimate")
plt.show()
""",
        "Efficiency is highest when the channel is clean. As QBER rises, more bits must be discarded or compressed, reducing final usable key output.",
    ),
    (
        "09_Eve_Attack.ipynb",
        "09 Eve Attack",
        "An intercept-resend attack occurs when Eve measures each qubit in a random basis and sends a replacement. When Eve chooses the wrong basis, she disturbs the state and introduces detectable errors.",
        """# Compare BB84 with and without Eve
clean = simulate_bb84(n=1024, eve=False)
attacked = simulate_bb84(n=1024, eve=True)

table = pd.DataFrame([
    {"Scenario": "No Eve", "Sifted key length": clean["sifted_key_length"], "QBER": clean["qber"]},
    {"Scenario": "Intercept-resend Eve", "Sifted key length": attacked["sifted_key_length"], "QBER": attacked["qber"]},
])
display(table)

plt.figure(figsize=(6, 4))
plt.bar(table["Scenario"], table["QBER"], color=["seagreen", "firebrick"])
plt.ylabel("QBER")
plt.title("Eve attack detection using QBER")
plt.show()
""",
        "The intercept-resend attack increases QBER significantly. BB84 detects eavesdropping statistically by publicly comparing a sample of key bits.",
    ),
    (
        "10_Eve_with_Noise.ipynb",
        "10 Eve with Noise",
        "Real channels may contain both natural noise and an eavesdropper. Security analysis must distinguish expected channel errors from suspicious excess QBER.",
        """# Simulate Eve plus depolarizing channel noise
levels = np.linspace(0, 0.20, 5)
rows = []
for level in levels:
    noise = depolarizing_noise_model(float(level))
    result = simulate_bb84(n=1024, noise_model=noise, eve=True)
    rows.append({"Noise level": level, "Eve": True, "Sifted key length": result["sifted_key_length"], "QBER": result["qber"]})

table = pd.DataFrame(rows)
display(table)

plt.figure(figsize=(7, 4))
plt.plot(table["Noise level"], table["QBER"], marker="o", color="firebrick")
plt.axhline(0.11, color="black", linestyle="--", label="Example abort threshold")
plt.xlabel("Depolarizing noise level")
plt.ylabel("QBER")
plt.title("Eve attack with channel noise")
plt.legend()
plt.show()
""",
        "When Eve and noise are both present, QBER can quickly exceed an acceptable threshold. In practice, Alice and Bob abort if observed QBER is too high.",
    ),
    (
        "11_Information_Reconciliation.ipynb",
        "11 Information Reconciliation",
        "Information reconciliation is the classical post-processing step where Alice and Bob correct mismatches in their sifted keys. This notebook uses a simplified block parity example for learning.",
        """# Simple block-parity reconciliation demonstration
result = simulate_bb84(n=256, noise_model=bit_flip_noise_model(0.05))
alice_key = result["alice_key"].copy()
bob_key = result["bob_key"].copy()

block_size = 8
corrections = 0
for start in range(0, len(alice_key), block_size):
    end = min(start + block_size, len(alice_key))
    alice_parity = int(alice_key[start:end].sum() % 2)
    bob_parity = int(bob_key[start:end].sum() % 2)
    if alice_parity != bob_parity:
        # Teaching simplification: locate the first mismatch using revealed comparison.
        mismatches = np.where(alice_key[start:end] != bob_key[start:end])[0]
        if len(mismatches) > 0:
            bob_key[start + mismatches[0]] = alice_key[start + mismatches[0]]
            corrections += 1

before_qber = result["qber"]
after_qber = qber(alice_key, bob_key)
table = pd.DataFrame({
    "Metric": ["QBER before reconciliation", "QBER after reconciliation", "Corrections applied", "Sifted key length"],
    "Value": [before_qber, after_qber, corrections, len(alice_key)],
})
display(table)

plt.figure(figsize=(5, 4))
plt.bar(["Before", "After"], [before_qber, after_qber], color=["tomato", "seagreen"])
plt.ylabel("QBER")
plt.title("Effect of simplified reconciliation")
plt.show()
""",
        "Reconciliation reduces mismatches but leaks some information through public discussion. Real protocols account for this leakage during privacy amplification.",
    ),
    (
        "12_Privacy_Amplification.ipynb",
        "12 Privacy Amplification",
        "Privacy amplification compresses the reconciled key to reduce Eve's possible information. Universal hashing is commonly used; this notebook demonstrates a simple random binary hash matrix.",
        """# Simple privacy amplification using a random binary hash matrix
result = simulate_bb84(n=512, noise_model=bit_flip_noise_model(0.02))
alice_key = result["alice_key"]

qber_estimate = result["qber"]
final_length = max(1, int(len(alice_key) * max(0.1, 1 - 3 * qber_estimate) * 0.5))

# Random binary matrix maps the sifted key to a shorter final key.
hash_matrix = np.random.randint(0, 2, size=(final_length, len(alice_key)))
final_key = (hash_matrix @ alice_key) % 2

table = pd.DataFrame({
    "Metric": ["Sifted key length", "Estimated QBER", "Final key length", "First 32 final bits"],
    "Value": [len(alice_key), qber_estimate, final_length, final_key[:32].tolist()],
})
display(table)

plt.figure(figsize=(6, 4))
plt.bar(["Sifted", "After privacy amplification"], [len(alice_key), final_length], color=["slategray", "royalblue"])
plt.ylabel("Number of bits")
plt.title("Key compression during privacy amplification")
plt.show()
""",
        "Privacy amplification intentionally shortens the key. The shorter final key is safer because any partial information available to Eve is strongly reduced.",
    ),
    (
        "13_IBM_Quantum_Hardware.ipynb",
        "13 IBM Quantum Hardware",
        "BB84 circuits can be executed on simulators or IBM Quantum backends. Hardware execution requires an IBM Quantum account and current backend access, so this notebook provides a simulator run plus optional runtime setup comments.",
        """# Build and run a small BB84 circuit batch on AerSimulator.
# To run on IBM hardware, install qiskit-ibm-runtime, save your token, and replace
# AerSimulator with a selected IBM backend from QiskitRuntimeService.
n = 16
alice_bits = random_bits(n)
alice_bases = random_bases(n)
bob_bases = random_bases(n)
circuits = []

for bit, alice_basis, bob_basis in zip(alice_bits, alice_bases, bob_bases):
    qc = prepare_bb84_qubit(int(bit), int(alice_basis))
    qc = measure_bb84_qubit(qc, int(bob_basis))
    circuits.append(qc)

simulator = AerSimulator()
compiled = transpile(circuits, simulator)
job = simulator.run(compiled, shots=1)
counts = job.result().get_counts()
bob_bits = np.array([int(max(c, key=c.get)) for c in counts])
alice_key, bob_key, mask = sift_key(alice_bits, alice_bases, bob_bases, bob_bits)

table = pd.DataFrame({
    "Metric": ["Backend used", "Total circuits", "Sifted key length", "QBER"],
    "Value": ["AerSimulator", n, int(mask.sum()), qber(alice_key, bob_key)],
})
display(table)

print("Optional hardware setup:")
print("from qiskit_ibm_runtime import QiskitRuntimeService")
print("service = QiskitRuntimeService(channel='ibm_quantum', token='YOUR_TOKEN')")
print("backend = service.least_busy(operational=True, simulator=False)")
""",
        "The notebook is ready for simulator execution and shows where IBM Quantum hardware access can be added. Hardware results may show real device noise and queue delays.",
    ),
    (
        "14_Final_Comparison.ipynb",
        "14 Final Comparison",
        "This final notebook compares clean BB84, noise models, Eve attack, and Eve plus noise in one table. It summarizes how QBER and efficiency change across scenarios.",
        """# Final scenario comparison
scenarios = [
    ("Clean BB84", None, False),
    ("Bit flip p=0.10", bit_flip_noise_model(0.10), False),
    ("Phase flip p=0.10", phase_flip_noise_model(0.10), False),
    ("Depolarizing p=0.10", depolarizing_noise_model(0.10), False),
    ("Amplitude damping gamma=0.10", amplitude_damping_noise_model(0.10), False),
    ("Eve intercept-resend", None, True),
    ("Eve + depolarizing p=0.10", depolarizing_noise_model(0.10), True),
]

rows = []
for name, noise, eve in scenarios:
    result = simulate_bb84(n=1024, noise_model=noise, eve=eve)
    estimated_efficiency = (result["sifted_key_length"] / 1024) * max(0, 1 - 2 * result["qber"])
    rows.append({
        "Scenario": name,
        "Sifted key length": result["sifted_key_length"],
        "QBER": result["qber"],
        "Estimated efficiency": estimated_efficiency,
        "Decision": "Accept" if result["qber"] < 0.11 else "Reject / investigate",
    })

table = pd.DataFrame(rows)
display(table)

plt.figure(figsize=(10, 4))
plt.bar(table["Scenario"], table["QBER"], color="indianred")
plt.axhline(0.11, color="black", linestyle="--", label="Example abort threshold")
plt.xticks(rotation=35, ha="right")
plt.ylabel("QBER")
plt.title("Final BB84 comparison")
plt.legend()
plt.tight_layout()
plt.show()
""",
        "The final comparison shows the central BB84 lesson: clean channels produce low QBER, while noise and eavesdropping raise QBER and reduce usable key efficiency.",
    ),
]


README = """# BB84 QKD Project

This folder contains a complete notebook-based BB84 Quantum Key Distribution project.

## Files

- `01_BB84_Noise_Free.ipynb` - basic BB84 without noise
- `02_BitFlip_Noise.ipynb` - bit-flip channel
- `03_PhaseFlip_Noise.ipynb` - phase-flip channel
- `04_Depolarizing_Noise.ipynb` - depolarizing channel
- `05_Amplitude_Damping.ipynb` - amplitude damping channel
- `06_QBER_vs_Noise.ipynb` - QBER comparison
- `07_Key_Agreement_Rate.ipynb` - key agreement rate
- `08_Efficiency_Rate.ipynb` - final-key efficiency estimate
- `09_Eve_Attack.ipynb` - intercept-resend attack
- `10_Eve_with_Noise.ipynb` - Eve attack with noisy channel
- `11_Information_Reconciliation.ipynb` - simplified reconciliation
- `12_Privacy_Amplification.ipynb` - simplified privacy amplification
- `13_IBM_Quantum_Hardware.ipynb` - simulator workflow and IBM hardware notes
- `14_Final_Comparison.ipynb` - full comparison table and graph
- `CONCLUSION.md` - separate project conclusion
- `run_all_notebooks.py` - executes every notebook in order

## How to run in VS Code

1. Open this `BB84_QKD_Project` folder in VS Code.
2. Create and activate a virtual environment.
3. Install dependencies:

```powershell
pip install -r requirements.txt
```

4. Open any notebook and select the Python environment as the notebook kernel.
5. Run cells from top to bottom.

You can also run all notebooks from the terminal:

```powershell
python run_all_notebooks.py
```

## Note

The IBM Quantum notebook runs on `AerSimulator` by default. Real IBM hardware requires your own IBM Quantum token and current backend availability.
"""


CONCLUSION = """# Project Conclusion

This project demonstrates the BB84 Quantum Key Distribution protocol from the ideal case to realistic noisy and attacked scenarios.

In a noise-free channel, Alice and Bob obtain matching sifted keys after basis reconciliation, producing QBER close to zero. With bit-flip, phase-flip, depolarizing, and amplitude-damping noise, QBER increases and the usable key rate decreases. This shows why QBER is one of the most important measurements in QKD security analysis.

The Eve attack notebooks show that intercept-resend eavesdropping introduces detectable disturbance. When Eve is combined with channel noise, the total QBER can cross an abort threshold, meaning Alice and Bob should reject the key or investigate the channel.

Information reconciliation can reduce mismatches, but it leaks some information through public communication. Privacy amplification solves this by compressing the reconciled key into a shorter and more secure final key.

Overall, BB84 is secure because quantum measurement disturbance makes eavesdropping visible statistically. The final usable key depends on channel noise, QBER, reconciliation efficiency, and privacy amplification.
"""


REQUIREMENTS = """qiskit>=1.0
qiskit-aer>=0.14
qiskit-ibm-runtime>=0.25
numpy>=1.26
pandas>=2.0
matplotlib>=3.8
jupyter>=1.0
nbclient>=0.10
ipykernel>=6.29
pylatexenc>=2.10
"""


RUNNER = """from pathlib import Path
import nbformat
from nbclient import NotebookClient


project_dir = Path(__file__).resolve().parent
notebooks = sorted(project_dir.glob("*.ipynb"))

for notebook_path in notebooks:
    print(f"Running {notebook_path.name}...")
    notebook = nbformat.read(notebook_path, as_version=4)
    client = NotebookClient(notebook, timeout=300, kernel_name="python3")
    client.execute()
    nbformat.write(notebook, notebook_path)
    print(f"Done {notebook_path.name}")

print("All notebooks executed successfully.")
"""


def main():
    PROJECT.mkdir(exist_ok=True)
    for filename, title, theory, body, conclusion in NOTEBOOKS:
        (PROJECT / filename).write_text(
            json.dumps(notebook(title, theory, body, conclusion), indent=2),
            encoding="utf-8",
        )
    (PROJECT / "README.md").write_text(README, encoding="utf-8")
    (PROJECT / "CONCLUSION.md").write_text(CONCLUSION, encoding="utf-8")
    (PROJECT / "requirements.txt").write_text(REQUIREMENTS, encoding="utf-8")
    (PROJECT / "run_all_notebooks.py").write_text(RUNNER, encoding="utf-8")


if __name__ == "__main__":
    main()
