# SPDX-FileCopyrightText: (C) University at Buffalo
#
# SPDX-License-Identifier: Apache-2.0

import logging
from dataclasses import dataclass, field as dc_field
from pathlib import Path
from typing import Tuple

from coldfront.core.models import CustomField, ObjectType, Tag
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from jinja2 import BaseLoader, Environment
from ruamel.yaml import YAML

logger = logging.getLogger(__name__)


@dataclass
class LoadResult:
    """Outcome of a load_data() run.

    found    -- records parsed from the YAML (or normalized, for dict format)
    loaded   -- records created or updated successfully
    created  -- subset of loaded: newly created
    updated  -- subset of loaded: already existed
    skipped  -- records intentionally skipped (warn + continue)
    errors   -- hard failures; one message per failed record
    warnings -- per-record messages for skips (e.g. "resource_object not found")
    """

    found: int = 0
    loaded: int = 0
    created: int = 0
    updated: int = 0
    skipped: int = 0
    errors: list = dc_field(default_factory=list)
    warnings: list = dc_field(default_factory=list)

    @property
    def ok(self):
        """No hard failures."""
        return not self.errors

    @property
    def partial(self):
        """Some records were skipped or failed to load."""
        return self.loaded < self.found or bool(self.warnings)


class BaseInitializer:
    # --- Class-level configuration (subclasses override) ---

    # The Django model class this initializer creates (required)
    MODEL = None

    # Association maps: {param_name: (ModelClass, lookup_field)}
    REQUIRED_ASSOCS = {}
    OPTIONAL_ASSOCS = {}
    OPTIONAL_M2M_ASSOCS = {}

    # Record format
    RECORDS_ARE_DICT = False  # If True, records keys are primary identifiers
    PRIMARY_KEY = "name"  # Field name for dict-keyed record keys

    # Unique params for split_params (None -> default ["name", "slug"])
    MATCH_PARAMS = None

    def __init__(self, data_file_path: str) -> None:
        self.data_file_path = data_file_path
        self._has_slug = self._check_field("slug")

    def _check_field(self, field_name):
        """Check if the model has a specific field."""
        m = self._model
        if m is None:
            return False
        try:
            m._meta.get_field(field_name)
            return True
        except Exception:
            return False

    # ---------------------------------------------------------------------------
    # Model capability detection
    # ---------------------------------------------------------------------------

    @property
    def _model(self):
        return self.MODEL

    def _supports_custom_fields(self):
        m = self._model
        return m is not None and hasattr(m, "custom_field_data")

    def _supports_tags(self):
        m = self._model
        return m is not None and hasattr(m, "tags")

    def _supports_created(self):
        if self._model is None:
            return False
        try:
            from django.db.models import DateTimeField

            f = self._model._meta.get_field("created")
            return isinstance(f, DateTimeField)
        except Exception:
            return False

    def _display_name(self, obj):
        if hasattr(obj, "name"):
            return obj.name
        if hasattr(obj, "slug"):
            return obj.slug
        if hasattr(obj, "username"):
            return obj.username
        return str(obj)

    # ---------------------------------------------------------------------------
    # Generic load_data pipeline
    # ---------------------------------------------------------------------------

    def load_data(self, records):
        if records is None:
            return None

        items = self._normalize_records(records)
        result = LoadResult(found=len(items))
        self._result = result

        for params in items:
            try:
                # Hook 1: pre-processing (color, schema, resource_object, etc.)
                self._pre_process(params)

                if params.pop("_skip", False):
                    self._skip(params.pop("_skip_reason", None))
                    continue

                custom_field_data = self._pop_custom_fields(params)
                tags = self._pop_tags(params)
                create_date = self._pop_created(params)

                # Pop slug for models that don't support it
                # (common in YAML but not a DB field)
                if not self._has_slug:
                    params.pop("slug", None)

                # Resolve FK / M2M associations
                self.resolve_required(params)
                self.resolve_optional(params)
                m2m_values = self.collect_m2m_values(params)

                # Split and create
                unique_params = self.MATCH_PARAMS or ["name", "slug"]
                # Ensure PRIMARY_KEY is included for dict-keyed records
                if self.RECORDS_ARE_DICT and self.PRIMARY_KEY not in unique_params:
                    unique_params = [self.PRIMARY_KEY] + unique_params
                matching_params, defaults = self.split_params(params, unique_params)
                obj, created = self._model.objects.get_or_create(
                    **matching_params, defaults=defaults
                )

                if created:
                    if create_date and self._supports_created():
                        self.set_create_date(obj, create_date)
                    logger.debug(
                        "Created %s: %s", self._model.__name__, self._display_name(obj)
                    )

                # Set M2M after creation
                self.set_m2m_values(obj, m2m_values)

                # Hook 2: post-processing (project users, permissions, choices, etc.)
                self._post_process(obj, created, params)

                # Apply custom fields and tags
                self.set_custom_fields_values(obj, custom_field_data)
                self.set_tags(obj, tags)

                self._ok(obj, created)
            except Exception as e:
                self._fail(str(e))

        return result

    def _ok(self, obj, created):
        """Record one successfully loaded record."""
        result = self._result
        result.loaded += 1
        if created:
            result.created += 1
        else:
            result.updated += 1

    def _skip(self, reason=None):
        """Record one intentionally skipped record."""
        result = self._result
        result.skipped += 1
        if reason:
            result.warnings.append(reason)

    def _fail(self, msg):
        """Record one hard failure."""
        self._result.errors.append(msg)

    def _normalize_records(self, records):
        """Convert dict-keyed records into list-of-params format."""
        if isinstance(records, dict):
            items = []
            for key, value in records.items():
                entry = {self.PRIMARY_KEY: key}
                if isinstance(value, dict):
                    entry.update(value)
                items.append(entry)
            return items
        return records

    # ---------------------------------------------------------------------------
    # Hook methods (override in subclasses)
    # ---------------------------------------------------------------------------

    def _pre_process(self, params):
        """Called before any resolution. Override for color, schema, etc."""
        pass

    def _post_process(self, obj, created, params):
        """Called after creation, before custom_fields/tags.
        Override for project users, permissions, choices, etc."""
        pass

    # ---------------------------------------------------------------------------
    # FK / M2M resolution helpers
    # ---------------------------------------------------------------------------

    def _resolve_model_cls(self, model_cls):
        """Convert string model paths to actual model classes."""
        if isinstance(model_cls, str):
            from django.apps import apps

            return apps.get_model(model_cls)
        return model_cls

    def resolve_required(self, params):
        """Resolve required FK associations — raises if missing."""
        for assoc, (model_cls, field) in self.REQUIRED_ASSOCS.items():
            value = params.pop(assoc)
            model_cls = self._resolve_model_cls(model_cls)
            params[assoc] = model_cls.objects.get(**{field: value})

    def resolve_optional(self, params):
        """Resolve optional FK associations — null/DoesNotExist safe."""
        for assoc, (model_cls, field) in self.OPTIONAL_ASSOCS.items():
            if assoc not in params:
                continue
            val = params[assoc]
            if val is None or val == "null":
                params[assoc] = None
                continue
            params.pop(assoc)  # pop now that we know it's a real value
            model_cls = self._resolve_model_cls(model_cls)
            try:
                params[assoc] = model_cls.objects.get(**{field: val})
            except model_cls.DoesNotExist:
                logger.warning(
                    "%s with %s='%s' not found, setting %s=None",
                    model_cls.__name__,
                    field,
                    val,
                    assoc,
                )
                params[assoc] = None

    def collect_m2m_values(self, params):
        """Pop M2M values from params before split_params. Returns dict."""
        m2m_values = {}
        for assoc, (model_cls, field) in self.OPTIONAL_M2M_ASSOCS.items():
            if assoc in params:
                m2m_values[assoc] = params.pop(assoc)
        return m2m_values

    def set_m2m_values(self, obj, m2m_values):
        """Apply collected M2M values after creation."""
        if not m2m_values:
            return
        for assoc, (model_cls, field) in self.OPTIONAL_M2M_ASSOCS.items():
            if assoc in m2m_values:
                model_cls = self._resolve_model_cls(model_cls)
                getattr(obj, assoc).set(
                    model_cls.objects.filter(**{field + "__in": m2m_values[assoc]})
                )
        obj.save()

    # ---------------------------------------------------------------------------
    # Pop helpers (respect model capabilities)
    # ---------------------------------------------------------------------------

    def _pop_custom_fields(self, params):
        if not self._supports_custom_fields():
            return None
        # Delegate to the existing public method
        return self.pop_custom_fields(params)

    def _pop_tags(self, params):
        if not self._supports_tags():
            return None
        return params.pop("tags", None)

    def _pop_created(self, params):
        if not self._supports_created():
            return None
        return params.pop("created", None)

    # ---------------------------------------------------------------------------
    # Existing public methods (unchanged)
    # ---------------------------------------------------------------------------

    def get_context(self):
        return {}

    def load_yaml(self, data_file_name):
        """Load YAML from a file in ``self.data_file_path``.

        Returns None when the file does not exist.
        """
        yf = Path(f"{self.data_file_path}/{data_file_name}")
        if not yf.is_file():
            return None

        with yf.open("r") as stream:
            return self.load_yaml_string(stream.read())

    def load_yaml_string(self, data_string):
        """Load YAML from a string directly (no file needed).

        Supports the ``# cf_template`` convention: if the first line is
        ``# cf_template`` the string is rendered as a Jinja2 template.
        """
        yaml = YAML(typ="safe")

        lines = data_string.splitlines()
        if lines and lines[0].strip() == "# cf_template":
            template = Environment(loader=BaseLoader).from_string(data_string)
            return yaml.load(template.render(self.get_context()))

        return yaml.load(data_string)

    def pop_custom_fields(self, params):
        if "custom_field_data" in params:
            return params.pop("custom_field_data")
        elif "custom_fields" in params:
            logger.warning("Please rename 'custom_fields' to 'custom_field_data'!")
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
                    logger.warning(
                        "Custom field %s is not enabled for %s's model!"
                        " Please check the 'on_objects' for that custom field"
                        " in custom_fields.yml",
                        key,
                        entity,
                    )
                entity.custom_field_data[key] = value
                save = True

        if missing_cfs:
            raise Exception(
                f"Custom field(s) '{missing_cfs}' requested for {entity}"
                " but not found in ColdFront!"
                " Please check the custom_fields.yml"
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
            raise Exception(f"Tags cannot be applied to {entity}'s model")

        object_type = ObjectType.objects.get_for_model(entity._meta.model)

        save = False
        for tag in Tag.objects.filter(name__in=tags):
            if (
                not Tag.objects.filter(id=tag.pk)
                .filter(
                    Q(object_types__id=object_type.pk) | Q(object_types__isnull=True)
                )
                .exists()
            ):
                raise Exception(f"Tag {tag} cannot be applied to {entity}'s model")
            entity.tags.add(tag)
            save = True

        if save:
            entity.save()

    def split_params(
        self, params: dict, unique_params: list = None
    ) -> Tuple[dict, dict]:
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
    "object_permissions",
    "roles",
    "users",
    "groups",
    "custom_field_choicesets",
    "custom_fields",
    "tags",
    "tenant_groups",
    "tenants",
    "resource_types",
    "resources",
    "slurm_qos",
    "slurm_clusters",
    "slurm_partitions",
    "storage_clusters",
    "storage_resources",
    "storage_snapshot_policies",
    "projects",
    "publications",
    "funding",
    "allocations",
    "storage_quotas",
    "slurm_accounts",
    "slurm_associations",
    "slurm_users",
    "custom_links",
    "allocation_change_requests",
    "comment_entries",
)


INITIALIZER_REGISTRY = dict()


def register_initializer(name: str, initializer):
    INITIALIZER_REGISTRY[name] = initializer
