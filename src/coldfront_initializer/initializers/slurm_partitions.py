# SPDX-FileCopyrightText: (C) University at Buffalo
#
# SPDX-License-Identifier: Apache-2.0

from coldfront.slurm.models import SlurmAccount, SlurmCluster, SlurmPartition, SlurmQOS

from coldfront_initializer.initializers.base import (
    BaseInitializer,
    register_initializer,
)


class SlurmPartitionInitializer(BaseInitializer):
    MODEL = SlurmPartition
    REQUIRED_ASSOCS = {
        "cluster": (SlurmCluster, "name"),
    }
    OPTIONAL_ASSOCS = {
        "qos": (SlurmQOS, "name"),
    }
    OPTIONAL_M2M_ASSOCS = {
        "allow_qos": (SlurmQOS, "name"),
        "allow_groups": ("users.Group", "name"),
        "allow_accounts": (SlurmAccount, "name"),
    }
    MATCH_PARAMS = ["name", "cluster"]


register_initializer("slurm_partitions", SlurmPartitionInitializer)
