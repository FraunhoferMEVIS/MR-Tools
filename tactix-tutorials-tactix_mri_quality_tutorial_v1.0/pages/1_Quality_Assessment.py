"""!
Copyright (c) Fraunhofer MEVIS, Germany. All rights reserved.
The software is not qualified for use as a medical product or as part
thereof. No bugs or restrictions are known.
"""

import streamlit

streamlit.title("Image Quality Assessment in Magnetic Resonance Imaging")


streamlit.write(
    "*Magnetic Resonance Imaging* is one of the most important imaging modalities in modern medicine. " \
    "It enables non-invasive, high-resolution visualization of soft tissues and plays a central role in " \
    "the diagnosis, treatment planning and monitoring of numerous diseases. " \
    "However, the diagnostic value of MRI scans depends on their image quality. " \
    "Artifacts, noise, low contrast or motion blur can significantly impair image interpretation and may even lead to misdiagnosis."
)

streamlit.write(
    "*Image Quality Assessment* refers to the systematic process of evaluating the quality of medical images. " \
    "The goal is to quantitatively or qualitatively determine how suitable an image is for diagnostic or " \
    "further processing purposes. " \
    "In medical imaging —and particularly in MRI— QA is not merely a technical quality measure but a " \
    "clinically relevant factor, as image quality is directly linked to diagnostic accuracy, examination duration, " \
    "repeat scans and ultimately patient safety and comfort."
)

streamlit.write(
    "Traditionally, image quality has been assessed subjectively by radiologists, for example based on " \
    "visual criteria such as sharpness, contrast, noise or the visibility of anatomical structures. " \
    "While these subjective assessments are valuable, they are inherently affected by variability due to experience " \
    "and individual perception. To address these limitations, objective QA methods have been developed " \
    "that quantify image quality using measurable parameters such as signal-to-noise ratio, contrast-to-noise ratio, " \
    "sharpness measures or structural similarity metrics."
)

streamlit.write(
    "This tutorial provides an introduction to Image Quality Assessment for MRI data. " \
    "The focus is on classical quality parameters such as sharpness, signal-to-noise ratio and universal quality indices."
)


col1, col2 = streamlit.columns(2)

with col2:
    if streamlit.button("Quality Parameter"):
        streamlit.switch_page("pages/2_Quality_Parameter.py")


streamlit.divider()

with streamlit.expander("**Literature**"):

    sources = [
        "Herath, H. M. S. S., Herath, H. M. K. K. M. B., Madusanka, N., & Lee, B. I. (2025). A Systematic Review of Medical Image Quality Assessment. Journal of Imaging, 11(4), 100."
    ]

    for i in range(len(sources)):
        num, cite = streamlit.columns([1.25,20])
        with num:
            streamlit.write(f"[{i+1}]")
        with cite:
            streamlit.write(sources[i])
       