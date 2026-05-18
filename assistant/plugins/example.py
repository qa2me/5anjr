"""
Example custom command plugin.

Two ways to add commands:

METHOD 1 - Simple keyword matching:
  Define PATTERNS (list of keywords) and handle(text, speaker, timers).
  Return True if you handled the command.

METHOD 2 - Decorator API (more powerful):
  Define setup(api) and use @api.on_keywords() or @api.on_regex().
  on_keywords: fires when any keyword is in the spoken text.
  on_regex: fires when the regex pattern matches.
"""


PATTERNS = ["hello", "hi", "hey", "howdy"]


def handle(text, speaker, timers):
    speaker.say("Hello! Custom plugin working.")
    return True
