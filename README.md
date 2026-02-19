# Disable Again Until Audio Ends

An Anki 2.1 add-on that disables the **Again** (and optionally other answer keys) until all answer audio has finished playing — so you actually listen to word and sentence audio instead of skipping it.

[![Anki 2.1.22+](https://img.shields.io/badge/Anki-2.1.22%2B-blue)](https://apps.ankiweb.net/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## Features

- **Blocks Again (and more):** Disables the Again button and its keyboard shortcut until answer audio finishes. Optionally block Hard / Good / Easy as well (configurable).
- **Works with your shortcuts:** No matter which key you use for Again (1, F, or custom), that key is blocked until audio ends.
- **Flexible audio detection:** Works with Anki’s autoplay (av_player) and in-card `<audio>` (e.g. `{{Word Audio}}`, `{{Sentence Audio}}`).
- **Configurable scope:** Restrict to specific note types by choosing which fields count as “audio fields,” or apply to all cards.

---

## Installation

1. In Anki: **Tools** → **Add-ons** → **Get Add-ons**.
2. Paste this code and click **OK**: **`1753038642`**
3. Restart Anki.

---

## Configuration

**Tools** → **Add-ons** → select **Disable Again Until Audio** → **Config**.

| Option | Description |
|--------|-------------|
| **Block these answer keys until audio ends** | Check **Again (ease 1)**, **Hard (2)**, **Good (3)**, **Easy (4)**. At least one must be checked. Use this if your “fail” key isn’t 1, or to block multiple keys. |
| **Audio field names** | One field per line (e.g. `Word Audio`, `Sentence Audio`). Only cards with at least one of these fields filled get the blocking behavior. Leave empty to apply to all cards with answer audio. |
| **Apply to all cards** | When checked, the field list is ignored and the add-on applies to any card with answer-side audio. |

---

## Usage

- When you show the answer, any checked answer buttons are disabled until:
  - Anki’s audio queue is empty, and  
  - Every `<audio>` on the card has finished.
- Pressing a blocked keyboard shortcut shows: *“Finish listening to audio before using that shortcut.”*
- Good / Easy (or any unchecked keys) stay available so you can still pass the card while audio plays.

---

## Compatibility

- **Anki:** 2.1.22 or newer (uses `gui_hooks.webview_did_receive_js_message` and `av_player`).
- **Scheduler:** V3 (default in recent Anki).

---

## License

MIT. See [LICENSE](LICENSE).

---

## Contributing

Issues and pull requests are welcome. If you’re fixing a bug or adding a feature, please open an issue first so we can align.
