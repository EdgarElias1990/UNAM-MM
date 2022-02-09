odoo.define('jt_finance.base_import_without_debug', function (require) {
'use strict';
var core = require('web.core');
var ajax = require('web.ajax');
var qweb = core.qweb;
ajax.loadXML('/jt_finance/static/src/xml/base_import_view.xml', qweb);
});
