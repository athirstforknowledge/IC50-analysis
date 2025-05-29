# Python IC50/EC50 Analysis Tool

## Overview

This Python tool provides a straightforward way to calculate IC50 (half maximal inhibitory concentration) or EC50 (half maximal effective concentration) values from dose-response experimental data. It uses non-linear regression to fit a four-parameter logistic (4PL) model to the provided concentration and response values, and includes options for visualizing the curve fit.

This tool is designed for researchers who need a quick and reliable method to analyze dose-response assays, such as drug screening, enzyme kinetics, or cytotoxicity studies.

## Features

* **IC50/EC50 Calculation:** Employs the robust `scipy.optimize.curve_fit` for non-linear regression.
* **Four-Parameter Logistic Model (4PL):** Uses a standard sigmoidal model to describe the dose-response relationship:
    `Y = Bottom + (Top - Bottom) / (1 + (X / IC50)^HillSlope)`
* **Data Visualization:** Generates plots of the experimental data points and the fitted curve using `matplotlib`, with the IC50/EC50 value highlighted.
* **Customizable Initial Guesses:** Allows users to provide initial parameter guesses for the curve fitting algorithm.
* **Handles Both Inhibition and Stimulation Data:** Adapts to different data trends.

## Installation

### Prerequisites

* Python 3.7+
* The following Python packages (see `requirements.txt`):
    * `numpy`
    * `scipy`
    * `matplotlib`

### Steps

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/athirstforknowledge/IC50-analysis.git](https://github.com/athirstforknowledge/IC50-analysis.git)
    cd IC50-analysis
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Usage

You can use the `calculate_ic50` function from the `ic50_pkg.analyzer` module in your Python scripts.

*(We will add an example script or usage section here later)*

### Input Data Format

* **Concentrations:** A list or NumPy array of drug/compound concentrations (positive numerical values).
* **Responses:** A list or NumPy array of the corresponding experimental responses (numerical values).

### Interpreting Results

* **IC50/EC50:** The concentration that elicits 50% of the maximal response.
* **E\_min (Bottom):** The minimum response level.
* **E\_max (Top):** The maximum response level.
* **Hill Slope:** The steepness of the curve.

## Contributing

Contributions are welcome! If you'd like to contribute, please follow these steps:

1.  Fork the repository.
2.  Create a new branch (`git checkout -b feature/your-feature-name`).
3.  Make your changes and commit them (`git commit -m 'Add some feature'`).
4.  Push to the branch (`git push origin feature/your-feature-name`).
5.  Open a Pull Request.

## License

This project is licensed under the MIT License - see the `LICENSE` file for details (You may need to create a `LICENSE` file if one doesn't exist. The MIT license is a common, permissive choice).

## Acknowledgements

* Built using `numpy`, `scipy`, and `matplotlib`.