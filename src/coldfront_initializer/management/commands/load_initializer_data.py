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

                    self.stdout.write(
                        self.style.SUCCESS(f"Loading {library}/{file.name}... "),
                        ending="",
                    )
                    result = initializer_instance.load_data(records)
                    self._print_initializer_line(file_stem, result)
                    results.append((file_stem, result, None))
                except Exception as e:
                    self.stderr.write(
                        self.style.ERROR(f"{library}/{file.name} failed: {e}")
                    )
                    if verbosity >= 2:
                        import traceback

                        traceback.print_exception(e)
                    results.append((file_stem, None, str(e)))

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

                if records is None:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Skipping {initializer_name}: no YAML file found"
                        )
                    )
                    continue

                result = initializer_instance.load_data(records)
                self._print_initializer_line(initializer_name, result)
                results.append((initializer_name, result, None))
            except Exception as e:
                self.stderr.write(
                    self.style.ERROR(f"{initializer.__name__} failed: {e}")
                )
                if verbosity >= 2:
                    import traceback

                    traceback.print_exception(e)
                results.append((initializer_name, None, str(e)))

        self._print_summary(results, "initializers")

    def _print_initializer_line(self, name, result):
        """Print the per-initializer inline outcome (parsed/loaded/skipped/failed)."""
        parts = []
        if result.found:
            parts.append(f"parsed {result.found}")
        if result.loaded:
            parts.append(f"loaded {result.loaded}")
        if result.skipped:
            parts.append(f"skipped {result.skipped}")
        if result.errors:
            parts.append(f"failed {len(result.errors)}")

        line = ", ".join(parts)
        if result.errors:
            self.stdout.write(self.style.ERROR(line))
        else:
            self.stdout.write(self.style.SUCCESS(line))

        for msg in result.errors:
            self.stderr.write(self.style.ERROR(f"  {name}: {msg}"))

    def _print_summary(self, results, label):
        """Print a summary table of all loaded initializers (tri-state)."""
        if not results:
            return

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"─── {label} summary ───"))
        loaded_init = 0
        issues = 0
        total_found = 0
        total_loaded = 0
        total_skipped = 0

        for name, result, error in results:
            if result is None:
                # Whole initializer failed (parse error or raised exception)
                self.stdout.write(self.style.ERROR(f"  ❌ {name}: FAILED — {error}"))
                issues += 1
                continue

            total_found += result.found
            total_loaded += result.loaded
            total_skipped += result.skipped

            if result.errors:
                issues += 1
                self.stdout.write(
                    self.style.ERROR(
                        f"  ❌ {name}: loaded {result.loaded} of {result.found}"
                        f" ({len(result.errors)} errors)"
                    )
                )
                for msg in result.errors:
                    self.stderr.write(self.style.ERROR(f"      {name}: {msg}"))
            elif result.loaded == result.found and not result.warnings:
                self.stdout.write(
                    self.style.SUCCESS(f"  ✅ {name}: {result.loaded} records")
                )
                loaded_init += 1
            else:
                issues += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"  ⚠️ {name}: {result.loaded} of {result.found} records"
                        f" loaded ({result.skipped} skipped)"
                    )
                )
                for msg in result.warnings:
                    self.stderr.write(self.style.WARNING(f"      {name}: {msg}"))

        self.stdout.write(
            self.style.SUCCESS(
                f"Loaded {loaded_init}/{len(results)} {label}"
                f" ({total_found} found, {total_loaded} loaded,"
                f" {total_skipped} skipped)"
            )
        )
        if issues:
            self.stdout.write(self.style.WARNING(f"{issues} {label} had issues"))
        self.stdout.write("")
