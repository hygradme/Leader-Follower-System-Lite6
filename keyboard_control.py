# ======================================================================
# ファイル名：keyboard_control.py
# （Windows 環境を想定し、keyboard モジュールを使ったグローバルキー検知）
# ======================================================================

import sys

# Windows であれば keyboard モジュールを使う実装
if sys.platform.startswith("win"):
    import keyboard   # pip install keyboard が必要
    import queue

    # キー押下イベントを内部キューに蓄積するためのキュー
    _event_queue = queue.Queue()

    # キー押下時のコールバック：押されたキー名 (event.name) をキューに入れる
    def _on_press_callback(event):
        # event.name は "a", "b", "space", "enter" などの文字列
        # 下位レベルの OS イベントなので、必ず小文字で来るわけではないが
        # keyboard モジュールは大文字と小文字を区別しないため、このままで OK
        _event_queue.put(event.name)

    # プログラム起動時に一度だけキーフックを登録
    keyboard.on_press(_on_press_callback)

    def getch_nonblocking():
        """
        キューに溜まっているキーイベントを一つ取り出して返す。
        何もなければ None を返す。
        返り値は常に文字列 (str) で "a", "b", "space", "enter" など。
        """
        try:
            key = _event_queue.get_nowait()
            return key
        except queue.Empty:
            return None

    def cleanup_console():
        """
        プログラム終了時にキーフックを解除し、リソースを解放する。
        """
        keyboard.unhook_all()

else:
    # Windows 以外（Linux/macOS）では、従来の stdin からの非ブロッキング読み取りにフォールバック
    import select
    import tty
    import termios

    _orig_term_attrs = None

    def _enter_raw_mode():
        global _orig_term_attrs
        fd = sys.stdin.fileno()
        _orig_term_attrs = termios.tcgetattr(fd)
        tty.setcbreak(fd)

    def _exit_raw_mode():
        global _orig_term_attrs
        fd = sys.stdin.fileno()
        if _orig_term_attrs is not None:
            termios.tcsetattr(fd, termios.TCSADRAIN, _orig_term_attrs)

    # ファイルがインポートされた段階で raw モードに切り替える
    _enter_raw_mode()

    def getch_nonblocking():
        """
        stdin がキーダウン状態なら 1 文字読み取って返し、
        なければ None を返す。Linux/macOS フォーカスが必要。
        """
        dr, _, _ = select.select([sys.stdin], [], [], 0)
        if dr:
            ch = sys.stdin.read(1)
            return ch.lower()
        return None

    def cleanup_console():
        _exit_raw_mode()
