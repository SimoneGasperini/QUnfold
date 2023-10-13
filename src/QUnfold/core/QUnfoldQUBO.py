#!/usr/bin/env python
# -*- coding: utf-8 -*-

# ---------------------- Metadata ----------------------
#
# File name:  QUnfoldQUBO.py
# Author:     Gianluca Bianco (biancogianluca9@gmail.com) & Simone Gasperini (simone.gasperini4@unibo.it)
# Date:       2023-06-16
# Copyright:  (c) 2023 Gianluca Bianco under the MIT license.

import numpy as np
from pyqubo import LogEncInteger
from dwave.samplers import SimulatedAnnealingSampler
from dwave.system import LeapHybridSampler


class QUnfoldQUBO:
    def __init__(self, response, meas, lam=0.0):
        self.R = response
        self.d = meas
        self.lam = lam
        # Normalize the response
        if not self._is_normalized(self.R):
            self.R = self._normalize(self.R)

    @staticmethod
    def _is_normalized(matrix):
        return np.allclose(np.sum(matrix, axis=1), 1)

    @staticmethod
    def _normalize(matrix):
        row_sums = np.sum(matrix, axis=1)
        mask = np.nonzero(row_sums)
        norm_matrix = np.copy(matrix)
        norm_matrix[mask] /= row_sums[mask][:, np.newaxis]
        return norm_matrix

    @staticmethod
    def _get_laplacian(dim):
        diag = np.ones(dim) * -2
        ones = np.ones(dim - 1)
        D = np.diag(diag) + np.diag(ones, k=1) + np.diag(ones, k=-1)
        return D

    def _define_variables(self):
        # Get largest power of 2 integer below the total number of entries
        n = int(2 ** np.floor(np.log2(sum(self.d)))) - 1
        # Encode integer variables using logarithmic binary encoding
        vars = [LogEncInteger(f"x{i}", value_range=(0, n)) for i in range(len(self.d))]
        return vars

    def _define_hamiltonian(self, x):
        hamiltonian = 0
        dim = len(x)
        # Add linear terms
        a = -2 * (self.R.T @ self.d)
        for i in range(dim):
            hamiltonian += a[i] * x[i]
        # Add quadratic terms
        G = self._get_laplacian(dim)
        B = (self.R.T @ self.R) + self.lam * (G.T @ G)
        for i in range(dim):
            for j in range(dim):
                hamiltonian += B[i, j] * x[i] * x[j]
        return hamiltonian

    def _define_pyqubo_model(self):
        x = self._define_variables()
        h = self._define_hamiltonian(x)
        labels = [x[i].label for i in range(len(x))]
        model = h.compile()
        return labels, model

    def solve_simulated_annealing(self, num_reads=100, seed=None):
        labels, model = self._define_pyqubo_model()
        sampler = SimulatedAnnealingSampler()
        sampleset = sampler.sample(model.to_bqm(), num_reads=num_reads, seed=seed)
        decoded_sampleset = model.decode_sampleset(sampleset)
        best_sample = min(decoded_sampleset, key=lambda s: s.energy)
        return np.array([best_sample.subh[label] for label in labels])

    def solve_hybrid_sampler(self):
        labels, model = self._define_pyqubo_model()
        sampler = LeapHybridSampler()
        sampleset = sampler.sample(model.to_bqm())
        decoded_sampleset = model.decode_sampleset(sampleset)
        best_sample = min(decoded_sampleset, key=lambda s: s.energy)
        return np.array([best_sample.subh[label] for label in labels])
