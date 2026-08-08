# SPDX-FileCopyrightText: (C) University at Buffalo
#
# SPDX-License-Identifier: Apache-2.0

from coldfront.slurm.models import SlurmCluster, SlurmQOS
from coldfront.tenancy.models import Tenant

from coldfront_initializer.initializers.base import (
    BaseInitializer,
    register_initializer,
)


class SlurmClusterInitializer(BaseInitializer):
    MODEL = SlurmCluster
    OPTIONAL_ASSOCS = {
        "tenant": (Tenant, "name"),
        "default_qos": (SlurmQOS, "name"),
    }
    OPTIONAL_M2M_ASSOCS = {
        "qos_list": (SlurmQOS, "name"),
    }


register_initializer("slurm_clusters", SlurmClusterInitializer)
