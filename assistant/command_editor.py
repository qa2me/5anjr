import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk, GLib
import json
import os

COMMANDS_FILE = os.path.join(os.path.dirname(__file__), "user_commands.json")


def _load():
    if not os.path.exists(COMMANDS_FILE):
        return []
    try:
        with open(COMMANDS_FILE) as f:
            return json.load(f)
    except Exception:
        return []


def _save(commands):
    with open(COMMANDS_FILE, "w") as f:
        json.dump(commands, f, indent=2)


class CommandEditor:
    def __init__(self):
        self._window = None

    def open(self, parent=None):
        if self._window:
            self._window.present()
            return
        self._build_window(parent)

    def _build_window(self, parent):
        self._window = Gtk.Window.new(Gtk.WindowType.TOPLEVEL)
        self._window.set_title("Command Editor")
        self._window.set_default_size(640, 420)
        self._window.set_position(Gtk.WindowPosition.CENTER)
        self._window.set_keep_above(False)
        if parent:
            self._window.set_transient_for(parent)
        self._window.connect("destroy", self._on_destroy)

        css = b"""
        .editor-box { background: rgba(20, 20, 25, 0.95); }
        .editor-header { color: #fff; font-size: 14px; font-weight: bold; }
        """
        provider = Gtk.CssProvider()
        provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            self._window.get_screen(), provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vbox.set_margin_start(12)
        vbox.set_margin_end(12)
        vbox.set_margin_top(12)
        vbox.set_margin_bottom(12)

        header = Gtk.Label(label="My Custom Commands")
        header.get_style_context().add_class("editor-header")
        header.set_halign(Gtk.Align.START)
        vbox.pack_start(header, False, False, 0)

        hint = Gtk.Label(label="Add commands by voice or action. No coding needed.")
        hint.set_halign(Gtk.Align.START)
        hint.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.6, 0.6, 0.6, 1))
        vbox.pack_start(hint, False, False, 0)

        vbox.pack_start(Gtk.Separator(), False, False, 4)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        self._store = Gtk.ListStore(str, str, str, int)
        self._refresh_store()

        self._tree = Gtk.TreeView(model=self._store)
        self._tree.set_rules_hint(True)

        rend_text = Gtk.CellRendererText()
        col_keywords = Gtk.TreeViewColumn("Say this...", rend_text, text=0)
        col_keywords.set_resizable(True)
        col_keywords.set_min_width(180)
        self._tree.append_column(col_keywords)

        col_action = Gtk.TreeViewColumn("Action", rend_text, text=1)
        col_action.set_resizable(True)
        self._tree.append_column(col_action)

        col_value = Gtk.TreeViewColumn("Details", rend_text, text=2)
        col_value.set_resizable(True)
        col_value.set_expand(True)
        self._tree.append_column(col_value)

        scrolled.add(self._tree)
        vbox.pack_start(scrolled, True, True, 0)

        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        btn_box.set_halign(Gtk.Align.END)

        add_btn = Gtk.Button.new_with_label("+ Add Command")
        add_btn.connect("clicked", self._on_add)
        btn_box.pack_start(add_btn, False, False, 0)

        edit_btn = Gtk.Button.new_with_label("Edit")
        edit_btn.connect("clicked", self._on_edit)
        btn_box.pack_start(edit_btn, False, False, 0)

        del_btn = Gtk.Button.new_with_label("Delete")
        del_btn.connect("clicked", self._on_delete)
        btn_box.pack_start(del_btn, False, False, 0)

        vbox.pack_start(btn_box, False, False, 0)

        self._window.add(vbox)
        self._window.show_all()

    def _refresh_store(self):
        self._store.clear()
        for cmd in _load():
            keywords = ", ".join(cmd.get("keywords", []))
            actions = cmd.get("actions", [])
            if actions:
                a = actions[0]
                atype = {"app": "Open App", "url": "Open URL", "speak": "Speak",
                         "shell": "Run Command", "app+url": "App + URL"}.get(a.get("type", ""), a.get("type", ""))
                aval = a.get("value", "")
                if a.get("type") == "app+url" and a.get("url"):
                    aval = f"{aval} + {a['url']}"
            else:
                atype = ""
                aval = ""
            self._store.append([keywords, atype, aval, cmd.get("id", 0)])

    def _on_add(self, btn):
        dialog = CommandDialog(self._window)
        dialog.run()
        self._refresh_store()

    def _on_edit(self, btn):
        sel = self._tree.get_selection()
        model, it = sel.get_selected()
        if it is None:
            return
        cmd_id = model[it][3]
        commands = _load()
        for cmd in commands:
            if cmd.get("id") == cmd_id:
                dialog = CommandDialog(self._window, cmd)
                dialog.run()
                break
        self._refresh_store()

    def _on_delete(self, btn):
        sel = self._tree.get_selection()
        model, it = sel.get_selected()
        if it is None:
            return
        cmd_id = model[it][3]
        commands = _load()
        commands = [c for c in commands if c.get("id") != cmd_id]
        _save(commands)
        self._refresh_store()

    def _on_destroy(self, *args):
        self._window = None


class CommandDialog:
    def __init__(self, parent, existing=None):
        self._existing = existing
        self._actions_list = []

        self._dialog = Gtk.Dialog(
            title="Edit Command" if existing else "Add Command",
            transient_for=parent,
            modal=True,
        )
        self._dialog.set_default_size(480, 350)
        self._dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        self._dialog.add_button("Save", Gtk.ResponseType.OK)

        box = self._dialog.get_content_area()
        box.set_spacing(8)
        box.set_margin_start(12)
        box.set_margin_end(12)
        box.set_margin_top(12)
        box.set_margin_bottom(12)

        # Keywords
        box.pack_start(Gtk.Label(label="When I say..."), False, False, 0)
        self._keywords_entry = Gtk.Entry()
        self._keywords_entry.set_placeholder_text("open codeforces, launch codeforces")
        box.pack_start(self._keywords_entry, False, False, 0)
        kw_hint = Gtk.Label(label="Separate phrases with commas")
        kw_hint.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.6, 0.6, 0.6, 1))
        kw_hint.set_halign(Gtk.Align.START)
        box.pack_start(kw_hint, False, False, 0)

        box.pack_start(Gtk.Separator(), False, False, 4)

        # Actions section
        action_header = Gtk.Label(label="Do this (1 action per row):")
        action_header.set_halign(Gtk.Align.START)
        box.pack_start(action_header, False, False, 0)

        self._actions_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        box.pack_start(self._actions_box, True, True, 0)

        add_action_btn = Gtk.Button.new_with_label("+ Add Action")
        add_action_btn.connect("clicked", self._on_add_action)
        box.pack_start(add_action_btn, False, False, 0)

        preview_label = Gtk.Label()
        preview_label.set_markup("<i>Tip: add multiple actions to chain them (e.g. open app + open URL)</i>")
        preview_label.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.5, 0.5, 0.5, 1))
        box.pack_start(preview_label, False, False, 0)

        if existing:
            self._keywords_entry.set_text(", ".join(existing.get("keywords", [])))
            for action in existing.get("actions", []):
                self._add_action_row(action)

        self._dialog.show_all()

    def _add_action_row(self, action_data=None):
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)

        type_combo = Gtk.ComboBoxText()
        type_combo.append("app", "Open App")
        type_combo.append("url", "Open URL")
        type_combo.append("speak", "Speak Response")
        type_combo.append("shell", "Run Command")
        type_combo.append("app+url", "App + URL")
        type_combo.set_active(0)
        hbox.pack_start(type_combo, False, False, 0)

        value_entry = Gtk.Entry()
        value_entry.set_placeholder_text("firefox / https://example.com / your message")
        value_entry.set_hexpand(True)
        hbox.pack_start(value_entry, True, True, 0)

        # Extra URL field for app+url type
        url_entry = Gtk.Entry()
        url_entry.set_placeholder_text("URL to open (for App+URL)")
        url_entry.set_no_show_all(True)
        hbox.pack_start(url_entry, False, False, 0)

        def on_type_change(cb):
            active = cb.get_active_id()
            if active == "app+url":
                url_entry.show()
            else:
                url_entry.hide()

        type_combo.connect("changed", on_type_change)

        remove_btn = Gtk.Button.new_with_label("X")
        remove_btn.connect("clicked", lambda btn: (hbox.destroy(), None))
        hbox.pack_start(remove_btn, False, False, 0)

        if action_data:
            atype = action_data.get("type", "")
            type_map = {"app": "0", "url": "1", "speak": "2", "shell": "3", "app+url": "4"}
            type_combo.set_active_id(atype)
            value_entry.set_text(action_data.get("value", ""))
            if atype == "app+url" and action_data.get("url"):
                url_entry.set_text(action_data["url"])
                url_entry.show()

        self._actions_box.pack_start(hbox, False, False, 0)
        hbox.show_all()

    def _on_add_action(self, btn):
        self._add_action_row()

    def run(self):
        response = self._dialog.run()
        if response == Gtk.ResponseType.OK:
            self._save()
        self._dialog.destroy()

    def _save(self):
        keywords_text = self._keywords_entry.get_text().strip()
        if not keywords_text:
            return
        keywords = [k.strip().lower() for k in keywords_text.split(",") if k.strip()]

        actions = []
        for child in self._actions_box.get_children():
            widgets = child.get_children()
            if len(widgets) < 3:
                continue
            type_combo = widgets[0]
            value_entry = widgets[1]
            atype = type_combo.get_active_id()
            avalue = value_entry.get_text().strip()
            if not avalue:
                continue
            action = {"type": atype, "value": avalue}
            if atype == "app+url" and len(widgets) > 3:
                url_entry = widgets[2]
                url = url_entry.get_text().strip()
                if url:
                    action["url"] = url
            actions.append(action)

        if not keywords or not actions:
            return

        commands = _load()
        if self._existing:
            cmd_id = self._existing.get("id", 0)
            for cmd in commands:
                if cmd.get("id") == cmd_id:
                    cmd["keywords"] = keywords
                    cmd["actions"] = actions
                    break
        else:
            new_id = max([c.get("id", 0) for c in commands], default=0) + 1
            commands.append({"id": new_id, "keywords": keywords, "actions": actions})
        _save(commands)


def open_editor(parent=None):
    editor = CommandEditor()
    editor.open(parent)
