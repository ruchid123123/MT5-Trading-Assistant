# MT5 Trading Assistant / MT5 交易助手

## Overview / 项目概览

The MT5 Trading Assistant is a comprehensive MetaTrader 5 (MT5) platform application that provides a graphical user interface (GUI) for calculating and managing positions. This application is designed to help traders efficiently manage their trades and make informed decisions.

MT5 交易助手是一个功能强大的 MetaTrader 5 (MT5) 平台辅助程序，提供图形用户界面 (GUI) 用于计算和管理仓位。该程序旨在帮助交易者更高效地管理交易并做出明智的决策。

---

## 🚀 Key Features / 核心功能

- **Position Calculation / 仓位计算**: Automatically calculates the recommended lot size based on account balance and risk percentage. (根据账户余额和风险比例自动计算推荐手数。)
- **Order Management / 订单管理**: Real-time retrieval of MT5 positions and pending orders. (实时获取并管理 MT5 持仓和挂单。)
- **TTP (Triple Take Profit) Mechanism / 三级止盈机制**: Set up to 3 take profit zones. The program automatically trails the stop loss to breakeven or profit zones as targets are hit. (支持设置 3 级止盈。当达到止盈点时，程序会自动移动止损位至保本或盈利区域。)
- **Risk Management / 风险管理**: Easily modify or close positions with a single click. (一键修改或平仓，快速控制风险。)
- **Dark Mode / 深色模式**: Modern GUI with a dark aesthetic for professional trading. (现代感十足的深色模式界面。)

---

## 🛠 Installation & Usage / 安装与使用

### For Developers (Running from Source) / 开发者（运行源码）
1. **Requirements / 要求**: Python 3.9+ (Windows environment recommended).
2. **Install Dependencies / 安装依赖**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Run / 运行**:
   ```bash
   python main.py
   ```

### For Users / 普通用户
Simply download the pre-compiled version from the `release/` folder:
可以直接从 `release/` 文件夹下载预编译版本：
- **`release/MT5.Trading.Assistant.exe`**

---

## 🔍 Reverse Engineering Notes / 逆向说明
This repository contains both the original binary and the recovered Python source code. For more details on the reverse engineering process, see the [research/](research/) directory.

本仓库包含原始二进制文件以及还原后的 Python 源代码。有关逆向工程的详细过程，请参阅 [research/](research/) 目录。

---

## License / 许可协议
The MT5 Trading Assistant application is licensed under the MIT License.

## Acknowledgments / 致谢
Originally created by [Reno-codes]. Source code recovered and refined by Gemini CLI Agent.

