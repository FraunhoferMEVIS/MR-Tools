# MR Image Quality Assessment – Streamlit Tutorial

This repository contains a **Streamlit-based tutorial application** for image quality assessment (IQA) in **Magnetic Resonance Imaging (MRI)**.  
The app introduces classical image quality concepts and demonstrates how common quality parameters can be computed and interpreted using real MR image data.

---

## Getting Started

### 1. Clone the Repository

```bash
git clone <gitlab-repository-url>
cd <repository-folder>
```

It's recommended to keep the structure of the worktree for each branch, e.g. checkout this tutorial to a designated location using git worktree:

```bash
git worktree add ../MRI-QA-Tutorial MRI-QA-Tutorial
```

### 2. Create a Virtual Environment & Activate
Create it:

```bash
python -m venv .venv
```

Activate it:

- Windows

```bash
.venv\Scripts\activate
```

- Linux/macOS

```bash
source .venv/bin/activate
```

### 3. Install Requirements

```bash
pip install -r requirements.txt
```

### 4. Run the Application

From the repository root directory:

```bash
streamlit run app.py
```

or equivalently:

```bash
python -m streamlit run app.py
```

The application will open automatically in your default web browser.

---

## Application Structure

```text
.
├── app.py                     # Streamlit entry point
├── pages/                     # Streamlit multi-page tutorial
│   ├── 1_Quality_Assessment.py
│   ├── 2_Quality_Parameter.py
│   ├── 3_Quality_Index.py
│   ├── 4_Sharpness.py
│   ├── 5_SNR.py
│   └── 6_Image_Processing.py
│
├── parameter/                 # Core quality metric implementations
│   ├── huang_threshold.py     # Huang thresholding
│   ├── quality_index.py       # Universal Image Quality Index 
│   ├── sharpness.py           # Sharpness metric
│   └── snr.py                 # Signal-to-noise ratio 
│
├── images/                    # Example MR images (DICOM)
├── requirements.txt
└── README.md
```

---

## Tutorial Overview

The tutorial is organized as a **guided learning path**, accessible via the Streamlit sidebar:

1. **Quality Assessment**  
   Introduction and motivation for image quality assessment in MRI.

2. **Quality Parameters**  
   Upload a DICOM MR image and compute UQI, sharpness and SNR.

3. **Quality Index (UQI)**  
   Explanation and visualization of the Universal Image Quality Index.

4. **Sharpness**  
   Entropy-based sharpness estimation using Laplace filtering.

5. **Signal-to-Noise Ratio (SNR)**  
   Automatic foreground/background segmentation and noise estimation.

6. **Image Processing**  
   Fundamental concepts including histograms, thresholding, filtering, morphology and entropy.
