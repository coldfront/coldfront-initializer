# SPDX-FileCopyrightText: (C) ColdFront Authors
#
# SPDX-License-Identifier: Apache-2.0

from coldfront.ras.models import Allocation
from coldfront.slurm.models import SlurmAccount, SlurmAssociation, SlurmCluster, SlurmQOS

from coldfront_initializer.initializers.base import (
    BaseInitializer,
    register_initializer,
)


MATCH_PARAMS = ["allocation"]

OPTIONAL_FK = {
    "default_qos": (SlurmQOS, "name"),
}


class SlurmAssociationInitializer(BaseInitializer):
    def load_data(self, records):
        if records is None:
            return

        for params in records:
            # Look up allocation by slug
            allocation_slug = params.pop("allocation", None)
            if allocation_slug is None:
                print("⚠️  SlurmAssociation requires 'allocation' field")
                continue

            try:
                params["allocation"] = Allocation.objects.get(slug=allocation_slug)
            except Allocation.DoesNotExist:
                print(
                    f"⚠️  Allocation with slug '{allocation_slug}' not found, "
                    "skipping SlurmAssociation"
                )
                continue

            # Resolve slurm_account and parent (may be cluster:account format)
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
                            print(
                                f"⚠️  SlurmAccount '{acct_name}' on cluster "
                                f"'{cluster_name}' not found, "
                                f"setting {assoc}=None"
                            )
                            params[assoc] = None
                    else:
                        # Legacy: lookup by name only
                        try:
                            params[assoc] = SlurmAccount.objects.get(name=val)
                        except SlurmAccount.DoesNotExist:
                            print(
                                f"⚠️  SlurmAccount with name='{val}' not found, "
                                f"setting {assoc}=None"
                            )
                            params[assoc] = None

            # Resolve remaining optional FK references (default_qos)
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
                            f"⚠️  {model.__name__} with {field}='{val}' not found, "
                            f"setting {assoc}=None"
                        )
                        params[assoc] = None

            matching_params, defaults = self.split_params(params, MATCH_PARAMS)

            # Use update_or_create because a post_save signal on Allocation
            # may have already created a bare SlurmAssociation (with all-None
            # default values). get_or_create would return that existing record
            # without applying our defaults.
            assoc_obj, created = SlurmAssociation.objects.update_or_create(
                **matching_params, defaults=defaults
            )

            if created:
                print(
                    "🖥️  Created SlurmAssociation for allocation",
                    assoc_obj.allocation.slug,
                )


register_initializer("slurm_associations", SlurmAssociationInitializer)
