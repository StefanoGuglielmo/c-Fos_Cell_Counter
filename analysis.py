from pathlib import Path

import cv2
import numpy as np
import pandas as pd
from skimage.measure import regionprops
from stardist.models import StarDist2D


# ============================================================
# DEFAULT SETTINGS
# ============================================================

N_REFERENCE_CELLS = 5

# StarDist
PROB_THRESH = 0.479071
NMS_THRESH = 0.30

# Classification
DIAMETER_MIN_FACTOR = 0.50
DIAMETER_MAX_FACTOR = 2.00
INTENSITY_FACTOR = 0.50


# ============================================================
# STARDIST MODEL
# ============================================================

MODEL_DIR = (
    Path(__file__).resolve().parent
    / "model"
    / "2D_versatile_fluo"
)

print(
    f"Loading StarDist model from:\n{MODEL_DIR}"
)

if not MODEL_DIR.exists():

    raise FileNotFoundError(
        f"StarDist model folder not found:\n{MODEL_DIR}"
    )

model = StarDist2D(
    None,
    name=MODEL_DIR.name,
    basedir=str(
        MODEL_DIR.parent
    )
)

print(
    "StarDist model loaded."
)


# ============================================================
# NORMALIZATION
# ============================================================

def normalize(image: np.ndarray) -> np.ndarray:

    image = image.astype(np.float32)

    mn = image.min()
    mx = image.max()

    if mx == mn:
        return np.zeros_like(image)

    return (image - mn) / (mx - mn)


# ============================================================
# LOAD IMAGE
# ============================================================

def load_image(image_path):

    image = cv2.imread(
        str(image_path),
        cv2.IMREAD_GRAYSCALE
    )

    if image is None:

        raise RuntimeError(
            f"Cannot read image: {image_path}"
        )

    return image


# ============================================================
# STARDIST SEGMENTATION
# ============================================================

def segment_image(
    image: np.ndarray,
    prob_thresh: float = PROB_THRESH,
    nms_thresh: float = NMS_THRESH
) -> np.ndarray:

    normalized = normalize(
        image
    )

    n_tiles = model._guess_n_tiles(
        normalized
    )

    labels, _ = model.predict_instances(
        normalized,
        n_tiles=n_tiles,
        prob_thresh=prob_thresh,
        nms_thresh=nms_thresh,
        show_tile_progress=False

    )

    return labels


# ============================================================
# MEASURE CELLS
# ============================================================

def measure_cells(
    image: np.ndarray,
    labels: np.ndarray
) -> pd.DataFrame:

    cells = []

    for region in regionprops(
        labels,
        intensity_image=image
    ):

        area = region.area

        diameter = (
            2 * np.sqrt(
                area / np.pi
            )
        )

        cells.append({

            "label":
                region.label,

            "x":
                region.centroid[1],

            "y":
                region.centroid[0],

            "area":
                area,

            "diameter":
                diameter,

            "mean_intensity":
                region.mean_intensity,

            "max_intensity":
                region.max_intensity,
        })

    return pd.DataFrame(
        cells
    )


# ============================================================
# CLASSIFICATION
# ============================================================

def classify_cells(
    df: pd.DataFrame,
    reference_diameter: float,
    reference_intensity: float,
    diameter_min_factor: float = DIAMETER_MIN_FACTOR,
    diameter_max_factor: float = DIAMETER_MAX_FACTOR,
    intensity_factor: float = INTENSITY_FACTOR
):

    # --------------------------------------------------------
    # Calculate allowed cell-size range
    # --------------------------------------------------------

    min_diameter = (
        reference_diameter
        *
        diameter_min_factor
    )

    max_diameter = (
        reference_diameter
        *
        diameter_max_factor
    )

    # --------------------------------------------------------
    # Calculate cFos intensity threshold
    # --------------------------------------------------------

    intensity_threshold = (
        reference_intensity
        *
        intensity_factor
    )

    # --------------------------------------------------------
    # Classify cells
    # --------------------------------------------------------

    df["cFos_positive"] = (

        (
            df["diameter"]
            >=
            min_diameter
        )

        &

        (
            df["diameter"]
            <=
            max_diameter
        )

        &

        (
            df["mean_intensity"]
            >=
            intensity_threshold
        )
    )

    return (
        df,
        min_diameter,
        max_diameter,
        intensity_threshold
    )


# ============================================================
# ANALYZE IMAGE
# ============================================================

def analyze_image(
    image_path,
    reference_diameter,
    reference_intensity,
    prob_thresh=PROB_THRESH,
    nms_thresh=NMS_THRESH,
    diameter_min_factor=DIAMETER_MIN_FACTOR,
    diameter_max_factor=DIAMETER_MAX_FACTOR,
    intensity_factor=INTENSITY_FACTOR
):

    image_path = Path(
        image_path
    )

    print(
        f"\nProcessing: {image_path.name}"
    )

    # --------------------------------------------------------
    # Load
    # --------------------------------------------------------

    image = load_image(
        image_path
    )

    # --------------------------------------------------------
    # Segmentation
    # --------------------------------------------------------

    print(
        "Running StarDist..."
    )

    labels = segment_image(
        image,
        prob_thresh=prob_thresh,
        nms_thresh=nms_thresh
    )

    # --------------------------------------------------------
    # Measurements
    # --------------------------------------------------------

    df = measure_cells(
        image,
        labels
    )

    print(
        f"Cells detected: {len(df)}"
    )

    # --------------------------------------------------------
    # Classification
    # --------------------------------------------------------

    (
        df,
        min_diameter,
        max_diameter,
        intensity_threshold
    ) = classify_cells(
        df,
        reference_diameter,
        reference_intensity,
        diameter_min_factor=diameter_min_factor,
        diameter_max_factor=diameter_max_factor,
        intensity_factor=intensity_factor
    )

    positive = int(
        df[
            "cFos_positive"
        ].sum()
    )

    negative = (
        len(df)
        -
        positive
    )

    print(
        f"cFos+ cells: {positive}"
    )

    print(
        f"cFos- cells: {negative}"
    )

    # --------------------------------------------------------
    # Results
    # --------------------------------------------------------

    return {

        "image":
            image,

        "labels":
            labels,

        "dataframe":
            df,

        "reference_diameter":
            reference_diameter,

        "reference_intensity":
            reference_intensity,

        "min_diameter":
            min_diameter,

        "max_diameter":
            max_diameter,

        "intensity_threshold":
            intensity_threshold,

        "positive":
            positive,

        "negative":
            negative,
    }


# ============================================================
# SAVE CELL DATA
# ============================================================

def save_cell_data(
    result,
    output_dir,
    stem
):

    output_dir = Path(
        output_dir
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    df = result[
        "dataframe"
    ]

    path = (
        output_dir
        /
        f"{stem}_cells.csv"
    )

    df.to_csv(
        path,
        index=False
    )

    return path


# ============================================================
# CREATE POSITIVE MASK
# ============================================================

def create_positive_mask(
    labels,
    df
):

    positive_labels = (
        df.loc[
            df["cFos_positive"],
            "label"
        ]
        .astype(int)
        .values
    )

    mask = np.isin(
        labels,
        positive_labels
    )

    return (
        mask.astype(
            np.uint8
        )
        *
        255
    )