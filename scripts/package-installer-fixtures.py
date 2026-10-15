#!/usr/bin/env python3
"""Build disposable packages for the isolated package-result experiment."""
from pathlib import Path
import subprocess
import sys
import tempfile

output = Path(sys.argv[1]).resolve()
output.mkdir(parents=True, exist_ok=True)
for name, version, refuse_remove in (
    ("warning", "1.0", True),
    ("cleanup", "1.0", False),
    ("upgrade", "2.0", False),
):
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        (root / "DEBIAN").mkdir()
        (root / "DEBIAN/control").write_text(
            "Package: pardus-install-result-test\n"
            f"Version: {version}\nArchitecture: all\nSection: misc\nPriority: optional\n"
            "Maintainer: Local test <test@example.invalid>\n"
            "Description: Disposable package installer result test\n"
        )
        marker = root / "usr/share/pardus-install-result-test/marker"
        marker.parent.mkdir(parents=True)
        marker.write_text(version + "\n")
        if refuse_remove:
            script = root / "DEBIAN/prerm"
            script.write_text(
                '#!/bin/sh\nif [ "$1" = remove ]; then\n'
                '  echo "Test fixture intentionally refuses removal." >&2\n'
                '  exit 42\nfi\nexit 0\n'
            )
            script.chmod(0o755)
        subprocess.run(["dpkg-deb", "--root-owner-group", "--build", str(root),
                        str(output / f"{name}.deb")], check=True)
