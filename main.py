#!/usr/bin/env python3

import dropbox
from dropbox.exceptions import AuthError, ApiError
import sys
from pathlib import Path
import os

# Add OAuth2 access token here.
# You can generate one for yourself in the App Console.
# See <https://blogs.dropbox.com/developers/2014/05/generate-an-access-token-for-your-own-account/>
TOKEN = os.getenv("DROPBOX_TOKEN")
EXCLUSIONS = [".*/Personal/.*", "_remotely-save-metadata-on-remote.json"]
REMOTE_PATH = "/Apps/remotely-save/Personal Vault"

# relative location...?
DEST_PATH = "/home/fareed/code/quartz/content"


def list_remote_files(path: str) -> list[str]:
    with dropbox.Dropbox(TOKEN) as dbx:
        result = dbx.files_list_folder(path, recursive=True)
        return [file.path_display for file in result.entries]


def list_dest_files(path: str) -> list[str]:
    return [str(x) for x in Path(path).rglob("*")]


def get_diff(
    remote_path: str, dest_path: str, remote_files: list[str], dest_files: list[str]
) -> list[str]:
    remote_files = set(x.removeprefix(remote_path) for x in remote_files)
    dest_files = set(x.removeprefix(dest_path) for x in dest_files)

    return list(remote_files.difference(dest_files))


print("Dropbox")
remote_files = get_remote_files(REMOTE_PATH)
print(remote_files)

print("DIR")
dest_files = get_dest_files(DEST_PATH)
print(dest_files)

print("difference")
print(get_diff(REMOTE_PATH, DEST_PATH, remote_files, dest_files))
