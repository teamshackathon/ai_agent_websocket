1. 初期ビルド
```
以下の条件を満たす環境を構築するWebアプリの初期コードを作成してください。

- 言語:Next.js
- 録音開始と録音停止のボタンが用意されている
- 録音停止ボタンを押下するとそれまで録音されていた音声データを保存し、再生リストに追加される
- 録音中に無音を検知したら自動的に音声データを保存し、再生リストに追加する。音声データ保存後は音声録音が再開されている
- 音声データを保存したら自動的にWebsockelt通信でサーバーサイドに音声データを送信する
```