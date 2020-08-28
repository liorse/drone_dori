from PyQt5.QtWidgets import QApplication, QMainWindow, \
    QPushButton, QVBoxLayout, QWidget

def btn_enable_opc_evt():
    print("sent enable event to OPC")

def btn_disable_opc_evt():
    print("sent disable event to OPC")

app = QApplication([])
win = QMainWindow()
central_widget = QWidget()
btn_enable_opc = QPushButton('Enable OPC', central_widget)
btn_disable_opc = QPushButton('Disable OPC', central_widget)

btn_enable_opc.clicked.connect(btn_enable_opc_evt)
btn_disable_opc.clicked.connect(btn_disable_opc_evt)

layout = QVBoxLayout(central_widget)
layout.addWidget(btn_enable_opc)
layout.addWidget(btn_disable_opc)
win.setCentralWidget(central_widget)
win.show()
app.exit(app.exec_())
