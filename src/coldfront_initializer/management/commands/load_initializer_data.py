# SPDX-FileCopyrightText: (C) University at Buffalo
#
# SPDX-License-Identifier: Apache-2.0

import logging
import os

from django.core.management.base import BaseCommand, CommandError

import coldfront_initializer
from coldfront_initializer.initializers.base import (
    INITIALIZER_ORDER,
    INITIALIZER_REGISTRY,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Load data from YAML files into ColdFront"
    requires_migrations_checks = True

    def add_arguments(self, parser):
        parser.add_argument("--path", help="Path of the initial data YAMLs")
        parser.add_argument("--library", help="Name of the library to load")
        parser.add_argument(
            "--filter",
            nargs="+",
            help="List of file names to load from the library",
            default="",
        )

    def handle(self, *args, **options):
        verbosity = options.get("verbosity", 1)
        self._configure_logging(verbosity)

        target_path = options["path"]
        library = options["library"]

        if not target_path and not library:
            raise CommandError("Please provide a --path or a --library to load.")

        if target_path:
            self.load_dir(target_path, verbosity)

        if library:
            self.load_library(library, options["filter"], verbosity)

    def _configure_logging(self, verbosity):
        """Configure the coldfront_initializer logger to output through
        Django's styled streams, respecting the verbosity level.

        Verbosity levels:
            0  (quiet)     — only WARNING and above
            1  (normal)    — INFO and above (default)
            2  (verbose)   — DEBUG and above
            3  (debug)     — DEBUG and above (same as 2)
        """
        coldfront_logger = logging.getLogger("coldfront_initializer")
        # Remove any existing handlers to avoid duplicates
        for handler in coldfront_logger.handlers[:]:
            coldfront_logger.removeHandler(handler)
        # Child loggers (e.g. coldfront_initializer.initializers.users)
        # will propagate to this logger
        coldfront_logger.propagate = True

        # Single handler that writes everything to stdout via Django's stream
        handler = logging.StreamHandler(self.stdout)
        handler.setFormatter(logging.Formatter("%(message)s"))
        coldfront_logger.addHandler(handler)

        if verbosity >= 2:
            coldfront_logger.setLevel(logging.DEBUG)
        elif verbosity >= 1:
            coldfront_logger.setLevel(logging.INFO)
        else:
            coldfront_logger.setLevel(logging.WARNING)

    def _count_records(self, records):
        """Return the number of records in a YAML data set."""
        if records is None:
            return 0
        if isinstance(records, dict):
            return len(records)
        if isinstance(records, list):
            return len(records)
        return 0

    def load_library(self, library, filter, verbosity):
        filter = [n for name in filter for n in name.split(",") if n.strip()]

        library_base_path = os.path.dirname(coldfront_initializer.__file__)
        library_path = f"{library_base_path}/library/{library}"
        if not os.path.isdir(library_path):
            raise CommandError(f"Library directory {library_path} not found.")

        if library not in INITIALIZER_REGISTRY:
            self.stderr.write(self.style.ERROR(f"Initializer for {library} not found!"))
            return

        initializer = INITIALIZER_REGISTRY[library]
        initializer_instance = initializer(library_path)

        results = []

        with os.scandir(library_path) as yaml_files:
            for file in yaml_files:
                if not file.name.endswith("yml"):
                    continue
                if filter and file.name not in filter:
                    continue

                file_stem = file.name.removesuffix(".yml")
                try:
                    records = initializer_instance.load_yaml(file.name)
                    if not records:
                        self.stderr.write(
                            self.style.WARNING(
                                f"Library file {file.name} has no records, skipping"
                            )
                        )
                        continue

                    count = self._count_records(records)
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Loading {library}/{file.name}... {count} records found"
                        )
                    )
                    initializer_instance.load_data(records)
                    results.append((file_stem, True, count, None))
                except Exception as e:
                    self.stderr.write(
                        self.style.ERROR(f"{library}/{file.name} failed: {e}")
                    )
                    if verbosity >= 2:
                        import traceback

                        traceback.print_exception(e)
                    results.append((file_stem, False, 0, str(e)))

        self._print_summary(results, library)

    def load_dir(self, target_path, verbosity):
        if not os.path.isdir(target_path):
            raise CommandError("Path must be a directory.")

        results = []

        for initializer_name in INITIALIZER_ORDER:
            if initializer_name not in INITIALIZER_REGISTRY:
                self.stderr.write(
                    self.style.ERROR(f"Initializer for {initializer_name} not found!")
                )
                continue

            initializer = INITIALIZER_REGISTRY[initializer_name]
            initializer_instance = initializer(target_path)

            try:
                self.stdout.write(
                    self.style.SUCCESS(f"Loading {initializer_name}... "), ending=""
                )
                records = initializer_instance.load_yaml(f"{initializer_name}.yml")
                count = self._count_records(records)

                if records is None:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Skipping {initializer_name}: no YAML file found"
                        )
                    )
                    continue

                initializer_instance.load_data(records)
                self.stdout.write(self.style.SUCCESS(f"{count} records loaded"))
                results.append((initializer_name, True, count, None))
            except Exception as e:
                self.stderr.write(
                    self.style.ERROR(f"{initializer.__name__} failed: {e}")
                )
                if verbosity >= 2:
                    import traceback

                    traceback.print_exception(e)
                results.append((initializer_name, False, 0, str(e)))

        self._print_summary(results, "initializers")

    def _print_summary(self, results, label):
        """Print a summary table of all loaded initializers."""
        if not results:
            return

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"─── {label} summary ───"))
        success_count = 0
        total_records = 0

        for name, success, count, error in results:
            if success:
                self.stdout.write(self.style.SUCCESS(f"  ✅ {name}: {count} records"))
                success_count += 1
                total_records += count
            else:
                self.stdout.write(self.style.ERROR(f"  ❌ {name}: FAILED — {error}"))

        self.stdout.write(
            self.style.SUCCESS(
                f"Loaded {success_count}/{len(results)} {label}"
                f" ({total_records} total records)"
            )
        )
        self.stdout.write("")
