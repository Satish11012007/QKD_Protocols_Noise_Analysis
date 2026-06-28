# BB84 QKD Project

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
