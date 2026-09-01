#!/usr/bin/env python3
import sys
import time
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QPushButton, QLabel, QComboBox, QHBoxLayout, QSpinBox, QColorDialog
)
from PySide6.QtCore import QTimer, Qt
from PySide6.QtSerialPort import QSerialPort, QSerialPortInfo
from PySide6.QtGui import QColor

from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QColorDialog, QDialogButtonBox, QListWidget, QDialog, QCheckBox
from PySide6.QtGui import QPainter, QColor, QConicalGradient, QMouseEvent, QIcon
from PySide6.QtCore import Qt, QPointF, QRectF, QSize, QSettings, QPoint
import math

class EffectsDialog(QDialog):
    """Popup dialog to select an effect."""
    def __init__(self, parent=None):
        super().__init__(parent)
        # Create a list of the effects in a new window
        self.setWindowTitle("Select Effect")
        layout = QVBoxLayout(self)
        self.parent_widget = parent
        self.effect_list = QListWidget()
        # Effect list 
        self.effect_list.addItems(["SENSOR_MODE","INTENSITY", "COMET+","COMET-","BREATHING","GRADIENT","CANDLE","BEAT"])
        layout.addWidget(QLabel("Choose an effect:"))
        layout.addWidget(self.effect_list)

        self.flash_checkbox = QCheckBox("Enable break flash")
        self.flash_checkbox.setChecked(self.parent_widget.break_flash_enabled if self.parent_widget else True)
        layout.addWidget(self.flash_checkbox)

        # Double-clicking an item selects it and closes the dialog
        self.effect_list.itemDoubleClicked.connect(self.accept)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.setCenterButtons(True)
        if button_box.layout() is not None:
            button_box.layout().setSpacing(10)
            button_box.layout().setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(24)
        layout.addWidget(button_box)

    def selected_effect(self):
        item = self.effect_list.currentItem()
        # Return the selected effect
        return item.text() if item else None

class CustomColorButton(QPushButton):
    """Button that opens the color picker on double-click only."""

    def __init__(self, parent=None, logo=True, index=0):
        if logo:
            super().__init__("🎨")
        else:
            super().__init__()
        self.parent_widget = parent
        # self.setFixedSize(35, 35)
        # Colour array index
        self.index = index
        # Dark theme
        self.setStyleSheet(f"""
            QPushButton {{
                border-radius: 6px;
                height: 15px;
                width: 15px;
                margin: 2px;
                border: 1px solid #444;
                background-color: rgb({self.parent_widget.colors[self.index][0]},{self.parent_widget.colors[self.index][1]},{self.parent_widget.colors[self.index][2]});
            }}
            QPushButton:pressed {{
                border: 2px solid #888;
            }}
        """)
        self._last_click = None

    def mousePressEvent(self, event: QMouseEvent):
        self._last_click = "Click"

    def mouseReleaseEvent(self, event: QMouseEvent):
        # Schedule single-click action if it's not a double-click
        QTimer.singleShot(QApplication.instance().doubleClickInterval(), self.perform_single_click_action)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        self._last_click = "Double Click"

        """Open a color wheel picker with live updates, apply on OK."""

        if not self.parent_widget.serial.is_connected:
            return

        # Create a Qt color dialog (force the modern wheel, not OS default)
        color_dialog = QColorDialog(QColor(self.parent_widget.colors[self.index][0],self.parent_widget.colors[self.index][1],self.parent_widget.colors[self.index][2]),self)
        color_dialog.setWindowTitle("🎨 Pick LED Color")
        color_dialog.setOption(QColorDialog.ShowAlphaChannel, False)
        color_dialog.setOption(QColorDialog.DontUseNativeDialog, False)  # ensures wheel is available
        color_dialog.setOption(QColorDialog.NoButtons, False)
        color_dialog.setStyleSheet("""
            QWidget {
                background-color: #121212;
                color: #f0f0f0;
                font-size: 12px;
            }
            QPushButton {
                border-radius: 6px;
                height: 15px;
                width: 40px;
                margin: 2px;
                border: 1px solid #444;
            }
            QPushButton:pressed {
                border: 2px solid #888;
            }
            QComboBox {
                background-color: #1e1e1e;
                border-radius: 4px;
                padding: 2px;
            }
            QLabel {
                color: #e0e0e0;
            }
        """)
        # Connect live updates as the user moves in the color wheel
        color_dialog.currentColorChanged.connect(self.parent_widget.update_color_live)

        # Show dialog and commit on OK
        if color_dialog.exec() == QColorDialog.Accepted:
            final_color = color_dialog.selectedColor()
            if final_color.isValid():
                r, g, b = final_color.red(), final_color.green(), final_color.blue()
                # Update current colour
                self.parent_widget.colors[self.index][0],self.parent_widget.colors[self.index][1],self.parent_widget.colors[self.index][2] = final_color.red(), final_color.green(), final_color.blue()
                # ✅ Commit final color
                self.parent_widget.send_rgb_color(r, g, b)
                # Update button to preview the chosen color
                self.setStyleSheet(f"""
                    QPushButton {{
                        border-radius: 6px;
                        height: 15px;
                        width: 15px;
                        margin: 2px;
                        border: 1px solid #444;
                        background-color: rgb({r},{g},{b});
                    }}
                    QPushButton:pressed {{
                        border: 2px solid #888;
                    }}
                """)
                # self.setStyleSheet(f"background-color: rgb({r},{g},{b});")
                # self.setStyleSheet(f"border-radius: 6px;")

    def perform_single_click_action(self):
        if self._last_click == "Click":
            # Apply current colour when clicking
            self.parent_widget.send_rgb_color(self.parent_widget.colors[self.index][0],self.parent_widget.colors[self.index][1],self.parent_widget.colors[self.index][2])
            pass

class SerialManager:
    def __init__(self):
        self.serial_port = QSerialPort()
        self.is_connected = False

    def get_ports(self):
        return [p.portName() for p in QSerialPortInfo.availablePorts()]

    def connect(self, port):
        if self.is_connected:
            self.disconnect()
        self.serial_port.setPortName(port)
        self.serial_port.setBaudRate(9600)
        if self.serial_port.open(QSerialPort.ReadWrite):
            time.sleep(2)  # wait for Arduino reset
            self.is_connected = True
            return True
        return False

    def disconnect(self):
        if self.is_connected:
            self.serial_port.close()
            self.is_connected = False

    def send(self, cmd):
        if self.is_connected:
            self.serial_port.write((cmd + "\n").encode())

class LightPomodoroApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.serial = SerialManager()
        # Pomodoro state
        self.timer = QTimer()
        self.timer.timeout.connect(self.tick)
        self._state = True
        self.is_running = False
        self.is_break = False
        self.time_left = 0
        self.break_flash_enabled = True

        self.focus_minutes = 45
        self.break_minutes = 5



        # Drag tracking
        self.drag_pos = None

        # Window location
        self.x = 0
        self.y = 0

        # Create an array (list) of 4 RGB colours
        self.colors = [
            [255, 0, 0],  # First color
            [0, 255, 0],  # Second color
            [0, 0, 0],  # Third color
            [255, 85, 0]   # Fourth color
        ]

        self.current_color = [0,0,0] # Stores the last sent colour for effects

        self.window_width = 120
        self.window_height = 175

        # Load settings when the app starts
        self.load_settings()

        self.init_ui()

    def load_settings(self):
        settings = QSettings("MyCompany", "LED Pomodoro")

        if settings.contains("pos"): #window position
            self.move(settings.value("pos", QPoint(100, 100)))
            pos = settings.value("pos", QPoint(100, 100))  # Default to (100, 100)
            pos = QPoint(pos.x(), pos.y())

            self.x = pos.x()
            self.y = pos.y()

        if settings.contains("colors"):
            # Group back into RGB triplets
            flat = settings.value("colors")
            # Ensure all are integers (QSettings may return strings)
            flat = [int(x) for x in flat]
            self.colors = [flat[i:i+3] for i in range(0, len(flat), 3)]

        if settings.contains("f_mins"):
            self.focus_minutes = settings.value("f_mins")

        if settings.contains("b_mins"):
            self.break_minutes = settings.value("b_mins")

        if settings.contains("break_flash_enabled"):
            raw = settings.value("break_flash_enabled", True)
            if isinstance(raw, str):
                self.break_flash_enabled = raw.lower() in ("1", "true", "yes", "on")
            else:
                self.break_flash_enabled = bool(raw)

    def mouseDoubleClickEvent(self, event):
        """
        This is called when the user double-clicks inside the window.
        """
        if event.button() == Qt.LeftButton:
            # Check if the click happened on the *window*, not a child widget
            # child = self.childAt(event.position().toPoint())
            # if child is None:  # Blank space only
            # Update the window position to the top-right corner of the current screen
            self.current_screen = QApplication.screenAt(self.pos())
            self.x = self.current_screen.geometry().x() + self.current_screen.geometry().width() - self.width()
            self.y = self.current_screen.geometry().y() + self.current_screen.geometry().height() - self.height() - self.taskbar_height
            # Move window to a new screen location
            self.move(self.x, self.y)
        super().mouseDoubleClickEvent(event)

    def init_ui(self):
        self.setWindowTitle("LED Pomodoro")        
        # Get list of available screens
        screens = QApplication.screens()

        self.resize(self.window_width, self.window_height) 

        # Determine the taskbar height by comparing the screen geometry and available geometry
        primary_screen = QApplication.primaryScreen()
        geo = primary_screen.geometry()
        available_geometry = primary_screen.availableGeometry()
        self.taskbar_height = geo.height() - available_geometry.height()

        # Target screen is the current screen that the window is on (or the specified screen index)
        # Get the current screen index based on the window's position
        self.current_screen = QApplication.screenAt(self.pos())
        self.x = self.current_screen.geometry().x() + self.current_screen.geometry().width() - self.width()
        self.y = self.current_screen.geometry().y() + self.current_screen.geometry().height() - self.height() - self.taskbar_height

        # Move window safely inside screen area
        if self.x == 0 and self.y == 0:
            self.move(self.x, self.y)

        # Frameless, always on top
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)

        # Dark theme
        self.setStyleSheet("""
            QWidget {
                background-color: #121212;
                color: #f0f0f0;
                font-size: 12px;
            }
            QPushButton {
                border-radius: 6px;
                height: 15px;
                width: 15px;
                margin: 2px;
            }
            QPushButton:pressed {
                border: 2px solid #888;
            }
            QComboBox {
                background-color: #1e1e1e;
                border: none;
                border-radius: 4px;
                padding: 2px;
            }
            QSpinBox {
                background-color: #888;
                # border: none;
                border-radius: 4px;
                padding: 2px;
            }
            QLabel {
                color: #e0e0e0;
            }
        """)

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setSpacing(6)

        # Close button (hidden until hover top)
        self.close_btn = QPushButton("×")
        self.close_btn.setFixedSize(20, 20)
        self.close_btn.setStyleSheet(
            "QPushButton { background: none; color: #666; border: none; }"
            "QPushButton:hover { color: red; }"
        )
        self.close_btn.clicked.connect(self.close)
        self.close_btn.hide()
        layout.addWidget(self.close_btn, alignment=Qt.AlignRight)

        # Connection row
        conn_layout = QHBoxLayout()
        self.port_combo = QComboBox()
        self.port_combo.addItems(self.serial.get_ports() or ["No ports"])
        conn_layout.addWidget(self.port_combo)
        self.connect_btn = QPushButton("⏺")
        self.connect_btn.setFixedWidth(15)
        self.connect_btn.clicked.connect(self.toggle_connection)
        conn_layout.addWidget(self.connect_btn)
        layout.addLayout(conn_layout)

        # LED color buttons
        led_layout = QHBoxLayout()
        self.red_btn = CustomColorButton(self, False, 0)
        # self.red_btn = QPushButton("")
        # self.red_btn.setStyleSheet("background-color: red; border: 1px solid #444;")
        # self.red_btn.clicked.connect(lambda: self.serial.send("RED"))
        led_layout.addWidget(self.red_btn)

        self.green_btn = CustomColorButton(self, False, 1)
        led_layout.addWidget(self.green_btn)

        self.off_btn = CustomColorButton(self, False, 2)
        led_layout.addWidget(self.off_btn)

        # Custom color button
        self.custom_btn = CustomColorButton(self, True, 3)
        led_layout.addWidget(self.custom_btn)

        layout.addLayout(led_layout)

        # Pomodoro settings
        settings_layout = QHBoxLayout()
        self.focus_spin = QSpinBox()
        self.focus_spin.setRange(1, 60)
        self.focus_spin.setValue(self.focus_minutes)
        self.focus_spin.setFixedWidth(35)
        self.focus_spin.valueChanged.connect(self.update_time)
        
        settings_layout.addWidget(QLabel("F"))
        settings_layout.addWidget(self.focus_spin)

        self.break_spin = QSpinBox()
        self.break_spin.setRange(1, 60)
        self.break_spin.setValue(self.break_minutes)
        self.break_spin.setFixedWidth(35)
        self.break_spin.valueChanged.connect(lambda v: setattr(self, "break_minutes", v))
        settings_layout.addWidget(QLabel("B"))
        settings_layout.addWidget(self.break_spin)
        layout.addLayout(settings_layout)

        # Pomodoro display
        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        self.time_label = QLabel(f"{self.focus_minutes}:00")
        self.time_label.setObjectName("timeLabel")
        self.time_label.setAlignment(Qt.AlignCenter)
        self.time_label.setStyleSheet("font-size: 22px; font-weight: bold; background-color: rgb(18,18,18); color: rgb(255,255,255);")
        layout.addWidget(self.time_label)

        # Control buttons
        ctrl_layout = QHBoxLayout()
        start_btn = QPushButton("▶")
        start_btn.setFixedWidth(20)
        start_btn.setStyleSheet("font-size: 10px; font-weight: bold;")
        start_btn.clicked.connect(self.start_pomodoro)
        ctrl_layout.addWidget(start_btn)

        stop_btn = QPushButton("■")
        stop_btn.setFixedWidth(20)
        stop_btn.clicked.connect(self.stop_pomodoro)
        stop_btn.setStyleSheet("font-size: 10px; font-weight: bold;")
        ctrl_layout.addWidget(stop_btn)

        effects_btn = QPushButton("⬤")
        effects_btn.setFixedWidth(20)
        effects_btn.clicked.connect(self.open_effects)
        effects_btn.setStyleSheet("font-size: 10px; font-weight: bold;")
        ctrl_layout.addWidget(effects_btn)

        layout.addLayout(ctrl_layout)

        self.setCentralWidget(central)

    def open_effects(self):
        dlg = EffectsDialog(self)
        if dlg.exec():  # OK pressed
            self.break_flash_enabled = dlg.flash_checkbox.isChecked()
            effect = dlg.selected_effect()
            if effect:
                # Chnage the effect colour to the current color
                r = self.current_color[0]
                g = self.current_color[1]
                b = self.current_color[2]

                command = f"EFFECT_COLOR:{r},{g},{b}"
                self.serial.send(command)
                # Send the effect command
                if effect == "SENSOR_MODE":
                    command = f"SENSOR_MODE"
                elif effect == "INTENSITY":
                    command = f"INTENSITY:{(r + g + b) / 3}"
                else:
                    command = f"EFFECT:{effect}"
                return self.serial.send(command)


    def update_time(self, v):
        setattr(self, "focus_minutes", v)
        if not self.is_running:  
            self.time_label.setText(f"{self.focus_minutes}:00")

    def closeEvent(self, event):
        # Save settings when the app closes
        self.save_settings()
        super().closeEvent(event)

    def save_settings(self):
        settings = QSettings("MyCompany", "LED Pomodoro")   # (Organization, Application)
        settings.clear()  # Removes all keys and values
        settings.sync()   # Force writing the changes to disk
        settings.remove("colors")   # Deletes only the "colorArray" key
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())
        settings.setValue("pos", self.pos())
        settings.setValue("size", self.size())
        # Make the colors array flat for storage 
        flat = [component for color in self.colors for component in color]
        settings.setValue("colors", flat)
        settings.setValue("f_mins", self.focus_minutes)
        settings.setValue("b_mins", self.break_minutes)
        settings.setValue("break_flash_enabled", self.break_flash_enabled)
        settings.sync()

    # ---- Show close only near top ----
    def mouseMoveEvent(self, event):
        if event.position().y() < 20:  # top edge
            self.close_btn.show()
        else:
            self.close_btn.hide()
            self.resize(self.window_width, self.window_height) 

        # drag
        if self.drag_pos is not None and event.buttons() & Qt.LeftButton:
            delta = event.globalPosition().toPoint() - self.drag_pos
            self.move(self.pos() + delta)
            self.drag_pos = event.globalPosition().toPoint()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self.drag_pos = None

    # ---- Toggle connection ----
    def toggle_connection(self):
        # Update the port list in case a new device was plugged in
        self.port_combo.clear()
        # self.serial.get_ports()
        self.port_combo.addItems(self.serial.get_ports() or ["No ports"])
        if not self.serial.is_connected:
            port = self.port_combo.currentText()
            if port != "No ports" and self.serial.connect(port):
                self.status_label.setText("Connected")
                self.connect_btn.setText("⏹")
        else:
            self.serial.disconnect()
            self.status_label.setText("Disconnected")
            self.connect_btn.setText("⏺")

    # ---- Custom colour send ----
    def send_rgb_color(self, r: int, g: int, b: int) -> bool:
        """Send RGB color command to the device"""
        command = f"RGB:{r},{g},{b}"
        self.current_color = [r,g,b]
        return self.serial.send(command)

    def update_color_live(self, color: QColor):
        """Send live updates to LEDs while dragging in the wheel."""
        if not self.serial.is_connected:
            return
        if color.isValid():
            r, g, b = color.red(), color.green(), color.blue()
            self.send_rgb_color(r, g, b)

    def pick_color(self):
        if not self.serial.is_connected:
            return
        color = QColorDialog.getColor()
        if color.isValid():
            r, g, b, _ = color.getRgb()
            self.serial.send(f"COLOR {r} {g} {b}")
            # update button preview
            self.custom_btn.setStyleSheet(f"background-color: rgb({r},{g},{b});")

    # ---- Pomodoro ----
    def start_pomodoro(self):
        if not self.is_running:
            self.is_running = True
            self.is_break = False
            self.time_left = self.focus_minutes * 60
            self.timer.start(1000)
            index = 0
            self.send_rgb_color(self.colors[index][0], self.colors[index][1], self.colors[index][2])
            self.status_label.setText("Focus")
            self.time_label.setStyleSheet("font-size: 22px; font-weight: bold; background-color: rgb(18,18,18); color: rgb(255,255,255);")

    def stop_pomodoro(self):
        self.is_running = False
        self.timer.stop()
        self.serial.send("OFF")
        self.status_label.setText("Stopped")
        self.time_label.setText(f"{self.focus_minutes:02d}:00")
        self.time_label.setStyleSheet("font-size: 22px; font-weight: bold; background-color: rgb(18,18,18); color: rgb(255,255,255);")

    def tick(self):
        if not self.is_running:
            return
        self.time_left -= 1
        mins, secs = divmod(self.time_left, 60)
        self.time_label.setText(f"{mins:02d}:{secs:02d}")

        if self.is_break:
            index = 1
            if self.break_flash_enabled:
                if self._state:
                    self.send_rgb_color(self.colors[index][0], self.colors[index][1], self.colors[index][2])
                    self.time_label.setStyleSheet(f"font-size: 22px; font-weight: bold; background-color: rgb({self.colors[index][0]},{self.colors[index][1]},{self.colors[index][2]}); color: rgb(255,255,255);")
                else:
                    self.serial.send("OFF")
                    self.time_label.setStyleSheet("font-size: 22px; font-weight: bold; background-color: rgb(18,18,18); color: rgb(255,255,255);")
                self._state = not self._state
            else:
                self.send_rgb_color(self.colors[index][0], self.colors[index][1], self.colors[index][2])
                self.time_label.setStyleSheet(f"font-size: 22px; font-weight: bold; background-color: rgb({self.colors[index][0]},{self.colors[index][1]},{self.colors[index][2]}); color: rgb(255,255,255);")

        if self.time_left <= 0:
            if self.is_break:
                self.is_break = False
                self.time_left = self.focus_minutes * 60
                index = 0
                self.send_rgb_color(self.colors[index][0], self.colors[index][1], self.colors[index][2])
                self.status_label.setText("Focus")
                self.time_label.setStyleSheet("font-size: 22px; font-weight: bold; background-color: rgb(18,18,18); color: rgb(255,255,255);")
            else:
                self.is_break = True
                self.time_left = self.break_minutes * 60
                index = 1
                self.send_rgb_color(self.colors[index][0], self.colors[index][1], self.colors[index][2])
                self.status_label.setText("Break")
                self.time_label.setStyleSheet("font-size: 22px; font-weight: bold; background-color: rgb(18,18,18); color: rgb(255,255,255);")
                self._state = True

def main():
    app = QApplication(sys.argv)

    app.setWindowIcon(QIcon("icon.png"))
    # Get the primary screen object
    win = LightPomodoroApp()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()