odoo.define('hr_attendance_geolocation_map.attendance_map', function (require) {
"use strict";

var AbstractAction = require('web.AbstractAction');
var core = require('web.core');

var QWeb = core.qweb;
var _t = core._t;

var AttendanceMapWidget = AbstractAction.extend({
    
    init: function (parent, action, options) {
        this._super.apply(this, arguments);
        this.locations = action.params.locations || [];
        this.attendance_id = action.params.attendance_id;
    },

    willStart: function () {
        // Load Leaflet library if not already loaded
        var self = this;
        return this._super.apply(this, arguments).then(function () {
            return self._loadLeafletAssets();
        });
    },

    start: function () {
        var self = this;
        // Create the HTML structure directly
        this.$el.html(this._getMapHtml());
        
        return this._super.apply(this, arguments).then(function () {
            // Wait a bit for DOM to be ready, then initialize map
            setTimeout(function () {
                self._initializeMap();
            }, 100);
        });
    },

    _getMapHtml: function () {
        return '<div class="o_attendance_map">' +
                   '<div class="o_content">' +
                       '<div class="map-header" style="padding: 20px; text-align: center;">' +
                           '<h3>Attendance Locations</h3>' +
                           '<p class="text-muted">Check-in and Check-out locations for this attendance record</p>' +
                           '<div class="map-legend" style="margin: 10px 0;">' +
                               '<span style="color: red; margin-right: 20px;">🔴 Check-in</span>' +
                               '<span style="color: blue;">🔵 Check-out</span>' +
                           '</div>' +
                       '</div>' +
                       '<div class="map-container">' +
                           '<div id="attendance-map" style="height: 500px; width: 100%;"></div>' +
                       '</div>' +
                   '</div>' +
               '</div>';
    },

    _loadLeafletAssets: function () {
        // Load Leaflet library if not already loaded
        if (window.L) {
            return Promise.resolve();
        }
        
        return new Promise(function (resolve, reject) {
            // Load Leaflet CSS
            var link = document.createElement('link');
            link.rel = 'stylesheet';
            link.href = 'https://unpkg.com/leaflet@1.7.1/dist/leaflet.css';
            document.head.appendChild(link);
            
            // Load Leaflet JS
            var script = document.createElement('script');
            script.src = 'https://unpkg.com/leaflet@1.7.1/dist/leaflet.js';
            script.onload = function () {
                resolve();
            };
            script.onerror = function () {
                reject(new Error('Failed to load Leaflet'));
            };
            document.head.appendChild(script);
        });
    },

    _initializeMap: function () {
        var self = this;
        
        // Check if we have any locations
        if (!this.locations || this.locations.length === 0) {
            this.$('#attendance-map').html(
                '<div class="alert alert-warning text-center" style="margin: 50px; padding: 20px;">' + 
                '<i class="fa fa-exclamation-triangle" style="font-size: 48px; color: #f39c12; margin-bottom: 10px;"></i><br/>' +
                _t('No location data available for this attendance record.') +
                '</div>'
            );
            return;
        }

        try {
            // Initialize the map
            var mapElement = document.getElementById('attendance-map');
            if (!mapElement) {
                console.error('Map container not found');
                return;
            }

            this.map = L.map('attendance-map').setView([0, 0], 2);

            // Add OpenStreetMap tiles
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap contributors'
            }).addTo(this.map);

            // Add markers for each location
            this._addLocationMarkers();

        } catch (error) {
            console.error('Error initializing map:', error);
            this.$('#attendance-map').html(
                '<div class="alert alert-danger text-center" style="margin: 50px; padding: 20px;">' + 
                '<i class="fa fa-times-circle" style="font-size: 48px; color: #e74c3c; margin-bottom: 10px;"></i><br/>' +
                _t('Error loading map. Please try again.') +
                '</div>'
            );
        }
    },

    _addLocationMarkers: function () {
        var self = this;
        var markers = [];

        this.locations.forEach(function (location) {
            if (location.latitude && location.longitude) {
                var icon = self._createCustomIcon(location.type);
                var marker = L.marker([location.latitude, location.longitude], { icon: icon })
                    .bindPopup(self._createPopupContent(location))
                    .addTo(self.map);
                
                markers.push(marker);
            }
        });

        // Fit map to show all markers
        if (markers.length > 0) {
            var group = new L.featureGroup(markers);
            this.map.fitBounds(group.getBounds(), { padding: [20, 20] });
        }
    },

    _createCustomIcon: function (type) {
        var color = type === 'check_in' ? 'red' : 'blue';
        var symbol = type === 'check_in' ? '🔴' : '🔵';
        
        return L.divIcon({
            className: 'custom-div-icon',
            html: '<div style="background-color: ' + color + '; color: white; border-radius: 50%; width: 25px; height: 25px; text-align: center; line-height: 25px; border: 2px solid white; box-shadow: 0 0 5px rgba(0,0,0,0.3);">' + symbol + '</div>',
            iconSize: [25, 25],
            iconAnchor: [12, 12]
        });
    },

    _createPopupContent: function (location) {
        var title = location.type === 'check_in' ? _t('Check-in') : _t('Check-out');
        var time = location.time || '';
        var employee = location.employee || '';
        
        return '<div style="text-align: center;">' +
               '<h4 style="margin: 5px 0; color: ' + (location.type === 'check_in' ? 'red' : 'blue') + ';">' + title + '</h4>' +
               (employee ? '<p style="margin: 2px 0;"><strong>' + employee + '</strong></p>' : '') +
               (time ? '<p style="margin: 2px 0;">' + time + '</p>' : '') +
               '<p style="margin: 2px 0; font-size: 12px; color: #666;">' + 
               location.latitude.toFixed(6) + ', ' + location.longitude.toFixed(6) +
               '</p></div>';
    },

    destroy: function () {
        if (this.map) {
            this.map.remove();
        }
        this._super.apply(this, arguments);
    }
});

core.action_registry.add('hr_attendance_map', AttendanceMapWidget);

return AttendanceMapWidget;

});
