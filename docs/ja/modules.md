# モジュールドキュメント

lifegence_jp は日本の業務運営に必要な3つのモジュールを提供します。本ドキュメントでは各モジュールのDocType、ワークフロー、API、プリインストールデータについて説明します。

## 目次

- [BPMモジュール](#bpmモジュール)
- [JP HRモジュール](#jp-hrモジュール)
- [JP Accountingモジュール](#jp-accountingモジュール)

---

## BPMモジュール

**表示名:** ワークフロー

n8n連携によるビジネスプロセス自動化のための承認ワークフローエンジンです。金額ベースの承認エスカレーション、稟議管理、Webhook駆動の自動化機能を提供します。

### DocType一覧

| DocType | 用途 |
|---------|------|
| BPM Settings | BPMモジュールのグローバル設定（自動化の有効/無効、タイムアウト、n8n接続） |
| BPM Action | 自動化アクションの定義（Webhook、n8nワークフロー、Frappe API、カスタムスクリプト） |
| BPM Action Log | 実行されたBPMアクションの監査ログ（結果とタイムスタンプ付き） |
| Ringi | 稟議書ドキュメント |
| Ringi Approver | 稟議書に紐づく承認者の子テーブル |
| Ringi Template | 稟議書の再利用可能なテンプレート |
| Ringi Template Approver | 稟議テンプレートのデフォルト承認者を定義する子テーブル |
| Seal Request | 社印使用の承認依頼 |
| General Application | 社内申請用の汎用申請フォーム |
| Application Template | 汎用申請の再利用可能なテンプレート |

### 承認ワークフロー

本モジュールは、標準ERPNextドキュメントとBPMカスタムDocTypeの両方に適用される8つのワークフローをインストールします。

#### ERPNextドキュメントのワークフロー

| ワークフロー | 対象ドキュメント | フロー |
|-------------|----------------|--------|
| Lead Approval | リード | Draft -> Pending Review -> Qualified / Unqualified |
| Opportunity Approval | 商談 | Draft -> Pending Review -> Converted / Lost |
| Quotation Approval | 見積書 | Draft -> Pending Manager Approval -> （エスカレーション） -> Approved / Rejected |
| Sales Order Approval | 受注 | Draft -> Pending Manager Approval -> （エスカレーション） -> Confirmed / Rejected |
| Purchase Order Approval | 発注 | Draft -> Pending Manager Approval -> Pending Budget Check -> （エスカレーション） -> Approved / Rejected |

#### BPM DocTypeのワークフロー

| ワークフロー | 対象ドキュメント | フロー |
|-------------|----------------|--------|
| Ringi Approval | 稟議 | Draft -> Pending Supervisor Approval -> Pending Department Head Approval -> Approved / Rejected |
| Seal Request Approval | 押印依頼 | Draft -> Pending Legal Review -> Pending General Affairs -> Approved / Rejected |
| General Application Approval | 汎用申請 | Draft -> Pending HR Review -> Completed / Rejected |

#### 金額ベースのエスカレーション

見積書、受注、発注のワークフローでは、ドキュメントの金額に基づいて承認権限がエスカレーションされます。

| 金額範囲（円） | 必要な承認ロール |
|---------------|-----------------|
| 500万円以下 | Approval Manager |
| 500万1円 〜 2,000万円 | Approval Director |
| 2,000万円超 | Approval Executive |

これらの閾値はセットアップ時にインストールされる承認ルールで設定されます。組織のポリシーに合わせて **設定 > Authorization Rule** で調整してください。

### BPMアクションタイプ

BPM Actionはドキュメントのワークフロー状態が変化したときにトリガーされます。`doc_events` フックがすべてのDocTypeの `on_update` を監視し、一致する状態変化をディスパッチャーに転送します。

| アクションタイプ | 説明 |
|-----------------|------|
| Webhook | ドキュメントデータを含むHTTP POSTを外部URLに送信 |
| n8n Workflow | n8n APIを経由してn8nワークフローをトリガー |
| Frappe API | ホワイトリスト登録されたFrappe APIメソッドを呼び出し |
| Custom Script | サーバーサイドのPythonスクリプトを実行 |

各BPM Actionには、トリガー条件（ドキュメントタイプ、ワークフロー状態遷移）を指定できます。

### APIリファレンス

すべてのAPIエンドポイントは `/api/method/lifegence_jp.bpm.api.<モジュール>.<関数名>` でアクセスできます。

#### ワークフローAPI (`lifegence_jp.bpm.api.workflow`)

| エンドポイント | パラメータ | 説明 |
|---------------|-----------|------|
| `get_pending_approvals` | `user`（省略可） | 指定ユーザーの承認待ちドキュメントを返す（デフォルトは現在のユーザー） |
| `apply_action` | `doctype`, `name`, `action` | ドキュメントにワークフローアクションを適用 |
| `get_workflow_status` | `doctype`, `name` | ドキュメントの現在のワークフロー状態を返す |
| `get_workflow_history` | `doctype`, `name` | ドキュメントのワークフロー遷移履歴を返す |

#### 稟議API (`lifegence_jp.bpm.api.ringi`)

| エンドポイント | パラメータ | 説明 |
|---------------|-----------|------|
| `get_pending_ringis` | `user`（省略可） | 承認待ちの稟議ドキュメントを返す |
| `approve_ringi` | `name`, `comments`（省略可） | 稟議を承認する |
| `return_ringi` | `name`, `comments` | 稟議を差し戻す（コメント必須） |
| `get_ringi_summary` | `filters`（省略可） | 稟議の集計統計を返す |

#### Webhook API (`lifegence_jp.bpm.api.webhook`)

| エンドポイント | パラメータ | 説明 |
|---------------|-----------|------|
| `receive` | （リクエストボディ） | 受信Webhookを処理。ゲストアクセス許可。HMAC-SHA256署名を検証。 |

### プリインストールデータ

**ロール（8件）:**
CRM Approver、Approval Manager、Approval Director、Approval Executive、Budget Controller、Ringi Approver、General Affairs、Legal Reviewer

**ワークフローステート（21件）:**
Draft、Pending Review、Pending Manager Approval、Pending Director Approval、Pending Executive Approval、Pending Budget Check、Approved、Rejected、Cancelled、Qualified、Unqualified、Converted、Lost、Confirmed、Submitted、Pending Supervisor Approval、Pending Department Head Approval、Pending Legal Review、Pending General Affairs、Pending HR Review、Completed

**ワークフローアクションマスター（17件）:**
Submit for Review、Approve、Reject、Request Changes、Escalate to Director、Escalate to Executive、Qualify、Disqualify、Mark as Lost、Convert、Confirm、Submit for Budget Check、Pass Budget Check、Cancel、Submit for Approval、Return、Complete

---

## JP HRモジュール

**表示名:** 人事労務

社会保険、源泉徴収、残業管理、マイナンバー管理、年末調整に対応した日本の人事労務管理モジュールです。

### DocType一覧

| DocType | 用途 |
|---------|------|
| JP HR Settings | JP HRモジュールのグローバル設定 |
| Social Insurance Rate | 都道府県別・年度別の保険料率テーブル（健康保険・厚生年金保険料率） |
| Standard Monthly Remuneration | 従業員の標準報酬月額等級 |
| Social Insurance Record | 従業員の社会保険加入・保険料記録 |
| Labor Insurance Record | 従業員の労働保険記録（労災保険・雇用保険） |
| Overtime Agreement | 三六協定の定義（時間上限付き） |
| Overtime Alert Log | 残業上限に近づいた場合のアラートログ |
| My Number Record | マイナンバーの暗号化保管 |
| My Number Access Log | マイナンバーへのすべてのアクセスの監査ログ |
| Withholding Tax Table | 国税庁の月額源泉徴収税額表 |
| Remuneration Calculation | 従業員報酬の計算記録 |
| Resident Tax | 従業員別の年間住民税データ |
| Resident Tax Monthly | 月別の住民税控除額 |
| Year End Adjustment | 年末調整ドキュメント |
| Year End Adjustment Deduction | 年末調整の控除項目の子テーブル |

### 社会保険

本モジュールには健康保険と厚生年金の保険料率テーブルが含まれています。料率は都道府県により異なり、毎年更新されます。

主な機能:
- 標準報酬月額等級に基づく保険料の自動計算
- 各種健康保険組合への対応（協会けんぽ、組合管掌健保）
- 労働保険の管理（労災保険、雇用保険）

### 源泉徴収

国税庁の令和7年版源泉徴収税額表を内蔵しています。

- **甲欄:** 扶養控除等申告書を提出した従業員用。扶養親族0人〜7人までの列を用意。
- **乙欄:** 扶養控除等申告書を提出していない従業員用。一律の税額列。

### 残業管理（三六協定）

労使協定で定められた三六協定の上限に対して、従業員の残業時間を追跡します。

**一般上限（通常の従業員）:**

| 期間 | 上限 |
|------|------|
| 月間 | 45時間 |
| 年間 | 360時間 |

**特別条項適用時の上限:**

| 期間 | 上限 |
|------|------|
| 月間 | 100時間 |
| 年間 | 720時間 |

従業員が設定された閾値に近づいた場合や超過した場合に、Overtime Alert Logが生成されます。

### マイナンバー管理

マイナンバー（個人番号）は暗号化して保管し、厳格なアクセス制御を適用しています。

- データベース内で暗号化して保管
- すべてのアクセスをMy Number Access Logに記録（アクションタイプ: 閲覧、エクスポート、提供、削除）
- アクセスには **HR Manager** または **System Manager** ロールが必要
- 番号法（マイナンバー法）に準拠した設計

### 年末調整

年末調整ドキュメントは11種類の控除に対応しており、従業員の社会保険記録と源泉徴収記録からデータを自動取得できます。

### APIリファレンス

すべてのAPIエンドポイントは `/api/method/lifegence_jp.jp_hr.api.<モジュール>.<関数名>` でアクセスできます。

#### 残業API (`lifegence_jp.jp_hr.api.overtime`)

| エンドポイント | パラメータ | 説明 |
|---------------|-----------|------|
| `check_overtime_against_agreement` | `employee`, `month`（省略可） | 従業員の現在の残業時間を三六協定の上限と照合 |
| `get_overtime_alerts` | `employee`（省略可）, `status`（省略可） | 残業アラートログを返す（従業員・ステータスでフィルタ可） |

#### マイナンバーAPI (`lifegence_jp.jp_hr.api.my_number`)

| エンドポイント | パラメータ | 説明 |
|---------------|-----------|------|
| `get_my_number_masked` | `employee` | マスク済みマイナンバーを返す（下4桁のみ表示） |
| `access_my_number` | `employee`, `purpose` | 完全なマイナンバーを取得しアクセスを記録。HR ManagerまたはSystem Managerが必要。 |
| `check_my_number_status` | `employee` | 従業員のマイナンバー記録の有無を返す |

#### 社会保険API (`lifegence_jp.jp_hr.api.social_insurance`)

| エンドポイント | パラメータ | 説明 |
|---------------|-----------|------|
| `calculate_premiums` | `employee`, `effective_date`（省略可） | 現在の報酬等級に基づいて健康保険料・厚生年金保険料を計算 |
| `get_employee_insurance_summary` | `employee` | 従業員の保険加入状況と保険料の概要を返す |

#### 源泉徴収API (`lifegence_jp.jp_hr.api.withholding_tax`)

| エンドポイント | パラメータ | 説明 |
|---------------|-----------|------|
| `calculate_monthly_withholding` | `employee`, `gross_salary`, `dependents_count` | 国税庁の税額表に基づく月額源泉徴収税額を計算 |
| `get_employee_annual_withholding` | `employee`, `fiscal_year` | 従業員の年間源泉徴収税額合計を返す |

#### 年末調整API (`lifegence_jp.jp_hr.api.year_end_adjustment`)

| エンドポイント | パラメータ | 説明 |
|---------------|-----------|------|
| `auto_populate_year_end_data` | `employee`, `fiscal_year` | 社会保険記録と源泉徴収記録から年末調整ドキュメントにデータを自動入力 |

---

## JP Accountingモジュール

**表示名:** 会計

適格請求書等保存方式（インボイス制度）と支払時の源泉徴収に対応した日本の会計・税務コンプライアンスモジュールです。

### DocType一覧

| DocType | 用途 |
|---------|------|
| JP Invoice Settings | 適格請求書制度と電子インボイスの会社レベル設定 |
| Withholding Tax Entry | 取引先・個人への支払に対する源泉徴収税の個別記録 |
| Withholding Tax Rule | 所得種類別の源泉徴収税率を定義するルール |

### 適格請求書等保存方式（インボイス制度）

2023年10月より、日本の適格請求書等保存方式（インボイス制度）では、消費税の仕入税額控除を受けるために、登録事業者が登録番号を含む特定の情報を記載した請求書を発行することが義務付けられています。

JP Invoice Settingsには以下の情報を保管します:
- 法人番号（13桁）
- 適格請求書発行事業者の登録番号（T + 13桁）
- 標準税率と軽減税率
- 電子インボイスの設定

### 源泉徴収税ルール

6種類の所得に対応しています:

| 所得種類 | 英語名 | 説明 |
|---------|--------|------|
| 報酬・料金 | Fees/Commissions | 専門家報酬、コンサルティング等 |
| 給与 | Salary | 給与所得 |
| 退職 | Retirement | 退職所得 |
| 配当 | Dividend | 配当所得 |
| 利子 | Interest | 利子所得 |
| その他 | Other | その他の所得 |

### APIリファレンス

#### 税務レポートAPI (`lifegence_jp.jp_accounting.api.tax_report`)

| エンドポイント | パラメータ | 説明 |
|---------------|-----------|------|
| `get_withholding_tax_summary` | `company`, `fiscal_year`, `income_type`（省略可） | 源泉徴収税エントリの集計を返す（所得種類でフィルタ可） |

---

## 関連ドキュメント

- [セットアップガイド](setup.md) -- インストールと初期設定
- [設定リファレンス](configuration.md) -- 設定フィールドの完全なリファレンス
- [トラブルシューティング](troubleshooting.md) -- よくある問題と解決方法
