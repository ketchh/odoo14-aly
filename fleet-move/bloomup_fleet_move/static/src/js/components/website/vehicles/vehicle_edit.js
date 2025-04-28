odoo.define('bloomup_fleet_move.vehicle_edit', function (require) {
    "use strict";

    require('web.dom_ready');
    var core = require('web.core');
    var _t = core._t;
    var rpc = require('web.rpc');
    var session  = require('web.session');
    const { Component, useState, mount } = owl;
    const { xml } = owl.tags;

    const Autocomplete = require('bloomup_owl_components.autocomplete');
    const ToastOwl = require('bloomup_owl_components.toast');

    class VehicleEdit extends Component{
        static template = 'VehiclesEdit2';
        constructor(parent, props) {
            super(parent, props);
            this.dispatch = owl.hooks.useDispatch();
            this.state = owl.hooks.useStore((state) => state);
        }
        static components = { 
            Autocomplete,
            ToastOwl
        };
        async change(e){
            var value = $(e.currentTarget).val();
            var name = $(e.currentTarget).attr('name');
            this.dispatch('change', name, value);
        }
        async save(e){
            e.preventDefault();
            var self = this;
            this.dispatch('save').then(function(){
                self.dispatch('get_records');
            });
        }

        Produttore = {
            'placeholder': this.env.qweb.translateFn('Brand'),
            'model': 'fleet.vehicle.model.brand'
        };
        Modello = {
            'placeholder': this.env.qweb.translateFn('Model'),
            'model': 'fleet.vehicle.model'
        };
    }

    return VehicleEdit;
});