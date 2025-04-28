odoo.define('bloomup_owl_components.pagination', function (require) {
    "use strict";

    require('web.dom_ready');
    var core = require('web.core');
    var _t = core._t;
    var rpc = require('web.rpc');
    var session  = require('web.session');
    const { Component, useState, mount } = owl;
    const { xml } = owl.tags;

    class Pagination extends Component{
        /**
         * Paginatore con le frecce destra e sinistra e il numero di pagina al centro.
         * Nello store devono essere i seguenti parametri:
         * - page: identifica la pagina
         * - next/prev: due campi true/false che dicono se in quel momento può 
         *              andare avanti o indietro (esempio finite le righe o pagina 1)
         * - una action di nome get_records che recupera tutti i records
         * - due actions next_page e prev_page.
         * Il componente va inizializzato nella mounted() del componente root:
         * ESEMPIO:
         * const page = new Pagination();
           page.mount(document.querySelector('.o_portal_navbar '));
           * L'EVENTO VA INSERITO NEL COMPONENTE CHE LO RICHIAMA (non necessariamente il root)
         * ESEMPIO:
         * this.env.bus.on("get_vehicles", null, self.get_vehicles);
         */
        static template = xml`
            <div t-transition="fade" class=" app-pagination mb-0 py-2">
                <button type="button" class="btn p-0 b-left"
                     t-on-click="prev_page" >
                    <i class="fa fa-caret-left" style="
                        font-size: 20px; 
                    "></i>
                </button>
                <button class="b-page btn p-0">
                    <b ><t t-esc="state.page"/></b></button>
                <button type="button" class="btn p-0 b-right" t-on-click="next_page" >
                    <i class="fa fa-caret-right " style="
                        font-size: 20px; 
                    "></i>
                </button>
            </div>
        `;
        constructor(parent, props) {
            super(parent, props);
            this.dispatch = owl.hooks.useDispatch();
            this.state = owl.hooks.useStore((state) => state);
        }
        next_page() {
            var self = this;
            self.dispatch('next_page'); 
            self.dispatch('get_records');
        }
        prev_page() {
            var self = this;
            self.dispatch('prev_page'); 
            self.dispatch('get_records');
        }
    }
    return Pagination;
});