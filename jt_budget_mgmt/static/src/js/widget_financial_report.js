odoo.define('jt_budget_mgmt.widget_financial_report', function (require) {
"use strict";
    var config = require('web.config');
    var core = require('web.core');
    var Dialog = require('web.Dialog');
    var data = require('web.data');
    var Widget = require('web.Widget');
    var RelationalFields = require('web.relational_fields');
    var AccountReport = require('account_reports.account_report');
    var StandaloneFieldManagerMixin = require('web.StandaloneFieldManagerMixin');

    var QWeb = core.qweb;
    var _t = core._t;

    var M2MFilters = Widget.extend(StandaloneFieldManagerMixin, {
        /**
         * @constructor
         * @param {Object} fields
         */
        init: function (parent, fields) {
            this._super.apply(this, arguments);
            StandaloneFieldManagerMixin.init.call(this);
            this.fields = fields;
            this.widgets = {};
        },
        /**
         * @override
         */
        willStart: function () {
            var self = this;
            var defs = [this._super.apply(this, arguments)];
            _.each(this.fields, function (field, fieldName) {
                defs.push(self._makeM2MWidget(field, fieldName));
            });
            return Promise.all(defs);
        },
        /**
         * @override
         */
        start: function () {
            var self = this;
            var $content = $(QWeb.render("m2mWidgetTable", {fields: this.fields}));
            self.$el.append($content);
            _.each(this.fields, function (field, fieldName) {
                self.widgets[fieldName].appendTo($content.find('#'+fieldName+'_field'));
            });
            return this._super.apply(this, arguments);
        },

        //--------------------------------------------------------------------------
        // Private
        //--------------------------------------------------------------------------

        /**
         * This method will be called whenever a field value has changed and has
         * been confirmed by the model.
         *
         * @private
         * @override
         * @returns {Promise}
         */

		/**
        _confirmChange: function () {
            var self = this;
            var result = StandaloneFieldManagerMixin._confirmChange.apply(this, arguments);
            var data = {};
            _.each(this.fields, function (filter, fieldName) {
                data[fieldName] = self.widgets[fieldName].value.res_ids;
            });
			console.log("====",this)
            this.trigger_up('value_changed', data);
            return result;
        },
		*/
        _confirmChange_custom: function () {
       		var self = this;
            var result = StandaloneFieldManagerMixin._confirmChange.apply(this, arguments);
            var data = {};
            _.each(this.fields, function (filter, fieldName) {
                data[fieldName] = self.widgets[fieldName].value.res_ids;
            });
            this.trigger_up('value_changed', data);
            return result;
        },

        /**
         * This method will create a record and initialize M2M widget.
         *
         * @private
         * @param {Object} fieldInfo
         * @param {string} fieldName
         * @returns {Promise}
         */

        _makeM2MWidget: function (fieldInfo, fieldName) {
            var self = this;
            var options = {};
            options[fieldName] = {
                options: {
                    no_create_edit: true,
                    no_create: true,
                }
            };
            return this.model.makeRecord(fieldInfo.modelName, [{
                fields: [{
                    name: 'id',
                    type: 'integer',
                }, {
                    name: 'display_name',
                    type: 'char',
                }],
                name: fieldName,
                relation: fieldInfo.modelName,
                type: 'many2many',
                value: fieldInfo.value,
            }], options).then(function (recordID) {
                self.widgets[fieldName] = new RelationalFields.FieldMany2ManyTags(self,
                    fieldName,
                    self.model.get(recordID),
                    {mode: 'edit',}
                );
                self._registerWidget(recordID, fieldName, self.widgets[fieldName]);
            });
        },
    });

    var AccountReportInh = AccountReport.include({
        custom_events: {
            'value_changed': function(ev) {
                 var self = this;
                 self.report_options.partner_ids = ev.data.partner_ids;
                 self.report_options.partner_categories = ev.data.partner_categories;
                 self.report_options.analytic_accounts = ev.data.analytic_accounts;
                 // Budget Report Filters
                 self.report_options.code_sections = ev.data.code_sections;
                 self.report_options.section_program = ev.data.section_program;
                 self.report_options.section_sub_program = ev.data.section_sub_program;
                 self.report_options.section_dependency = ev.data.section_dependency;
                 self.report_options.section_sub_dependency = ev.data.section_sub_dependency;
                 self.report_options.section_expense_item = ev.data.section_expense_item;
                 self.report_options.section_or = ev.data.section_or;
                 self.report_options.section_ai = ev.data.section_ai;
                 self.report_options.section_conpp = ev.data.section_conpp;
                 self.report_options.section_conpa = ev.data.section_conpa;
                 self.report_options.section_expense = ev.data.section_expense;
                 self.report_options.section_ug = ev.data.section_ug;
                 self.report_options.section_wallet = ev.data.section_wallet;
                 self.report_options.section_tp = ev.data.section_tp;
                 self.report_options.section_pn = ev.data.section_pn;
                 self.report_options.section_stage = ev.data.section_stage;
                 self.report_options.section_agreement_type = ev.data.section_agreement_type;
                 self.report_options.section_agreement_number = ev.data.section_agreement_number;

                 return self.reload().then(function () {
                     self.$searchview_buttons.find('.account_partner_filter').click();
                     self.$searchview_buttons.find('.account_analytic_filter').click();
                     self.$searchview_buttons.find('.program_code_section_filter').click();
                 });
             },
        },

        _confirmChange_coustom: function () {
            var data = {};
            _.each(this.fields, function (filter, fieldName) {
                data[fieldName] = self.widgets[fieldName].value.res_ids;
            });
            this.trigger_up('value_changed', data);
        },

        render_searchview_buttons: function() {
            this._super.apply(this, arguments);
			var self = this;


		    _.each(this.$searchview_buttons.find('.js_budget_control_choice_filter'), function(k) {
		        $(k).toggleClass('selected', (_.filter(self.report_options[$(k).data('filter')], function(el){return ''+el.id == ''+$(k).data('id') 			&& el.selected === true;})).length > 0);
		    });

		    this.$searchview_buttons.find('.js_budget_control_choice_filter').click(function (event) {
		        var option_value = $(this).data('filter');
		        var option_id = $(this).data('id');
		        _.filter(self.report_options[option_value], function(el) {
		            if (''+el.id == ''+option_id){
		                if (el.selected === undefined || el.selected === null){el.selected = false;}
		                el.selected = !el.selected;
		            } else if (option_value === 'ir_filters') {
		                el.selected = false;
		            }
		            return el;
		        });
		    _.each(self.$searchview_buttons.find('.js_budget_control_choice_filter'), function(k) {
		        $(k).toggleClass('selected', (_.filter(self.report_options[$(k).data('filter')], function(el){return ''+el.id == ''+$(k).data('id') 			&& el.selected === true;})).length > 0);
		    });
				 
		    });

		
            // program_code_section filter
            if (this.report_options.code_sections) {
                if (!this.M2MFilters) {
                    var fields = {};
                    if (this.report_options.code_sections && !this.report_options.is_code_sections) {
                        fields['code_sections'] = {
                            label: _t('Programmatic Code Section'),
                            modelName: 'report.program.fields',
                            value: this.report_options.code_sections.map(Number),
                        };
                    }
                    if (this.report_options.section_program) {
                        fields['section_program'] = {
                            label: _t('Program'),
                            modelName: 'program',
                            value: this.report_options.section_program.map(Number),
                        };
                    }
                    if (this.report_options.section_sub_program) {
                        fields['section_sub_program'] = {
                            label: _t('Sub-Program'),
                            modelName: 'sub.program',
                            value: this.report_options.section_sub_program.map(Number),
                        };
                    }
                    if (this.report_options.section_dependency) {
                        fields['section_dependency'] = {
                            label: _t('Dependency'),
                            modelName: 'dependency',
                            value: this.report_options.section_dependency.map(Number),
                        };
                    }
                    if (this.report_options.section_sub_dependency) {
                        fields['section_sub_dependency'] = {
                            label: _t('Sub-Dependency'),
                            modelName: 'sub.dependency',
                            value: this.report_options.section_sub_dependency.map(Number),
                        };
                    }
                    if (this.report_options.section_expense_item) {
                        fields['section_expense_item'] = {
                            label: _t('Expense Item'),
                            modelName: 'expenditure.item',
                            value: this.report_options.section_expense_item.map(Number),
                        };
                    }
                    if (this.report_options.section_or) {
                        fields['section_or'] = {
                            label: _t('Origin Resource'),
                            modelName: 'resource.origin',
                            value: this.report_options.section_or.map(Number),
                        };
                    }
                    if (this.report_options.section_ai) {
                        fields['section_ai'] = {
                            label: _t('Institutional Activity'),
                            modelName: 'institutional.activity',
                            value: this.report_options.section_ai.map(Number),
                        };
                    }
                    if (this.report_options.section_conpp) {
                        fields['section_conpp'] = {
                            label: _t('Budget Program Conversion (CONPP)'),
                            modelName: 'budget.program.conversion',
                            value: this.report_options.section_conpp.map(Number),
                        };
                    }
                    if (this.report_options.section_conpa) {
                        fields['section_conpa'] = {
                            label: _t('SHCP Games (CONPA)'),
                            modelName: 'departure.conversion',
                            value: this.report_options.section_conpa.map(Number),
                        };
                    }
                    if (this.report_options.section_expense) {
                        fields['section_expense'] = {
                            label: _t('Type of Expense (TG)'),
                            modelName: 'expense.type',
                            value: this.report_options.section_expense.map(Number),
                        };
                    }
                    if (this.report_options.section_ug) {
                        fields['section_ug'] = {
                            label: _t('Geographic Location (UG)'),
                            modelName: 'geographic.location',
                            value: this.report_options.section_ug.map(Number),
                        };
                    }
                    if (this.report_options.section_wallet) {
                        fields['section_wallet'] = {
                            label: _t('Wallet Key (CC)'),
                            modelName: 'key.wallet',
                            value: this.report_options.section_wallet.map(Number),
                        };
                    }
                    if (this.report_options.section_tp) {
                        fields['section_tp'] = {
                            label: _t('Project Type (TP)'),
                            modelName: 'project.type',
                            value: this.report_options.section_tp.map(Number),
                        };
                    }
                    if (this.report_options.section_pn) {
                        fields['section_pn'] = {
                            label: _t('Project Number'),
                            modelName: 'project.type',
                            value: this.report_options.section_pn.map(Number),
                        };
                    }
                    if (this.report_options.section_stage) {
                        fields['section_stage'] = {
                            label: _t('Stage'),
                            modelName: 'stage',
                            value: this.report_options.section_stage.map(Number),
                        };
                    }
                    if (this.report_options.section_agreement_type) {
                        fields['section_agreement_type'] = {
                            label: _t('Agreement Type'),
                            modelName: 'agreement.type',
                            value: this.report_options.section_agreement_type.map(Number),
                        };
                    }
                    if (this.report_options.section_agreement_number) {
                        fields['section_agreement_number'] = {
                            label: _t('Agreement Number'),
                            modelName: 'agreement.type',
                            value: this.report_options.section_agreement_number.map(Number),
                        };
                    }


                    if (!_.isEmpty(fields)) {
                        this.M2MFilters = new M2MFilters(this, fields);
                        this.M2MFilters.appendTo(this.$searchview_buttons.find('.js_program_code_section_m2m'));
				    	this.$searchview_buttons.find('.o_budget_filter_search').on('click', this.M2MFilters._confirmChange_custom.bind(this.M2MFilters));

                    }
                } else {
                    this.$searchview_buttons.find('.js_program_code_section_m2m').append(this.M2MFilters.$el);
				    this.$searchview_buttons.find('.o_budget_filter_search').on('click', this.M2MFilters._confirmChange_custom.bind(this.M2MFilters));

                }
            }
        },
    });

});
