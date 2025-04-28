odoo.define('bloomup_owl_components.cancel_dialog', function (require) {
    "use strict";

    require('web.dom_ready');
    var core = require('web.core');
    var _t = core._t;
    var rpc = require('web.rpc');
    var session  = require('web.session');
    const { Component, useState, mount } = owl;
    const { xml } = owl.tags;

    let transalteFunction = {
        'it_IT': function(str){
            const translations = {
                'Cancel': 'Annulla',
                'Next': 'Avanti'
            };
            return translations[str] || str;
        }
    } 

    class CancelDialog extends Component{
        /**
         * Dialog per la cancellazione dell'oggetto.
         * Nello state vengono inseriti title (la domanda)
         * e il body (il testo).
         * Il bottone Annulla chiude il modal.
         * Il bottone Avanti (#cancel-go) deve essere ascoltato dal componente
         * padre che lo richiama.
         * ESEMPIO UTILIZZO TEMPLATE:
         * <CancelDialog
                title="'Sei sicuro di voler cancellare l\'auto?'"
                body="'Cancellando l\'auto non potrai più accedere ai suoi dati,
                ma continuerai a vedere tutte le sue movimentazioni richieste.'"
            /> 
         * ESEMPIO UTILIZZO CODICE DI ASCOLTO:
           $('#confirm').modal({
                backdrop: 'static',
                keyboard: false
            }).on('click', '#cancel-go', async function(){
                do_something();
            });
         */
        static template = xml`
            <div id="confirm" class="modal modal-fullscreen  fade " tabindex="-1" role="dialog" aria-labelledby="myLargeModalLabel" aria-hidden="true">
                <div class="modal-dialog ">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title"><t t-esc="state.title"/></h5>
                            <button type="button" class="close" data-dismiss="modal" aria-label="Chiudi">
                                <i class="fa fa-times text-danger" style="
                                    font-size: 20px; 
                                "></i>
                            </button>
                        </div>
                        <div class="modal-body">
                            <p><t t-esc="state.body"/></p>
                        </div>
                        <div class="modal-footer">
                            <div class="col-12 p-0">
                                <button id="cancel-go" 
                                type="button" 
                                class="btn btn-primary float-md-right d-none d-md-block"><span>Next</span></button>
                                <button type="button" 
                                class="btn btn-danger float-md-left d-none d-md-block" 
                                data-dismiss="modal"><span>Cancel</span></button>

                                <button id="cancel-go" 
                                type="button" 
                                class="btn btn-block btn-primary d-md-none"><span>Next</span></button>
                                <button type="button" 
                                class="btn btn-block btn-danger d-md-none" 
                                data-dismiss="modal"><span>Cancel</span></button>
                            </div>    
                        </div>
                    </div>
                </div>
            </div>
        `;

        state = useState({
            'title': '',
            'body': ''
        });
        
        constructor(parent, props) {
            super(parent, props);
            this.state.title = props.title;
            this.state.body = props.body;
           /* if (this.env.session.user_context.lang){
                if (transalteFunction[this.env.session.user_context.lang]) {
                    this.env.qweb.translateFn = transalteFunction[this.env.session.user_context.lang];
                }
            }*/
        }


    }
    return CancelDialog
});