"""!
Copyright (c) Fraunhofer MEVIS, Germany. All rights reserved.
The software is not qualified for use as a medical product or as part
thereof. No bugs or restrictions are known.
"""

import matplotlib.pyplot as plt
import numpy
import streamlit

from image_utils import get_default_image_slice, load_dicom_volume, select_image_source
from parameter.quality_index import QualityIndex


streamlit.title("Universal Quality Index")


streamlit.write(
    "The Universal Quality Index (UQI) is computed by modeling any image distortion as a combination of three factors:"
)

streamlit.markdown("""
- loss of correlation
- luminance distortion
- contrast distortion
""")

streamlit.write("The dynamic range of UQI is between [0, 1]")


streamlit.subheader("Computation of UQI")

streamlit.write("The Computation of the UQI is based on the mean gray values of: ")

streamlit.markdown("""                
- the original image
- the edge-reinforced image
- the Median-difference image
""")


streamlit.graphviz_chart("""
digraph {
    rankdir=LR;
    node [shape=rect, style=filled, fontname="Helvetica"]

    orig [label="Original image", fillcolor="#DCE6F2"]
                         
    muO [label="μ_O", fillcolor="#C7E6C7"]
                         
    lap [label="Laplace filter", fillcolor="#F6C28B"]
    abs [label="Absolute filter", fillcolor="#F6C28B"]
    muL [label="μ_L", fillcolor="#C7E6C7"]

    med [label="Median filter", fillcolor="#F6C28B"]
    sub [label="Subtraction from original", fillcolor="#F6C28B"]
    muM [label="μ_M", fillcolor="#C7E6C7"]

    orig -> muO
    orig -> lap -> abs -> muL
    orig -> med -> sub -> muM
}
""")


file_source = select_image_source(
    "Upload your own MR image file or PNG image to compute the quality index.",
    "Or choose a demo example file from the images folder:",
)

volume, load_error = load_dicom_volume(file_source)
if load_error is not None:
    streamlit.error(f"Unable to read the selected image file: {load_error}")

if volume is None:
    streamlit.info("No image loaded. Upload or choose a demo file to compute the quality index.")
    streamlit.stop()

image = get_default_image_slice(volume)

# Normalization 0-255
pixel_min, pixel_max = image.min(), image.max()
image_norm = ((image - pixel_min) / (pixel_max - pixel_min) * 255).astype(numpy.uint8)

# Filters
_, laplace_norm = QualityIndex(image_norm).laplace_filter()
median, median_norm = QualityIndex(image_norm).median_filter()


fig, axes = plt.subplots(2, 3, figsize=(15, 8))

# fig, axes = plt.subplots(2, 4, figsize=(20, 8))

# MR images: original and filtered

axes[0, 0].imshow(image_norm, cmap="gray", vmin=0, vmax=255)
axes[0, 0].set_title("Original")
axes[0, 0].axis("off")

axes[0, 1].imshow(laplace_norm, cmap="gray", vmin=0, vmax=255)
axes[0, 1].set_title("Laplace filtered")
axes[0, 1].axis("off")

axes[0, 2].imshow(median_norm, cmap="gray", vmin=0, vmax=255)
axes[0, 2].set_title("Original − Median")
axes[0, 2].axis("off")

# corresponding histograms

axes[1, 0].hist(image_norm.ravel(), bins=256, range=(0, 255), color="gray")
axes[1, 0].set_xlim((0, 255))
axes[1, 0].set_ylabel("Frequency")

axes[1, 1].hist(laplace_norm.ravel(), bins=256, range=(0, 255), color="gray")
axes[1, 1].set_xlim((0, 255))

axes[1, 2].hist(median_norm.ravel(), bins=256, range=(0, 255), color="gray")
axes[1, 2].set_xlim((0, 255))

for ax in axes[1, :]:
    ax.set_xlabel("Gray value")

plt.tight_layout()
streamlit.pyplot(fig)


streamlit.write(
    "**Edge-reinforced Image**  \n"
    "Edge detection is performed by convolving the image with a Laplace kernel with −4 as the central element. " \
    "The Laplace operator is a second-order derivative and responds strongly to " \
    "rapid local intensity changes while suppressing slowly varying regions. "
    "This emphasizes anatomical boundaries and fine structural details in MR images.  \n\n"
    "After filtering, the absolute value is taken to remove sign information, "
    "so that only the magnitude of local intensity changes remains. "
    "As a result, the image represents edge strength rather than edge direction.  \n\n"
    "In the context of MR image quality assessment, the mean gray value of the "
    "Laplace-filtered image reflects the global amount of high-frequency content, "
    "which is associated with image sharpness and spatial detail, but may also include contributions from noise."
)

streamlit.write(
    "**Median-difference image**  \n"
    "First, the original image is smoothed using a median filter, which suppresses impulse-like noise "
    "and small local intensity fluctuations while preserving edges. " \
    "The median-filtered image represents a locally robust estimate of the underlying signal.  \n\n"
    "The median-difference image is obtained by subtracting this smoothed image from the original image. " \
    "The resulting difference image highlights local intensity components that are not explained " \
    "by the median filter, such as noise, fine texture or small-scale inconsistencies.  \n\n"
    "For MR images, the mean gray value of the median-difference image can be interpreted as a measure " \
    "of local instability or noise content and therefore acts as a penalizing term in the Universal Quality Index."
)


streamlit.markdown("#### Mathematical Definition of the UQI")


streamlit.latex(r"\mathrm{UQI} = (1 - (\frac{\mu^2_M}{\mu^2_O})^\frac{1}{3}) * \frac{\mu_L}{\mu_O}")

streamlit.latex(
    r"""
    \begin{aligned}
    \mu_O &:\ \text{mean gray value of the original image} \\
    \mu_L &:\ \text{mean gray value of the Laplace-filtered image} \\
    \mu_M &:\ \text{mean gray value of the Median-difference image}
    \end{aligned}
    """
)


button_left, space, button_right = streamlit.columns([1, 1, 1])

with button_left:
    if streamlit.button("← Quality Parameter"):
        streamlit.switch_page("pages/2_Quality_Parameter.py")

with button_right:
    if streamlit.button("Sharpness →"):
        streamlit.switch_page("pages/4_Sharpness.py")


streamlit.divider()

with streamlit.expander("**Literature**"):

    sources = [
        "Wang, Z., & Bovik, A. C. (2002). A universal image quality index. IEEE signal processing letters, 9(3), 81-84."
    ]

    for i in range(len(sources)):
        num, cite = streamlit.columns([1.25,20])
        with num:
            streamlit.write(f"[{i+1}]")
        with cite:
            streamlit.write(sources[i])
