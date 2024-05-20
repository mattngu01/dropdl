#!/usr/bin/env python3

import dropbox
from dropbox import DropboxOAuth2FlowNoRedirect
from dropbox.files import FileMetadata
from pathlib import Path
import os
import tempfile
import shutil
import typer
from typing_extensions import Annotated

# Add OAuth2 access token here.
# You can generate one for yourself in the App Console.
# See <https://blogs.dropbox.com/developers/2014/05/generate-an-access-token-for-your-own-account/>
APP_KEY = os.getenv("DROPBOX_KEY")
APP_SECRET = os.getenv("DROPBOX_SECRET")
ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")
EXCLUSIONS = [".*/Personal/.*", "_remotely-save-metadata-on-remote.json"]
REMOTE_PATH = "/Apps/remotely-save/Personal Vault"

# relative location...?
DEST_PATH = "/home/matt/garden/content"

app = typer.Typer()


@app.command("auth")
def get_tokens(
    app_key: Annotated[str, typer.Argument(envvar="DROPBOX_KEY")],
    app_secret: Annotated[str, typer.Argument(envvar="DROPBOX_SECRET")],
) -> tuple[str]:
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
    print(
        f"Run \n\nexport DROPBOX_ACCESS_TOKEN={oauth_result.access_token} DROPBOX_REFRESH_TOKEN={oauth_result.refresh_token}\n\n",
        "to automatically authenticate without user prompt.",
    )

    return oauth_result.access_token, oauth_result.refresh_token


def create_client(
    app_key: str,
    app_secret: str,
    access_token: str | None = None,
    refresh_token: str | None = None,
) -> dropbox.Dropbox:
    if access_token is None and refresh_token is None:
        access_token, refresh_token = get_tokens(app_key, app_secret)

    return dropbox.Dropbox(
        oauth2_access_token=access_token,
        oauth2_refresh_token=refresh_token,
        app_key=app_key,
        app_secret=app_secret,
    )


def get_remote_files_metadata_recursive(
    dbx: dropbox.Dropbox, path: str
) -> list[FileMetadata]:
    result = dbx.files_list_folder(path, recursive=True)
    return [file for file in result.entries if isinstance(file, FileMetadata)]


def list_remote_dir_names_recursive(dbx: dropbox.Dropbox, path: str) -> list[str]:
    result = dbx.files_list_folder(path, recursive=True)
    return [
        file.path_display
        for file in result.entries
        if isinstance(file, dropbox.files.FolderMetadata) and file.path_display != path
    ]


def download_folder(dbx: dropbox.Dropbox, remote_path: str, dest_path: str) -> None:
    dl_folder = tempfile.mkdtemp()
    print(f"Downloading to temporary dir '{dl_folder}'")
    files = get_remote_files_metadata_recursive(dbx, remote_path)
    dirs_to_create = [
        d.removeprefix(REMOTE_PATH)
        for d in list_remote_dir_names_recursive(dbx, remote_path)
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


@app.command("dl")
def dl_folder_cmd(remote_path: str, dest_path: str) -> None:
    dbx = create_client(APP_KEY, APP_SECRET, ACCESS_TOKEN, REFRESH_TOKEN)
    # TODO: option to remove existing destination folder
    download_folder(dbx, remote_path, dest_path)


@app.command("ls")
def ls_cmd(path: str, include_dirs: Annotated[bool, typer.Option()] = True) -> None:
    dbx = create_client(APP_KEY, APP_SECRET, ACCESS_TOKEN, REFRESH_TOKEN)

    result = get_remote_files_metadata_recursive(dbx, path)
    result = [x.path_display for x in result]

    if include_dirs:
        result.extend(list_remote_dir_names_recursive(dbx, path))

    result.sort()

    for f in result:
        print(f)


if __name__ == "__main__":
    app()
