"""!
Copyright (c) Fraunhofer MEVIS, Germany. All rights reserved.
The software is not qualified for use as a medical product or as part
thereof. No bugs or restrictions are known.
"""

import numpy


class HuangThreshold:
    """
    Implementation of the thresholding method  proposed in:

    Huang, L.-K. and Wang M.-J.J., 
    Image thresholding by minimizing the measures of fuzziness, 
    Pattern Recognition, 28(1):41-51, 1995

    The method determines the optimal threshold by minimizing the
    fuzzy entropy of an image.
    """
    
    def __init__(self, histogram):
        self.h = histogram              # number of pixels with gray level g 
        self.L = len(self.h)            # number of gray levels (number of bins)
        self.g = numpy.arange(self.L)   # gray levels -> array([0, 1, 2, ..., 255])


    def bin_limits(self):
        """
        Determine the gray-level range of an image.
        Only gray levels with non-zero occurrence contribute to the fuzziness measure.

        Returns:
            first_bin : int
                Lowest gray level with non-zero histogram count
            last_bin : int
                Highest gray level with non-zero histogram count
            C : float
                Normalization constant (gray-level range)
        """
        non_zero_bin = numpy.nonzero(self.h)[0]

        self.first_bin = int(non_zero_bin[0])
        self.last_bin = int(non_zero_bin[-1])

        self.C = float(self.last_bin - self.first_bin)  # Eq. (4)

        return self.first_bin, self.last_bin, self.C
    

    def calculate_average_gray_level(self):
        """
        Compute class-wise cumulative sums and mean gray levels for all possible thresholds t.
            Background class: g ≤ t
            Foreground class: g > t
        """

        # S_b(t): number of pixels in the background class up to threshold t
        self.S_b = numpy.cumsum(self.h)             # Eq. (12)

        # W_b(t): weighted sum of gray levels in the background class
        self.W_b = numpy.cumsum(self.g * self.h)    # Eq. (14)

        # S_f(t): number of pixels in the foreground class
        self.S_f = self.S_b[-1] - self.S_b          # Eq. (17)

        # W_f(t): weighted sum of gray levels in the foreground class
        self.W_f = self.W_b[-1] - self.W_b          # Eq. (19)

        # μ_b(t): mean gray level of background class 
        self.mu_b = numpy.divide(self.W_b, self.S_b, where=self.S_b > 0)  # Eq. (20)
        self.mu_b = numpy.rint(self.mu_b).astype(int)   # rounding to nearest integer

        # μ_f(t): mean gray level of foreground class 
        self.mu_f = numpy.divide(self.W_f, self.S_f, where=self.S_f > 0)  # Eq. (21)
        self.mu_f = numpy.rint(self.mu_f).astype(int)   # rounding to nearest integer

        return self.mu_b, self.mu_f
    
    
    def calculate_membership(self, t):   # Mitgliedschaft mu_x für alle Bins x, gegeben Threshold t (Gleichung (4))
        """
        Compute the fuzzy membership function μ_x for all gray levels, given a threshold t (Eq. (4)).

        Parameters:
            t : int
                Candidate threshold

        Returns:
            mu : ndarray
                Membership values for all gray levels
        """
        
        # Background class: g ≤ t
        x_b = self.g <= t
        self.mu[x_b] = 1.0 / (1.0 + numpy.abs(self.g[x_b] - self.mu_b[t]) / self.C)

        # Foreground class: g > t
        x_f = self.g > t
        self.mu[x_f] = 1.0 / (1.0 + numpy.abs(self.g[x_f] - self.mu_f[t]) / self.C)

        return self.mu
    
    
    def calculate_entropy(self, mu): 
        """
        Compute the fuzzy entropy for a given membership function.

            Shannon's entropy function:
                S(μ) = -μ ln(μ) - (1 - μ) ln(1 - μ) 

            Total entropy computed as a histogram-weighted sum:
                E = Σ S(μ(g)) · h(g)       

        Parameters:
            mu : ndarray
                Membership values for all gray levels

        Returns:
            entropy : float
                Fuzzy entropy value
        """

        # limit cases: µ ln(µ) = 0 for µ = 0; (1-µ) ln(1-µ) = 0 for µ = 1
        self.S = - numpy.where(mu > 0, mu * numpy.log(mu), 0.0) - numpy.where(mu < 1, (1 - mu) * numpy.log(1 - mu), 0.0)  # Eq. (6)

        # histogram-weighted entropy
        self.entropy = numpy.sum(self.S * self.h)  # Eq. (8)

        return self.entropy
    
    
    def find_threshold(self):
        """
        Search for the optimal threshold by minimizing fuzzy entropy.
        For each possible threshold t within the effective gray-level range:
        1. Compute fuzzy memberships
        2. Compute fuzzy entropy
        3. Select the threshold that minimizes entropy

        Returns:
            threshold : int
                Optimal threshold according to Huang's method
        """

        # determine gray-level range
        self.bin_limits()                  

        # precompute class mean gray levels for all t
        self.calculate_average_gray_level() 

        # storage for membership values
        self.mu = numpy.zeros(self.L)     

        entropy_min = numpy.inf
        threshold = None

        # iteration over all candidate thresholds
        for t in range(self.first_bin, self.last_bin):

            mu = self.calculate_membership(t)
            entropy = self.calculate_entropy(mu)

            if entropy < entropy_min:
                entropy_min = entropy
                threshold = t

        return threshold
