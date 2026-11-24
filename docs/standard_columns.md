# GROWL standard columns

Version **0.1-draft**. This page is generated from `src/growl_tools/standard_columns.py`; edit that file, then run `python -m growl_tools.standard_columns > docs/standard_columns.md`.

Reference dataset: van Son et al. (2022a, 2023) fiducial COMPAS model (onboarding tutorial file), `COMPAS_Output_wWeights.h5`, [doi:10.5281/zenodo.7612755](https://doi.org/10.5281/zenodo.7612755).

Status `to_check` means drafted but not yet reviewed by a GROWL mentor.

## `BSE_System_Parameters`

One row = one simulated binary (every binary that was evolved, whatever its outcome).

Other names: `SystemParameters`.

Needed to know how many binaries were simulated, and so for the formation efficiency. 'SystemParameters' is the older COMPAS name (seen in vanson-2022-weightymatter).

| Column | Unit | Description | Notes | Other names | Status |
|---|---|---|---|---|---|
| `SEED` | - | Unique ID of the binary (the random seed it was evolved with). Links rows between groups. |  |  | to_check |
| `Mass@ZAMS(1)` | Msun | Birth (zero-age main sequence, ZAMS) mass of star 1, the initially more massive star (the primary). |  |  | to_check |
| `Mass@ZAMS(2)` | Msun | Birth (ZAMS) mass of star 2, the initially less massive star (the secondary). |  |  | to_check |
| `Metallicity@ZAMS(1)` | - | Birth metallicity Z of star 1: the mass fraction of elements heavier than helium. Both stars have the same Z. | Solar is Z ~ 0.0142 (Asplund+2009) in recent COMPAS versions; older papers use 0.02. Check which one your paper uses. |  | to_check |
| `Stellar_Type@ZAMS(1)` | - | Stellar type of star 1 at birth, as a Hurley et al. (2000) code (1 = main-sequence star; 16 = chemically homogeneous star in COMPAS). |  |  | to_check |
| `Stellar_Type@ZAMS(2)` | - | Stellar type of star 2 at birth (Hurley et al. 2000 code). |  |  | to_check |

## `BSE_Double_Compact_Objects`

One row = one binary that formed a double compact object (BH+BH, BH+NS or NS+NS).

Other names: `DoubleCompactObjects`.

'DoubleCompactObjects' is the older COMPAS name (seen in vanson-2022-weightymatter).

| Column | Unit | Description | Notes | Other names | Status |
|---|---|---|---|---|---|
| `SEED` | - | Unique ID of the binary; same as in BSE_System_Parameters. |  |  | to_check |
| `Mass(1)` | Msun | Mass of the compact object (black hole or neutron star) that star 1 became. | Star 1 is the initially more massive star, NOT necessarily the heavier compact object. Use max(Mass(1), Mass(2)) for the primary BH mass m1. |  | to_check |
| `Mass(2)` | Msun | Mass of the compact object that star 2 became. |  |  | to_check |
| `Stellar_Type(1)` | - | Final stellar type of star 1 (Hurley et al. 2000 code): 13 = neutron star, 14 = black hole. |  |  | to_check |
| `Stellar_Type(2)` | - | Final stellar type of star 2 (13 = NS, 14 = BH). |  |  | to_check |
| `Metallicity@ZAMS(1)` | - | Birth metallicity Z of the binary (copied here so the DCO table can be used on its own). |  |  | to_check |
| `Time` | Myr | Time from the birth of the binary to the formation of the double compact object (the second supernova). |  |  | to_check |
| `Coalescence_Time` | Myr | Time from the formation of the double compact object to its merger by gravitational-wave emission. The delay time is Time + Coalescence_Time. | Computed with Peters (1964); check for very large values (non-merging systems) before plotting. |  | to_check |
| `Merges_Hubble_Time` | - | 1 if the double compact object merges within the age of the Universe (a Hubble time), else 0. | Check in the paper (or the code version) whether this compares the Coalescence_Time or the full delay time with the Hubble time. |  | to_check |
| `CE_Event_Counter` | - | Number of common-envelope events the binary went through. 0 means it only had stable mass transfer (or none). |  |  | to_check |
| `Optimistic_CE` | - | 1 if the binary survived a common envelope with a Hertzsprung-gap donor. Such systems are kept in the 'optimistic' CE assumption and removed in the 'pessimistic' one. | Which variant the paper uses (optimistic or pessimistic) belongs in the metadata table. |  | to_check |
| `Immediate_RLOF>CE` | - | 1 if a star filled its Roche lobe straight after a common envelope. These systems are usually treated as mergers and removed. |  |  | to_check |
| `MT_Donor_Hist(1)` | - | History of the stellar types of star 1 each time it was a mass-transfer donor, as a string of Hurley type codes (e.g. '2-4'). | Stored as a byte string: decode with .astype(str). |  | to_check |
| `MT_Donor_Hist(2)` | - | Same as MT_Donor_Hist(1), for star 2. |  |  | to_check |
| `mixture_weight` | - | Statistical weight of the binary from adaptive importance sampling (STROOPWAFEL). Sum weights instead of counting rows. | Not standard COMPAS output: added by the sampling code. A fairly sampled dataset has no weight column (every weight is 1). |  | to_check |

## `BSE_RLOF`

One row = one mass-transfer event (Roche-lobe overflow); a binary can have several rows.

Has no weight column: take the weight from the binary's SEED.

| Column | Unit | Description | Notes | Other names | Status |
|---|---|---|---|---|---|
| `SEED` | - | Unique ID of the binary. |  |  | to_check |
| `MT_Event_Counter` | - | Number of this mass-transfer event within the binary's life (1 = first). |  |  | to_check |
| `CEE>MT` | - | 1 if this mass-transfer event ended in a common envelope (it was unstable). |  |  | to_check |
| `RLOF(1)>MT` | - | 1 if star 1 still overflows its Roche lobe after this event. |  |  | to_check |
| `RLOF(2)>MT` | - | 1 if star 2 still overflows its Roche lobe after this event. |  |  | to_check |
| `Mass(1)<MT` | Msun | Mass of star 1 just before this event. |  |  | to_check |
| `Mass(1)>MT` | Msun | Mass of star 1 just after this event. |  |  | to_check |
| `Mass(2)<MT` | Msun | Mass of star 2 just before this event. |  |  | to_check |
| `Mass(2)>MT` | Msun | Mass of star 2 just after this event. |  |  | to_check |
| `Eccentricity<MT` | - | Orbital eccentricity just before this event. |  |  | to_check |
| `Eccentricity>MT` | - | Orbital eccentricity just after this event. |  |  | to_check |

## `Rates_*`

One row = one double compact object included in the cosmic integration (see DCOmask).

Added after the simulation by the cosmic-integration code, not by COMPAS. The group name encodes the star formation rate density parameters.

| Column | Unit | Description | Notes | Other names | Status |
|---|---|---|---|---|---|
| `DCOmask` | - | One entry per row of BSE_Double_Compact_Objects: True if that double compact object is included in the rates below. | The rows of merger_rate follow the True entries of DCOmask, in order. |  | to_check |
| `redshifts` | - | Redshift grid of the merger rates. | Has one more entry than merger_rate has columns: check whether these are bin edges. |  | to_check |
| `merger_rate` | Gpc^-3 yr^-1 | Merger rate density contributed by each double compact object (rows) at each redshift (columns). |  |  | to_check |
| `merger_rate_z0` | Gpc^-3 yr^-1 | Merger rate density contributed by each double compact object today (z = 0). |  |  | to_check |

## Columns added by GROWL

Every double-compact-object table in a standardized GROWL file (`input_data/<name>`, see below) has the standard columns the dataset provides, plus:

| Column | Unit | Description | Notes | Status |
|---|---|---|---|---|
| `delay_time` | Myr | Time from the birth of the binary to its merger: Time + Coalescence_Time. |  | to_check |
| `metallicity` | - | Birth metallicity Z (copy of Metallicity@ZAMS(1)). |  | to_check |
| `formation_efficiency_per_solar_mass` | Msun^-1 | eta_i = w_i / (N_j * M_rep): how many systems like this one form per solar mass of star formation in this system's metallicity bin j. The metallicity bin edges are stored in the file (growl/metallicity_bin_edges) and a cosmic integration must use the same edges. | Depends on the metallicity bins and on the sampling setup stored in the file's growl metadata. | to_check |

## Layout of a standardized GROWL file

One HDF5 file per submodel, laid out so that SSPC (syntheticstellarpopconvolve) can use it directly as its input/output file:

```
input_data/<name>        pandas table (format='table'), one per sample, e.g. BBH, BHNS, BNS
                         attrs['units']: JSON {column: unit}
config/                  empty; SSPC stores its configuration here
growl/                   attrs['metadata']: JSON (dataset, submodel, sampling setup, M_rep, ...)
growl/metallicity_bin_edges   linear Z edges used for formation_efficiency_per_solar_mass
growl/n_systems_per_bin       simulated binaries per metallicity bin (N_j)
growl/mass_formed_per_bin     N_j * M_rep [Msun]
output_data/             written by SSPC
```

In SSPC, point `data_column_dict` at `formation_efficiency_per_solar_mass` (`normalized_yield`), `delay_time` (Myr) and `metallicity`, and use `growl/metallicity_bin_edges` as the metallicity bin edges of the star formation history.
