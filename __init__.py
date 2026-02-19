# Disable Again (Fail) button until all answer audio has finished playing.
# Works with both Anki's av_player (autoplay) and in-card <audio> elements.

from __future__ import annotations

from aqt import gui_hooks, mw
from aqt.sound import av_player
from aqt.qt import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QPlainTextEdit,
    QDialogButtonBox,
    QCheckBox,
    QGroupBox,
)
from aqt.utils import tooltip

# State: we disable the Again button when the answer is shown and re-enable
# when (1) av_player queue is empty and (2) all <audio> in the card have ended.
_state = {
    "pending": False,
    "av_done": False,
    "card_done": False,
}

_MSG = "disableAgainAudioDone"

# Delay (ms) before disabling - ease buttons may be drawn after a short delay.
_DISABLE_DELAY_MS = 200

# Build JS to disable/enable buttons by ease (1=Again, 2=Hard, 3=Good, 4=Easy).
def _js_disable_buttons(eases: list[int]) -> str:
    if not eases:
        return "(function(){})();"
    arr = ",".join(str(e) for e in eases)
    return f"""
(function(){{
  var eases = [{arr}];
  for (var i = 0; i < eases.length; i++) {{
    var b = document.querySelector('button[id=\"ease' + eases[i] + '\"]') || document.querySelector('button[id^=\"ease' + eases[i] + '\"]');
    if (b) b.disabled = true;
  }}
}})();
"""


def _js_enable_buttons(eases: list[int]) -> str:
    if not eases:
        return "(function(){})();"
    arr = ",".join(str(e) for e in eases)
    return f"""
(function(){{
  var eases = [{arr}];
  for (var i = 0; i < eases.length; i++) {{
    var b = document.querySelector('button[id=\"ease' + eases[i] + '\"]') || document.querySelector('button[id^=\"ease' + eases[i] + '\"]');
    if (b) b.disabled = false;
  }}
}})();
"""

# Injected into the answer HTML: run after DOM update, wait for all <audio> to end, then notify.
# onUpdateHook runs after the new card is in the DOM (Anki reviewer API).
_CARD_AUDIO_SCRIPT = """
<script>
(function(){
  function run() {
    function notify() { try { if (typeof pycmd === 'function') pycmd('""" + _MSG + """'); } catch(e) {} }
    var audios = document.querySelectorAll('audio');
    if (audios.length === 0) { notify(); return; }
    var left = audios.length;
    function onEnd() {
      left--;
      if (left <= 0) notify();
    }
    for (var i = 0; i < audios.length; i++) audios[i].addEventListener('ended', onEnd);
  }
  if (typeof onUpdateHook !== 'undefined' && Array.isArray(onUpdateHook)) {
    onUpdateHook.push(run);
  } else {
    run();
  }
})();
</script>
"""


def _get_config() -> dict:
    cfg = mw.addonManager.getConfig(__name__)
    if cfg is None:
        return {"audio_field_names": [], "blocked_eases": [1]}
    names = cfg.get("audio_field_names")
    if isinstance(names, list):
        names = [str(s).strip() for s in names if str(s).strip()]
    elif isinstance(names, str):
        names = [s.strip() for s in names.replace(",", "\n").splitlines() if s.strip()]
    else:
        names = []
    raw = cfg.get("blocked_eases")
    if isinstance(raw, list):
        blocked = [int(x) for x in raw if str(x).strip() and str(x).isdigit() and 1 <= int(x) <= 4]
    else:
        blocked = [1]
    if not blocked:
        blocked = [1]
    return {"audio_field_names": names, "blocked_eases": blocked}


def _card_has_audio_fields(card) -> bool:
    cfg = _get_config()
    names = cfg.get("audio_field_names") or []
    if not names:
        return True
    note = card.note()
    model = note.note_type()
    field_names = [f["name"] for f in model["flds"]]
    for name in names:
        if name in field_names and (note[name] or "").strip():
            return True
    return False


def _try_enable_again() -> None:
    if not _state["pending"] or not _state["av_done"] or not _state["card_done"]:
        return
    _state["pending"] = False
    rev = getattr(mw, "reviewer", None)
    if rev is not None and getattr(rev, "bottom", None) is not None:
        eases = _get_config().get("blocked_eases") or [1]
        rev.bottom.web.eval(_js_enable_buttons(eases))


def _on_reviewer_did_show_answer(card) -> None:
    if not _card_has_audio_fields(card):
        return
    rev = getattr(mw, "reviewer", None)
    if rev is None or getattr(rev, "bottom", None) is None:
        return

    # Always track: for no-audio cards the injected script notifies immediately.
    has_av = bool(card.answer_av_tags())
    _state["pending"] = True
    _state["av_done"] = not has_av
    _state["card_done"] = False

    blocked_eases = _get_config().get("blocked_eases") or [1]

    def _do_disable() -> None:
        if not _state["pending"]:
            return
        r = getattr(mw, "reviewer", None)
        if r is not None and getattr(r, "bottom", None) is not None:
            r.bottom.web.eval(_js_disable_buttons(blocked_eases))

    mw.progress.single_shot(_DISABLE_DELAY_MS, _do_disable)


def _on_av_player_did_end_playing(*args) -> None:
    if not _state["pending"]:
        return
    if not av_player.queue_is_empty():
        return
    rev = getattr(mw, "reviewer", None)
    if rev is None or getattr(mw, "state", None) != "review":
        return
    if getattr(rev, "state", None) != "answer":
        return
    _state["av_done"] = True
    _try_enable_again()


def _on_js_message(handled, message: str, context) -> tuple[bool, None]:
    if message != _MSG:
        return handled
    # Message from our injected card script; re-enable when both av and card audio are done.
    _state["card_done"] = True
    _try_enable_again()
    return (True, None)


def _on_card_will_show(html: str, card, context: str) -> str:
    if context != "reviewAnswer":
        return html
    return html + _CARD_AUDIO_SCRIPT


def _on_reviewer_will_answer_card(proceed_and_ease, reviewer, card) -> tuple[bool, int]:
    proceed, ease = proceed_and_ease
    blocked = _get_config().get("blocked_eases") or [1]
    if ease in blocked and _state["pending"]:
        tooltip("Finish listening to audio before using that shortcut.")
        return (False, ease)
    return (proceed, ease)


def _on_reviewer_did_show_question(card) -> None:
    # Reset so the next answer doesn't reuse stale state.
    _state["pending"] = False
    _state["av_done"] = False
    _state["card_done"] = False


def _on_reviewer_will_end() -> None:
    _state["pending"] = False
    _state["av_done"] = False
    _state["card_done"] = False


def _open_config() -> None:
    cfg = _get_config()
    names_list = cfg.get("audio_field_names") or []
    names_text = "\n".join(names_list)
    blocked_eases = cfg.get("blocked_eases") or [1]

    d = QDialog(mw)
    d.setWindowTitle("Disable Again Until Audio — Config")
    layout = QVBoxLayout(d)

    # Blocked keys (ease buttons / keyboard shortcuts)
    key_group = QGroupBox("Block these answer keys until audio ends")
    key_layout = QVBoxLayout(key_group)
    key_help = QLabel(
        "Check each key you want disabled while audio is playing. "
        "Useful if your \"Again\" (fail) shortcut is not 1, or to block multiple keys."
    )
    key_help.setWordWrap(True)
    key_layout.addWidget(key_help)
    cb_again = QCheckBox("Again (ease 1)")
    cb_hard = QCheckBox("Hard (ease 2)")
    cb_good = QCheckBox("Good (ease 3)")
    cb_easy = QCheckBox("Easy (ease 4)")
    cb_again.setChecked(1 in blocked_eases)
    cb_hard.setChecked(2 in blocked_eases)
    cb_good.setChecked(3 in blocked_eases)
    cb_easy.setChecked(4 in blocked_eases)
    key_layout.addWidget(cb_again)
    key_layout.addWidget(cb_hard)
    key_layout.addWidget(cb_good)
    key_layout.addWidget(cb_easy)
    layout.addWidget(key_group)

    # Audio fields
    layout.addWidget(
        QLabel(
            "Audio field names (one per line). Only cards that have at least one of these fields with content will have the selected buttons disabled until audio ends."
        )
    )
    layout.addWidget(
        QLabel("Leave empty to apply to all cards with any audio on the answer side.")
    )
    te = QPlainTextEdit()
    te.setPlaceholderText("e.g.:\nWord Audio\nSentence Audio")
    te.setPlainText(names_text)
    te.setMinimumHeight(120)
    layout.addWidget(te)

    apply_all = QCheckBox("Apply to all cards (ignore field list)")
    apply_all.setChecked(len(names_list) == 0)
    layout.addWidget(apply_all)

    bb = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
    )
    bb.accepted.connect(d.accept)
    bb.rejected.connect(d.reject)
    layout.addWidget(bb)

    if d.exec():
        new_blocked = []
        if cb_again.isChecked():
            new_blocked.append(1)
        if cb_hard.isChecked():
            new_blocked.append(2)
        if cb_good.isChecked():
            new_blocked.append(3)
        if cb_easy.isChecked():
            new_blocked.append(4)
        if not new_blocked:
            new_blocked = [1]
        if apply_all.isChecked():
            new_names = []
        else:
            new_names = [
                s.strip()
                for s in te.toPlainText().replace(",", "\n").splitlines()
                if s.strip()
            ]
        mw.addonManager.writeConfig(
            __name__,
            {"audio_field_names": new_names, "blocked_eases": new_blocked},
        )


# Register hooks
gui_hooks.reviewer_did_show_answer.append(_on_reviewer_did_show_answer)
gui_hooks.reviewer_did_show_question.append(_on_reviewer_did_show_question)
gui_hooks.reviewer_will_end.append(_on_reviewer_will_end)
gui_hooks.reviewer_will_answer_card.append(_on_reviewer_will_answer_card)
gui_hooks.av_player_did_end_playing.append(_on_av_player_did_end_playing)
gui_hooks.webview_did_receive_js_message.append(_on_js_message)
gui_hooks.card_will_show.append(_on_card_will_show)

mw.addonManager.setConfigAction(__name__, _open_config)
