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
    def get_settings_defaults(self):
        return dict(
            # put your plugin's default settings here
            licenseKey = None,
            printerId = None,
            # host = "http://3ffa20353787.ngrok.io",
            host = "https://func-octoprint-failure-detection.azurewebsites.net/api", # TODO: Move this to a custom domain... At some point...
            # host = "http://host.docker.internal:7071/api",
            # host = "http:/api.presspla.uk",
            debug = False,
            enabled = False,
            interval = 30.0,
            training = False,
            email = None,
            stopOnFailure = False,
            navbarEnabled = True,

            notificationSettings = dict(
                email   = None,
                sms     = None,
            )
        )

    def loop(self):
        self._logger.info("Timer fired")
        # Not printing & not debugging
        if not self._printer.is_printing() and not self._settings.get(["debug"]):
            self._logger.info("Not printing")
            return 

        if not self._settings.get(["enabled"]): 
            self._logger.info("Not opted-in")
            return 

        self.niceStatus = "Watching"
        self._plugin_manager.send_plugin_message(self._identifier, dict(type="var_update", name="status", value=self.niceStatus))

        self._logger.info("We are printing, attempting to check for failure")
        # Upload the screenshot 
        self.detect_failure()

    def get_check_interval(self):
        return int(self._settings.get(["interval"]))

    def on_after_startup(self):
        self._logger.info("Hello World! (License Key: {})".format(self._settings.get(["licenseKey"])))
        self.timer = RepeatedTimer(self.get_check_interval, self.loop, run_first=True)

        # Create a unique way of identifying this install
        printerId = self._settings.get(["printerId"])
        if printerId is None:
            printerId = str(uuid.uuid4())
            self._settings.set(["printerId"], printerId)
            print("saving printer settings")
            self._settings.save()
            print("done")

        self.printerId = printerId
        self.niceStatus = "Ready"

    def get_assets(self):
        # Define your plugin's asset files to automatically include in the
        # core UI here.
        return {
            "js":   [ "js/failure_detection.js" ],
            "css":  [ "css/failure_detection.css" ]
        }

    def get_update_information(self):
        return {
            "failure_detection": {
                "displayName": "Simple Failure Detection",
                "displayVersion": self._plugin_version,

                "type": "httpheader",
                "header_url": "https://failuredetection.blob.core.windows.net/public/dist/latest.zip",
                "header_name": "Last-Modified",
                "header_method": "HEAD",

                # "type": "github",
                # "user": "Barratt",
                # "repo": "octoprint-failure-detection",
                # "current": self._plugin_version,

                # update method: pip
                "pip": "https://failuredetection.blob.core.windows.net/public/dist/latest.zip",
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
            if not self._settings.get(["enabled"]): 
                self._logger.info("Not opted-in")
                return 

            self._logger.info("Print cancelled, this is usually due to failure so lets grab a screenshot")
            # Upload the screenshot 
            self.detect_failure()
            self.niceStatus = "Ready"
            self._plugin_manager.send_plugin_message(self._identifier, dict(type="var_update", name="status", value=self.niceStatus))
            
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
            
            response = requests.post(endpoint, data=img, headers = {
                'Authorization': licenseKey, 
                'PrinterID': self.printerId,    # Using these we don't accidentally send the notification to the wrong printer.
                'PrintID': self.printId,
                # Print time and layer height could be interesting metrics to track
                # If we're 4 hours into a print and nothings coming out the nozzle etc
                'Content-Type': 'application/octet-stream'
            })

            self._logger.info('Sent! Got status %s and response: %s with headers: %s', response.status_code, response.text, response.headers)
            if licenseKey is None:
                self._logger.info("Our license key was not set before, lets set it")
                self._settings.set(["licenseKey"], response.headers.get("Authorization", licenseKey))
                self._settings.save()

            # This can be triggered on cancell or on timer if we see a failure we might want to stop the print though if its running
            

            self._logger.info("Done")
            # os.remove(filename)
        except Exception as e:
            self._logger.warn("Could not detect: %s" % e)
            self.niceStatus = 'Error'
            self._plugin_manager.send_plugin_message(self._identifier, dict(type="var_update", name="status", value=self.niceStatus))

    
    def get_settings_restricted_paths(self):
            return dict(
                admin=[
                    ['licenseKey'],
                ]
            )

    def on_settings_save(self, data):
        self._logger.info('Saving')
        # Validate settings
        # If email / sms has changed let the server know the new details

        octoprint.plugin.SettingsPlugin.on_settings_save(self, data)
    
    def get_template_configs(self):
        return [
			dict(type = "settings", custom_bindings = True),
			dict(type = "navbar", custom_bindings = True)
		]

    def get_template_vars(self):
        return dict(
            licenseKey = self._settings.get(["licenseKey"]),
            host = self._settings.get(["host"]),
            enabled = self._settings.get(["enabled"]),
            navbarEnabled = self._settings.get(["navbarEnabled"]),
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
