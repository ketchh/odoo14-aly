odoo.define('netcheck_2.precompiled', function (require) {
    "use strict";
    
    require('web.dom_ready');
    const { Component, useState, mount } = owl;
    const AbstractField = require('web.AbstractFieldOwl');
    const fieldRegistry = require('web.field_registry_owl');
    var session = require('web.session');
    var rpc = require('web.rpc');
    var core = require('web.core');
    var ModelFieldSelector = require("web.ModelFieldSelector");
    var _t = core._t; 
    var web_client = require('web.web_client');
    var Widget = require("web.Widget");
    
    class PrecompiledWidget extends AbstractField {
        static supportedFieldTypes = ['char'];
        static template = 'PrecompiledWidget';
        constructor(...args){
            super(...args);
            if (this.isEmpty){
                this.chain = 'display_name';
            }else{
                this.chain = this.value;
            }
            
            this.fieldSelector = false;
            this.fieldSelectorModel = $('div[name="ref_doc_id"] select').val();
        }
        setFieldSelectorModel(){
            var self = this;
            self.fieldSelector = new ModelFieldSelector(
                web_client,
                self.fieldSelectorModel,
                self.chain !== undefined ? self.chain.toString().split(".") : [],
                {
                    'readonly': 0,
                    'filters': {
                        'searchable': false 
                        //all the fields are visible (e.g. display_name)
                    }
                }
            );
            /* override _hidePopover function (ModelFieldSelector)
            *  when field is selected in ModelFieldSelector,
            *  chain is saved in current PrecompiledWidget.  
            * 
            *  var hidepopover is the old original function
            *  binding to self.fieldSelector  
            */
            var hidepopover = self.fieldSelector._hidePopover.bind(self.fieldSelector);
            self.fieldSelector._hidePopover = function(){
                self._setValue(this.chain.join('.'));
                hidepopover();
            }
            if(self.mode == 'edit'){
                self.fieldSelector.appendTo(self.el);
                if (self.isEmpty){
                    self.fieldSelector._hidePopover()
                }
            }else{
                var html = self.value;
                $(self.el).html(html);
            }
        }
        mounted(){
            var self = this;
            if(!this.attrs.modifiersValue.invisible){
                if(this.recordData['ref_doc_id']){
                    self.fieldSelectorModel = $('div[name="ref_doc_id"] select').val();
                    self.setFieldSelectorModel();
                }
                /* Listen onchange on ref_doc_id */
                $('div[name="ref_doc_id"] select').on('change', function(){
                    self.chain = 'display_name';
                    self.fieldSelectorModel = $('div[name="ref_doc_id"] select').val();
                    if(self.fieldSelector){
                        self.fieldSelector.destroy();
                    }
                    self.setFieldSelectorModel();
                });
            }
        }
    }
    fieldRegistry.add('precompiled_widget', PrecompiledWidget);
});