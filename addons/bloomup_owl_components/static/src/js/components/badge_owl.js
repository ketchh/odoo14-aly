odoo.define('bloomup_owl_components.badge_owl', function (require) {
    "use strict";

    require('web.dom_ready');
    var core = require('web.core');
    var _t = core._t;
    var rpc = require('web.rpc');
    var session  = require('web.session');
    const { Component, useState, mount } = owl;
    const { xml } = owl.tags;

    class BadgeOwl extends Component{
        /**
         * Component badge nella dashboard del my/account
         * Per ogni riga va aggiunto. Le righe vanno messe in un template odoo standard.
         * Cosi come il badge all'interno del quale va in uno span con class zero
         * lo spinner.
         * La funzione get_badge è nel python ed è documentata li.
         * ESEMPIO TEMPLATE:
         * <a class="list-group-item list-group-item-action d-flex 
            align-items-center justify-content-between " 
            href="/my/vehicles" title="Veicoli"
            >
                Veicoli
                <span class="badge 
                badge-secondary badge-pill badge-owl" 
                data-model="fleet.vehicle" data-field="owner_id">
                    <span class="zero"><i class="fa fa-spin fa-spinner"/></span>
                </span>
            </a>
         */
        static template = xml`
            <span><t t-esc="state.count"/></span>
        `;

        state = useState({
            'count': 0
        });

        async mounted() {
            var self=this;
            var model=$(self.el).parent().attr('data-model');
            var field=$(self.el).parent().attr('data-field');
            
            $('.zero').hide();
            await rpc.query({
                model: 'res.partner',
                method: 'get_badge',
                args: [model, field],
            }).then(function (res) {
                self.state.count = res;
            })
        }
    }
    
    if($('.badge-owl').length){
        owl.utils.whenReady().then(() => {
            
            $('.badge-owl').each(function(i,el){
                var app = new BadgeOwl();
                app.mount(el);
            })
            
        });
    }
});