"""Inspect actual native build metadata; never execute a foreign Linux binary."""

import json
import shutil
import subprocess  # nosec B404
from pathlib import Path

import pytest
from packaging.version import Version

ROOT = Path(__file__).resolve().parents[1]
DRIVER = "github.com/snowflakedb/gosnowflake/v2"


@pytest.mark.packaged
@pytest.mark.skipif(shutil.which("go") is None, reason="static Go build-info check needs Go")
@pytest.mark.parametrize("target", ["linux-amd64", "linux-arm64"])
def test_shipped_driver_excludes_diagnostic_credential_leak(target):
    """A stale binary or dependency downgrade must block the release."""
    result = subprocess.run(  # nosec B603 B607: fixed static Go inspector and bundled artifact
        ["go", "version", "-m", str(ROOT / "bin" / target / "toolbox")],
        text=True,
        capture_output=True,
        check=True,
    )
    modules = {}
    for line in result.stdout.splitlines():
        fields = line.split()
        if fields and fields[0] == "dep":
            modules[fields[1]] = fields[2]
        assert not (fields and fields[0] == "=>"), "unrecorded module replacement"
    version = Version(modules[DRIVER].removeprefix("v"))
    assert version >= Version("2.2.0"), "CVE-2026-86597: diagnostic logs can leak credentials"
    provenance = json.loads((ROOT / "toolbox-provenance.json").read_text())
    assert modules == provenance["binaries"][target]["go_modules"], (
        "provenance must describe actual binary dependencies"
    )
