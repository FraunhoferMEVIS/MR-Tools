"""!
Copyright (c) Fraunhofer MEVIS, Germany. All rights reserved.
The software is not qualified for use as a medical product or as part
thereof. No bugs or restrictions are known.
"""

import matplotlib.pyplot as plt
import numpy
import skimage
import streamlit

from image_utils import get_default_image_slice, load_dicom_volume, select_image_source
from parameter.sharpness import Sharpness


streamlit.title("Sharpness")


streamlit.write(
    "In MRI, *sharpness* describes the ability of an image to represent spatial details with " \
    "clearly defined anatomical boundaries. It is closely related to the steepness of intensity transitions " \
    "at tissue interfaces, i.e. how abruptly gray values change across edges. " \
    "Images with low sharpness exhibit smooth, slowly varying intensity profiles, " \
    "which visually appear as blurred edges, reduced contrast at boundaries or double contours caused by partial volume effects."
)


streamlit.subheader("Different levels in sharpness")

file_source = select_image_source(
    "Upload your own MR image file or PNG image to compare sharpness levels.",
    "Or choose a demo example file from the images folder:",
)

volume, load_error = load_dicom_volume(file_source)
if load_error is not None:
    streamlit.error(f"Unable to read the selected image file: {load_error}")

if volume is None:
    streamlit.info("No image loaded. Upload or choose a demo file to compare sharpness.")
    streamlit.stop()

image = get_default_image_slice(volume)

# Normalization 0-255
pixel_min, pixel_max = numpy.min(image), numpy.max(image)
image_norm = ((image - pixel_min) / (pixel_max - pixel_min) * 255).astype(numpy.uint8)

# add Gaussian blur
sigma = streamlit.slider("Gaussian blur σ", 0.0, 10.0, 0.0, step=0.1)

image_norm = image_norm.astype(numpy.float32)
image_blurred = skimage.filters.gaussian(image_norm, sigma=sigma, preserve_range=True)
image_blurred = numpy.clip(image_blurred, 0, 255).astype(numpy.uint8)

# computation of sharpness for both images
sharpness_original = Sharpness(image_norm).compute_sharpness()
sharpness_blurred = Sharpness(image_blurred).compute_sharpness()

col1, col2 = streamlit.columns(2)

with col1:
    streamlit.write(f"**Sharpness:** {sharpness_original:.2f}")
    fig1, ax1 = plt.subplots()
    ax1.imshow(image_norm, cmap="gray")
    ax1.set_title("Original")
    ax1.axis("off")
    streamlit.pyplot(fig1)

with col2:
    streamlit.write(f"**Sharpness:** {sharpness_blurred:.2f}")
    fig2, ax2 = plt.subplots()
    ax2.imshow(image_blurred, cmap="gray")
    ax2.set_title("Blur")  # * Unschärfe wurde künstlich durch Gaussian smooting filter erzeugt
    ax2.axis("off")
    streamlit.pyplot(fig2)


streamlit.subheader("Computation of Sharpness")

streamlit.write("The Computation of the Sharpness is based on the entropy values of: ")

streamlit.markdown("""                
- the original image
- the edge-reinforced image
""")

streamlit.graphviz_chart("""
digraph {
    rankdir=LR;
    node [shape=rect, style=filled, fontname="Helvetica"]

    orig [label="Original image", fillcolor="#DCE6F2"]
                         
    HO [label="H_O", fillcolor="#C7E6C7"]
                         
    lap [label="Laplace filter", fillcolor="#F6C28B"]
    abs [label="Absolute filter", fillcolor="#F6C28B"]
    HL [label="H_L", fillcolor="#C7E6C7"]

    orig -> HO
    orig -> lap -> abs -> HL
}
""")


streamlit.write(
    "**Edge-reinforced Image**  \n"
    "The edge-reinforced image is obtained by applying a Laplace filter followed by an absolute value operation. "
    "The Laplace operator acts as a second-order derivative and responds strongly to rapid local intensity changes, "
    "while suppressing slowly varying regions.  \n\n"
    "As a result, anatomical boundaries and fine structural details are emphasized, whereas homogeneous regions "
    "contribute little to the filtered image. Taking the absolute value removes edge direction information, "
    "so that only the magnitude of local intensity changes remains.  \n\n"
    "This representation isolates high-frequency image components, which are closely related to perceived image sharpness."
)

streamlit.markdown("#### Mathematical Definition of Sharpness")

streamlit.latex(r"\mathrm{Sharpness} = 2^{H_L - H_O} * 100")

streamlit.latex(
    r"""
    \begin{aligned}
    H_O &:\ \text{Entropy of the original image} \\
    H_L &:\ \text{Entropy of the Laplace-filtered image}
    \end{aligned}
    """
)

streamlit.write(
    "The entropy difference reflects how strongly the image information is redistributed towards " \
    "high-frequency components after explicit edge enhancement. Sharp images show a pronounced increase in entropy " \
    "after Laplace filtering, whereas blurred images exhibit only a small entropy change."
)

button_left, space, button_right = streamlit.columns([1, 1, 1])

with button_left:
    if streamlit.button("← Quality Index"):
        streamlit.switch_page("pages/3_Quality_Index.py")

with button_right:
    if streamlit.button("SNR →"):
        streamlit.switch_page("pages/5_SNR.py")
