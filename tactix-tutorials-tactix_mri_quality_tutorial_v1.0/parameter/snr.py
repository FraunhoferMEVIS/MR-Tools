"""!
Copyright (c) Fraunhofer MEVIS, Germany. All rights reserved.
The software is not qualified for use as a medical product or as part
thereof. No bugs or restrictions are known.
"""

import numpy
import skimage


class SNR:
    """
    Signal-to-Noise Ratio (SNR) estimation for medical images.

    The SNR is computed as the ratio between:
    - the mean intensity of the foreground (signal)
    - the standard deviation of the background (noise)

    Foreground and background regions are derived from a global threshold and refined using morphological operations.
    """
    def __init__(self, image, image_norm, threshold):
        """
        Parameters:
            image : ndarray
                Original image 
            image_norm : ndarray
                Normalized image used for masking and statistics
            threshold : float
                Intensity threshold separating foreground and background
        """
        self.image = image
        self.image_norm = image_norm
        self.threshold = threshold


    def foreground_mask(self):
        """
        Generate a foreground mask using the given threshold.

        Returns:
            mask_fg : ndarray of bool
                Binary foreground mask
        """
        mask_fg = self.image_norm > self.threshold
        return mask_fg


    def background_mask(self, mask_fg):
        """
        Generate a background mask from the foreground mask.

        Processing steps:
        - Median filtering to remove isolated foreground voxels
        - Morphological closing to fill holes caused by anatomy
        - Morphological dilation to ensure separation of signal and noise
        - Logical inversion to obtain the background mask

        Parameters:
            mask_fg : ndarray of bool
                Foreground mask

        Returns:
            mask_bg : ndarray of bool
                Background mask
        """

        # Median filter
        median_fg = skimage.filters.median(mask_fg.astype(numpy.uint8)).astype(bool)

        # Morphological closing
        closing_fg = skimage.morphology.binary_closing(median_fg, footprint=skimage.morphology.disk(15))

        # Morphological dilation 
        dilatation_fg = skimage.morphology.binary_dilation(closing_fg, footprint=skimage.morphology.disk(1))

        # Background mask as inverse of refined foreground mask
        mask_bg = numpy.logical_not(dilatation_fg)
        
        return mask_bg
    

    def compute_snr(self):
        """
        Compute the signal-to-noise ratio.

          The SNR is defined as:
              SNR = 0.655 * (μ_F / σ_B)

          where:
              μ_F : mean intensity of the foreground
              σ_B : standard deviation of the background

        Returns:
            SNR : float
                Signal-to-noise ratio
        """
        mask_fg = self.foreground_mask()
        mask_bg = self.background_mask(mask_fg)

        # pixel values per mask
        pixel_fg = self.image_norm[mask_fg]
        pixel_bg = self.image_norm[mask_bg]
    
        # standard deviation of the gray values of the background
        sigma_bg = numpy.std(pixel_bg, ddof=1)

        # average gray value of the image foregrounds
        mean_fg = numpy.mean(pixel_fg)

        SNR = 0.655 * (mean_fg / sigma_bg)

        return SNR
