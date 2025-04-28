odoo.define('bloomup_fleet_move.planner_requests', function (require) {
    "use strict";

    require('web.dom_ready');
    var core = require('web.core');
    var _t = core._t;
    var rpc = require('web.rpc');
    var session  = require('web.session');
    var web_client = require('web.web_client');
    const { Component, useState, mount } = owl;
    const { xml } = owl.tags;
    const AbstractAction = require("web.AbstractAction");
    const {
        ComponentWrapper,
        WidgetAdapterMixin,
      } = require("web.OwlCompatibility");
    
    const Loader = require('bloomup_owl_components.loader');
    const FleetMove = require('bloomup_fleet_move.planner_fleet_move');
    const Groups = require('bloomup_fleet_move.planner_fleet_move_group');
    const bus = new owl.core.EventBus();

    const TRANSLATE = {
        'it_IT': {
            'formatDate': 'dd/mm/yy',
            'monthNames': [ 
                "Gennaio", 
                "Febbraio", 
                "Marzo", 
                "Aprile", 
                "Maggio", 
                "Giugno", 
                "Luglio", 
                "Agosto", 
                "Settembre", 
                "Ottobre", 
                "Novembre", 
                "Dicembre" 
            ],
            'dayNamesMin': [ 
                "Do", 
                "Lu", 
                "Ma", 
                "Me",
                "Gi",
                "Ve",
                "Sa"
            ]
        },
        'en_US': {
            'formatDate': 'mm/dd/yy',
            'monthNames': [ 
                "January", 
                "February", 
                "March", 
                "April", 
                "May", 
                "June", 
                "July", 
                "August", 
                "September", 
                "October", 
                "November", 
                "December" 
            ],
            'dayNamesMin': [ 
                "Su", 
                "Mo", 
                "Tu", 
                "We",
                "Th",
                "Fr",
                "Sa"
            ]
        }
    };

    const state = {
        records: [],
        records_position: {},
        records_bg:{},
        records_hidden: [],
        groups: [],
        group_by: false,
        order_by: false,
        filter_by: false,
        loading: false,
        group_chosen: false,
        selectedDate: false,
        users: []
    }

    const actions = {
        set_loading({state}, loading){
            state.loading = loading;
        },
        async get_records({state}){
            state.loading=true;
            return rpc.query({
                model: 'fleet.move',
                method: 'search_planner',
                args: [state.selectedDate],
            }).then(function (res) {
                state.records = res;
                state.loading=false;
            });
        },
        async get_groups({state}){
            state.loading = false;
            var user_used = [];
            await rpc.query({
                model: 'fleet.move.group',
                method: 'search_group',
                args: []
            }).then(
                function(res){
                    state.groups = res;
                    var added = [];
                    res.forEach(function(k, v){
                        k.event_ids.forEach(function(e, i){
                            if(! added.includes(e.obj.id)){
                                state.records_hidden.push(e.obj);
                                added.push(e.obj.id);
                            }
                        })
                    });
                    state.groups.forEach(function(group, k){
                        if(group.employee_id){
                            user_used.push(group.employee_id[0]);
                        }
                    });
                    
                }
            );
            await rpc.query({
                model: 'hr.employee',
                method: 'search_read',
                args: [[['id','not in',user_used]],['id','name']]
            }).then(function(res){
                state.users = res;
            });
        },
        set_group_chosen({state}, group){
            state.group_chosen = group;
        },
        show_record({state}, event_id){
            var found = -1;
            state.records_hidden.forEach(function(elem, i){
                if(elem.id == event_id){
                    found = i;
                    return
                }
            });
            if(found >= 0){
                var actual = state.records_hidden[found]['confirmed_date'];
                actual = moment(actual)
                var start = state.selectedDate + ' 00:00:00';
                var stop = state.selectedDate + ' 23:59:59';
                start = moment(start);
                stop = moment(stop);
                if(actual.isBetween(start, stop)){
                    var recs = state.records_hidden[found];
                    state.records.push({
                        'id': recs['id'],
                        'name': recs['name'],
                        'confirmed_date': recs['confirmed_date'],
                        'delivery_address': recs['delivery_address'],
                        'partner_id': recs['partner_id'],
                        'pickup_address': recs['pickup_address'],
                        'user_id': recs['user_id'],
                        'vehicle_id': recs['vehicle_id'],
                        'bg': recs['bg']
                    });
                }
                state.records_hidden.splice(found,1);
            }
        },
        hide_record({state}, event_id){
            var found = -1;
            var new_Array = [];
            state.records.forEach(function(elem, i){
                if(elem.id != event_id){
                    new_Array.push({
                        'id': elem['id'],
                        'name': elem['name'],
                        'confirmed_date': elem['confirmed_date'],
                        'delivery_address': elem['delivery_address'],
                        'partner_id': elem['partner_id'],
                        'pickup_address': elem['pickup_address'],
                        'user_id': elem['user_id'],
                        'vehicle_id': elem['vehicle_id'],
                        'bg': elem['bg']
                    })
                }
            });
            state.records = new_Array;
        },
        setselectedDate({state}, date){
            state.selectedDate = date.getFullYear()+'-'+("0" + (date.getMonth() + 1)).slice(-2)+'-'+date.getDate();
        },
        resetRecords({state}){
            state.records = [];
        },
        set_bg({state}, record, bg){
            state.records_bg[record] = bg;
        },
        set_position({state}, record, offset){
            state.records_position[record] = offset;
        }
    }

    const store = new owl.Store({ state, actions });  
    
    class Planner extends Component{
        static template = 'PlannerApp';
        static components = { 
            Loader , 
            FleetMove,
            Groups
        };
        text = useState(TRANSLATE['en_US']);

        constructor(parent, props) {
            super(parent, props);
            this.env.store = store;
            this.dispatch = owl.hooks.useDispatch();
            this.state = owl.hooks.useStore((state) => state);
            this.env.bus = bus;
            this.env.web_client = web_client;
        }
        async willStart() {
            var self = this;
            self.env.session = session;
            if(TRANSLATE[self.env.session.user_context.lang]){
                self.text = TRANSLATE[self.env.session.user_context.lang];
            }
            await self.dispatch('get_records');
            await self.dispatch('get_groups');
        }  
        mounted(){
            var self=this;
            $('#datepicker').datepicker({
                dateFormat: self.text['formatDate'],
                monthNames: self.text['monthNames'],
                dayNamesMin: self.text['dayNamesMin'],
                onSelect: function(){
                    var currentDate = $( "#datepicker" ).datepicker( "getDate" );
                    self.dispatch('setselectedDate', currentDate);
                    self.dispatch('resetRecords');
                    self.dispatch('get_records');
                }
            });
            $('#datepicker').datepicker( "setDate", moment().format('L') );
            var currentDate = $( "#datepicker" ).datepicker( "getDate" );
            self.dispatch('setselectedDate', currentDate);
        }
        async add_group(){
            var self =  this;
            var attrs = {
                'user_id': self.env.session.uid
            }
            await rpc.query({
                model: 'fleet.move.group',
                method: 'create',
                args: [attrs]
            });
            await self.dispatch('get_groups');
        }
        
    }

    const ClientAction = AbstractAction.extend(WidgetAdapterMixin, {
        start() {
          const component = new ComponentWrapper(this, Planner);

          $(this.el.querySelector(".o_content")).addClass('o_web_planner')
    
          return component.mount(this.el.querySelector(".o_content"));
    
        },
    
      });
    
    
    
    core.action_registry.add("planner_action_client", ClientAction);
    
     return ClientAction;
    
});