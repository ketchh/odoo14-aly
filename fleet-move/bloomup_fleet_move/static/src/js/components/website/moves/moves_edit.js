odoo.define('bloomup_fleet_move.moves_edit', function (require) {
    "use strict";

    require('web.dom_ready');
    var core = require('web.core');
    var _t = core._t;
    var rpc = require('web.rpc');
    var session  = require('web.session');
    const { Component, useState, mount } = owl;
    const { xml } = owl.tags;
    const { useContext } = owl.hooks;

    const Autocomplete = require('bloomup_owl_components.autocomplete');
    const ToastOwl = require('bloomup_owl_components.toast');


    class MoveEdit extends Component{
        static template = 'MoveEdit';
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
        
    }

    return MoveEdit;
});