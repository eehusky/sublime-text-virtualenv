
import os.path
import shlex

import sublime
import sublime_plugin
import Default as sublime_default

from . import virtualenv_lib as virtualenv


def settings():
    return sublime.load_settings("Virtualenv.sublime-settings")


class VirtualenvCommand:

    @property
    def virtualenv_exec(self):
        return shlex.split(settings().get('executable'))

    @property
    def virtualenv_directories(self):
        return [os.path.expanduser(path)
                for path in settings().get('virtualenv_directories')]

    def get_virtualenv(self, **kwargs):
        venv = kwargs.pop('virtualenv', "")

        if not venv:
            try:
                project_data = self.window.project_data() or {}
                venv = project_data['virtualenv']
            except KeyError:
                sublime.error_message("Could not determine virtualenv from settings.")

        return os.path.expanduser(venv)

    def set_virtualenv(self, venv):
        project_data = self.window.project_data() or {}
        project_data['virtualenv'] = venv
        self.window.set_project_data(project_data)

    def find_virtualenvs(self):
        return virtualenv.find_virtualenvs(self.virtualenv_directories)


class VirtualenvExecCommand(sublime_default.exec.ExecCommand, VirtualenvCommand):
    def run(self, **kwargs):
        venv = self.get_virtualenv(**kwargs)
        postactivate = virtualenv.activate(venv)
        kwargs['path'] = postactivate['path']
        kwargs['env'] = dict(kwargs.get('env', {}), **postactivate['env'])
        super(VirtualenvExecCommand, self).run(**kwargs)


class ActivateVirtualenvCommand(sublime_plugin.WindowCommand, VirtualenvCommand):
    def run(self, **kwargs):
        self.available_venvs = self.find_virtualenvs()
        self.window.show_quick_panel(self.available_venvs, self._set_virtualenv)

    def _set_virtualenv(self, index):
        if index != -1:
            self.set_virtualenv(self.available_venvs[index])


class NewVirtualenvCommand(sublime_plugin.WindowCommand, VirtualenvCommand):
    def run(self, path="", **kwargs):
        if path:
            self.create_virtualenv(os.path.expanduser(path))
        else:
            self.window.show_input_panel(
                "Virtualenv Path:", self.virtualenv_directories[0] + os.path.sep,
                self.create_virtualenv, None, None)

    def create_virtualenv(self, path):
        venv = os.path.normpath(path)
        self.window.run_command('exec', {'cmd': self.virtualenv_exec + [venv]})
        self.set_virtualenv(venv)
