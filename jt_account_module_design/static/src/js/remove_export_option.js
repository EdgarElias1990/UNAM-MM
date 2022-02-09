odoo.define('remove_export_option.remove_export_option', function (require) {
"use strict";

var Sidebar = require('web.Sidebar');
var core = require('web.core');
var _t = core._t;
var _lt = core._lt;
var rpc = require('web.rpc');
    Sidebar.include({
        start: function () {
            var self = this;
            var def;
	    if (self.env.context.hide_project_payment_action_button)
            {

		def = rpc.query({
			'model': 'account.move',
			'method': 'get_all_action_ids',
			'args': [0],
			'kwargs': {context: self.env.context},
	    	}).then(function(result) {
			self.items['other'] = $.grep(self.items['other'], function(i){
			     if (i && i.action)
			     {
				if (!(result.includes(i.action.id)))
				{
					return i;	
				}
		             }		
			     else
			     {
				return i;
		             }
		        });
                });
                return Promise.resolve(def).then(this._super.bind(this));
            }

        if (self.env.context.hide_project_payment_action_button_factura)
            {
        def = rpc.query({
			'model': 'account.move',
			'method': 'get_all_action_ids_factura',
			'args': [0],
			'kwargs': {context: self.env.context},
	    	}).then(function(result) {
			self.items['other'] = $.grep(self.items['other'], function(i){
			     if (i && i.action)
			     {
				if (!(result.includes(i.action.id)))
				{
					return i;
				}
		             }
			     else
			     {
				return i;
		             }
		        });
                });
                return Promise.resolve(def).then(this._super.bind(this));
            }

        if (self.env.context.hide_project_payment_action_button_nota)
            {
        def = rpc.query({
			'model': 'account.move',
			'method': 'get_all_action_ids_nota',
			'args': [0],
			'kwargs': {context: self.env.context},
	    	}).then(function(result) {
			self.items['other'] = $.grep(self.items['other'], function(i){
			     if (i && i.action)
			     {
				if (!(result.includes(i.action.id)))
				{
					return i;
				}
		             }
			     else
			     {
				return i;
		             }
		        });
                });
                return Promise.resolve(def).then(this._super.bind(this));
            }

        if (self.env.context.hide_project_payment_action_button_cobro)
            {
        def = rpc.query({
			'model': 'account.payment',
			'method': 'get_all_action_ids_cobro',
			'args': [0],
			'kwargs': {context: self.env.context},
	    	}).then(function(result) {
			self.items['other'] = $.grep(self.items['other'], function(i){
			     if (i && i.action)
			     {
				if (!(result.includes(i.action.id)))
				{
					return i;
				}
		             }
			     else
			     {
				return i;
		             }
		        });
                });
                return Promise.resolve(def).then(this._super.bind(this));
            }

	    if (!self.env.context.income_payment_action && self.env.context.default_payment_type)
            {

		def = rpc.query({
			'model': 'account.payment',
			'method': 'get_hide_action_ids',
			'args': [0],
			'kwargs': {context: {}},
	    	}).then(function(result) {
			self.items['other'] = $.grep(self.items['other'], function(i){
			     if (i && i.action)
			     {
				if (!(result.includes(i.action.id)))
				{
					return i;	
				}
		             }		
			     else
			     {
				return i;
		             }
		        });
                });
                return Promise.resolve(def).then(this._super.bind(this));
            }

	if (self.env.context.income_payment_action && self.env.context.default_payment_type)
            {

		def = rpc.query({
			'model': 'account.payment',
			'method': 'get_hide_action_income_ids',
			'args': [0],
			'kwargs': {context: {}},
	    	}).then(function(result) {
			self.items['other'] = $.grep(self.items['other'], function(i){
			     if (i && i.action)
			     {
				if (!(result.includes(i.action.id)))
				{
					return i;	
				}
		             }		
			     else
			     {
				return i;
		             }
		        });
                });
                return Promise.resolve(def).then(this._super.bind(this));
            }
        },
    });
});
