odoo.define('bloomup_owl_components.loader', function (require) {
    "use strict";

    require('web.dom_ready');
    var core = require('web.core');
    var _t = core._t;
    
    var rpc = require('web.rpc');
    var session  = require('web.session');

    const { Component, useState, mount } = owl;
    const { xml } = owl.tags;

    class Loader extends Component{
        /**
         * Loader tutta pagina 
         * ESEMPIO:
         * <div t-if="state.loading">
         *      <Loader/>
         * </div>
         */
        static template = xml`
        <div class="loading">
        <div class="spinner-grow text-primary" style="width: 6rem; height: 6rem;" role="status">
        </div></div>
        `;
    }
    return Loader;


});
