# Installation & Usage

```shell
$ pip install https://github.com/mattngu01/dropdl/releases/download/v0.1.1/dropdl-0.1.1-py3-none-any.whl
$ dropdl --help

 Usage: dropdl [OPTIONS] COMMAND [ARGS]...

╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --install-completion          Install completion for the current shell.                                              │
│ --show-completion             Show completion for the current shell, to copy it or customize the installation.       │
│ --help                        Show this message and exit.                                                            │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ auth                                                                                                                 │
│ dl                                                                                                                   │
│ ls                                                                                                                   │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

# Authorization

You will need to [create a developer app](https://www.dropbox.com/developers/apps).

Set environment variables `DROPBOX_KEY` and `DROPBOX_SECRET` to the app key and app secret.

Run the `auth` command to obtain the long-lived access and refresh token. Setting it to the according environment variables allows for automated use (i.e. in a Docker container or script).
```shell
$ python main.py auth
1. Go to: https://www.dropbox.com/oauth2/authorize?response_type=code&client_id=CLIENT_ID&token_access_type=offline
2. Click "Allow" (you might have to log in first).
3. Copy the authorization code.
Enter the authorization code here: COPY PASTE AUTH CODE FROM BROWSER
Run

export DROPBOX_ACCESS_TOKEN=GENERATED_DROPBOX_ACCESS_TOKEN DROPBOX_REFRESH_TOKEN=GENERATED_DROPBOX_REFRESH_TOKEN

to automatically authenticate without user prompt in future runs.
```

# Resources
- https://github.com/dropbox/dropbox-sdk-python
- https://www.dropbox.com/developers/apps