# coding=utf-8
from __future__ import absolute_import

import octoprint.plugin

import io
import uuid
import requests
from octoprint.util import RepeatedTimer
from PIL import Image

class Failure_detectionPlugin(octoprint.plugin.SettingsPlugin,
    octoprint.plugin.AssetPlugin,
    octoprint.plugin.TemplatePlugin,
    octoprint.plugin.EventHandlerPlugin,
    octoprint.plugin.StartupPlugin
):

    def loop(self):
        self._logger.info("Timer fired")
        # Not printing & not debugging
        if not self._printer.is_printing() and not self._settings.get(["debug"]):
            self._logger.info("Not printing")
            return 

        self._logger.info("We are printing, attempting to check for failure")
        # Upload the screenshot 
        self.detect_failure()

    def on_after_startup(self):
        self.printFileName = ""
        self.printId = ""
        self.availableCredits = 0

        self._logger.info("Hello World! (License Key: {})".format(self._settings.get(["licenseKey"])))
        self.timer = RepeatedTimer(10.0, self.loop, run_first=True)
        # We can start it when a print starts.
        self.timer.start()

    ##~~ SettingsPlugin mixin
    def get_settings_defaults(self):
        return dict(
            # put your plugin's default settings here
            licenseKey = None,
            # host = "http://3ffa20353787.ngrok.io",
            # host = "https://func-octoprint-failure-detection.azurewebsites.net",
            host = "http://host.docker.internal:7071/api",
            debug = False,
            notificationSettings = dict(
                email   = None,
                sms     = None,
            )
        )

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
        return {
            "failure_detection": {
                "displayName": "Simple Failure Detection",
                "displayVersion": self._plugin_version,

                # version check: github repository
                "type": "github_release",
                "user": "Barratt",
                "repo": "octoprint-failure-detection",
                "current": self._plugin_version,

                # update method: pip
                "pip": "https://github.com/barratt/octoprint-failure-detection/archive/{target_version}.zip",
            }
        }

    def on_event(self, event, payload):
        self._logger.info("Hello")
        self._logger.info(event)
        self._logger.info(payload)

        # PrinterStateChanged
        if event == "PrintStarted":
            self._logger.info("PRINT STARTED")
            self.printId = str(uuid.uuid4())
            self.timer.start()

        if event == "PrintCancelled": 
            self._logger.info("HELLO CANCELLED!")
            # Detect failure and stop the timer?


        #  PrintCancelled could be _really_ good for us.

        # self._logger.info(payload.name)


    def detect_failure(self):
        try:
            snapshot_url = self._settings.global_get(["webcam", "snapshot"])
            filename = 'sfdprint.jpg'
            filepath = '/tmp/' + filename

            snapshotReeponse = requests.get(snapshot_url)
            # Snapshot response can be none
            img = io.BytesIO(snapshotReeponse.content)

            endpoint = self._settings.get(["host"]) + "/capture"
            licenseKey = self._settings.get(["licenseKey"]) or ""
            trainingMode = self._settings.get(["training"]) or False # Allows full size image uploading
            self._logger.info('Sending last capture to {} with key {}...'.format(endpoint, licenseKey))

            if not trainingMode:
                self._logger.info("Resizing before we send to reduce bandwidth")
                new_width  = 600
                new_height = 600
                img = Image.open(filepath)
                img = img.resize((new_height, new_width))
                self._logger.info('saving as {}'.format(filepath))
                img.save(filepath)
                
            self._logger.info('reading image')
            img = open(filepath, 'rb').read()

            self._logger.info('sending image')
            # We need some kind of way of detecting this printer is unique for their license key, for now we will just rate limit
            response = requests.post(endpoint, data=img, headers = {
                'Authorization': licenseKey, 
                'Content-Type': 'application/octet-stream'
            })

            self._logger.info('Sent! Got status %s and response: %s with headers: %s', response.status_code, response.text, response.headers)

            if licenseKey is None:
                self._logger.info("Our license key was not set before, lets set it")
                self._settings.set(["licenseKey"], response.headers.get("Authorization", licenseKey))
                self._settings.save()

            self._logger.info("Done")
            # os.remove(filename)
        except Exception as e:
            self._logger.warn("Could not detect: %s" % e)
    
    def get_settings_restricted_paths(self):
            return dict(
                admin=[
                    ['licenseKey'],
                ]
            )

    def on_settings_save(self, data):
        self._logger.info('Saving')
        octoprint.plugin.SettingsPlugin.on_settings_save(self, data)
    
    def get_template_configs(self):
        return [
			dict(type = "settings", custom_bindings = False)
		]

    def get_template_vars(self):
        return dict(
            licenseKey = self._settings.get(["licenseKey"]),
            host = self._settings.get(["host"]),
            enabled = self._settings.get(["enabled"]),
        )
# If you want your plugin to be registered within OctoPrint under a different name than what you defined in setup.py
# ("OctoPrint-PluginSkeleton"), you may define that here. Same goes for the other metadata derived from setup.py that
# can be overwritten via __plugin_xyz__ control properties. See the documentation for that.
__plugin_name__ = "Simple Failure Detection"

# Starting with OctoPrint 1.4.0 OctoPrint will also support to run under Python 3 in addition to the deprecated
# Python 2. New plugins should make sure to run under both versions for now. Uncomment one of the following
# compatibility flags according to what Python versions your plugin supports!
#__plugin_pythoncompat__ = ">=2.7,<3" # only python 2
__plugin_pythoncompat__ = ">=3,<4" # only python 3
# __plugin_pythoncompat__ = ">=2.7,<4" # python 2 and 3

def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = Failure_detectionPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
    }
