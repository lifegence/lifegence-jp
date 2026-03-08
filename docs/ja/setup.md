# セットアップガイド

本ガイドでは、lifegence_jp（Frappe/ERPNext向け日本業務プロセスアプリ）のインストールと初期設定について説明します。本アプリは BPM（ワークフロー自動化）、JP HR（人事労務）、JP Accounting（会計・税務）の3モジュールを提供します。

## 前提条件

| 要件 | 最低バージョン |
|------|---------------|
| Python | 3.10以上 |
| Frappe Framework | v15以上 |
| ERPNext | v15以上 |

対象サイトにERPNextがインストール済みのFrappe Bench環境が必要です。初期セットアップについては [Frappe Bench ドキュメント](https://frappeframework.com/docs/user/en/installation) を参照してください。

## インストール

### 1. アプリのダウンロード

```bash
bench get-app https://github.com/lifegence/lifegence-jp.git
```

特定のブランチやタグを指定する場合:

```bash
bench get-app https://github.com/lifegence/lifegence-jp.git --branch main
```

### 2. サイトへのインストール

```bash
bench --site your-site install-app lifegence_jp
```

### 3. マイグレーションの実行

```bash
bench --site your-site migrate
```

## インストール後に自動実行される処理

`after_install` フックにより、`install-app` 実行時に以下のセットアップが自動的に行われます。

**BPMモジュール:**
- 8つの承認ワークフローを作成（リード、商談、見積、受注、発注、稟議、押印依頼、汎用申請）
- 金額ベースの承認エスカレーション用の承認ルールを設定
- 承認フローで使用するワークフローステートおよびワークフローアクションマスターをインストール

**JP HRモジュール:**
- JP HR設定のデフォルト値を作成:
  - 雇用保険料率区分: 一般
  - 保険料自動計算: 有効
  - 会計年度開始月: 4月

**`bench migrate` で読み込まれるフィクスチャ:**
- 8つのカスタムロール（CRM Approver、Approval Manager、Approval Director など）
- ワークフローステート（Draft、Pending Review、Approved、Rejected など）
- ワークフローアクションマスター（Submit for Review、Approve、Reject など）
- 承認閾値の承認ルール
- 社会保険料率テーブル
- 源泉徴収税額表（国税庁 令和7年版）
- デフォルト設定ドキュメント（BPM Settings、JP HR Settings、JP Invoice Settings）

## 初期設定

インストール後、各モジュールを組織に合わせて設定します。各フィールドの詳細は[設定リファレンス](configuration.md)を参照してください。

### BPMモジュール

1. **BPM Settings** を開き、デフォルト値を確認します。
2. n8n によるワークフロー自動化を使用する場合は、`n8n_base_url` と `n8n_api_key` を設定します。
3. 必要に応じてユーザーに承認ロールを割り当てます:
   - **CRM Approver** -- リード・商談の承認
   - **Approval Manager** -- 標準金額の承認
   - **Approval Director** -- 中規模金額の承認
   - **Approval Executive** -- 高額案件の承認
   - **Budget Controller** -- 発注の予算チェック
   - **Ringi Approver** -- 稟議書の承認
   - **General Affairs** -- 押印依頼・汎用申請
   - **Legal Reviewer** -- 契約・法務レビュー

4. プリインストールされた承認ルールの金額閾値が組織のポリシーに合致しているか確認します（例: 見積承認 -- Manager: 500万円以下、Director: 500万〜2,000万円、Executive: 2,000万円超）。

### JP HRモジュール

1. **JP HR Settings** を開きます。
2. **health_insurance_association** に加入している健康保険組合名を設定します。
3. **pension_office_code** に管轄の年金事務所コードを設定します。
4. **employment_insurance_rate_type** が業種に合致しているか確認します（一般、建設業、農林水産業）。
5. 当年度の社会保険料率テーブルが読み込まれているか確認します。テーブルが存在しない場合は `bench --site your-site migrate` を実行してください。

### JP Accountingモジュール

1. **JP Invoice Settings** を開きます。
2. **company_registration_number** に法人番号（13桁）を入力します。
3. 適格請求書発行事業者の場合、**qualified_invoice_issuer_number** に登録番号（T + 13桁）を入力します。
4. **default_tax_rate**（通常10%）と **reduced_tax_rate**（8%）を設定します。
5. 電子インボイスを使用する場合は **enable_e_invoice** を有効にし、**e_invoice_format**（Peppol BIS または JP PINT）を選択します。

## アプリの更新

最新バージョンに更新するには:

```bash
cd ~/frappe-bench
bench get-app lifegence_jp --upgrade
bench --site your-site migrate
bench build
bench restart
```

Supervisorを使用した本番環境の場合:

```bash
sudo supervisorctl restart all
```

## アンインストール

サイトからアプリを削除するには:

```bash
bench --site your-site uninstall-app lifegence_jp
bench remove-app lifegence_jp
```

アンインストールするとアプリのDocTypeおよび関連データがサイトデータベースから削除されます。アンインストール前にサイトのバックアップを取得してください。

## 次のステップ

- [モジュールドキュメント](modules.md) -- 3モジュール全体のDocType・APIの詳細
- [設定リファレンス](configuration.md) -- 設定フィールドの完全なリファレンス
- [トラブルシューティング](troubleshooting.md) -- よくある問題と解決方法

---

本ソフトウェアは [MIT ライセンス](../../LICENSE) の下で公開されています。
