odoo.define('bloomup_fleet_move.requests_table', function (require) {
    "use strict";

    require('web.dom_ready');
    var core = require('web.core');
    var _t = core._t;
    var rpc = require('web.rpc');
    var session  = require('web.session');
    const { Component, useState, mount } = owl;
    const { xml } = owl.tags;
    const CancelDialog = require('bloomup_owl_components.cancel_dialog');
    const RequestEdit = require('bloomup_fleet_move.moves_edit');
    const ToastOwl = require('bloomup_owl_components.toast');

    class MoveTable extends Component{
        static template = 'MoveTable';
        constructor(parent, props) {
            super(parent, props);
            this.dispatch = owl.hooks.useDispatch();
            this.state = owl.hooks.useStore((state) => state);
            
        }
        static components = { 
            CancelDialog,
            RequestEdit
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
                        toastOwl.state.title=self.env.qweb.translateFn("Error");
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
            $('#edit_move').modal({
                backdrop: 'static',
                keyboard: false
            });
        }
        async new(){
            this.dispatch('set_record_id', false);
            this.dispatch('reset_record_change');
            $('#edit_move').modal({
                backdrop: 'static',
                keyboard: false
            });
            /* pulisco il form */
            $('#edit_move').find('.is-invalid').removeClass('is-invalid');
            $('form.edit_move').trigger('reset');
        }
        async mounted() {
            var self = this;
            this.env.bus.on("new", null, self.new.bind(self));
            this.dispatch('set_mandatory', [
                'vehicle_id', 
                'pickup_address',
                'delivery_address'
            ]);
        }
        async set_order(field){
            console.log(field)
        }
    }
    return MoveTable
});