# SPDX-FileCopyrightText: (C) Tobias Genannt
# SPDX-FileCopyrightText: (C) ColdFront Authors
#
# SPDX-License-Identifier: Apache-2.0

# ruff: noqa: F401
# All initializers must be imported here, to be registered
from .allocations import AllocationInitializer
from .custom_fields import CustomFieldInitializer
from .groups import GroupInitializer
from .object_permissions import ObjectPermissionInitializer
from .projects import ProjectInitializer
from .resource_types import ResourceTypeInitializer
from .resources import ResourceInitializer
from .tags import TagInitializer
from .tenant_groups import TenantGroupInitializer
from .tenants import TenantInitializer
from .users import UserInitializer
