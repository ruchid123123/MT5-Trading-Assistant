import sys
import os
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, 
                             QLineEdit, QLabel, QPushButton, QComboBox, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QDialog, QStackedWidget, 
                             QGroupBox, QMessageBox, QCheckBox, QTextEdit)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt5.QtGui import QIcon, QColor
import MetaTrader5 as mt5

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class TTPThread(QThread):
    update_ui_signal = pyqtSignal(int, bool)
    fetch_positions_signal = pyqtSignal()
    log_message_signal = pyqtSignal(str)
    finished = pyqtSignal()
    
    def __init__(self, position_id, open_price, sl, tp1, tp2=None, tp3=None, buffer_pips=0, parent=None):
        super().__init__(parent)
        self.position_id = position_id
        self.open_price = open_price
        self.sl = sl
        self.tp1 = tp1
        self.tp2 = tp2
        self.tp3 = tp3
        self.buffer_pips = buffer_pips
        self.stop_flag = False

    def run(self):
        current_target_tp = self.tp1
        trailing_sl = self.sl
        self.update_ui_signal.emit(self.position_id, True)
        
        while not self.stop_flag:
            if not self.is_still_open(self.position_id):
                break
            
            current_price = self.get_current_price(self.position_id)
            if current_price is None:
                QThread.msleep(500)
                continue

            is_long = self.is_long_position(self.position_id)
            
            # Logic for Long Position
            if is_long:
                if current_price >= current_target_tp:
                    new_sl = current_target_tp - self.buffer_pips
                    if new_sl > trailing_sl:
                        trailing_sl = new_sl
                        self.update_stop_loss(self.position_id, trailing_sl)
                    
                    # Move to next TP stage
                    if abs(current_target_tp - self.tp1) < 1e-07 and self.tp2:
                        current_target_tp = self.tp2
                    elif abs(current_target_tp - self.tp2) < 1e-07 and self.tp3:
                        current_target_tp = self.tp3
                    else:
                        self.close_position(self.position_id)
                        break
            # Logic for Short Position
            else:
                if current_price <= current_target_tp:
                    new_sl = current_target_tp + self.buffer_pips
                    if trailing_sl == 0 or new_sl < trailing_sl:
                        trailing_sl = new_sl
                        self.update_stop_loss(self.position_id, trailing_sl)
                    
                    if abs(current_target_tp - self.tp1) < 1e-07 and self.tp2:
                        current_target_tp = self.tp2
                    elif abs(current_target_tp - self.tp2) < 1e-07 and self.tp3:
                        current_target_tp = self.tp3
                    else:
                        self.close_position(self.position_id)
                        break
            
            QThread.msleep(1000)
            
        self.update_ui_signal.emit(self.position_id, False)
        self.finished.emit()

    def is_still_open(self, position_id):
        pos = mt5.positions_get(ticket=int(position_id))
        return pos is not None and len(pos) > 0

    def is_long_position(self, position_id):
        pos = mt5.positions_get(ticket=int(position_id))
        return pos[0].type == mt5.ORDER_TYPE_BUY if pos else True

    def update_stop_loss(self, position_id, stop_loss):
        pos = mt5.positions_get(ticket=int(position_id))
        if not pos: return
        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "position": int(position_id),
            "sl": float(stop_loss),
            "tp": float(pos[0].tp)
        }
        result = mt5.order_send(request)
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            self.log_message_signal.emit(f"Position {position_id} SL updated to {stop_loss}")
            self.fetch_positions_signal.emit()

    def close_position(self, position_id):
        pos = mt5.positions_get(ticket=int(position_id))
        if not pos: return
        symbol = pos[0].symbol
        tick = mt5.symbol_info_tick(symbol)
        order_type = mt5.ORDER_TYPE_SELL if pos[0].type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
        price = tick.bid if order_type == mt5.ORDER_TYPE_SELL else tick.ask
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": pos[0].volume,
            "type": order_type,
            "position": int(position_id),
            "price": price,
            "deviation": 10,
            "magic": 123456,
            "comment": "TTP Closed",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        result = mt5.order_send(request)
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            self.log_message_signal.emit(f"Position {position_id} closed at target TP")
            self.fetch_positions_signal.emit()

    def get_current_price(self, position_id):
        pos = mt5.positions_get(ticket=int(position_id))
        if not pos: return None
        tick = mt5.symbol_info_tick(pos[0].symbol)
        if not tick: return None
        return tick.bid if pos[0].type == mt5.ORDER_TYPE_BUY else tick.ask

class MT5TradingAssistant(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('MT5 Trading Assistant - Core Logic Restored')
        self.setGeometry(100, 100, 1200, 800)
        self.ttp_threads = {}
        self.init_ui()
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_live_data)
        self.mt5_connected = False

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.tabs = QStackedWidget()
        self.layout.addWidget(self.tabs)
        
        # Risk Calculator Page
        self.calc_page = QWidget()
        calc_layout = QFormLayout(self.calc_page)
        self.balance_input = QLineEdit("10000")
        self.risk_percent = QLineEdit("1")
        self.stop_loss_pips = QLineEdit("20")
        calc_layout.addRow("Account Balance:", self.balance_input)
        calc_layout.addRow("Risk Percentage (%):", self.risk_percent)
        calc_layout.addRow("Stop Loss (Pips):", self.stop_loss_pips)
        
        self.calc_btn = QPushButton("Calculate Lot Size")
        self.calc_btn.clicked.connect(self.calculate_results)
        calc_layout.addRow(self.calc_btn)
        
        self.result_label = QLabel("Recommended Lot: -")
        calc_layout.addRow(self.result_label)
        self.tabs.addWidget(self.calc_page)

        # Order Manager Page
        self.order_page = QWidget()
        order_layout = QVBoxLayout(self.order_page)
        self.conn_btn = QPushButton("Connect to MT5")
        self.conn_btn.clicked.connect(self.toggle_mt5)
        order_layout.addWidget(self.conn_btn)
        
        self.pos_table = QTableWidget(0, 7)
        self.pos_table.setHorizontalHeaderLabels(["Ticket", "Symbol", "Volume", "Type", "Open Price", "Profit", "Action"])
        self.pos_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        order_layout.addWidget(self.pos_table)
        self.tabs.addWidget(self.order_page)

        # Navigation
        nav_layout = QHBoxLayout()
        self.btn_tab1 = QPushButton("Calculator")
        self.btn_tab1.clicked.connect(lambda: self.tabs.setCurrentIndex(0))
        self.btn_tab2 = QPushButton("Order Manager")
        self.btn_tab2.clicked.connect(lambda: self.tabs.setCurrentIndex(1))
        nav_layout.addWidget(self.btn_tab1)
        nav_layout.addWidget(self.btn_tab2)
        self.layout.addLayout(nav_layout)

    def calculate_results(self):
        try:
            balance = float(self.balance_input.text())
            risk = float(self.risk_percent.text()) / 100
            sl_pips = float(self.stop_loss_pips.text())
            
            risk_amount = balance * risk
            # Simple assumption: 1 pip on 1 lot standard = $10 (varies by symbol)
            lot_size = risk_amount / (sl_pips * 10) 
            self.result_label.setText(f"Recommended Lot: {round(lot_size, 2)} (Risk: ${round(risk_amount, 2)})")
        except ValueError:
            QMessageBox.warning(self, "Error", "Invalid Input")

    def toggle_mt5(self):
        if not self.mt5_connected:
            if mt5.initialize():
                self.mt5_connected = True
                self.conn_btn.setText("Disconnect MT5")
                self.timer.start(1000)
            else:
                QMessageBox.critical(self, "Error", "MT5 Init Failed")
        else:
            mt5.shutdown()
            self.mt5_connected = False
            self.conn_btn.setText("Connect MT5")
            self.timer.stop()

    def update_live_data(self):
        if not self.mt5_connected: return
        positions = mt5.positions_get()
        self.pos_table.setRowCount(0)
        if positions:
            for p in positions:
                row = self.pos_table.rowCount()
                self.pos_table.insertRow(row)
                self.pos_table.setItem(row, 0, QTableWidgetItem(str(p.ticket)))
                self.pos_table.setItem(row, 1, QTableWidgetItem(p.symbol))
                self.pos_table.setItem(row, 2, QTableWidgetItem(str(p.volume)))
                self.pos_table.setItem(row, 3, QTableWidgetItem("BUY" if p.type == 0 else "SELL"))
                self.pos_table.setItem(row, 4, QTableWidgetItem(str(p.price_open)))
                self.pos_table.setItem(row, 5, QTableWidgetItem(str(round(p.profit, 2))))
                
                close_btn = QPushButton("Close")
                close_btn.clicked.connect(lambda _, t=p.ticket: self.close_by_ticket(t))
                self.pos_table.setCellWidget(row, 6, close_btn)

    def close_by_ticket(self, ticket):
        # Logic to send close request immediately
        pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = MT5TradingAssistant()
    ex.show()
    sys.exit(app.exec_())
