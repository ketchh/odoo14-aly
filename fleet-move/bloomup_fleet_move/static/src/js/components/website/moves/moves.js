odoo.define('bloomup_fleet_move.requests', function (require) {
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
    const Pagination = require('bloomup_owl_components.pagination');
    const AddButton = require('bloomup_owl_components.add_button');
    const Table = require('bloomup_fleet_move.requests_table');
    const TableSearch = require('bloomup_owl_components.search');

    const records_store = require('bloomup_owl_components.records_store');

    const state = records_store.state; 

    const actions = records_store.actions;

    const store = new owl.Store({ state, actions });

    let transalteFunction = {
        'it_IT': function(str){
            const translations = {
                'Name': 'Nome',
                'Date': 'Data',
                'Requested Date': 'Data Richiesta',
                'Confirmed Date': 'Data Confermata',
                'Picking': 'Prelievo',
                'Delivery': 'Consegna',
                'Vehicle': 'Veicolo',
                'State': 'Stato',
                'Actions': 'Azioni',
                'Edit Move': 'Modifica movimentazione',
                'New Move': 'Nuova movimentazione',
                'Save': 'Salva',
                'Cancel': 'Annulla',
                'Error': 'Errore',
                'Are you sure you want to cancel the request?': 'Sei sicuro di voler cancellare la richiesta?',
                'By canceling the request you will continue to see it in your list.': 'Annullando la richiesta continuerai a vederla nella tua lista.'
            };
            return translations[str] || str;
        }
    } 

    class Moves extends Component{
        static template = 'MovesTemplate';
        constructor(parent, props) {
            super(parent, props);
            this.useExternalXml(
                ['/bloomup_fleet_move/static/src/xml/move.xml'], 
                this.env
            );
            this.env.store = store;
            this.dispatch = owl.hooks.useDispatch();
            this.state = owl.hooks.useStore((state) => state);
            this.dispatch('set_model', 'fleet.move');
            //this.dispatch('set_order','confirmed_date desc,request_date asc');
            this.dispatch('set_fields', [
                'id',
                'name',
                'request_date',
                'confirmed_date',
                ['vehicle_id', 'display_name'],
                ['pickup_address', 'display_name'],
                ['user_id', 'name'],
                ['delivery_address', 'display_name'],
                ['employee_id', 'name'],
                ['state', 'portal_name']
            ]);
        }
        static components = { 
            Loader,
            Table
        };
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

            const page = new Pagination();
            page.mount(document.querySelector('.o_portal_navbar '));
            $('.o_portal_navbar').addClass('navbar-app');

            const addbutton2 = new AddButton();
            addbutton2.mount(document.querySelector('.o_portal_navbar '));

            const search = new TableSearch();
            search.available_fields = {
                'request_date': 'Data Richiesta',
                'confirmed_date': 'Data Conferma',
                'vehicle_id': 'Veicolo',
                'pickup_address': 'Prelievo',
                'delivery_address': 'Consegna',
                'state': 'Stato'
            }
            search.sort_fields = {
                'request_date asc': 'Data richiesta crescente',
                'request_date desc': 'Data richiesta decrescente',
                'confirmed_date asc': 'Data conferma crescente',
                'confirmed_date desc': 'Data conferma decrescente',
                'vehicle_id asc': 'Veicolo crescente',
                'vehicle_id desc': 'Veicolo decrescente',
                'pickup_address asc': 'Prelievo crescente',
                'pickup_address desc': 'Prelievo decrescente',
                'delivery_address asc': 'Consegna crescente',
                'delivery_address desc': 'Consegna decrescente',
                'state asc': 'Stato crescente',
                'state desc': 'Stato decrescente',
            }
            search.date_field = ['confirmed_date', 'request_date'];
            search.mount(document.querySelector('.o_portal_navbar '));

            /* per mobile */
            const addbutton = new AddButton();
            addbutton.mount(document.querySelector('#bottom-bar '));

            const page2 = new Pagination();
            page2.mount(document.querySelector('#bottom-bar '));

            const search2 = new TableSearch();
            search2.available_fields = {
                'request_date': 'Data Richiesta',
                'confirmed_date': 'Data Conferma',
                'vehicle_id': 'Veicolo',
                'pickup_address': 'Prelievo',
                'delivery_address': 'Consegna',
                'state': 'Stato'
            }
            search2.sort_fields = {
                'request_date asc': 'Data richiesta crescente',
                'request_date desc': 'Data richiesta decrescente',
                'confirmed_date asc': 'Data conferma crescente',
                'confirmed_date desc': 'Data conferma decrescente',
                'vehicle_id asc': 'Veicolo crescente',
                'vehicle_id desc': 'Veicolo decrescente',
                'pickup_address asc': 'Prelievo crescente',
                'pickup_address desc': 'Prelievo decrescente',
                'delivery_address asc': 'Consegna crescente',
                'delivery_address desc': 'Consegna decrescente',
                'state asc': 'Stato crescente',
                'state desc': 'Stato decrescente',
            }
            search2.date_field = ['confirmed_date', 'request_date'];
            search2.mount(document.querySelector('#bottom-bar '));
            
        }  
        async useExternalXml(urls) {
            var self = this;
            const requests = await Promise.all(urls.map(url => fetch(url)));
            const contents = await Promise.all(requests.map(req => req.text()));
            contents.forEach(xml => {
                self.env.qweb.addTemplates(xml);
            });
        }
    }

    publicWidget.registry.Moves = publicWidget.Widget.extend({
        selector: '#my_move',
        start: function () {
            var self = this;
            var def = this._super.apply(this, arguments);
            const app = new Moves();
            app.mount(self.el);
            return def;
        },
    });
});