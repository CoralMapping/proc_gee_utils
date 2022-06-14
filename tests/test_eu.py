"""
 Copyright Arizona State University 2021-2022

 Licensed under the Apache License, Version 2.0 (the "License").
 You may not use this file except in compliance with the License.
 A copy of the License is located at

     http://www.apache.org/licenses/LICENSE-2.0

 or in the "license" file accompanying this file. This file is distributed
 on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
 express or implied. See the License for the specific language governing
 permissions and limitations under the License.
"""


import json
from unittest.mock import call, MagicMock, patch

import pytest
import ee

from geeutils import eu


class TestAuthenticate:
    def test_works_with_service_account_key(self):
        mock_os = MagicMock()
        fake_service_account_key = json.dumps({"client_email": "foo@bar.com"})
        mock_os.environ = {"SERVICE_ACCOUNT_KEY": fake_service_account_key}
        mock_ee = MagicMock()
        fake_credentials = MagicMock()
        mock_ee.ServiceAccountCredentials.return_value = fake_credentials
        with patch.multiple("geeutils.eu", ee=mock_ee, os=mock_os):
            eu.authenticate()

        mock_ee.ServiceAccountCredentials.assert_called_once_with(
            "foo@bar.com", key_data=fake_service_account_key
        )
        mock_ee.Initialize.assert_called_once_with(fake_credentials)

    def test_clear_message_if_key_is_invalid_json(self):
        mock_os = MagicMock()
        fake_service_account_key = ""
        mock_os.environ = {"SERVICE_ACCOUNT_KEY": fake_service_account_key}
        with pytest.raises(ValueError) as e:
            with patch("geeutils.eu.os", mock_os):
                eu.authenticate()

        expected_message = "SERVICE_ACCOUNT_KEY is empty or contains invalid JSON"
        assert expected_message in e.exconly()

    def test_works_with_supplied_personal_credentials_file(self):
        mock_os = MagicMock()
        mock_os.environ = {}
        mock_os.path.exists.return_value = True
        mock_ee = MagicMock()
        with patch.multiple("geeutils.eu", ee=mock_ee, os=mock_os):
            eu.authenticate()

        mock_os.path.exists.assert_called_once_with(
            "/root/.config/earthengine/credentials"
        )
        mock_ee.Authenticate.assert_not_called()
        mock_ee.Initialize.assert_called_once_with()

    def test_uses_oauth_flow_if_credentials_not_found(self):
        mock_os = MagicMock()
        mock_os.environ = {}
        mock_os.path.exists.return_value = False
        mock_ee = MagicMock()
        with patch.multiple("geeutils.eu", ee=mock_ee, os=mock_os):
            eu.authenticate()

        mock_os.path.exists.assert_called_once_with(
            "/root/.config/earthengine/credentials"
        )
        mock_ee.Authenticate.assert_called_once_with()
        mock_ee.Initialize.assert_called_once_with()

    def test_auth_fails_if_no_service_key_no_credentials(self):
        mock_os = MagicMock()
        mock_os.environ = {}
        mock_os.path.exists.return_value = False
        mock_ee = MagicMock()
        mock_ee.ee_exception.EEException = ee.ee_exception.EEException
        with pytest.raises(ee.ee_exception.EEException):
            with patch.multiple("geeutils.eu", ee=mock_ee, os=mock_os):
                eu.authenticate(allow_interactive=False)

        mock_ee.Authenticate.assert_not_called()


class TestCreateAssetFolder:

    fake_gee_asset_path = "projects/path/to/my/folder"

    def test_happy_path(self):
        mock_ee = MagicMock()
        info_return_values = [{"type": "Folder", "id": "projects/path/to"}, None]
        mock_ee.data.getInfo.side_effect = info_return_values
        mock_ee.data.createAsset.return_value = {
            "type": "Folder",
            "id": self.fake_gee_asset_path,
        }

        with patch.multiple("geeutils.eu", ee=mock_ee):
            eu.create_asset_folder(self.fake_gee_asset_path)

        mock_ee.data.getInfo.assert_has_calls(
            [call("projects/path/to"), call("projects/path/to/my")]
        )
        expected_asset = {"type": "Folder"}
        mock_ee.data.createAsset.assert_called_once_with(
            expected_asset, opt_path="projects/path/to/my"
        )

    @pytest.mark.parametrize(
        "asset_id", ["/foo/bar/baz/quux", "foo/bar/baz/quux/", "/foo/bar/baz/quux/"]
    )
    def test_strips_leading_and_trailing_slashes_from_asset_id(self, asset_id):
        mock_ee = MagicMock()
        mock_ee.data.getInfo.return_value = None
        with patch("geeutils.eu.ee", mock_ee):
            eu.create_asset_folder(asset_id)

        expected_asset = {"type": "Folder"}
        mock_ee.data.createAsset.assert_called_once_with(
            expected_asset, opt_path="foo/bar/baz"
        )

    def test_raises_if_asset_id_is_too_short(self):
        with pytest.raises(ValueError):
            eu.create_asset_folder("too/short")


@pytest.mark.parametrize(
    "input_crs,extra_kwarg", [(None, {}), ("EPSG:BOGUS", {"crs": "EPSG:BOGUS"})]
)
def test_export_to_asset(input_crs, extra_kwarg):
    fake_aoi = {"foo": "bar"}
    fake_image = MagicMock()
    fake_asset_id = "bogus/path/to/asset"
    mock_geometry = MagicMock()
    fake_task_id = "MYFAKETASKIDMYFAKETASKID"
    mock_ee = MagicMock()
    mock_export = MagicMock(id=fake_task_id)
    mock_ee.Geometry.Polygon.return_value = mock_geometry
    mock_ee.batch.Export.image.toAsset.return_value = mock_export

    with patch("geeutils.eu.ee", mock_ee):
        actual_task_id = eu.export_to_asset(
            fake_aoi, fake_image, fake_asset_id, input_crs
        )

    expected_export_kwargs = {
        "image": fake_image,
        "assetId": fake_asset_id,
        "region": mock_geometry,
        "scale": 10,
        "maxPixels": 1e13,
    }
    expected_export_kwargs.update(extra_kwarg)

    mock_ee.Geometry.Polygon.assert_called_once_with(fake_aoi)
    mock_ee.batch.Export.image.toAsset.assert_called_once_with(**expected_export_kwargs)
    mock_export.start.assert_called_once_with()
    assert actual_task_id == fake_task_id


class TestExportToGcs:
    @pytest.mark.parametrize(
        "input_crs,extra_kwarg", [(None, {}), ("EPSG:BOGUS", {"crs": "EPSG:BOGUS"})]
    )
    def test_happy_path(self, input_crs, extra_kwarg):
        fake_aoi = {"foo": "bar"}
        fake_image = MagicMock()
        fake_gcs_bucket_name = "bogus-bucket"
        fake_gcs_path = "bogus/path/to/blob"
        mock_geometry = MagicMock()
        fake_file_dimensions = 256
        fake_task_id = "MYFAKETASKIDMYFAKETASKID"
        mock_ee = MagicMock()
        mock_export = MagicMock(id=fake_task_id)
        mock_ee.Geometry.Polygon.return_value = mock_geometry
        mock_ee.batch.Export.image.toCloudStorage.return_value = mock_export

        with patch("geeutils.eu.ee", mock_ee):
            actual_task_id = eu.export_to_gcs(
                fake_aoi,
                fake_image,
                fake_gcs_bucket_name,
                fake_gcs_path,
                crs=input_crs,
                file_dimensions=fake_file_dimensions,
            )

        expected_export_kwargs = {
            "image": fake_image,
            "bucket": fake_gcs_bucket_name,
            "fileNamePrefix": fake_gcs_path,
            "region": mock_geometry,
            "scale": 10,
            "maxPixels": 1e13,
            "fileDimensions": [fake_file_dimensions] * 2,
            "skipEmptyTiles": False,
        }
        expected_export_kwargs.update(extra_kwarg)

        mock_ee.Geometry.Polygon.assert_called_once_with(fake_aoi)
        mock_ee.batch.Export.image.toCloudStorage.assert_called_once_with(
            **expected_export_kwargs
        )
        mock_export.start.assert_called_once_with()
        assert actual_task_id == fake_task_id

    @pytest.mark.parametrize(
        "input_file_dimensions", [-256, 0, 1000, "not a numeric type"]
    )
    def test_raises_if_file_dimensions_not_valid(self, input_file_dimensions):
        fake_aoi = {"foo": "bar"}
        fake_image = MagicMock()
        fake_gcs_bucket_name = "bogus-bucket"
        fake_gcs_path = "bogus/path/to/blob"
        fake_file_dimensions = input_file_dimensions
        mock_ee = MagicMock()

        with pytest.raises(ValueError):
            with patch("geeutils.eu.ee", mock_ee):
                actual_task_id = eu.export_to_gcs(
                    fake_aoi,
                    fake_image,
                    fake_gcs_bucket_name,
                    fake_gcs_path,
                    file_dimensions=fake_file_dimensions,
                )
