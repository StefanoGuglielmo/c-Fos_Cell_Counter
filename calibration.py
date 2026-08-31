import numpy as np

from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QImage, QPainter, QPen, QBrush
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
)


# ============================================================
# CALIBRATION VIEW
# ============================================================

class CalibrationView(QWidget):

    def __init__(self, image, n_cells):

        super().__init__()

        # ----------------------------------------------------
        # Store image information
        # ----------------------------------------------------

        self.image = image

        self.H, self.W = image.shape

        self.n_cells = n_cells

        # ----------------------------------------------------
        # Zoom
        # ----------------------------------------------------

        self.zoom = 1.0

        # ----------------------------------------------------
        # Center of the current view
        # ----------------------------------------------------

        self.center_x = self.W / 2
        self.center_y = self.H / 2

        # ----------------------------------------------------
        # Current measurement
        # ----------------------------------------------------

        self.first_point = None
        self.mouse_position = None

        # ----------------------------------------------------
        # Completed measurements
        # ----------------------------------------------------

        self.references = []

        # ----------------------------------------------------
        # Panning
        # ----------------------------------------------------

        self.panning = False
        self.pan_start = None

        # ----------------------------------------------------
        # Callback used by the dialog to update the counter
        # ----------------------------------------------------

        self.on_reference_added = None

        # ====================================================
        # NORMALIZE IMAGE
        # ====================================================

        normalized = image.astype(
            np.float32
        )

        mn = normalized.min()
        mx = normalized.max()

        if mx != mn:

            normalized = (
                (normalized - mn)
                / (mx - mn)
                * 255
            )

        else:

            normalized = np.zeros_like(
                normalized
            )

        normalized = normalized.astype(
            np.uint8
        )

        # ====================================================
        # NUMPY → QIMAGE
        # ====================================================

        self.qimage = QImage(
            normalized.data,
            self.W,
            self.H,
            self.W,
            QImage.Format_Grayscale8,
        ).copy()

        # ----------------------------------------------------
        # Mouse tracking
        # ----------------------------------------------------

        self.setMouseTracking(True)

        self.setMinimumSize(
            900,
            700
        )

    # ========================================================
    # GET CURRENT VIEW
    # ========================================================

    def get_view(self):

        # Width and height of the image currently visible
        view_w = self.width() / self.zoom
        view_h = self.height() / self.zoom

        # Never display an area larger than the image
        view_w = min(
            view_w,
            self.W
        )

        view_h = min(
            view_h,
            self.H
        )

        # Top-left corner of the visible image
        x0 = (
            self.center_x
            - view_w / 2
        )

        y0 = (
            self.center_y
            - view_h / 2
        )

        # Keep the view inside the image
        x0 = max(
            0,
            min(
                x0,
                self.W - view_w
            )
        )

        y0 = max(
            0,
            min(
                y0,
                self.H - view_h
            )
        )

        return (
            x0,
            y0,
            view_w,
            view_h
        )

    # ========================================================
    # IMAGE → SCREEN
    # ========================================================

    def image_to_screen(
        self,
        x,
        y
    ):

        x0, y0, _, _ = self.get_view()

        screen_x = (
            x - x0
        ) * self.zoom

        screen_y = (
            y - y0
        ) * self.zoom

        return QPoint(
            int(screen_x),
            int(screen_y)
        )

    # ========================================================
    # SCREEN → IMAGE
    # ========================================================

    def screen_to_image(
        self,
        x,
        y
    ):

        x0, y0, _, _ = self.get_view()

        image_x = (
            x / self.zoom
            + x0
        )

        image_y = (
            y / self.zoom
            + y0
        )

        image_x = float(
            np.clip(
                image_x,
                0,
                self.W - 1
            )
        )

        image_y = float(
            np.clip(
                image_y,
                0,
                self.H - 1
            )
        )

        return (
            image_x,
            image_y
        )

    # ========================================================
    # DRAW IMAGE AND MEASUREMENTS
    # ========================================================

    def paintEvent(self, event):

        painter = QPainter(self)

        # ----------------------------------------------------
        # Black background
        # ----------------------------------------------------

        painter.fillRect(
            self.rect(),
            Qt.black
        )

        # ----------------------------------------------------
        # Determine visible image region
        # ----------------------------------------------------

        x0, y0, view_w, view_h = (
            self.get_view()
        )

        sx = int(x0)
        sy = int(y0)

        sw = max(
            1,
            int(view_w)
        )

        sh = max(
            1,
            int(view_h)
        )

        # ----------------------------------------------------
        # Source rectangle
        # ----------------------------------------------------

        source_rect = self.qimage.rect().intersected(
            self.qimage.rect().__class__(
                sx,
                sy,
                sw,
                sh
            )
        )

        # ----------------------------------------------------
        # Draw image
        # ----------------------------------------------------

        painter.drawImage(
            self.rect(),
            self.qimage,
            source_rect
        )

        # ====================================================
        # DRAW COMPLETED REFERENCES
        # ====================================================

        for i, ref in enumerate(
            self.references
        ):

            p1 = self.image_to_screen(
                *ref["p1"]
            )

            p2 = self.image_to_screen(
                *ref["p2"]
            )

            center = self.image_to_screen(
                ref["center_x"],
                ref["center_y"]
            )

            radius = max(
                3,
                int(
                    ref["diameter"]
                    * self.zoom
                    / 2
                )
            )

            # ------------------------------------------------
            # Diameter line
            # ------------------------------------------------

            painter.setPen(
                QPen(
                    Qt.red,
                    2
                )
            )

            painter.drawLine(
                p1,
                p2
            )

            # ------------------------------------------------
            # Cell circle
            # ------------------------------------------------

            painter.setPen(
                QPen(
                    Qt.yellow,
                    2
                )
            )

            painter.drawEllipse(
                center,
                radius,
                radius
            )

            # ------------------------------------------------
            # Measurement points
            # ------------------------------------------------

            painter.setBrush(
                QBrush(
                    Qt.green
                )
            )

            painter.drawEllipse(
                p1,
                5,
                5
            )

            painter.drawEllipse(
                p2,
                5,
                5
            )

            # ------------------------------------------------
            # Reference number
            # ------------------------------------------------

            painter.setPen(
                QPen(
                    Qt.yellow,
                    2
                )
            )

            painter.drawText(
                center.x() + 8,
                center.y() - 8,
                str(i + 1)
            )

        # ====================================================
        # DRAW CURRENT MEASUREMENT
        # ====================================================

        if self.first_point is not None:

            p1 = self.image_to_screen(
                *self.first_point
            )

            # ------------------------------------------------
            # First point cross
            # ------------------------------------------------

            painter.setPen(
                QPen(
                    Qt.yellow,
                    2
                )
            )

            painter.drawLine(
                p1.x() - 10,
                p1.y(),
                p1.x() + 10,
                p1.y()
            )

            painter.drawLine(
                p1.x(),
                p1.y() - 10,
                p1.x(),
                p1.y() + 10
            )

            # ------------------------------------------------
            # Temporary diameter line
            # ------------------------------------------------

            if self.mouse_position is not None:

                p2 = self.image_to_screen(
                    *self.mouse_position
                )

                painter.drawLine(
                    p1,
                    p2
                )

        painter.end()

    # ========================================================
    # MOUSE PRESS
    # ========================================================

    def mousePressEvent(self, event):

        # ====================================================
        # MIDDLE BUTTON → START PAN
        # ====================================================

        if event.button() == Qt.MiddleButton:

            self.panning = True

            self.pan_start = event.position()

            return

        # ====================================================
        # RIGHT BUTTON → UNDO
        # ====================================================

        if event.button() == Qt.RightButton:

            # Cancel current measurement first
            if self.first_point is not None:

                self.first_point = None

            # Otherwise remove last completed reference
            elif self.references:

                self.references.pop()

                if self.on_reference_added is not None:

                    self.on_reference_added(
                        len(self.references)
                    )

            self.update()

            return

        # ====================================================
        # LEFT BUTTON → MEASURE
        # ====================================================

        if event.button() == Qt.LeftButton:

            x, y = self.screen_to_image(
                event.position().x(),
                event.position().y()
            )

            # ------------------------------------------------
            # First click
            # ------------------------------------------------

            if self.first_point is None:

                self.first_point = (
                    x,
                    y
                )

            # ------------------------------------------------
            # Second click
            # ------------------------------------------------

            else:

                ref = self.measure_reference(
                    self.first_point,
                    (x, y)
                )

                if ref is not None:

                    self.references.append(
                        ref
                    )

                    if self.on_reference_added is not None:

                        self.on_reference_added(
                            len(self.references)
                        )

                self.first_point = None

                # ------------------------------------------------
                # Automatically finish
                # ------------------------------------------------

                if len(
                    self.references
                ) >= self.n_cells:

                    self.window().accept()

            self.update()

    # ========================================================
    # MOUSE RELEASE
    # ========================================================

    def mouseReleaseEvent(self, event):

        if event.button() == Qt.MiddleButton:

            self.panning = False

            self.pan_start = None

    # ========================================================
    # MOUSE MOVE
    # ========================================================

    def mouseMoveEvent(self, event):

        x, y = self.screen_to_image(
            event.position().x(),
            event.position().y()
        )

        self.mouse_position = (
            x,
            y
        )

        # ----------------------------------------------------
        # Pan image
        # ----------------------------------------------------

        if self.panning:

            dx = (
                event.position().x()
                - self.pan_start.x()
            )

            dy = (
                event.position().y()
                - self.pan_start.y()
            )

            self.center_x -= (
                dx / self.zoom
            )

            self.center_y -= (
                dy / self.zoom
            )

            self.pan_start = (
                event.position()
            )

        self.update()

    # ========================================================
    # MOUSE WHEEL → ZOOM
    # ========================================================

    def wheelEvent(self, event):

        old_zoom = self.zoom

        # ----------------------------------------------------
        # Determine zoom direction
        # ----------------------------------------------------

        if event.angleDelta().y() > 0:

            new_zoom = (
                old_zoom * 1.25
            )

        else:

            new_zoom = (
                old_zoom / 1.25
            )

        new_zoom = float(
            np.clip(
                new_zoom,
                0.1,
                20
            )
        )

        # ----------------------------------------------------
        # Find image position under cursor
        # ----------------------------------------------------

        mouse_x, mouse_y = (
            self.screen_to_image(
                event.position().x(),
                event.position().y()
            )
        )

        # ----------------------------------------------------
        # Keep that image position under cursor
        # ----------------------------------------------------

        self.center_x += (
            mouse_x
            - self.center_x
        ) * (
            1
            - old_zoom / new_zoom
        )

        self.center_y += (
            mouse_y
            - self.center_y
        ) * (
            1
            - old_zoom / new_zoom
        )

        self.zoom = new_zoom

        self.update()

    # ========================================================
    # MEASURE REFERENCE CELL
    # ========================================================

    def measure_reference(
        self,
        p1,
        p2
    ):

        x1, y1 = p1
        x2, y2 = p2

        # ----------------------------------------------------
        # Calculate diameter
        # ----------------------------------------------------

        diameter = np.hypot(
            x2 - x1,
            y2 - y1
        )

        if diameter < 2:

            return None

        # ----------------------------------------------------
        # Calculate center
        # ----------------------------------------------------

        cx = (
            x1 + x2
        ) / 2

        cy = (
            y1 + y2
        ) / 2

        radius = diameter / 2

        # ----------------------------------------------------
        # Create circular mask
        # ----------------------------------------------------

        yy, xx = np.ogrid[
            :self.H,
            :self.W
        ]

        circle = (
            (xx - cx) ** 2
            +
            (yy - cy) ** 2
            <= radius ** 2
        )

        # ----------------------------------------------------
        # Extract pixel values
        # ----------------------------------------------------

        values = self.image[
            circle
        ]

        if len(values) == 0:

            return None

        # ----------------------------------------------------
        # Return measurement
        # ----------------------------------------------------

        return {

            "p1":
                p1,

            "p2":
                p2,

            "center_x":
                cx,

            "center_y":
                cy,

            "diameter":
                diameter,

            "mean_intensity":
                float(
                    values.mean()
                ),

            "max_intensity":
                float(
                    values.max()
                ),
        }


# ============================================================
# CALIBRATION DIALOG
# ============================================================

class CalibrationDialog(QDialog):

    def __init__(
        self,
        image,
        n_cells
    ):

        super().__init__()

        self.setWindowTitle(
            "cFos Calibration"
        )

        self.resize(
            1200,
            900
        )

        # ====================================================
        # MAIN LAYOUT
        # ====================================================

        layout = QVBoxLayout(
            self
        )

        # ====================================================
        # INSTRUCTIONS
        # ====================================================

        instructions = QLabel(
            f"Select {n_cells} representative cFos+ cells\n\n"
            "LEFT CLICK → first edge\n"
            "LEFT CLICK → opposite edge\n"
            "RIGHT CLICK → undo\n"
            "MIDDLE DRAG → pan\n"
            "MOUSE WHEEL → zoom"
        )

        instructions.setAlignment(
            Qt.AlignCenter
        )

        layout.addWidget(
            instructions
        )

        # ====================================================
        # IMAGE
        # ====================================================

        self.view = CalibrationView(
            image,
            n_cells
        )

        # Tell the view how to update the counter
        self.view.on_reference_added = (
            self.update_reference_count
        )

        layout.addWidget(
            self.view,
            stretch=1
        )

        # ====================================================
        # BOTTOM BAR
        # ====================================================

        bottom_layout = QHBoxLayout()

        # ----------------------------------------------------
        # Reference counter
        # ----------------------------------------------------

        self.status_label = QLabel(
            f"References: 0/{n_cells}"
        )

        bottom_layout.addWidget(
            self.status_label
        )

        bottom_layout.addStretch()

        # ----------------------------------------------------
        # Cancel button
        # ----------------------------------------------------

        cancel_button = QPushButton(
            "Cancel"
        )

        cancel_button.clicked.connect(
            self.reject
        )

        bottom_layout.addWidget(
            cancel_button
        )

        layout.addLayout(
            bottom_layout
        )

    # ========================================================
    # UPDATE REFERENCE COUNTER
    # ========================================================

    def update_reference_count(
        self,
        count
    ):

        self.status_label.setText(
            f"References: "
            f"{count}/"
            f"{self.view.n_cells}"
        )


# ============================================================
# PUBLIC CALIBRATION FUNCTION
# ============================================================

def calibrate_image(
    image,
    n_cells=5
):

    # --------------------------------------------------------
    # Create dialog
    # --------------------------------------------------------

    dialog = CalibrationDialog(
        image,
        n_cells
    )

    # --------------------------------------------------------
    # Show dialog and wait
    # --------------------------------------------------------

    result = dialog.exec()

    # --------------------------------------------------------
    # User cancelled
    # --------------------------------------------------------

    if result != QDialog.Accepted:

        raise RuntimeError(
            "Calibration cancelled."
        )

    # --------------------------------------------------------
    # Retrieve measurements
    # --------------------------------------------------------

    references = (
        dialog.view.references
    )

    # --------------------------------------------------------
    # Safety check
    # --------------------------------------------------------

    if len(references) != n_cells:

        raise RuntimeError(
            "Calibration did not collect "
            "enough reference cells."
        )

    # ========================================================
    # CALCULATE FINAL CALIBRATION
    # ========================================================

    reference_diameter = float(
        np.median(
            [
                r["diameter"]
                for r in references
            ]
        )
    )

    reference_intensity = float(
        np.median(
            [
                r["mean_intensity"]
                for r in references
            ]
        )
    )

    # --------------------------------------------------------
    # Return exactly the same information as before
    # --------------------------------------------------------

    return (
        reference_diameter,
        reference_intensity,
        references
    )