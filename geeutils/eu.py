"""
 Copyright Vulcan Inc. 2018-2020

 Licensed under the Apache License, Version 2.0 (the "License").
 You may not use this file except in compliance with the License.
 A copy of the License is located at

     http://www.apache.org/licenses/LICENSE-2.0

 or in the "license" file accompanying this file. This file is distributed
 on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
 express or implied. See the License for the specific language governing
 permissions and limitations under the License.
"""


"""A utility library for interacting with the Google Earth Engine (GEE) API."""

import json
import os

import ee


def authenticate(allow_interactive=True) -> None:
    """Authenticate with the GEE API.

    A SERVICE_ACCOUNT_KEY environment variable must be set with the key to a
    Google Cloud Platform service account that has permissions in GEE.

    Args:
        allow_interactive: If False, does not allow the interactive login workflow.
                           Default=True, continue to interactive login workflow.

    Returns:
        None
    """

    try:
        service_account_key = os.environ['SERVICE_ACCOUNT_KEY']
    except KeyError:
        if not os.path.exists('/root/.config/earthengine/credentials'):
            if not allow_interactive:
                raise ee.ee_exception.EEException('You cannot authenticate as SERVICE_ACCOUNT_KEY and GEE credentials file is missing')
            ee.Authenticate()
        ee.Initialize()
        return

    try:
        service_account_name = json.loads(service_account_key)['client_email']
    except json.decoder.JSONDecodeError as e:
        raise ValueError('SERVICE_ACCOUNT_KEY is empty or contains invalid JSON') from e
    credentials = ee.ServiceAccountCredentials(service_account_name,
                                               key_data=service_account_key)
    ee.Initialize(credentials)


def create_asset_folder(asset_id: str) -> None:
    """Create an asset folder in GEE.

    Also create intermediate folders along the path, if they don't already
    exist.

    Args:
        asset_id: A path to the folder to be created.

    Returns:
        None
    """

    if asset_id.startswith('/'):
        asset_id = asset_id[1:]
    if asset_id.endswith('/'):
        asset_id = asset_id[:-1]
    path_segments = asset_id.split('/')
    if len(path_segments) < 3:
        raise ValueError('GEE asset id {} is too short (must have more than 2 path segments)'.format(asset_id))
    for i in range(2, len(path_segments)-1):
        path = '/'.join(path_segments[:i+1])
        if not ee.data.getInfo(path):
            ee.data.createAsset({'type': 'Folder'},
                                opt_path=path)


def export_to_asset(aoi: dict,
                    image: ee.Image,
                    asset_id: str,
                    crs: str=None) -> str:
    """Export an image to GEE as a GEE asset.

    Args:
        aoi: A GeoJSON geometry describing the geographic area to export.
        image: An instance of ee.Image - the image to export.
        asset_id: The ID of the GEE asset to be created.
        crs: Optional.  If provided, convert the image to this Coordinate Reference System.

    Returns:
        A string containing the GEE export task ID.
    """
    try:
        region = ee.Geometry.Polygon(aoi)
    except ee.ee_exception.EEException:
        region = ee.Geometry.MultiPolygon(aoi)
    export_kwargs = {
        'image': image,
        'assetId': asset_id,
        'region': region,
        'scale': 10,
        'maxPixels': 1e13
    }
    if crs:
        export_kwargs.update({'crs': crs})
    export = ee.batch.Export.image.toAsset(**export_kwargs)
    export.start()

    return export.id


def export_to_gcs(aoi: dict,
                  image: ee.Image,
                  gcs_bucket_name: str,
                  gcs_path: str,
                  crs: str=None) -> str:
    """Export an image to Google Cloud Storage (GCS).

    Depending on the size of the image, GEE may export it in multiple chunks.

    Args:
        aoi: A GeoJSON geometry describing the geographic area to export.
        image: An instance of ee.Image - the image to export.
        gcs_bucket_name: The name of the target GCS bucket.
        gcs_path: The path in the bucket where the image should be exported.
        crs: Optional.  If provided, convert the image to this Coordinate Reference System.

    Returns:
        A string containing the GEE export task ID.
    """
    try:
        region = ee.Geometry.Polygon(aoi)
    except ee.ee_exception.EEException:
        region = ee.Geometry.MultiPolygon(aoi)
    export_kwargs = {
        'image': image,
        'bucket': gcs_bucket_name,
        'fileNamePrefix': gcs_path,
        'region': region,
        'scale': 10,
        'maxPixels': 1e13
    }
    if crs:
        export_kwargs.update({'crs': crs})
    export = ee.batch.Export.image.toCloudStorage(**export_kwargs)
    export.start()

    return export.id
