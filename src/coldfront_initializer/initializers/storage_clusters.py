# SPDX-FileCopyrightText: (C) University at Buffalo
#
# SPDX-License-Identifier: Apache-2.0

from coldfront.storage.models import StorageCluster

from coldfront_initializer.initializers.base import (
    BaseInitializer,
    register_initializer,
)


class StorageClusterInitializer(BaseInitializer):
    MODEL = StorageCluster


register_initializer("storage_clusters", StorageClusterInitializer)
