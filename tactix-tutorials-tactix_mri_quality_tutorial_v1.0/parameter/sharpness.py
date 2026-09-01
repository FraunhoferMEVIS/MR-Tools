"""!
Copyright (c) Fraunhofer MEVIS, Germany. All rights reserved.
The software is not qualified for use as a medical product or as part
thereof. No bugs or restrictions are known.
"""

import numpy
import skimage


class Sharpness: 
    """
    Sharpness estimation based on entropy differences.
    Comparison of :
    - the Shannon entropy of the original image
    - the Shannon entropy of an edge-enhanced version of the image

    A Laplace filter is used to emphasize edges. 
    The relative increase in entropy is interpreted as a measure of image sharpness.
    """
    def __init__(self, image):
        self.image = image.astype(numpy.float32)


    def entropy_original(self):
        """
        Compute Shannon entropy of the original image.
        """
        entropy_original = skimage.measure.shannon_entropy(self.image)
        return entropy_original
    

    def entropy_laplace(self):
        """
        Compute Shannon entropy of the Laplace-filtered image.
        """
        laplace = numpy.abs(skimage.filters.laplace(self.image))
        entropy_laplace = skimage.measure.shannon_entropy(laplace)
        return entropy_laplace
    

    def compute_sharpness(self):
        """
        Compute the sharpness measure based on entropy difference.

            Sharpness is defined as:
                S = 2^(H_laplace - H_original) * 100
        """
        entropy_original = self.entropy_original()
        entropy_laplace = self.entropy_laplace()
        sharpness = (2 ** (entropy_laplace - entropy_original)) * 100  
        return sharpness
