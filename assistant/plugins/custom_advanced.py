"""
Advanced plugin example using the decorator API.

Copy and rename this file to create your own commands.
"""


def setup(api):
    @api.on_keywords(["good morning", "good evening", "good afternoon"])
    def greet_time(text, speaker, timers):
        speaker.say("Good day to you!")
        return True

    @api.on_keywords(["thank", "thanks", "appreciate"])
    def thank_you(text, speaker, timers):
        speaker.say("You are welcome!")
        return True

    @api.on_regex(r"(?:tell|share|say)\s+(?:me\s+)?(?:a\s+)?joke")
    def tell_joke(text, speaker, timers, match):
        speaker.say("Why do programmers prefer dark mode? Because light attracts bugs!")
        return True

    @api.on_regex(r"repeat\s+(?:after\s+me\s+)?(.+)")
    def echo(text, speaker, timers, match):
        msg = match.group(1).strip()
        if msg:
            speaker.say(msg)
            return True
        return False

    @api.on_keywords(["screenshot", "take screenshot", "capture screen"])
    def screenshot(text, speaker, timers):
        import subprocess
        try:
            subprocess.Popen(["gnome-screenshot", "-i"])
            speaker.say("Opening screenshot tool")
        except FileNotFoundError:
            try:
                subprocess.Popen(["spectacle"])
                speaker.say("Opening screenshot tool")
            except FileNotFoundError:
                speaker.say("Screenshot tool not found")
        return True
