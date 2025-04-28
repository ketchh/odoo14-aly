odoo.define('bloomup_fleet_move_tyre.google_maps', function (require) {
    "use strict";
    
    require('web.dom_ready');
    const AbstractField = require('web.AbstractFieldOwl');
    const fieldRegistry = require('web.field_registry_owl');
    var session = require('web.session');
    var rpc = require('web.rpc');
    var core = require('web.core');
    var web_client = require('web.web_client');
    const { Component, useState, mount } = owl;

    
    var _t = core._t; 

    const icons = {
        'me_svg': '<svg width="40" height="40" viewBox="65.9918 59.0044 36.3538 51.9995" xmlns="http://www.w3.org/2000/svg"><g id="SVGRepo_iconCarrier" transform="matrix(0.9999999999999999, 0, 0, 0.9999999999999999, 58.16874313354492, 59.003910064697266)"><path style="fill:#F07857;" d="M38.853,5.324L38.853,5.324c-7.098-7.098-18.607-7.098-25.706,0h0 C6.751,11.72,6.031,23.763,11.459,31L26,52l14.541-21C45.969,23.763,45.249,11.72,38.853,5.324z M26.177,24c-3.314,0-6-2.686-6-6 s2.686-6,6-6s6,2.686,6,6S29.491,24,26.177,24z"/></g></svg>',
        'tyre_repairer': '<svg width="40" height="40" viewBox="65.9918 59.0044 36.3538 51.9995" xmlns="http://www.w3.org/2000/svg"><g id="SVGRepo_iconCarrier" transform="matrix(0.9999999999999999, 0, 0, 0.9999999999999999, 58.16874313354492, 59.003910064697266)"><path style="fill:#253342;" d="M38.853,5.324L38.853,5.324c-7.098-7.098-18.607-7.098-25.706,0h0 C6.751,11.72,6.031,23.763,11.459,31L26,52l14.541-21C45.969,23.763,45.249,11.72,38.853,5.324z M26.177,24c-3.314,0-6-2.686-6-6 s2.686-6,6-6s6,2.686,6,6S29.491,24,26.177,24z"/></g></svg>',
        'tyre_team': '<svg width="40" height="40" viewBox="65.9918 59.0044 36.3538 51.9995" xmlns="http://www.w3.org/2000/svg"><g id="SVGRepo_iconCarrier" transform="matrix(0.9999999999999999, 0, 0, 0.9999999999999999, 58.16874313354492, 59.003910064697266)"><path style="fill:#BF2C34;" d="M38.853,5.324L38.853,5.324c-7.098-7.098-18.607-7.098-25.706,0h0 C6.751,11.72,6.031,23.763,11.459,31L26,52l14.541-21C45.969,23.763,45.249,11.72,38.853,5.324z M26.177,24c-3.314,0-6-2.686-6-6 s2.686-6,6-6s6,2.686,6,6S29.491,24,26.177,24z"/></g></svg>',
        'favorite': '<svg width="40" height="40" viewBox="65.9918 59.0044 36.3538 51.9995" xmlns="http://www.w3.org/2000/svg"><g id="SVGRepo_iconCarrier" transform="matrix(0.9999999999999999, 0, 0, 0.9999999999999999, 58.16874313354492, 59.003910064697266)"><path style="fill:#253342;" d="M38.853,5.324L38.853,5.324c-7.098-7.098-18.607-7.098-25.706,0h0 C6.751,11.72,6.031,23.763,11.459,31L26,52l14.541-21C45.969,23.763,45.249,11.72,38.853,5.324z M26.177,24c-3.314,0-6-2.686-6-6 s2.686-6,6-6s6,2.686,6,6S29.491,24,26.177,24z"/></g><g id="g-3" transform="matrix(0.4804490208625793, 0, 0, 0.49921402335166926, 71.4374008178711, 61.83005905151367)" style=""><polygon style="fill:#F5C26B;" points="26.934,1.318 35.256,18.182 53.867,20.887 40.4,34.013 43.579,52.549 26.934,43.798 10.288,52.549 13.467,34.013 0,20.887 18.611,18.182 "/></g></svg>',
        'tyre_team_favorite': '<svg width="40" height="40" viewBox="65.9918 59.0044 36.3538 51.9995" xmlns="http://www.w3.org/2000/svg"><g id="SVGRepo_iconCarrier" transform="matrix(0.9999999999999999, 0, 0, 0.9999999999999999, 58.16874313354492, 59.003910064697266)"><path style="fill:#BF2C34;" d="M38.853,5.324L38.853,5.324c-7.098-7.098-18.607-7.098-25.706,0h0 C6.751,11.72,6.031,23.763,11.459,31L26,52l14.541-21C45.969,23.763,45.249,11.72,38.853,5.324z M26.177,24c-3.314,0-6-2.686-6-6 s2.686-6,6-6s6,2.686,6,6S29.491,24,26.177,24z"/></g><g id="g-3" transform="matrix(0.4804490208625793, 0, 0, 0.49921402335166926, 71.4374008178711, 61.83005905151367)" style=""><polygon style="fill:#F5C26B;" points="26.934,1.318 35.256,18.182 53.867,20.887 40.4,34.013 43.579,52.549 26.934,43.798 10.288,52.549 13.467,34.013 0,20.887 18.611,18.182 "/></g></svg>',
    }

    class GoogleMapsField extends AbstractField {
        state = useState({
            'loading': true, /* semaphore to show the spinner loader */
            'error': false, /* true if there was an error, false otherwise */
            'error_message': false, /* message to display if error == true */
            'warning': false, /* true if there was a warning, false otherwise */
            'warning_message': false /* message to display if warning == true */
        });
        /*
         * WARNING: show a bootstrap alert-warning on top of the dialog before the map
         * ERROR: not load map and show a text-danger message in the dialog
         */
        setup() {
            super.setup();
            var self=this;
            self.map = false; /* instantiated google map */
            self.center = {
                'lat': false,
                'lng': false
            }; /* latitude and longitude of the delivery address */
            self.cap = false; /* postcode of the delivery address (see get_center_and_cap) */
            self.res_id = false; /* db id of the delivery address (see get_center_and_cap) */
            self.customer_id = false; /* db id of the customer */
            self.radius = false; /* radius for the cap (see get_radius) */
            self.reloadmarker = false; /* semaphore: true if it is reloading the markers, false otherwise (see bound_changed) */
            self.tyre_repairs = []; /* list of tyre repairers */
            self.tyre_repairer_markers = []; /* list of tyre repairers markers (Google Map) */
            self.bounds = {
                'lat':{
                    'lo':0, //SouthWest
                    'hi':0  //NorthEast
                },
                'lng':{
                    'lo':0, //SouthWest
                    'hi':0  //NorthEast
                }
            }; /* current map bounds */

            self.res_id = self.recordData.delivery_address.res_id;
            self.customer_id = self.recordData.customer_id.data.id;
            
            owl.hooks.onWillStart(async () =>{
                /* Check if the Google Maps JavaScript API is
                already loaded. If it is not loaded, it dynamically loads the
                API by creating a script element and appending it to the HTML
                document's head. */
                if (!(typeof google === 'object' && typeof google.maps === 'object')){
                    (g=>{var h,a,k,p="The Google Maps JavaScript API",c="google",l="importLibrary",q="__ib__",m=document,b=window;b=b[c]||(b[c]={});var d=b.maps||(b.maps={}),r=new Set,e=new URLSearchParams,u=()=>h||(h=new Promise(async(f,n)=>{await (a=m.createElement("script"));e.set("libraries",[...r]+"");for(k in g)e.set(k.replace(/[A-Z]/g,t=>"_"+t[0].toLowerCase()),g[k]);e.set("callback",c+".maps."+q);a.src=`https://maps.${c}apis.com/maps/api/js?`+e;d[q]=f;a.onerror=()=>h=n(Error(p+" could not load."));a.nonce=m.querySelector("script[nonce]")?.nonce||"";m.head.append(a)}));d[l]?console.warn(p+" only loads once. Ignoring:",g):d[l]=(f,...n)=>r.add(f)&&u().then(()=>d[l](f,...n))})({
                        key: self.recordData.google_maps,
                        v: "weekly",
                    });
                }
                await self.get_center_and_cap();
                await self.get_radius();

                if(!self.res_id){
                    self.state.error = true;
                    self.state.error_message = _t("The map cannot be loaded because the delivery address is missing.");
                }else if(!self.center.lat || !self.center.lng){
                    self.state.error = true;
                    self.state.error_message = _t("The map cannot be loaded because the delivery address is not geolocalized.");
                }
                if(!self.state.error){
                    if(!self.radius){
                        self.state.warning = true;
                        self.state.warning_message = _t("We were unable to set a search radius because the postal code does not appear in our databases or is not set in the delivery address.");
                    }
                }
            });

            owl.hooks.onMounted(() => {
                self.state.loading = false;
                if(self.center.lat && self.center.lng){
                    self.load_map();
                }
            });

        }
        /**
         * The function retrieves the latitude, longitude, and zip code of a
         * delivery address and assigns them to the "center" and "cap" variables
         * respectively.
         */
        async get_center_and_cap(){
            var self=this;
            if(self.res_id){
                var address = await rpc.query({
                    model:'fleet.partner',
                    method:'search_read',
                    args:[[['id','=',self.res_id]],['id','latitude','longitude','zip']]
                });
                self.center = {
                    'lat':parseFloat(address[0].latitude),
                    'lng':parseFloat(address[0].longitude)
                };
                self.cap = address[0].zip;

            }
            
        }
        /**
         * The function `get_radius` retrieves the searching radius of a tyre repairer based
         * on the delivery_address cap
         */
        async get_radius(){
            var self=this;
            if(self.cap){
                var radius = await rpc.query({
                    model: 'tyre.repairer.radius',
                    method: 'search_read',
                    args: [[['cap','=',self.cap]],['cap','radius']]
                });
                if(radius.length > 0){
                    self.radius = parseInt(radius[0].radius);
                }
            }
        }
        /**
         * The function "load_map" loads a Google Map into a specified HTML
         * element, sets the center and zoom level, and adds a marker and circle to
         * the map.
         */
        async load_map(){
            var self=this;
            const { Map } = await google.maps.importLibrary("maps");
            var div = document.getElementById("fleet_move_tyre_map")
            var map = new Map(div, {
                center: self.center,
                zoom: 15,
                zoomControl: false,
                scaleControl: true,
                mapTypeId: google.maps.MapTypeId.ROADMAP,
                styles:[ // hide standard poi
                    {
                        featureType: "poi",
                        stylers: [
                        { visibility: "off" } 
                        ]   
                    }
                ]
            });
            div.style.height = "800px";
            self.map = map;
            
            self.set_center_marker();
            self.set_circle();
            self.bounds_changed();
            self.addLegend();
        }
        /**
         * The function sets a marker at the center of a Google Map using a custom
         * SVG icon.
         * The marker is the delivery address.
         */
        set_center_marker(){
            var self = this;
            var marker = new google.maps.Marker({
                position: self.center,
                map: self.map,
                clickable: false,
                icon: {
                    url: 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(icons.me_svg)
                },
            });
        }
        /**
         * The function sets a circle on a Google Map with a specified radius and
         * adjusts the map's bounds to fit the circle.
         */
        set_circle(){
            var self = this;
            /* radius setting */
            if(self.radius){
                var circle = new google.maps.Circle({
                    center: self.center,
                    radius: self.radius * 1000,
                    map: self.map,
                    fillOpacity: 0.15,
                });
                self.map.fitBounds(circle.getBounds());
            }
        }
        /**
         * The function `bounds_changed` listens for changes in the bounds of a
         * Google Maps object and get tyre repairers markers.
         */
        bounds_changed(){
            var self = this;
            google.maps.event.addListener(self.map, 'bounds_changed', async function() {
                if (!self.infowindowsOpen && !self.reloadmarker){
                    
                    var bounds =  self.map.getBounds();
                    self.bounds['lat'] = {
                        'lo': bounds.getSouthWest().lat(),
                        'hi': bounds.getNorthEast().lat()
                    };
                    self.bounds['lng'] = {
                        'lo':bounds.getSouthWest().lng(),
                        'hi':bounds.getNorthEast().lng()
                    }
                    
                    await self.get_tyre_repairers();
                    self.add_tyre_repairer_markers();

                }
            });
        }
        /**
         * The function "get_tyre_repairers" retrieves tyre repairers based on
         * given bounds and adds them to the "tyre_repairs" array.
         */
        async get_tyre_repairers(){
            var self = this;
            if(!self.reloadmarker){
                self.reloadmarker = true;
                var results = await rpc.query({
                    model: 'tyre.repairer',
                    method: 'get_tyre_repairers',
                    args:[self.bounds,self.tyre_repairs]
                });
                if (results.length>0){
                    for(var i in results){
                        self.tyre_repairs.push(results[i]);
                    }
                }
                self.reloadmarker = false;
            }
        }
        /**
         * The function adds markers to a map for tyre repairers, with different
         * icons based on their attributes.
         */
        add_tyre_repairer_markers(){
            var self = this;
            for (var m in self.tyre_repairs){
                var icon = icons['tyre_repairer'];
                if(self.tyre_repairs[m].tyreteam){
                    icon = icons['tyre_team'];
                }
                if( self.tyre_repairs[m].favorite_customers.includes(self.customer_id) ){
                    icon = icons['favorite'];
                }
                if(self.tyre_repairs[m].tyreteam && self.tyre_repairs[m].favorite_customers.includes(self.customer_id)){
                    icon = icons['tyre_team_favorite'];
                }
                var marker = new google.maps.Marker({
                    position: self.tyre_repairs[m].geo,
                    map: self.map,
                    icon: {
                        url: 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(icon)
                    },
                });
                /* The above code is creating an info window for a Google Maps
                marker. It sets the content of the info window to include the
                name and address of a tyre repair location, as well as a button
                to assign the repair. When the marker is clicked, the info
                window is displayed with the assigned content. Additionally,
                when the info window is ready, it adds a click event listener to
                the assign button. When the button is clicked, it makes an
                asynchronous request to update the selected tyre repairer for a
                fleet move record and closes a modal window. */
                var infoWindow = new google.maps.InfoWindow();
                var content = '<h5 style="width:90%"><b>'+ self.tyre_repairs[m].name +'</b></h5>';
                content += '<small>' + self.tyre_repairs[m].address + '</small><br/>';
                content += '<button class="btn btn-primary button-assign mt-3" data-id="' + self.tyre_repairs[m].id + '">' + _t('Assign') + '</button>';
                (function (marker, content) {
                    google.maps.event.addListener(marker, "click", function (e) {
                        //Wrap the content inside an HTML DIV in order to set height and width of InfoWindow.
                        infoWindow.setContent(content);
                        infoWindow.setOptions({maxWidth:250})
                        infoWindow.open(self.map, marker);
                    });
                })(marker, content);
                google.maps.event.addListener(infoWindow, 'domready', function() {
                    $('.button-assign').click(async function(e){
                        var id = e.target.dataset.id;
                        await rpc.query({
                            model: 'fleet.move',
                            method: 'write',
                            args:[self.recordData.id,{'selected_tyre_repairer':parseInt(id)}]
                        });
                        document.querySelectorAll('[data-dismiss="modal"]')[0].click();
                    });                  
                 });
                self.tyre_repairer_markers.push(marker);
            }
        }
        /**
         * The function "addLegend" adds a legend to a Google Maps instance,
         * displaying different icons and their corresponding names.
         */
        addLegend(){
            var self = this;
            const licons = {
                me: {
                  name:  _t("Delivery Address"),
                  icon:  'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(icons.me_svg)
                },
                tyre_repairer: {
                    name:  _t("Tyre Repairer"),
                    icon:  'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(icons.tyre_repairer)
                },
                tyre_team: {
                    name: _t("Tyre Team"),
                    icon:  'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(icons.tyre_team)
                },
                favorite: {
                    name: _t("Favorite Tyre Repairer"),
                    icon:  'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(icons.favorite)
                },
                tyre_tem_favorite: {
                    name: _t("Favorite Tyre Team"),
                    icon:  'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(icons.tyre_team_favorite)
                }
            };
            const legend = document.getElementById("legend");
            
            for (const key in licons) {
                const type = licons[key];
                const name = type.name;
                const icon = type.icon;
                const div = document.createElement("div");
    
                div.innerHTML = '<img src="' + icon + '"> ' + name;
                legend.appendChild(div);
    
            }
    
            self.map.controls[google.maps.ControlPosition.RIGHT_BOTTOM].push(legend);
        }
    }
    GoogleMapsField.template = 'GoogleMapsField';
    fieldRegistry.add('google_maps_field', GoogleMapsField);
    return GoogleMapsField;
});