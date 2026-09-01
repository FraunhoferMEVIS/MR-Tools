# TACTIX k-space Tutorial v1.0

## Overview
This repository provides an implementation of k-space to help understand and simulate the data acquisition and image reconstruction process in Magnetic Resonance Imaging (MRI). The project covers key topics such as Fourier Transform, sampling, k-space trajectories, and reconstruction techniques.

## Structure
The repository is structured into the following sections:

1. **Signals** – Understanding the basic signals in MRI.
2. **Spatial Frequencies** – Exploring the role of spatial frequency components.
3. **Fourier Transform** – Explanation of the Fourier Transform in MRI.
4. **Example Fourier Transform** – Demonstration of Fourier Transform on sample data.
5. **Sampling** – Explanation of sampling and its impact on image reconstruction.
6. **K-space Trajectories** – Different methods for filling k-space, including Cartesian, radial, spiral, and zig-zag.
7. **Artifacts** – Common MRI artifacts and their causes.
8. **Reconstruction**
9. **Partial Fourier Imaging**
10. **Parallel Imaging** 
11. **EPI (Echo Planar Imaging)** 
12. **Compressed Sensing**
13. **Reconstruction in 3D**
14. **Questions and Answers**
15. **Sources**

## Installation
To run this project, ensure you have the required dependencies installed. The application is built using Python and requires Streamlit for interactive visualization.

### Prerequisites
Make sure you have the following installed:
- Python (>= 3.8)
- Streamlit
- scikit-image
- NumPy
- Matplotlib
- OpenCV
- IPython
- PyWavelets
- pydicom

You can install the dependencies using:
```bash
pip install streamlit numpy matplotlib opencv-python IPython scikit-image scikit-learn PyWavelets pydicom 
```
In addition, you need to download the source code of this repository as a zip file or clone the repository to the desired location. 

## Usage
This project uses Streamlit to create an interactive interface for visualizing k-space and MRI image reconstruction.

### Running the Application
To start the application, navigate to the project directory and run:
```bash
python -m streamlit run k-space_streamlit/app.py

```
This will launch a web-based interface where you can explore different k-space trajectories, sampling techniques, and reconstruction methods in real-time.

## Project Status
The project is currently in development, and more features will be added over time. Contributions and feedback are welcome!

