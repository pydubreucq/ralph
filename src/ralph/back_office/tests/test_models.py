# -*- coding: utf-8 -*-
from dj.choices import Country
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory

from ralph.assets.country_utils import iso2_to_iso3, iso3_to_iso2
from ralph.assets.models import AssetLastHostname
from ralph.assets.tests.factories import (
    BackOfficeAssetModelFactory,
    CategoryFactory
)
from ralph.back_office.models import BackOfficeAsset, BackOfficeAssetStatus
from ralph.back_office.tests.factories import BackOfficeAssetFactory
from ralph.lib.transitions.tests import TransitionTestCase
from ralph.tests import RalphTestCase
from ralph.tests.factories import UserFactory


class HostnameGeneratorTests(RalphTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_pl = UserFactory(username='hostname_2')
        cls.user_pl.country = Country.pl
        cls.user_pl.save()

    def _check_hostname_not_generated(self, asset):
        asset._try_assign_hostname(True)
        changed_asset = BackOfficeAsset.objects.get(pk=asset.id)
        self.assertEqual(changed_asset.hostname, '')

    def _check_hostname_is_generated(self, asset):
        asset._try_assign_hostname(True)
        changed_asset = BackOfficeAsset.objects.get(pk=asset.id)
        self.assertTrue(len(changed_asset.hostname) > 0)

    def test_generate_first_hostname(self):
        """Scenario:
         - none of assets has hostname
         - after generate first of asset have XXXYY00001 in hostname field
        """
        category = CategoryFactory(code='PC')
        model = BackOfficeAssetModelFactory(category=category)
        asset = BackOfficeAssetFactory(
            model=model, owner=self.user_pl, hostname=''
        )
        template_vars = {
            'code': asset.model.category.code,
            'country_code': asset.country_code,
        }
        asset.generate_hostname(template_vars=template_vars)
        self.assertEqual(asset.hostname, 'POLPC00001')

    def test_generate_next_hostname(self):
        category = CategoryFactory(code='PC')
        model = BackOfficeAssetModelFactory(category=category)
        asset = BackOfficeAssetFactory(
            model=model, owner=self.user_pl, hostname=''
        )
        BackOfficeAssetFactory(owner=self.user_pl, hostname='POLSW00003')
        AssetLastHostname.increment_hostname(prefix='POLPC')
        AssetLastHostname.increment_hostname(prefix='POLPC')
        template_vars = {
            'code': asset.model.category.code,
            'country_code': asset.country_code,
        }
        asset.generate_hostname(template_vars=template_vars)
        self.assertEqual(asset.hostname, 'POLPC00003')

    def test_cant_generate_hostname_for_model_without_category(self):
        model = BackOfficeAssetModelFactory(category=None)
        asset = BackOfficeAssetFactory(
            model=model, owner=self.user_pl, hostname=''
        )
        self._check_hostname_not_generated(asset)

    def test_can_generate_hostname_for_model_with_hostname(self):
        category = CategoryFactory(code='PC')
        model = BackOfficeAssetModelFactory(category=category)
        asset = BackOfficeAssetFactory(model=model, owner=self.user_pl)
        self._check_hostname_is_generated(asset)

    def test_cant_generate_hostname_for_model_without_user(self):
        model = BackOfficeAssetModelFactory()
        asset = BackOfficeAssetFactory(model=model, owner=None, hostname='')
        self._check_hostname_not_generated(asset)

    def test_cant_generate_hostname_for_model_without_user_and_category(self):
        model = BackOfficeAssetModelFactory(category=None)
        asset = BackOfficeAssetFactory(model=model, owner=None, hostname='')
        self._check_hostname_not_generated(asset)

    def test_generate_next_hostname_out_of_range(self):
        category = CategoryFactory(code='PC')
        model = BackOfficeAssetModelFactory(category=category)
        asset = BackOfficeAssetFactory(
            model=model, owner=self.user_pl, hostname=''
        )
        AssetLastHostname.objects.create(
            prefix='POLPC', counter=99999
        )
        template_vars = {
            'code': asset.model.category.code,
            'country_code': asset.country_code,
        }
        asset.generate_hostname(template_vars=template_vars)
        self.assertEqual(asset.hostname, 'POLPC100000')

    def test_convert_iso2_to_iso3(self):
        self.assertEqual(iso2_to_iso3('PL'), 'POL')

    def test_convert_iso3_to_iso2(self):
        self.assertEqual(iso3_to_iso2('POL'), 'PL')

    def test_validate_imei(self):
        bo_asset_failed = BackOfficeAssetFactory(imei='failed')
        bo_asset = BackOfficeAssetFactory(imei='990000862471854')

        self.assertFalse(bo_asset_failed.validate_imei())
        self.assertTrue(bo_asset.validate_imei())


class TestBackOfficeAsset(RalphTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_pl = UserFactory(username='user_1', country=Country.pl)
        cls.user_us = UserFactory(username='user_2', country=Country.us)
        cls.category = CategoryFactory(code='PC')
        cls.category_without_code = CategoryFactory()
        cls.model = BackOfficeAssetModelFactory(category=cls.category)
        cls.model_without_code = BackOfficeAssetModelFactory(
            category=cls.category_without_code
        )

    def setUp(self):
        super().setUp()
        AssetLastHostname.objects.create(prefix='POLPC', counter=1000)
        self.bo_asset = BackOfficeAssetFactory(
            model=self.model,
            hostname='abc',
            owner=self.user_pl,
        )

    def test_try_assign_hostname(self):
        self.bo_asset._try_assign_hostname(commit=True)
        self.assertEqual(self.bo_asset.hostname, 'POLPC01001')

    def test_try_assign_hostname_no_change(self):
        self.bo_asset.hostname = 'POLPC01001'
        self.bo_asset.save()
        self.bo_asset._try_assign_hostname(commit=True)
        self.assertEqual(self.bo_asset.hostname, 'POLPC01001')

    def test_try_assign_hostname_no_hostname(self):
        self.bo_asset.hostname = ''
        self.bo_asset.save()
        self.bo_asset._try_assign_hostname(commit=True)
        self.assertEqual(self.bo_asset.hostname, 'POLPC01001')

    def test_try_assign_hostname_forced(self):
        self.bo_asset.hostname = 'POLPC001010'
        self.bo_asset.save()
        self.bo_asset._try_assign_hostname(commit=True, force=True)
        self.assertEqual(self.bo_asset.hostname, 'POLPC01001')

    def test_try_assign_hostname_with_country(self):
        self.bo_asset._try_assign_hostname(country='US', commit=True)
        self.assertEqual(self.bo_asset.hostname, 'USPC00001')

    def test_try_assign_hostname_category_without_code(self):
        bo_asset_2 = BackOfficeAssetFactory(
            model=self.model_without_code, hostname='abcd'
        )
        bo_asset_2._try_assign_hostname(commit=True)
        self.assertEqual(bo_asset_2.hostname, 'abcd')

    def test_try_assign_hostname_when_status_in_progress(self):
        self.bo_asset.status = BackOfficeAssetStatus.new
        self.bo_asset.save()

        self.bo_asset.status = BackOfficeAssetStatus.in_progress
        self.bo_asset.save()
        self.assertEqual(self.bo_asset.hostname, 'POLPC01001')


class TestBackOfficeAssetTransitions(TransitionTestCase, RalphTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_pl = UserFactory(username='user_1', country=Country.pl)
        cls.user_us = UserFactory(username='user_2', country=Country.us)
        cls.user_us_2 = UserFactory(username='user_3', country=Country.us)
        cls.category = CategoryFactory(code='PC')
        cls.model = BackOfficeAssetModelFactory(category=cls.category)

    def setUp(self):
        super().setUp()
        AssetLastHostname.objects.create(prefix='POLPC', counter=1000)
        self.bo_asset = BackOfficeAssetFactory(
            model=self.model,
            hostname='abc',
            owner=self.user_us,
        )
        self.bo_asset._try_assign_hostname(commit=True, force=True)
        self.request = RequestFactory().get('/assets/')
        self.request.user = self.user_pl
        # ugly hack from https://code.djangoproject.com/ticket/17971
        setattr(self.request, 'session', 'session')
        messages = FallbackStorage(self.request)
        setattr(self.request, '_messages', messages)

    def test_change_hostname(self):
        _, transition, _ = self._create_transition(
            model=self.bo_asset,
            name='test',
            source=[BackOfficeAssetStatus.new.id],
            target=BackOfficeAssetStatus.used.id,
            actions=['change_hostname']
        )
        self.bo_asset.run_status_transition(
            transition_obj_or_name=transition,
            data={'change_hostname__country': Country.pl},
            request=self.request
        )
        self.assertEqual(self.bo_asset.hostname, 'POLPC01001')

    def test_assign_owner(self):
        _, transition, _ = self._create_transition(
            model=self.bo_asset,
            name='test',
            source=[BackOfficeAssetStatus.new.id],
            target=BackOfficeAssetStatus.used.id,
            actions=['assign_owner']
        )
        self.bo_asset.run_status_transition(
            transition_obj_or_name=transition,
            data={'assign_owner__owner': self.user_pl.id},
            request=self.request
        )
        self.assertEqual(self.bo_asset.hostname, 'POLPC01001')

    def test_assign_owner_when_owner_country_not_changed(self):
        current_hostname = self.bo_asset.hostname
        _, transition, _ = self._create_transition(
            model=self.bo_asset,
            name='test',
            source=[BackOfficeAssetStatus.new.id],
            target=BackOfficeAssetStatus.used.id,
            actions=['assign_owner']
        )
        self.bo_asset.run_status_transition(
            transition_obj_or_name=transition,
            data={'assign_owner__owner': self.user_us_2.id},
            request=self.request
        )
        self.assertEqual(self.bo_asset.hostname, current_hostname)
