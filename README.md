# RAG Q&A Bot

LangChainを使用した「自分専用」要約・Q&AボットのRAGアプリケーション

## 概要

このアプリケーションは、アップロードしたドキュメント（PDF、Markdown、テキストファイル）やWebページの内容に基づいて質問に回答するRAG（Retrieval-Augmented Generation）システムです。

### 主な機能

- **ドキュメント読み込み**: PDF、Markdown、テキストファイル、Webページに対応
- **ベクトル検索**: FAISSによる高速な類似度検索
- **チャット履歴**: 会話のコンテキストを保持した対話
- **引用元表示**: 回答の根拠となった箇所を表示
- **複数ドキュメント対応**: 複数のファイル/URLを登録可能

## 要件定義

| 項目 | 採用技術 |
|------|----------|
| フレームワーク | LangChain |
| LLM | OpenAI GPT-4o-mini |
| Embeddings | OpenAI text-embedding-3-small |
| ベクトルDB | FAISS |
| UI | Streamlit |
| APIキー管理 | python-dotenv (.env) |

## 事前準備

### 必要なもの

- Python 3.10以上
- OpenAI APIキー（**有料**）

### OpenAI APIキーの取得

> **注意**: ChatGPT Plus（月額$20）とOpenAI APIは**別サービス**です。
> ChatGPT Plusに加入していても、APIは別途料金がかかります。

1. [OpenAI Platform](https://platform.openai.com/) にアクセス
2. アカウントを作成またはログイン
3. [Billing](https://platform.openai.com/account/billing) でクレジットカードを登録
4. クレジットを購入（最低$5から）
5. [API Keys](https://platform.openai.com/api-keys) で新しいAPIキーを作成
6. 作成したキーをコピー（一度しか表示されません）

### API料金の目安

このアプリで使用するモデルは非常に安価です：

| モデル | 用途 | 料金（目安） |
|--------|------|-------------|
| text-embedding-3-small | 文書のベクトル化 | $0.02 / 100万トークン |
| gpt-4o-mini | 回答生成 | $0.15 / 100万入力トークン |

通常の利用であれば、月に数十円〜数百円程度です。

## インストール

```bash
# リポジトリをクローンまたはダウンロード後、ディレクトリに移動
cd langchain

# 仮想環境を作成
python -m venv venv

# 仮想環境を有効化（Windows）
venv\Scripts\activate

# 仮想環境を有効化（Mac/Linux）
source venv/bin/activate

# 依存パッケージをインストール
pip install -r requirements.txt
```

## 設定

### APIキーの設定

1. `.env.example`をコピーして`.env`ファイルを作成

```bash
# Windows
copy .env.example .env

# Mac/Linux
cp .env.example .env
```

2. `.env`ファイルを編集してAPIキーを設定

```
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
```

> **セキュリティ注意**: `.env`ファイルはGitにコミットしないでください（.gitignoreで除外済み）

## 実行方法

```bash
# 仮想環境を有効化（未有効の場合）
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# アプリを起動
streamlit run app.py
```

ブラウザが自動で開き、`http://localhost:8501` にアクセスします。

### 終了方法

- ターミナルで `Ctrl + C`
- 仮想環境を終了: `deactivate`

## アプリの使い方

### 1. ドキュメントの登録

**ファイルアップロード**
1. サイドバーの「ファイルアップロード」でPDF/TXT/MDファイルを選択
2. 「ファイルを追加」ボタンをクリック
3. 処理完了後、「登録チャンク数」が増加

**URL追加**
1. サイドバーの「URL追加」にWebページのURLを入力
2. 「URLを追加」ボタンをクリック

### 2. 質問する

1. チャット入力欄に質問を入力
2. Enterキーで送信
3. 回答と引用元が表示される

### 3. 引用元の確認

- 右側の「引用元」エリアに、回答の根拠となった文書の該当箇所が表示されます
- 各出典をクリックすると詳細を確認できます

### 4. リセット

- **履歴クリア**: チャット履歴のみ削除（登録ドキュメントは保持）
- **全てリセット**: ドキュメントとチャット履歴を全て削除

## フォルダ構造

```
langchain/
├── app.py                 # Streamlit メインUI
├── rag_engine.py          # RAGコアロジック
├── document_loader.py     # ドキュメント読み込み処理
├── requirements.txt       # 依存パッケージ
├── .env.example           # 環境変数テンプレート
├── .env                   # 環境変数（APIキー）※Git管理外
├── .gitignore             # Git除外設定
├── README.md              # このファイル
├── venv/                  # 仮想環境 ※Git管理外
└── data/                  # アップロードファイル保存用
    └── .gitkeep
```

### 各ファイルの説明

| ファイル | 説明 |
|----------|------|
| `app.py` | Streamlit UIの実装。ファイルアップロード、チャット画面、引用元表示を担当 |
| `rag_engine.py` | RAGのコアロジック。FAISSベクトルストア、検索、回答生成、チャット履歴管理 |
| `document_loader.py` | ドキュメント読み込み。PDF/テキスト/URL対応、チャンク分割処理 |
| `requirements.txt` | Pythonパッケージの依存関係定義 |
| `.env.example` | 環境変数のテンプレート |
| `.gitignore` | Git管理から除外するファイル/フォルダの定義 |

## 改善ポイント

### 機能拡張

- [ ] Word/Excel/PowerPointファイル対応
- [ ] 画像内テキストのOCR対応
- [ ] ベクトルDBの永続化（現在はメモリ上のみ）
- [ ] 複数の会話セッション管理
- [ ] 回答の評価・フィードバック機能

### パフォーマンス

- [ ] チャンクサイズの最適化（現在500文字）
- [ ] 検索結果数(k)の調整機能
- [ ] キャッシュ機能の追加
- [ ] 非同期処理によるUI応答性向上

### セキュリティ

- [ ] アップロードファイルのサイズ制限
- [ ] ファイルタイプの厳密な検証
- [ ] レート制限の実装

### UX

- [ ] ドラッグ&ドロップ対応
- [ ] 登録済みドキュメント一覧表示
- [ ] 個別ドキュメントの削除機能
- [ ] ダークモード対応

## デプロイ・運用

### ローカル運用のまま使う場合

現状のままで個人利用には十分です。定期的に以下を確認してください：

- OpenAI APIの使用量（[Usage](https://platform.openai.com/usage)）
- `data/`フォルダのサイズ管理

### クラウドデプロイする場合

#### Streamlit Cloud（推奨・無料）

1. GitHubにリポジトリをプッシュ
2. [Streamlit Cloud](https://streamlit.io/cloud) でアカウント作成
3. リポジトリを選択してデプロイ
4. Secrets設定で`OPENAI_API_KEY`を追加

#### その他の選択肢

- **Heroku**: Procfile追加で対応可能
- **AWS/GCP/Azure**: コンテナ化してデプロイ
- **自社サーバー**: Nginx + Gunicornで運用

### 本番運用時の注意点

1. **APIキー管理**: 環境変数またはシークレット管理サービスを使用
2. **アクセス制限**: 認証機能の追加を検討
3. **ログ管理**: 質問/回答のログを適切に管理
4. **コスト監視**: OpenAI APIの使用量アラートを設定
5. **バックアップ**: 重要なドキュメントは別途保管

## ライセンス

MIT License

## 参考リンク

- [LangChain Documentation](https://python.langchain.com/)
- [OpenAI API Reference](https://platform.openai.com/docs/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [FAISS Wiki](https://github.com/facebookresearch/faiss/wiki)
