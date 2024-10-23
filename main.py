import sys
from PyQt6.QtCore import Qt, QPoint, QPointF
from PyQt6.QtGui import QPainter, QPen, QPixmap, QWheelEvent
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea, QSplitter

class DrawingCanvas(QWidget):
    def __init__(self):
        super().__init__()
        self.setMouseTracking(True)
        self.lines = []  # Store the lines as tuples of points (start, end)
        self.current_line = None  # Currently drawing line
        self.scale_factor = 1.0  # For zooming
        self.pan_active = False  # Track whether panning is active
        self.last_pan_point = QPoint(0, 0)  # Last point where middle mouse button was pressed
        self.offset = QPoint(0, 0)  # Canvas offset for translation (panning)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Adjust the starting point according to the scale factor
            scaled_pos = event.pos() / self.scale_factor
            self.current_line = (scaled_pos - self.offset, scaled_pos - self.offset)  # Start a new line
        elif event.button() == Qt.MouseButton.MiddleButton:
            self.pan_active = True
            self.last_pan_point = event.pos()  # Start tracking the mouse position for panning

    def mouseMoveEvent(self, event):
        if self.current_line:
            # Adjust the current line endpoint according to the scale factor
            scaled_pos = event.pos() / self.scale_factor
            self.current_line = (self.current_line[0], scaled_pos - self.offset)
            self.update()  # Trigger a repaint
        elif self.pan_active:
            # Calculate the difference in mouse movement for panning
            delta = (event.pos() - self.last_pan_point) / self.scale_factor
            self.offset += delta  # Update the canvas offset
            self.last_pan_point = event.pos()  # Update the last pan position
            self.update()  # Repaint the canvas with the new offset


    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.current_line:
            # Save the current line to the list of lines (accounting for offset)
            self.lines.append((self.current_line[0], self.current_line[1]))
            self.current_line = None
            self.update()  # Trigger a repaint
        elif event.button() == Qt.MouseButton.MiddleButton:
            self.pan_active = False  # Stop panning when middle button is released

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.scale(self.scale_factor, self.scale_factor)  # Apply zooming
        painter.translate(self.offset)  # Apply translation (panning)

        # Set the background to white
        painter.fillRect(self.rect(), Qt.GlobalColor.white)

        pen = QPen(Qt.GlobalColor.black, 2, Qt.PenStyle.SolidLine)
        painter.setPen(pen)

        # Draw all the saved lines (accounting for offset)
        for line in self.lines:
            painter.drawLine(line[0], line[1])

        # Draw the currently drawn line (if any)
        if self.current_line:
            painter.drawLine(self.current_line[0], self.current_line[1])

    def wheelEvent(self, event: QWheelEvent):
        # Zoom in/out based on scroll direction
        zoom_in_factor = 1.25
        zoom_out_factor = 1 / zoom_in_factor
        
        # Get the position of the mouse relative to the widget and convert to QPoint
        mouse_pos = event.position() / self.scale_factor  # QPointF
        mouse_pos = QPoint(int(mouse_pos.x()), int(mouse_pos.y()))  # Convert to QPoint
        
        # Determine the zoom factor
        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor
        
        # Update the scale factor
        old_scale_factor = self.scale_factor
        self.scale_factor *= zoom_factor
        
        # Calculate the new offset to ensure the zoom origin is at the mouse cursor
        self.offset = (self.offset + mouse_pos) - (mouse_pos * zoom_factor)
        
        # Repaint the widget with the new scale and offset
        self.update()


    def export_canvas(self, filename='canvas.png'):
        # Create a QPixmap with the same size as the widget
        pixmap = QPixmap(self.size())
        pixmap.fill(Qt.GlobalColor.white)  # Fill with white background

        # Render the widget onto the QPixmap
        painter = QPainter(pixmap)
        self.render(painter)
        painter.end()

        # Save the QPixmap as a PNG file
        pixmap.save(filename)
        print(f'Canvas exported as {filename}')

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Ablevas 0.1')
        self.setGeometry(100, 100, 1000, 650)

        # Main layout
        main_layout = QVBoxLayout(self)

        # Create a vertical QSplitter for the main window
        main_splitter = QSplitter(Qt.Orientation.Vertical)

        # Create a QSplitter for the top section (Horizontal Splitter)
        top_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_label = QLabel("Tools Panel")
        left_label.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        left_layout.addWidget(left_label)
        left_panel.setMinimumWidth(120)  # Allow a minimum width
        top_splitter.addWidget(left_panel)

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
        export_button = QPushButton('Export as PNG')
        export_button.clicked.connect(self.export_canvas)
        right_layout.addWidget(export_button)
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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
