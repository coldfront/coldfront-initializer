# AGENTS.md — ColdFront Initializer Plugin

## Overview

`coldfront-initializer` is a Django plugin (app) for [ColdFront](https://github.com/coldfront/coldfront), an HPC resource allocation system. It loads initial data from YAML files into the ColdFront database. This is useful for:

- **Importing data** into a fresh ColdFront 2.x instance from YAML definitions
- **Migrating** from ColdFront 1.1.x to 2.0.x by exporting data to YAML and re-importing
- **Testing** with realistic fixture data

---

## Project Structure (Key Locations)

```
src/coldfront_initializer/
├── __init__.py                        # PluginConfig (Django app registration)
├── version.py                         # Version string
├── initializers/                      # One initializer per model type
│   ├── base.py                        # BaseInitializer class, INITIALIZER_ORDER, registry
│   └── <model>_initializer.py         # One file per model (e.g., users.py, projects.py)
├── management/commands/
│   ├── load_initializer_data.py       # Loads YAML files into ColdFront DB
│   ├── copy_initializer_examples.py   # Copies example YAMLs to a path
│   └── load_test_data.py              # Wrapper that loads examples/ as test data
├── examples/                          # Example YAML files (used as test data)
│   └── *.yml                          # One file per initializer, named <initializer_name>.yml
└── library/                           # Community-maintained library of initial data
    └── custom_fields/
        └── custom_fields.yml
```

- **Initializers** live in `src/coldfront_initializer/initializers/`, one file per model
- **Example YAML files** live in `src/coldfront_initializer/examples/`, one per initializer
- **Library YAML files** live in `src/coldfront_initializer/library/<name>/` — these are community-maintained data sets (e.g., standard custom fields for HPC centers) that can be loaded with `--library`

---

## Architecture

### How It Works

Each ColdFront model type has a dedicated **initializer class** in `initializers/`. All extend `BaseInitializer` (defined in `base.py`). The **load order** is defined by `INITIALIZER_ORDER` in `base.py` — this matters because some models depend on others.

Each initializer is registered in `INITIALIZER_REGISTRY` via `register_initializer()`. The `initializers/__init__.py` imports all modules to trigger registration.

### BaseInitializer (`base.py`) — The Generic Pipeline

Most initializers need no custom `load_data` method. Instead, they declare **class variables** that configure a generic pipeline in `BaseInitializer`:

| Class Variable | Purpose | Default |
|---|---|---|
| `MODEL` | The Django model class (required) | `None` |
| `REQUIRED_ASSOCS` | Required FK lookups `{param: (Model, field)}` | `{}` |
| `OPTIONAL_ASSOCS` | Optional FK lookups (null-safe) `{param: (Model, field)}` | `{}` |
| `OPTIONAL_M2M_ASSOCS` | Optional M2M relations `{param: (Model, field)}` | `{}` |
| `RECORDS_ARE_DICT` | YAML records are dict-keyed (key = identifier) | `False` |
| `PRIMARY_KEY` | Field name for dict-keyed record keys | `"name"` |
| `MATCH_PARAMS` | Unique fields for `get_or_create` | `None` → `["name", "slug"]` |

The generic `load_data` pipeline:

1. **Normalize records** — converts dict-keyed YAML into list-of-params format
2. **`_pre_process(params)` hook** — color mapping, schema validation, resource_object parsing
3. **Pop well-known params** — `custom_field_data`, `tags`, `created` (only if model supports them)
4. **Resolve required FKs** — looks up model instances by field value
5. **Resolve optional FKs** — same, but null-safe (handles `None`/`"null"`, catches `DoesNotExist`)
6. **Collect M2M values** — pops M2M params before `split_params`
7. **`split_params` + `get_or_create`** — creates or retrieves the model instance
8. **Set M2M values** — applies collected M2M relations after creation
9. **`_post_process(obj, created, params)` hook** — project users, permissions, choices
10. **Set custom fields and tags**

Model capabilities (custom fields, tags, created date, slug field) are **inferred at runtime** via `hasattr()` and `_meta.get_field()`, not declared as flags.

### Simple Initializer Example

```python
class TenantInitializer(BaseInitializer):
    MODEL = Tenant
    OPTIONAL_ASSOCS = {"group": (TenantGroup, "name")}
```

This single class does everything — no `load_data` method needed.

### Initializer with Hooks

```python
class ProjectInitializer(BaseInitializer):
    MODEL = Project
    REQUIRED_ASSOCS = {"owner": (User, "username")}
    OPTIONAL_ASSOCS = {"tenant": (Tenant, "name"), "group": (Group, "name")}

    def _pre_process(self, params):
        self._usernames = params.pop("users", [])

    def _post_process(self, obj, created, params):
        for username in self._usernames:
            user = User.objects.get(username=username)
            ProjectUser.objects.get_or_create(user=user, project=obj)
```

### Dict-Keyed Initializer

When YAML records use identifiers as keys (e.g., `username: {details...}`), set `RECORDS_ARE_DICT = True` and `PRIMARY_KEY` to the identifier field. The generic pipeline normalizes these into list-of-params format automatically.

---

## Management Commands

1. **`load_initializer_data`** — Main command. Loads YAML files from `--path` or `--library`. Reads files in `INITIALIZER_ORDER`, each named `<initializer_name>.yml`.
2. **`copy_initializer_examples`** — Copies example YAML files to a user-specified directory.
3. **`load_test_data`** — Convenience wrapper that calls `load_initializer_data --path <examples_dir>`.

---

## YAML File Conventions

- Each YAML file corresponds to one initializer type (e.g., `users.yml`, `projects.yml`).
- Two formats are supported:
  - **List format** (most initializers): `- name: foo\n  slug: bar\n  ...`
  - **Dict format** (users, groups, roles, etc.): `username:\n  password_hash: ...`
- If the first line is `# cf_template`, the file is treated as a Jinja2 template.
- Custom fields are specified under `custom_field_data` (legacy `custom_fields` is supported with a warning).
- Tags are specified under `tags`.
- Foreign key references use string names that are resolved by `resolve_optional` / `resolve_required`.

---

## Adding a New Initializer

1. Create a file in `initializers/` (e.g., `my_model.py`).
2. Define a class extending `BaseInitializer` with `MODEL = MyModel`.
3. Add `REQUIRED_ASSOCS`, `OPTIONAL_ASSOCS`, `OPTIONAL_M2M_ASSOCS` as needed.
4. If records are dict-keyed, set `RECORDS_ARE_DICT = True` and `PRIMARY_KEY`.
5. If special pre/post processing is needed, override `_pre_process` / `_post_process`.
6. If the pipeline doesn't fit (rare), override `load_data` entirely.
7. Call `register_initializer("my_model", MyModelInitializer)` at module level.
8. Add the import to `initializers/__init__.py`.
9. Add `"my_model"` to `INITIALIZER_ORDER` in `base.py` at the correct position.
10. Create an example YAML file in `examples/my_model.yml`.

### Common patterns

- **FK resolution**: Add entries to `REQUIRED_ASSOCS` or `OPTIONAL_ASSOCS`. The model class can be a string (e.g., `"users.Group"`) for lazy imports.
- **M2M resolution**: Add entries to `OPTIONAL_M2M_ASSOCS`. Values are collected before `split_params` and applied after creation.
- **Dict-keyed records**: Set `RECORDS_ARE_DICT = True`. The key becomes `PRIMARY_KEY` in the normalized params.
- **Skip a record on error**: Set `params["_skip"] = True` in `_pre_process` and override `load_data` to check for it.
- **Null handling**: Optional FKs automatically handle `None` / `"null"` strings and `DoesNotExist` gracefully.
- **String model references**: Use `"app.Model"` format (e.g., `"users.Group"`, `"coldfront.ras.models.Project"`). The resolver uses `django.apps.apps.get_model()`.

---

## Dependencies

- `coldfront` (installed separately, imported at runtime)
- `jinja2>=3.1.6` — template rendering for YAML files
- `ruamel-yaml>=0.19.1` — YAML parsing (safe loader)
- Dev: `ruff>=0.15.7`, `reuse>=6.2.0` (REUSE compliance)

---

## Coding Conventions

- **Formatter**: `ruff format`
- **Linter**: `ruff check --fix`
- **Run**: `uv run ruff format && uv run ruff check --fix`
- **Python**: 3.12+
- **Build system**: `uv` with `uv_build`
- **Logging**: Use `logging.getLogger(__name__)` — never `print()`.
- **SPDX headers**: Every `.py` file starts with an SPDX copyright header.

---

## Common Tasks

```bash
# Load test data
uv run coldfront load_test_data -f

# Load custom YAML from a directory
uv run coldfront load_initializer_data --path /path/to/yaml/files

# Copy example files for editing
uv run coldfront copy_initializer_examples --path /path/for/example/files

# Format/lint code
uv run ruff format
uv run ruff check --fix

# Build and publish
uv build
uv publish
```

---

## Key Notes for Agents

- **All initializers are registered via import** in `initializers/__init__.py`. Don't forget to add new imports there.
- **Load order** in `INITIALIZER_ORDER` must be maintained — some models depend on others.
- **Model capabilities are inferred** — you don't need to declare `supports_custom_fields` or `supports_tags`. The base class checks `hasattr()` at runtime.
- **`_pre_process` and `_post_process`** are no-ops by default. Only override them when needed.
- **For M2M fields**, pop the values in `_pre_process` and store them as instance variables. They would otherwise end up in `defaults` and cause `DirectAssignment` errors.
- **For models without a `slug` field**, the generic pipeline automatically pops `slug` from params if it's present in the YAML.
- **`split_params`** uses `MATCH_PARAMS` (or `["name", "slug"]` by default). For dict-keyed records, `PRIMARY_KEY` is automatically included.
