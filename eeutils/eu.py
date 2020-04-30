import json
import os

import ee


def authenticate() -> None:
    service_account_key = os.environ['SERVICE_ACCOUNT_KEY']
    service_account_name = json.loads(service_account_key)['client_email']
    credentials = ee.ServiceAccountCredentials(service_account_name,
                                               key_data=service_account_key)
    ee.Initialize(credentials)


def create_asset_folder(asset_id: str) -> None:
    # One folder at a time, make sure the full path exists in GEE
    # The last segment is the asset name, not a folder name
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


def export_to_asset(aoi: dict, image: ee.Image, asset_id: str) -> str:
    try:
        region = ee.Geometry.Polygon(aoi)
    except ee.ee_exception.EEException:
        region = ee.Geometry.MultiPolygon(aoi)
    export = ee.batch.Export.image.toAsset(image=image,
                                           assetId=asset_id,
                                           region=region,
                                           scale=10,
                                           maxPixels=1e13)
    export.start()

    return export.id


def export_to_gcs(aoi: dict, image: ee.Image, gcs_bucket_name: str, gcs_path: str) -> str:
    try:
        region = ee.Geometry.Polygon(aoi)
    except ee.ee_exception.EEException:
        region = ee.Geometry.MultiPolygon(aoi)
    export = ee.batch.Export.image.toCloudStorage(image=image,
                                                  bucket=gcs_bucket_name,
                                                  fileNamePrefix=gcs_path,
                                                  region=region,
                                                  scale=10,
                                                  maxPixels=1e13)
    export.start()

    return export.id
