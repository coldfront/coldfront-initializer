# SPDX-FileCopyrightText: (C) University at Buffalo
#
# SPDX-License-Identifier: Apache-2.0

from coldfront.ras.models import Allocation, AllocationChangeRequest
from coldfront.users.models import User

from coldfront_initializer.initializers.base import (
    BaseInitializer,
    register_initializer,
)


class AllocationChangeRequestInitializer(BaseInitializer):
    MODEL = AllocationChangeRequest
    REQUIRED_ASSOCS = {
        "allocation": (Allocation, "slug"),
        "requested_by": (User, "username"),
    }
    OPTIONAL_ASSOCS = {
        "reviewer": (User, "username"),
    }
    MATCH_PARAMS = ["slug"]


register_initializer("allocation_change_requests", AllocationChangeRequestInitializer)
