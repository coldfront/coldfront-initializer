# SPDX-FileCopyrightText: (C) University at Buffalo
#
# SPDX-License-Identifier: Apache-2.0

# ruff: noqa: F401
# All initializers must be imported here, to be registered
from .allocations import AllocationInitializer
from .allocation_change_requests import AllocationChangeRequestInitializer
from .comment_entries import CommentEntryInitializer
from .custom_field_choicesets import CustomFieldChoiceSetInitializer
from .custom_fields import CustomFieldInitializer
from .custom_links import CustomLinkInitializer
from .groups import GroupInitializer
from .object_permissions import ObjectPermissionInitializer
from .projects import ProjectInitializer
from .resource_types import ResourceTypeInitializer
from .resources import ResourceInitializer
from .roles import RoleInitializer
from .slurm_accounts import SlurmAccountInitializer
from .slurm_associations import SlurmAssociationInitializer
from .slurm_clusters import SlurmClusterInitializer
from .slurm_partitions import SlurmPartitionInitializer
from .slurm_qos import SlurmQOSInitializer
from .slurm_users import SlurmUserInitializer
from .storage_clusters import StorageClusterInitializer
from .storage_quotas import StorageQuotaInitializer
from .storage_resources import StorageResourceInitializer
from .storage_snapshot_policies import StorageSnapshotPolicyInitializer
from .tags import TagInitializer
from .tenant_groups import TenantGroupInitializer
from .tenants import TenantInitializer
from .users import UserInitializer
