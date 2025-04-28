odoo.define('bloomup_owl_components.change_color', function (require) {
    "use strict";

    require('web.dom_ready');
    var core = require('web.core');
    var _t = core._t;
    var rpc = require('web.rpc');
    var session  = require('web.session');
    const { Component, useState, mount } = owl;
    const { xml } = owl.tags;

    class ChangeColor extends Component{
        /**
        Mette un menu con tre pallini orizzontali che apre un popover con dentro i colori
        di bootstrap.
        Triggera un evento set_color che va configurato nel componente padre:
        this.env.bus.on("set_color", null, self.set_color.bind(self));
        Le props da passare sono class e id:
            - class: le classi che acquisice il div padre. es: col-1 p-0
            - id: identificativo del componente padre (id numerico o anche testuale)
        */
        static template = xml`
            <div t-transition="fade" t-att-class="class">
                <span style="cursor:pointer; padding:5px"
                class="change-color p-0 float-right" 
                ><i class="fa
                fa-ellipsis-h"></i></span>
            </div>
        `;
        constructor(parent, props) {
            super(parent, props);
            this.class = props.class;
            this.id = props.id;
            this.colors = [
                'bg-primary',
                'bg-secondary',
                'bg-success',
                'bg-danger',
                'bg-warning',
                'bg-info',
                'bg-light',
                'bg-dark'
            ];
            this.chosen = false;
        }
        async chose(color_id){
            this.chosen = this.colors[color_id];
            this.env.bus.trigger('set_color', this.chosen, this.id);
        }
        async mounted(){
            var self = this;
            $(self.el).find(".change-color").popover({
                html : true, 
                placement: 'bottom',
                container: self.__owl__.parent.el,
                content: function() {
                    var style="width:30px; height: 30px; margin:4px;";
                    var html = "<div class='row' style='width:152px'>";
                    self.colors.forEach(function(k,v){
                        html += "<div class='col-3 p-0'><button class='p-0 chose border btn "+k+"' style='"+style+"' data-id='"+v+"' ></button></div>";
                    });
                    html += "</div>"
                    return html;
                },
            });
            $(self.el).find(".change-color").on('shown.bs.popover', function () {
                var btns = document.getElementsByClassName("chose");
                for (var i=0; i < btns.length; i++) {
                    btns[i].onclick = function(e) { 
                        var color_id = $(e.target).attr('data-id');
                        self.chose(color_id);
                    };
                }
            });
            
        }
    }
    return ChangeColor;
});