"""!
Copyright (c) Fraunhofer MEVIS, Germany. All rights reserved.
The software is not qualified for use as a medical product or as part
thereof. No bugs or restrictions are known.
"""

import streamlit as st

k_space = st.Page("pages/1_k-space.py", title="k-Space")
signals = st.Page("pages/2_Signals.py", title="Signals")
spatial_frequencies = st.Page("pages/3_Spatial_Frequencies.py", title="Spatial Frequencies")
fourier_transf = st.Page("pages/4_Fourier_Transform.py", title="Fourier Transform")
example_fourier_transf = st.Page("pages/5_Example_Fourier_Transform.py", title="Example Fourier Transform")
sampling = st.Page("pages/6_Sampling.py", title="Sampling")
ksp_trajectories = st.Page("pages/7_k-space_trajectories.py", title="k-Space Trajectories")
artifacts = st.Page("pages/8_Artifacts.py", title="Artifacts")

reconstruction = st.Page("pages/9_Reconstruction.py", title="Introduction")
partial_fourier = st.Page("pages/10_Partial_Fourier_Imaging.py", title="Partial Fourier")
pmri = st.Page("pages/11_Parallel_Imaging.py", title="Parallel Imaging")
receiver_coils = st.Page("pages/12_Receiver_Coils.py", title="\u2003▸\u2002Receiver Coils")
pmri_review = st.Page("pages/13_Parallel_Imaging_Chapter_Review.py", title="\u2003▸\u2002Parallel Imaging - Chapter Review")
epi = st.Page("pages/14_EPI.py", title="Echo Planar Imaging")
compressed_sensing = st.Page("pages/15_Compressed_Sensing.py", title="Compressed Sensing")
cs_review = st.Page("pages/16_Compressed_Sensing_Chapter_Review.py", title="\u2003▸\u2002Compressed Sensing - Chapter Review")
recon_in_3d = st.Page("pages/17_Reconstruction_in_3D.py", title="Reconstruction in 3D")

qanda = st.Page("pages/18_Questions_and_Answers.py", title="Questions and Answers")
sources = st.Page("pages/19_Sources.py", title="Sources")

pg = st.navigation({
    "I n t r o d u c t i o n": [k_space],
    "F u n d a m e n t a l s": [signals, spatial_frequencies, fourier_transf, example_fourier_transf, sampling, ksp_trajectories, artifacts],
    "R e c o n s t r u c t i o n": [reconstruction, partial_fourier, pmri, receiver_coils, pmri_review, epi, compressed_sensing, cs_review, recon_in_3d],
    "Q & A and S o u r c e s": [qanda, sources]
})

pg.run()