# ColdFront Initializers Plugin

This plugin loads data from yaml files into ColdFront. 

## Install

Install ColdFront and add `initializers` extra group:

```
$ uv tool install coldfront[initializers]
```

If you already have ColdFront installed you can run:

```
$ uv sync --extra initializers
```

Or install directly via pip:

```
$ uv pip install coldfront-initializers
```

Next add the plugin to the `PLUGINS` setting in your ColdFront configuration:

```
PLUGINS="coldfront_initializer"
```

## Loading data

Load ColdFront test data (NOT FOR PRODUCTION USE):

```
$ uv run coldfront load_test_data
```

Copy the example test data files so you can edit/update:

```
$ uv run coldfront copy_initializers_examples --path /path/for/example/files
```

Load data from a directory:

```
$ uv run coldfront load_initializer_data --path /path/to/yaml/files
```

## Community supported library of initial data

The ColdFront community maintians a library of common initial data available for importing into your ColdFront instance.  To load run:

```
$ uv run coldfront load_initializer_data --library resource_types
```

### Resource Types

- Slurm Cluster, Slurm Partition

## Credits

This plugin was adopted from https://github.com/tobiasge/netbox-initializers written by Tobias Genannt.

## License

Apache 2.0
