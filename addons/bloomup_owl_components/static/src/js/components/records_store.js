odoo.define('bloomup_owl_components.records_store', function (require) {
    "use strict";

    require('web.dom_ready');
    var core = require('web.core');
    var _t = core._t;
    var rpc = require('web.rpc');
    var session  = require('web.session');
    const { Component, useState, mount } = owl;
    const { xml } = owl.tags;
    const { useContext } = owl.hooks;
    
    const ToastOwl = require('bloomup_owl_components.toast');

    const state = {
        records: [],
        page: 1,
        next: false,
        prev: false,
        loading: true,
        record_id: false,
        record_change: {},
        limit: 8,
        order: 'id desc',
        model: false,
        fields: ['id', 'name'],
        fields_mandatory: []
    }

    const actions = {
        set_model({state}, model){
            state.model = model;
        },
        set_fields({state}, fields){
            state.fields = fields;
        },
        set_mandatory({state}, fields){
            state.fields_mandatory = fields;
        },
        async get_records({state}){
            state.loading = true;
            await rpc.query({
                model: 'res.partner',
                method: 'get_records',
                args: [
                    state.model,
                    state.fields,
                    state.page,
                    state.order,
                    state.limit
                ],
            }).then(function (res) {
                if (res){
                    state.next = res['next'];
                    state.prev = res['prev'];
                    state.records = res['records'];
                }
                state.loading = false;
            });
        },
        async cancel_record({state}, record_id){
            state.loading = true;
            var res = await rpc.query({
                model: 'res.partner',
                method: 'cancel_record',
                args: [state.model, record_id],
            });
            return res;
        },
        async get_data_record({state}, record_id){
            state.loading = true;
            state.record_id = false;
            state.record_change = {};
            await rpc.query({
                model: 'res.partner',
                method: 'get_data_record',
                args: [state.model, record_id, state.fields],
            }).then(function(data){
                state.record_id = data;
                state.record_change = {'id': data['id']};
                state.loading = false;
            });
        },
        async save({state}){
            var error = false;
            $('.invalid-feedback').remove();
            $('.is-invalid').removeClass('is-invalid');
            state.fields_mandatory.forEach(element => {
                var value = $('[name="'+element+'"]').val();
                if(!value){
                    $('[name="'+element+'"]').addClass('is-invalid');
                    var html = "<div class='invalid-feedback'>Il campo è obbligatorio.</div>";
                    $("[name='"+element+"']").after(html);
                    error = true;
                }
            });
            if (error){
                return false;
            }
            state.loading = true;
            await rpc.query({
                model: 'res.partner',
                method: 'save_record',
                args:[
                    state.model,
                    state.record_change
                ]
            }).then(function(res){
                if(!res){
                    const toastOwl = new ToastOwl();
                    toastOwl.mount(document.querySelector('#container-owl-notification'));
                    toastOwl.state.title="Errore";
                    toastOwl.state.body="Si è verificato un errore imprevisto";
                    toastOwl.state.class="bg-danger";
                }else{
                    if(res['validation_errors']){
                        var arr = res['validation_errors'];
                        $.each(arr, function(key, value){
                            $("[name='"+key+"']").addClass('is-invalid');
                            var html = "<div class='invalid-feedback'>"+value+"</div>";
                            $("[name='"+key+"']").after(html);
                        });
                    }
    
                    if (res['error']){
                        const toastOwl = new ToastOwl();
                        toastOwl.mount(document.querySelector('#container-owl-notification'));
                        toastOwl.state.title="Errore";
                        toastOwl.state.body=res['error'];
                        toastOwl.state.class="bg-danger";
                    }
                    if (res['success']){
                        const toastOwl = new ToastOwl();
                        toastOwl.mount(document.querySelector('#container-owl-notification'));
                        toastOwl.state.title="Successo";
                        toastOwl.state.body=res['success'];
                        toastOwl.state.class="bg-success";
                        $('.modal').modal('hide');
                    }
                }
                state.loading = false;
            });
        },
        async change({state}, name, value){
            if(!state.record_change){
                state.record_change={};
            }
            state.record_change[name] = value;
        },
        next_page({state}){
            if(state.next){
                state.page = state.page + 1;
            }
        },
        prev_page({state}){
            if(state.prev){
                state.page = state.page - 1;
            }
        },
        set_record_id({state}, value){
            state.record_id = value;
        },
        reset_record_change({state}){
            state.record_change = {};
        },
        set_record_change({state}, param, value){
            state.record_change[param] = value;
        }
    }

    return {state, actions};
});