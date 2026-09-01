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
from parameter.quality_index import QualityIndex
from parameter.sharpness import Sharpness
from parameter.snr import SNR


streamlit.title("Quality Parameter")


file_source = select_image_source(
    "Upload your own MR image file or PNG image to compute the quality parameter.",
    "Or choose a demo example file from the images folder:",
)

streamlit.subheader("Image")


if file_source is not None:
    volume, load_error = load_dicom_volume(file_source)
    if load_error is not None:
        streamlit.error(f"Unable to read the selected image file: {load_error}")
        volume = None

    if volume is not None:
        match volume.ndim:
            case 2:
                slice = volume.astype(numpy.float32)

                fig, ax = plt.subplots()
                ax.imshow(volume, cmap="gray")
                ax.axis("off")
                streamlit.pyplot(fig)

            case 3:
                slice_idx = streamlit.slider(
                    "Slice index",
                    min_value=0,
                    max_value=volume.shape[0] - 1,
                    value=volume.shape[0] // 2)
                
                slice = volume[slice_idx].astype(numpy.float32)

                fig, ax = plt.subplots()
                ax.imshow(volume[slice_idx], cmap="gray")
                ax.axis("off")
                streamlit.pyplot(fig)

        streamlit.session_state["current_slice"] = slice


if "current_slice" in streamlit.session_state:
    image = streamlit.session_state["current_slice"]

    # Normalization 0-255
    pixel_min, pixel_max = numpy.min(image), numpy.max(image)
    image_norm = ((image - pixel_min) / (pixel_max - pixel_min) * 255).astype(numpy.uint8)

    # --- Threshold --- 
    histogram, _ = numpy.histogram(image_norm.ravel(), bins=256, range=(0, 255))
    threshold = HuangThreshold(histogram.astype(float)).find_threshold()

    # --- Universal Image Quality Index --- 
    uqi = QualityIndex(image_norm).compute_uqi()

    # --- Sharpness --- 
    sharpness = Sharpness(image).compute_sharpness()

    # --- SNR --- 
    snr = SNR(image, image_norm, threshold).compute_snr()


    streamlit.subheader("Computed Parameters")

    col1, col2, col3 = streamlit.columns(3)

    with col1:
        streamlit.metric("UQI", f"{uqi:.2f}")
        
    with col2:
        streamlit.metric("Sharpness", f"{sharpness:.2f}")

    with col3:
        streamlit.metric("SNR", f"{snr:.2f}")


    streamlit.subheader("Foreground & Background Mask")

    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    # Prepare masks
    mask_fg = SNR(image, image_norm, threshold).foreground_mask()
    mask_bg = SNR(image, image_norm, threshold).background_mask(mask_fg)

    # 1 — Original image
    axes[0].imshow(image, cmap="gray")
    axes[0].set_title("Original")
    axes[0].axis("off")

    # 2 — Foreground mask 
    mask_fg = numpy.where(mask_fg, image, numpy.nan) 
    axes[1].imshow(mask_fg, cmap="gray")
    axes[1].set_title("Foreground mask")
    axes[1].axis("off")

    # 3 — Background mask 
    mask_bg_vis = numpy.full(mask_bg.shape, 128, dtype=numpy.uint8)  
    mask_bg_vis[~mask_bg] = 0                                    
    axes[2].imshow(mask_bg_vis, cmap="gray", vmin=0, vmax=255)
    axes[2].set_title("Background mask")
    axes[2].axis("off")

    streamlit.pyplot(fig)

else:
    streamlit.info("No image loaded. Load a DICOM file to calculate quality parameters.")


streamlit.divider()


streamlit.text(
    "The following pages provide more detailed information on image quality characteristics and the " \
    "calculation of quality parameters.  Furthermore, the process of making the masks and their intended use will be explained.")

button_left, space, button_right = streamlit.columns([1, 1, 1])

with button_left:
    if streamlit.button("← Quality Assessment"):
        streamlit.switch_page("pages/1_Quality_Assessment.py")

with button_right:
    if streamlit.button("Quality Index →"):
        streamlit.switch_page("pages/3_Quality_Index.py")
