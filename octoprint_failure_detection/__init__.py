# coding=utf-8
from __future__ import absolute_import

### (Don't forget to remove me)
# This is a basic skeleton for your plugin's __init__.py. You probably want to adjust the class name of your plugin
# as well as the plugin mixins it's subclassing from. This is really just a basic skeleton to get you started,
# defining your plugin as a template plugin, settings and asset plugin. Feel free to add or remove mixins
# as necessary.
#
# Take a look at the documentation on what other plugin mixins are available.

import octoprint.plugin

class Failure_detectionPlugin(octoprint.plugin.SettingsPlugin,
    octoprint.plugin.AssetPlugin,
    octoprint.plugin.TemplatePlugin
):

    def on_after_startup(self):
        self._logger.info("Hello World! (more: %s)" % self._settings.get(["licenseKey"]))

    ##~~ SettingsPlugin mixin

    def get_settings_defaults(self):
        return {
            # put your plugin's default settings here
            licenseKey = "My License"
        }

    ##~~ AssetPlugin mixin

    def get_assets(self):
        # Define your plugin's asset files to automatically include in the
        # core UI here.
        return {
            "js": ["js/failure_detection.js"],
            "css": ["css/failure_detection.css"],
            "less": ["less/failure_detection.less"]
        }

    ##~~ Softwareupdate hook

    def get_update_information(self):
        # Define the configuration for your plugin to use with the Software Update
        # Plugin here. See https://docs.octoprint.org/en/master/bundledplugins/softwareupdate.html
        # for details.
        return {
            "failure_detection": {
                "displayName": "Failure_detection Plugin",
                "displayVersion": self._plugin_version,

                # version check: github repository
                "type": "github_release",
                "user": "you",
                "repo": "OctoPrint-Failure_detection",
                "current": self._plugin_version,

                # update method: pip
                "pip": "https://github.com/you/OctoPrint-Failure_detection/archive/{target_version}.zip",
            }
        }

    def detect_failure(self):
        try:
            snapshot_url = self._settings.global_get(["webcam", "snapshot"])
            filename = str('/tmp/' + ''.join([random.choice(string.ascii_letters + string.digits) for n in xrange(32)])) + '.jpg'
            urlrequest(snapshot_url, filename=filename)
            self._logger.info('Sending to sever...')
            self.upload_file(filename, filename, pic=True)
            os.remove(filename)
        except Exception as e:
            self._logger.warn("Could not detect: %s" % e)


# If you want your plugin to be registered within OctoPrint under a different name than what you defined in setup.py
# ("OctoPrint-PluginSkeleton"), you may define that here. Same goes for the other metadata derived from setup.py that
# can be overwritten via __plugin_xyz__ control properties. See the documentation for that.
__plugin_name__ = "Failure_detection Plugin"

# Starting with OctoPrint 1.4.0 OctoPrint will also support to run under Python 3 in addition to the deprecated
# Python 2. New plugins should make sure to run under both versions for now. Uncomment one of the following
# compatibility flags according to what Python versions your plugin supports!
#__plugin_pythoncompat__ = ">=2.7,<3" # only python 2
#__plugin_pythoncompat__ = ">=3,<4" # only python 3
#__plugin_pythoncompat__ = ">=2.7,<4" # python 2 and 3

def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = Failure_detectionPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
    }
