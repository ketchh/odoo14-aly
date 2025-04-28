odoo.define('bloomup_fleet_move.addresses', function (require) {
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
    const Table = require('bloomup_fleet_move.addresses_table');
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
                'Name':'Nome',
                'Address': 'Indirizzo',
                'City': 'Città',
                'State': 'Provincia',
                'Zip': 'Cap',
                'Action': 'Azioni',
                'Edit Address': 'Modifica Indirizzo',
                'New Address': 'Nuovo Indirizzo',
                'Type': 'Tipo',
                'Company': 'Azienda',
                'Person': 'Privatao',
                'Company name': 'Ragione Sociale',
                'Last name': 'Cognome',
                'Country': 'Nazione',
                'Street/square': 'Via/Piazza',
                'Number': 'Civico',
                'Phone': 'Telefono',
                'Contact Person': 'Referente',
                'Vat': 'P.Iva',
                'Fiscal Code': 'Codice Fiscale',
                'Save': 'Salva',
                'Cancel': 'Annulla',
                "Are you sure you want to delete the address?": "Sei sicuro di voler cancellare l'indirizzo?",
                "By deleting the address you will no longer be able to access your data, but you will continue to see all the movements in which it appears.": "Cancellando l'indirizzo non potrai più accedere ai suoi dati,  ma continuerai a vedere tutte le movimentazioni in cui compare."
            };
            return translations[str] || str;
        }
    } 

    class Addresses extends Component{
        static template = 'Addresses';
        
        constructor(parent, props) {
            super(parent, props);
            this.useExternalXml(
                ['/bloomup_fleet_move/static/src/xml/addresses.xml'], 
                this.env
            );
            this.env.store = store;
            this.dispatch = owl.hooks.useDispatch();
            this.state = owl.hooks.useStore((state) => state);
            this.dispatch('set_model', 'fleet.partner');
            this.dispatch('set_fields', [
                'company_type',
                'id',
                'name',
                'firstname',
                'lastname',
                'street',
                'street2',
                'city',
                ['state_id', 'name'],
                ['country_id', 'name'],
                'zip',
                'reference',
                'email',
                'phone',
                'vat',
                'fiscalcode'
            ]);
        }

        static components = { 
            Loader , 
            Table
        };

        async useExternalXml(urls) {
            var self = this;
            const requests = await Promise.all(urls.map(url => fetch(url)));
            const contents = await Promise.all(requests.map(req => req.text()));
            contents.forEach(xml => {
                self.env.qweb.addTemplates(xml);
            });
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
                'name': 'Nome',
                'street': 'Indirizzo',
                'street2': 'Civico',
                'city': 'Città',
                'state_id': 'Provincia',
            }
            search.sort_fields = {
                'name asc': 'Nome crescente',
                'name desc': 'Nome decrescente',
                'street asc': 'Indirizzo crescente',
                'street desc': 'Indirizzo decrescente',
                'street2 asc': 'Civico crescente',
                'street2 desc': 'Civico decrescente',
                'city asc': 'Città crescente',
                'city desc': 'Città decrescente',
                'state_id asc': 'Provincia crescente',
                'state_id desc': 'Provincia decrescente',
            }
            search.mount(document.querySelector('.o_portal_navbar '));

            /* per mobile */
            const addbutton = new AddButton();
            addbutton.mount(document.querySelector('#bottom-bar '));

            const page2 = new Pagination();
            page2.mount(document.querySelector('#bottom-bar '));

            const search2 = new TableSearch();
            search2.available_fields = {
                'name': 'Nome',
                'street': 'Indirizzo',
                'street2': 'Civico',
                'city': 'Città',
                'state_id': 'Provincia',
            }
            search2.sort_fields = {
                'name asc': 'Nome crescente',
                'name desc': 'Nome decrescente',
                'street asc': 'Indirizzo crescente',
                'street desc': 'Indirizzo decrescente',
                'street2 asc': 'Civico crescente',
                'street2 desc': 'Civico decrescente',
                'city asc': 'Città crescente',
                'city desc': 'Città decrescente',
                'state_id asc': 'Provincia crescente',
                'state_id desc': 'Provincia decrescente',
            }
            search2.mount(document.querySelector('#bottom-bar '));
        }
        
    }

    publicWidget.registry.Addresses = publicWidget.Widget.extend({
        selector: '#my_addresses',
        start: function () {
            var self = this;
            var def = this._super.apply(this, arguments);
            const app = new Addresses();
            app.mount(self.el);
            return def;
        },
    
        
    });
  

});
