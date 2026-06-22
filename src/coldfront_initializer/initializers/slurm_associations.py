# SPDX-FileCopyrightText: (C) ColdFront Authors
#
# SPDX-License-Identifier: Apache-2.0

from coldfront.ras.models import Allocation
from coldfront.slurm.models import SlurmAccount, SlurmAssociation, SlurmQOS

from coldfront_initializer.initializers.base import (
    BaseInitializer,
    register_initializer,
)


MATCH_PARAMS = ["allocation"]

OPTIONAL_FK = {
    "slurm_account": (SlurmAccount, "name"),
    "parent": (SlurmAccount, "name"),
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
