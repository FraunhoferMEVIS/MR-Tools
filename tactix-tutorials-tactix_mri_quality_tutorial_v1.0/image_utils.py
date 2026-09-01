"""!
Copyright (c) Fraunhofer MEVIS, Germany. All rights reserved.
The software is not qualified for use as a medical product or as part
thereof. No bugs or restrictions are known.
"""

from pathlib import Path
from typing import Any

import imageio.v3 as imageio
import numpy
import pydicom
import streamlit


_DICOM_EXTENSIONS = {".dcm", ".dicom"}
_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}
_SUPPORTED_EXTENSIONS = _DICOM_EXTENSIONS | _IMAGE_EXTENSIONS


def _to_grayscale(image: numpy.ndarray) -> numpy.ndarray:
    """
    Convert an RGB or RGBA image to grayscale.
    """
    if image.ndim == 3 and image.shape[-1] in (3, 4):
        rgb = image[..., :3].astype(numpy.float32)
        return (0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]).astype(numpy.float32)
    return image.astype(numpy.float32)


def _iter_demo_files(images_dir: Path) -> list[Path]:
    """
    Iterate over demo image files in the specified directory.
    """
    if not images_dir.exists():
        return []
    return sorted(
        [path for path in images_dir.iterdir() if path.is_file() and path.suffix.lower() in _SUPPORTED_EXTENSIONS],
        key=lambda path: path.name.lower(),
    )


def select_image_source(upload_description: str, demo_description: str) -> Any:
    """
    Select an image source, either by uploading a file or choosing a demo file.
    """
    streamlit.write(upload_description)
    uploaded_file = streamlit.file_uploader(
        "Upload image file",
        type=[ext.lstrip(".") for ext in sorted(_SUPPORTED_EXTENSIONS)],
        accept_multiple_files=False,
    )

    streamlit.write(demo_description)
    demo_files = _iter_demo_files(Path(__file__).resolve().parent / "images")
    demo_labels = ["None", *[path.name for path in demo_files]]
    selected_label = streamlit.selectbox("Demo image file", demo_labels, index=0)

    if uploaded_file is not None:
        return uploaded_file
    if selected_label != "None":
        return demo_files[demo_labels.index(selected_label) - 1]
    return None


def load_dicom_volume(file_source: Any) -> tuple[numpy.ndarray | None, str | None]:
    """
    Load a DICOM volume or an image file and return it as a NumPy array.
    """
    if file_source is None:
        return None, None

    source_name = getattr(file_source, "name", str(file_source))
    extension = Path(source_name).suffix.lower()

    try:
        if extension in _DICOM_EXTENSIONS:
            if hasattr(file_source, "seek"):
                file_source.seek(0)
            dataset = pydicom.dcmread(file_source)
            return numpy.asarray(dataset.pixel_array).astype(numpy.float32), None

        if hasattr(file_source, "seek"):
            file_source.seek(0)
        image = imageio.imread(file_source)
        return _to_grayscale(numpy.asarray(image)), None
    except Exception as exc:
        return None, str(exc)


def get_default_image_slice(volume: numpy.ndarray) -> numpy.ndarray:
    """
    Get the default image slice from a 3D volume.
    """
    image = numpy.asarray(volume)
    image = numpy.squeeze(image)

    if image.ndim == 0:
        return image.reshape(1, 1).astype(numpy.float32)

    if image.ndim == 2:
        return image.astype(numpy.float32)

    if image.ndim == 3 and image.shape[-1] in (3, 4):
        return _to_grayscale(image)

    while image.ndim > 2:
        image = image[image.shape[0] // 2]

    return image.astype(numpy.float32)
