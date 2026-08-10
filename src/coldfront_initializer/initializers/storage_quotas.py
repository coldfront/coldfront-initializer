# SPDX-FileCopyrightText: (C) University at Buffalo
#
# SPDX-License-Identifier: Apache-2.0

import logging

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
    LoadResult,
    register_initializer,
)

logger = logging.getLogger(__name__)


class StorageQuotaInitializer(BaseInitializer):
    MODEL = StorageQuota
    REQUIRED_ASSOCS = {
        "storage": (StorageResource, "name"),
        "owning_user": (User, "username"),
        "owning_group": (Group, "name"),
    }
    OPTIONAL_ASSOCS = {
        "snapshot_policy": (StorageSnapshotPolicy, "name"),
    }
    OPTIONAL_M2M_ASSOCS = {
        "clusters": (StorageCluster, "name"),
    }
    MATCH_PARAMS = ["allocation"]

    def _pre_process(self, params):
        allocation_slug = params.pop("allocation", None)
        if allocation_slug is None:
            logger.warning("StorageQuota requires 'allocation' field")
            params["_skip"] = True
            params["_skip_reason"] = "StorageQuota requires 'allocation' field"
            return
        try:
            params["allocation"] = Allocation.objects.get(slug=allocation_slug)
        except Allocation.DoesNotExist:
            logger.warning(
                "Allocation with slug '%s' not found, skipping StorageQuota",
                allocation_slug,
            )
            params["_skip"] = True
            params["_skip_reason"] = (
                f"Allocation with slug '{allocation_slug}' not found,"
                " skipping StorageQuota"
            )

    def load_data(self, records):
        if records is None:
            return None

        result = LoadResult(found=len(records))
        self._result = result

        for params in records:
            try:
                self._pre_process(params)
                if params.pop("_skip", False):
                    self._skip(params.pop("_skip_reason", None))
                    continue

                custom_field_data = self._pop_custom_fields(params)
                tags = self._pop_tags(params)

                self.resolve_required(params)
                self.resolve_optional(params)
                m2m_values = self.collect_m2m_values(params)

                matching_params, defaults = self.split_params(params, self.MATCH_PARAMS)
                obj, created = self._model.objects.get_or_create(
                    **matching_params, defaults=defaults
                )

                if created:
                    logger.debug(
                        "Created StorageQuota for allocation %s", obj.allocation.slug
                    )

                self.set_m2m_values(obj, m2m_values)
                self.set_custom_fields_values(obj, custom_field_data)
                self.set_tags(obj, tags)

                self._ok(obj, created)
            except Exception as e:
                self._fail(str(e))

        return result


register_initializer("storage_quotas", StorageQuotaInitializer)
