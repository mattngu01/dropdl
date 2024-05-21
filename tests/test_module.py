import datetime

import dropbox
from dropbox.files import FileMetadata, FolderMetadata, ListFolderResult

from dropdl.main import (
    create_client,
    dl_folder_cmd,
    download_file_with_metadata,
    download_folder,
    get_remote_files_metadata_recursive,
    get_tokens,
    list_remote_dir_names_recursive,
    ls_cmd,
)


def test_get_tokens(mocker):
    mock_input = mocker.patch("builtins.input")
    mock_input.return_value = "test_auth_code"
    mock_start = mocker.patch(
        "dropbox.DropboxOAuth2FlowNoRedirect.start", return_value="http://example.com"
    )
    mock_finish = mocker.patch("dropbox.DropboxOAuth2FlowNoRedirect.finish")
    mock_finish.return_value.access_token = "test_access_token"
    mock_finish.return_value.refresh_token = "test_refresh_token"

    app_key = "test_app_key"
    app_secret = "test_app_secret"
    access_token, refresh_token = get_tokens(app_key, app_secret)

    assert access_token == "test_access_token"
    assert refresh_token == "test_refresh_token"
    mock_start.assert_called_once()
    mock_finish.assert_called_once_with("test_auth_code")


def test_create_client(mocker):
    mock_get_tokens = mocker.patch(
        "dropdl.main.get_tokens",
        return_value=("test_access_token", "test_refresh_token"),
    )
    mock_dropbox = mocker.patch("dropdl.main.dropbox.Dropbox")

    app_key = "test_app_key"
    app_secret = "test_app_secret"

    create_client(app_key, app_secret)

    mock_dropbox.assert_called_once_with(
        oauth2_access_token="test_access_token",
        oauth2_refresh_token="test_refresh_token",
        app_key=app_key,
        app_secret=app_secret,
    )
    mock_get_tokens.assert_called_once_with(app_key, app_secret)


def test_get_remote_files_metadata_recursive(mocker):
    dbx = mocker.Mock(spec=dropbox.Dropbox)
    dbx.files_list_folder.return_value = ListFolderResult(
        entries=[FileMetadata(name="test_file", path_display="/test_file")]
    )

    path = "/test_path"

    files = get_remote_files_metadata_recursive(dbx, path)

    assert len(files) == 1
    assert isinstance(files[0], FileMetadata)
    assert files[0].name == "test_file"
    dbx.files_list_folder.assert_called_once_with(path, recursive=True)


def test_list_remote_dir_names_recursive(mocker):
    dbx = mocker.Mock(spec=dropbox.Dropbox)
    dbx.files_list_folder.return_value = ListFolderResult(
        entries=[FolderMetadata(name="test_folder", path_display="/test_folder")]
    )
    path = "/test_path"

    dirs = list_remote_dir_names_recursive(dbx, path)

    assert len(dirs) == 1
    assert dirs[0] == "/test_folder"
    dbx.files_list_folder.assert_called_once_with(path, recursive=True)


def test_download_file_with_metadata(mocker):
    mock_utime = mocker.patch("os.utime")
    dbx = mocker.Mock(spec=dropbox.Dropbox)
    file = FileMetadata(
        name="test_file",
        path_display="/test_file",
        client_modified=datetime.datetime(2022, 5, 20),
    )
    dbx.files_download_to_file.return_value = file
    remote_path = "/test_path"
    dl_folder = "/test_dl_folder"

    download_file_with_metadata(dbx, file, remote_path, dl_folder)

    dl_path = dl_folder + "/test_file"
    dbx.files_download_to_file.assert_called_once_with(
        download_path=dl_path, path="/test_file"
    )
    mock_utime.assert_called_once_with(
        dl_path,
        times=(file.client_modified.timestamp(), file.client_modified.timestamp()),
    )


def test_download_folder(mocker):
    mock_mkdtemp = mocker.patch("tempfile.mkdtemp", return_value="/test_dl_folder")
    mock_list_dirs = mocker.patch(
        "dropdl.main.list_remote_dir_names_recursive", return_value=[]
    )
    mock_get_files = mocker.patch(
        "dropdl.main.get_remote_files_metadata_recursive", return_value=[]
    )
    mock_copytree = mocker.patch("shutil.copytree")
    mock_rmtree = mocker.patch("shutil.rmtree")

    dbx = mocker.Mock()
    remote_path = "/test_path"
    dest_path = "/test_dest_path"

    download_folder(dbx, remote_path, dest_path)

    mock_mkdtemp.assert_called_once()
    mock_list_dirs.assert_called_once_with(dbx, remote_path)
    mock_get_files.assert_called_once_with(dbx, remote_path)
    mock_copytree.assert_called_once_with("/test_dl_folder", dest_path)
    mock_rmtree.assert_called_once_with("/test_dl_folder")


def test_dl_folder_cmd(mocker):
    mock_create_client = mocker.patch("dropdl.main.create_client")
    mock_download_folder = mocker.patch("dropdl.main.download_folder")

    remote_path = "/test_remote_path"
    dest_path = "/test_dest_path"

    dl_folder_cmd(remote_path, dest_path)

    mock_create_client.assert_called_once()
    mock_download_folder.assert_called_once_with(
        mock_create_client.return_value, remote_path, dest_path
    )


def test_ls_cmd(mocker):
    mock_create_client = mocker.patch("dropdl.main.create_client")
    mock_get_files = mocker.patch(
        "dropdl.main.get_remote_files_metadata_recursive", return_value=[]
    )
    mock_list_dirs = mocker.patch(
        "dropdl.main.list_remote_dir_names_recursive", return_value=[]
    )

    path = "/test_path"
    include_dirs = True

    ls_cmd(path, include_dirs)

    mock_create_client.assert_called_once()
    mock_get_files.assert_called_once_with(mock_create_client.return_value, path)
    mock_list_dirs.assert_called_once_with(mock_create_client.return_value, path)
