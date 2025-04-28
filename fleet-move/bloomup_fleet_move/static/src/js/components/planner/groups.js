odoo.define('bloomup_fleet_move.planner_fleet_move_group', function (require) {
    "use strict";

    require('web.dom_ready');
    var core = require('web.core');
    var _t = core._t;
    var rpc = require('web.rpc');
    const { Component, useState, mount } = owl;
    const { xml } = owl.tags;
    const bus = new owl.core.EventBus();

    class PlannerFleetGroup extends Component{
        static template = 'PlannerGroup';
        constructor(parent, props) {
            super(parent, props);
            this.dispatch = owl.hooks.useDispatch();
            this.state = owl.hooks.useStore((state) => state);
        }
        async cancel(event_id, obj_id){
            var self = this;
            await rpc.query({
                model: 'fleet.move.event',
                method: 'unlink',
                args: [event_id]
            });
            self.dispatch('show_record', obj_id);
            await self.dispatch('get_groups');
        }
        async delete_group(group_id){
            var self=this;
            self.state.groups.forEach(function(g, h){
                if(g.id==group_id){
                    g.event_ids.forEach(function(event, i){
                        self.cancel(event.id, event.obj.id);
                    })
                }
            });
            await rpc.query({
                model: 'fleet.move.group',
                method: 'unlink',
                args: [group_id]
            });
            await self.dispatch('get_groups');
        }
        async complete_group(group_id){
            var self = this;
            await rpc.query({
                model: 'fleet.move.group',
                method: 'write',
                args: [group_id, {'state': 'done'}]
            });
            await self.dispatch('get_groups');
        }
        open_calendar(group_id) {
            var action = {
                name: 'Planner Group',
                type: 'ir.actions.act_window',
                target: 'new', 
                res_model: 'fleet.move.event',
                view_type: 'calendar',
                views: [[false,'calendar']],
                domain: [['fleet_group_id', '=', group_id]],
                context: {
                    'edit': false, 
                    'create': false,
                    'default_fleet_group_id': group_id
                }
            };
            this.env.web_client.do_action(action);
        }
        async select_employee(employee_id, group_id){
            var self = this;
            await rpc.query({
                model: 'fleet.move.group',
                method: 'write',
                args: [group_id, {'employee_id': employee_id}]
            });
            await self.dispatch('get_groups');
        }
        async open(event_id){
            var self = this;
            var obj = false;
            self.state.groups.forEach(function(g, h){
                g.event_ids.forEach(function(event, i){
                    if(event.id == event_id){
                        obj = event.obj
                    }
                })
            });
            if (obj){
                var action = {
                    type: 'ir.actions.act_window',
                    name: obj.name,
                    target: 'new', 
                    res_model: 'fleet.move',
                    res_id: obj.id,
                    view_type: 'form',
                    views: [[false,'form']],
                    flags:{
                        mode:'readonly'
                    },
                    context: {'edit': false, 'create': false}
                };
                self.env.web_client.do_action(action);
            }
        }
    }
    return PlannerFleetGroup;
});