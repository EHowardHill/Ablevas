import json
from PyQt6.QtCore import Qt, QPoint, QPointF, QRectF
from PyQt6.QtGui import QPainter, QPen, QPainterPath, QTransform
from PyQt6.QtWidgets import QWidget, QMessageBox

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
        self.mode = 1
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

    def mode_1(self):
        self.mode = 1
    
    def mode_2(self):
        self.mode = 2

    def getCurrentTransform(self):
        transform = QTransform()
        transform.translate(self.offset.x(), self.offset.y())
        transform.scale(self.scale_factor, self.scale_factor)
        return transform

    def getInverseTransform(self):
        transform = self.getCurrentTransform()
        inverse, invertible = transform.inverted()
        if invertible:
            return inverse
        else:
            return None

    def mapToScene(self, pos):
        inverse_transform = self.getInverseTransform()
        if inverse_transform:
            return inverse_transform.map(pos)
        else:
            return pos

    def wheelEvent(self, event):
        zoom_in_factor = 1.25
        zoom_out_factor = 1 / zoom_in_factor

        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor

        # Get the center of the widget in widget coordinates
        center_widget = self.rect().center()

        # Calculate the new scale factor
        new_scale_factor = self.scale_factor * zoom_factor

        # Adjust the offset to keep the scene centered
        self.offset = QPointF(self.offset) + (1 - zoom_factor) * (QPointF(center_widget) - QPointF(self.offset))

        # Update the scale factor
        self.scale_factor = new_scale_factor

        self.update()

    def mousePressEvent(self, event):
        pos = event.position()

        if event.button() == Qt.MouseButton.LeftButton:
            if self.mode == 1:  # Drawing mode
                self.points = []
                self.sampled_points = []
                self.first_control_points = []
                self.second_control_points = []
                self.smoothed_path = None
                self.points.append(pos)
                self.update()
            elif self.mode == 2:  # Adjustment mode
                cp_type, index = self.getControlPointAtPosition(pos)
                if index is not None:
                    self.selected_control_point_type = cp_type
                    self.selected_control_point_index = index
        elif event.button() == Qt.MouseButton.MiddleButton:
            self.pan_active = True
            self.last_pan_point = event.pos()  # Start tracking the mouse position for panning

    def mouseMoveEvent(self, event):
        if self.pan_active:
            # Calculate the delta without dividing by scale_factor
            delta = event.pos() - self.last_pan_point

            # Update the offset by subtracting the delta
            self.offset = QPointF(self.offset) + QPointF(delta)

            # Update the last pan point to the current position
            self.last_pan_point = event.pos()

            # Trigger a repaint
            self.update()
        else:
            pos = self.mapToScene(event.position())  # Map to scene coordinates

            if self.mode == 1:  # Drawing mode
                self.points.append(pos)
                self.update()
            elif self.mode == 2 and self.selected_control_point_index is not None:
                # Adjustment mode: move the selected control point
                if self.selected_control_point_type == 'first':
                    self.first_control_points[self.selected_control_point_index] = pos
                elif self.selected_control_point_type == 'second':
                    self.second_control_points[self.selected_control_point_index] = pos
                self.smoothed_path = self.createBezierPathFromControlPoints(
                    self.sampled_points, self.first_control_points, self.second_control_points
                )
                self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.mode == 1:  # Drawing mode
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
            elif self.mode == 2 and self.selected_control_point_index is not None:
                self.selected_control_point_index = None
                self.selected_control_point_type = None
        elif event.button() == Qt.MouseButton.MiddleButton:
            self.pan_active = False

    def paintEvent(self, event):
        print(self.mode)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), Qt.GlobalColor.white)

        # Apply scaling and translation
        painter.save()
        painter.translate(self.offset)
        painter.scale(self.scale_factor, self.scale_factor)

        painter.fillRect(self.rect(), Qt.GlobalColor.white)

        pen = QPen(Qt.GlobalColor.black, 2)
        painter.setPen(pen)

        if self.mode == 1:  # Drawing mode
            path = QPainterPath()
            if self.points:
                path.moveTo(self.points[0])
                for point in self.points[1:]:
                    path.lineTo(point)
            painter.drawPath(path)

        elif self.mode == 2 and self.smoothed_path:
            painter.drawPath(self.smoothed_path)

            pen = QPen(Qt.GlobalColor.red, 1, Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.setBrush(Qt.GlobalColor.white)

            for i in range(len(self.first_control_points)):
                cp1 = self.first_control_points[i]
                cp2 = self.second_control_points[i]
                p0 = self.sampled_points[i]
                p1 = self.sampled_points[i + 1]

                painter.drawLine(p0, cp1)
                painter.drawLine(p1, cp2)

                painter.drawEllipse(cp1, self.control_point_radius, self.control_point_radius)
                painter.drawEllipse(cp2, self.control_point_radius, self.control_point_radius)

        # Draw the Hollow Red Rectangle (unchanged)
        pen = QPen(Qt.GlobalColor.red, 5)  # 5 pixels thick
        pen.setStyle(Qt.PenStyle.SolidLine)
        painter.setPen(pen)
        painter.setBrush(Qt.GlobalColor.transparent)  # Hollow rectangle

        # Define the rectangle from (-960, -540) to (960, 540)
        rect = QRectF(-960, -540, 1920, 1080)
        painter.drawRect(rect)

        painter.restore()

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
        pos = self.mapToScene(pos)

        if self.first_control_points:
            for i, cp in enumerate(self.first_control_points):
                if (cp - pos).manhattanLength() <= self.control_point_radius * 2:
                    return ('first', i)
            for i, cp in enumerate(self.second_control_points):
                if (cp - pos).manhattanLength() <= self.control_point_radius * 2:
                    return ('second', i)
        return (None, None)

    def saveToFile(self):
        # Prepare data to be saved
        data = {
            "points": [{"x": p.x(), "y": p.y()} for p in self.points],
            "sampled_points": [{"x": p.x(), "y": p.y()} for p in self.sampled_points],
            "first_control_points": [{"x": p.x(), "y": p.y()} for p in self.first_control_points],
            "second_control_points": [{"x": p.x(), "y": p.y()} for p in self.second_control_points],
            "scale_factor": self.scale_factor,
            "offset": {"x": self.offset.x(), "y": self.offset.y()},
            "is_drawing": self.is_drawing
        }

        try:
            with open("data.json", "w") as f:
                json.dump(data, f, indent=4)
            QMessageBox.information(self, "Save Successful", "Bezier curve data has been saved to data.json.")
        except Exception as e:
            QMessageBox.critical(self, "Save Failed", f"An error occurred while saving:\n{e}")

    def loadFromFile(self):
        try:
            with open("data.json", "r") as f:
                data = json.load(f)

            # Load points
            self.points = [QPointF(p["x"], p["y"]) for p in data.get("points", [])]
            self.sampled_points = [QPointF(p["x"], p["y"]) for p in data.get("sampled_points", [])]
            self.first_control_points = [QPointF(p["x"], p["y"]) for p in data.get("first_control_points", [])]
            self.second_control_points = [QPointF(p["x"], p["y"]) for p in data.get("second_control_points", [])]
            self.scale_factor = data.get("scale_factor", 1.0)
            offset_data = data.get("offset", {"x": 0, "y": 0})
            self.offset = QPointF(offset_data.get("x", 0), offset_data.get("y", 0))
            self.is_drawing = data.get("is_drawing", True)

            # Recreate the smoothed path
            if not self.is_drawing and self.sampled_points and self.first_control_points and self.second_control_points:
                self.smoothed_path = self.createBezierPathFromControlPoints(
                    self.sampled_points, self.first_control_points, self.second_control_points
                )
            else:
                self.smoothed_path = None

            self.update()
            QMessageBox.information(self, "Load Successful", "Bezier curve data has been loaded from data.json.")
        except FileNotFoundError:
            QMessageBox.warning(self, "Load Failed", "data.json file not found.")
        except Exception as e:
            QMessageBox.critical(self, "Load Failed", f"An error occurred while loading:\n{e}")
