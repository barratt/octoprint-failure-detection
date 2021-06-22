# coding=utf-8
from __future__ import absolute_import

import octoprint.plugin

import urllib
import random
import string
import sys
import os
import json
import uuid
from requests import Request, Session
from requests_toolbelt.multipart.encoder import MultipartEncoder

from octoprint.util import RepeatedTimer

if sys.version_info.major > 2:
    import urllib.request
    urlrequest = urllib.request.urlretrieve
    xrange = range
else:
    urlrequest = urllib.urlretrieve

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

        # TODO: Check is printing
        # Upload the screenshot 
        self.detect_failure()

    def on_after_startup(self):
        self.printFileName = ""
        self.printId = ""
        self.availableCredits = 0

        self._logger.info("Hello")
        self._logger.info("Hello World! (more: %s)" % self._settings.get(["licenseKey"]))
        self.timer = RepeatedTimer(10.0, self.loop, run_first=True)
        self.timer.start()

    ##~~ SettingsPlugin mixin

    def get_settings_defaults(self):
        return dict(
            # put your plugin's default settings here
            licenseKey = None,
            host = "http://3ffa20353787.ngrok.io",
            # host = "https://func-octoprint-failure-detection.azurewebsites.net",
            debug = True,
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
        # Define the configuration for your plugin to use with the Software Update
        # Plugin here. See https://docs.octoprint.org/en/master/bundledplugins/softwareupdate.html
        # for details.
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
        self._logger.info(payload)

        if event == "PrintStarted":
            self.printId = str(uuid.uuid4())
        # self._logger.info(payload.name)


    def detect_failure(self):
        try:
            snapshot_url = self._settings.global_get(["webcam", "snapshot"])
            filename = ''.join([random.choice(string.ascii_letters + string.digits) for n in xrange(32)]) + '.jpg'
            filepath = '/tmp/' + filename

            urlrequest(snapshot_url, filename=filepath)

            self._logger.info('Sending to sever...')
            endpoint = self._settings.get(["host"]) + "/api/capture"
            licenseKey = self._settings.get(["licenseKey"]) or ""

            # Send up printer specs, file name etc
            # TODO: Send up the notification method too!
            mp_encoder = MultipartEncoder(
                fields={
                    'img': ('a.jpg', open(filepath, 'rb'), 'image/jpeg'),
                    'data': ('data.json', json.dumps({
                        'printerName': self._settings.get(["printer_name"]) or None,
                        'job': self._printer.get_current_job() or None,
                        'printId': self.printId or None,
                        'notificationSettings': self._settings.get(["notification_settings"])
                    }), 'application/json'),
                }
            )
            # PrinterInterface.get_state_id(self)
            req = Request('POST', endpoint, data=mp_encoder, headers = {
                'Authorization': licenseKey, 
                'Content-Type': mp_encoder.content_type,
            }).prepare()

            s = Session()
            response = s.send(req)
            self._logger.info('Sent! Got status %s and response: %s with headers: %s', response.status_code, response.text, response.headers)
            self._settings.set(["licenseKey"], response.headers.get("Authorization", licenseKey))

            self._logger.info("Done")
            # os.remove(filename)
        except Exception as e:
            self._logger.warn("Could not detect: %s" % e)
    
    def get_settings_restricted_paths(self):
            return dict(
                admin=[['licenseKey'], ]
            )

    def on_settings_save(self, data):
        octoprint.plugin.SettingsPlugin.on_settings_save(self, data)
    
    def get_template_configs(self):
        return [
            # dict(type="settings", custom_bindings=False)
            dict(type='settings', custom_bindings=True, template='simple_failure_detection_settings.jinja2')
        ]

    def get_template_vars(self):
        return dict(licenseKey = self._settings.get(["licenseKey"]))
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
