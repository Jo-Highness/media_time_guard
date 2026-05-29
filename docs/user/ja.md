# Media Time Guard – ユーザーガイド（日本語）

Media Time Guard は、ある人物の1日のメディア時間をその人物のメディアプレーヤー
（例: Sonos One）上で制限し、子供が回避しようとしても確実に制限を適用します。

## 1. インストール

**HACS 経由（推奨）**
1. HACS を開く → ⋮ メニュー → *カスタムリポジトリ*。
2. リポジトリ URL を追加し、カテゴリは **Integration**。
3. *Media Time Guard* を検索してダウンロード。
4. Home Assistant を再起動。

**手動:** `custom_components/media_time_guard/` フォルダを `<config>/custom_components/` に
コピーして HA を再起動します。

## 2. 人物の設定

*設定 → デバイスとサービス → 統合を追加 → 「Media Time Guard」*。
人物ごとに1つのエントリが作成されます。ウィザードは4ステップです:

1. **人物とプレーヤー**
   - **名前**: 例 `Luke`。（子供には `person` エンティティがないことが多いので、名前を入力します。）
   - **person エンティティ**（任意）: 存在する場合。
   - **メディアプレーヤー**: 1つ以上。プレーヤーは **1人** にのみ割り当てられます。
2. **1日の予算**: 月曜〜日曜の分数。`0` = 終日禁止。
3. **警告**（任意）: 有効/無効、残り時間のしきい値（分）、方式:
   - **TTS**: TTS エンジンとアナウンス文を選択。`{minutes}` は残り分数に置換されます。
   - **メディア**: 再生するメディア URL / コンテンツ ID。
4. **リセット**: カウンターをリセットする時刻（既定 `00:00`）。

後でエントリの **設定** ボタンから変更できます。

## 3. 動作

- 割り当てられたプレーヤーの少なくとも1つが **再生中**（`playing`）のときのみ時間が加算されます。
- 複数のスピーカーで同時に再生しても **二重には** 加算されません。
- 予算を使い切ると、すべてのプレーヤーが **停止** され、その日の残りはロックされます。
  スピーカーの電源を入れ直しても HA を再起動してもロックは **解除されません**。
- 終了の少し前に1回限りの警告が出ます（有効な場合）。

## 4. 人物ごとのエンティティ

| エンティティ | 意味 |
|---|---|
| `sensor.media_time_<person>_remaining` | 本日の残り分数 |
| `switch.media_time_<person>_suspend_today` | 本日の強制を一時停止（例: 病気） |
| `number.media_time_<person>_extend` | 本日の追加分（絶対値） |
| `button.media_time_<person>_extend_15` / `_extend_30` | +15 / +30 分 |

センサーの属性: `budget_minutes`, `used_minutes`, `remaining_minutes`, `is_locked`,
`is_suspended`, `extra_minutes_today`, `warned_today`。

## 5. よくある操作

- **時間を増やす:** +15/+30 ボタンを押す、number エンティティを設定する、または
  `media_time_guard.extend_time` を `person` と `minutes` で呼び出す。
- **本日は制限なし（子供が病気）:** *Suspend Today* スイッチをオンにするか、
  `media_time_guard.suspend_today` を `suspended: true` で呼び出す。
- **手動リセット:** `media_time_guard.reset_person` を呼び出す。

## 6. 既知の制限

カウントは `playing` 状態に基づきます。**ミュートや非常に小さい音量での再生も加算されます**。
プレーヤーが依然として「再生中」だからです。
