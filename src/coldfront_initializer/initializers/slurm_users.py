# SPDX-FileCopyrightText: (C) University at Buffalo
#
# SPDX-License-Identifier: Apache-2.0

import logging

from django.conf import settings

from coldfront.slurm.models import SlurmAccount, SlurmCluster, SlurmQOS, SlurmUser

from coldfront_initializer.initializers.base import (
    BaseInitializer,
    register_initializer,
)

logger = logging.getLogger(__name__)

ADMIN_LEVEL_MAP = {
    "None": 0,
    "Operator": 1,
    "Admin": 2,
}


class SlurmUserInitializer(BaseInitializer):
    MODEL = SlurmUser
    REQUIRED_ASSOCS = {
        "user": (settings.AUTH_USER_MODEL, "username"),
        "cluster": (SlurmCluster, "name"),
    }
    OPTIONAL_ASSOCS = {
        "default_account": (SlurmAccount, "name"),
        "default_qos": (SlurmQOS, "name"),
    }
    MATCH_PARAMS = ["user", "cluster"]

    def _pre_process(self, params):
        if "admin_level" in params:
            val = params["admin_level"]
            if val is None or val == "null":
                params["admin_level"] = None
            else:
                params["admin_level"] = ADMIN_LEVEL_MAP.get(val, val)


register_initializer("slurm_users", SlurmUserInitializer)
