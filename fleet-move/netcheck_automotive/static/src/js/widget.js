odoo.define('netcheck_automotive.rvr', function (require) {
    "use strict";
    
    require('web.dom_ready');
    const { Component, useState, mount } = owl;
    const AbstractField = require('web.AbstractFieldOwl');
    const fieldRegistry = require('web.field_registry_owl');
    var session = require('web.session');
    var rpc = require('web.rpc');
    var core = require('web.core');
    var Dialog = require('web.Dialog');
    var _t = core._t;   
    const RvR = require('netcheck_2.rvr');

    class DamageWidget extends Component{
        static template = 'DamageWidget';
        constructor(parent, props) {
            super(parent, props);
            this.env.session = session;
            this.detail = false;
        }
        async open_damage(damage_id){
            var self = this;
            if (self.detail){
                self.detail.destroy();
            }
            var damage = false;
            self.props.damages.forEach(function(elem){
                if(elem.id == damage_id){
                    damage = elem;
                }
            });
            var images = false;
            await rpc.query({
                model: "checklist.damage.image",
                method: "read",
                args:[
                    damage.images
                ]
            }).then(function(res){
                images= res;
            });

            var props = {
                'damage': damage,
                'images': images
            }

            var detail = new DamageDetail(self, props);
            detail.mount(self.el);
            self.detail = detail;
        }
    }

    class DamageDetail extends Component{
        static template = 'DamageDetail';
        constructor(parent, props) {
            super(parent, props);
        }
        
        async open_damage_image(img_id){
            await rpc.query({
                model: "checklist.damage.image",
                method: "read",
                args: [img_id]
            }).then(function(res){
                var html = '<img src="' + res[0].raw_value + '" \
                class="img-fluid rounded mx-auto d-block"/>';
                var dialog = new Dialog(this, {
                    size: 'large',
                    buttons: [{
                        text: _t("Close"),
                        classes : "btn-primary",
                        close:true,
                    }], 
                    title: "Image",
                    $content: html
                });
                dialog.open();
            });
        }
    }

    class AlyRvr extends RvR{
        constructor(...args){
            super(...args);
            var self = this;
        }
        async return_html_value(){
            var self = this;
            await super.return_html_value();
            
            if(self.field_type == 'damage'){
                var number = 0;
                await rpc.query({
                    model: "checklist.line",
                    method: "read",
                    args: [self.recordData['checklist_line_id'].res_id, ['number_of_damages']]
                }).then(function(res){
                    if(res){
                        number = res[0].number_of_damages;
                    }
                });
                self.html_value = '<a href="#" class="damages" \
                style="white-space:nowrap;\
                float:left;">\
                <i class="fa fa-list" ></i></a>';
                if (number > 0){
                    self.html_value += ' ';
                    if(number == 1){
                        self.html_value += number + ' ' + _t('Damage');
                    }else{
                        self.html_value += number + ' ' + _t('Damages');
                    }
                }

            }
        }
        async mounted(){
            await super.mounted();
            var self = this;
            $(self.el).on('click', '.damages', function(e){
                e.stopPropagation();
                e.preventDefault();
                self.get_images();
            });
        }
        async get_images(){
            var self = this;
            /*find damage images*/
            var damages = false;
            await rpc.query({
                model: "checklist.damage",
                method: 'search_read',
                args: [
                    [
                        ['registration_id', '=', 
                        self.recordData['id']]
                    ]
                ]
            }).then(function(res){
                if(res){
                    damages = res;
                }
            });
            var nod = damages.length;
            if (damages.length == 1){
                nod += ' ' + _t('Damage');
            }else{
                nod += ' ' + _t('Damages');
            }
            var props = {
                'image': self.value,
                'damages': damages,
                'number_of_damages': nod
            }
            var DamageWidgetX = new DamageWidget(self, props);
            
            var dialog = new Dialog(this, {
                size: 'large',
                buttons: [{
                    text: _t("Close"),
                    classes : "btn-primary",
                    close:true,
                }], 
                title: self.recordData['checklist_line_id'].data.display_name,
                $content: ''
            });
            dialog.opened().then(function () {
                DamageWidgetX.mount(dialog.el);
            });
            dialog.open();
        }
        
    }

    fieldRegistry.add('rvr_widget', AlyRvr);
})