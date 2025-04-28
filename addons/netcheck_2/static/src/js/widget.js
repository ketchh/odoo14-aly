odoo.define('netcheck_2.rvr', function (require) {
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

    class RvR extends AbstractField {
        static supportedFieldTypes = ['char'];
        static template = 'RvR';
        constructor(...args){
            super(...args);
            var self = this;
            self.env.session = session;
            self.field_type = false;
            self.html_value = _t('<p>Empty<p>');
            self.photo_type = ['photo', 'signature'];
            var attrs = JSON.parse(self.attrs.attrs.replaceAll("'",'"'));
            if(attrs){
                if(attrs.field_type){
                    self.field_type = this.recordData[attrs.field_type];
                }
            }
            
        }
        async willStart() {
            var self = this;
            await self.return_html_value();
        }
        async return_html_value(){
            var self = this;
            if(['string'].includes(self.field_type)){
                self.html_value = self.value;
            }
            if(self.field_type == 'integer'){
                self.html_value = parseInt(self.value);
            }
            if(self.field_type == 'float'){
                var number = parseFloat(self.value);
                self.html_value = number.toLocaleString(
                    self.env.session.user_context.lang.replace('_','-')
                );
            }
            if(self.field_type == 'boolean'){
                if(['true', 'True', '1', 1].includes(self.value)){
                    self.html_value = '<i class="fa fa-check-square-o"></i>';
                }else{
                    self.html_value = '<i class="fa fa-square-o"></i>';
                }
            }
            if(self.photo_type.includes(self.field_type)){
                self.html_value = '<a href="#" class="view" style="white-space:nowrap;\
                float:left; margin-right: 10px">\
                <i class="fa fa-file-image-o" ></i></a>\
                <a href="#" class="download" style="white-space:nowrap; float:left">\
                <i class="fa fa-download" ></i></a>';
            }
            if(self.field_type == 'video'){
                self.html_value = '<a href="#" class="view" style="white-space:nowrap;\
                float:left; margin-right: 10px">\
                <i class="fa fa-file-video-o" ></i></a>\
                <a href="#" class="download" style="white-space:nowrap; float:left">\
                <i class="fa fa-download" ></i></a>';
            }
            if(self.field_type == 'audio'){
                self.html_value = '<a href="#" class="view" style="white-space:nowrap;\
                float:left; margin-right: 10px">\
                <i class="fa fa-file-audio-o" ></i></a>\
                <a href="#" class="download" style="white-space:nowrap; float:left">\
                <i class="fa fa-download" ></i></a>';
            }
            if(self.field_type == 'datetime'){
                var dt_passed = new Date(self.value + ' GMT');
                /*console.log(dt_passed.toUTCString());
							  console.log(dt_passed);
                var year = dt_passed.getFullYear();
                var month = dt_passed.getMonth();
                var day = dt_passed.getDate();
                var hour = dt_passed.getHours();
                var minute = dt_passed.getMinutes();
                var seconds = dt_passed.getSeconds();
                var dt = new Date(Date.UTC(year, month, day, hour, minute, seconds));
                var options = { timeZone: self.env.session.user_context.tz};*/
                dt = dt_passed;
                self.html_value = dt.toLocaleDateString(
                    self.env.session.user_context.lang.replace('_','-')
                ) + ' ' + dt.toLocaleTimeString(
                    self.env.session.user_context.lang.replace('_','-'),
                    options
                );
            }
            if(self.field_type == 'date'){
                var dt = new Date(self.value);
                var options = { timeZone: self.env.session.user_context.tz};
                self.html_value = dt.toLocaleDateString(
                    self.env.session.user_context.lang.replace('_','-')
                );
            }
            if(self.field_type == 'selection'){
                var line_id = self.recordData['checklist_line_id'].res_id;
                var model = self.recordData['checklist_line_id'].model;
                var line_data = false;
                await rpc.query({
                    model: model,
                    method: 'read',
                    args: [line_id]
                }).then(function(res){
                    if(res){
                        line_data = res[0];
                    }
                });
                if(line_data.option_ids_string.includes('option_selection_model')){
                    var ids = self.value.split(',');
                    var ids = ids.map(function (x) { 
                        return parseInt(x, 10); 
                    });
                    await rpc.query({
                        model: line_data.name_model_string,
                        method: 'read',
                        args: [ids]
                    }).then(function(response){
                        if(response){
                            var html = response.map(function(x){
                                return x.display_name;
                            });
                            self.html_value = html.toString();
                        }
                    })
                }else{
                    var ids = self.value.split(',');
                    var ids = ids.map(function (x) { 
                        return parseInt(x, 10); 
                    });
                    await rpc.query({
                        model: 'checklist.line.option.selection',
                        method: 'read',
                        args: [ids]
                    }).then(function(response){
                        if(response){
                            var html = response.map(function(x){
                                return x.display_name;
                            });
                            self.html_value = html.toString();
                        }
                    })
                }
            }
        }
        async mounted(){
            var self = this;
            $(self.el).on('click', '.view', function(e){
                e.stopPropagation();
                e.preventDefault();
                var html = _t('<p>Empty<p>');
                if(self.photo_type.includes(self.field_type)){
                    html = '<img src="' + self.value + '" \
                    class="img-fluid rounded mx-auto d-block"/>';
                }
                if(self.field_type == 'video'){
                    html = '<div class="embed-responsive embed-responsive-16by9">\
                    <iframe class="embed-responsive-item" src="'+ self.value +'"></iframe>\
                  </div>';
                }
                if(self.field_type == 'audio'){
                    html = '<audio\
                        controls\
                        src="'+ self.value +'" class="align-self-center">\
                            Your browser does not support the\
                            <code>audio</code> element.\
                    </audio>';
                }
                var dialog = new Dialog(this, {
                    size: 'large',
                    buttons: [{
                        text: _t("Close"),
                        classes : "btn-primary",
                        close:true,
                    }],
                    title: self.recordData['checklist_line_id'].data.display_name,
                    $content: html
                });
                dialog.open();
            });

            $(self.el).on('click', '.download', function(e){
                e.stopPropagation();
                e.preventDefault();
                if(self.field_type == 'photo'){
                    var name = 'image-' + self.resId;
                }
                if(self.field_type == 'video'){
                    var name = 'video-' + self.resId;
                }
                if(self.field_type == 'audio'){
                    var name = 'audio-' + self.resId;
                }
                var a = document.createElement('a');
                a.href = self.value;
                a.download = name;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
            })
        }
    }

    fieldRegistry.add('rvr_widget', RvR);

    return RvR;
});
