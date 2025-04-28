odoo.define('bloomup_fleet_move.address_edit', function (require) {
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


    class AddressEdit extends Component{
        static template = 'AddressEdit';
        constructor(parent, props) {
            super(parent, props);
            this.dispatch = owl.hooks.useDispatch();
            this.state = owl.hooks.useStore((state) => state);
        };
        static components = { 
            Autocomplete,
            ToastOwl
        };
        async change(e){
            var self = this;
            var value = $(e.currentTarget).val();
            var name = $(e.currentTarget).attr('name');
            /* obbligato a farlo per struttura form */
            if (name == 'company_type'){
                this.dispatch('set_record_id', {
                    'company_type': value,
                    'id': self.state.record_id.id,
                    'name': self.state.record_id.name,
                    'firstname': self.state.record_id.firstname,
                    'lastname': self.state.record_id.lastname,
                    'street': self.state.record_id.street,
                    'street2': self.state.record_id.street2,
                    'city': self.state.record_id.city,
                    'state_id': self.state.record_id.state_id,
                    'country_id': self.state.record_id.country_id,
                    'zip': self.state.record_id.zip,
                    'reference': self.state.record_id.reference,
                    'email': self.state.record_id.email,
                    'phone': self.state.record_id.phone,
                    'vat': self.state.record_id.vat,
                    'fiscalcode': self.state.record_id.fiscalcode
                });
                if (value == 'company'){
                    self.dispatch('set_mandatory', [
                        'name', 
                        'country_id', 
                        'state_id', 
                        'city', 
                        'zip', 
                        'street', 
                        'street2'
                    ])
                }else{
                    self.dispatch('set_mandatory',['firstname', 'lastname', 'country_id', 'state_id', 
                    'city', 'zip', 'street', 'street2'])
                }
            }
            this.dispatch('change', name, value);
        };
        async save(e){
            e.preventDefault();
            var self = this;
            self.dispatch('set_record_change', 'company_type', $('[name="company_type"]').val());
            this.dispatch('save').then(function(){
                self.dispatch('get_records');
            });
        }
        
    }

    return AddressEdit;
});