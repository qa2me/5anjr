import gi
gi.require_version("Gtk", "3.0")
gi.require_version("AyatanaAppIndicator3", "0.1")
from gi.repository import Gtk, AyatanaAppIndicator3, GLib
import signal


class AppIndicator:
    def __init__(self, app_name, on_quit, on_toggle, hotkey_info="", timer_manager=None):
        self.app_name = app_name
        self.on_quit = on_quit
        self.on_toggle = on_toggle
        self.hotkey_info = hotkey_info
        self.timer_manager = timer_manager

        self.indicator = AyatanaAppIndicator3.Indicator.new(
            app_name,
            "audio-input-microphone",
            AyatanaAppIndicator3.IndicatorCategory.APPLICATION_STATUS,
        )
        self.indicator.set_status(AyatanaAppIndicator3.IndicatorStatus.ACTIVE)

        self._build_menu()
        GLib.timeout_add(2000, self._refresh_timers)

    def _build_menu(self):
        menu = Gtk.Menu()

        status = Gtk.MenuItem(label="Voice Assistant Active")
        status.set_sensitive(False)
        menu.append(status)

        if self.hotkey_info:
            hotkey_item = Gtk.MenuItem(label=self.hotkey_info)
            hotkey_item.set_sensitive(False)
            menu.append(hotkey_item)

        if self.timer_manager:
            summary = self.timer_manager.get_summary()
            if summary:
                menu.append(Gtk.SeparatorMenuItem())
                for line in summary.split("\n"):
                    item = Gtk.MenuItem(label=line)
                    item.set_sensitive(False)
                    menu.append(item)

        menu.append(Gtk.SeparatorMenuItem())

        toggle_label = "Open listener" if self.timer_manager else "Listening for 'hey linux'"
        item_toggle = Gtk.MenuItem(label=toggle_label)
        item_toggle.connect("activate", lambda _: self.on_toggle())
        menu.append(item_toggle)

        menu.append(Gtk.SeparatorMenuItem())

        item_quit = Gtk.MenuItem(label="Quit")
        item_quit.connect("activate", lambda _: self.on_quit())
        menu.append(item_quit)

        menu.show_all()
        self.indicator.set_menu(menu)

    def _refresh_timers(self):
        if self.timer_manager:
            self._build_menu()
        return True

    def run(self):
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        Gtk.main()

    def quit(self):
        Gtk.main_quit()
