odoo.define('bloomup_fleet_move.planner_fleet_move', function (require) {
    "use strict";

    require('web.dom_ready');
    var core = require('web.core');
    var _t = core._t;
    var rpc = require('web.rpc');
    const { Component, useState, mount } = owl;
    const { xml } = owl.tags;
    const ChangeColor = require('bloomup_owl_components.change_color');
    

    class FleetMoveCard extends Component{
        static template = 'PlannerFleetMoveCard';
        static components = { 
            ChangeColor
        };
        set_color(color, id){
            var self=this;
            if(id == this.record.id){
                this.current_state.bg=color; 
                $(self.el).find('.change-color').popover('hide');
                self.dispatch('set_bg', self.record.id, color);
            }
        };
        constructor(parent, props) {
            super(parent, props);
            var self=this;
            this.record = props.record;
            this.dispatch = owl.hooks.useDispatch();
            this.state = owl.hooks.useStore((state) => state);
            this.current_state = useState({
                'bg': 'bg-light'
            });
            
            if(this.state.records_bg[this.record.id]){
                this.current_state.bg = this.state.records_bg[this.record.id];
            }
            
            this.env.bus.on("set_color", null, self.set_color.bind(self));
        }
        check_insisde(event){
            var self = this; 
            var groups = $('.group');
            var found = false;            
            groups.each(function(k ,elem){
                var offset = $(elem).offset();
                var offseth = offset.top + $(elem).outerHeight();
                if(event.pageY > offset.top &&
                    event.pageY < offseth && 
                    event.pageX > offset.left){
                    found = true;
                    if(self.state.group_chosen != $(elem).attr('data-id')){
                        self.dispatch('set_group_chosen', $(elem).attr('data-id'));
                        $('.group').removeClass('bg-primary').addClass('bg-secondary');
                        $(elem).addClass('bg-primary').removeClass('bg-secondary');
                    }
                }
                if(!found){
                    self.dispatch('set_group_chosen', false);
                    $('.group').removeClass('bg-primary').addClass('bg-secondary');
                }
            });
        }
        mounted(){
            var self = this;
            $(self.el).draggable({
                containment: '.row95',
                zIndex: 100,
                drag: function( event, ui ) {
                    self.check_insisde(event);
                },
                stop: function( event, ui ) {
                    self.check_insisde(event);
                    var left_block = $('.left-block').offset();
                    var right_block = $('.right-block').offset();
                    $('.group').removeClass('bg-primary').addClass('bg-secondary');
                    if(self.state.group_chosen){
                        self.save_move();
                    }else{
                        if (event.pageX > right_block.left){
                            var originalPosition = ui.originalPosition;
                            originalPosition.top = originalPosition.top + left_block.top;
                            if (originalPosition.left < 0){
                                originalPosition.left = 0;
                            }
                            self.dispatch('set_position', self.record.id, originalPosition);
                            self.dispatch('resetRecords');
                            self.dispatch('get_records');
                        }else{
                            self.dispatch('set_position', self.record.id, ui.offset);
                        }
                    }
                }
            });
            if(this.state.records_position[this.record.id]){
                $(this.el).offset(this.state.records_position[this.record.id]);
            }
        }
        async save_move(){
            var self = this;
            var  attrs = {
                'fleet_move_id': self.record.id,
                'fleet_group_id': self.state.group_chosen,
                'event_type': 'fleet_move'
            }
            await rpc.query({
                model: 'fleet.move.event',
                method: 'create',
                args: [attrs]
            });
            self.destroy();
            //self.dispatch('hide_record', self.record.id);
            await self.dispatch('get_groups');
        }
        open(record_id){
            var self = this;
            
            var action = {
                type: 'ir.actions.act_window',
                target: 'new', 
                res_model: 'fleet.move',
                res_id: record_id,
                view_type: 'form',
                views: [[false,'form']],
                flags:{
                    mode:'readonly',
                },
                context: {create: false}
            };
            self.env.web_client.do_action(action).then(function(res){
                $('.modal').on('hidden.bs.modal', function (e) {
                    self.dispatch('resetRecords');
                    self.dispatch('get_records');
                    self.dispatch('get_groups');
                })
            });
        }
    }

    class PlannerFleetMove extends Component{
        static template = 'PlannerFleetMove';
        static components = { 
            FleetMoveCard,
        };
        constructor(parent, props) {
            super(parent, props);
            this.dispatch = owl.hooks.useDispatch();
            this.state = owl.hooks.useStore((state) => state);
        }
    }
    return PlannerFleetMove;
});