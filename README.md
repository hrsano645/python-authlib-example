# python-authlib-example

authlibを使ったoAuth2の認証を行うためのサンプルコード

## 必要なもの

* requirements.txtを参照ください
* ryeを使って環境作成できます
* サンプルはoAuth2クライアント認証の`client_secret_basic`の利用を想定しています
  * 参考: <https://qiita.com/TakahikoKawasaki/items/63ed4a9d8d6e5109e401>

## サンプルコード

`src/python_authlib_example/__init__.py` にあります。

* 冒頭にある定数の設定をします
* main関数で、oAuth2のクライアントオブジェクトまで作成しています
* API操作のコードはrequestsオブジェクトとして準備します
* 取得したトークンは`SAVE_TOKEN_PATH`のパスに保存されます。再利用もします。
* リフレッシュトークンによる更新も行います

## 参考

Authlibの該当ページ: <https://docs.authlib.org/en/latest/client/oauth2.html>
