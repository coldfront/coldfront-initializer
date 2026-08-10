# SPDX-FileCopyrightText: (C) University at Buffalo
#
# SPDX-License-Identifier: Apache-2.0

import pytest

from coldfront_initializer.initializers.base import (
    INITIALIZER_ORDER,
    INITIALIZER_REGISTRY,
    LoadResult,
)


@pytest.mark.django_db
def test_all_initializers_return_load_result(load_all):
    """Every initializer with example data must return a LoadResult."""
    results = load_all()
    assert results
    for name in INITIALIZER_ORDER:
        result = results[name]
        if result is None:
            continue  # no example YAML for this initializer
        assert isinstance(result, LoadResult), f"{name}: expected LoadResult"


@pytest.mark.django_db
def test_example_data_loads_cleanly(load_all):
    """Example data loads without errors or skips; loaded == found."""
    results = load_all()
    for name in INITIALIZER_ORDER:
        result = results[name]
        if result is None:
            continue
        assert result.errors == [], f"{name} errors: {result.errors}"
        assert result.loaded == result.found, (
            f"{name}: loaded {result.loaded} != found {result.found}"
        )


@pytest.mark.django_db
def test_key_models_are_created(load_all):
    """The example data actually creates records in the database."""
    load_all()

    from coldfront.ras.models import Allocation, Project
    from coldfront.users.models import Group, User

    assert User.objects.count() > 0
    assert Group.objects.count() > 0
    assert Project.objects.count() > 0
    assert Allocation.objects.count() > 0


@pytest.mark.django_db
def test_loaded_records_match_db_counts(load_all):
    """Each initializer creates exactly one DB row per loaded record."""
    results = load_all()
    for name in INITIALIZER_ORDER:
        result = results[name]
        if result is None:
            continue
        model = INITIALIZER_REGISTRY[name].MODEL
        db_count = model.objects.count()
        assert result.loaded == db_count, (
            f"{name}: loaded {result.loaded} != DB {model.__name__} count {db_count}"
        )


@pytest.mark.django_db
def test_allocation_count_matches_yaml(load_all, examples_dir):
    """Allocation records loaded must match the number in the example YAML."""
    results = load_all()
    result = results["allocations"]
    assert result is not None

    initializer = INITIALIZER_REGISTRY["allocations"](examples_dir)
    records = initializer.load_yaml("allocations.yml")
    assert result.found == len(records)
    assert result.loaded == len(records)
    assert result.skipped == 0


@pytest.mark.django_db
def test_allocations_skip_counted(load_all, examples_dir, tmp_path):
    """A record with a missing resource_object is skipped and counted."""
    load_all()  # ensure users/projects/resources exist

    yaml_data = """\
- slug: a-skip-test-ok
  project: Angular momentum in QGP holography
  owner: cgray
  resource_object: "ras.resource:Commercial Software X"
- slug: a-skip-test-bad
  project: Angular momentum in QGP holography
  owner: cgray
  resource_object: "ras.resource:DoesNotExist"
"""
    (tmp_path / "allocations.yml").write_text(yaml_data)

    initializer = INITIALIZER_REGISTRY["allocations"](str(tmp_path))
    records = initializer.load_yaml("allocations.yml")
    result = initializer.load_data(records)

    assert result.found == 2
    assert result.loaded == 1
    assert result.skipped == 1
    assert result.errors == []
    assert len(result.warnings) == 1
    assert "resource_object not found" in result.warnings[0]

    # The skipped record must not exist in the DB
    from coldfront.ras.models import Allocation

    assert Allocation.objects.filter(slug="a-skip-test-ok").exists()
    assert not Allocation.objects.filter(slug="a-skip-test-bad").exists()
