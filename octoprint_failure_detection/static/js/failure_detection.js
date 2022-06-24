/*
 * View model for OctoPrint-Failure_detection
 *
 * Author: Barratt
 * License: MIT
 */
$(function() {
    function Failure_detectionViewModel(parameters) {
        var self = this;
        self.settings = parameters[0];
        
        self.status = ko.observable();
        self.navbarEnabled = ko.observable();
        self.sensitivityOptions = ko.observableArray(['Not Sensitive', 'Recommended', 'Very Sensitive']);
        self.sensitivity = ko.observable();


        self.onBeforeBinding = function() {
            self.navbarEnabled(self.settings.settings.plugins.simple_failure_detection.navbarEnabled);
            self.status(self.settings.settings.plugins.simple_failure_detection.niceStatus);
            // self.goToUrl();
        }

        // Watch for status change somehow?
    }

    /* view model class, parameters for constructor, container to bind to
     * Please see http://docs.octoprint.org/en/master/plugins/viewmodels.html#registering-custom-viewmodels for more details
     * and a full list of the available options.
     */
    OCTOPRINT_VIEWMODELS.push({
        construct: Failure_detectionViewModel,
        // ViewModels your plugin depends on, e.g. loginStateViewModel, settingsViewModel, ...
        dependencies: [ 
            "settingsViewModel", 
            "navigationViewModel"
            /* "loginStateViewModel" */
        ],
        elements: [ 
            '#sfd_nav',
            '#failure_detection_settings'
        ]
    });
});
