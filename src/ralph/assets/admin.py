# -*- coding: utf-8 -*-
from django.contrib.admin import TabularInline
from import_export.admin import ImportExportModelAdmin

from ralph.admin import RalphAdmin, register
from ralph.assets.models.assets import (
    AssetModel,
    Category,
    Environment,
    Manufacturer,
    Service,
    ServiceEnvironment
)
from ralph.assets.models.components import (
    ComponentModel,
    GenericComponent
)
from ralph.data_importer import resources
from ralph.lib.permissions.admin import PermissionAdminMixin


@register(ServiceEnvironment)
class ServiceEnvironmentAdmin(RalphAdmin):

    search_fields = ['service__name', 'environment__name']
    list_select_related = ['service', 'environment']


class ServiceEnvironmentInline(TabularInline):
    model = ServiceEnvironment


@register(Service)
class ServiceAdmin(RalphAdmin):
    exclude = ['environments']
    inlines = [ServiceEnvironmentInline]
    search_fields = ['name']


@register(Manufacturer)
class ManufacturerAdmin(ImportExportModelAdmin, RalphAdmin):

    search_fields = ['name']


@register(Environment)
class EnvironmentAdmin(RalphAdmin):

    search_fields = ['name']


@register(AssetModel)
class AssetModelAdmin(
    PermissionAdminMixin,
    ImportExportModelAdmin,
    RalphAdmin
):

    resource_class = resources.AssetModelResource
    list_select_related = ['manufacturer']
    raw_id_fields = ['manufacturer']
    search_fields = ['name', 'manufacturer__name']


@register(Category)
class CategoryAdmin(RalphAdmin):

    search_fields = ['name']


@register(ComponentModel)
class ComponentModelAdmin(RalphAdmin):
    pass


@register(GenericComponent)
class GenericComponentAdmin(RalphAdmin):
    pass
