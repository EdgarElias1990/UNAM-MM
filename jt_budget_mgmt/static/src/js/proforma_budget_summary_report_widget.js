odoo.define('jt_budget_mgmt.summary_report_widget', function(require) {
"use strict";
    var Widget = require('web.Widget');
    var core = require('web.core');
    var session = require('web.session');
    var AbstractAction = require('web.AbstractAction');

    var _t = core._t;
    var QWeb = core.qweb;

    var active_id;
    var ReportWidget = AbstractAction.extend({
        'template' : "summary_report_template",
        events: {
            'click .summary_print_pdf': '_onClickPrintPDF',
            'click .summary_print_xls': '_onClickPrintXLS',
        },

        _onClickPrintPDF: function(){
            var self = this;
            return this._rpc({
                model: 'proforma.budget.summary',
                method: 'generate_report',
                args: [active_id],
                context: {'type': 'download_pdf'},
            }).then(function (record) {
                var action_download_summary = {
                    name: "Download Report",
                    type: 'ir.actions.act_window',
                    res_model: 'proforma.budget.summary',
                    res_id: parseInt(record),
                    target: 'new',
                    views: [[false, 'form']],
                    flags: {mode:'readonly'},
                }
                return self.do_action(action_download_summary)
            });
        },

        _onClickPrintXLS: function(){
            var self = this;
            return this._rpc({
                model: 'proforma.budget.summary',
                method: 'generate_report',
                args: [active_id],
                context: {'type': 'download_xls'},
            }).then(function (record) {
                var action_download_summary = {
                    name: "Download Report",
                    type: 'ir.actions.act_window',
                    res_model: 'proforma.budget.summary',
                    res_id: parseInt(record),
                    target: 'new',
                    views: [[false, 'form']],
                    flags: {mode:'readonly'},
                }
                return self.do_action(action_download_summary)
            });
        },

        init: function (parent, options) {
            this._super.apply(this, arguments);
            this._rpc({
                model: 'proforma.budget.summary',
                method: 'generate_report',
                args: [active_id],
                context: {'type': 'view'},
            }).then(function (report) {
                $('.o_summary_reports_body').html(report)
            });
        },
    });

    core.action_registry.add('ProformaBudgetSummary', ReportWidget);
    return ReportWidget;
});
