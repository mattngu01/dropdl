#!/usr/bin/env python3

import dropbox
from dropbox.exceptions import AuthError, ApiError
import sys
from pathlib import Path
import os
import tempfile
from contextlib import closing

# Add OAuth2 access token here.
# You can generate one for yourself in the App Console.
# See <https://blogs.dropbox.com/developers/2014/05/generate-an-access-token-for-your-own-account/>
TOKEN = os.getenv("DROPBOX_TOKEN")
EXCLUSIONS = [".*/Personal/.*", "_remotely-save-metadata-on-remote.json"]
REMOTE_PATH = "/Apps/remotely-save/Personal Vault"

# relative location...?
DEST_PATH = "/home/matt/garden/content"


def list_remote_files_recursive(path: str) -> list[str]:
    with dropbox.Dropbox(TOKEN) as dbx:
        result = dbx.files_list_folder(path, recursive=True)
        return [
            file.path_display
            for file in result.entries
            if isinstance(file, dropbox.files.FileMetadata)
        ]


def list_remote_dirs_recursive(path: str) -> list[str]:
    with dropbox.Dropbox(TOKEN) as dbx:
        result = dbx.files_list_folder(path, recursive=True)
        return [
            file.path_display
            for file in result.entries
            if isinstance(file, dropbox.files.FolderMetadata)
            and file.path_display != path
        ]


def list_dest_dir(path: str) -> list[str]:
    return [str(x) for x in Path(path).rglob("*")]


def get_diff(
    remote_path: str, dest_path: str, remote_files: list[str], dest_files: list[str]
) -> list[str]:
    remote_files = set(x.removeprefix(remote_path) for x in remote_files)
    dest_files = set(x.removeprefix(dest_path) for x in dest_files)

    return list(remote_files.difference(dest_files))


def download_folder(remote_path: str):
    dl_folder = tempfile.mkdtemp()
    print(f"Downloading to temporary dir '{dl_folder}'")
    files = list_remote_files_recursive(remote_path)
    dirs_to_create = [
        d.removeprefix(REMOTE_PATH) for d in list_remote_dirs_recursive(remote_path)
    ]

    for d in dirs_to_create:
        os.mkdir(dl_folder + d)

    with dropbox.Dropbox(TOKEN) as dbx:
        for f in files:
            stripped = f.removeprefix(REMOTE_PATH)
            dl_path = dl_folder + stripped

            dbx.files_download_to_file(download_path=dl_path, path=f)
            print(f"Downloaded {f} to {dl_path}")


print("Dropbox")
remote_files = list_remote_files_recursive(REMOTE_PATH)
print(remote_files)

print("DIR")
dest_files = list_dest_dir(DEST_PATH)
print(dest_files)

print("difference")
print(get_diff(REMOTE_PATH, DEST_PATH, remote_files, dest_files))

print("\n\n")
download_folder(REMOTE_PATH)

# should just download the whole directory, then copy it over to the content file while maintaining file metadata
