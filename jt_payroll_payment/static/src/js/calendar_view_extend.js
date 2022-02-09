odoo.define('jt_payroll_payment.calendar_view_extend', function(require) {
    'use strict';
	
var CalendarRenderer = require("web.CalendarRenderer");

CalendarRenderer.include({

	getColor: function (key) {
		if (this.model === 'calendar.payment.regis' && key === 'Non Business Day'){
			return 2
		}
		if (this.model === 'calendar.payment.regis' && key === 'Payment schedule'){
			return 21
		}
		return this._super.apply(this, arguments);
	},
    });

});
