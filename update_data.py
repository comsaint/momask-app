"""
Script to download data from GCS
"""
from settings import ROOT_FOLDER, ASSETS_FOLDER
from google.cloud import storage

client = storage.Client()
# https://console.cloud.google.com/storage/browser/[bucket-id]/
bucket = client.get_bucket('momask')
b = bucket.blob('df.csv')

with open((ASSETS_FOLDER / 'df.csv').resolve(), "w") as f:
    b.download_to_file(f)
