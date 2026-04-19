from datetime import datetime
import os
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QLabel, QPushButton, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView, QDialog, QStackedWidget, QGroupBox, QMessageBox, QCheckBox, QTextEdit
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt5.QtGui import QIcon, QColor, QPalette
from PyQt5 import QtGui
import MetaTrader5 as mt5

def resource_path(relative_path):
    ''' Get absolute path to resource, works for dev and for PyInstaller '''
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
    
    def __init__(self, position_id=None, open_price=None, sl=None, tp1=None, tp2=None, tp3=None, buffer_pips=None, parent=None):
        super().__init__(parent)
        self.position_id = position_id
        self.open_price = open_price
        self.sl = sl
        self.tp1 = tp1
        self.tp2 = tp2
        self.tp3 = tp3
        self.buffer_pips = buffer_pips
        self.parent_app = parent
        self.stop_flag = False

    def run(self):
        current_tp = self.tp1
        trailing_sl = self.sl
        buffer_pips = self.buffer_pips
        short_first_round = True
        self.update_ui_signal.emit(self.position_id, True)
        
        while not self.stop_flag:
            current_price = self.get_current_price(self.position_id)
            is_open = self.is_still_open(self.position_id)
            if not is_open:
                break
            
            is_long_position = self.is_long_position(self.position_id)
            if is_long_position:
                if current_price >= current_tp:
                    new_sl = current_tp - buffer_pips
                    if new_sl > trailing_sl:
                        trailing_sl = new_sl
                        self.update_stop_loss(self.position_id, trailing_sl)
                    
                    if abs(current_tp - self.tp1) < 1e-06 and self.tp2 is not None:
                        current_tp = self.tp2
                    elif abs(current_tp - self.tp2) < 1e-06 and self.tp3 is not None:
                        current_tp = self.tp3
                    else:
                        self.close_position(self.position_id)
                        break
            else: # Short position
                if current_price <= current_tp:
                    new_sl = current_tp + buffer_pips
                    if short_first_round and (trailing_sl == 0 or new_sl < trailing_sl):
                        trailing_sl = new_sl
                        self.update_stop_loss(self.position_id, trailing_sl)
                        short_first_round = False
                    elif new_sl < trailing_sl:
                        trailing_sl = new_sl
                        self.update_stop_loss(self.position_id, trailing_sl)
                    
                    if abs(current_tp - self.tp1) < 1e-06 and self.tp2 is not None:
                        current_tp = self.tp2
                    elif abs(current_tp - self.tp2) < 1e-06 and self.tp3 is not None:
                        current_tp = self.tp3
                    else:
                        self.close_position(self.position_id)
                        break
            
            QThread.msleep(1000)
            
        self.update_ui_signal.emit(self.position_id, False)
        self.finished.emit()

    def is_still_open(self, position_id):
        position = mt5.positions_get(ticket=int(position_id))
        return position is not None and len(position) > 0

    def stop(self):
        self.stop_flag = True

    def is_long_position(self, position_id):
        position = mt5.positions_get(ticket=int(position_id))
        if position is None or len(position) == 0:
            return False
        return position[0].type == mt5.ORDER_TYPE_BUY

    def update_stop_loss(self, position_id, stop_loss):
        position = mt5.positions_get(ticket=int(position_id))
        if position is None or len(position) == 0:
            return
        current_tp = position[0].tp
        modify_request = {
            'action': mt5.TRADE_ACTION_SLTP,
            'position': int(position_id),
            'sl': stop_loss,
            'tp': current_tp }
        result = mt5.order_send(modify_request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            self.log_message_signal.emit(f"Failed to update SL: {result.comment}")
        elif self.parent_app:
            self.fetch_positions_signal.emit()

    def close_position(self, position_id):
        position = mt5.positions_get(ticket=int(position_id))
        if position is None or len(position) == 0:
            return
        symbol = position[0].symbol
        lot_size = position[0].volume
        order_type = mt5.ORDER_TYPE_SELL if position[0].type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
        close_request = {
            'action': mt5.TRADE_ACTION_DEAL,
            'symbol': symbol,
            'volume': lot_size,
            'type': order_type,
            'position': int(position_id),
            'price': mt5.symbol_info_tick(symbol).bid if order_type == mt5.ORDER_TYPE_SELL else mt5.symbol_info_tick(symbol).ask,
            'deviation': 10,
            'comment': 'TTP Close',
            'type_time': mt5.ORDER_TIME_GTC,
            'type_filling': mt5.ORDER_FILLING_IOC }
        result = mt5.order_send(close_request)
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            if self.parent_app:
                self.fetch_positions_signal.emit()

    def get_current_price(self, position_id):
        position = mt5.positions_get(ticket=int(position_id))
        if not position: return None
        symbol = position[0].symbol
        tick = mt5.symbol_info_tick(symbol)
        if not tick: return None
        return tick.bid if position[0].type == mt5.ORDER_TYPE_BUY else tick.ask

class MT5TradingAssistant(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('MT5 Trading Assistant (Decompiled)')
        self.setGeometry(100, 100, 1200, 800)
        # UI Initialization omitted for brevity but logic is preserved
        self.timer = QTimer(self)
        self.mt5_connected = False

    def connect_mt5(self):
        if not self.mt5_connected:
            if mt5.initialize():
                self.mt5_connected = True
                self.timer.start(400)
            else:
                QMessageBox.critical(self, "Error", "MT5 Initialize Failed")
        else:
            mt5.shutdown()
            self.mt5_connected = False
            self.timer.stop()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MT5TradingAssistant()
    window.show()
    sys.exit(app.exec_())
