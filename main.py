import sys
from PyQt6.QtCore import Qt, QPoint, QPointF
from PyQt6.QtGui import QPainter, QPen, QPixmap, QWheelEvent, QPainterPath, QTransform
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea, QSplitter, QTabWidget, QToolButton, QFileDialog

from src.canvas import DrawingCanvas

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Ablevas 0.1')
        self.setGeometry(100, 100, 1000, 650)

        # Main layout
        main_layout = QHBoxLayout(self)  # Changed to horizontal layout to accommodate ribbon on the left

        # Create a vertical QSplitter for the main window
        main_splitter = QSplitter(Qt.Orientation.Vertical)

        # Create a QSplitter for the top section (Horizontal Splitter)
        top_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: Ribbon control instead of tools panel
        ribbon_tabs = QTabWidget()
        ribbon_tabs.setMinimumWidth(120)  # Set a minimum width for the vertical ribbon
        ribbon_tabs.setTabPosition(QTabWidget.TabPosition.West)  # Place tabs vertically on the left
        self.add_ribbon_tabs(ribbon_tabs)
        top_splitter.addWidget(ribbon_tabs)

        # Center: Canvas for drawing
        self.canvas = DrawingCanvas()
        top_splitter.addWidget(self.canvas)

        # Right panel
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_label = QLabel("Palette / Layers")
        right_label.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        right_layout.addWidget(right_label)

        # Export button
        right_panel.setMinimumWidth(120)  # Allow a minimum width
        top_splitter.addWidget(right_panel)

        # Set resize proportions (optional) to give initial sizes
        top_splitter.setSizes([240, 520, 240])

        # Add the top section to the vertical main splitter
        main_splitter.addWidget(top_splitter)

        # Bottom: Add a horizontal scroll area using a splitter
        self.add_bottom_scroll_panel(main_splitter)

        # Set initial sizes for the top and bottom sections
        main_splitter.setSizes([450, 200])  # Adjust the proportions between top and bottom

        # Add the main splitter to the layout
        main_layout.addWidget(main_splitter)

        self.setLayout(main_layout)

    def mode_1(self):
        self.canvas.mode = 1

    def mode_2(self):
        self.canvas.mode = 2

    def add_ribbon_tabs(self, ribbon_tabs):
        # File Tab
        file_tab = QWidget()
        file_layout = QVBoxLayout(file_tab)  # Use vertical layout to stack buttons

        open_button = QToolButton()
        open_button.setText("Open")
        open_button.clicked.connect(self.open_file)
        file_layout.addWidget(open_button)

        save_button = QToolButton()
        save_button.setText("Save")
        save_button.clicked.connect(self.save_file)
        file_layout.addWidget(save_button)

        ribbon_tabs.addTab(file_tab, "File")

        # Pencil Tab
        pencil_tab = QWidget()
        pencil_layout = QVBoxLayout(pencil_tab)  # Use vertical layout to stack buttons

        pencil_button = QToolButton()
        pencil_button.setText("Pencil")
        # Connect to a placeholder function (you can implement a pencil tool logic later)
        pencil_layout.addWidget(pencil_button)

        ribbon_tabs.addTab(pencil_tab, "Pencil")

        # Pen Tab
        pen_tab = QWidget()
        pen_layout = QVBoxLayout(pen_tab)  # Use vertical layout to stack buttons

        mode_1_button = QToolButton()
        mode_1_button.setText("Draw Mode")
        mode_1_button.clicked.connect(self.mode_1)

        mode_2_button = QToolButton()
        mode_2_button.setText("Adjust Mode")
        mode_2_button.clicked.connect(self.mode_2)

        # Connect to a placeholder function (you can implement a pen tool logic later)
        pen_layout.addWidget(mode_1_button)
        pen_layout.addWidget(mode_2_button)

        ribbon_tabs.addTab(pen_tab, "Pen")

    def add_bottom_scroll_panel(self, splitter):
        # Create a QSplitter for the bottom section
        bottom_splitter = QSplitter(Qt.Orientation.Vertical)

        # Horizontal scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        # Create a widget to hold the horizontal content
        bottom_widget = QWidget()
        scroll_layout = QHBoxLayout(bottom_widget)

        # Add some placeholder buttons to demonstrate the scrollable area
        for i in range(1, 21):  # 20 buttons to demonstrate scrolling
            button = QPushButton(f'Item {i}')
            scroll_layout.addWidget(button)

        scroll_area.setWidget(bottom_widget)
        bottom_splitter.addWidget(scroll_area)

        # Set initial and minimum height for the bottom panel
        bottom_splitter.setSizes([240])  # Set initial height to 240
        bottom_splitter.setMinimumHeight(240)  # Minimum height of 240

        # Add the bottom section to the main splitter
        splitter.addWidget(bottom_splitter)

    def export_canvas(self):
        # Call the export function in the canvas widget
        self.canvas.export_canvas()

    def open_file(self):
        # Open file dialog for selecting a file
        #file_name, _ = QFileDialog.getOpenFileName(self, "Open File", "", "Image Files (*.png *.jpg *.bmp);;All Files (*)")
        #if file_name:
            #print(f"Opening file: {file_name}")
            # Load the file into the canvas (implementation needed)
        self.canvas.loadFromFile()

    def save_file(self):
        # Open file dialog for saving a file
        #file_name, _ = QFileDialog.getSaveFileName(self, "Save File", "", "PNG Files (*.png);;All Files (*)")
        #if file_name:
            #print(f"Saving file: {file_name}")
            # Save the canvas as a file (implementation needed)
        self.canvas.saveToFile()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
