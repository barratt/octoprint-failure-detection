/*
 * View model for OctoPrint-Failure_detection
 *
 * Author: You
 * License: AGPLv3
 */
$(function() {
    function Failure_detectionViewModel(parameters) {
        var self = this;
        self.settings = parameters[0];
        console.log("Hello shaun");
        // assign the injected parameters, e.g.:
        // self.loginStateViewModel = parameters[0];

        // TODO: Implement your plugin's view model here.
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
            /* "loginStateViewModel" */
        ],
        elements: [ 
            '#failure_detection_settings',
        ]
    });
});
