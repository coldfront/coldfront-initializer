# SPDX-FileCopyrightText: (C) University at Buffalo
#
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

import pytest

from coldfront_initializer.initializers.base import (
    INITIALIZER_ORDER,
    INITIALIZER_REGISTRY,
)

EXAMPLES_DIR = (
    Path(__file__).resolve().parents[1] / "src" / "coldfront_initializer" / "examples"
)


@pytest.fixture
def examples_dir():
    """Path to the example YAML data sets shipped with the plugin."""
    return str(EXAMPLES_DIR)


@pytest.fixture
def load_all(examples_dir):
    """Load every initializer from the example data, in dependency order.

    Returns {initializer_name: LoadResult} (None when no YAML file exists).
    """

    def _load():
        results = {}
        for name in INITIALIZER_ORDER:
            initializer = INITIALIZER_REGISTRY[name](examples_dir)
            records = initializer.load_yaml(f"{name}.yml")
            if records is None:
                results[name] = None
                continue
            results[name] = initializer.load_data(records)
        return results

    return _load
