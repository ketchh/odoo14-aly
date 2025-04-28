odoo.define('bloomup_fleet_move.field_empty_highlight', function (require) {
    "use strict";

    // Import widget di base e il registry per i campi
    var basic_fields = require('web.basic_fields');
    var fieldRegistry = require('web.field_registry');

    // ================================================================
    // Widget per i campi testuali (FieldChar)
    // ================================================================
    var FieldCharHighlight = basic_fields.FieldChar.extend({
        /**
         * Metodo per il rendering in modalità di modifica.
         * Aggiunge la classe CSS se il valore è una stringa vuota.
         */

        _renderEdit: function () {
            this._super.apply(this, arguments);
            if (!this.value || this.value === '') {
                this.$el.css('background-color', 'yellow');
            } else {
                this.$el.css('background-color', 'white');
            }
        },
        /**
         * Metodo per il rendering in modalità sola lettura.
         * Aggiunge la classe CSS se il valore è una stringa vuota.
         */
        _renderReadonly: function () {
            console.log("TESSSSSTTTTTT READ");
            this._super.apply(this, arguments);
            if (!this.value || this.value === '') {
                this.$el.css('background-color', 'yellow');
            } else {
                this.$el.css('background-color', 'white');
            }
        },
    });
    // Registriamo il widget con un nome univoco per poterlo usare nelle viste XML.
    fieldRegistry.add('field_char_highlight', FieldCharHighlight);

    // ================================================================
    // (Opzionale) Widget per i campi testuali multilinea (FieldText)
    // ================================================================
    if (basic_fields.FieldText) {
        var FieldTextHighlight = basic_fields.FieldText.extend({
            _renderEdit: function () {
                this._super.apply(this, arguments);
                if (this.value === '') {
                    this.$el.css('background-color', 'yellow');
                } else {
                    this.$el.css('background-color', 'yellow');
                }
            },
            _renderReadonly: function () {
                this._super.apply(this, arguments);
                if (this.value === '') {
                    this.$el.css('background-color', 'yellow');

                } else {
                    this.$el.css('background-color', 'yellow');
                }
            },
        });
        fieldRegistry.add('field_text_highlight', FieldTextHighlight);
    }

    // ================================================================
    // Widget per i campi numerici in virgola mobile (FieldFloat)
    // ================================================================
    var FieldFloatHighlight = basic_fields.FieldFloat.extend({
        _renderEdit: function () {
            this._super.apply(this, arguments);
            // Per i campi numerici, consideriamo "vuoto" solo se il valore è null o undefined
            if (this.value === null || this.value === undefined) {
                this.$el.css('background-color', 'yellow');
            } else {
                this.$el.css('background-color', 'yellow');
            }
        },
        _renderReadonly: function () {
            this._super.apply(this, arguments);
            if (this.value === null || this.value === undefined) {
                this.$el.css('background-color', 'yellow');
            } else {
                this.$el.css('background-color', 'yellow');
            }
        },
    });
    fieldRegistry.add('field_float_highlight', FieldFloatHighlight);

    // ================================================================
    // Widget per i campi numerici interi (FieldInteger)
    // ================================================================
    var FieldIntegerHighlight = basic_fields.FieldInteger.extend({
        _renderEdit: function () {
            this._super.apply(this, arguments);
            if (this.value === null || this.value === undefined) {
                this.$el.css('background-color', 'yellow');
            } else {
                this.$el.css('background-color', 'yellow');
            }
        },
        _renderReadonly: function () {
            this._super.apply(this, arguments);
            if (this.value === null || this.value === undefined) {
                this.$el.css('background-color', 'yellow');
            } else {
                this.$el.css('background-color', 'yellow');
            }
        },
    });
    fieldRegistry.add('field_integer_highlight', FieldIntegerHighlight);
});
