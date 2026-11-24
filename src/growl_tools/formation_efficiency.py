"""Formation efficiencies: how many (merging) compact binaries form per solar mass of stars.

This follows onboarding Tutorial 3, Part 1 (growl-tools/tutorials). In short:

1. A simulation only evolves binaries inside a "box" of birth parameters (primary mass between
   ``m1_min`` and ``m1_max``, secondary above ``m2_min``, ...). One simulated binary stands for
   ``M_rep`` solar masses of *all* star formation: the stars outside the box and the single stars
   formed alongside it. :func:`mass_per_binary` computes ``M_rep`` from a :class:`SamplingSetup`.
2. The mass formed in metallicity bin j is ``M_j = N_j * M_rep``, with ``N_j`` the number of
   simulated binaries in that bin (:func:`systems_per_bin`).
3. The formation efficiency of bin j is ``eta_j = sum(w_i in j) / M_j``
   (:func:`formation_efficiency_vs_Z`), and the per-system value that cosmic-integration codes
   such as SSPC need is ``eta_i = w_i / M_j(i)`` (:func:`formation_efficiency_per_system`).
   The ``w_i`` are the sampling weights (1 for a fairly sampled simulation).

Which numbers go into the :class:`SamplingSetup` (mass ranges, binary fraction, IMF, mass-ratio
cut) and how the metallicities were sampled differ between datasets. Finding them in the paper
and justifying them is part of each student's project, so this module never guesses them.

The per-system ``eta_i`` depends on the metallicity bins. A cosmic-integration run must use
**the same metallicity bin edges** for the star formation history as were used here. Store
them with the data (see :func:`growl_tools.standard_format.write_growl_file`).
"""
from dataclasses import dataclass, asdict, field

import numpy as np
from scipy.integrate import quad

KROUPA_BOUNDS = (0.01, 0.08, 0.5, 200.0)   # Msun, Kroupa (2001)
KROUPA_SLOPES = (0.3, 1.3, 2.3)            # dN/dm ~ m^-alpha in each segment


@dataclass
class SamplingSetup:
    """The birth-parameter "box" a simulation sampled, and the assumed population outside it.

    m1_min, m1_max  primary (initially more massive star) mass range simulated [Msun]
    m2_min          smallest secondary mass simulated [Msun]
    q_min           smallest mass ratio m2/m1 simulated (0 = no cut besides m2_min)
    f_bin           binary fraction assumed for the real population (0 < f_bin <= 1)
    imf_bounds      mass bounds of the broken power-law IMF segments [Msun]
    imf_slopes      power-law slope alpha (dN/dm ~ m^-alpha) in each segment
    source          where these values are stated (paper section / table), for the record

    The mass ratio of the real population is assumed flat between 0 and 1.
    """
    m1_min: float
    m1_max: float
    m2_min: float = 0.1
    q_min: float = 0.0
    f_bin: float = 0.7
    imf_bounds: tuple = KROUPA_BOUNDS
    imf_slopes: tuple = KROUPA_SLOPES
    source: str = ""

    def __post_init__(self):
        if not 0 < self.f_bin <= 1:
            raise ValueError("f_bin must be in (0, 1]")
        if len(self.imf_bounds) != len(self.imf_slopes) + 1:
            raise ValueError("imf_bounds needs one more entry than imf_slopes")
        if not self.imf_bounds[0] <= self.m1_min < self.m1_max <= self.imf_bounds[-1]:
            raise ValueError("m1_min/m1_max must lie inside the IMF bounds")

    def to_dict(self):
        d = asdict(self)
        d["imf_bounds"], d["imf_slopes"] = list(self.imf_bounds), list(self.imf_slopes)
        return d


def _imf_unnormalised(m, bounds, slopes):
    """dN/dm of a broken power law, continuous across the breaks; 0 outside the bounds."""
    m = np.asarray(m, dtype=float)
    out = np.zeros_like(m)
    const = 1.0
    for i, alpha in enumerate(slopes):
        lo, hi = bounds[i], bounds[i + 1]
        if i > 0:   # continuity at the break lo
            const *= lo ** (alpha - slopes[i - 1])
        sel = (m >= lo) & ((m < hi) if i < len(slopes) - 1 else (m <= hi))
        out[sel] = const * m[sel] ** -alpha
    return out


def imf_pdf(m, bounds=KROUPA_BOUNDS, slopes=KROUPA_SLOPES):
    """Normalised initial mass function dP/dm [Msun^-1]."""
    norm = quad(lambda x: _imf_unnormalised(x, bounds, slopes), bounds[0], bounds[-1],
                points=bounds[1:-1], limit=200)[0]
    return _imf_unnormalised(m, bounds, slopes) / norm


def _mass_per_binary_quad(s):
    pdf = lambda m: imf_pdf(m, s.imf_bounds, s.imf_slopes)
    pts = s.imf_bounds[1:-1]
    m_avg = quad(lambda m: m * pdf(m), s.imf_bounds[0], s.imf_bounds[-1], points=pts, limit=200)[0]
    mass_per_binary_drawn = m_avg * (1.5 + (1 - s.f_bin) / s.f_bin)
    p_inside = lambda m: pdf(m) * (1 - min(1.0, max(s.q_min, s.m2_min / m)))
    inner = [p for p in pts if s.m1_min < p < s.m1_max]
    f_sim = quad(p_inside, s.m1_min, s.m1_max, points=inner or None, limit=200)[0]
    return mass_per_binary_drawn / f_sim


def _mass_per_binary_analytic(s):
    """Ilya Mandel's closed form, as in COMPAS compas_python_utils/cosmic_integration
    (``analytical_star_forming_mass_per_binary_using_kroupa_imf``). Kroupa IMF only."""
    if tuple(s.imf_slopes) != KROUPA_SLOPES or len(s.imf_bounds) != 4 or s.q_min > 0:
        raise ValueError("the analytic formula only covers the Kroupa (0.3, 1.3, 2.3) IMF "
                         "with q_min = 0; use method='quad' or 'sampling'")
    m1, m2, m3, m4 = s.imf_bounds
    alpha = (-(m4**(-1.3) - m3**(-1.3)) / 1.3 - (m3**(-0.3) - m2**(-0.3)) / (m3 * 0.3)
             + (m2**0.7 - m1**0.7) / (m2 * m3 * 0.7))**(-1)
    m_avg = alpha * (-(m4**(-0.3) - m3**(-0.3)) / 0.3 + (m3**0.7 - m2**0.7) / (m3 * 0.7)
                     + (m2**1.7 - m1**1.7) / (m2 * m3 * 1.7))
    fint = (-alpha / 1.3 * (s.m1_max**(-1.3) - s.m1_min**(-1.3))
            + alpha * s.m2_min / 2.3 * (s.m1_max**(-2.3) - s.m1_min**(-2.3)))
    return (1 / fint) * m_avg * (1.5 + (1 - s.f_bin) / s.f_bin)


def _mass_per_binary_sampling(s, n_samples, seed):
    """Monte Carlo: draw a synthetic population from the IMF and count what lands in the box."""
    rng = np.random.default_rng(seed)
    grid = np.logspace(np.log10(s.imf_bounds[0]), np.log10(s.imf_bounds[-1]), 20001)
    pdf = imf_pdf(grid, s.imf_bounds, s.imf_slopes)
    cdf = np.concatenate([[0], np.cumsum(0.5 * (pdf[1:] + pdf[:-1]) * np.diff(grid))])
    m1 = np.interp(rng.random(n_samples), cdf / cdf[-1], grid)
    is_binary = rng.random(n_samples) < s.f_bin
    q = rng.random(n_samples)
    total_mass = m1.sum() + (q * m1)[is_binary].sum()
    inside = (is_binary & (m1 >= s.m1_min) & (m1 <= s.m1_max)
              & (q * m1 >= s.m2_min) & (q >= s.q_min))
    n_inside = inside.sum()
    if n_inside == 0:
        raise ValueError("no samples inside the simulated box; increase n_samples")
    return total_mass / n_inside


def mass_per_binary(setup, method="quad", n_samples=20_000_000, seed=0):
    """Star-forming mass M_rep [Msun] represented by one simulated binary.

    method
        "quad"      numerical integral over the IMF (any broken power law, q_min allowed)
        "analytic"  closed form from the COMPAS cosmic-integration code (Kroupa IMF, q_min = 0)
        "sampling"  Monte Carlo draw of a synthetic population, as COMPAS' older
                    totalMassEvolvedPerZ does; statistical error ~ 1/sqrt(n inside the box)

    All three should agree; comparing them is a good check of the setup.
    """
    if method == "quad":
        return _mass_per_binary_quad(setup)
    if method == "analytic":
        return _mass_per_binary_analytic(setup)
    if method == "sampling":
        return _mass_per_binary_sampling(setup, int(n_samples), seed)
    raise ValueError(f"unknown method {method!r}")


# ---------------------------------------------------------------------------------------------
# metallicity bins
# ---------------------------------------------------------------------------------------------

def metallicity_bin_edges(Z, mode, n_bins=50, z_min=None, z_max=None):
    """Metallicity bin edges (linear Z, increasing) to compute formation efficiencies in.

    mode
        "log_uniform"  metallicities drawn continuously (flat in log Z): ``n_bins`` equal bins in
                       log Z between z_min and z_max (default: the min and max of ``Z``)
        "grid"         a fixed set of metallicities: one bin per distinct value, with edges halfway
                       (in log Z) between neighbours
    """
    Z = np.asarray(Z, dtype=float)
    if mode == "log_uniform":
        lo = np.log10(z_min if z_min is not None else Z.min())
        hi = np.log10(z_max if z_max is not None else Z.max())
        return 10 ** np.linspace(lo, hi, n_bins + 1)
    if mode == "grid":
        grid = np.log10(np.unique(Z))
        if len(grid) < 2:
            raise ValueError("need at least two distinct metallicities for mode='grid'")
        mids = 0.5 * (grid[1:] + grid[:-1])
        edges = np.concatenate([[grid[0] - (mids[0] - grid[0])], mids,
                                [grid[-1] + (grid[-1] - mids[-1])]])
        return 10 ** edges
    raise ValueError(f"unknown mode {mode!r}")


def metallicity_bin_index(Z, edges):
    """Index of the bin each Z falls in; values on the outer edges go into the outer bins."""
    idx = np.digitize(np.asarray(Z, dtype=float), edges) - 1
    return np.clip(idx, 0, len(edges) - 2)


def systems_per_bin(edges, Z_all_systems=None, n_simulated=None):
    """Number N_j of simulated binaries in each metallicity bin.

    Give ``Z_all_systems`` (the metallicity of every simulated binary, e.g. from
    BSE_System_Parameters) whenever the file has it. If it does not, give ``n_simulated`` (the
    total, from the paper) and the binaries are assumed spread flat in log Z over the edges.
    """
    if Z_all_systems is not None:
        idx = metallicity_bin_index(Z_all_systems, edges)
        return np.bincount(idx, minlength=len(edges) - 1).astype(float)
    if n_simulated is not None:
        dlog = np.diff(np.log10(edges))
        return n_simulated * dlog / dlog.sum()
    raise ValueError("give Z_all_systems or n_simulated")


def formation_efficiency_per_system(Z, weight, edges, n_per_bin, m_rep):
    """eta_i = w_i / (N_j * M_rep): (merging) systems per Msun formed in system i's Z bin."""
    w = np.ones(len(Z)) if weight is None else np.asarray(weight, dtype=float)
    mass_formed = np.asarray(n_per_bin, dtype=float) * m_rep
    return w / mass_formed[metallicity_bin_index(Z, edges)]


def formation_efficiency_vs_Z(Z, weight, edges, n_per_bin, m_rep):
    """eta_j = sum of weights in bin j / (N_j * M_rep), one value per metallicity bin."""
    w = np.ones(len(Z)) if weight is None else np.asarray(weight, dtype=float)
    sum_w = np.bincount(metallicity_bin_index(Z, edges), weights=w, minlength=len(edges) - 1)
    with np.errstate(divide="ignore", invalid="ignore"):
        return sum_w / (np.asarray(n_per_bin, dtype=float) * m_rep)


def mean_formation_efficiency(weight, n_simulated, m_rep):
    """Average over all simulated metallicities: sum(w) / (N_simulated * M_rep)."""
    return np.sum(weight) / (n_simulated * m_rep)
