import os
import re
import importlib.util
import inspect
import logging


PLUGINS_DIR = os.path.join(os.path.dirname(__file__), "plugins")


class PluginAPI:
    def __init__(self, speaker, timers, app_context):
        self.speaker = speaker
        self.timers = timers
        self.app = app_context
        self._keyword_handlers = []
        self._regex_handlers = []

    def on_keywords(self, keywords):
        def decorator(func):
            self._keyword_handlers.append({"keywords": keywords, "func": func})
            return func
        return decorator

    def on_regex(self, pattern):
        def decorator(func):
            compiled = re.compile(pattern, re.IGNORECASE)
            self._regex_handlers.append({"pattern": compiled, "func": func})
            return func
        return decorator

    def run_keyword_handlers(self, text):
        for h in self._keyword_handlers:
            for kw in h["keywords"]:
                if kw in text:
                    result = h["func"](text, self.speaker, self.timers)
                    if result:
                        return True
        return False

    def run_regex_handlers(self, text):
        for h in self._regex_handlers:
            m = h["pattern"].search(text)
            if m:
                result = h["func"](text, self.speaker, self.timers, m)
                if result:
                    return True
        return False


def _load_module(fpath, mod_name):
    spec = importlib.util.spec_from_file_location(mod_name, fpath)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def discover_plugins():
    plugins = []
    if not os.path.isdir(PLUGINS_DIR):
        return plugins
    for fname in sorted(os.listdir(PLUGINS_DIR)):
        if fname == "__init__.py" or not fname.endswith(".py"):
            continue
        mod_path = os.path.join(PLUGINS_DIR, fname)
        mod_name = f"assistant.plugins.{fname[:-3]}"
        try:
            mod = _load_module(mod_path, mod_name)
            plugins.append((fname, mod))
        except Exception as e:
            logging.warning(f"Failed to load plugin {fname}: {e}")
    return plugins


def register_plugins(speaker, timers, app_context):
    api = PluginAPI(speaker, timers, app_context)
    plugins = discover_plugins()
    for fname, mod in plugins:
        try:
            if hasattr(mod, "setup"):
                mod.setup(api)
            if hasattr(mod, "PATTERNS") and hasattr(mod, "handle"):
                kw = mod.PATTERNS if isinstance(mod.PATTERNS, list) else [mod.PATTERNS]
                api._keyword_handlers.append({
                    "keywords": kw,
                    "func": lambda t, sp, tm, h=mod.handle: h(t, sp, tm),
                })
        except Exception as e:
            logging.warning(f"Failed to register plugin {fname}: {e}")
    return api
