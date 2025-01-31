import sys
import psutil
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QLineEdit, QHBoxLayout, QWidget, QMessageBox, QProgressBar
)
import pyqtgraph as pg


class TaskManagerDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Advanced Task Manager")
        self.setGeometry(100, 100, 1200, 800)
        self.setStyleSheet("background-color: #1e1e2e; color: white;")

        # Main Layout
        main_layout = QVBoxLayout()

        # Header Section
        header = QLabel("Advanced Task Manager Dashboard")
        header.setFont(QFont("Arial", 24, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("color: #00d1ff; margin-bottom: 20px;")
        main_layout.addWidget(header)

        # System Stats Section
        stats_layout = QHBoxLayout()
        self.cpu_label = QLabel("CPU Usage: 0%")
        self.memory_label = QLabel("Memory Usage: 0%")
        self.disk_label = QLabel("Disk Usage: 0%")
        for label in [self.cpu_label, self.memory_label, self.disk_label]:
            label.setFont(QFont("Arial", 14))
            label.setStyleSheet("color: #ffffff; margin: 0 20px;")
            stats_layout.addWidget(label)
        main_layout.addLayout(stats_layout)

        # Search Bar
        search_layout = QHBoxLayout()
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search processes...")
        self.search_bar.setStyleSheet(
            "background-color: #2e2e3e; color: white; padding: 10px; border: 1px solid #00d1ff; border-radius: 5px;"
        )
        search_button = QPushButton("Search")
        search_button.setStyleSheet(
            "background-color: #00d1ff; color: black; font-weight: bold; padding: 10px 20px; border-radius: 5px;"
        )
        search_button.clicked.connect(self.update_process_table)
        search_layout.addWidget(self.search_bar)
        search_layout.addWidget(search_button)
        main_layout.addLayout(search_layout)

        # Process Table
        self.process_table = QTableWidget()
        self.process_table.setColumnCount(5)
        self.process_table.setHorizontalHeaderLabels(["PID", "Name", "Status", "CPU (%)", "Memory (%)"])
        self.process_table.horizontalHeader().setStretchLastSection(True)
        self.process_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.process_table.setStyleSheet(
            "QTableWidget { background-color: #2e2e3e; color: white; gridline-color: #444; }"
            "QHeaderView::section { background-color: #44475a; color: #00d1ff; border: none; }"
            "QTableWidget::item { padding: 10px; }"
        )
        main_layout.addWidget(self.process_table)

        # CPU and Memory Graph
        self.graph_widget = pg.PlotWidget()
        self.graph_widget.setBackground("#1e1e2e")
        self.graph_widget.setTitle("System Usage", color="#ffffff", size="16pt")
        self.graph_widget.addLegend()
        self.graph_widget.showGrid(x=True, y=True, alpha=0.3)
        self.cpu_plot = self.graph_widget.plot(
            pen=pg.mkPen(color="#00d1ff", width=2), name="CPU Usage (%)"
        )
        self.memory_plot = self.graph_widget.plot(
            pen=pg.mkPen(color="#ff6f91", width=2), name="Memory Usage (%)"
        )
        main_layout.addWidget(self.graph_widget)

        # Footer Section
        footer_layout = QHBoxLayout()
        refresh_button = QPushButton("Refresh")
        refresh_button.setStyleSheet(
            "background-color: #00d1ff; color: black; font-weight: bold; padding: 10px 20px; border-radius: 5px;"
        )
        refresh_button.clicked.connect(self.update_process_table)
        terminate_button = QPushButton("Terminate Process")
        terminate_button.setStyleSheet(
            "background-color: #ff6f91; color: black; font-weight: bold; padding: 10px 20px; border-radius: 5px;"
        )
        terminate_button.clicked.connect(self.terminate_selected_process)
        footer_layout.addWidget(refresh_button)
        footer_layout.addWidget(terminate_button)
        main_layout.addLayout(footer_layout)

        # Set Central Widget
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # Timer for Real-Time Updates
        self.cpu_data, self.memory_data = [], []
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_dashboard)
        self.timer.start(1000)  # Update every second

        # Initial Table Update
        self.update_process_table()

    def get_processes(self):
        filter_text = self.search_bar.text().lower()
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
            try:
                info = proc.info
                if filter_text in info['name'].lower():
                    processes.append(info)
            except psutil.AccessDenied:
                processes.append({'pid': proc.pid, 'name': "Access Denied", 'cpu_percent': 0.0, 'memory_percent': 0.0, 'status': "N/A"})
            except (psutil.NoSuchProcess, psutil.ZombieProcess):
                pass
        return processes

    def update_process_table(self):
        processes = self.get_processes()
        self.process_table.setRowCount(len(processes))

        for row, proc in enumerate(processes):
            pid_item = QTableWidgetItem(str(proc['pid']))
            name_item = QTableWidgetItem(proc['name'])
            status_item = QTableWidgetItem(proc.get('status', "N/A"))
            cpu_item = QTableWidgetItem(f"{proc['cpu_percent']:.1f}")
            memory_item = QTableWidgetItem(f"{proc['memory_percent']:.1f}")

            # Highlight rows with high CPU or memory usage
            if proc['cpu_percent'] > 50 or proc['memory_percent'] > 50:
                for item in [pid_item, name_item, status_item, cpu_item, memory_item]:
                    item.setForeground(QColor("#ff6f91"))

            self.process_table.setItem(row, 0, pid_item)
            self.process_table.setItem(row, 1, name_item)
            self.process_table.setItem(row, 2, status_item)
            self.process_table.setItem(row, 3, cpu_item)
            self.process_table.setItem(row, 4, memory_item)

    def update_dashboard(self):
        # Update system stats
        self.cpu_label.setText(f"CPU Usage: {psutil.cpu_percent()}%")
        self.memory_label.setText(f"Memory Usage: {psutil.virtual_memory().percent}%")
        self.disk_label.setText(f"Disk Usage: {psutil.disk_usage('/').percent}%")

        # Update real-time graphs
        self.cpu_data.append(psutil.cpu_percent())
        self.memory_data.append(psutil.virtual_memory().percent)

        if len(self.cpu_data) > 20:  # Keep the last 20 data points
            self.cpu_data.pop(0)
            self.memory_data.pop(0)

        self.cpu_plot.setData(self.cpu_data)
        self.memory_plot.setData(self.memory_data)

    def terminate_selected_process(self):
        selected_row = self.process_table.currentRow()
        if selected_row >= 0:
            pid = int(self.process_table.item(selected_row, 0).text())
            confirm = QMessageBox.question(self, "Confirm", f"Terminate process {pid}?", QMessageBox.Yes | QMessageBox.No)
            if confirm == QMessageBox.Yes:
                try:
                    psutil.Process(pid).terminate()
                    self.update_process_table()
                except psutil.AccessDenied:
                    QMessageBox.warning(self, "Error", "Access Denied")
                except psutil.NoSuchProcess:
                    QMessageBox.warning(self, "Error", "Process no longer exists")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TaskManagerDashboard()
    window.show()
    sys.exit(app.exec_())
