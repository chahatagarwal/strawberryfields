# Copyright 2019 Xanadu Quantum Technologies Inc.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
r"""
Point Processes
===============

**Module name:** :mod:`strawberryfields.apps.points`

.. currentmodule:: strawberryfields.apps.points

This module provides functions for building kernel matrices and generating point processes using
GBS. An accompanying tutorial can be found :ref:`here <apps-points-tutorial>`.

Point processes
---------------

A point process is a mechanism that generates random point patterns among a set of possible
outcomes.
Point processes are statistical models that can replicate the stochastic
properties of natural phenomena, or be used as subroutines in statistical and machine learning
algorithms.

Several point processes rely on matrix functions to assign probabilities to different point
patterns. As shown in Ref. :cite:`jahangiri2019point`, GBS naturally gives rise to a *hafnian*
point process that employs the `hafnian
<https://the-walrus.readthedocs.io/en/latest/hafnian.html>`_ as the underlying matrix function.
This point process has the central property of generating clustered data points with
high probability. In this setting, a GBS device is programmed according to a *kernel* matrix that
encodes information about the similarity between points. When this kernel matrix is positive
semidefinite, it is possible to use GBS to implement a *permanental* point process and employ
fast classical algorithms to sample from the resulting distribution.

One choice of kernel matrix is the radial basis function (RBF) kernel whose elements are computed
as:

.. math::
    K_{i,j} = e^{-\|\bf{r}_i-\bf{r}_j\|^2/(2\sigma^2)},

where :math:`\bf{r}_i` are the coordinates of point :math:`i`, :math:`\sigma` is a kernel
parameter, and :math:`\|\cdot\|` denotes a choice of norm. The RBF kernel is positive
semidefinite when the Euclidean norm is used, as is the case for the provided :func:`rbf_kernel`
function.

Summary
-------

.. autosummary::
    rbf_kernel
    sample

Code details
^^^^^^^^^^^^
"""

import numpy as np
import scipy
from thewalrus.csamples import generate_thermal_samples, rescale_adjacency_matrix_thermal


def rbf_kernel(R: np.ndarray, sigma: float) -> np.ndarray:
    r"""Calculate the RBF kernel matrix from a set of input points.

    The kernel parameter :math:`\sigma` is used to define the kernel scale. Points that are much
    further than :math:`\sigma` from each other lead to small entries of the kernel
    matrix, whereas points much closer than :math:`\sigma` generate large entries.

    The Euclidean norm is used to measure distance in this function, resulting in a
    positive-semidefinite kernel.

    **Example usage:**

    >>> R = np.array([[0, 1], [1, 0], [0, 0], [1, 1]])
    >>> rbf_kernel (R, 1.0)
    array([[1., 0.36787944, 0.60653066, 0.60653066],
           [0.36787944, 1., 0.60653066, 0.60653066],
           [0.60653066, 0.60653066, 1., 0.36787944],
           [0.60653066, 0.60653066, 0.36787944, 1.,]])

    Args:
        R (array): Coordinate matrix. Rows of this array are the coordinates of the points.
        sigma (float): kernel parameter

    Returns:
        K (array): the RBF kernel matrix
    """
    return np.exp(-(scipy.spatial.distance.cdist(R, R)) ** 2 / 2 / sigma ** 2)


def sample(K: np.ndarray, n_mean: float, n_samples: int) -> list:
    """Sample subsets of points using the permanental point process.

    Points can be encoded through a radial basis function kernel, provided in :func:`rbf_kernel`.
    Subsets of points are sampled with probabilities that are proportional to the permanent of the
    submatrix of the kernel selected by those points.

    This permanental point process is likely to sample points that are clustered together
    :cite:`jahangiri2019point`. It can be realized using a variant of Gaussian boson sampling
    with thermal states as input.

    **Example usage:**

    >>> K = np.array([[1., 0.36787944, 0.60653066, 0.60653066],
    >>>               [0.36787944, 1., 0.60653066, 0.60653066],
    >>>               [0.60653066, 0.60653066, 1., 0.36787944],
    >>>               [0.60653066, 0.60653066, 0.36787944, 1.]])
    >>> sample(K, 1.0, 10)
    [[0, 1, 1, 1],
     [0, 0, 0, 0],
     [1, 0, 0, 0],
     [0, 0, 0, 1],
     [0, 1, 1, 0],
     [2, 0, 0, 0],
     [0, 0, 0, 0],
     [0, 0, 0, 0],
     [0, 0, 1, 1],
     [0, 0, 0, 0]]

    Args:
        K (array): the positive semidefinite kernel matrix
        n_mean (float): average number of points per sample
        n_samples (int): number of samples to be generated

    Returns:
        samples (list[list[int]]): samples generated by the point process
    """
    ls, O = rescale_adjacency_matrix_thermal(K, n_mean)
    return np.array(generate_thermal_samples(ls, O, num_samples=n_samples)).tolist()