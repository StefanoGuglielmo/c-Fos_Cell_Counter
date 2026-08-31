import sys
import os

if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")

if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")


from pathlib import Path

from PySide6.QtCore import (
    Qt,
    QThread,
    QTimer,
)

from PySide6.QtGui import (
    QImage,
    QPixmap,
)

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QSpinBox,
    QDoubleSpinBox,
    QRadioButton,
    QButtonGroup,
    QProgressBar,
    QTextEdit,
    QFileDialog,
    QMessageBox,
    QGroupBox,
    QScrollArea,
    QFrame,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
)

load_image = None
calibrate_image = None
AnalysisWorker = None


# ============================================================
# MAIN WINDOW
# ============================================================

class MainWindow(QMainWindow):

    def __init__(self):

        super().__init__()

        # ----------------------------------------------------
        # Window
        # ----------------------------------------------------

        self.setWindowTitle(
            "c-Fos Cell Counter"
        )

        self.resize(
            1500,
            900
        )

        # ----------------------------------------------------
        # Worker
        # ----------------------------------------------------

        self.thread = None

        self.worker = None

        # ----------------------------------------------------
        # Current output directory
        # ----------------------------------------------------

        self.current_output_dir = None

        # ====================================================
        # CENTRAL WIDGET
        # ====================================================

        central_widget = QWidget()

        self.setCentralWidget(
            central_widget
        )

        # ====================================================
        # MAIN HORIZONTAL LAYOUT
        # ====================================================

        main_layout = QHBoxLayout(
            central_widget
        )

        # ====================================================
        # LEFT PANEL
        # ====================================================

        left_widget = QWidget()

        left_layout = QVBoxLayout(
            left_widget
        )

        # ----------------------------------------------------
        # TITLE
        # ----------------------------------------------------

        title = QLabel(
            "c-Fos Cell Counter"
        )

        title.setAlignment(
            Qt.AlignCenter
        )

        title.setStyleSheet(
            """
            QLabel {
                font-size: 28px;
                font-weight: bold;
                padding: 15px;
            }
            """
        )

        left_layout.addWidget(
            title
        )

        # ====================================================
        # INPUT FOLDER
        # ====================================================

        input_layout = QHBoxLayout()

        input_label = QLabel(
            "Input folder:"
        )

        self.input_edit = QLineEdit()

        input_button = QPushButton(
            "Browse..."
        )

        input_button.clicked.connect(
            self.select_input_folder
        )

        input_layout.addWidget(
            input_label
        )

        input_layout.addWidget(
            self.input_edit
        )

        input_layout.addWidget(
            input_button
        )

        left_layout.addLayout(
            input_layout
        )

        # ====================================================
        # OUTPUT FOLDER
        # ====================================================

        output_layout = QHBoxLayout()

        output_label = QLabel(
            "Output folder:"
        )

        self.output_edit = QLineEdit()

        output_button = QPushButton(
            "Browse..."
        )

        output_button.clicked.connect(
            self.select_output_folder
        )

        output_layout.addWidget(
            output_label
        )

        output_layout.addWidget(
            self.output_edit
        )

        output_layout.addWidget(
            output_button
        )

        left_layout.addLayout(
            output_layout
        )

        # ====================================================
        # SETTINGS
        # ====================================================

        settings_group = QGroupBox(
            "Analysis settings"
        )

        settings_group.setToolTip(
            "Parameters controlling cell detection and c-Fos classification."
        )

        settings_layout = QVBoxLayout(
            settings_group
        )

        # ====================================================
        # REFERENCE CELLS
        # ====================================================

        reference_layout = QHBoxLayout()

        reference_label = QLabel(
            "Calibration cells:"
        )

        reference_label.setToolTip(
            "Number of manually selected c-Fos-positive reference cells "
            "used to determine the reference cell diameter and reference intensity."
        )

        self.reference_spin = QSpinBox()

        self.reference_spin.setMinimum(
            1
        )

        self.reference_spin.setMaximum(
            100
        )

        self.reference_spin.setValue(
            5
        )

        self.reference_spin.setToolTip(
            "Number of reference c-Fos-positive cells selected during calibration.\n\n"
            "These cells are used to calculate:\n"
            "• the reference cell diameter\n"
            "• the reference fluorescence intensity\n\n"
            "More cells can give a more representative calibration, "
            "but require more manual selections."
        )

        reference_layout.addWidget(
            reference_label
        )

        reference_layout.addWidget(
            self.reference_spin
        )

        reference_layout.addStretch()

        settings_layout.addLayout(
            reference_layout
        )

        # ====================================================
        # CFOS INTENSITY FACTOR
        # ====================================================

        intensity_layout = QHBoxLayout()

        intensity_label = QLabel(
            "cFos intensity factor:"
        )

        intensity_label.setToolTip(
            "Controls the fluorescence intensity threshold used to classify cells as c-Fos-positive."
        )

        self.intensity_spin = QDoubleSpinBox()

        self.intensity_spin.setMinimum(
            0.01
        )

        self.intensity_spin.setMaximum(
            10.00
        )

        self.intensity_spin.setSingleStep(
            0.05
        )

        self.intensity_spin.setDecimals(
            3
        )

        self.intensity_spin.setValue(
            0.50
        )

        self.intensity_spin.setToolTip(
            "The intensity threshold is calculated as:\n\n"
            "reference intensity × cFos intensity factor\n\n"
            "A cell must have a mean intensity equal to or greater "
            "than this threshold to pass the intensity criterion.\n\n"
            "Lower values → less strict intensity criterion.\n"
            "Higher values → more strict intensity criterion."
        )

        intensity_layout.addWidget(
            intensity_label
        )

        intensity_layout.addWidget(
            self.intensity_spin
        )

        intensity_layout.addStretch()

        settings_layout.addLayout(
            intensity_layout
        )

        # ====================================================
        # MINIMUM CELL-SIZE FACTOR
        # ====================================================

        min_size_layout = QHBoxLayout()

        min_size_label = QLabel(
            "Minimum cell-size factor:"
        )

        min_size_label.setToolTip(
            "Controls the minimum allowed cell diameter relative to the reference cells."
        )

        self.min_size_spin = QDoubleSpinBox()

        self.min_size_spin.setMinimum(
            0.01
        )

        self.min_size_spin.setMaximum(
            10.00
        )

        self.min_size_spin.setSingleStep(
            0.05
        )

        self.min_size_spin.setDecimals(
            3
        )

        self.min_size_spin.setValue(
            0.50
        )

        self.min_size_spin.setToolTip(
            "The minimum allowed cell diameter is calculated as:\n\n"
            "reference diameter × minimum cell-size factor\n\n"
            "Cells smaller than this value cannot be classified as c-Fos-positive.\n\n"
            "Lower values → allow smaller cells.\n"
            "Higher values → exclude more small cells."
        )

        min_size_layout.addWidget(
            min_size_label
        )

        min_size_layout.addWidget(
            self.min_size_spin
        )

        min_size_layout.addStretch()

        settings_layout.addLayout(
            min_size_layout
        )

        # ====================================================
        # MAXIMUM CELL-SIZE FACTOR
        # ====================================================

        max_size_layout = QHBoxLayout()

        max_size_label = QLabel(
            "Maximum cell-size factor:"
        )

        max_size_label.setToolTip(
            "Controls the maximum allowed cell diameter relative to the reference cells."
        )

        self.max_size_spin = QDoubleSpinBox()

        self.max_size_spin.setMinimum(
            0.01
        )

        self.max_size_spin.setMaximum(
            10.00
        )

        self.max_size_spin.setSingleStep(
            0.05
        )

        self.max_size_spin.setDecimals(
            3
        )

        self.max_size_spin.setValue(
            1.50
        )

        self.max_size_spin.setToolTip(
            "The maximum allowed cell diameter is calculated as:\n\n"
            "reference diameter × maximum cell-size factor\n\n"
            "Cells larger than this value cannot be classified as c-Fos-positive.\n\n"
            "Lower values → exclude more large cells.\n"
            "Higher values → allow larger cells."
        )

        max_size_layout.addWidget(
            max_size_label
        )

        max_size_layout.addWidget(
            self.max_size_spin
        )

        max_size_layout.addStretch()

        settings_layout.addLayout(
            max_size_layout
        )

        # ====================================================
        # STARDIST PROBABILITY THRESHOLD
        # ====================================================

        prob_layout = QHBoxLayout()

        prob_label = QLabel(
            "StarDist probability threshold:"
        )

        prob_label.setToolTip(
            "Controls how confident StarDist must be before accepting a detected cell."
        )

        self.prob_spin = QDoubleSpinBox()

        self.prob_spin.setMinimum(
            0.00
        )

        self.prob_spin.setMaximum(
            1.00
        )

        self.prob_spin.setSingleStep(
            0.01
        )

        self.prob_spin.setDecimals(
            6
        )

        self.prob_spin.setValue(
            0.35
        )

        self.prob_spin.setToolTip(
            "Minimum probability assigned by StarDist for accepting a detected object.\n\n"
            "Lower values → StarDist accepts more possible cells, "
            "but may increase false detections.\n\n"
            "Higher values → StarDist requires greater confidence, "
            "but may miss weaker or difficult cells."
        )

        prob_layout.addWidget(
            prob_label
        )

        prob_layout.addWidget(
            self.prob_spin
        )

        prob_layout.addStretch()

        settings_layout.addLayout(
            prob_layout
        )

        # ====================================================
        # STARDIST NMS THRESHOLD
        # ====================================================

        nms_layout = QHBoxLayout()

        nms_label = QLabel(
            "StarDist NMS threshold:"
        )

        nms_label.setToolTip(
            "Controls how strongly overlapping StarDist detections are suppressed."
        )

        self.nms_spin = QDoubleSpinBox()

        self.nms_spin.setMinimum(
            0.00
        )

        self.nms_spin.setMaximum(
            1.00
        )

        self.nms_spin.setSingleStep(
            0.01
        )

        self.nms_spin.setDecimals(
            3
        )

        self.nms_spin.setValue(
            0.30
        )

        self.nms_spin.setToolTip(
            "Non-Maximum Suppression (NMS) threshold used by StarDist "
            "to decide whether overlapping detections represent the same cell.\n\n"
            "Lower values → stronger suppression of overlapping detections.\n\n"
            "Higher values → more overlapping detections can be retained."
        )

        nms_layout.addWidget(
            nms_label
        )

        nms_layout.addWidget(
            self.nms_spin
        )

        nms_layout.addStretch()

        settings_layout.addLayout(
            nms_layout
        )

        # ====================================================
        # CALIBRATION MODE
        # ====================================================

        calibration_label = QLabel(
            "Calibration:"
        )

        calibration_label.setToolTip(
            "Determines whether the reference calibration is reused "
            "for all images or measured independently for every image."
        )

        settings_layout.addWidget(
            calibration_label
        )

        # ----------------------------------------------------
        # Shared calibration
        # ----------------------------------------------------

        self.shared_radio = QRadioButton(
            "Use the same calibration for all images"
        )

        self.shared_radio.setChecked(
            True
        )

        self.shared_radio.setToolTip(
            "Select this when all images were acquired under comparable "
            "imaging conditions.\n\n"
            "The first image is manually calibrated and the same "
            "reference diameter and intensity are used for every image."
        )

        # ----------------------------------------------------
        # Individual calibration
        # ----------------------------------------------------

        self.individual_radio = QRadioButton(
            "Calibrate each image independently"
        )

        self.individual_radio.setToolTip(
            "Select this when images may differ in fluorescence intensity "
            "or cell size.\n\n"
            "Each image will receive its own manual calibration."
        )

        # ----------------------------------------------------
        # Radio button group
        # ----------------------------------------------------

        calibration_group = QButtonGroup(
            self
        )

        calibration_group.addButton(
            self.shared_radio
        )

        calibration_group.addButton(
            self.individual_radio
        )

        settings_layout.addWidget(
            self.shared_radio
        )

        settings_layout.addWidget(
            self.individual_radio
        )

        # ====================================================
        # ADD SETTINGS GROUP TO LEFT PANEL
        # ====================================================

        left_layout.addWidget(
            settings_group
        )

        # ====================================================
        # SETTINGS EXPLANATION
        # ====================================================

        settings_info = QLabel(
            "Detection:\n"
            "StarDist identifies individual cells.\n"
            "Classification:\n"
            "Detected cells are classified as c-Fos+ based on "
            "cell size and fluorescence intensity relative to "
            "the manually calibrated reference cells."
        )

        settings_info.setWordWrap(
            True
        )

        settings_info.setStyleSheet(
            """
            QLabel {
                color: #555555;
                font-size: 12px;
                padding: 8px;
            }
            """
        )

        settings_layout.addWidget(
            settings_info
        )

        # ====================================================
        # BUTTONS
        # ====================================================

        button_layout = QHBoxLayout()

        # ----------------------------------------------------
        # START
        # ----------------------------------------------------

        self.start_button = QPushButton(
            "START ANALYSIS"
        )

        self.start_button.setMinimumHeight(
            50
        )

        self.start_button.setStyleSheet(
            """
            QPushButton {
                font-size: 18px;
                font-weight: bold;
            }
            """
        )

        self.start_button.clicked.connect(
            self.start_analysis
        )

        button_layout.addWidget(
            self.start_button
        )

        # ----------------------------------------------------
        # CANCEL
        # ----------------------------------------------------

        self.cancel_button = QPushButton(
            "CANCEL"
        )

        self.cancel_button.setMinimumHeight(
            50
        )

        self.cancel_button.setEnabled(
            False
        )

        self.cancel_button.clicked.connect(
            self.cancel_analysis
        )

        button_layout.addWidget(
            self.cancel_button
        )

        left_layout.addLayout(
            button_layout
        )

        # ====================================================
        # RESET BUTTON
        # ====================================================

        self.reset_button = QPushButton(
            "RESET"
        )

        self.reset_button.clicked.connect(
            self.reset_application
        )

        left_layout.addWidget(
            self.reset_button
        )

        # ====================================================
        # OPEN OUTPUT FOLDER
        # ====================================================

        self.open_output_button = QPushButton(
            "OPEN OUTPUT FOLDER"
        )

        self.open_output_button.setEnabled(
            False
        )

        self.open_output_button.clicked.connect(
            self.open_output_folder
        )

        left_layout.addWidget(
            self.open_output_button
        )

        # ====================================================
        # PROGRESS
        # ====================================================

        progress_label = QLabel(
            "Progress:"
        )

        left_layout.addWidget(
            progress_label
        )

        self.progress_bar = QProgressBar()

        self.progress_bar.setValue(
            0
        )

        left_layout.addWidget(
            self.progress_bar
        )

        # ====================================================
        # STATUS
        # ====================================================

        status_label = QLabel(
            "Status:"
        )

        left_layout.addWidget(
            status_label
        )

        self.status_text = QTextEdit()

        self.status_text.setReadOnly(
            True
        )

        left_layout.addWidget(
            self.status_text
        )

        # ====================================================
        # LEFT PANEL SCROLL AREA
        # ====================================================

        left_scroll = QScrollArea()

        left_scroll.setWidgetResizable(
            True
        )

        left_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        left_scroll.setWidget(
            left_widget
        )

        main_layout.addWidget(
            left_scroll,
            1
        )

        # ====================================================
        # RIGHT PANEL
        # ====================================================

        right_widget = QWidget()

        right_layout = QVBoxLayout(
            right_widget
        )

        # ====================================================
        # RESULTS TABLE
        # ====================================================

        results_title = QLabel(
            "Results"
        )

        results_title.setStyleSheet(
            """
            QLabel {
                font-size: 22px;
                font-weight: bold;
                padding: 5px;
            }
            """
        )

        right_layout.addWidget(
            results_title
        )

        # ----------------------------------------------------
        # Table
        # ----------------------------------------------------

        self.results_table = QTableWidget()

        self.results_table.setColumnCount(
            5
        )

        self.results_table.setHorizontalHeaderLabels(
            [
                "Image",
                "Detected",
                "c-Fos+",
                "c-Fos-",
                "% c-Fos+ of detected cells",
            ]
        )

        # ----------------------------------------------------
        # Table appearance
        # ----------------------------------------------------

        self.results_table.setEditTriggers(
            QTableWidget.NoEditTriggers
        )

        self.results_table.setSelectionBehavior(
            QTableWidget.SelectRows
        )

        self.results_table.setAlternatingRowColors(
            True
        )

        header = (
            self.results_table.horizontalHeader()
        )

        header.setSectionResizeMode(
            0,
            QHeaderView.Stretch
        )

        header.setSectionResizeMode(
            1,
            QHeaderView.ResizeToContents
        )

        header.setSectionResizeMode(
            2,
            QHeaderView.ResizeToContents
        )

        header.setSectionResizeMode(
            3,
            QHeaderView.ResizeToContents
        )

        header.setSectionResizeMode(
            4,
            QHeaderView.ResizeToContents
        )

        self.results_table.setMaximumHeight(
            250
        )

        right_layout.addWidget(
            self.results_table
        )

        # ====================================================
        # OVERLAY TITLE
        # ====================================================

        overlay_title = QLabel(
            "Classification overlays"
        )

        overlay_title.setAlignment(
            Qt.AlignCenter
        )

        overlay_title.setStyleSheet(
            """
            QLabel {
                font-size: 22px;
                font-weight: bold;
                padding: 10px;
            }
            """
        )

        right_layout.addWidget(
            overlay_title
        )

        # ====================================================
        # OVERLAY SCROLL AREA
        # ====================================================

        self.scroll_area = QScrollArea()

        self.scroll_area.setWidgetResizable(
            True
        )

        # ----------------------------------------------------
        # Container
        # ----------------------------------------------------

        self.overlay_container = QWidget()

        self.overlay_layout = QVBoxLayout(
            self.overlay_container
        )

        self.overlay_layout.setAlignment(
            Qt.AlignTop
        )

        self.overlay_layout.setSpacing(
            20
        )

        self.scroll_area.setWidget(
            self.overlay_container
        )

        right_layout.addWidget(
            self.scroll_area
        )

        # ====================================================
        # ADD RIGHT PANEL
        # ====================================================

        main_layout.addWidget(
            right_widget,
            2
        )

        # ====================================================
        # INITIAL STATUS
        # ====================================================

        self.log(
            "Ready."
        )

    # ========================================================
    # LOG
    # ========================================================

    def log(
        self,
        message
    ):

        self.status_text.append(
            message
        )

        QApplication.processEvents()

    # ========================================================
    # HELPER
    # ========================================================

    def set_settings_enabled(
        self,
        enabled
    ):

        self.reference_spin.setEnabled(
            enabled
        )

        self.intensity_spin.setEnabled(
            enabled
        )

        self.min_size_spin.setEnabled(
            enabled
        )

        self.max_size_spin.setEnabled(
            enabled
        )

        self.prob_spin.setEnabled(
            enabled
        )

        self.nms_spin.setEnabled(
            enabled
        )

        self.shared_radio.setEnabled(
            enabled
        )

        self.individual_radio.setEnabled(
            enabled
        )

    # ========================================================
    # INPUT FOLDER
    # ========================================================

    def select_input_folder(
        self
    ):

        folder = QFileDialog.getExistingDirectory(
            self,
            "Select input folder"
        )

        if folder:

            self.input_edit.setText(
                folder
            )

    # ========================================================
    # OUTPUT FOLDER
    # ========================================================

    def select_output_folder(
        self
    ):

        folder = QFileDialog.getExistingDirectory(
            self,
            "Select output folder"
        )

        if folder:

            self.output_edit.setText(
                folder
            )

    # ========================================================
    # CLEAR OVERLAYS
    # ========================================================

    def clear_overlays(
        self
    ):

        while self.overlay_layout.count():

            item = self.overlay_layout.takeAt(
                0
            )

            widget = item.widget()

            if widget is not None:

                widget.deleteLater()

    # ========================================================
    # CLEAR RESULTS TABLE
    # ========================================================

    def clear_results_table(
        self
    ):

        self.results_table.setRowCount(
            0
        )

    # ========================================================
    # START ANALYSIS
    # ========================================================

    def start_analysis(
        self
    ):

        # ----------------------------------------------------
        # Get folders
        # ----------------------------------------------------

        input_dir = Path(
            self.input_edit.text()
        )

        output_dir = Path(
            self.output_edit.text()
        )

        # ----------------------------------------------------
        # Validate input
        # ----------------------------------------------------

        if not input_dir.exists():

            QMessageBox.warning(
                self,
                "Invalid input folder",
                "Please select a valid input folder."
            )

            return

        # ----------------------------------------------------
        # Find images
        # ----------------------------------------------------

        image_files = sorted(
            f
            for f in input_dir.iterdir()
            if f.suffix.lower()
            in (
                ".tif",
                ".tiff"
            )
        )

        if not image_files:

            QMessageBox.warning(
                self,
                "No images",
                "No TIFF images were found."
            )

            return

        # ----------------------------------------------------
        # Create output
        # ----------------------------------------------------

        output_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        self.current_output_dir = (
            output_dir
        )

        # ----------------------------------------------------
        # Settings
        # ----------------------------------------------------

        n_reference_cells = (
            self.reference_spin.value()
        )

        use_shared_calibration = (
            self.shared_radio.isChecked()
        )

        # ----------------------------------------------------
        # Analysis settings
        # ----------------------------------------------------

        settings = {

            "n_reference_cells":
                n_reference_cells,

            "intensity_factor":
                self.intensity_spin.value(),

            "diameter_min_factor":
                self.min_size_spin.value(),

            "diameter_max_factor":
                self.max_size_spin.value(),

            "prob_thresh":
                self.prob_spin.value(),

            "nms_thresh":
                self.nms_spin.value(),
        }

        # ====================================================
        # RESET PREVIOUS RESULTS
        # ====================================================

        self.clear_overlays()

        self.clear_results_table()

        self.progress_bar.setValue(
            0
        )

        self.open_output_button.setEnabled(
            False
        )

        self.start_button.setEnabled(
            False
        )

        self.reference_spin.setEnabled(
            False
        )

        self.intensity_spin.setEnabled(
            False
        )

        self.min_size_spin.setEnabled(
            False
        )

        self.max_size_spin.setEnabled(
            False
        )

        self.prob_spin.setEnabled(
            False
        )

        self.nms_spin.setEnabled(
            False
        )

        self.shared_radio.setEnabled(
            False
        )

        self.individual_radio.setEnabled(
            False
        )

        self.reset_button.setEnabled(
            False
        )

        self.cancel_button.setEnabled(
            False
        )

        self.log(
            ""
        )

        self.log(
            f"Found {len(image_files)} TIFF images."
        )

        # ====================================================
        # CALIBRATION
        # ====================================================

        calibrations = {}

        # ----------------------------------------------------
        # SHARED
        # ----------------------------------------------------

        if use_shared_calibration:

            self.log(
                "Starting shared calibration..."
            )

            first_image = image_files[0]

            self.log(
                f"Calibration image: "
                f"{first_image.name}"
            )

            image = load_image(
                first_image
            )

            (
                reference_diameter,
                reference_intensity,
                _
            ) = calibrate_image(
                image,
                n_reference_cells
            )

            # ------------------------------------------------
            # Same calibration for all images
            # ------------------------------------------------

            for image_path in image_files:

                calibrations[
                    image_path
                ] = (
                    reference_diameter,
                    reference_intensity
                )

            self.log(
                "Shared calibration completed."
            )

            self.log(
                f"Reference diameter: "
                f"{reference_diameter:.2f} px"
            )

            self.log(
                f"Reference intensity: "
                f"{reference_intensity:.2f}"
            )

        # ----------------------------------------------------
        # INDIVIDUAL
        # ----------------------------------------------------

        else:

            self.log(
                "Individual calibration selected."
            )

            for index, image_path in enumerate(
                image_files
            ):

                self.log(
                    ""
                )

                self.log(
                    f"Calibration "
                    f"{index + 1}/"
                    f"{len(image_files)}: "
                    f"{image_path.name}"
                )

                image = load_image(
                    image_path
                )

                (
                    reference_diameter,
                    reference_intensity,
                    _
                ) = calibrate_image(
                    image,
                    n_reference_cells
                )

                calibrations[
                    image_path
                ] = (
                    reference_diameter,
                    reference_intensity
                )

                self.log(
                    "Calibration completed."
                )

        # ====================================================
        # START WORKER
        # ====================================================

        self.start_worker(
            image_files,
            output_dir,
            calibrations,
            settings
        )

    # ========================================================
    # START WORKER
    # ========================================================

    def start_worker(
        self,
        image_files,
        output_dir,
        calibrations,
        settings
    ):

        # ----------------------------------------------------
        # Create thread
        # ----------------------------------------------------

        self.thread = QThread()

        # ----------------------------------------------------
        # Create worker
        # ----------------------------------------------------

        self.worker = AnalysisWorker(
            image_files,
            output_dir,
            calibrations,
            settings
        )

        # ----------------------------------------------------
        # Move worker
        # ----------------------------------------------------

        self.worker.moveToThread(
            self.thread
        )

        # ====================================================
        # SIGNALS
        # ====================================================

        self.worker.log_message.connect(
            self.log
        )

        self.worker.progress.connect(
            self.progress_bar.setValue
        )

        self.worker.overlay_ready.connect(
            self.show_overlay
        )

        self.worker.finished.connect(
            self.analysis_finished
        )

        self.worker.error.connect(
            self.analysis_error
        )

        self.worker.cancelled.connect(
            self.analysis_cancelled
        )

        # ----------------------------------------------------
        # Start worker when thread starts
        # ----------------------------------------------------

        self.thread.started.connect(
            self.worker.run
        )

        # ----------------------------------------------------
        # Start
        # ----------------------------------------------------

        self.thread.start()

        self.cancel_button.setEnabled(
            True
        )

        self.log(
            "Analysis is running."
        )

    # ========================================================
    # SHOW OVERLAY
    # ========================================================

    def show_overlay(
        self,
        filename,
        overlay,
        detected,
        positive,
        negative
    ):

        # ====================================================
        # ADD RESULT TO TABLE
        # ====================================================

        row = (
            self.results_table.rowCount()
        )

        self.results_table.insertRow(
            row
        )

        # ----------------------------------------------------
        # Percentage
        # ----------------------------------------------------

        if detected > 0:

            positive_percentage = (
                positive
                /
                detected
                *
                100
            )

        else:

            positive_percentage = 0.0

        # ----------------------------------------------------
        # Table values
        # ----------------------------------------------------

        values = [

            filename,

            str(detected),

            str(positive),

            str(negative),

            f"{positive_percentage:.2f}%",

        ]

        for column, value in enumerate(
            values
        ):

            item = QTableWidgetItem(
                value
            )

            if column > 0:

                item.setTextAlignment(
                    Qt.AlignCenter
                )

            self.results_table.setItem(
                row,
                column,
                item
            )

        # ----------------------------------------------------
        # Select newest row
        # ----------------------------------------------------

        self.results_table.selectRow(
            row
        )

        # ====================================================
        # CREATE OVERLAY FRAME
        # ====================================================

        frame = QFrame()

        frame.setFrameShape(
            QFrame.StyledPanel
        )

        frame.setFrameShadow(
            QFrame.Raised
        )

        frame_layout = QVBoxLayout(
            frame
        )

        # ====================================================
        # IMAGE NAME
        # ====================================================

        name_label = QLabel(
            filename
        )

        name_label.setAlignment(
            Qt.AlignCenter
        )

        name_label.setStyleSheet(
            """
            QLabel {
                font-size: 18px;
                font-weight: bold;
                padding: 8px;
            }
            """
        )

        frame_layout.addWidget(
            name_label
        )

        # ====================================================
        # IMAGE
        # ====================================================

        image_label = QLabel()

        image_label.setAlignment(
            Qt.AlignCenter
        )

        image_label.setMinimumSize(
            500,
            400
        )

        image_label.setStyleSheet(
            """
            QLabel {
                background-color: black;
                border: 1px solid gray;
            }
            """
        )

        # ----------------------------------------------------
        # Get image dimensions
        # ----------------------------------------------------

        height, width, channels = (
            overlay.shape
        )

        bytes_per_line = (
            channels
            *
            width
        )

        # ----------------------------------------------------
        # NumPy RGB → QImage
        # ----------------------------------------------------

        q_image = QImage(
            overlay.data,
            width,
            height,
            bytes_per_line,
            QImage.Format_RGB888
        )

        # ----------------------------------------------------
        # Independent copy
        # ----------------------------------------------------

        q_image = q_image.copy()

        # ----------------------------------------------------
        # QImage → QPixmap
        # ----------------------------------------------------

        pixmap = QPixmap.fromImage(
            q_image
        )

        # ----------------------------------------------------
        # Scale preview
        # ----------------------------------------------------

        scaled_pixmap = pixmap.scaled(
            700,
            500,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )

        image_label.setPixmap(
            scaled_pixmap
        )

        frame_layout.addWidget(
            image_label
        )

        # ====================================================
        # RESULT LABEL
        # ====================================================

        result_label = QLabel(

            f"Detected cells: {detected}    |    "
            f"c-Fos+ : {positive}    |    "
            f"c-Fos- : {negative}    |    "
            f"c-Fos+ : {positive_percentage:.2f}%"

        )

        result_label.setAlignment(
            Qt.AlignCenter
        )

        result_label.setStyleSheet(
            """
            QLabel {
                font-size: 16px;
                font-weight: bold;
                padding: 8px;
            }
            """
        )

        frame_layout.addWidget(
            result_label
        )

        # ====================================================
        # ADD TO GALLERY
        # ====================================================

        self.overlay_layout.addWidget(
            frame
        )

        # ----------------------------------------------------
        # Scroll to newest image
        # ----------------------------------------------------

        QApplication.processEvents()

        scrollbar = (
            self.scroll_area.verticalScrollBar()
        )

        scrollbar.setValue(
            scrollbar.maximum()
        )

    # ========================================================
    # CANCEL
    # ========================================================

    def cancel_analysis(
        self
    ):

        if self.worker is None:

            return

        self.log(
            "Cancellation requested..."
        )

        self.worker.request_cancel()

        self.cancel_button.setEnabled(
            False
        )

    # ========================================================
    # ANALYSIS FINISHED
    # ========================================================

    def analysis_finished(
        self
    ):

        self.progress_bar.setValue(
            100
        )

        self.log(
            ""
        )

        self.log(
            "================================"
        )

        self.log(
            "ANALYSIS COMPLETE"
        )

        self.log(
            "================================"
        )

        self.cleanup_worker()

        self.start_button.setEnabled(
            True
        )

        self.reset_button.setEnabled(
            True
        )

        self.cancel_button.setEnabled(
            False
        )

        self.open_output_button.setEnabled(
            True
        )

        self.set_settings_enabled(
            True
        )

        QMessageBox.information(
            self,
            "Analysis complete",
            "The analysis has finished successfully."
        )

    # ========================================================
    # ERROR
    # ========================================================

    def analysis_error(
        self,
        error_text
    ):

        self.log(
            ""
        )

        self.log(
            "ERROR DURING ANALYSIS:"
        )

        self.log(
            error_text
        )

        self.cleanup_worker()

        self.start_button.setEnabled(
            True
        )

        self.reset_button.setEnabled(
            True
        )

        self.cancel_button.setEnabled(
            False
        )

        self.set_settings_enabled(
            True
        )

        QMessageBox.critical(
            self,
            "Analysis error",
            "An error occurred during analysis.\n\n"
            "See the Status window for details."
        )

    # ========================================================
    # CANCELLED
    # ========================================================

    def analysis_cancelled(
        self
    ):

        self.log(
            ""
        )

        self.log(
            "Analysis cancelled by user."
        )

        self.cleanup_worker()

        self.start_button.setEnabled(
            True
        )

        self.reset_button.setEnabled(
            True
        )

        self.cancel_button.setEnabled(
            False
        )

        self.set_settings_enabled(
            True
        )

    # ========================================================
    # CLEANUP WORKER
    # ========================================================

    def cleanup_worker(
        self
    ):

        if self.thread is None:

            return

        self.thread.quit()

        self.thread.wait()

        self.worker = None

        self.thread = None

    # ========================================================
    # OPEN OUTPUT FOLDER
    # ========================================================

    def open_output_folder(
        self
    ):

        if self.current_output_dir is None:

            return

        if not self.current_output_dir.exists():

            return

        # ----------------------------------------------------
        # Windows
        # ----------------------------------------------------

        if sys.platform == "win32":

            os.startfile(
                str(
                    self.current_output_dir
                )
            )

        # ----------------------------------------------------
        # macOS
        # ----------------------------------------------------

        elif sys.platform == "darwin":

            os.system(
                f'open "{self.current_output_dir}"'
            )

        # ----------------------------------------------------
        # Linux
        # ----------------------------------------------------

        else:

            os.system(
                f'xdg-open "{self.current_output_dir}"'
            )

    # ========================================================
    # RESET APPLICATION
    # ========================================================

    def reset_application(
        self
    ):

        # ----------------------------------------------------
        # Don't reset while worker is running.
        # ----------------------------------------------------

        if self.worker is not None:

            QMessageBox.warning(
                self,
                "Analysis running",
                "Please wait until the analysis "
                "has finished or cancel it first."
            )

            return

        # ----------------------------------------------------
        # Clear results
        # ----------------------------------------------------

        self.clear_overlays()

        self.clear_results_table()

        self.progress_bar.setValue(
            0
        )

        # ----------------------------------------------------
        # Clear log
        # ----------------------------------------------------

        self.status_text.clear()

        self.log(
            "Ready."
        )

        # ----------------------------------------------------
        # Reset output state
        # ----------------------------------------------------

        self.current_output_dir = None

        self.open_output_button.setEnabled(
            False
        )

        # ----------------------------------------------------
        # Reset controls
        # ----------------------------------------------------

        self.start_button.setEnabled(
            True
        )

        self.reset_button.setEnabled(
            True
        )

        self.cancel_button.setEnabled(
            False
        )

        self.set_settings_enabled(
            True
        )

    # ========================================================
    # CLOSE APPLICATION
    # ========================================================

    def closeEvent(
        self,
        event
    ):

        # ----------------------------------------------------
        # If analysis is running, ask user.
        # ----------------------------------------------------

        if self.worker is not None:

            answer = QMessageBox.question(
                self,
                "Analysis running",
                "An analysis is still running.\n\n"
                "Do you want to stop it and close "
                "the application?"
            )

            if answer != QMessageBox.Yes:

                event.ignore()

                return

            self.worker.request_cancel()

            self.cleanup_worker()

        event.accept()


# ============================================================
# STARTUP SPLASH SCREEN
# ============================================================

def create_splash():

    # --------------------------------------------------------
    # Create basic widget
    # --------------------------------------------------------

    splash = QWidget()

    # --------------------------------------------------------
    # Remove normal window frame
    # --------------------------------------------------------

    splash.setWindowFlags(
        Qt.FramelessWindowHint
    )

    # --------------------------------------------------------
    # Window size
    # --------------------------------------------------------

    splash.setFixedSize(
        520,
        300
    )

    # --------------------------------------------------------
    # Appearance
    # --------------------------------------------------------

    splash.setStyleSheet(
        """
        QWidget {
            background-color: #202124;
            border: 1px solid #444444;
        }

        QLabel {
            color: white;
        }

        QProgressBar {
            border: none;
            border-radius: 5px;
            background-color: #3c4043;
            height: 10px;
        }

        QProgressBar::chunk {
            background-color: #4caf50;
            border-radius: 5px;
        }
        """
    )

    # --------------------------------------------------------
    # Layout
    # --------------------------------------------------------

    layout = QVBoxLayout(
        splash
    )

    layout.setContentsMargins(
        40,
        35,
        40,
        35
    )

    layout.setSpacing(
        15
    )

    # ========================================================
    # TITLE
    # ========================================================

    title = QLabel(
        "c-Fos Cell Counter"
    )

    title.setAlignment(
        Qt.AlignCenter
    )

    title.setStyleSheet(
        """
        QLabel {
            font-size: 30px;
            font-weight: bold;
            color: white;
            border: none;
        }
        """
    )

    layout.addWidget(
        title
    )

    # ========================================================
    # SUBTITLE
    # ========================================================

    subtitle = QLabel(
        "Automated cell detection and c-Fos classification"
    )

    subtitle.setAlignment(
        Qt.AlignCenter
    )

    subtitle.setStyleSheet(
        """
        QLabel {
            font-size: 13px;
            color: #bdbdbd;
            border: none;
        }
        """
    )

    layout.addWidget(
        subtitle
    )

    layout.addStretch()

    # ========================================================
    # STATUS
    # ========================================================

    status = QLabel(
        "Starting application..."
    )

    status.setAlignment(
        Qt.AlignCenter
    )

    status.setStyleSheet(
        """
        QLabel {
            font-size: 14px;
            color: #eeeeee;
            border: none;
        }
        """
    )

    layout.addWidget(
        status
    )

    # ========================================================
    # PROGRESS BAR
    # ========================================================

    progress = QProgressBar()

    progress.setMinimum(
        0
    )

    progress.setMaximum(
        100
    )

    progress.setValue(
        0
    )

    progress.setTextVisible(
        False
    )

    layout.addWidget(
        progress
    )

    # ========================================================
    # VERSION / STATUS
    # ========================================================

    version = QLabel(
        "Initializing..."
    )

    version.setAlignment(
        Qt.AlignCenter
    )

    version.setStyleSheet(
        """
        QLabel {
            font-size: 11px;
            color: #888888;
            border: none;
        }
        """
    )

    layout.addWidget(
        version
    )

    return (
        splash,
        status,
        progress,
        version
    )


# ============================================================
# APPLICATION
# ============================================================

def main():

    # ========================================================
    # CREATE APPLICATION
    # ========================================================

    app = QApplication(
        sys.argv
    )

    # ========================================================
    # CREATE SPLASH
    # ========================================================

    (
        splash,
        status,
        progress,
        version
    ) = create_splash()

    # --------------------------------------------------------
    # Show splash
    # --------------------------------------------------------

    splash.show()

    # --------------------------------------------------------
    # Force Qt to actually display it
    # before loading heavy modules
    # --------------------------------------------------------

    app.processEvents()

    # ========================================================
    # LOAD IMAGE ANALYSIS
    # ========================================================

    status.setText(
        "Loading image analysis..."
    )

    progress.setValue(
        15
    )

    version.setText(
        "Loading image processing modules"
    )

    app.processEvents()

    # --------------------------------------------------------
    # Import analysis module
    # --------------------------------------------------------

    global load_image

    from analysis import load_image

    # ========================================================
    # LOAD CALIBRATION
    # ========================================================

    status.setText(
        "Loading calibration system..."
    )

    progress.setValue(
        35
    )

    version.setText(
        "Preparing manual calibration"
    )

    app.processEvents()

    # --------------------------------------------------------
    # Import calibration module
    # --------------------------------------------------------

    global calibrate_image

    from calibration import calibrate_image

    # ========================================================
    # LOAD ANALYSIS WORKER
    # ========================================================

    status.setText(
        "Loading cell detection engine..."
    )

    progress.setValue(
        55
    )

    version.setText(
        "Initializing StarDist / TensorFlow"
    )

    app.processEvents()

    # --------------------------------------------------------
    # Import worker module
    # --------------------------------------------------------

    global AnalysisWorker

    from worker import AnalysisWorker

    # ========================================================
    # PREPARE USER INTERFACE
    # ========================================================

    status.setText(
        "Preparing user interface..."
    )

    progress.setValue(
        80
    )

    version.setText(
        "Building application interface"
    )

    app.processEvents()

    # ========================================================
    # CREATE MAIN WINDOW
    # ========================================================

    window = MainWindow()

    # ========================================================
    # FINALIZATION
    # ========================================================

    status.setText(
        "Application ready!"
    )

    progress.setValue(
        100
    )

    version.setText(
        "Ready"
    )

    app.processEvents()

    # --------------------------------------------------------
    # Show main window and close splash
    # --------------------------------------------------------

    window.show()

    splash.close()

    # ========================================================
    # START APPLICATION
    # ========================================================

    sys.exit(
        app.exec()
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()
