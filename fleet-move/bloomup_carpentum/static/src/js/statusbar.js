odoo.define('bloomup_carpentum.statusbar', function (require) {
    "use strict";
    var AbstractField = require('web.AbstractField');
    var core = require('web.core');
    var rpc = require('web.rpc');
    var qweb = core.qweb;
    var registry = require('web.field_registry');
    /**
     * Crea una statusbar "bloomupstatusbar"
     * che controlla i campi code_tipo_entrata_veicolo e stato_incarico
     * dell'incarico per capire che tipologia è e visualizza solo
     * le fasi associate a questa tipologia.
     */

    var BloomupFieldStatus = AbstractField.extend({
        className: 'o_statusbar_status',
        events: {
            'click button:not(.dropdown-toggle)': '_onClickStage',
        },
        specialData: "_fetchSpecialStatus",
        supportedFieldTypes: ['selection', 'many2one'],
        /**
         * @override init from AbstractField
         */
        init: function () {
            this._super.apply(this, arguments);
            
            this._onClickStage = _.debounce(this._onClickStage, 300, true); // TODO maybe not useful anymore ?
    
            // Retro-compatibility: clickable used to be defined in the field attrs
            // instead of options.
            // If not set, the statusbar is not clickable.
            try {
                this.isClickable = !!JSON.parse(this.attrs.clickable);
            } catch (_) {
                this.isClickable = !!this.nodeOptions.clickable;
            }
        },
        /* cerca fasi corrette */
        willStart: function() {
            var self = this;
            var move_type = self.record.data.move_type.res_id;
            
            self.phase_ok = [];
            var def = rpc.query({
                model: 'fleet.move.status',
                method: 'search_read',
                domain: [['move_type','=',move_type]],
            }).then(function(res){
                self.phase_ok = res;
                self._setState();
            });
            
            return Promise.all([def, this._super.apply(this, arguments)]);
    
        },
        //--------------------------------------------------------------------------
        // Public
        //--------------------------------------------------------------------------
    
        /**
         * Returns false to force the statusbar to be always visible (even the field
         * it not set).
         *
         * @override
         * @returns {boolean} always false
         */
        isEmpty: function () {
            return false;
        },
    
        //--------------------------------------------------------------------------
        // Private
        //--------------------------------------------------------------------------
    
        /**
         * @override _reset from AbstractField
         * @private
         */
        _reset: function () {
            this._super.apply(this, arguments);
            this._setState();
        },
        /**
         * Prepares the rendering data from the field and record data.
         * @private
         */
        _setState: function () {
            var self = this;
            if (this.field.type === 'many2one') {
                this.status_information = _.map(self.phase_ok, function (info) {
                    
                    return _.extend({
                        selected: info.id === self.value.res_id,
                    }, info);
                });
            } else {
                var selection = this.field.selection;
                if (this.attrs.statusbar_visible) {
                    var restriction = this.attrs.statusbar_visible.split(",");
                    selection = _.filter(selection, function (val) {
                        return _.contains(restriction, val[0]) || val[0] === self.value;
                    });
                }
                this.status_information = _.map(selection, function (val) {
                    return { id: val[0], display_name: val[1], selected: val[0] === self.value, fold: false };
                });
            }
        },
        /**
         * @override _render from AbstractField
         * @private
         */
        _render: function () {
            var selections = _.partition(this.status_information, function (info) {
                return (info.selected || !info.fold);
            });
            this.$el.html(qweb.render("FieldStatus.content", {
                selection_unfolded: selections[0],
                selection_folded: selections[1],
                clickable: this.isClickable,
            }));
        },
    
        //--------------------------------------------------------------------------
        // Handlers
        //--------------------------------------------------------------------------
    
        /**
         * Called when on status stage is clicked -> sets the field value.
         *
         * @private
         * @param {MouseEvent} e
         */
        _onClickStage: function (e) {
            this._setValue($(e.currentTarget).data("value"));
        },
    });

    registry.add('bloomupstatusbar', BloomupFieldStatus);
})