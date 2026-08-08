# SPDX-FileCopyrightText: (C) University at Buffalo
#
# SPDX-License-Identifier: Apache-2.0

import logging

from coldfront.ras.models import Allocation
from coldfront.slurm.models import (
    SlurmAccount,
    SlurmAssociation,
    SlurmCluster,
    SlurmQOS,
)

from coldfront_initializer.initializers.base import (
    BaseInitializer,
    register_initializer,
)

logger = logging.getLogger(__name__)


class SlurmAssociationInitializer(BaseInitializer):
    MODEL = SlurmAssociation
    OPTIONAL_ASSOCS = {
        "default_qos": (SlurmQOS, "name"),
    }
    MATCH_PARAMS = ["allocation"]

    def load_data(self, records):
        if records is None:
            return

        for params in records:
            # Look up allocation by slug (required, skip on failure)
            allocation_slug = params.pop("allocation", None)
            if allocation_slug is None:
                logger.warning("SlurmAssociation requires 'allocation' field")
                continue
            try:
                params["allocation"] = Allocation.objects.get(slug=allocation_slug)
            except Allocation.DoesNotExist:
                logger.warning(
                    "Allocation with slug '%s' not found, skipping SlurmAssociation",
                    allocation_slug,
                )
                continue

            # Resolve slurm_account and parent (cluster:account format)
            for assoc in ("slurm_account", "parent"):
                if assoc in params:
                    val = params[assoc]
                    if val is None or val == "null":
                        params[assoc] = None
                        continue
                    if ":" in val:
                        cluster_name, acct_name = val.split(":", 1)
                        try:
                            cluster = SlurmCluster.objects.get(name=cluster_name)
                            params[assoc] = SlurmAccount.objects.get(
                                name=acct_name, cluster=cluster
                            )
                        except (SlurmCluster.DoesNotExist, SlurmAccount.DoesNotExist):
                            logger.warning(
                                "SlurmAccount '%s' on cluster '%s' not found,"
                                " setting %s=None",
                                acct_name,
                                cluster_name,
                                assoc,
                            )
                            params[assoc] = None
                    else:
                        try:
                            params[assoc] = SlurmAccount.objects.get(name=val)
                        except SlurmAccount.DoesNotExist:
                            logger.warning(
                                "SlurmAccount with name='%s' not found,"
                                " setting %s=None",
                                val,
                                assoc,
                            )
                            params[assoc] = None

            # Resolve remaining optional FK references (default_qos)
            self.resolve_optional(params)

            matching_params, defaults = self.split_params(params, self.MATCH_PARAMS)
            obj, created = self.MODEL.objects.get_or_create(
                **matching_params, defaults=defaults
            )

            if created:
                logger.debug(
                    "Created SlurmAssociation for allocation %s",
                    obj.allocation.slug,
                )


register_initializer("slurm_associations", SlurmAssociationInitializer)
