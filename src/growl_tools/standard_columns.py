"""The GROWL standard columns: names, units and descriptions.

DRAFT, version 0.1. This list is the reference that every dataset in the GROWL catalog is
compared against (see :func:`growl_tools.standard_format.compare_columns`). It starts from the
file every GROWL Task Force member knows from the onboarding tutorials:

    van Son et al. (2022a, 2023) fiducial COMPAS simulation, ``COMPAS_Output_wWeights.h5``,
    Zenodo https://doi.org/10.5281/zenodo.7612755

Standard names are the COMPAS names used in that file. When a dataset uses a different name for
the same quantity, add that name to ``aliases`` (with the dataset it came from in ``notes``);
when a dataset has a useful column that is not here yet, add a new entry. The documentation page
``docs/standard_columns.md`` is generated from this file (``python -m growl_tools.standard_columns``),
so edit the dictionary, not the page.

Each column entry has these fields:

    dtype        dtype in the reference file
    unit         physical unit ("" for dimensionless numbers, flags, IDs and codes)
    description  what the column means, written for someone new to the field
    aliases      other names that mean exactly the same thing (same unit, same definition)
    notes        traps, conventions, where an alias came from
    status       "to_check" (drafted, not yet reviewed) or "checked" (reviewed by a GROWL mentor)

The units and descriptions were drafted from the COMPAS output documentation
(https://compas.readthedocs.io/en/latest/pages/User%20guide/COMPAS%20output/standard-logfiles-record-specification.html);
the reference file itself carries no unit attributes.
"""

STANDARD_COLUMNS_VERSION = "0.1-draft"

REFERENCE_DATASET = {
    "name": "van Son et al. (2022a, 2023) fiducial COMPAS model (onboarding tutorial file)",
    "file": "COMPAS_Output_wWeights.h5",
    "doi": "10.5281/zenodo.7612755",
    "papers": ["arXiv:2110.01634", "arXiv:2209.13609"],
}

# Group names that end in "*" are matched by prefix (e.g. the Rates group name encodes the
# star formation history parameters used for that cosmic integration).
STANDARD_GROUPS = {
    "BSE_System_Parameters": {
        "row": "one simulated binary (every binary that was evolved, whatever its outcome)",
        "aliases": ["SystemParameters"],
        "notes": "Needed to know how many binaries were simulated, and so for the formation "
                 "efficiency. 'SystemParameters' is the older COMPAS name "
                 "(seen in vanson-2022-weightymatter).",
        "status": "to_check",
    },
    "BSE_Double_Compact_Objects": {
        "row": "one binary that formed a double compact object (BH+BH, BH+NS or NS+NS)",
        "aliases": ["DoubleCompactObjects"],
        "notes": "'DoubleCompactObjects' is the older COMPAS name "
                 "(seen in vanson-2022-weightymatter).",
        "status": "to_check",
    },
    "BSE_RLOF": {
        "row": "one mass-transfer event (Roche-lobe overflow); a binary can have several rows",
        "aliases": [],
        "notes": "Has no weight column: take the weight from the binary's SEED.",
        "status": "to_check",
    },
    "Rates_*": {
        "row": "one double compact object included in the cosmic integration (see DCOmask)",
        "aliases": [],
        "notes": "Added after the simulation by the cosmic-integration code, not by COMPAS. "
                 "The group name encodes the star formation rate density parameters.",
        "status": "to_check",
    },
}


def _col(dtype, unit, description, aliases=(), notes="", status="to_check"):
    return {"dtype": dtype, "unit": unit, "description": description,
            "aliases": list(aliases), "notes": notes, "status": status}


STANDARD_COLUMNS = {
    # ------------------------------------------------------------------------------------
    "BSE_System_Parameters": {
        "SEED": _col("uint64", "",
            "Unique ID of the binary (the random seed it was evolved with). Links rows "
            "between groups."),
        "Mass@ZAMS(1)": _col("float64", "Msun",
            "Birth (zero-age main sequence, ZAMS) mass of star 1, the initially more massive "
            "star (the primary)."),
        "Mass@ZAMS(2)": _col("float64", "Msun",
            "Birth (ZAMS) mass of star 2, the initially less massive star (the secondary)."),
        "Metallicity@ZAMS(1)": _col("float64", "",
            "Birth metallicity Z of star 1: the mass fraction of elements heavier than helium. "
            "Both stars have the same Z.",
            notes="Solar is Z ~ 0.0142 (Asplund+2009) in recent COMPAS versions; older papers "
                  "use 0.02. Check which one your paper uses."),
        "Stellar_Type@ZAMS(1)": _col("int32", "",
            "Stellar type of star 1 at birth, as a Hurley et al. (2000) code "
            "(1 = main-sequence star; 16 = chemically homogeneous star in COMPAS)."),
        "Stellar_Type@ZAMS(2)": _col("int32", "",
            "Stellar type of star 2 at birth (Hurley et al. 2000 code)."),
    },
    # ------------------------------------------------------------------------------------
    "BSE_Double_Compact_Objects": {
        "SEED": _col("uint64", "", "Unique ID of the binary; same as in BSE_System_Parameters."),
        "Mass(1)": _col("float64", "Msun",
            "Mass of the compact object (black hole or neutron star) that star 1 became.",
            notes="Star 1 is the initially more massive star, NOT necessarily the heavier "
                  "compact object. Use max(Mass(1), Mass(2)) for the primary BH mass m1."),
        "Mass(2)": _col("float64", "Msun",
            "Mass of the compact object that star 2 became."),
        "Stellar_Type(1)": _col("int32", "",
            "Final stellar type of star 1 (Hurley et al. 2000 code): 13 = neutron star, "
            "14 = black hole."),
        "Stellar_Type(2)": _col("int32", "", "Final stellar type of star 2 (13 = NS, 14 = BH)."),
        "Metallicity@ZAMS(1)": _col("float64", "",
            "Birth metallicity Z of the binary (copied here so the DCO table can be used on "
            "its own)."),
        "Time": _col("float64", "Myr",
            "Time from the birth of the binary to the formation of the double compact object "
            "(the second supernova)."),
        "Coalescence_Time": _col("float64", "Myr",
            "Time from the formation of the double compact object to its merger by "
            "gravitational-wave emission. The delay time is Time + Coalescence_Time.",
            notes="Computed with Peters (1964); check for very large values (non-merging "
                  "systems) before plotting."),
        "Merges_Hubble_Time": _col("uint8", "",
            "1 if the double compact object merges within the age of the Universe "
            "(a Hubble time), else 0.",
            notes="Check in the paper (or the code version) whether this compares the "
                  "Coalescence_Time or the full delay time with the Hubble time."),
        "CE_Event_Counter": _col("uint32", "",
            "Number of common-envelope events the binary went through. 0 means it only had "
            "stable mass transfer (or none)."),
        "Optimistic_CE": _col("uint8", "",
            "1 if the binary survived a common envelope with a Hertzsprung-gap donor. Such "
            "systems are kept in the 'optimistic' CE assumption and removed in the "
            "'pessimistic' one.",
            notes="Which variant the paper uses (optimistic or pessimistic) belongs in the "
                  "metadata table."),
        "Immediate_RLOF>CE": _col("uint8", "",
            "1 if a star filled its Roche lobe straight after a common envelope. These "
            "systems are usually treated as mergers and removed."),
        "MT_Donor_Hist(1)": _col("bytes (S17)", "",
            "History of the stellar types of star 1 each time it was a mass-transfer donor, "
            "as a string of Hurley type codes (e.g. '2-4').",
            notes="Stored as a byte string: decode with .astype(str)."),
        "MT_Donor_Hist(2)": _col("bytes (S17)", "",
            "Same as MT_Donor_Hist(1), for star 2."),
        "mixture_weight": _col("float64", "",
            "Statistical weight of the binary from adaptive importance sampling (STROOPWAFEL). "
            "Sum weights instead of counting rows.",
            aliases=[],
            notes="Not standard COMPAS output: added by the sampling code. A fairly sampled "
                  "dataset has no weight column (every weight is 1)."),
    },
    # ------------------------------------------------------------------------------------
    "BSE_RLOF": {
        "SEED": _col("uint64", "", "Unique ID of the binary."),
        "MT_Event_Counter": _col("uint32", "",
            "Number of this mass-transfer event within the binary's life (1 = first)."),
        "CEE>MT": _col("uint8", "",
            "1 if this mass-transfer event ended in a common envelope (it was unstable)."),
        "RLOF(1)>MT": _col("uint8", "",
            "1 if star 1 still overflows its Roche lobe after this event."),
        "RLOF(2)>MT": _col("uint8", "",
            "1 if star 2 still overflows its Roche lobe after this event."),
        "Mass(1)<MT": _col("float64", "Msun", "Mass of star 1 just before this event."),
        "Mass(1)>MT": _col("float64", "Msun", "Mass of star 1 just after this event."),
        "Mass(2)<MT": _col("float64", "Msun", "Mass of star 2 just before this event."),
        "Mass(2)>MT": _col("float64", "Msun", "Mass of star 2 just after this event."),
        "Eccentricity<MT": _col("float64", "", "Orbital eccentricity just before this event."),
        "Eccentricity>MT": _col("float64", "", "Orbital eccentricity just after this event."),
    },
    # ------------------------------------------------------------------------------------
    "Rates_*": {
        "DCOmask": _col("bool", "",
            "One entry per row of BSE_Double_Compact_Objects: True if that double compact "
            "object is included in the rates below.",
            notes="The rows of merger_rate follow the True entries of DCOmask, in order."),
        "redshifts": _col("float64", "",
            "Redshift grid of the merger rates.",
            notes="Has one more entry than merger_rate has columns: check whether these are "
                  "bin edges."),
        "merger_rate": _col("float64", "Gpc^-3 yr^-1",
            "Merger rate density contributed by each double compact object (rows) at each "
            "redshift (columns)."),
        "merger_rate_z0": _col("float64", "Gpc^-3 yr^-1",
            "Merger rate density contributed by each double compact object today (z = 0)."),
    },
}


# Columns that GROWL adds to every double-compact-object table of a standardized file
# (growl_tools.standard_format.write_growl_file). Their names are the ones SSPC is pointed at.
DERIVED_COLUMNS = {
    "delay_time": _col("float64", "Myr",
        "Time from the birth of the binary to its merger: Time + Coalescence_Time."),
    "metallicity": _col("float64", "",
        "Birth metallicity Z (copy of Metallicity@ZAMS(1))."),
    "formation_efficiency_per_solar_mass": _col("float64", "Msun^-1",
        "eta_i = w_i / (N_j * M_rep): how many systems like this one form per solar mass of "
        "star formation in this system's metallicity bin j. The metallicity bin edges are "
        "stored in the file (growl/metallicity_bin_edges) and a cosmic integration must use "
        "the same edges.",
        notes="Depends on the metallicity bins and on the sampling setup stored in the file's "
              "growl metadata."),
}


def iter_columns():
    """Yield (group, column, info) for every standard column."""
    for group, cols in STANDARD_COLUMNS.items():
        for name, info in cols.items():
            yield group, name, info


def standard_columns_markdown():
    """Return the documentation page for the standard columns, as Markdown."""
    ref = REFERENCE_DATASET
    out = [
        "# GROWL standard columns",
        "",
        f"Version **{STANDARD_COLUMNS_VERSION}**. This page is generated from "
        "`src/growl_tools/standard_columns.py`; edit that file, then run "
        "`python -m growl_tools.standard_columns > docs/standard_columns.md`.",
        "",
        f"Reference dataset: {ref['name']}, `{ref['file']}`, "
        f"[doi:{ref['doi']}](https://doi.org/{ref['doi']}).",
        "",
        "Status `to_check` means drafted but not yet reviewed by a GROWL mentor.",
        "",
    ]
    for group, cols in STANDARD_COLUMNS.items():
        g = STANDARD_GROUPS[group]
        out += [f"## `{group}`", "", f"One row = {g['row']}.", ""]
        if g["aliases"]:
            out += ["Other names: " + ", ".join(f"`{a}`" for a in g["aliases"]) + ".", ""]
        if g["notes"]:
            out += [g["notes"], ""]
        out += ["| Column | Unit | Description | Notes | Other names | Status |",
                "|---|---|---|---|---|---|"]
        for name, c in cols.items():
            aliases = ", ".join(f"`{a}`" for a in c["aliases"])
            cells = [f"`{name}`", c["unit"] or "-", c["description"], c["notes"], aliases,
                     c["status"]]
            out.append("| " + " | ".join(s.replace("|", "\\|") for s in cells) + " |")
        out.append("")
    out += [
        "## Columns added by GROWL",
        "",
        "Every double-compact-object table in a standardized GROWL file "
        "(`input_data/<name>`, see below) has the standard columns the dataset provides, plus:",
        "",
        "| Column | Unit | Description | Notes | Status |",
        "|---|---|---|---|---|",
    ]
    for name, c in DERIVED_COLUMNS.items():
        cells = [f"`{name}`", c["unit"] or "-", c["description"], c["notes"], c["status"]]
        out.append("| " + " | ".join(s.replace("|", "\\|") for s in cells) + " |")
    out += [
        "",
        "## Layout of a standardized GROWL file",
        "",
        "One HDF5 file per submodel, laid out so that SSPC "
        "(syntheticstellarpopconvolve) can use it directly as its input/output file:",
        "",
        "```",
        "input_data/<name>        pandas table (format='table'), one per sample, e.g. BBH, BHNS, BNS",
        "                         attrs['units']: JSON {column: unit}",
        "config/                  empty; SSPC stores its configuration here",
        "growl/                   attrs['metadata']: JSON (dataset, submodel, sampling setup, M_rep, ...)",
        "growl/metallicity_bin_edges   linear Z edges used for formation_efficiency_per_solar_mass",
        "growl/n_systems_per_bin       simulated binaries per metallicity bin (N_j)",
        "growl/mass_formed_per_bin     N_j * M_rep [Msun]",
        "output_data/             written by SSPC",
        "```",
        "",
        "In SSPC, point `data_column_dict` at `formation_efficiency_per_solar_mass` "
        "(`normalized_yield`), `delay_time` (Myr) and `metallicity`, and use "
        "`growl/metallicity_bin_edges` as the metallicity bin edges of the star formation "
        "history.",
    ]
    return "\n".join(out)


if __name__ == "__main__":
    print(standard_columns_markdown())
