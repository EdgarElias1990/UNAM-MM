odoo.define('jt_budget_mgmt.exportData', function (require) {
"use strict";

    var DataExport = require('web.DataExport');
    var config = require('web.config');
    var core = require('web.core');
    var Dialog = require('web.Dialog');
    var data = require('web.data');
    var framework = require('web.framework');
    var pyUtils = require('web.py_utils');

    var QWeb = core.qweb;
    var _t = core._t;

    var DataExportInh = DataExport.include({
        init: function (parent, record, defaultExportFields, groupedBy, activeDomain, idsToExport) {
            this._super.apply(this, arguments);
            this.idsToExport = idsToExport;
        },
        export() {
            let exportedFields = this.defaultExportFields.map(field => ({
                name: field,
                label: this.record.fields[field].string,
            }));
            this._exportData(exportedFields, 'xlsx', this.idsToExport);
        },
    });

});