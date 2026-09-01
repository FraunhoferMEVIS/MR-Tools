"""!
Copyright (c) Fraunhofer MEVIS, Germany. All rights reserved.
The software is not qualified for use as a medical product or as part
thereof. No bugs or restrictions are known.
"""

import matplotlib.pyplot as plt
import numpy
import streamlit

from image_utils import get_default_image_slice, load_dicom_volume, select_image_source
from parameter.huang_threshold import HuangThreshold
from parameter.snr import SNR


streamlit.title("SNR")


streamlit.subheader("Noise")

streamlit.write(
    "In MRI, *noise* appears as a grainy, random intensity pattern that does not carry anatomical information. " \
    "It originates mainly from thermal (Brownian) motion of charge carriers in the patient and electronic noise in the receiver chain. " \
    "If the underlying signal is weak, noise can dominate the image and obscure fine structures."
)


streamlit.subheader("Signal-to-noise ratio")

streamlit.write(
    "The relationship between the intensity of the signal and the statistical noise is defined by the signal-to-noise ratio (SNR)." \
)

streamlit.latex(r"\mathrm{SNR} = \frac{\mathrm{Signal}}{\mathrm{Noise}}")

streamlit.badge(
    "The higher the SNR, the lower the noise in the image.", color="green")


streamlit.subheader("Improving SNR")

streamlit.markdown("**Increase signal strength**")
col1, col2 = streamlit.columns(2)
with col1:
    streamlit.badge("Higher field strength", color="green")
    streamlit.badge("More signal averages", color="green")
with col2:
    streamlit.badge("Larger measurement volume", color="green")
    streamlit.badge("Thicker slices", color="green")

streamlit.markdown("**Reduce noise contribution**")
col3, col4 = streamlit.columns(2)
with col3:
    streamlit.badge("Smaller bandwidth", color="orange")
with col4:
    streamlit.badge("Shorter echo time", color="orange")
    streamlit.badge("Coil closer to object", color="orange")

streamlit.subheader("Effect of noise on SNR")

streamlit.write(
    "To illustrate the influence of noise, Gaussian noise with adjustable standard deviation σ is artificially added to an MR slice."
)

file_source = select_image_source(
    "Upload your own MR image file or PNG image to observe SNR effects.",
    "Or choose a demo example file from the images folder:",
)

volume, load_error = load_dicom_volume(file_source)
if load_error is not None:
    streamlit.error(f"Unable to read the selected image file: {load_error}")

if volume is None:
    streamlit.info("No image loaded. Upload or choose a demo file to observe SNR effects.")
    streamlit.stop()

image = get_default_image_slice(volume)

# Normalization 0-255
pixel_min, pixel_max = numpy.min(image), numpy.max(image)
image_norm = ((image - pixel_min) / (pixel_max - pixel_min) * 255).astype(numpy.uint8)

# add Gaussian noise
sigma = streamlit.slider("Noise intensity σ", 0, 40, 0)

noise = numpy.random.normal(0, sigma, image_norm.shape)
image_noisy = image_norm.astype(numpy.float32) + noise
image_noisy = numpy.clip(image_noisy, 0, 255).astype(numpy.uint8)

# computation of SNR for both images
histogram, _ = numpy.histogram(image_norm.ravel(), bins=256, range=(0, 255))
threshold = HuangThreshold(histogram.astype(float)).find_threshold()
snr_original = SNR(image, image_norm, threshold).compute_snr()

histogram, _ = numpy.histogram(image_noisy.ravel(), bins=256, range=(0, 255))
threshold = HuangThreshold(histogram.astype(float)).find_threshold()
snr_noisy = SNR(image, image_noisy, threshold).compute_snr()

col1, col2 = streamlit.columns(2)

with col1:
    streamlit.write(f"**SNR:** {snr_original:.2f}")
    fig1, ax1 = plt.subplots()
    ax1.imshow(image_norm, cmap="gray")
    ax1.set_title("Original")
    ax1.axis("off")
    streamlit.pyplot(fig1)

with col2:
    streamlit.write(f"**SNR:** {snr_noisy:.2f}")
    fig2, ax2 = plt.subplots()
    ax2.imshow(image_noisy, cmap="gray")
    ax2.set_title("Noise")  # Noise was artificially generated using Gaussian noise
    ax2.axis("off")
    streamlit.pyplot(fig2)


streamlit.subheader("Computation of Sharpness")

streamlit.write(
    "The computation of the signal-to-noise ratio is based on a separation of the image into foreground and background. " \
    "Both regions are derived automatically from the image intensity distribution."
)

streamlit.markdown("""
The computation is based on:

- a foreground mask representing anatomical signal
- a background mask representing noise-dominated regions
- the mean gray value of the foreground
- the standard deviation of the background
"""
)

streamlit.graphviz_chart("""
digraph {
    rankdir=LR;
    node [shape=rect, style=filled, fontname="Helvetica"]

    img [label="Image", fillcolor="#DCE6F2"]

    hist [label="Histogram", fillcolor="#F6C28B"]
    thr [label="Threshold", fillcolor="#F6C28B"]

    fg [label="Foreground mask", fillcolor="#C7E6C7"]
    bg [label="Background mask", fillcolor="#C7E6C7"]

    muF [label="μ_F", fillcolor="#C7E6C7"]
    sigmaB [label="σ_B", fillcolor="#C7E6C7"]

    snr [label="SNR", fillcolor="#D9C2E9"]

    img -> hist -> thr
    thr -> fg
    fg -> bg

    fg -> muF
    bg -> sigmaB

    muF -> snr
    sigmaB -> snr
}
""")

streamlit.write(
    "**Foreground segmentation**  \n"
    "A global intensity threshold is determined using Huang’s fuzzy entropy method. "
    "All pixels with normalized gray values above this threshold are classified as foreground. "
    "This region is assumed to contain primarily anatomical signal."
)

streamlit.write(
    "**Background mask refinement**  \n"
    "The background mask is derived from the foreground mask using morphological operations. "
    "Median filtering removes isolated misclassified pixels, binary closing fills holes caused by anatomy, "
    "and a slight dilation ensures spatial separation between signal and noise regions. "
    "The final background mask is obtained by logical inversion and is assumed to contain predominantly noise."
)


streamlit.markdown("#### Mathematical Definition of SNR")

streamlit.latex(r"\mathrm{SNR} = 0.655 * \frac{µ_F}{σ_B}")

streamlit.latex(
    r"""
    \begin{aligned}
    µ_F &:\ \text{mean of gray values of foreground} \\
    σ_B &:\ \text{standard deviation of gray values of background}
    \end{aligned}
    """
)

streamlit.write(
    "The factor of 0.655 compensates for the distortion of the raw data caused by the Fourier transform " \
    "during slice creation, and the Gaussian noise present in the raw data is centered about zero. " \
    "After the raw data are Fourier transformed and converted into a magnitude image with all positive values, " \
    "the noise distribution becomes distorted. This factor accounts for the distortion."
)


button_left, space, button_right = streamlit.columns([1, 1, 1])

with button_left:
    if streamlit.button("← Sharpness"):
        streamlit.switch_page("pages/4_Sharpness.py")

with button_right:
    if streamlit.button("Image Processing →"):
        streamlit.switch_page("pages/6_Image_Processing.py")


streamlit.divider()

with streamlit.expander("**Literature**"):

    sources = [
        "https://www.magnetomworld.siemens-healthineers.com/publications/mr-basics",
        "Firbank, M. J., Coulthard, A., Harrison, R. M., & Williams, E. D. (1999). A comparison of two methods for measuring the signal to noise ratio on MR images. Physics in Medicine & Biology, 44(12), N261."
    ]

    for i in range(len(sources)):
        num, cite = streamlit.columns([1.25,20])
        with num:
            streamlit.write(f"[{i+1}]")
        with cite:
            streamlit.write(sources[i])
