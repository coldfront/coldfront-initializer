# ColdFront Initializer Plugin

ColdFront initializer is a plugin for ColdFront version 2 that loads data from YAML files into the ColdFront database.

## Features

- Load data new into ColdFront 2.x.
- Migrate data from a ColdFront 1.1.x instance to a ColdFront 2.x instance.
- Load test data into a development instance.
- Import community supported data libraries into ColdFront: fields of science, permissions, roles.

## Install

Install ColdFront and add `initializer` extra group:

```
$ uv tool install coldfront[initializer]
```

If you already have ColdFront installed you can run:

```
$ uv sync --extra initializer
```

Or install directly via pip:

```
$ uv pip install coldfront-initializer
```

Next add the plugin to the `PLUGINS` setting in your ColdFront configuration:

```
PLUGINS="coldfront_initializer"
```

## Load Data

### Load the Test Data

WARNING: Do not use the test data in production.

Run this command to load the test data:

```
$ uv run coldfront load_test_data
```

### Copy the Example Files

Run this command to copy the example files to a directory:

```
$ uv run coldfront copy_initializer_examples --path /path/for/example/files
```

You can edit the copied files. Then load the edited files with the command `load_initializer_data`.

### Load Data From a Directory

Run this command to load the YAML files from a directory:

```
$ uv run coldfront load_initializer_data --path /path/to/yaml/files
```

### Example YAML Files

Each YAML file has the name of the initializer. For example, to load users into
ColdFront you create a file named `users.yml`. The YAML file format uses either
a list or a dict format. This example shows the dict format in `users.yml` where
the key of each record is the user name:

```yaml
# users.yml
admin:
  is_active: true
  is_superuser: true
  password_hash: pbkdf2_sha256$1000000$...

cgray:
  first_name: C.
  last_name: Gray
  is_active: true
  is_superuser: false
```

This example shows the list format in `projects.yml`:

```yaml
# projects.yml
- name: Angular momentum in QGP holography
  slug: p1000001
  owner: cgray
  tenant: Computer Science
  users:
    - cgray
    - astewart
  tags:
    - Faculty
  custom_field_data:
    allocation_code: 1001
```

Foreign key references use string names. The plugin resolves the names. For
example, `owner: cgray` refers to the user `cgray`. Tags are under `tags`.
Custom fields are under `custom_field_data`.

## Community Library

The ColdFront community maintains a library of common initial data. You can load this data into your ColdFront instance.

Run this command to load the `custom_fields` library:

```
$ uv run coldfront load_initializer_data --library custom_fields
```

Run this command to list the available libraries and their YAML files:

```
$ uv run coldfront load_initializer_data --list-libraries
```

The command shows the library name and the YAML files in the library.

## Credits

This plugin was adopted from https://github.com/tobiasge/netbox-initializers written by Tobias Genannt.

## License

Apache 2.0
