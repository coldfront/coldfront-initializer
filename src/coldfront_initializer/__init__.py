# SPDX-FileCopyrightText: (C) ColdFront Authors
#
# SPDX-License-Identifier: Apache-2.0

from coldfront.plugins import PluginConfig

from .version import __version__


class ColdFrontInitializerConfig(PluginConfig):
    name = "coldfront_initializer"
    verbose_name = "ColdFront Initializer"
    version = __version__
    description = "Load initial data into ColdFront"
    author = "Andrew E. Bruno"
    author_email = "aebruno2@buffalo.edu"
    min_version = "2.0.0"
    default_settings = {}


config = ColdFrontInitializerConfig
