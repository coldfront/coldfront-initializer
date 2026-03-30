# SPDX-FileCopyrightText: (C) Tobias Genannt
# SPDX-FileCopyrightText: (C) ColdFront Authors
#
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path
from typing import Tuple

from coldfront.core.models import CustomField, ObjectType, Tag
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from jinja2 import BaseLoader, Environment
from ruamel.yaml import YAML


class BaseInitializer:
    def __init__(self, data_file_path: str) -> None:
        self.data_file_path = data_file_path

    def load_data(self, records):
        # Must be implemented by specific subclass
        pass

    def is_template_file(self, f):
        pos = f.tell()
        line = f.readline().strip()
        f.seek(pos)
        return line == "# cf_template"

    def get_context(self):
        return {}

    def load_yaml(self, data_file_name):
        yf = Path(f"{self.data_file_path}/{data_file_name}")
        if not yf.is_file():
            return None

        with yf.open("r") as stream:
            yaml = YAML(typ="safe")

            if self.is_template_file(stream):
                template = Environment(loader=BaseLoader).from_string(stream.read())
                return yaml.load(template.render(self.get_context()))

            return yaml.load(stream)

    def pop_custom_fields(self, params):
        if "custom_field_data" in params:
            return params.pop("custom_field_data")
        elif "custom_fields" in params:
            print("⚠️ Please rename 'custom_fields' to 'custom_field_data'!")
            return params.pop("custom_fields")

        return None

    def set_custom_fields_values(self, entity, custom_field_data):
        if not custom_field_data:
            return

        missing_cfs = []
        save = False
        for key, value in custom_field_data.items():
            try:
                cf = CustomField.objects.get(name=key)
            except ObjectDoesNotExist:
                missing_cfs.append(key)
            else:
                ct = ObjectType.objects.get_for_model(entity)
                if not cf.object_types.filter(pk=ct.pk).exists():
                    print(
                        f"⚠️ Custom field {key} is not enabled for {entity}'s model!"
                        "Please check the 'on_objects' for that custom field in custom_fields.yml"
                    )
                entity.custom_field_data[key] = value
                save = True

        if missing_cfs:
            raise Exception(
                f"⚠️ Custom field(s) '{missing_cfs}' requested for {entity} but not found in ColdFront!"
                "Please check the custom_fields.yml"
            )

        if save:
            entity.save()

    def set_create_date(self, entity, create_date):
        if not create_date:
            return

        entity.created = create_date
        entity.save()

    def set_tags(self, entity, tags):
        if not tags:
            return

        if not hasattr(entity, "tags"):
            raise Exception(f"⚠️ Tags cannot be applied to {entity}'s model")

        object_type = ObjectType.objects.get_for_model(entity._meta.model)

        save = False
        for tag in Tag.objects.filter(name__in=tags):
            # Limit tags to those applicable to the object type
            if (
                not Tag.objects.filter(id=tag.pk)
                .filter(
                    Q(object_types__id=object_type.pk) | Q(object_types__isnull=True)
                )
                .exists()
            ):
                raise Exception(f"⚠️ Tag {tag} cannot be applied to {entity}'s model")

            entity.tags.add(tag)
            save = True

        if save:
            entity.save()

    def split_params(
        self, params: dict, unique_params: list = None
    ) -> Tuple[dict, dict]:
        """Split params dict into dict with matching params and a dict with default values"""

        if unique_params is None:
            unique_params = ["name", "slug"]

        matching_params = {}
        for unique_param in unique_params:
            param = params.pop(unique_param, "__not_set__")
            if param != "__not_set__":
                matching_params[unique_param] = param
        return matching_params, params


class InitializationError(Exception):
    pass


INITIALIZER_ORDER = (
    "users",
    "groups",
    "object_permissions",
    "custom_field_choicesets",
    "custom_fields",
    "tags",
    "tenant_groups",
    "tenants",
    "resource_types",
    "resources",
    "projects",
    "allocations",
)


INITIALIZER_REGISTRY = dict()


def register_initializer(name: str, initializer):
    INITIALIZER_REGISTRY[name] = initializer
