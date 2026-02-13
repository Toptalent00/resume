import threading
import time
import tkinter as tk
from tkinter import messagebox, ttk

try:
    from pynput import keyboard as pynput_keyboard
except ImportError as exc:
    raise SystemExit("Missing dependency: pip install pynput") from exc


START_HOTKEY = "<ctrl>+<alt>+<shift>+s"
STOP_HOTKEY = "<ctrl>+<shift>+q"
NEWLINE_MODES = ("Enter", "Shift+Enter", "Ctrl+Enter")


class TypeProgramApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Type Program")
        self.root.geometry("720x520")
        self.root.minsize(520, 420)

        self.text_box = tk.Text(root, wrap="word", height=12)
        self.delay_var = tk.StringVar(value="0.0")
        self.interval_var = tk.StringVar(value="0.02")
        self.status_var = tk.StringVar(value="Idle")
        self.tab_to_spaces_var = tk.BooleanVar(value=True)
        self.tab_width_var = tk.StringVar(value="4")
        self.newline_mode_var = tk.StringVar(value=NEWLINE_MODES[0])
        self.stop_event = threading.Event()
        self.typing_thread = None
        self.hotkey_listener = None
        self.is_hidden = False

        self._build_ui()
        self._start_hotkey_listener()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build_ui(self) -> None:
        padding = {"padx": 12, "pady": 10}

        info = ttk.Label(
            self.root,
            text=(
                "Paste the text below. Focus the target window, then press "
                "Ctrl+Alt+Shift+S to start or Ctrl+Shift+Q to stop typing."
            ),
            wraplength=680,
        )
        info.grid(row=0, column=0, columnspan=3, sticky="w", **padding)

        text_frame = ttk.Frame(self.root)
        text_frame.grid(row=1, column=0, columnspan=3, sticky="nsew", **padding)
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        text_frame.grid_rowconfigure(0, weight=1)
        text_frame.grid_columnconfigure(0, weight=1)

        text_scroll = ttk.Scrollbar(text_frame, orient="vertical")
        text_scroll.grid(row=0, column=1, sticky="ns")
        self.text_box.grid(row=0, column=0, sticky="nsew")
        self.text_box.config(yscrollcommand=text_scroll.set)
        text_scroll.config(command=self.text_box.yview)

        options = ttk.Frame(self.root)
        options.grid(row=2, column=0, columnspan=3, sticky="ew", **padding)
        options.grid_columnconfigure(0, weight=1)
        options.grid_columnconfigure(1, weight=1)
        options.grid_columnconfigure(2, weight=1)
        options.grid_columnconfigure(3, weight=1)

        ttk.Label(options, text="Start delay (sec)").grid(row=0, column=0, sticky="w")
        ttk.Entry(options, textvariable=self.delay_var, width=8).grid(
            row=0, column=1, sticky="w", padx=(6, 24)
        )
        ttk.Label(options, text="Interval (sec)").grid(row=0, column=2, sticky="w")
        ttk.Entry(options, textvariable=self.interval_var, width=8).grid(
            row=0, column=3, sticky="w"
        )

        formatting = ttk.Frame(self.root)
        formatting.grid(row=3, column=0, columnspan=3, sticky="ew", **padding)
        formatting.grid_columnconfigure(0, weight=1)
        formatting.grid_columnconfigure(1, weight=1)
        formatting.grid_columnconfigure(2, weight=1)
        formatting.grid_columnconfigure(3, weight=1)

        ttk.Checkbutton(
            formatting,
            text="Convert tabs to spaces",
            variable=self.tab_to_spaces_var,
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(formatting, text="Tab width").grid(row=0, column=1, sticky="w")
        ttk.Entry(formatting, textvariable=self.tab_width_var, width=6).grid(
            row=0, column=2, sticky="w", padx=(6, 24)
        )
        ttk.Label(formatting, text="New line").grid(row=0, column=3, sticky="w")
        ttk.Combobox(
            formatting,
            textvariable=self.newline_mode_var,
            values=NEWLINE_MODES,
            width=12,
            state="readonly",
        ).grid(row=0, column=4, sticky="w")

        buttons = ttk.Frame(self.root)
        buttons.grid(row=4, column=0, columnspan=3, sticky="ew", **padding)

        ttk.Button(
            buttons,
            text="Start (Ctrl+Alt+Shift+S)",
            command=self.start_typing,
        ).grid(row=0, column=0, padx=(0, 8))
        ttk.Button(
            buttons,
            text="Stop (Ctrl+Shift+Q)",
            command=self.stop_typing,
        ).grid(row=0, column=1)

        status_frame = ttk.Frame(self.root)
        status_frame.grid(row=5, column=0, columnspan=3, sticky="ew", **padding)
        ttk.Label(status_frame, text="Status:").grid(row=0, column=0, sticky="w")
        ttk.Label(status_frame, textvariable=self.status_var).grid(
            row=0, column=1, sticky="w", padx=(6, 0)
        )

        ttk.Label(
            self.root,
            text="Hotkeys: Ctrl+Alt+Shift+S start, Ctrl+Shift+Q stop (global)",
        ).grid(row=6, column=0, columnspan=3, sticky="w", **padding)

    def _start_hotkey_listener(self) -> None:
        self.hotkey_listener = pynput_keyboard.GlobalHotKeys(
            {
                START_HOTKEY: self._on_start_hotkey,
                STOP_HOTKEY: self._on_stop_hotkey,
            }
        )
        self.hotkey_listener.start()

    def _on_start_hotkey(self) -> None:
        self.root.after(0, self.start_typing)

    def _on_stop_hotkey(self) -> None:
        self.root.after(0, self.stop_typing)

    def _parse_float(self, value: str, default: float) -> float:
        try:
            return float(value)
        except ValueError:
            return default

    def _parse_int(self, value: str, default: int) -> int:
        try:
            return int(value)
        except ValueError:
            return default

    def _hide_window(self) -> None:
        if not self.is_hidden:
            self.root.withdraw()
            self.is_hidden = True

    def _show_window(self) -> None:
        if self.is_hidden:
            self.root.deiconify()
            self.is_hidden = False

    def _normalize_text(self, text: str, tab_to_spaces: bool, tab_width: int) -> str:
        normalized = text.replace("\r\n", "\n").replace("\r", "\n")
        if tab_to_spaces:
            normalized = normalized.replace("\t", " " * tab_width)
        return normalized

    def _tap_key(
        self,
        controller: pynput_keyboard.Controller,
        key: pynput_keyboard.Key,
        modifiers: tuple[pynput_keyboard.Key, ...] = (),
    ) -> None:
        for modifier in modifiers:
            controller.press(modifier)
        controller.press(key)
        controller.release(key)
        for modifier in reversed(modifiers):
            controller.release(modifier)

    def _send_newline(
        self,
        controller: pynput_keyboard.Controller,
        newline_mode: str,
    ) -> None:
        if newline_mode == "Shift+Enter":
            modifiers = (pynput_keyboard.Key.shift,)
        elif newline_mode == "Ctrl+Enter":
            modifiers = (pynput_keyboard.Key.ctrl,)
        else:
            modifiers = ()
        self._tap_key(controller, pynput_keyboard.Key.enter, modifiers)

    def start_typing(self) -> None:
        text = self.text_box.get("1.0", "end-1c")
        if not text.strip():
            messagebox.showwarning("No text", "Please enter text to type.")
            return

        delay = self._parse_float(self.delay_var.get(), 0.0)
        interval = self._parse_float(self.interval_var.get(), 0.02)
        self.delay_var.set(f"{delay:g}")
        self.interval_var.set(f"{interval:g}")

        tab_width = self._parse_int(self.tab_width_var.get(), 4)
        if tab_width < 1:
            tab_width = 4
        self.tab_width_var.set(str(tab_width))

        newline_mode = self.newline_mode_var.get().strip()
        if newline_mode not in NEWLINE_MODES:
            newline_mode = NEWLINE_MODES[0]
            self.newline_mode_var.set(newline_mode)

        text = self._normalize_text(text, self.tab_to_spaces_var.get(), tab_width)

        if self.typing_thread and self.typing_thread.is_alive():
            return

        self.stop_event.clear()
        self.status_var.set("Typing...")
        self.typing_thread = threading.Thread(
            target=self._type_worker,
            args=(text, delay, interval, newline_mode),
            daemon=True,
        )
        self.typing_thread.start()
        self._hide_window()

    def stop_typing(self) -> None:
        if self.typing_thread and self.typing_thread.is_alive():
            self.stop_event.set()
            self.status_var.set("Stopping...")
            self._show_window()

    def _sleep_with_cancel(self, seconds: float) -> bool:
        end_time = time.time() + seconds
        while time.time() < end_time:
            if self.stop_event.is_set():
                return False
            time.sleep(0.05)
        return True

    def _type_worker(
        self,
        text: str,
        delay: float,
        interval: float,
        newline_mode: str,
    ) -> None:
        if delay > 0:
            if not self._sleep_with_cancel(delay):
                self.root.after(0, self._typing_finished)
                return

        controller = pynput_keyboard.Controller()
        for char in text:
            if self.stop_event.is_set():
                break
            if char == "\n":
                self._send_newline(controller, newline_mode)
            elif char == "\t":
                self._tap_key(controller, pynput_keyboard.Key.tab)
            else:
                controller.type(char)
            if interval > 0:
                time.sleep(interval)

        self.root.after(0, self._typing_finished)

    def _typing_finished(self) -> None:
        self._show_window()
        if self.stop_event.is_set():
            self.status_var.set("Stopped")
        else:
            self.status_var.set("Done")

    def on_close(self) -> None:
        self.stop_event.set()
        if self.hotkey_listener:
            self.hotkey_listener.stop()
        self.root.destroy()


def main() -> None:
    root = tk.Tk()
    app = TypeProgramApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
