# SPDX-FileCopyrightText: (C) Tobias Genannt
# SPDX-FileCopyrightText: (C) ColdFront Authors
#
# SPDX-License-Identifier: Apache-2.0

import os
import traceback
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

import coldfront_initializer.initializers
from coldfront_initializer.initializers.base import (
    INITIALIZER_ORDER,
    INITIALIZER_REGISTRY,
)


class Command(BaseCommand):
    help = "Copy initializer example files to user specified directory"

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            action="store",
            dest="path",
            help="Path where the examples should be placed",
            required=True,
        )

    def handle(self, *args, **options):
        target_path = options["path"]
        if not target_path:
            raise CommandError("Path cannot be empty.")

        if not os.path.isdir(target_path):
            raise CommandError("Path must be a directory.")

        intializer_base_path = os.path.dirname(
            coldfront_initializer.initializers.__file__
        )
        intializer_path = f"{intializer_base_path}/yaml"

        warnings = 0
        for initializer_name in INITIALIZER_ORDER:
            if initializer_name not in INITIALIZER_REGISTRY:
                self.stderr.write(
                    self.style.ERROR(f"Initializer for {initializer_name} not found!")
                )
                continue

            initializer = INITIALIZER_REGISTRY[initializer_name]
            initializer_instance = initializer(intializer_path)

            dst_file = f"{target_path}/{initializer_name}.yml"
            if os.path.isfile(dst_file):
                self.stdout.write(
                    self.style.WARNING(
                        f"Warning: Destination file exists for {initializer_name}.yml, File will not be copied."
                    )
                )
                warnings += 1
                continue
            try:
                initializer_instance.dump_data(Path(dst_file))
            except Exception as e:
                traceback.print_exception(e)
                raise CommandError(f"Copy {initializer.__name__} failed.") from e

        self.stdout.write(
            self.style.SUCCESS(
                f"Copied initializer examples to '{target_path}' with {warnings} warnings."
            )
        )
