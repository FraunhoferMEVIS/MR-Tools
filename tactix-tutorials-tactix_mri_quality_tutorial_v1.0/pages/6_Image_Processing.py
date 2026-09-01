"""!
Copyright (c) Fraunhofer MEVIS, Germany. All rights reserved.
The software is not qualified for use as a medical product or as part
thereof. No bugs or restrictions are known.
"""

from matplotlib.patches import Patch
import matplotlib.cm as cm
import matplotlib.pyplot as plt
import numpy
import skimage
import streamlit


streamlit.title("Image Processing")

streamlit.write(
    "The image processing methods used in this tutorial on image quality assessment include thresholding methods, " \
    "filtering methods or edge-preserving smoothing methods and morphological image processing methods."
    )


streamlit.subheader("Histogram")

streamlit.write(
    "A gray value histogram shows the frequency distribution of the gray values of an image across the gray value itself. " \
    "However, it does not contain any information about the image content.")

image = numpy.array([
    [0, 1, 1, 2, 2],
    [0, 0, 1, 2, 3],
    [1, 2, 3, 3, 4],
    [0, 2, 3, 4, 4]])

counts = numpy.bincount(image.ravel())
values = numpy.arange(len(counts))

col_img, col_hist = streamlit.columns(2)

FIGSIZE = (5, 4)

with col_img:
    fig_img, ax_img = plt.subplots(figsize=FIGSIZE)
    im = ax_img.imshow(image, cmap="gray", interpolation="nearest")
    ax_img.set_title("Grayscale image (5×4)")
    ax_img.axis("off")
    ax_img.grid(False)
    
    cmap = plt.get_cmap("gray")
    unique_values = numpy.unique(image)
    vmax = unique_values.max()

    legend_elements = [Patch(facecolor=cmap(v / vmax), label=str(v)) for v in unique_values]

    ax_img.legend(
        handles=legend_elements,
        title="Gray value",
        loc="center left",
        bbox_to_anchor=(1.02, 0.5))

    fig_img.subplots_adjust(right=0.78)
    streamlit.pyplot(fig_img)

with col_hist:
    fig_hist, ax_hist = plt.subplots(figsize=FIGSIZE)
    ax_hist.bar(values, counts)
    ax_hist.set_xlabel("Gray value")
    ax_hist.set_ylabel("Frequency")
    ax_hist.set_title("Histogram")
    ax_hist.set_ylim(0, counts.max() * 1.2)

    fig_hist.subplots_adjust(right=0.95)
    streamlit.pyplot(fig_hist)


streamlit.subheader("Thresholding methods")

streamlit.write(
    "Image thresholding is applied to grayscale images to segment image structures, " \
    "where each pixel carries an intensity value ranging from 0 (black) to 255 (white). " \
    "The method converts the grayscale image into a binary one by assigning each pixel " \
    "to either the foreground (region of interest) or the background. " \
    "This decision is based on a chosen threshold: " \
    "pixels with intensities above that threshold are labeled as foreground, " \
    "while those with lower intensities are assigned to the background."
    )

streamlit.latex(r"""
                g(x,y) =
                \begin{cases}
                1 & \text{if } f(x,y) \ge T \\
                0 & \text{otherwise}
                \end{cases}
                """)

streamlit.latex(
    r"""
    \begin{aligned}
    T &:\ \text{Threshold} \\
    f(x,y) &:\ \text{Image with coordinates x and y} \\
    g(x,y) &:\ \text{Binary mask with coordinates x and y}
    \end{aligned}
    """
)

with streamlit.expander("**Image thresholding by Huang et al.**"):
    streamlit.write(
        "One thresholding method is the image thresholding by minimizing the measures of the fuzziness " \
        "by Huang et al. which is based on minimizing the fuzziness of an image. " \
        "Fuzziness represents the uncertainty of the class mambership of a pixel value. " \
        "A membership function describes the relationship between a pixel and the area " \
        "to which it belongs (object or background)."
        )


streamlit.subheader("Morphological image processing")

streamlit.write(
    "Morphological operations are image-processing methods focusing on the shape and structure of objects " \
    "within a binary image. The fundamental concept is to examine an image using a structuring element and " \
    "adjust pixel values according to their spatial configuration and the shape of the structuring element. " \
    "Essential morphological operations are listed below:"
    )

with streamlit.expander("**Erosion**"):
    streamlit.write(
        "Erosion reduces the size of an object in a binary image by removing pixels from the object boundaries. " \
        "At the same time, this enlarges holes in the object. " \
        "As the structuring element slides over the image, the output pixel is set to foreground " \
        "only if all covered pixels match the foreground; otherwise, it becomes background."
        )
    
with streamlit.expander("**Dilation**"):
    streamlit.write(
        "Dilation increases the size of an object in a binary image while holes in the object become smaller. " \
        "As the structuring element slides over the image, the output pixel is set to foreground " \
        "if any covered pixel matches the foreground; otherwise, it becomes background."
        )
    
with streamlit.expander("**Opening**"):
    streamlit.write(
        "During the opening, erosion is performed followed by dilation. " \
        "This removes small objects or noise while preserving the size and shape of larger objects. "
        )
    
with streamlit.expander("**Closing**"):
    streamlit.write(
        "During the closing, dilation is performed followed by erosion. " \
        "This closes the holes in an object while preserving its overall shape. "
        )


# image size
size = 120
image = numpy.zeros((size, size), dtype=bool)

# rectangular object
image[20:100, 20:100] = True

# circular object inside rectangle
radius = 18
center = (size // 2, size // 2)
y, x = numpy.ogrid[:size, :size]
circle = (x - center[0])**2 + (y - center[1])**2 <= radius**2
image[circle] = False   # hole inside the rectangle

# structuring element
se = skimage.morphology.disk(3)

erosion = skimage.morphology.binary_erosion(image, se)
dilation = skimage.morphology.binary_dilation(image, se)
opening = skimage.morphology.binary_opening(image, se)
closing = skimage.morphology.binary_closing(image, skimage.morphology.disk(3))

fig, axes = plt.subplots(1, 5, figsize=(15, 3))

titles = ["Original", "Erosion", "Dilation", "Opening", "Closing"]
images = [image, erosion, dilation, opening, closing]

for ax, img, title in zip(axes, images, titles):
    ax.imshow(img, cmap="gray")
    ax.set_title(title)
    ax.axis("off")

streamlit.pyplot(fig)


streamlit.write(
    "The circular structure acts as a hole inside the rectangular object. "
    "Erosion enlarges the hole, while dilation reduces it. "
    "Opening tends to remove thin connections and small inner structures, "
    "whereas closing effectively fills holes and smooths inner boundaries."
)


streamlit.subheader("Filtering")

streamlit.write(
    "Filtering operations modify pixel intensities based on their local neighborhood. "
    "They are commonly used for noise suppression, edge enhancement or feature extraction. "
    "In this tutorial, the focus lies on the Laplace filter and the Median filter."
)

with streamlit.expander("**Laplace filter (edge enhancement)**"):
    streamlit.write(
        "The Laplace filter is a linear, second-order derivative operator that emphasizes "
        "rapid local intensity changes. Homogeneous regions are largely suppressed, "
        "while edges and fine structural details produce strong responses."
    )

    streamlit.latex(r"""
    \nabla^2 f = \frac{\partial^2 f}{\partial x^2} + \frac{\partial^2 f}{\partial y^2}
    """)

    streamlit.write("The Laplace kernel is given by:")

    streamlit.latex(r"""
    \begin{bmatrix}
    0 & 1 & 0 \\
    1 & -4 & 1 \\
    0 & 1 & 0
    \end{bmatrix}
    """)

    streamlit.write(
        "The Laplace operator acts as a high-pass filter and is therefore sensitive to noise. "
        "Here the absolute value of the filter response is used so that only the magnitude of local intensity changes remains."
    )

with streamlit.expander("**Median filter (edge-preserving smoothing)**"):
    streamlit.write(
        "The median filter is a non-linear, order-statistic filter. "
        "Each pixel is replaced by the median intensity value within a local neighborhood."
    )

    streamlit.latex(r"""
    g(x,y) = \mathrm{median}\{ f(i,j) \mid (i,j) \in W \}
    """)

    streamlit.write(
        "Median filtering effectively suppresses impulse-like noise and small intensity outliers "
        "while preserving edge locations much better than linear averaging filters. "
    )


streamlit.subheader("Entropy")

streamlit.write(
    "Image entropy quantifies the statistical distribution of gray values and reflects "
    "the average information content of an image. It is computed from the normalized histogram "
    "and does not directly encode spatial information."
)

streamlit.latex(r"H = -\sum_{i=0}^{n-1} p(i)\,\log p(i)")

streamlit.latex(
    r"""
    \begin{aligned}
    i &:\ \text{gray value} \\
    p(i) &:\ \text{frequency of gray value } i
    \end{aligned}
    """
)

streamlit.write(
    "Images with a narrow intensity distribution exhibit low entropy, "
    "whereas images with a broad or irregular distribution show higher entropy. "
)


button_left, space, button_right = streamlit.columns([1, 1, 1])

with button_left:
    if streamlit.button("← SNR"):
        streamlit.switch_page("pages/5_SNR.py")


streamlit.divider()

with streamlit.expander("**Literature**"):

    sources = [
        "https://www.geeksforgeeks.org/computer-vision/image-thresholding-techniques-in-computer-vision",
        "Huang, L.-K. and Wang M.-J.J., Image thresholding by minimizing the measures of fuzziness, Pattern Recognition, 28(1):41-51, 1995",
        "https://www.geeksforgeeks.org/computer-vision/different-morphological-operations-in-image-processing",
        "Haasdonk, B., Digitale Bildverarbeitung, FH Offenburg SS 2007, Einheit 5 (https://lmb.informatik.uni-freiburg.de/people/haasdonk/DBV_FHO/DBV_FHO_SS07_E05_handout.pdf)",
        "Thormaehlen, T., Multimedia Signal Processing Image Processing, Marburg University, 2023, Part 6, Chapter 1 (https://www.mathematik.uni-marburg.de/~thormae/lectures/mmk/mmk_6_1_eng_web.html#1)"
    ]

    for i in range(len(sources)):
        num, cite = streamlit.columns([1.25,20])
        with num:
            streamlit.write(f"[{i+1}]")
        with cite:
            streamlit.write(sources[i])
