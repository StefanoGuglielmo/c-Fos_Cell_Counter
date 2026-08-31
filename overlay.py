import numpy as np
from skimage.segmentation import find_boundaries


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
# CREATE CLASSIFICATION OVERLAY
# ============================================================

def create_overlay(
    image: np.ndarray,
    labels: np.ndarray,
    df
) -> np.ndarray:

    # --------------------------------------------------------
    # Original image
    # --------------------------------------------------------

    base = normalize(image)

    # Convert grayscale → RGB
    overlay = np.stack(
        [base, base, base],
        axis=-1
    )

    # --------------------------------------------------------
    # Find positive cell labels
    # --------------------------------------------------------

    positive_labels = set(
        df.loc[
            df["cFos_positive"],
            "label"
        ].astype(int)
    )

    # --------------------------------------------------------
    # Find boundaries of all cells
    # --------------------------------------------------------

    boundaries = find_boundaries(
        labels,
        mode="outer"
    )

    # Labels corresponding to every boundary pixel
    boundary_labels = labels[
        boundaries
    ]

    # --------------------------------------------------------
    # Find positive boundaries
    # --------------------------------------------------------

    positive_boundary = np.isin(
        boundary_labels,
        list(positive_labels)
    )

    # Coordinates of all boundaries
    rows, cols = np.where(
        boundaries
    )

    # ========================================================
    # 1. DRAW NEGATIVE CELLS BLUE
    # ========================================================

    overlay[
        rows[~positive_boundary],
        cols[~positive_boundary]
    ] = [
        0.0,
        0.0,
        1.0
    ]

    # ========================================================
    # 2. FILL POSITIVE CELLS RED
    # ========================================================

    # Create mask containing the complete positive cells.
    positive_mask = np.isin(
        labels,
        list(positive_labels)
    )

    # Transparency of red fill.
    #
    # 0.0 = no red
    # 1.0 = completely red
    alpha = 0.60

    # Red color.
    red = np.array(
        [
            1.0,
            0.0,
            0.0
        ],
        dtype=np.float32
    )

    # Blend red with the original image.
    overlay[
        positive_mask
    ] = (
        alpha * red
        +
        (1 - alpha)
        * overlay[
            positive_mask
        ]
    )

    # ========================================================
    # 3. DRAW POSITIVE BOUNDARIES RED
    # ========================================================

    # IMPORTANT:
    #
    # Positive boundaries are drawn AFTER the blue boundaries.
    #
    # Therefore blue can never cover the red boundary.

    overlay[
        rows[positive_boundary],
        cols[positive_boundary]
    ] = [
        1.0,
        0.0,
        0.0
    ]

    # ========================================================
    # 4. CONVERT TO 8-BIT IMAGE
    # ========================================================

    overlay = (
        overlay * 255
    ).clip(
        0,
        255
    ).astype(
        np.uint8
    )

    return overlay