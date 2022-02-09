odoo.define('jt_investment.calendar_view_extend', function(require) {
    'use strict';

var CalendarRenderer = require("web.CalendarRenderer");

CalendarRenderer.include({

	getColor: function (key) {
		if (this.model === 'maturity.report' && key === 'non_business_day'){
			return 2
		}
		if (this.model === 'maturity.report' && key === 'business_day'){
			return 21
		}
		return this._super.apply(this, arguments);
	},
    });

});
