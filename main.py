import sys
import socket
import requests
import speedtest
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QPushButton, QTextEdit, QLabel)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont, QPalette, QColor
import threading
import time


class NetworkWarmerThread(QThread):
    log_signal = pyqtSignal(str)
    complete_signal = pyqtSignal()
    speed_signal = pyqtSignal(float, float)
    
    def __init__(self):
        super().__init__()
        self.running = True
        
    def stop(self):
        self.running = False
        
    def run(self):
        try:
            self.log_signal.emit("=== Network Warming Started ===\n")
            
            if not self.running:
                return
            self.log_signal.emit("[1/3] HTTP Warm-up...")
            self.http_warmup()
            
            if not self.running:
                return
            self.log_signal.emit("[2/3] UDP Connection Tests...")
            self.udp_warmup()
            
            if not self.running:
                return
            self.log_signal.emit("[3/3] M-Lab Speed Test...")
            self.speed_test()
            
            if self.running:
                self.log_signal.emit("\n=== Warming Complete ===")
                self.log_signal.emit("Network connection optimized.\n")
            else:
                self.log_signal.emit("\n=== Warming Stopped ===\n")
                
        except Exception as e:
            self.log_signal.emit(f"\nError: {str(e)}\n")
        finally:
            self.complete_signal.emit()
    
    def http_warmup(self):
        targets = [
            "https://www.google.com",
            "https://www.cloudflare.com",
            "https://www.amazon.com",
            "https://1.1.1.1",
            "https://8.8.8.8"
        ]
        
        success_count = 0
        for target in targets:
            if not self.running:
                break
            try:
                response = requests.get(target, timeout=5)
                if response.status_code == 200:
                    success_count += 1
                time.sleep(0.1)
            except Exception:
                pass
        
        self.log_signal.emit(f"  HTTP: {success_count}/{len(targets)} successful\n")
    
    def udp_warmup(self):
        dns_servers = [
            ("8.8.8.8", 53),      # Google DNS
            ("8.8.4.4", 53),      # Google DNS
            ("1.1.1.1", 53),      # Cloudflare DNS
            ("1.0.0.1", 53),      # Cloudflare DNS
        ]
        
        success_count = 0
        for server, port in dns_servers:
            if not self.running:
                break
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.settimeout(2)
                sock.sendto(b'\x00\x00', (server, port))
                sock.close()
                success_count += 1
                time.sleep(0.1)
            except Exception:
                pass
        
        self.log_signal.emit(f"  UDP: {success_count}/{len(dns_servers)} successful\n")
    
    def speed_test(self):
        try:
            st = speedtest.Speedtest()
            
            if not self.running:
                return
            
            self.log_signal.emit("  Finding optimal server...")
            st.get_best_server()
            
            if not self.running:
                return
            
            self.log_signal.emit("  Testing download speed...")
            download_speed = st.download() / 1_000_000
            
            if not self.running:
                return
            
            self.log_signal.emit("  Testing upload speed...")
            upload_speed = st.upload() / 1_000_000
            
            self.log_signal.emit(f"  Download: {download_speed:.2f} Mbps")
            self.log_signal.emit(f"  Upload: {upload_speed:.2f} Mbps\n")
            
            self.speed_signal.emit(download_speed, upload_speed)
            
        except Exception as e:
            self.log_signal.emit(f"  Speed test failed: {str(e)}\n")


class NetworkWarmerGUI(QMainWindow):
    
    def __init__(self):
        super().__init__()
        self.worker_thread = None
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Network Warmer")
        self.setFixedSize(200, 400)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        title = QLabel("Network Warmer")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont("Segoe UI", 14, QFont.Weight.Bold)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Speed labels
        self.download_label = QLabel("Download: -- Mbps")
        self.download_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.download_label.setStyleSheet("""
            QLabel {
                color: #00D084;
                font-size: 11px;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.download_label)
        
        self.upload_label = QLabel("Upload: -- Mbps")
        self.upload_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.upload_label.setStyleSheet("""
            QLabel {
                color: #00D084;
                font-size: 11px;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.upload_label)
        
        self.start_btn = QPushButton("START")
        self.start_btn.setFixedHeight(50)
        self.start_btn.clicked.connect(self.start_warming)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #00D084;
                color: white;
                border: none;
                border-radius: 25px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #00B872;
            }
            QPushButton:pressed {
                background-color: #009960;
            }
            QPushButton:disabled {
                background-color: #5A5A5A;
            }
        """)
        layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("STOP")
        self.stop_btn.setFixedHeight(40)
        self.stop_btn.clicked.connect(self.stop_warming)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #E83E3E;
                color: white;
                border: none;
                border-radius: 20px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #D43333;
            }
            QPushButton:pressed {
                background-color: #C02828;
            }
            QPushButton:disabled {
                background-color: #5A5A5A;
            }
        """)
        layout.addWidget(self.stop_btn)
        
        # Log area
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setStyleSheet("""
            QTextEdit {
                background-color: #1E1E1E;
                color: #FFFFFF;
                border: none;
                border-radius: 5px;
                padding: 8px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 9px;
            }
        """)
        layout.addWidget(self.log_area)
        
        central_widget.setLayout(layout)
        
        # styling
        self.setStyleSheet("""
            QMainWindow {
                background-color: #141414;
            }
            QLabel {
                color: #FFFFFF;
            }
        """)
        
        self.log("Ready to warm network connection.")
    
    def log(self, message):
        self.log_area.append(message)
        self.log_area.verticalScrollBar().setValue(
            self.log_area.verticalScrollBar().maximum()
        )
    
    def start_warming(self):
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.log_area.clear()
        self.download_label.setText("Download: -- Mbps")
        self.upload_label.setText("Upload: -- Mbps")
        
        self.worker_thread = NetworkWarmerThread()
        self.worker_thread.log_signal.connect(self.log)
        self.worker_thread.complete_signal.connect(self.warming_complete)
        self.worker_thread.speed_signal.connect(self.update_speeds)
        self.worker_thread.start()
    
    def stop_warming(self):
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.stop()
            self.log("\nStopping warming process...")
    
    def warming_complete(self):
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
    
    def update_speeds(self, download, upload):
        self.download_label.setText(f"Download: {download:.2f} Mbps")
        self.upload_label.setText(f"Upload: {upload:.2f} Mbps")
    
    def closeEvent(self, event):
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.stop()
            self.worker_thread.wait()
        event.accept()


def main():
    app = QApplication(sys.argv)
    window = NetworkWarmerGUI()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
