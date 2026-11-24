from pathlib import Path

import h5py
import numpy as np
import pytest

from growl_tools.standard_columns import (STANDARD_COLUMNS, STANDARD_GROUPS, iter_columns,
                                          standard_columns_markdown)
from growl_tools.standard_format import compare_columns, write_report, summarize

REQUIRED_FIELDS = {"dtype", "unit", "description", "aliases", "notes", "status"}
TUTORIAL_FILE = Path("~/Projects/GitHub/GROWL-catalog-public/onboarding_growl/data/"
                     "vanSon2022_data/COMPAS_Output_wWeights.h5").expanduser()


def test_every_column_is_documented():
    assert set(STANDARD_COLUMNS) == set(STANDARD_GROUPS)
    for group, name, info in iter_columns():
        assert set(info) == REQUIRED_FIELDS, (group, name)
        assert info["description"].strip(), (group, name)
        assert info["status"] in {"to_check", "checked"}, (group, name)


def test_docs_page_is_up_to_date():
    page = Path(__file__).parents[1] / "docs" / "standard_columns.md"
    assert page.read_text() == standard_columns_markdown() + "\n", \
        "run: python -m growl_tools.standard_columns > docs/standard_columns.md"


def test_compare_columns(tmp_path):
    path = tmp_path / "toy.h5"
    with h5py.File(path, "w") as f:
        dco = f.create_group("DoubleCompactObjects")       # older group name = alias
        dco["SEED"] = np.arange(3, dtype="uint64")
        dco["Mass(1)"] = np.ones(3)
        dco["SemiMajorAxis@DCO"] = np.ones(3)              # not in the standard list
        f.create_group("BSE_Supernovae")["SEED"] = np.arange(2)
    rows = compare_columns(path)
    by = {(r["group_standard"], r["column_standard"] or r["column_in_file"]): r for r in rows}

    assert by[("BSE_Double_Compact_Objects", "Mass(1)")]["match"] == "alias"
    assert by[("BSE_Double_Compact_Objects", "Mass(2)")]["match"] == "missing"
    assert by[("BSE_Double_Compact_Objects", "SemiMajorAxis@DCO")]["match"] == "extra"
    assert by[("", "SEED")]["match"] == "extra_group"
    assert by[("BSE_System_Parameters", "SEED")]["group_in_file"] == ""
    assert "BSE_System_Parameters" in summarize(rows)
    write_report(rows, tmp_path / "column_check.csv")


@pytest.mark.skipif(not TUTORIAL_FILE.exists(), reason="tutorial file not available")
def test_reference_file_matches_standard_exactly():
    rows = compare_columns(TUTORIAL_FILE)
    assert {r["match"] for r in rows} == {"exact"}
    for r in rows:
        assert r["dtype_in_file"] == r["dtype_standard"].replace("bytes (S17)", "|S17"), r


def test_write_growl_file_is_readable_like_sspc(tmp_path):
    pd = pytest.importorskip("pandas")
    pytest.importorskip("tables")
    import json
    from growl_tools.standard_format import write_growl_file, read_growl_metadata

    df = pd.DataFrame({
        "Mass(1)": np.arange(10.0), "MT_Donor_Hist(1)": np.array([b"2-4"] * 10, dtype=object),
        "delay_time": np.ones(10), "metallicity": np.full(10, 1e-3),
        "formation_efficiency_per_solar_mass": np.full(10, 1e-5)})
    path = tmp_path / "growl.h5"
    write_growl_file(path, {"BBH": df}, {"dataset": "toy"}, [1e-4, 1e-3, 1e-2], [5, 5], 100.0)

    chunk = pd.read_hdf(path, "/input_data/BBH", start=3, stop=6)   # SSPC's chunked readout
    assert list(chunk["Mass(1)"]) == [3.0, 4.0, 5.0]
    assert chunk["MT_Donor_Hist(1)"].iloc[0] == "2-4"
    with h5py.File(path, "r") as f:
        assert {"input_data", "config", "growl"} <= set(f.keys())        # SSPC needs the first two
        units = json.loads(f["input_data/BBH"].attrs["units"])
    assert units["Mass(1)"] == "Msun" and units["delay_time"] == "Myr"
    meta, edges, n_j = read_growl_metadata(path)
    assert meta["m_rep_Msun"] == 100.0 and len(edges) == 3 and list(n_j) == [5, 5]
    with pytest.raises(FileExistsError):
        write_growl_file(path, {"BBH": df}, {}, [1e-4, 1e-3, 1e-2], [5, 5], 100.0)
    with pytest.raises(ValueError):
        write_growl_file(path, {"BBH": df[["Mass(1)"]]}, {}, [1e-4, 1e-2], [5], 100.0,
                         overwrite=True)
