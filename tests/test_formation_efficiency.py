import numpy as np
import pytest

from growl_tools.formation_efficiency import (
    SamplingSetup, mass_per_binary, metallicity_bin_edges, metallicity_bin_index, systems_per_bin,
    formation_efficiency_per_system, formation_efficiency_vs_Z, mean_formation_efficiency)

VAN_SON = SamplingSetup(m1_min=5, m1_max=150, m2_min=0.1, f_bin=0.7)


def test_m_rep_matches_tutorial_3():
    # onboarding Tutorial 3, section 1.3: M_rep = 101.7 Msun for van Son et al. (2022)
    assert mass_per_binary(VAN_SON, "quad") == pytest.approx(101.71, abs=0.01)
    assert mass_per_binary(VAN_SON, "analytic") == pytest.approx(101.71, abs=0.01)
    assert mass_per_binary(VAN_SON, "sampling", n_samples=5_000_000) == pytest.approx(101.71, rel=0.02)


def test_f_bin_one_gives_less_mass():
    s = SamplingSetup(m1_min=5, m1_max=150, f_bin=1.0)
    assert mass_per_binary(s) < mass_per_binary(VAN_SON)


def test_analytic_refuses_other_imfs():
    s = SamplingSetup(m1_min=5, m1_max=150, imf_slopes=(0.3, 1.3, 2.7))
    with pytest.raises(ValueError):
        mass_per_binary(s, "analytic")
    assert mass_per_binary(s, "quad") > 0  # quad handles any broken power law


def test_grid_bins_hold_one_metallicity_each():
    grid = np.array([1e-4, 3e-4, 1e-3, 3e-3, 0.01, 0.03])
    Z = np.repeat(grid, 10)
    edges = metallicity_bin_edges(Z, "grid")
    assert len(edges) == len(grid) + 1
    assert np.array_equal(metallicity_bin_index(grid, edges), np.arange(len(grid)))
    assert np.array_equal(systems_per_bin(edges, Z_all_systems=Z), np.full(len(grid), 10))


def test_efficiency_is_independent_of_binning():
    rng = np.random.default_rng(1)
    Z_all = 10 ** rng.uniform(-4, np.log10(0.03), 200_000)
    Z = Z_all[:5000]
    w = rng.random(5000)
    m_rep = 100.0
    mean = mean_formation_efficiency(w, len(Z_all), m_rep)
    for n_bins in (5, 40):
        edges = metallicity_bin_edges(Z_all, "log_uniform", n_bins=n_bins)
        n_j = systems_per_bin(edges, n_simulated=len(Z_all))
        eta_j = formation_efficiency_vs_Z(Z, w, edges, n_j, m_rep)
        # mass-weighted average over bins gives back the overall mean
        assert np.sum(eta_j * n_j) / n_j.sum() == pytest.approx(mean)
        eta_i = formation_efficiency_per_system(Z, w, edges, n_j, m_rep)
        assert np.sum(eta_i * n_j[metallicity_bin_index(Z, edges)]) / len(Z_all) == pytest.approx(mean)
