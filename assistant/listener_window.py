import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Pango
import math
import threading


class ListenerWindow:
    def __init__(self, speaker, recognizer, on_text_callback, on_edit_commands=None):
        self.speaker = speaker
        self.recognizer = recognizer
        self.on_text = on_text_callback
        self.on_edit_commands = on_edit_commands
        self._pulse = 0.0
        self._pulse_dir = 1
        self._done = False

        self._build_window()

    def _build_window(self):
        self.window = Gtk.Window.new(Gtk.WindowType.POPUP)
        self.window.set_default_size(480, 230)
        self.window.set_position(Gtk.WindowPosition.CENTER)
        self.window.set_decorated(False)
        self.window.set_keep_above(True)
        self.window.set_skip_taskbar_hint(True)
        self.window.set_app_paintable(True)
        visual = self.window.get_screen().get_rgba_visual()
        if visual:
            self.window.set_visual(visual)

        css = b"""
        .listener-box { background: rgba(20, 20, 25, 0.92); border-radius: 24px; }
        .listener-entry {
            background: rgba(255, 255, 255, 0.07);
            color: #ffffff;
            border-radius: 12px;
            padding: 10px 18px;
            font-size: 16px;
            caret-color: #5b9aff;
            border: 1px solid rgba(255, 255, 255, 0.06);
        }
        .listener-entry:focus { border-color: rgba(91, 154, 255, 0.3); }
        .hint-label {
            color: rgba(255, 255, 255, 0.35);
            font-size: 12px;
        }
        .cmd-btn {
            background: rgba(255, 255, 255, 0.08);
            color: #ffffff;
            border-radius: 8px;
            padding: 4px 10px;
            font-size: 13px;
            border: 1px solid rgba(255, 255, 255, 0.08);
        }
        .cmd-btn:hover { background: rgba(255, 255, 255, 0.18); }
        """
        provider = Gtk.CssProvider()
        provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            self.window.get_screen(), provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        main_box.get_style_context().add_class("listener-box")

        self.draw_area = Gtk.DrawingArea()
        self.draw_area.set_size_request(480, 130)
        self.draw_area.connect("draw", self._on_draw)

        overlay = Gtk.Overlay()
        overlay.add(self.draw_area)

        mic_hint = Gtk.Label(label="Listening...")
        mic_hint.get_style_context().add_class("hint-label")
        overlay.add_overlay(mic_hint)
        overlay.set_overlay_pass_through(mic_hint, True)

        main_box.pack_start(overlay, True, True, 0)

        entry_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        entry_box.set_margin_start(24)
        entry_box.set_margin_end(24)
        entry_box.set_margin_bottom(20)

        self.entry = Gtk.Entry()
        self.entry.get_style_context().add_class("listener-entry")
        self.entry.set_placeholder_text("Type your command or speak...")
        self.entry.connect("activate", self._on_enter)
        entry_box.pack_start(self.entry, True, True, 0)

        cmd_btn = Gtk.Button.new_with_label("+ Cmd")
        cmd_btn.set_tooltip_text("Add or edit custom commands")
        cmd_btn.get_style_context().add_class("cmd-btn")
        cmd_btn.connect("clicked", lambda btn: self._on_edit_commands())
        entry_box.pack_start(cmd_btn, False, False, 6)

        main_box.pack_start(entry_box, False, False, 0)

        self.window.add(main_box)

        self.window.connect("key-press-event", self._on_key_press)
        self.window.connect("destroy", self._on_destroy)

        GLib.timeout_add(30, self._tick)

    def _on_draw(self, widget, cr):
        width = widget.get_allocated_width()
        height = widget.get_allocated_height()
        cx, cy = width / 2, height / 2 + 8

        pulse_r = 55 + self._pulse * 18

        for i in range(5):
            radius = pulse_r + i * 16
            alpha = 0.07 - i * 0.013
            if alpha <= 0:
                break
            cr.set_source_rgba(0.3, 0.6, 1.0, alpha)
            cr.arc(cx, cy, radius, 0, 2 * math.pi)
            cr.fill()

        cr.set_source_rgba(0.35, 0.65, 1.0, 0.12)
        cr.arc(cx, cy, pulse_r, 0, 2 * math.pi)
        cr.fill()

        cr.set_source_rgba(0.5, 0.78, 1.0, 0.5)
        cr.arc(cx, cy, 3.5, 0, 2 * math.pi)
        cr.fill()

        return False

    def _tick(self):
        if self._done:
            return False
        self._pulse += 0.025 * self._pulse_dir
        if self._pulse > 1.0:
            self._pulse_dir = -1
        elif self._pulse < 0.0:
            self._pulse_dir = 1
        self.draw_area.queue_draw()
        return True

    def _on_enter(self, entry):
        text = entry.get_text().strip()
        self._finish(text)

    def _on_key_press(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            self._finish("")
            return True
        return False

    def _on_destroy(self, *args):
        self._finish("")

    def _finish(self, text):
        if self._done:
            return
        self._done = True
        cb = self.on_text
        self.window.destroy()
        if cb:
            cb(text)

    def present(self):
        self.window.show_all()
        self.entry.grab_focus()

        def _listen():
            text = self.recognizer.listen()
            if text and not self._done:
                GLib.idle_add(self._on_voice, text)

        threading.Thread(target=_listen, daemon=True).start()

    def _on_voice(self, text):
        if self._done:
            return
        current = self.entry.get_text().strip()
        if current and current != self.entry.get_placeholder_text():
            return
        self.entry.set_text(text)
        self.entry.grab_focus()
        self.entry.set_position(-1)

    def _on_edit_commands(self):
        if self.on_edit_commands:
            self.on_edit_commands()
