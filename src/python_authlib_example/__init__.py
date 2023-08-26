# python-authlib-example
# 例: oAuth2のクライアント認証。client_secret_basicタイプで認証を行います
# リフレッシュトークン対応

import json
import re
import wsgiref.simple_server
import wsgiref.util
from dataclasses import dataclass
from pathlib import Path

from authlib.integrations.requests_client import OAuth2Session

AUTHORZATION_BASE_URL = "認証サーバーのベースURL"
TOKEN_URL = "トークン更新のURL"
API_ENDPOINT = "APIのエンドポイント"

# クライアントIDとシークレットは別の保存方法推奨
CLIENT_ID = ""
CLIENT_SECRET = ""

REDIRECT_URI = "http://localhost:8080" # リダイレクト先のURL
SCOPE = "[scope]"
SAVE_TOKEN_PATH = Path("[path/to/token_save_dir]") / "access_token.json"


# ローカルサーバーを作って、リダイレクトされたUrlを取り出す作業。
# Googleのライブラリを参考にしています。
# ref: https://github.com/googleapis/google-auth-library-python-oauthlib/blob/3c829e87dd7720ddc1e70431927072e612170c98/google_auth_oauthlib/flow.py
# Licence: Apache v2
class RedirectWsgiApp(object):
    """WSGI app to handle the authorization redirect.
    Stores the request URI and displays the given success message.
    """

    def __init__(self, success_message):
        """
        Args:
            success_message (str): The message to display in the web browser
                the authorization flow is complete.
        """
        self.last_request_uri = None
        self._success_message = success_message

    def __call__(self, environ, start_response):
        """WSGI Callable.
        Args:
            environ (Mapping[str, Any]): The WSGI environment.
            start_response (Callable[str, list]): The WSGI start_response
                callable.
        Returns:
            Iterable[bytes]: The response body.
        """
        start_response("200 OK", [("Content-type", "text/plain; charset=utf-8")])
        self.last_request_uri = wsgiref.util.request_uri(environ)
        return [self._success_message.encode("utf-8")]


def get_auth_response_by_localserver(
    success_message: str,
    bind_addr=None,
    host="localhost",
    port=8080,
    redirect_uri_trailing_slash=True,
    timeout_seconds=None,
) -> str:
    """認証時にlocalhostを起動して、その後、
    リダイレクトURLのレスポンスを得たらコードを取り出し終了する"""

    redirect_uri = ""
    wsgi_app = RedirectWsgiApp(success_message)

    wsgiref.simple_server.WSGIServer.allow_reuse_address = False
    local_server = wsgiref.simple_server.make_server(bind_addr or host, port, wsgi_app)

    redirect_uri_format = (
        "http://{}:{}/" if redirect_uri_trailing_slash else "http://{}:{}"
    )
    redirect_uri = redirect_uri_format.format(host, local_server.server_port)

    print(f"リダイレクトURL: {redirect_uri}")
    print("レスポンス待機中...")

    local_server.timeout = timeout_seconds
    local_server.handle_request()

    # Note: using https here because oauthlib is very picky that
    # OAuth 2.0 should only occur over https.
    authorization_response = wsgi_app.last_request_uri.replace("http", "https")

    # This closes the socket
    local_server.server_close()

    return authorization_response


@dataclass
class ExampleOAuth2ClientGenerator:
    client_id: str
    client_secret: str
    token = None

    def _load_token(self) -> dict:
        """jsonで保存されているアクセストークンを取得する。"""
        try:
            with SAVE_TOKEN_PATH.open("r") as access_token_cache:
                token = json.load(access_token_cache)
        except IOError:
            return None
        return token

    # **kwargsはupdate_tokenが渡す引数を受け取るだけにしています
    def _save_token(self, token: dict, **kwargs):
        """アクセストークンをjsonで保存する。"""
        with SAVE_TOKEN_PATH.open("w") as access_token_cache:
            json.dump(token, access_token_cache)

    def _get_new_oauth_session(self):
        """MFクラウドのoAuthのセッション取得処理"""

        oauth2_session = OAuth2Session(
            client_id=self.client_id,
            client_secret=self.client_secret,
            scope=SCOPE,
            redirect_uri=REDIRECT_URI,
        )
        authorization_url, _ = oauth2_session.create_authorization_url(
            AUTHORZATION_BASE_URL,
        )

        print("こちらのURLから認証を行ってください", authorization_url)

        # リダイレクト先のサーバーを生成して、認証後にコードを取得する
        redirect_port = int(re.sub(r"https?://.*:", "", REDIRECT_URI))
        redirect_response = get_auth_response_by_localserver(
            success_message="get code!! close browser",
            bind_addr="0.0.0.0",
            port=redirect_port,
        )

        return oauth2_session, redirect_response

    def get_session(self) -> OAuth2Session:
        self.token = self._load_token()

        if self.token:
            # 現在のトークンを使ってセッションを作成。
            # 自動的にリフレッシュトークンも使いトークンの更新も行う
            oauth2_session = OAuth2Session(
                self.client_id,
                self.client_secret,
                token=self.token,
                token_endpoint=TOKEN_URL,
                update_token=self._save_token,
            )

        else:
            # 新規にセッションを作成する
            oauth2_session, redirect_response = self._get_new_oauth_session()

            # トークンを取得する
            self.token = oauth2_session.fetch_token(
                url=TOKEN_URL,
                authorization_response=redirect_response,
            )

            # 取得したtokenをjsonで保存
            self._save_token(self.token)

        return oauth2_session

def main():
    # クライアントの作成
    clientgenerator = ExampleOAuth2ClientGenerator(CLIENT_ID, CLIENT_SECRET)
    client = clientgenerator.get_session()
    # 現在のトークンを表示
    print(client.token)

    # なんらかのAPIを実行する...

if __name__ == "__main__":
    main()