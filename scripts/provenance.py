#!/usr/bin/env python3
"""Record pinned native build provenance and per-target SHA-256 values."""

import hashlib
import json
import subprocess  # nosec B404
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGETS = ("linux-amd64", "linux-arm64")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def binary_modules(path):
    # Static inspection only: the Linux payload is never run on the build host.
    info = subprocess.run(  # nosec B603 B607: fixed Go tool and local build artifact
        ["go", "version", "-m", str(path)], check=True, capture_output=True, text=True
    )
    modules = {}
    for line in info.stdout.splitlines():
        fields = line.split()
        if fields and fields[0] == "=>":
            raise ValueError("Module replacements must be explicitly recorded before release")
        if fields and fields[0] == "dep":
            modules[fields[1]] = fields[2]
    if modules.get("github.com/snowflakedb/gosnowflake/v2") != "v2.2.0":
        raise ValueError("Built Snowflake driver does not match the pinned security patch")
    return modules


def main():
    records = {
        target: {
            "path": f"bin/{target}/toolbox",
            "go_modules": binary_modules(ROOT / f"bin/{target}/toolbox"),
            "sha256": digest(ROOT / f"bin/{target}/toolbox"),
            "size": (ROOT / f"bin/{target}/toolbox").stat().st_size,
        }
        for target in TARGETS
    }
    data = {
        "upstream_commit": "b0010060a939455d91e4f8ba62dc3e72b1892469",
        "upstream_tag": "v1.3.0",
        "source": "https://github.com/googleapis/mcp-toolbox",
        "go_image": (
            "golang:1.26.2-bookworm@sha256:"
            "47ce5636e9936b2c5cbf708925578ef386b4f8872aec74a67bd13a627d242b19"
        ),
        "registered_prebuilts": (ROOT / "scripts/toolbox-prebuilts.txt").read_text().split(),
        "patch_sha256": digest(
            ROOT / "scripts/patches/0001-flowsteward-driver-bound-query-params.patch"
        ),
        "dependency_patches": {
            "scripts/patches/0002-snowflake-driver-security.patch": digest(
                ROOT / "scripts/patches/0002-snowflake-driver-security.patch"
            )
        },
        "binaries": records,
    }
    (ROOT / "toolbox-provenance.json").write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    (ROOT / "SHA256SUMS").write_text(
        "".join(f"{record['sha256']}  {record['path']}\n" for record in records.values())
    )


if __name__ == "__main__":
    main()
