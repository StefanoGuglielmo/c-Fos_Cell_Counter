import traceback
from pathlib import Path

import cv2
import pandas as pd

from PySide6.QtCore import (
    QObject,
    Signal,
    Slot,
)

from analysis import (
    segment_image,
    measure_cells,
    classify_cells,
    create_positive_mask,
)

from overlay import create_overlay


# ============================================================
# ANALYSIS WORKER
# ============================================================

class AnalysisWorker(QObject):

    # --------------------------------------------------------
    # Signals
    # --------------------------------------------------------

    log_message = Signal(str)

    progress = Signal(int)

    finished = Signal()

    error = Signal(str)

    cancelled = Signal()

    overlay_ready = Signal(
        str,
        object,
        int,
        int,
        int
    )

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        image_files,
        output_dir,
        calibrations,
        settings,
    ):

        super().__init__()

        self.image_files = image_files

        self.output_dir = Path(
            output_dir
        )

        self.calibrations = calibrations

        self.settings = settings

        self._cancel_requested = False

    # ========================================================
    # REQUEST CANCELLATION
    # ========================================================

    @Slot()
    def request_cancel(
        self
    ):

        self._cancel_requested = True

    # ========================================================
    # LOG
    # ========================================================

    def log(
        self,
        message
    ):

        self.log_message.emit(
            message
        )

    # ========================================================
    # MAIN ANALYSIS
    # ========================================================

    @Slot()
    def run(
        self
    ):

        try:

            total = len(
                self.image_files
            )

            results = []

            self.log(
                "Background analysis started."
            )

            # =================================================
            # SHOW SETTINGS
            # =================================================

            self.log(
                ""
            )

            self.log(
                "Analysis settings:"
            )

            self.log(
                f"cFos intensity factor: "
                f"{self.settings['intensity_factor']:.3f}"
            )

            self.log(
                f"Minimum cell-size factor: "
                f"{self.settings['diameter_min_factor']:.3f}"
            )

            self.log(
                f"Maximum cell-size factor: "
                f"{self.settings['diameter_max_factor']:.3f}"
            )

            self.log(
                f"StarDist probability threshold: "
                f"{self.settings['prob_thresh']:.6f}"
            )

            self.log(
                f"StarDist NMS threshold: "
                f"{self.settings['nms_thresh']:.3f}"
            )

            self.log(
                f"Calibration cells: "
                f"{self.settings['n_reference_cells']}"
            )

            # =================================================
            # PROCESS EACH IMAGE
            # =================================================

            for index, image_path in enumerate(
                self.image_files
            ):

                # ---------------------------------------------
                # Check cancellation
                # ---------------------------------------------

                if self._cancel_requested:

                    self.cancelled.emit()

                    return

                # ---------------------------------------------
                # Image name
                # ---------------------------------------------

                filename = image_path.name

                self.log(
                    ""
                )

                self.log(
                    "=" * 60
                )

                self.log(
                    f"Processing "
                    f"{index + 1}/{total}: "
                    f"{filename}"
                )

                self.log(
                    "=" * 60
                )

                # ---------------------------------------------
                # Load image
                # ---------------------------------------------

                image = cv2.imread(
                    str(image_path),
                    cv2.IMREAD_GRAYSCALE
                )

                if image is None:

                    self.log(
                        "ERROR: Cannot read image."
                    )

                    continue

                # ---------------------------------------------
                # Calibration
                # ---------------------------------------------

                (
                    reference_diameter,
                    reference_intensity
                ) = self.calibrations[
                    image_path
                ]

                self.log(
                    f"Reference diameter: "
                    f"{reference_diameter:.2f} px"
                )

                self.log(
                    f"Reference intensity: "
                    f"{reference_intensity:.2f}"
                )

                # =============================================
                # STARDIST
                # =============================================

                self.log(
                    "Running StarDist..."
                )

                labels = segment_image(
                    image,

                    prob_thresh=
                    self.settings[
                        "prob_thresh"
                    ],

                    nms_thresh=
                    self.settings[
                        "nms_thresh"
                    ]
                )

                if self._cancel_requested:

                    self.cancelled.emit()

                    return

                # =============================================
                # MEASURE CELLS
                # =============================================

                df = measure_cells(
                    image,
                    labels
                )

                detected = len(
                    df
                )

                self.log(
                    f"Detected cells: "
                    f"{detected}"
                )

                # =============================================
                # CLASSIFICATION
                # =============================================

                (
                    df,
                    min_diameter,
                    max_diameter,
                    intensity_threshold
                ) = classify_cells(

                    df,

                    reference_diameter,

                    reference_intensity,

                    diameter_min_factor=
                    self.settings[
                        "diameter_min_factor"
                    ],

                    diameter_max_factor=
                    self.settings[
                        "diameter_max_factor"
                    ],

                    intensity_factor=
                    self.settings[
                        "intensity_factor"
                    ]
                )

                positive = int(
                    df[
                        "cFos_positive"
                    ].sum()
                )

                negative = (
                    detected
                    -
                    positive
                )

                self.log(
                    f"cFos+: {positive}"
                )

                self.log(
                    f"cFos-: {negative}"
                )

                # =============================================
                # CREATE OVERLAY
                # =============================================

                self.log(
                    "Creating overlay..."
                )

                overlay = create_overlay(
                    image,
                    labels,
                    df
                )

                stem = image_path.stem

                # =============================================
                # SAVE OVERLAY
                # =============================================

                overlay_path = (
                    self.output_dir
                    /
                    f"{stem}_overlay.tif"
                )

                overlay_bgr = cv2.cvtColor(
                    overlay,
                    cv2.COLOR_RGB2BGR
                )

                success = cv2.imwrite(
                    str(overlay_path),
                    overlay_bgr
                )

                if success:

                    self.log(
                        f"Overlay saved: "
                        f"{overlay_path.name}"
                    )

                else:

                    self.log(
                        "ERROR: Could not save overlay."
                    )

                # =============================================
                # SAVE CELL DATA
                # =============================================

                cells_path = (
                    self.output_dir
                    /
                    f"{stem}_cells.csv"
                )

                df.to_csv(
                    cells_path,
                    index=False
                )

                self.log(
                    f"Cell data saved: "
                    f"{cells_path.name}"
                )

                # =============================================
                # POSITIVE MASK
                # =============================================

                positive_mask = (
                    create_positive_mask(
                        labels,
                        df
                    )
                )

                positive_mask_path = (
                    self.output_dir
                    /
                    f"{stem}_positive_mask.tif"
                )

                success = cv2.imwrite(
                    str(positive_mask_path),
                    positive_mask
                )

                if success:

                    self.log(
                        f"Positive mask saved: "
                        f"{positive_mask_path.name}"
                    )

                else:

                    self.log(
                        "ERROR: Could not save "
                        "positive mask."
                    )

                # =============================================
                # SEND OVERLAY + RESULTS TO GUI
                # =============================================

                self.overlay_ready.emit(
                    filename,
                    overlay,
                    detected,
                    positive,
                    negative
                )

                # =============================================
                # ADD TO SUMMARY
                # =============================================

                results.append({

                    "File Name":
                        filename,

                    "Detected cells":
                        detected,

                    "cFos+ cells":
                        positive,

                    "cFos- cells":
                        negative,

                    "Reference diameter":
                        reference_diameter,

                    "Reference intensity":
                        reference_intensity,

                    "Min diameter":
                        min_diameter,

                    "Max diameter":
                        max_diameter,

                    "Intensity threshold":
                        intensity_threshold,

                    "cFos intensity factor":
                        self.settings[
                            "intensity_factor"
                        ],

                    "Min cell-size factor":
                        self.settings[
                            "diameter_min_factor"
                        ],

                    "Max cell-size factor":
                        self.settings[
                            "diameter_max_factor"
                        ],

                    "StarDist probability":
                        self.settings[
                            "prob_thresh"
                        ],

                    "StarDist NMS":
                        self.settings[
                            "nms_thresh"
                        ],

                    "Calibration cells":
                        self.settings[
                            "n_reference_cells"
                        ],
                })

                # =============================================
                # UPDATE PROGRESS
                # =============================================

                progress = int(
                    (
                        (index + 1)
                        /
                        total
                    )
                    *
                    100
                )

                self.progress.emit(
                    progress
                )

            # =================================================
            # SAVE SUMMARY
            # =================================================

            summary = pd.DataFrame(
                results
            )

            summary_path = (
                self.output_dir
                /
                "summary.csv"
            )

            summary.to_csv(
                summary_path,
                index=False
            )

            self.log(
                ""
            )

            self.log(
                "=" * 60
            )

            self.log(
                "ANALYSIS COMPLETE"
            )

            self.log(
                "=" * 60
            )

            self.log(
                f"Processed images: "
                f"{len(results)}"
            )

            self.log(
                f"Summary saved: "
                f"{summary_path.name}"
            )

            self.finished.emit()

        except Exception:

            error_text = traceback.format_exc()

            self.error.emit(
                error_text
            )