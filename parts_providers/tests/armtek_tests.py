import json
import os
from unittest.mock import MagicMock, patch

from django.test import TestCase

from parts_providers import ProviderApiError
from parts_providers.armtek import (
    ASSORTMENT_SEARCH_URL,
    SEARCH_URL,
    USER_INFO_URL,
    USER_VKORG_LIST_URL,
    ArmTekProvider,
)
from parts_providers.parts_provider import AssortmentSearchResultItem, SearchResultItem

# ---------------------------------------------------------------------------
# Fixture data – realistic ArmTek JSON payloads
# ---------------------------------------------------------------------------

VKORG_RESPONSE = {
    'STATUS': 0,
    'MESSAGES': [],
    'RESP': [{'VKORG': '0123', 'PROGRAM_NAME': 'Retail'}],
}

USER_INFO_RESPONSE = {
    'STATUS': 0,
    'MESSAGES': [],
    'RESP': {
        'STRUCTURE': {
            'KUNAG': 'AGT001',
            'VKORG': '0123',
            'SNAME': 'Test Company',
            'FNAME': 'Test Company Full',
            'ADRESS': 'Test Address',
            'PHONE': '71234567890',
            'RG_TAB': [
                {
                    'KUNNR': 'KUN001',
                    'DEFAULT': 1,
                    'SNAME': 'Buyer',
                    'FNAME': 'Buyer Full Name',
                    'ADRESS': 'Buyer Address',
                    'PHONE': '79876543210',
                    'ZA_TAB': [],
                    'CONTACT_TAB': [],
                }
            ],
        }
    },
}

SEARCH_RESULTS_RESPONSE = {
    'STATUS': 0,
    'MESSAGES': [],
    'RESP': [
        {
            'PIN': 'HU615/3x',
            'BRAND': 'MANN',
            'NAME': 'Oil Filter',
            'ARTID': 'HU6153X',
            'KEYZAK': 'MSK01',
            'RVALUE': '10',
            'PRICE': '850.00',
            'DLVDT': '2026-06-08',
        }
    ],
}

SEARCH_NO_RESULTS_RESPONSE = {
    'STATUS': 1,
    'MESSAGES': [],
    'RESP': {'MSG': 'Ничего не найдено'},
}

ASSORTMENT_RESULTS_RESPONSE = {
    'STATUS': 0,
    'MESSAGES': [],
    'RESP': [
        {'PIN': 'HU615/3x', 'BRAND': 'MANN', 'NAME': 'Oil Filter'},
        {'PIN': 'HU615/3x', 'BRAND': 'BOSCH', 'NAME': 'Масляный фильтр'},
    ],
}

ASSORTMENT_NO_RESULTS_RESPONSE = {
    'STATUS': 1,
    'MESSAGES': [],
    'RESP': {'MSG': 'Ничего не найдено'},
}


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------

@patch.dict(os.environ, {'ARMTEK_LOGIN': 'test_login', 'ARMTEK_PASSWORD': 'test_password'})
class ArmTekProviderTest(TestCase):

    def setUp(self):
        self.provider = ArmTekProvider()
        self.provider.session = MagicMock()

    def _mock_response(self, status_code=200, json_data=None):
        mock = MagicMock()
        mock.status_code = status_code
        mock.json.return_value = json_data if json_data is not None else {}
        mock.text = json.dumps(json_data) if json_data is not None else ''
        return mock

    def _prime_vkorg_cache(self):
        """Set vkorg directly to skip the HTTP round-trip in tests that don't test vkorg."""
        self.provider._vkorg = '0123'

    def _prime_auth_cache(self):
        """Warm both vkorg and user_info caches so search/assortment tests don't need to mock those."""
        self._prime_vkorg_cache()
        self.provider.session.post.return_value = self._mock_response(json_data=USER_INFO_RESPONSE)
        _ = self.provider.buyer
        self.provider.session.post.reset_mock()

    # -----------------------------------------------------------------------
    # vkorg property
    # -----------------------------------------------------------------------

    def test_vkorg_returns_vkorg_string_on_success(self):
        self.provider.session.get.return_value = self._mock_response(json_data=VKORG_RESPONSE)

        result = self.provider.vkorg

        self.assertEqual(result, '0123')

    def test_vkorg_requests_correct_url(self):
        self.provider.session.get.return_value = self._mock_response(json_data=VKORG_RESPONSE)

        self.provider.vkorg

        self.provider.session.get.assert_called_once_with(USER_VKORG_LIST_URL)

    def test_vkorg_is_cached_after_first_call(self):
        self.provider.session.get.return_value = self._mock_response(json_data=VKORG_RESPONSE)

        _ = self.provider.vkorg
        _ = self.provider.vkorg

        self.provider.session.get.assert_called_once()

    def test_vkorg_raises_on_http_error(self):
        self.provider.session.get.return_value = self._mock_response(status_code=503)

        with self.assertRaises(ProviderApiError):
            _ = self.provider.vkorg

    def test_vkorg_raises_on_invalid_response_structure(self):
        self.provider.session.get.return_value = self._mock_response(
            json_data={'STATUS': 0, 'MESSAGES': [], 'RESP': [{'MISSING_VKORG': True}]}
        )

        with self.assertRaises(ProviderApiError):
            _ = self.provider.vkorg

    # -----------------------------------------------------------------------
    # user_info property
    # -----------------------------------------------------------------------

    def test_user_info_returns_structure_on_success(self):
        self._prime_vkorg_cache()
        self.provider.session.post.return_value = self._mock_response(json_data=USER_INFO_RESPONSE)

        result = self.provider.user_info

        self.assertEqual(result.KUNAG, 'AGT001')
        self.assertEqual(result.VKORG, '0123')
        self.assertEqual(result.RG_TAB[0].KUNNR, 'KUN001')

    def test_user_info_posts_to_correct_url_with_vkorg(self):
        self._prime_vkorg_cache()
        self.provider.session.post.return_value = self._mock_response(json_data=USER_INFO_RESPONSE)

        self.provider.user_info

        self.provider.session.post.assert_called_once_with(USER_INFO_URL, data={'VKORG': '0123'})

    def test_user_info_is_cached_after_first_call(self):
        self._prime_vkorg_cache()
        self.provider.session.post.return_value = self._mock_response(json_data=USER_INFO_RESPONSE)

        _ = self.provider.user_info
        _ = self.provider.user_info

        self.provider.session.post.assert_called_once()

    def test_user_info_raises_on_http_error(self):
        self._prime_vkorg_cache()
        self.provider.session.post.return_value = self._mock_response(status_code=401)

        with self.assertRaises(ProviderApiError):
            _ = self.provider.user_info

    def test_user_info_raises_on_invalid_response_structure(self):
        self._prime_vkorg_cache()
        self.provider.session.post.return_value = self._mock_response(
            json_data={'STATUS': 0, 'MESSAGES': [], 'RESP': {'STRUCTURE': {}}}
        )

        with self.assertRaises(ProviderApiError):
            _ = self.provider.user_info

    # -----------------------------------------------------------------------
    # buyer property
    # -----------------------------------------------------------------------

    def test_buyer_returns_kunnr_of_first_rg_tab_entry(self):
        self._prime_vkorg_cache()
        self.provider.session.post.return_value = self._mock_response(json_data=USER_INFO_RESPONSE)

        self.assertEqual(self.provider.buyer, 'KUN001')

    # -----------------------------------------------------------------------
    # assortment_search
    # -----------------------------------------------------------------------

    def test_assortment_search_returns_result_items_on_success(self):
        self._prime_vkorg_cache()
        self.provider.session.post.return_value = self._mock_response(json_data=ASSORTMENT_RESULTS_RESPONSE)

        results = self.provider.assortment_search('HU615/3x')

        self.assertEqual(len(results), 2)
        self.assertIsInstance(results[0], AssortmentSearchResultItem)
        self.assertEqual(results[0].article_number, 'HU615/3x')
        self.assertEqual(results[0].manufacture, 'MANN')
        self.assertEqual(results[0].name, 'Oil Filter')
        self.assertEqual(results[1].manufacture, 'BOSCH')
        self.assertEqual(results[1].name, 'Масляный фильтр')

    def test_assortment_search_posts_correct_payload(self):
        self._prime_vkorg_cache()
        self.provider.session.post.return_value = self._mock_response(json_data=ASSORTMENT_RESULTS_RESPONSE)

        self.provider.assortment_search('HU615/3x')

        self.provider.session.post.assert_called_once_with(
            ASSORTMENT_SEARCH_URL,
            data={'VKORG': '0123', 'PIN': 'HU615/3x'},
        )

    def test_assortment_search_returns_empty_list_when_resp_is_message(self):
        self._prime_vkorg_cache()
        self.provider.session.post.return_value = self._mock_response(json_data=ASSORTMENT_NO_RESULTS_RESPONSE)

        results = self.provider.assortment_search('UNKNOWN_PIN')

        self.assertEqual(results, [])

    def test_assortment_search_returns_empty_list_when_resp_is_empty_array(self):
        self._prime_vkorg_cache()
        self.provider.session.post.return_value = self._mock_response(
            json_data={'STATUS': 0, 'MESSAGES': [], 'RESP': []}
        )

        results = self.provider.assortment_search('HU615/3x')

        self.assertEqual(results, [])

    def test_assortment_search_raises_on_http_error(self):
        self._prime_vkorg_cache()
        self.provider.session.post.return_value = self._mock_response(status_code=500)

        with self.assertRaises(ProviderApiError):
            self.provider.assortment_search('HU615/3x')

    def test_assortment_search_raises_on_json_decode_error(self):
        self._prime_vkorg_cache()
        mock_resp = self._mock_response(status_code=200)
        mock_resp.json.side_effect = json.JSONDecodeError('Expecting value', '', 0)
        self.provider.session.post.return_value = mock_resp

        with self.assertRaises(ProviderApiError):
            self.provider.assortment_search('HU615/3x')

    def test_assortment_search_raises_on_invalid_response_structure(self):
        self._prime_vkorg_cache()
        self.provider.session.post.return_value = self._mock_response(
            json_data={'INVALID_KEY': 'bad_structure'}
        )

        with self.assertRaises(ProviderApiError):
            self.provider.assortment_search('HU615/3x')

    # -----------------------------------------------------------------------
    # search
    # -----------------------------------------------------------------------

    def test_search_returns_result_items_on_success(self):
        self._prime_auth_cache()
        self.provider.session.post.return_value = self._mock_response(json_data=SEARCH_RESULTS_RESPONSE)

        results = self.provider.search('HU615/3x')

        self.assertEqual(len(results), 1)
        self.assertIsInstance(results[0], SearchResultItem)
        self.assertEqual(results[0].article_number, 'HU6153X')
        self.assertEqual(results[0].manufacture, 'MANN')
        self.assertEqual(results[0].name, 'Oil Filter')
        self.assertEqual(results[0].price, '850.00')
        self.assertEqual(results[0].count, '10')
        self.assertEqual(results[0].delivery_time, '2026-06-08')

    def test_search_posts_correct_payload(self):
        self._prime_auth_cache()
        self.provider.session.post.return_value = self._mock_response(json_data=SEARCH_RESULTS_RESPONSE)

        self.provider.search('HU615/3x')

        self.provider.session.post.assert_called_once_with(
            SEARCH_URL,
            data={'VKORG': '0123', 'KUNNR_RG': 'KUN001', 'PIN': 'HU615/3x'},
        )

    def test_search_returns_empty_list_when_resp_is_message(self):
        self._prime_auth_cache()
        self.provider.session.post.return_value = self._mock_response(json_data=SEARCH_NO_RESULTS_RESPONSE)

        results = self.provider.search('UNKNOWN_PIN')

        self.assertEqual(results, [])

    def test_search_raises_on_http_error(self):
        self._prime_auth_cache()
        self.provider.session.post.return_value = self._mock_response(status_code=500)

        with self.assertRaises(ProviderApiError):
            self.provider.search('HU615/3x')

    def test_search_raises_on_json_decode_error(self):
        self._prime_auth_cache()
        mock_resp = self._mock_response(status_code=200)
        mock_resp.json.side_effect = json.JSONDecodeError('Expecting value', '', 0)
        self.provider.session.post.return_value = mock_resp

        with self.assertRaises(ProviderApiError):
            self.provider.search('HU615/3x')

    def test_search_raises_on_unexpected_exception(self):
        self._prime_auth_cache()
        # Cause a generic exception during pydantic validation by returning a totally unexpected structure.
        self.provider.session.post.return_value = self._mock_response(
            json_data={'STATUS': 0, 'MESSAGES': [], 'RESP': 12345}
        )

        with self.assertRaises(ProviderApiError):
            self.provider.search('HU615/3x')

    @patch('parts_providers.armtek.cache')
    def test_search_maps_warehouse_code_to_name_from_cache(self, mock_cache):
        self._prime_auth_cache()
        mock_cache.get.return_value = {'SKLNAME': 'Склад Москва'}
        self.provider.session.post.return_value = self._mock_response(json_data=SEARCH_RESULTS_RESPONSE)

        results = self.provider.search('HU615/3x')

        self.assertEqual(results[0].warehouse_location, 'Склад Москва')
        mock_cache.get.assert_called_once_with('MSK01', {'SKLNAME': 'Неизвестный склад'})

    @patch('parts_providers.armtek.cache')
    def test_search_uses_fallback_warehouse_name_when_not_in_cache(self, mock_cache):
        self._prime_auth_cache()
        mock_cache.get.return_value = {'SKLNAME': 'Неизвестный склад'}
        self.provider.session.post.return_value = self._mock_response(json_data=SEARCH_RESULTS_RESPONSE)

        results = self.provider.search('HU615/3x')

        self.assertEqual(results[0].warehouse_location, 'Неизвестный склад')
