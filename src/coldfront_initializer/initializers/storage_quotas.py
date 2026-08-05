# SPDX-FileCopyrightText: (C) ColdFront Authors
#
# SPDX-License-Identifier: Apache-2.0

from coldfront.ras.models import Allocation
from coldfront.storage.models import (
    StorageCluster,
    StorageQuota,
    StorageResource,
    StorageSnapshotPolicy,
)
from coldfront.users.models import Group, User

from coldfront_initializer.initializers.base import (
    BaseInitializer,
    register_initializer,
)

MATCH_PARAMS = ["allocation"]

REQUIRED_ASSOCS = {
    "storage": (StorageResource, "name"),
    "owning_user": (User, "username"),
    "owning_group": (Group, "name"),
}

OPTIONAL_M2M = {
    "clusters": StorageCluster,
}

OPTIONAL_FK = {
    "snapshot_policy": (StorageSnapshotPolicy, "name"),
}


class StorageQuotaInitializer(BaseInitializer):
    def load_data(self, records):
        if records is None:
            return

        for params in records:
            custom_field_data = self.pop_custom_fields(params)
            tags = params.pop("tags", None)

            # Resolve allocation by slug
            allocation_slug = params.pop("allocation", None)
            if allocation_slug is None:
                print("⚠️  StorageQuota requires 'allocation' field")
                continue

            try:
                params["allocation"] = Allocation.objects.get(slug=allocation_slug)
            except Allocation.DoesNotExist:
                print(
                    f"⚠️  Allocation with slug '{allocation_slug}' not found, "
                    "skipping StorageQuota"
                )
                continue

            # Resolve required FK references
            for assoc, details in REQUIRED_ASSOCS.items():
                if assoc in params:
                    model, field = details
                    query = {field: params.pop(assoc)}

                    params[assoc] = model.objects.get(**query)

            # Resolve optional FK references
            for assoc, details in OPTIONAL_FK.items():
                if assoc in params:
                    val = params[assoc]
                    if val is None or val == "null":
                        params[assoc] = None
                        continue
                    model, field = details
                    query = {field: val}
                    try:
                        params[assoc] = model.objects.get(**query)
                    except model.DoesNotExist:
                        print(
                            f"⚠️  {model.__name__} not found for {assoc}='{val}', "
                            f"setting {assoc}=None"
                        )
                        params[assoc] = None

            # Resolve M2M references (optional)
            cluster_names = params.pop("clusters", None)

            matching_params, defaults = self.split_params(params, MATCH_PARAMS)
            quota, created = StorageQuota.objects.get_or_create(
                **matching_params, defaults=defaults
            )

            if created:
                print(
                    "🖥️  Created StorageQuota for allocation",
                    quota.allocation.slug,
                )

            # Set M2M values after creation
            if cluster_names is not None:
                quota.clusters.set(
                    StorageCluster.objects.filter(name__in=cluster_names)
                )
                quota.save()

            self.set_custom_fields_values(quota, custom_field_data)
            self.set_tags(quota, tags)


register_initializer("storage_quotas", StorageQuotaInitializer)
