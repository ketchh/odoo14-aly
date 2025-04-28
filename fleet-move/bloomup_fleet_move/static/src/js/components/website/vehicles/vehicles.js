odoo.define('bloomup_fleet_move.vehicles', function (require) {
    "use strict";

    require('web.dom_ready');
    var core = require('web.core');
    var _t = core._t;
    var rpc = require('web.rpc');
    var session  = require('web.session');
    const { Component, useState, mount } = owl;
    const { xml } = owl.tags;
    const { useContext } = owl.hooks;
    var publicWidget = require('web.public.widget');

    const Loader = require('bloomup_owl_components.loader');
    const VehiclesTable = require('bloomup_fleet_move.vehicles_table');
    const Pagination = require('bloomup_owl_components.pagination');
    const AddButton = require('bloomup_owl_components.add_button');
    const TableSearch = require('bloomup_owl_components.search');

    const records_store = require('bloomup_owl_components.records_store');

    const state = records_store.state; 

    const actions = records_store.actions;

    const store = new owl.Store({ state, actions });  

    let transalteFunction = {
        'it_IT': function(str){
            const translations = {
                'Plate': "Targa",  
                'Brand': "Produttore",
                'Model': "Modello",
                'Action': "Azioni",
                "Edit Vehicle": "Modifica Veicolo",
                "New vehicle": "Nuovo Veicolo",
                "Frame Number": "Numero di Telaio",
                "Save": "Salva",
                "Cancel": "Cancel",
                "Are you sure you want to cancel the car?": "Sei sicuro di voler cancellare l'auto?",
                "By deleting the car you will no longer be able to access its data,but you will continue to see all its required movements.": "Cancellando l'auto non potrai più accedere ai suoi dati,ma continuerai a vedere tutte le sue movimentazioni richieste."
            };
            return translations[str] || str;
        }
    } 

    class Vehicles extends Component{
        static template = 'Vehicles';
        constructor(parent, props) {
            super(parent, props);
            this.useExternalXml(
                ['/bloomup_fleet_move/static/src/xml/vehicles.xml'], 
                this.env
            );
                        
            this.env.store = store;
            this.dispatch = owl.hooks.useDispatch();
            this.state = owl.hooks.useStore((state) => state);
            this.dispatch('set_model', 'fleet.vehicle');
            this.dispatch('set_fields', [
                'id',
                'license_plate',
                ['brand_id', 'name'],
                ['model_id', 'name'],
                'vin_sn'
            ]);
            this.dispatch('set_mandatory', [
                'license_plate',
                'brand_id',
                'model_id',
                'vin_sn'
            ]);
        }
        static components = { 
            Loader , 
            VehiclesTable,
        };
        async useExternalXml(urls) {
            var self = this;
            const requests = await Promise.all(urls.map(url => fetch(url)));
            const contents = await Promise.all(requests.map(req => req.text()));
            contents.forEach(xml => {
                self.env.qweb.addTemplates(xml);
            });
        }
        
        async willStart() {
            var self = this;
            this.dispatch('get_records');
            await rpc.query({
                model:'ir.http',
                method:'session_info',
                args:['']
            }).then(function(res){
                self.env.session = res;
                if (transalteFunction[self.env.session.user_context.lang]) {
                    self.env.qweb.translateFn = transalteFunction[self.env.session.user_context.lang];
                }
            });
        }        
        async mounted() {
            $('#bottom').addClass('d-none').addClass('d-md-block');
            $('#wrap .navbar').addClass('d-none').addClass('d-md-block');
            $('#top').addClass('top-mobile');

            const page = new Pagination(this);
            page.mount(document.querySelector('.o_portal_navbar '));
            $('.o_portal_navbar').addClass('navbar-app');

            const addbutton2 = new AddButton(this);
            addbutton2.mount(document.querySelector('.o_portal_navbar '));

            const search = new TableSearch();
            search.available_fields = {
                'license_plate': 'Targa',
                'brand_id': 'Produttore',
                'model_id': 'Modello',
                'vin_sn': 'Numero Telaio',
            }
            search.sort_fields = {
                'license_plate asc': 'Targa crescente',
                'license_plate desc': 'Targa decrescente',
                'brand_id asc': 'Produttore crescente',
                'brand_id desc': 'Produttore decrescente',
                'model_id asc': 'Modello crescente',
                'model_id desc': 'Modello decrescente',
                'vin_sn asc': 'Telaio crescente',
                'vin_sn desc': 'Telaio decrescente',
            }
            search.mount(document.querySelector('.o_portal_navbar '));

            /* per mobile */
            const addbutton = new AddButton(this);
            addbutton.mount(document.querySelector('#bottom-bar '));

            const page2 = new Pagination(this);
            page2.mount(document.querySelector('#bottom-bar '));

            const search2 = new TableSearch();
            search2.available_fields = {
                'license_plate': 'Targa',
                'brand_id': 'Produttore',
                'model_id': 'Modello',
                'vin_sn': 'Numero Telaio',
            }
            search2.sort_fields = {
                'license_plate asc': 'Targa crescente',
                'license_plate desc': 'Targa decrescente',
                'brand_id asc': 'Produttore crescente',
                'brand_id desc': 'Produttore decrescente',
                'model_id asc': 'Modello crescente',
                'model_id desc': 'Modello decrescente',
                'vin_sn asc': 'Telaio crescente',
                'vin_sn desc': 'Telaio decrescente',
            }
            search2.mount(document.querySelector('#bottom-bar '));
        }
        
    }

    publicWidget.registry.Vehicles = publicWidget.Widget.extend({
        selector: '.o_my_vehicle',
        start: function () {
            var self = this;
            var def = this._super.apply(this, arguments);
            const app = new Vehicles();
            app.mount(self.el);
            return def;
        },
    
        
    });

});
