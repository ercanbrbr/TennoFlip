from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QButtonGroup
from PySide6.QtCore import Signal

class PriceToggle(QWidget):
    toggled = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.btn_avg = QPushButton("Average")
        self.btn_low = QPushButton("Lowest In-game Price")
        
        self.btn_avg.setCheckable(True)
        self.btn_low.setCheckable(True)
        self.btn_avg.setChecked(True)
        
        self.btn_avg.setObjectName("toggle_left")
        self.btn_low.setObjectName("toggle_right")
        
        self.group = QButtonGroup(self)
        self.group.addButton(self.btn_avg)
        self.group.addButton(self.btn_low)
        self.group.setExclusive(True)
        
        layout.addWidget(self.btn_avg)
        layout.addWidget(self.btn_low)
        
        self.btn_avg.clicked.connect(lambda: self.toggled.emit(False))
        self.btn_low.clicked.connect(lambda: self.toggled.emit(True))
    
    def isChecked(self):
        return self.btn_low.isChecked()
    
    def setChecked(self, lowest):
        if lowest:
            self.btn_low.setChecked(True)
        else:
            self.btn_avg.setChecked(True)
