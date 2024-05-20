#!/usr/bin/env python3

import dropbox
from dropbox import DropboxOAuth2FlowNoRedirect
from dropbox.files import FileMetadata
from pathlib import Path
import os
import tempfile
import shutil

# Add OAuth2 access token here.
# You can generate one for yourself in the App Console.
# See <https://blogs.dropbox.com/developers/2014/05/generate-an-access-token-for-your-own-account/>
APP_KEY = os.getenv("DROPBOX_KEY")
APP_SECRET = os.getenv("DROPBOX_SECRET")
EXCLUSIONS = [".*/Personal/.*", "_remotely-save-metadata-on-remote.json"]
REMOTE_PATH = "/Apps/remotely-save/Personal Vault"

# relative location...?
DEST_PATH = "/home/matt/garden/content"


def authorize(app_key: str, app_secret: str) -> dropbox.Dropbox:
    auth_flow = DropboxOAuth2FlowNoRedirect(
        app_key, app_secret, token_access_type="offline"
    )

    authorize_url = auth_flow.start()
    print("1. Go to: " + authorize_url)
    print('2. Click "Allow" (you might have to log in first).')
    print("3. Copy the authorization code.")
    auth_code = input("Enter the authorization code here: ").strip()

    try:
        oauth_result = auth_flow.finish(auth_code)
    except Exception as e:
        print("Error: %s" % (e,))
        exit(1)

    # TODO: store access + refresh token on first time, and later use refresh token to recreate client
    return dropbox.Dropbox(
        oauth2_access_token=oauth_result.access_token,
        oauth2_refresh_token=oauth_result.refresh_token,
        app_key=app_key,
        app_secret=app_secret,
    )


def list_remote_files_recursive(dbx: dropbox.Dropbox, path: str) -> list[FileMetadata]:
    result = dbx.files_list_folder(path, recursive=True)
    return [file for file in result.entries if isinstance(file, FileMetadata)]


def list_remote_dirs_recursive(dbx: dropbox.Dropbox, path: str) -> list[str]:
    result = dbx.files_list_folder(path, recursive=True)
    return [
        file.path_display
        for file in result.entries
        if isinstance(file, dropbox.files.FolderMetadata) and file.path_display != path
    ]


def list_dest_dir(path: str) -> list[str]:
    return [str(x) for x in Path(path).rglob("*")]


def download_folder(dbx: dropbox.Dropbox, remote_path: str, dest_path: str) -> None:
    dl_folder = tempfile.mkdtemp()
    print(f"Downloading to temporary dir '{dl_folder}'")
    files = list_remote_files_recursive(dbx, remote_path)
    dirs_to_create = [
        d.removeprefix(REMOTE_PATH)
        for d in list_remote_dirs_recursive(dbx, remote_path)
    ]

    for d in dirs_to_create:
        os.mkdir(dl_folder + d)

    for file in files:
        stripped = file.path_display.removeprefix(REMOTE_PATH)
        dl_path = dl_folder + stripped

        dbx.files_download_to_file(download_path=dl_path, path=file.path_display)
        os.utime(
            dl_path,
            times=(
                file.client_modified.timestamp(),
                file.client_modified.timestamp(),
            ),
        )
        print(f"Downloaded {file.path_display} to {dl_path}")

    print("Moving files to destination")

    shutil.copytree(dl_folder, dest_path)

    print("Removing temp folder", dl_folder)
    shutil.rmtree(dl_folder)
    # should clean up temp folder even if it fails?


dbx = authorize(APP_KEY, APP_SECRET)
print("Dropbox")
remote_files = list_remote_files_recursive(dbx, REMOTE_PATH)
print(remote_files)

print("DIR")
dest_files = list_dest_dir(DEST_PATH)
print(dest_files)

print("\n\n")
download_folder(dbx, REMOTE_PATH, "temp")
dbx.close()

# should just download the whole directory, then copy it over to the content file while maintaining file metadata
