# Source Generated with Decompyle++
# File: mt5tradingassistant.pyc (Python 3.9)

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
    pass
# WARNING: Decompyle incomplete


class TTPThread(QThread):
    update_ui_signal = pyqtSignal(int, bool)
    fetch_positions_signal = pyqtSignal()
    log_message_signal = pyqtSignal(str)
    finished = pyqtSignal()
    
    def __init__(self = None, position_id = None, open_price = None, sl = None, tp1 = None, tp2 = None, tp3 = None, buffer_pips = None, parent = ((None,),)):
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
        if not self.stop_flag:
            current_price = self.get_current_price(self.position_id)
            is_open = self.is_still_open(self.position_id)
            if not is_open:
                pass
            else:
                is_long_position = self.is_long_position(self.position_id)
                if is_long_position and current_price >= current_tp:
                    new_sl = current_tp - buffer_pips
                    if new_sl > trailing_sl:
                        trailing_sl = new_sl
                        self.update_stop_loss(self.position_id, trailing_sl)
                    if abs(current_tp - self.tp1) < 1e-06 and self.tp2 is not None:
                        current_tp = self.tp2
                    elif abs(current_tp - self.tp2) < 1e-06 and self.tp3 is not None:
                        current_tp = self.tp3
                    elif (abs(current_tp - self.tp3) < 1e-06 or current_tp == self.tp1) and self.tp2 is None:
                        self.close_position(self.position_id)
                    
                if is_long_position and current_price <= current_tp:
                    new_sl = current_tp + buffer_pips
                    if short_first_round and new_sl > trailing_sl:
                        trailing_sl = new_sl
                        self.update_stop_loss(self.position_id, trailing_sl)
                        short_first_round = False
                    if new_sl < trailing_sl:
                        trailing_sl = new_sl
                        self.update_stop_loss(self.position_id, trailing_sl)
                    if abs(current_tp - self.tp1) < 1e-06 and self.tp2 is not None:
                        current_tp = self.tp2
                    elif abs(current_tp - self.tp2) < 1e-06 and self.tp3 is not None:
                        current_tp = self.tp3
                    elif (abs(current_tp - self.tp3) < 1e-06 or current_tp == self.tp1) and self.tp2 is None:
                        self.close_position(self.position_id)
                    
                QThread.msleep(1000)
        self.update_ui_signal.emit(self.position_id, False)
        self.finished.emit()

    
    def is_still_open(self, position_id):
        position = mt5.positions_get(int(position_id), **('ticket',))
        if position is not None:
            pass
        return len(position) > 0

    
    def stop(self):
        '''Set the stop flag to stop the thread gracefully.'''
        self.stop_flag = True

    
    def is_long_position(self, position_id):
        position = mt5.positions_get(int(position_id), **('ticket',))
        if position is None or len(position) == 0:
            print('MT5 Error', f'''Position {position_id} not found.''')
            self.log_message_signal.emit(f'''Position {position_id} not found.''')
            return False
        order_type = None[0].type
        return order_type == mt5.ORDER_TYPE_BUY

    
    def get_current_stop_loss(self, position_id):
        position = mt5.positions_get(int(position_id), **('ticket',))
        if position is None or len(position) == 0:
            print('MT5 Error', f'''Position {position_id} not found.''')
            self.log_message_signal.emit(f'''Position {position_id} not found.''')
            return None
        return None[0].sl

    
    def update_stop_loss(self, position_id, stop_loss):
        position = mt5.positions_get(int(position_id), **('ticket',))
        if position is None or len(position) == 0:
            print('MT5 Error', f'''Position {position_id} not found.''')
            self.log_message_signal.emit(f'''Position {position_id} not found.''')
            return None
        current_tp = None[0].tp
        modify_request = {
            'action': mt5.TRADE_ACTION_SLTP,
            'position': int(position_id),
            'sl': stop_loss,
            'tp': current_tp }
        result = mt5.order_send(modify_request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print('MT5 Error', f'''Failed to update SL for position {position_id}. Error: {result.comment}''')
        elif self.parent_app:
            self.fetch_positions_signal.emit()
        print('Updating SL for position', position_id, 'was Success!')
        self.log_message_signal.emit(f'''Updated SL for position {position_id} to {stop_loss}''')

    
    def close_position(self, position_id):
        position = mt5.positions_get(int(position_id), **('ticket',))
        if position is None or len(position) == 0:
            print('MT5 Error', f'''Position {position_id} not found.''')
            return None
        symbol = None[0].symbol
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
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print('MT5 Error', f'''Failed to close position {position_id}. Error: {result.comment}''')
            self.log_message_signal.emit(f'''Failed to close position {position_id}. Error: {result.comment}''')
        elif self.parent_app:
            self.fetch_positions_signal.emit()
        print('Closing position', position_id, 'was Success!')
        self.log_message_signal.emit(f'''Closed position {position_id}.''')

    
    def get_current_price(self, position_id):
        position = mt5.positions_get(int(position_id), **('ticket',))
        if position is None or len(position) == 0:
            print('MT5 Error', f'''Position {position_id} not found.''')
            self.log_message_signal.emit(f'''Position {position_id} not found.''')
            return None
        symbol = None[0].symbol
        tick = mt5.symbol_info_tick(symbol)
        if not tick:
            print('MT5 Error', f'''Failed to fetch price for symbol {symbol}.''')
            self.log_message_signal.emit(f'''Failed to fetch price for symbol {symbol}.''')
            return None
        if None[0].type == mt5.ORDER_TYPE_BUY:
            return tick.bid
        return None.ask

    
    def position_exists(self, position_id):
        position = mt5.positions_get(int(position_id), **('ticket',))
        if position is not None:
            pass
        return len(position) > 0

    __classcell__ = None


class MT5TradingAssistant(QWidget):
    update_ui_signal = pyqtSignal(int, bool)
    
    def __init__(self = None):
        super().__init__()
        self.setWindowTitle('MT5 Trading Assistant by @renato_lulic')
        self.setGeometry(100, 100, 1300, 750)
        self.setWindowIcon(QIcon(resource_path('logo.jpeg')))
        self.layout = QVBoxLayout(self)
        self.ttp_threads = { }
        self.active_ttp_states = { }
        self.close_button_states = { }
        self.ttp_position_values = { }
        self.update_ui_signal.connect(self.update_ui)
        self.stacked_widget = QStackedWidget(self)
        self.layout.addWidget(self.stacked_widget)
        self.main_page = QWidget()
        self.second_page = QWidget()
        self.create_main_page()
        self.create_second_page()
        self.stacked_widget.addWidget(self.main_page)
        self.stacked_widget.addWidget(self.second_page)
        self.navigation_layout = QHBoxLayout()
        self.layout.addLayout(self.navigation_layout)
        self.to_main_page_button = QPushButton('Risk & Position Calculator')
        None((lambda : self.stacked_widget.setCurrentWidget(self.main_page)))
        self.navigation_layout.addWidget(self.to_main_page_button)
        self.to_second_page_button = QPushButton('MT5 Order Manager')
        self.to_second_page_button.clicked.connect(self.check_and_open_second_page)
        self.navigation_layout.addWidget(self.to_second_page_button)
        self.create_toggle_buttons()
        self.set_dark_mode()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_live_data)
        self.timer.setInterval(400)
        self.mt5_connected = False
        self.positions_table.doubleClicked.connect(self.open_edit_modal)
        self.log_window = self.LogWindow(self)

    
    def update_ui(self, position_id, is_active):
        if is_active:
            self.mark_ttp_active(position_id)
        else:
            self.mark_ttp_inactive(position_id)

    
    def open_edit_modal(self, index):
        row = index.row()
        sl_value = self.positions_table.item(row, 7).text()
        tp_value = self.positions_table.item(row, 8).text()
        open_price = self.positions_table.item(row, 6).text()
        position_id = self.positions_table.item(row, 0).text()
        position_type = self.positions_table.item(row, 4).text()
        self.edit_modal = EditPositionModal(sl_value, tp_value, position_id, open_price, position_type, self)
        self.edit_modal.show()

    
    def modify_position(self, position_id, new_sl, new_tp, new_price):
        position = mt5.positions_get(int(position_id), **('ticket',))
        order = mt5.orders_get(int(position_id), **('ticket',))
        if position is None and order is None:
            print(position, order)
            self.show_error_dialog('MT5 Error', 'Could not find position/order.')
            return None
        if None is not None and len(order) > 0:
            modify_request = {
                'action': mt5.TRADE_ACTION_MODIFY,
                'order': int(position_id),
                'price': new_price,
                'sl': new_sl,
                'tp': new_tp }
            result = mt5.order_send(modify_request)
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                self.show_error_dialog('MT5 Error', f'''Failed to modify pending order {position_id}. Error: {result.comment} Error: {result}''')
            else:
                self.fetch_opened_positions_and_orders()
        elif position is not None and len(position) > 0:
            modify_request = {
                'action': mt5.TRADE_ACTION_SLTP,
                'position': int(position_id),
                'sl': new_sl,
                'tp': new_tp }
            result = mt5.order_send(modify_request)
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                self.show_error_dialog('MT5 Error', f'''Failed to modify position {position_id}. Error: {result.comment}''')
            else:
                self.fetch_opened_positions_and_orders()
        else:
            self.show_error_dialog('MT5 Error', 'Could not determine position type.')

    
    def create_main_page(self):
        layout = QVBoxLayout(self.main_page)
        self.create_input_form(layout)
        self.calculate_button = QPushButton('Calculate', self)
        self.calculate_button.clicked.connect(self.calculate_results)
        layout.addWidget(self.calculate_button)
        self.results_table = QTableWidget(self)
        layout.addWidget(self.results_table)
        self.risk_reward_lineedit = QLineEdit(self)
        self.risk_reward_lineedit.setReadOnly(True)
        self.risk_reward_lineedit.setAlignment(Qt.AlignCenter)
        self.risk_reward_lineedit.setText('RISK:REWARD will be displayed here')
        layout.addWidget(self.risk_reward_lineedit)
        self.position_size_lineedit = QLineEdit(self)
        self.position_size_lineedit.setReadOnly(True)
        self.position_size_lineedit.setAlignment(Qt.AlignCenter)
        self.position_size_lineedit.setText('Recommended Position Size will be displayed here')
        layout.addWidget(self.position_size_lineedit)

    
    def create_second_page(self):
        layout = QVBoxLayout(self.second_page)
        self.connect_button = QPushButton('Connect', self.second_page)
        self.connect_button.clicked.connect(self.connect_mt5)
        self.connect_button.setStyleSheet('font-size: 14px; padding: 8px;')
        layout.addWidget(self.connect_button)
        self.account_info_group = QGroupBox('Account Information', self.second_page)
        self.account_info_group.setStyleSheet('\n            QGroupBox {\n                font-size: 14px;\n                font-weight: bold;\n                border: 1px solid #0388fc;\n                border-radius: 1px;\n                padding: 5px;\n                margin-top: 5px;\n            }\n            QGroupBox::title {\n                subcontrol-origin: margin;\n                subcontrol-position: top center;\n                padding: 0 3px;\n            }\n        ')
        account_info_layout = QVBoxLayout(self.account_info_group)
        self.account_info_label = QLabel('Account Info will appear here', self.second_page)
        self.account_info_label.setStyleSheet('font-size: 14px; line-height: 1.5;')
        self.account_info_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        account_info_layout.addWidget(self.account_info_label)
        self.account_info_group.setLayout(account_info_layout)
        layout.addWidget(self.account_info_group)
        self.positions_table = QTableWidget(self.second_page)
        self.positions_table.setColumnCount(12)
        self.positions_table.setHorizontalHeaderLabels([
            'Ticket',
            'Time',
            'Symbol',
            'Lot Size',
            'Type',
            'Current Price',
            'Price',
            'S/L',
            'T/P',
            'Current Profit',
            'R:R',
            'Close/Cancel'])
        self.positions_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.positions_table.setStyleSheet('\n            QHeaderView::section {\n                background-color: #0388fc;\n                color: white;\n                font-weight: bold;\n            }\n            QTableWidget::item {\n                padding: 5px;\n            }\n        ')
        layout.addWidget(self.positions_table)
        self.log_button = QPushButton('Toggle Log', self.second_page)
        self.log_button.clicked.connect(self.toggle_log_window)
        layout.addWidget(self.log_button)

    
    def toggle_log_window(self):
        if self.log_window.isVisible():
            self.log_window.hide()
        else:
            self.log_window.show()

    
    class LogWindow(QDialog):
        
        def __init__(self = None, parent = None):
            super().__init__(parent)
            self.setWindowTitle('Terminal Log')
            self.setGeometry(100, 100, 600, 400)
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
            self.log_area = QTextEdit(self)
            self.log_area.setReadOnly(True)
            self.log_area.setStyleSheet('font-size: 12px; padding: 10px;')
            layout = QVBoxLayout(self)
            layout.addWidget(self.log_area)

        
        def append_log(self, message):
            self.log_area.append(message)

        __classcell__ = None

    
    def log_message(self, message):
        self.log_window.append_log(message)

    
    def connect_mt5(self):
        ''' Connect or disconnect from MT5. '''
        if not self.mt5_connected:
            self.connect_button.setText('Connect MT5')
            self.revert_to_account_info_label()
            if not self.initialize_mt5():
                return None
            None.connect_button.setText('Disconnect')
            self.timer.start()
        elif not self.is_mt5_connected():
            self.show_error_dialog('MT5 Error', 'MT5 has been disconnected unexpectedly. Please restart MT5.')
            self.timer.stop()
            self.mt5_connected = False
            self.connect_button.setText('Connect MT5')
            self.revert_to_account_info_label()
            return None
        self.timer.stop()
        mt5.shutdown()
        self.mt5_connected = False
        self.connect_button.setText('Connect MT5')
        self.show_error_dialog('MT5 Error', 'MT5 has been disconnected.')
        self.revert_to_account_info_label()

    
    def revert_to_account_info_label(self):
