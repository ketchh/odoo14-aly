odoo.define('bloomup_fleet_move.addresses_table', function (require) {
    "use strict";

    require('web.dom_ready');
    var core = require('web.core');
    var _t = core._t;
    var rpc = require('web.rpc');
    var session  = require('web.session');
    const { Component, useState, mount } = owl;
    const { xml } = owl.tags;
    const { useContext } = owl.hooks;
    const CancelDialog = require('bloomup_owl_components.cancel_dialog');
    const AddressEdit = require('bloomup_fleet_move.address_edit');
   
    class AddressesTable extends Component{
        static template = 'AddressesTable';
        constructor(parent, props) {
            super(parent, props);
            this.dispatch = owl.hooks.useDispatch();
            this.state = owl.hooks.useStore((state) => state);
        }
        static components = { 
            CancelDialog,
            AddressEdit
        };
        async edit(record_id){
            await this.dispatch('get_data_record', record_id);
            $('#edit_address').modal({
                backdrop: 'static',
                keyboard: false
            });
            if(this.state.record_id.company_type == 'person'){
                this.dispatch('set_mandatory',['firstname', 'lastname', 'country_id', 'state_id', 
                    'city', 'zip', 'street', 'street2']);
            }else{
                this.dispatch('set_mandatory', [
                    'name', 
                    'country_id', 
                    'state_id', 
                    'city', 
                    'zip', 
                    'street', 
                    'street2'
                ]);
            }
        }
        async cancel(record_id){
            var self = this;
            $('#confirm').modal({
                backdrop: 'static',
                keyboard: false
            }).on('click', '#cancel-go', async function(){
                var res = self.dispatch('cancel_record', record_id);
                res.then(function(p){
                    if(p['error']){
                        const toastOwl = new ToastOwl();
                        toastOwl.mount(document.querySelector('#container-owl-notification'));
                        toastOwl.state.title="Errore";
                        toastOwl.state.body=p['error'];
                        toastOwl.state.class="bg-danger";
                    }else{
                        self.dispatch('get_records');
                        $('#confirm').modal('hide');
                    }
                })
            });
        }
        async new(){
            this.dispatch('set_record_id', {
                'company_type': 'person',
                'id': false,
                'name': '',
                'firstname': '',
                'lastname': '',
                'street': '',
                'street2': '',
                'city': '',
                'state_id': ['', ''],
                'country_id': ['', ''],
                'zip': '',
                'reference': '',
                'email': '',
                'phone': '',
                'vat': '',
                'fiscalcode': ''
            });
            this.dispatch('reset_record_change');
            this.dispatch('set_mandatory',['firstname', 'lastname', 'country_id', 'state_id', 
                    'city', 'zip', 'street', 'street2']);
            $('#edit_address').modal({
                backdrop: 'static',
                keyboard: false
            });
            /* pulisco il form */
            $('#edit_address').find('.is-invalid').removeClass('is-invalid');
            $('form.address_edit').trigger('reset');
            $('input[name="country_id"]').val('');
            $('input[name="state_id"]').val('');
        }
        async mounted() {
            var self = this;
            this.env.bus.on("new", null, self.new.bind(self));
        }
        
    }

    return AddressesTable;

});