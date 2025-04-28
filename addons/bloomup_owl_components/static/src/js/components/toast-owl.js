odoo.define('bloomup_owl_components.toast', function (require) {
    "use strict";

    require('web.dom_ready');
    var core = require('web.core');
    var _t = core._t;
    var rpc = require('web.rpc');
    var session  = require('web.session');
    const { Component, useState, mount } = owl;
    const { xml } = owl.tags;

    class ToastOwl extends Component{    
        /**
         * Toast notification
         * Si usa dichiarandolo direttamente al momento (in modo da avere più toast)
         * - title: il titolo
         * - body: il testo
         * - class: bg-danger se errore, bg-success etc....(bootstrap classes)
         */
        static template = xml`
        <div t-att-class="'toast '+ state.class" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header">
                <strong class="mr-auto"><t t-esc="state.title"/></strong>
                <button type="button" class="ml-2 mb-1 close" data-dismiss="toast" aria-label="Close">
                    <span aria-hidden="false"><i class="fa fa-times text-danger"></i></span>
                </button>
            </div>
            <div class="toast-body">
                <t t-esc="state.body"/>
            </div>
        </div>
        `;

        state = useState({
            'title': '',
            'body': '',
            'class': ''
        })

        async mounted(){
            var self = this;
            $(this.el).toast({'delay':2000});
            $(this.el).toast('show');
            var container = $(this.el).parent();
            $(this.el).on('shown.bs.toast', function () {
                if(self.env.device.isMobile){
                    container.addClass('flex-column-reverse');
                    container.css('display', 'flex').fadeIn();
                }else{
                    container.fadeIn()
                    container.removeClass('flex-column-reverse');
                }
                
            });
            $(this.el).on('hidden.bs.toast', function () {
                if($(".toast").is(":visible")){
                }else{
                    container.fadeOut();
                    container.removeClass('flex-column-reverse');
                }
            })
        }
    }
    return ToastOwl
});