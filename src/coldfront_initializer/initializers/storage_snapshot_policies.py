# SPDX-FileCopyrightText: (C) University at Buffalo
#
# SPDX-License-Identifier: Apache-2.0

from coldfront.storage.models import StorageCluster, StorageSnapshotPolicy

from coldfront_initializer.initializers.base import (
    BaseInitializer,
    register_initializer,
)


class StorageSnapshotPolicyInitializer(BaseInitializer):
    MODEL = StorageSnapshotPolicy
    OPTIONAL_ASSOCS = {
        "cluster": (StorageCluster, "name"),
    }


register_initializer("storage_snapshot_policies", StorageSnapshotPolicyInitializer)
