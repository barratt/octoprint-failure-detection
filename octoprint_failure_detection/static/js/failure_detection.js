/*
 * View model for OctoPrint-Failure_detection
 *
 * Author: Barratt
 * License: MIT
 */
$(function() {
    function sfd(parameters) {
        var self = this;
        self.settings = parameters[0];
        self.sensitivityOptions = ko.observableArray(['Not Sensitive', 'Recommended', 'Very Sensitive']);
        self.sensitivity = ko.observable();
        self.status = ko.observable("Waiting");
        self.navbarEnabled = ko.observable();

        self.onBeforeBinding = function() {
            self.navbarEnabled(self.settings.settings.plugins.simple_failure_detection.navbarEnabled);
            self.status(self.settings.settings.plugins.simple_failure_detection.niceStatus);
        }

        self.onDataUpdaterPluginMessage = function(plugin, message) {
            if (plugin != "simple_failure_detection") return console.log("Got a message not for us"); // Not for us
            console.log("SFD: Received message")
            if (message.type == 'var_update') {
                return self[message.name](message.value)
            }
        }
    }

    OCTOPRINT_VIEWMODELS.push({
        construct: sfd,
        dependencies: [ 
            "settingsViewModel", 
            "navigationViewModel",
        ],
        elements: [
            '#failure_detection_settings',
            '#sfd_nav',
        ]
    });
});
