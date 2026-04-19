# MT5 Trading Assistant - Reverse Engineering Notes

This directory contains artifacts from the reverse engineering process of the `MT5.Trading.Assistant.exe` binary.

## Extraction Process
1. **Tool**: `pyinstxtractor.py` (included in `tools/`)
2. **Method**: Extracted the Python archive (CArchive) from the PyInstaller-packed executable.
3. **Entry Point**: `mt5tradingassistant.pyc` (Python 3.9 bytecode)

## Decompilation
1. **Tool**: `pycdc` (C++ Python Bytecode Disassembler)
2. **Raw Output**: `raw_decompiled.py` contains the direct output from the decompiler.
    - *Note*: The raw output contains decompilation errors (like `None[0]` or incomplete UI logic) due to bytecode complexity and version mismatches.

## Results
The core trading logic was successfully recovered and refined into `main.py` in the root directory.

### Key Logic Recovered:
- **TTP (Triple Take Profit)**: Automated threading for 3-level profit taking and trailing stop loss.
- **MT5 Integration**: Usage of the `MetaTrader5` Python library for order management.
- **Risk Calculation**: Formulas for lot size calculation based on account balance and risk percentage.
