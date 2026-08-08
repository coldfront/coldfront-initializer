# SPDX-FileCopyrightText: (C) University at Buffalo
#
# SPDX-License-Identifier: Apache-2.0

from coldfront.slurm.models import SlurmAccount, SlurmCluster, SlurmQOS

from coldfront_initializer.initializers.base import (
    BaseInitializer,
    register_initializer,
)


class SlurmAccountInitializer(BaseInitializer):
    MODEL = SlurmAccount
    REQUIRED_ASSOCS = {
        "cluster": (SlurmCluster, "name"),
    }
    OPTIONAL_M2M_ASSOCS = {
        "qos_add": (SlurmQOS, "name"),
        "qos_remove": (SlurmQOS, "name"),
    }
    MATCH_PARAMS = ["name", "cluster"]


register_initializer("slurm_accounts", SlurmAccountInitializer)
