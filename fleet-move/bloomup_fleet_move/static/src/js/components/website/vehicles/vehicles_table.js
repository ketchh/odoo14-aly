odoo.define('bloomup_fleet_move.vehicles_table', function (require) {
    "use strict";

    require('web.dom_ready');
    var core = require('web.core');
    var _t = core._t;
    var rpc = require('web.rpc');
    var session  = require('web.session');
    const { Component, useState, mount } = owl;
    const { xml } = owl.tags;
    const VehicleEdit = require('bloomup_fleet_move.vehicle_edit');
    const CancelDialog = require('bloomup_owl_components.cancel_dialog');
    const ToastOwl = require('bloomup_owl_components.toast');
   
    class VehiclesTable extends Component{
        static template = 'VehiclesTable';
        constructor(parent, props) {
            super(parent, props);
            this.dispatch = owl.hooks.useDispatch();
            this.state = owl.hooks.useStore((state) => state);
        }
        static components = { 
            VehicleEdit,
            CancelDialog,
        };
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
        async edit(record_id){
            await this.dispatch('get_data_record', record_id);
            $('#edit_vehicle').modal({
                backdrop: 'static',
                keyboard: false
            });
        }
        async new(){
            this.dispatch('set_record_id', false);
            this.dispatch('reset_record_change');
            $('#edit_vehicle').modal({
                backdrop: 'static',
                keyboard: false
            });
            /* pulisco il form */
            $('#edit_vehicle').find('.is-invalid').removeClass('is-invalid');
            $('form.vehicle_edit').trigger('reset');
        }

        async mounted() {
            var self = this;
            this.env.bus.on("new", null, self.new.bind(self));
        }
        
    }

    return VehiclesTable;

});