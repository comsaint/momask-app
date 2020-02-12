"""
Routine task to update the data from GCS.
"""


def update_data():
    from google.cloud import storage
    from google.auth.exceptions import DefaultCredentialsError
    from settings import ROOT_FOLDER, ASSETS_FOLDER
    import os
    try:
        client = storage.Client()
    except DefaultCredentialsError:
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = str((ROOT_FOLDER / "momask-b588ae99b8ea.json").resolve())
        client = storage.Client()

    with open(ASSETS_FOLDER / 'df_full.gz', 'wb') as file_obj:
        client.download_blob_to_file('gs://momask/df_full.gz', file_obj)
