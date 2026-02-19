# Disable Again Until Audio Ends

Anki 2.1 add-on that disables the **Again** (Fail) button until all answer audio has finished playing. You can still press Good / Easy while audio is playing; only Again is blocked until playback completes.

Works with:
- Anki’s built-in autoplay (av_player)
- In-card `<audio>` elements (e.g. `{{Sentence Audio}}`)

## Installation

1. **From this folder (e.g. after cloning / copying):**
   - Open Anki → **Tools** → **Add-ons** → **View Files**. This opens your `addons21` folder.
   - Copy the entire `disable_again_until_audio` folder (containing `__init__.py`, `manifest.json`, and this README) into `addons21`.
   - Restart Anki.

2. **From an .ankiaddon package:**
   - Zip the *contents* of `disable_again_until_audio` (the files inside the folder, not the folder itself), rename the zip to `disable_again_until_audio.ankiaddon`.
   - In Anki: **Tools** → **Add-ons** → **Install from file** and select the `.ankiaddon` file.
   - Restart Anki.

## Usage

- **Mouse and keyboard:** The Again button is disabled until audio ends, and pressing **1** (or your Again shortcut) is also blocked; a tooltip reminds you to finish listening first.
- **Config:** Open **Tools** → **Add-ons** → select **Disable Again Until Audio** → **Config** to choose which note fields count as “audio fields”:
  - **Apply to all cards:** Leave the list empty (or check “Apply to all cards”) to disable Again on any card that has answer audio.
  - **Specific fields:** Enter field names (one per line), e.g. `Word Audio` and `Sentence Audio`. Only cards that have at least one of these fields with content will have Again disabled until audio ends.

## Compatibility

- Anki 2.1.22+ (uses `gui_hooks.webview_did_receive_js_message` and `av_player`).
- V3 scheduler (standard in recent Anki).

## Note

If you were using the “disable Again” script inside your card template, you can remove it; this add-on handles the behavior for all cards and does not require template changes.
