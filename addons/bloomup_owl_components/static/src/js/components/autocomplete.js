odoo.define('bloomup_owl_components.autocomplete', function (require) {
    "use strict";

    require('web.dom_ready');
    var core = require('web.core');
    var _t = core._t;
    var rpc = require('web.rpc');
    var session  = require('web.session');
    const { Component, useState, mount } = owl;
    const { xml } = owl.tags;

    class Autocomplete extends Component{
        /**
         * Crea un input autocomplete con jquery autocomplete.
         * - placeholder: eventualre placheolder dell'input
         * - model: modello su cui fare la query
         * - results: sono i risultati dell'autocomplete
         * - value: valore dell'input
         * - name: name dell'input
         * ### Dipendenza da un altro campo.
         * - depends_name: name dell'input da cui dipende la query
         * - depends_field: nome field del modello da cui dipende
         * - depends_model: nome modello da cui dipende
         * ESEMPIO:
         * <Autocomplete model="'fleet.vehicle.model"
                placeholder="'MODELLO'" 
                name="'model_id'"
                depends_model="'fleet.vehicle.model.brand'"
                depends_name="'brand_id'"
                depends_field="'brand_id'"/>
         */
        static template = xml`
            <input type="text" class="form-control text-uppercase" 
            t-att-placeholder="state.placeholder"
            t-att-value="state.value"
            t-att-name="state.name"/>
        `;
        state = useState({
            'placeholder': '',
            'model': false,
            'results' : {},
            'value': '',
            'name': '',
            'depends_name': false,
            'depends_field': false,
            'depends_model': false,
        });
        
        constructor(parent, props) {
            super(parent, props);
            if(props.state){
                this.state.model = props.state.model;
                this.state.placeholder = props.state.placeholder;
            }else{
                this.state.model = props.model;
                this.state.placeholder = props.placeholder;
            }
            if (props.value){
                this.state.value = props.value;
            }
            this.state.name = props.name;
            if (props.depends_name){
                this.state.depends_name = props.depends_name;
            }
            if (props.depends_field){
                this.state.depends_field = props.depends_field;
            }
            if (props.depends_model){
                this.state.depends_model = props.depends_model;
            }
        }

        async mounted() {
            var self = this;
            $(this.el).autocomplete({
                source:function( request, response ) {
                    
                    var depends_value = $('input[name="'+self.state.depends_name+'"]').val();
                    
                    rpc.query({
                        model: 'res.partner',
                        method: 'owl_autocomplete',
                        args: [
                            self.state.model, 
                            request.term, 
                            self.state.depends_model, 
                            self.state.depends_field, 
                            depends_value
                        ],
                    }).then(function (res) {
                        self.state.results[ request.term ] = res;
                        response( res );
                    });
                }
            });
        }

    }
    return Autocomplete
});