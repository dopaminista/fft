import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel
from block import calculate_fft

class FFTApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        self.setWindowTitle('FFT Calculation')
        self.setGeometry(100, 100, 300, 200)

        self.status_label = QLabel('Status: Ready', self)

        self.start_button = QPushButton('Start FFT Calculation', self)
        self.start_button.clicked.connect(self.start_fft)

        layout = QVBoxLayout()
        layout.addWidget(self.status_label)
        layout.addWidget(self.start_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def start_fft(self):
        self.status_label.setText('Status: Running FFT...')
        status = calculate_fft()
        if isinstance(status, dict) and all(code == 0 for code in status.values()):
            self.status_label.setText('Status: FFT Completed Successfully')
        else:
            self.status_label.setText(f'Status: Error - {status}')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = FFTApp()
    ex.show()
    sys.exit(app.exec())
