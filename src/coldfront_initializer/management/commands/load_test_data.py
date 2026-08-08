# SPDX-FileCopyrightText: (C) University at Buffalo
#
# SPDX-License-Identifier: Apache-2.0

import os

from django.core.management import call_command
from django.core.management.base import BaseCommand

import coldfront_initializer


class Command(BaseCommand):
    help = "Load test data example YAML files into ColdFront"
    requires_migrations_checks = True

    def add_arguments(self, parser):
        parser.add_argument(
            "-f",
            "--force",
            help="Force lodaing test data with no warning.",
            action="store_true",
        )

    def handle(self, *args, **options):
        verbosity = options.get("verbosity", 1)

        if not options["force"]:
            self.stdout.write(
                self.style.WARNING(
                    """WARNING: Running this command loads fake test data into the ColdFront database. DO NOT USE IN PRODUCTION!"""
                )
            )
            user_response = input("Do you want to proceed?(yes):")

            if user_response != "yes":
                self.stdout.write("Please enter 'yes' if you wish to load test data.")
                return

        intializer_base_path = os.path.dirname(coldfront_initializer.__file__)
        intializer_path = f"{intializer_base_path}/examples"

        call_command(
            "load_initializer_data", "--path", intializer_path, verbosity=verbosity
        )
