odoo.define('bloomup_owl_components.add_button', function (require) {
    "use strict";

    require('web.dom_ready');
    var core = require('web.core');
    var _t = core._t;
    var rpc = require('web.rpc');
    var session  = require('web.session');
    const { Component, useState, mount } = owl;
    const { xml } = owl.tags;

    class AddButton extends Component{
        /**
         * Bottone aggiungi, tgriggera l'evento 'add_event' nello state.
         * il componente root deve avere un listener su new
         * Il componente va inizializzato nella mounted() del componente root:
         * ESEMPIO:
         * const page = new Pagination();
           page.mount(document.querySelector('#bottom-bar '));
         * L'EVENTO VA INSERITO NEL COMPONENTE CHE LO RICHIAMA (non necessariamente il root)
         * ESEMPIO:
         * this.env.bus.on("new", null, self.new.bind(self));
         */
        static template = xml`
            <div t-transition="fade" class="closest-app-add-button mb-0 py-2">
                <button type="button" class="btn p-0 app-add-button "
                     t-on-click="new" >
                    <i class="fa fa-plus" ></i>
                </button>
            </div>
        `;

        async new(){
            var self = this;
            this.env.bus.trigger("new", this); 
        }
    }
    return AddButton;
});