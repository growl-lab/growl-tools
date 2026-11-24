"""Compare a dataset's HDF5 file with the GROWL standard columns, read it under the standard
names, and write the standardized GROWL file (laid out for SSPC).

The standard columns live in :mod:`growl_tools.standard_columns`. This module answers, for one
file: which standard groups and columns does it have (under the standard name or a known other
name), which are missing, and which columns does it have that the standard list does not know
yet. Students save the result as ``column_check.csv`` in their dataset folder and fill in the
``student_notes`` column; a GROWL mentor then updates the standard list.

Command line::

    python -m growl_tools.standard_format path/to/file.h5 -o column_check.csv
"""
import csv
import fnmatch
import json
import os

import h5py
import numpy as np

from .standard_columns import (STANDARD_COLUMNS, STANDARD_GROUPS, STANDARD_COLUMNS_VERSION,
                               DERIVED_COLUMNS)

GROWL_FILE_VERSION = "0.1-draft"

SSPC_DATA_COLUMNS = {
    "normalized_yield": "formation_efficiency_per_solar_mass",
    "delay_time": ("delay_time", "Myr"),
    "metallicity": "metallicity",
}
"""What to put in SSPC's ``data_column_dict`` for a GROWL file. For delay_time SSPC needs an
astropy unit: ``{"column_name": "delay_time", "unit": astropy.units.Myr}``."""

REPORT_FIELDS = [
    "group_standard", "group_in_file", "column_standard", "column_in_file", "match",
    "unit_standard", "dtype_standard", "dtype_in_file", "n_rows", "student_notes",
]
"""Columns of the report. ``match`` is one of:

    exact          same group and column name as the standard
    alias          found under a known other name (group and/or column)
    missing        standard column not in the file (or its whole group is missing)
    extra          column in the file that the standard list does not have
    extra_group    whole group in the file that the standard list does not have
"""


def _empty_row(**values):
    row = {k: "" for k in REPORT_FIELDS}
    row.update(values)
    return row


def _n_rows(d):
    shape = getattr(d, "shape", None)
    return shape[0] if shape else ""


def _find_group(file_groups, standard_group):
    """Return (name_in_file, how) for a standard group, or (None, 'missing')."""
    candidates = [standard_group] + STANDARD_GROUPS[standard_group]["aliases"]
    for i, pattern in enumerate(candidates):
        for g in file_groups:
            if fnmatch.fnmatchcase(g, pattern):
                return g, ("exact" if i == 0 else "alias")
    return None, "missing"


def compare_columns(path):
    """Compare the HDF5 file at ``path`` with the standard columns.

    Returns a list of dicts with the keys in :data:`REPORT_FIELDS`, one per standard column
    and one per extra column/group in the file.
    """
    rows = []
    with h5py.File(path, "r") as f:
        file_groups = [g for g in f.keys() if isinstance(f[g], h5py.Group)]
        matched_groups = set()

        for std_group, std_cols in STANDARD_COLUMNS.items():
            g_file, g_how = _find_group(file_groups, std_group)
            if g_file is not None:
                matched_groups.add(g_file)
            file_cols = dict(f[g_file].items()) if g_file is not None else {}
            used = set()

            for std_name, info in std_cols.items():
                row = _empty_row(group_standard=std_group, group_in_file=g_file or "",
                                 column_standard=std_name, unit_standard=info["unit"],
                                 dtype_standard=info["dtype"], match="missing")
                for i, name in enumerate([std_name] + info["aliases"]):
                    if name in file_cols:
                        d = file_cols[name]
                        used.add(name)
                        exact = i == 0 and g_how == "exact"
                        row.update(column_in_file=name, match="exact" if exact else "alias",
                                   dtype_in_file=str(d.dtype), n_rows=_n_rows(d))
                        break
                rows.append(row)

            for name, d in file_cols.items():
                if name not in used:
                    rows.append(_empty_row(group_standard=std_group, group_in_file=g_file,
                                           column_in_file=name, match="extra",
                                           dtype_in_file=str(getattr(d, "dtype", "group")),
                                           n_rows=_n_rows(d)))

        for g in file_groups:
            if g not in matched_groups:
                for name, d in f[g].items():
                    rows.append(_empty_row(group_in_file=g, column_in_file=name,
                                           match="extra_group",
                                           dtype_in_file=str(getattr(d, "dtype", "group")),
                                           n_rows=_n_rows(d)))
    return rows


def summarize(rows):
    """Return a short text summary of a :func:`compare_columns` report."""
    counts = {}
    for r in rows:
        counts[r["match"]] = counts.get(r["match"], 0) + 1
    lines = [f"Compared with GROWL standard columns version {STANDARD_COLUMNS_VERSION}:"]
    for key in ["exact", "alias", "missing", "extra", "extra_group"]:
        lines.append(f"  {key:12s} {counts.get(key, 0)}")
    missing_groups = sorted({r["group_standard"] for r in rows
                             if r["match"] == "missing" and not r["group_in_file"]})
    if missing_groups:
        lines.append("  groups missing entirely: " + ", ".join(missing_groups))
    return "\n".join(lines)


def write_report(rows, out_path):
    """Write a :func:`compare_columns` report as CSV."""
    with open(out_path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=REPORT_FIELDS)
        w.writeheader()
        w.writerows(rows)


def read_standard(path, group, columns=None):
    """Read one group of a dataset file into a pandas DataFrame with standard column names.

    ``group`` is the standard group name (e.g. "BSE_Double_Compact_Objects"); older names and
    column aliases from the standard list are found automatically. ``columns`` (standard names)
    limits what is read; by default every standard column in the file is read. Columns that are
    not in the standard list are not read: check them with :func:`compare_columns`. Byte strings
    are decoded to str.
    """
    import pandas as pd

    std_cols = STANDARD_COLUMNS[group]
    wanted = list(std_cols) if columns is None else list(columns)
    unknown = [c for c in wanted if c not in std_cols]
    if unknown:
        raise KeyError(f"not standard columns of {group}: {unknown}")
    data = {}
    with h5py.File(path, "r") as f:
        g_file, _ = _find_group([g for g in f.keys() if isinstance(f[g], h5py.Group)], group)
        if g_file is None:
            raise KeyError(f"{path} has no group {group} (or any of its other names)")
        for name in wanted:
            for candidate in [name] + std_cols[name]["aliases"]:
                if candidate in f[g_file]:
                    values = f[g_file][candidate][()]
                    if values.dtype.kind == "S":
                        values = values.astype(str)
                    data[name] = values
                    break
            else:
                if columns is not None:
                    raise KeyError(f"{path}: column {name} not found in {g_file}")
    return pd.DataFrame(data)


def _units_for(columns):
    units = {}
    for group_cols in STANDARD_COLUMNS.values():
        for name, info in group_cols.items():
            units.setdefault(name, info["unit"])
    units.update({name: info["unit"] for name, info in DERIVED_COLUMNS.items()})
    return {c: units.get(c, "") for c in columns}


def write_growl_file(path, tables, metadata, metallicity_bin_edges, n_systems_per_bin, m_rep,
                     overwrite=False):
    """Write a standardized GROWL file that SSPC can use as its input/output file.

    tables
        {name: DataFrame}, e.g. {"BBH": ..., "BHNS": ..., "BNS": ...}. Each table should hold
        standard columns plus the derived columns ``delay_time``, ``metallicity`` and
        ``formation_efficiency_per_solar_mass`` (see standard_columns.DERIVED_COLUMNS).
    metadata
        JSON-serialisable dict: dataset name, submodel, sampling setup (SamplingSetup.to_dict()),
        how M_rep was computed, number of simulated binaries, who made the file, ...
    metallicity_bin_edges, n_systems_per_bin, m_rep
        exactly what was used to compute formation_efficiency_per_solar_mass.
    """
    if os.path.exists(path) and not overwrite:
        raise FileExistsError(f"{path} exists; pass overwrite=True to replace it")
    missing = {name: [c for c in DERIVED_COLUMNS if c not in df.columns]
               for name, df in tables.items()}
    missing = {k: v for k, v in missing.items() if v}
    if missing:
        raise ValueError(f"tables are missing the derived columns: {missing}")
    edges = np.asarray(metallicity_bin_edges, dtype=float)
    n_per_bin = np.asarray(n_systems_per_bin, dtype=float)
    if len(n_per_bin) != len(edges) - 1:
        raise ValueError("n_systems_per_bin needs one entry per metallicity bin")

    with h5py.File(path, "w") as f:           # the groups SSPC requires, plus GROWL's own
        f.create_group("input_data")
        f.create_group("config")
        f.attrs["growl_file_version"] = GROWL_FILE_VERSION
        f.attrs["growl_standard_columns_version"] = STANDARD_COLUMNS_VERSION
        g = f.create_group("growl")
        g.attrs["metadata"] = json.dumps({**metadata, "m_rep_Msun": float(m_rep)})
        g["metallicity_bin_edges"] = edges
        g["n_systems_per_bin"] = n_per_bin
        g["mass_formed_per_bin"] = n_per_bin * m_rep
        g["mass_formed_per_bin"].attrs["unit"] = "Msun"

    for name, df in tables.items():
        df = df.copy()
        for c in df.columns:                   # PyTables 'table' format cannot store bytes
            if df[c].dtype == object and len(df) and isinstance(df[c].iloc[0], bytes):
                df[c] = df[c].str.decode("utf-8")
        df.reset_index(drop=True).to_hdf(path, key=f"input_data/{name}", format="table",
                                         mode="a")
        with h5py.File(path, "a") as f:
            f[f"input_data/{name}"].attrs["units"] = json.dumps(_units_for(df.columns))


def read_growl_metadata(path):
    """Return (metadata dict, metallicity_bin_edges, n_systems_per_bin) of a GROWL file."""
    with h5py.File(path, "r") as f:
        g = f["growl"]
        return (json.loads(g.attrs["metadata"]), g["metallicity_bin_edges"][()],
                g["n_systems_per_bin"][()])


def main(argv=None):
    import argparse
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("path", help="HDF5 file to check")
    p.add_argument("-o", "--out", default="column_check.csv", help="CSV report to write")
    a = p.parse_args(argv)
    rows = compare_columns(a.path)
    write_report(rows, a.out)
    print(summarize(rows))
    print(f"Report written to {a.out}")


if __name__ == "__main__":
    main()
