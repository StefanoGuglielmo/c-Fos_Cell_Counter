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

## Project structure

```text
cFos_Counter/
│
├── model/
│   └── 2D_versatile_fluo/
│
├── example/
│   ├── input/
│   └── output/
│
├── app.py
├── analysis.py
├── calibration.py
├── overlay.py
├── worker.py
├── environment.yml
├── README.md
├── LICENSE
└── .gitignore
```

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
