# SPDX-FileCopyrightText: (C) University at Buffalo
#
# SPDX-License-Identifier: Apache-2.0

from coldfront.storage.models import StorageCluster, StorageResource

from coldfront_initializer.initializers.base import (
    BaseInitializer,
    register_initializer,
)


class StorageResourceInitializer(BaseInitializer):
    MODEL = StorageResource
    OPTIONAL_M2M_ASSOCS = {
        "clusters": (StorageCluster, "name"),
    }
    MATCH_PARAMS = ["name"]


register_initializer("storage_resources", StorageResourceInitializer)
