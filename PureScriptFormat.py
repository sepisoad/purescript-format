import os
import os.path
import re
import sublime
import sublime_plugin
import subprocess



class PurescriptFormatCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        purescript_format = find_purescript_format(self.view)

        if purescript_format == None:
            return

        region = sublime.Region(0, self.view.size())
        content = self.view.substr(region)

        stdout, stderr = subprocess.Popen(
            [purescript_format, 'format'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=os.name=="nt").communicate(input=bytes(content, 'UTF-8'))

        if stderr.strip():
            open_panel(self.view, re.sub('\x1b\[\d{1,2}m', '', stderr.strip().decode()))
        else:
            self.view.replace(edit, region, stdout.decode('UTF-8'))
            self.view.window().run_command("hide_panel", {"panel": "output.purescript_format"})



#### ON SAVE ####


class PurescriptFormatOnSave(sublime_plugin.EventListener):
    def on_pre_save(self, view):
        scope = view.scope_name(0)
        if (scope.find('source.purescript') != -1 or scope.find('source.haskell') != -1 ) and needs_format(view):
            view.run_command('purescript_format')


def needs_format(view):
    settings = sublime.load_settings('purescript-format-on-save.sublime-settings')
    on_save = settings.get('on_save', True)

    if isinstance(on_save, bool):
        return on_save

    if isinstance(on_save, dict):
        path = view.file_name()
        included = is_included(on_save, path)
        excluded = is_excluded(on_save, path)
        if isinstance(included, bool) and isinstance(excluded, bool):
            return included and not excluded

    open_panel(view, invalid_settings)
    return False


def is_included(on_save, path):
    if "including" in on_save:
        if not isinstance(on_save.get("including"), list):
            return None

        for string in on_save.get("including"):
            if string in path:
                return True

        return False

    return True


def is_excluded(on_save, path):
    if "excluding" in on_save:
        if not isinstance(on_save.get("excluding"), list):
            return None

        for string in on_save.get("excluding"):
            if string in path:
                return True

        return False

    return False



#### EXPLORE PATH ####


def find_purescript_format(view):
    settings = sublime.load_settings('purescript-format-on-save.sublime-settings')
    given_path = settings.get('absolute_path')
    if given_path != None and given_path != '':
        if isinstance(given_path, str) and os.path.isabs(given_path) and os.access(given_path, os.X_OK):
            return given_path

        open_panel(view, bad_absolute_path)
        return None

    exts = os.environ['PATHEXT'].lower().split(os.pathsep) if os.name == 'nt' else ['']
    for directory in os.environ['PATH'].split(os.pathsep):
        for ext in exts:
            path = os.path.join(directory, 'purs-tidy' + ext)
            if os.access(path, os.X_OK):
                return path

    open_panel(view, cannot_find_purescript_format())
    return None



#### ERROR MESSAGES ####


def open_panel(view, content):
    window = view.window()
    panel = window.create_output_panel("purescript_format")
    panel.set_read_only(False)
    panel.run_command('erase_view')
    panel.run_command('append', {'characters': content})
    panel.set_read_only(True)
    window.run_command("show_panel", {"panel": "output.purescript_format"})



#### ERROR MESSAGES ####


def cannot_find_purescript_format():
    return """-- PURESCRIPT-FORMAT NOT FOUND -----------------------------------------------

I tried run purescript-format, but I could not find it on your computer.
"""


invalid_settings = """-- INVALID SETTINGS ---------------------------------------------------

The "on_save" field in your settings is invalid.
"""


bad_absolute_path = """-- INVALID SETTINGS ---------------------------------------------------

The "absolute_path" field in your settings is invalid.
"""
