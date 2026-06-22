# SPDX-FileCopyrightText: (C) ColdFront Authors
#
# SPDX-License-Identifier: Apache-2.0

from coldfront.ras.models import (
    Allocation,
    Project,
)
from coldfront.tenancy.models import Tenant
from coldfront.users.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import (
    MultipleObjectsReturned,
    ObjectDoesNotExist,
)

from coldfront_initializer.initializers.base import (
    BaseInitializer,
    register_initializer,
)

MATCH_PARAMS = ["owner", "project", "resource_object_type", "resource_object_id"]
REQUIRED_ASSOCS = {
    "owner": (User, "username"),
    "project": (Project, "name"),
}
OPTIONAL_ASSOCS = {
    "tenant": (Tenant, "name"),
}


class AllocationInitializer(BaseInitializer):
    def parse_resource_object(self, value):
        if not value:
            raise ValueError("resource_object is required")

        # Parse the format <app_label>.<model>:<identifier_value>
        # Support both <app_label>.<model>:<value> and <app_label>.<model>:<field>=<value>
        ct_part, _, identifier_part = value.partition(":")
        if not identifier_part:
            raise ValueError(
                'resource_object must be in the format "<app_label>.<model>:<identifier>"'
            )
        app_label, model = ct_part.split(".")

        # Resolve the ContentType and model class
        try:
            ct = ContentType.objects.get_by_natural_key(
                app_label=app_label, model=model
            )
        except ObjectDoesNotExist:
            raise ValueError(
                'Invalid content type: "{app_label}.{model}" for resource_object'.format(
                    app_label=app_label, model=model
                )
            )

        model_class = ct.model_class()
        if model_class is None:
            raise ValueError("resource_object model class not found for content type")

        # Check if the identifier uses a specific field: <field>=<value>
        if "=" in identifier_part:
            field_name, _, field_value = identifier_part.partition("=")
            field_name = field_name.strip()
            field_value = field_value.strip()
        else:
            field_name = "name"
            field_value = identifier_part.strip()

        # Look up the object
        try:
            filter_kwargs = {field_name: field_value}
            obj = model_class.objects.get(**filter_kwargs)
        except ObjectDoesNotExist:
            raise ValueError("resource_object not found: {value}".format(value=value))
        except MultipleObjectsReturned:
            raise ValueError(
                '"resource_object {value}" matched multiple objects'.format(value=value)
            )

        return obj

    def load_data(self, records):
        if records is None:
            return

        for params in records:
            custom_field_data = self.pop_custom_fields(params)
            tags = params.pop("tags", None)
            create_date = params.pop("created", None)

            try:
                resource_obj = self.parse_resource_object(
                    params.pop("resource_object", None)
                )
                params["resource_object_type"] = ContentType.objects.get_for_model(
                    resource_obj
                )
                params["resource_object_id"] = resource_obj.pk
            except ValueError as e:
                print(f"⚠️ Unable to create Allocation {e}")
                continue

            for assoc, details in REQUIRED_ASSOCS.items():
                model, field = details
                query = {field: params.pop(assoc)}

                params[assoc] = model.objects.get(**query)

            for assoc, details in OPTIONAL_ASSOCS.items():
                if assoc in params:
                    model, field = details
                    query = {field: params.pop(assoc)}

                    params[assoc] = model.objects.get(**query)

            matching_params, defaults = self.split_params(params, MATCH_PARAMS)
            allocation, created = Allocation.objects.get_or_create(
                **matching_params, defaults=defaults
            )

            if created:
                self.set_create_date(allocation, create_date)
                print("🖥️  Created allocation", allocation.slug)

            self.set_custom_fields_values(allocation, custom_field_data)
            self.set_tags(allocation, tags)


register_initializer("allocations", AllocationInitializer)
