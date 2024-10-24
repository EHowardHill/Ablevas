import sys
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtGui import QPainter, QPen, QMouseEvent, QPainterPath
from PyQt6.QtCore import Qt, QPointF

class DrawingCanvas(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Interactive Bezier Curve Editor")
        self.resize(800, 600)
        self.points = []
        self.sampled_points = []
        self.first_control_points = []
        self.second_control_points = []
        self.smoothed_path = None
        self.is_drawing = True
        self.selected_control_point_index = None
        self.selected_control_point_type = None
        self.scale_factor = 1.0  # For zooming
        self.pan_active = False  # Track whether panning is active
        self.last_pan_point = QPoint(0, 0)  # Last point where middle mouse button was pressed
        self.offset = QPoint(0, 0)  # Canvas offset for translation (panning)
        self.control_point_radius = 5
        self.sampling_interval = 10  # Adjust this value to change the frequency
        self.show()

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

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.is_drawing:
                self.points = []
                self.sampled_points = []
                self.first_control_points = []
                self.second_control_points = []
                self.smoothed_path = None
                self.points.append(event.position())
                self.update()
            else:
                cp_type, index = self.getControlPointAtPosition(event.position())
                if index is not None:
                    self.selected_control_point_type = cp_type
                    self.selected_control_point_index = index
        elif event.button() == Qt.MouseButton.RightButton and not self.is_drawing:
            self.is_drawing = True
            self.points = []
            self.sampled_points = []
            self.first_control_points = []
            self.second_control_points = []
            self.smoothed_path = None
            self.update()
        elif event.button() == Qt.MouseButton.MiddleButton:
            self.pan_active = True
            self.last_pan_point = event.pos()  # Start tracking the mouse position for panning

    def mouseMoveEvent(self, event):

        if self.pan_active:
            # Calculate the difference in mouse movement for panning
            delta = (event.pos() - self.last_pan_point) / self.scale_factor
            self.offset += delta  # Update the canvas offset
            self.last_pan_point = event.pos()  # Update the last pan position
            self.update()  # Repaint the canvas with the new offset

        elif self.is_drawing:
            self.points.append(event.position())
            self.update()
            
        elif self.selected_control_point_index is not None:
            if self.selected_control_point_type == 'first':
                self.first_control_points[self.selected_control_point_index] = event.position()
            elif self.selected_control_point_type == 'second':
                self.second_control_points[self.selected_control_point_index] = event.position()
            self.smoothed_path = self.createBezierPathFromControlPoints(self.sampled_points, self.first_control_points, self.second_control_points)
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.is_drawing:
                self.is_drawing = False
                # Down-sample the points
                sampled_points = self.points[::self.sampling_interval]
                # Ensure the last point is included
                if self.points[-1] != sampled_points[-1]:
                    sampled_points.append(self.points[-1])
                self.sampled_points = sampled_points
                # Compute control points using the sampled points
                self.first_control_points, self.second_control_points = self.getCurveControlPoints(self.sampled_points)
                self.smoothed_path = self.createBezierPathFromControlPoints(self.sampled_points, self.first_control_points, self.second_control_points)
                self.update()
            elif self.selected_control_point_index is not None:
                self.selected_control_point_index = None
                self.selected_control_point_type = None

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.fillRect(self.rect(), Qt.GlobalColor.white)

        pen = QPen(Qt.GlobalColor.black, 2)
        painter.setPen(pen)

        if self.is_drawing:
            path = QPainterPath()
            if self.points:
                path.moveTo(self.points[0])
                for point in self.points[1:]:
                    path.lineTo(point)
            painter.drawPath(path)
        elif self.smoothed_path:
            painter.drawPath(self.smoothed_path)

            pen = QPen(Qt.GlobalColor.red, 1, Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.setBrush(Qt.GlobalColor.blue)

            for i in range(len(self.first_control_points)):
                cp1 = self.first_control_points[i]
                cp2 = self.second_control_points[i]
                p0 = self.sampled_points[i]
                p1 = self.sampled_points[i + 1]

                painter.drawLine(p0, cp1)
                painter.drawLine(p1, cp2)

                painter.drawEllipse(cp1, self.control_point_radius, self.control_point_radius)
                painter.drawEllipse(cp2, self.control_point_radius, self.control_point_radius)

    def createBezierPathFromControlPoints(self, points, first_control_points, second_control_points):
        if len(points) < 2:
            return None

        path = QPainterPath()
        path.moveTo(points[0])

        for i in range(len(first_control_points)):
            cp1 = first_control_points[i]
            cp2 = second_control_points[i]
            p = points[i + 1]
            path.cubicTo(cp1, cp2, p)

        return path

    def getCurveControlPoints(self, knots):
        n = len(knots) - 1
        if n < 1:
            return None, None
        if n == 1:
            first_control_points = [QPointF((2 * knots[0].x() + knots[1].x()) / 3,
                                            (2 * knots[0].y() + knots[1].y()) / 3)]
            second_control_points = [QPointF(2 * first_control_points[0].x() - knots[0].x(),
                                             2 * first_control_points[0].y() - knots[0].y())]
            return first_control_points, second_control_points

        # Calculate first control points
        rhs_x = [0.0] * n
        rhs_y = [0.0] * n

        rhs_x[0] = knots[0].x() + 2 * knots[1].x()
        for i in range(1, n - 1):
            rhs_x[i] = 4 * knots[i].x() + 2 * knots[i + 1].x()
        rhs_x[n - 1] = (8 * knots[n - 1].x() + knots[n].x()) / 2.0

        rhs_y[0] = knots[0].y() + 2 * knots[1].y()
        for i in range(1, n - 1):
            rhs_y[i] = 4 * knots[i].y() + 2 * knots[i + 1].y()
        rhs_y[n - 1] = (8 * knots[n - 1].y() + knots[n].y()) / 2.0

        x = self.solveTridiagonalSystem(rhs_x)
        y = self.solveTridiagonalSystem(rhs_y)

        first_control_points = []
        second_control_points = []
        for i in range(n):
            first_cp = QPointF(x[i], y[i])
            first_control_points.append(first_cp)
            if i < n - 1:
                second_cp = QPointF(2 * knots[i + 1].x() - x[i + 1],
                                    2 * knots[i + 1].y() - y[i + 1])
            else:
                second_cp = QPointF((knots[n].x() + x[n - 1]) / 2.0,
                                    (knots[n].y() + y[n - 1]) / 2.0)
            second_control_points.append(second_cp)

        return first_control_points, second_control_points

    def solveTridiagonalSystem(self, rhs):
        n = len(rhs)
        x = [0.0] * n
        tmp = [0.0] * n
        b = 2.0
        x[0] = rhs[0] / b
        for i in range(1, n):
            tmp[i] = 1 / b
            b = (4.0 if i < n - 1 else 3.5) - tmp[i]
            x[i] = (rhs[i] - x[i - 1]) / b
        for i in range(n - 2, -1, -1):
            x[i] -= tmp[i + 1] * x[i + 1]
        return x

    def getControlPointAtPosition(self, pos):
        for i, cp in enumerate(self.first_control_points):
            if (cp - pos).manhattanLength() <= self.control_point_radius * 2:
                return ('first', i)
        for i, cp in enumerate(self.second_control_points):
            if (cp - pos).manhattanLength() <= self.control_point_radius * 2:
                return ('second', i)
        return (None, None)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyCanvas()
    sys.exit(app.exec())
