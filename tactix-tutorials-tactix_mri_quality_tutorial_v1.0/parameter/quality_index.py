"""!
Copyright (c) Fraunhofer MEVIS, Germany. All rights reserved.
The software is not qualified for use as a medical product or as part
thereof. No bugs or restrictions are known.
"""

import numpy 
import skimage


class QualityIndex:
    """
    Computation of a Universal Image Quality Index (UQI).

    The UQI is derived from:
    - the mean gray value of the original image
    - the mean gray value of an edge-enhanced (Laplace-filtered) image
    - the mean gray value of the difference between the original and median-smoothed image
    """
     
    def __init__(self, image_norm):
        self.image_norm = image_norm.astype(numpy.float32)


    def laplace_filter(self):
        """
        Apply Laplace filtering to emphasize edges.

        The Laplace kernel used by skimage:
            [ 0,  1,  0 ]
            [ 1, -4,  1 ]
            [ 0,  1,  0 ]

        The absolute value removes sign information.
        The result is normalized to [0, 255].

        Returns:
            laplace : ndarray
                Absolute Laplace-filtered image
            laplace_norm : ndarray
                Normalized Laplace image
        """
        laplace = numpy.abs(skimage.filters.laplace(self.image_norm))

        laplace_min, laplace_max = numpy.min(laplace), numpy.max(laplace)
        laplace_norm = ((laplace - laplace_min) / (laplace_max - laplace_min)) * 255

        return laplace, laplace_norm
    

    def median_filter(self):
        """
        Apply median filtering and compute the difference image.

        Returns:
            median_difference : ndarray
                True difference image (original - median) without normalization
            median_norm : ndarray
                Normalized difference image [0, 255] for display
        """
        median = skimage.filters.median(self.image_norm)

        median_difference = numpy.abs(self.image_norm - median)

        median_min, median_max = numpy.min(median_difference), numpy.max(median_difference)
        median_norm = ((median_difference - median_min) / (median_max - median_min + 1e-8)) * 255
        
        return median_difference, median_norm
    

    def mean_original(self):
        """
        Mean gray value of the original image.
        """
        mean_original = numpy.mean(self.image_norm)
        return mean_original
    

    def mean_laplace(self, laplace_norm):
        """
        Mean gray value of the Laplace image.
        """
        mean_laplace = numpy.mean(laplace_norm)
        return mean_laplace
    

    def mean_median(self, median_norm):
        """
        Mean gray value of the median-difference image.
        """
        mean_median = numpy.mean(median_norm)
        return mean_median
    

    def compute_uqi(self):
        """
        Compute the Universal Quality Index (UQI).

            The UQI is defined as:
                UQI = max(0, 1 - (μ_M² / μ_O²)^(1/3)) * (μ_L / μ_O)

            where:
                μ_O : mean of original image
                μ_L : mean of true Laplace-filtered image (not normalized)
                μ_M : mean of true median-difference image (not normalized)

        Returns:
            UQI : float
                Universal image quality index
        """
        # Get TRUE (not normalized) values for mathematical correctness
        laplace, _ = self.laplace_filter()
        median_difference, _ = self.median_filter()

        mean_original = self.mean_original()
        mean_laplace = numpy.mean(laplace)
        mean_median = numpy.mean(median_difference)

        penalty_term = max(0, 1 - ((mean_median ** 2) / (mean_original ** 2)) ** (1/3))
        UQI = penalty_term * (mean_laplace / mean_original)

        return UQI
