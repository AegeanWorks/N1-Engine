"""Test isolation: never open the owner's live database.

The application defaults ``N1_DATABASE_URL`` to ``sqlite:///./main.db``, which
is the owner's real workspace database.  The test session must point at a
throwaway file before any ``main`` module is imported, and remove it when the
session ends.
"""

from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

_TEST_ROOT = Path(tempfile.mkdtemp(prefix="n1-engine-tests-"))
os.environ.update({"N1_DATABASE_URL": f"sqlite:///{(_TEST_ROOT / 'main.db').as_posix()}"})


def pytest_sessionfinish(session, exitstatus):  # noqa: ARG001 - pytest hook shape
    shutil.rmtree(_TEST_ROOT, ignore_errors=True)
