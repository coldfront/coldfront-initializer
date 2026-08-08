# SPDX-FileCopyrightText: (C) University at Buffalo
#
# SPDX-License-Identifier: Apache-2.0

from coldfront.slurm.models import SlurmQOS

from coldfront_initializer.initializers.base import (
    BaseInitializer,
    register_initializer,
)


class SlurmQOSInitializer(BaseInitializer):
    MODEL = SlurmQOS


register_initializer("slurm_qos", SlurmQOSInitializer)
