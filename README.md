# Pictsense Python Bot Library

Pictsense（ピクトセンス）の操作を自動化・ボット化するためのPythonライブラリです。
イベント駆動型の設計により、チャットへの自動応答、描画の自動化、ゲーム進行管理などを直感的に記述できます。

## 🌟 主な機能

- ロビー・部屋の自動管理: 部屋の作成、検索、入室、参加リクエストの自動承認。
- イベントハンドリング: チャット、入退室、描画、ゲーム開始、お題受信などをリアルタイムで取得。
- 高度な描画機能: 
  - 描画データ（ストローク）の送信。
  - フォントファイル（TrueType）を利用した文字のベクター描画。
- ゲームプレイ補助:
  - お題の自動パス。
  - 受信したヒントと選択肢に基づく回答の総当たり（ブルートフォース）試行。
- 低レイヤー操作: Socket.IO通信を介したサーバーとの直接メッセージ送受信。

## 📦 必要条件

以下のライブラリのインストールが必要です。

pip install aiohttp fontTools

---

## 🚀 クイックスタート

```python
from client import Pictsense

client = Pictsense()


@client.event
async def on_ready():
    print("Bot起動成功")
    await client.create_room("部屋名","オーナー名")


@client.event
async def on_join_request(message):
    await client.auto_reply_join_request(message)


@client.event
async def on_join(message):
    await client.send_chat("こんにちは")


if __name__ == "__main__":
    client.run()
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## 📖 API リファレンス
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### 1. 起動・終了

- `start()`  
  コールバック設定後、ロビーへ接続を開始します。

- `close()`  
  ロビーおよびルームへの接続を安全に終了します。

- `run()`  
  asyncio を内部で起動し、常駐実行します（on_ready が発火）。

---

### 2. イベント登録

`@pictsense.event` デコレータを使用して以下のイベントを処理できます。

- `on_ready`  
  ロビー接続完了時

- `on_join_request`  
  参加リクエストを受信した時

- `on_join`  
  ユーザーが入室した時

- `on_userleave`  
  ユーザーが退室した時

- `on_chat`  
  チャットメッセージを受信した時

- `on_gamestart`  
  ゲームが開始された時

- `on_subject`  
  お題が割り振られた時

- `on_question`  
  クイズが出題された時

- `on_hint`  
  ヒントが提示された時

- `on_stroke`  
  描画データ（ストローク）を受信した時

- `on_sysmessage`  
  システムメッセージを受信した時

- `on_clear`  
  キャンバスがクリアされた時

- `on_error`  
  エラーが発生した時

---

### 3. メッセージ・コマンド

- `on_command(msg, cmd, func)`  
  チャットが特定の cmd で始まる場合に func を実行します。

- `send_chat(text)`  
  チャットメッセージを送信します。

---

### 4. ルーム・ユーザー操作

- `join_room(room, name)`  
  指定したルーム名とユーザー名で参加します。

- `create_room(room, owner)`  
  新しくルームを作成します。

- `auto_reply_join_request(msg)`  
  受信した参加リクエストを自動で承認します。

- `get_user_by_uid(uid)`  
  UID（ユーザーID）からユーザー情報を取得します。

---

### 5. ゲーム・描画操作

- `send_game()`  
  ゲームを開始します。

- `send_pass()`  
  お題をパスします。

- `solve_question_bruteforce(msg)`  
  受信したヒントと候補から正解を総当たりで試行します。

- `send_stroke(size, color, alpha, path)`  
  指定した座標配列 `[[x, y], ...]` で線を描画します。

- `draw_text(context, x, y, size)`  
  設定したフォントを使用して文字をベクター描画します。  
  （デフォルト: NotoSansJP-VariableFont_wght.ttf）

---

### 6. 高負荷・テスト用（※非推奨）

- `raid_room()`  
  短時間に大量のデータを送信します。

- `dos_attack()`  
  raid_room をループ実行します。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## ⚠️ 注意事項
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

- 本ライブラリは学習およびデバッグを目的としています。
- サーバーに過度な負荷をかける機能（raid / dos）は、  
  自身の管理下にある環境以外での使用を禁止します。
- 利用規約を遵守し、他のプレイヤーの迷惑にならない範囲で利用してください。
