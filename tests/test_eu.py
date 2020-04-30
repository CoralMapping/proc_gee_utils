from unittest.mock import call, MagicMock, patch

import pytest

from eeutils import eu


class TestCreateAssetFolder:

    fake_gee_asset_path = 'projects/path/to/my/folder'

    def test_happy_path(self):
        mock_ee = MagicMock()
        info_return_values = [
            {'type': 'Folder', 'id': 'projects/path/to'},
            None
        ]
        mock_ee.data.getInfo.side_effect = info_return_values
        mock_ee.data.createAsset.return_value = {'type': 'Folder', 'id': self.fake_gee_asset_path}

        with patch.multiple('eeutils.eu',
                            ee=mock_ee):
            eu.create_asset_folder(self.fake_gee_asset_path)

        mock_ee.data.getInfo.assert_has_calls([
            call('projects/path/to'),
            call('projects/path/to/my')
        ])
        expected_asset = {'type': 'Folder'}
        mock_ee.data.createAsset.assert_called_once_with(expected_asset,
                                                         opt_path='projects/path/to/my')

    @pytest.mark.parametrize('asset_id', [
        '/foo/bar/baz/quux',
        'foo/bar/baz/quux/',
        '/foo/bar/baz/quux/'
    ])
    def test_strips_leading_and_trailing_slashes_from_asset_id(self, asset_id):
        mock_ee = MagicMock()
        mock_ee.data.getInfo.return_value = None
        with patch('eeutils.eu.ee', mock_ee):
            eu.create_asset_folder(asset_id)

        expected_asset = {'type': 'Folder'}
        mock_ee.data.createAsset.assert_called_once_with(expected_asset,
                                                         opt_path='foo/bar/baz')

    def test_raises_if_asset_id_is_too_short(self):
        with pytest.raises(ValueError):
            eu.create_asset_folder('too/short')
