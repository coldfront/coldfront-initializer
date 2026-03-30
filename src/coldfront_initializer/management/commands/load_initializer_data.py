# SPDX-FileCopyrightText: (C) Tobias Genannt
# SPDX-FileCopyrightText: (C) ColdFront Authors
#
# SPDX-License-Identifier: Apache-2.0

import os
import traceback

from django.core.management.base import BaseCommand, CommandError

import coldfront_initializer
from coldfront_initializer.initializers.base import (
    INITIALIZER_ORDER,
    INITIALIZER_REGISTRY,
)


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
        target_path = options["path"]
        library = options["library"]

        if not target_path and not library:
            raise CommandError("Please provide a --path or a --library to load.")

        if target_path:
            print(target_path)
            self.load_dir(target_path)

        if library:
            self.load_library(library, options["filter"])

    def load_library(self, library, filter):
        filter = [n for name in filter for n in name.split(",") if n.strip()]

        library_base_path = os.path.dirname(coldfront_initializer.__file__)
        library_path = f"{library_base_path}/library/{library}"
        if not os.path.isdir(library_path):
            raise CommandError(f"Library directory {library_path} not found.")

        if library not in INITIALIZER_REGISTRY:
            self.stderr.write(self.style.ERROR(f"Initializer for {library} not found!"))

        initializer = INITIALIZER_REGISTRY[library]
        initializer_instance = initializer(library_path)

        with os.scandir(library_path) as yaml_files:
            for file in yaml_files:
                if not file.name.endswith("yml"):
                    continue
                if filter and file.name not in filter:
                    continue

                try:
                    records = initializer_instance.load_yaml(file.name)
                    if not records:
                        raise CommandError(f"Library file {file.name} has no records.")

                    initializer_instance.load_data(records)
                except Exception as e:
                    traceback.print_exception(e)
                    raise CommandError(
                        f"{initializer.__name__} failed loading library file {file}."
                    ) from e

    def load_dir(self, target_path):
        if not os.path.isdir(target_path):
            raise CommandError("Path must be a directory.")

        for initializer_name in INITIALIZER_ORDER:
            if initializer_name not in INITIALIZER_REGISTRY:
                self.stderr.write(
                    self.style.ERROR(f"Initializer for {initializer_name} not found!")
                )
                continue

            initializer = INITIALIZER_REGISTRY[initializer_name]
            initializer_instance = initializer(target_path)
            try:
                records = initializer_instance.load_yaml(f"{initializer_name}.yml")
                initializer_instance.load_data(records)
            except Exception as e:
                traceback.print_exception(e)
                raise CommandError(f"{initializer.__name__} failed.") from e
