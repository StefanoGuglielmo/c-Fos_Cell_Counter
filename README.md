# c-Fos Cell Counter

A Python application for automated detection and quantification of c-Fos-positive (c-Fos+) cells in fluorescence TIFF images.

The application uses [StarDist](https://github.com/stardist/stardist) for cell detection and provides an interactive calibration procedure for classification of detected cells based on fluorescence intensity and cell area.

## Features

* Automated cell detection using StarDist
* Detection of c-Fos+ and c-Fos− cells
* Interactive manual calibration
* Automatic analysis of multiple TIFF images
* Visual overlay of cell classification
* Export of analysis results
* Windows standalone executable available

## Installation

There are two ways to use c-Fos Cell Counter.

### Option 1 - Windows executable

The easiest option for Windows users is to download the latest release:

**[Download the latest Windows release](../../releases/latest)**

Download the ZIP file, extract it, and run:

```text
c-Fos_Cell_Counter.exe
```

Python and Conda are not required when using the standalone Windows version.

### Option 2 - Run from Python

This option is intended for users who want to run or modify the source code.

#### Requirements

* Anaconda or Miniconda
* Python 3.9

#### Create the environment

Clone the repository:

```bash
git clone https://github.com/StefanoGuglielmo/c-Fos_Cell_Counter.git
cd c-Fos_Cell_Counter
```

Create the Conda environment:

```bash
conda env create -f environment.yml
```

Activate it:

```bash
conda activate cfos_counter
```

Run the application:

```bash
python app.py
```

## Example data

Example TIFF images are provided in:

```text
example/input/
```

The application can be tested using these images.

The corresponding output directory is:

```text
example/output/
```

## Model

The application uses the StarDist `2D_versatile_fluo` model for cell detection.

The model configuration and weights required by the application are included in:

```text
model/2D_versatile_fluo/
```

## Workflow

The general workflow is:

1. Load fluorescence TIFF images.
2. Detect cells using StarDist.
3. Perform manual calibration using representative c-Fos+ cells.
4. Determine classification thresholds.
5. Classify detected cells as c-Fos+ or c-Fos−.
6. Generate an overlay for visual inspection.
7. Save the analysis results.

## Usage

### 1. Configure the analysis

After opening the application, select the input folder containing the images to be analyzed and the output folder where the results will be saved.

The input images must be TIFF files, containing one channel and one Z-plane (red square).

The user can also modify the classification settings, including the number of calibration cells and the parameters used for c-Fos classification (blue square).

<img src="example/screenshots/app.png" width="1000">

### 2. Manual c-Fos calibration

Select representative c-Fos-positive cells to calibrate the analysis. For each calibration cell, left-click on one edge of the cell and then left-click on the opposite edge to define its diameter.

The application measures the fluorescence intensity and size of the selected cells and uses these measurements to determine the classification thresholds.

<img src="example/screenshots/calibration.png" width="1000">

### 3. Analyze and inspect the results

After calibration, the application automatically detects cells using StarDist and classifies them as c-Fos-positive or c-Fos-negative based on the calibration parameters.

The detected cells and their classification are displayed as an overlay on the original fluorescence image, allowing the results to be visually inspected directly in the application.

<img src="example/screenshots/app_results.png" width="1000">

### 4. Export the image results

The application exports the analysis results as image files, including an overlay of the entire image and a mask containing the detected c-Fos-positive cells.

<img src="example/screenshots/exported_overlay.png" width="1000">

### 5. Export the results

The application exports the analysis results as a CSV file, containing the measurements and classification results for the detected cells.

<img src="example/screenshots/results_csv.png" width="1000">

## Reproducibility

The Python environment is specified in `environment.yml`.

The application was developed and tested using:

* Python 3.9.23
* TensorFlow 2.10.0
* StarDist 0.9.2
* NumPy 1.23.5
* OpenCV 4.10.0.84
* PySide6 6.9.1
* scikit-image 0.24.0
* pandas 2.3.1
* matplotlib 3.9.4

## Citation

If you use cFos Counter in your research, please cite this repository.

## License

See `LICENSE` for the terms under which this software is distributed.
