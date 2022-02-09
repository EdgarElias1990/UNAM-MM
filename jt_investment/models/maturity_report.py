from odoo import models, fields, api,_
from odoo.addons.base.models.res_partner import _tz_get
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat
from datetime import timedelta, MAXYEAR
import datetime
from odoo.tools.misc import get_lang

class MaturityReport(models.Model):

    _name = 'maturity.report'
    _description = "Maturity Report"

    name = fields.Char("Name")
    partner_id = fields.Many2one('res.partner')
    date = fields.Date("Date")
    fund_id = fields.Many2one('investment.funds', "Fund")
    po_sale_security_id = fields.Many2one('purchase.sale.security', "Purchase/Sale of Securities")
    investment_id = fields.Many2one('investment.investment', "Investment")
    cetes_id = fields.Many2one('investment.cetes', "CETES")
    udibonos_id = fields.Many2one('investment.udibonos', "Udibonos")
    bonds_id = fields.Many2one('investment.bonds', "Bonds")
    will_pay_id = fields.Many2one("investment.will.pay", "I Will Pay")
    non_business_day = fields.Boolean("Non Business Day")
    type = fields.Selection([('non_business_day', 'Non Business Day'),
                             ('business_day', 'Business Day')], default='business_day')

    user_id = fields.Many2one('res.users', 'Owner', states={'done': [('readonly', True)]},
                              default=lambda self: self.env.user)
    allday = fields.Boolean("All Day")
    start = fields.Datetime('Start',help="Start date of an event, without time for full days events")
    stop = fields.Datetime('Stop',  help="Stop date of an event, without time for full days events")

    start_date = fields.Date('Starting At', compute='_compute_dates', inverse='_inverse_dates', store=True)
    start_datetime = fields.Datetime('Starting At', compute='_compute_dates', inverse='_inverse_dates', store=True)
    stop_date = fields.Date('End Date', compute='_compute_dates', inverse='_inverse_dates', store=True)
    stop_datetime = fields.Datetime('End Datetime', compute='_compute_dates', inverse='_inverse_dates', store=True)  # old date_deadline
    
    event_tz = fields.Selection('_event_tz_get', string='Timezone',
                                default=lambda self: self.env.context.get('tz') or self.user_id.tz)
    duration = fields.Float("Duration")
    description = fields.Text("Description")
    categ_ids = fields.Many2many('calendar.event.type', 'rel_maturity_report_event_type',
                                 'maturity_report_id', 'rel_report_event_id', "Tags")
    alarm_ids = fields.Many2many('calendar.alarm', 'calendar_alarm_maturity_report_rel', string='Reminders',
                                 ondelete="restrict", copy=False)
    location = fields.Char("Location")
    recurrency = fields.Boolean("Recurrent")
    interval = fields.Integer("Interval")
    rrule_type = fields.Selection([('daily', 'Days'), ('weekly', 'Weeks'),
                                   ('monthly', 'Months'), ('yearly', 'yearly')])
    end_type = fields.Selection([('count', "Number of Repetation"),
                                 ('end_Date', 'End Date')])
    final_date = fields.Date("Final Date")
    count = fields.Integer("Count")
    privacy = fields.Selection([('public', 'Evety One'),
                    ('private', 'Only Me'), ('confidencial', 'Only Internal Users')], string="Privacy")
    show_as = fields.Selection([('free', 'Free'), ('busy', 'Busy')], string="Show As")
    mo = fields.Boolean("Mon")
    tu = fields.Boolean("Tue")
    we = fields.Boolean("Wed")
    th = fields.Boolean("Thu")
    fr = fields.Boolean("Fri")
    sa = fields.Boolean("Sat")
    su = fields.Boolean("Sun")
    month_by = fields.Selection([('date', "Date of Month"),
                                 ('day', "Day of Month")], "Day of Month")
    day = fields.Integer("Day")
    byday = fields.Selection([('1', 'First'),
                              ('2', 'Second'),
                              ('3', 'Third'),
                              ('4', 'Forth'),
                              ('5', 'Fifth'),
                              ('-1', 'Last'),
                              ])
    week_list = fields.Selection([('MO', 'Monday'),
                                  ('TU', 'Tuesday'),
                                  ('WE', 'Wednesday'),
                                  ('Th', 'Thrusday'),
                                  ('FR', 'Friday'),
                                  ('ST', 'Saturday'),
                                  ('SU', 'Sunday')])

    display_time = fields.Char('Event Time', compute='_compute_display_time')

    def write(self,vals):
        res = super(MaturityReport, self).write(vals)
        if not self._context.get('dont_notify'):
            for meeting in self:
                if len(meeting.alarm_ids) > 0 or vals.get('alarm_ids'):
                    partners_to_notify = meeting.partner_id.ids
                    self._notify_next_alarm(partners_to_notify)
        return res
    
    @api.model
    def _get_date_formats(self):
        """ get current date and time format, according to the context lang
            :return: a tuple with (format date, format time)
        """
        lang = get_lang(self.env)
        return (lang.date_format, lang.time_format)

    @api.model
    def _get_display_time(self, start, stop, zduration, zallday):
        """ Return date and time (from to from) based on duration with timezone in string. Eg :
                1) if user add duration for 2 hours, return : August-23-2013 at (04-30 To 06-30) (Europe/Brussels)
                2) if event all day ,return : AllDay, July-31-2013
        """
        timezone = self._context.get('tz') or self.env.user.partner_id.tz or 'UTC'

        # get date/time format according to context
        format_date, format_time = self._get_date_formats()

        # convert date and time into user timezone
        self_tz = self.with_context(tz=timezone)
        date = fields.Datetime.context_timestamp(self_tz, fields.Datetime.from_string(start))
        date_deadline = fields.Datetime.context_timestamp(self_tz, fields.Datetime.from_string(stop))

        # convert into string the date and time, using user formats
        to_text = pycompat.to_text
        date_str = to_text(date.strftime(format_date))
        time_str = to_text(date.strftime(format_time))

        if zallday:
            display_time = _("AllDay , %s") % (date_str)
        elif zduration < 24:
            duration = date + timedelta(minutes=round(zduration*60))
            duration_time = to_text(duration.strftime(format_time))
            display_time = _(u"%s at (%s To %s) (%s)") % (
                date_str,
                time_str,
                duration_time,
                timezone,
            )
        else:
            dd_date = to_text(date_deadline.strftime(format_date))
            dd_time = to_text(date_deadline.strftime(format_time))
            display_time = _(u"%s at %s To\n %s at %s (%s)") % (
                date_str,
                time_str,
                dd_date,
                dd_time,
                timezone,
            )
        return display_time

    def _compute_display_time(self):
        for meeting in self:
            if meeting.start and meeting.stop: 
                meeting.display_time = self._get_display_time(meeting.start, meeting.stop, meeting.duration, meeting.allday)
            else:
                meeting.display_time = ''
                
    def _get_duration(self, start, stop):
        """ Get the duration value between the 2 given dates. """
        if start and stop:
            diff = fields.Datetime.from_string(stop) - fields.Datetime.from_string(start)
            if diff:
                duration = float(diff.days) * 24 + (float(diff.seconds) / 3600)
                return round(duration, 2)
            return 0.0

    @api.depends('allday', 'start', 'stop')
    def _compute_dates(self):
        """ Adapt the value of start_date(time)/stop_date(time) according to start/stop fields and allday. Also, compute
            the duration for not allday meeting ; otherwise the duration is set to zero, since the meeting last all the day.
        """
        for meeting in self:
            if meeting.allday and meeting.start and meeting.stop:
                meeting.start_date = meeting.start.date()
                meeting.start_datetime = False
                meeting.stop_date = meeting.stop.date()
                meeting.stop_datetime = False

                meeting.duration = 0.0
            else:
                meeting.start_date = False
                meeting.start_datetime = meeting.start
                meeting.stop_date = False
                meeting.stop_datetime = meeting.stop

                meeting.duration = self._get_duration(meeting.start, meeting.stop)

    def _inverse_dates(self):
        for meeting in self:
            if meeting.allday:

                # Convention break:
                # stop and start are NOT in UTC in allday event
                # in this case, they actually represent a date
                # i.e. Christmas is on 25/12 for everyone
                # even if people don't celebrate it simultaneously
                enddate = fields.Datetime.from_string(meeting.stop_date)
                enddate = enddate.replace(hour=18)

                startdate = fields.Datetime.from_string(meeting.start_date)
                startdate = startdate.replace(hour=8)  # Set 8 AM

                meeting.write({
                    'start': startdate.replace(tzinfo=None),
                    'stop': enddate.replace(tzinfo=None)
                })
            else:
                meeting.write({'start': meeting.start_datetime,
                               'stop': meeting.stop_datetime})
    
    @api.model
    def _event_tz_get(self):
        return _tz_get(self)


    @api.onchange('start_datetime', 'duration')
    def _onchange_duration(self):
        if self.start_datetime:
            start = self.start_datetime
            self.start = self.start_datetime
            # Round the duration (in hours) to the minute to avoid weird situations where the event
            # stops at 4:19:59, later displayed as 4:19.
            self.stop = start + timedelta(minutes=round((self.duration or 1.0) * 60))
            if self.allday:
                self.stop -= timedelta(seconds=1)

    @api.onchange('start_date')
    def _onchange_start_date(self):
        if self.start_date:
            self.start = datetime.datetime.combine(self.start_date, datetime.time.min)

    @api.onchange('stop_date')
    def _onchange_stop_date(self):
        if self.stop_date:
            self.stop = datetime.datetime.combine(self.stop_date, datetime.time.max)

    def do_check_alarm_for_one_date(self, one_date, event, event_maxdelta, in_the_next_X_seconds, alarm_type, after=False, missing=False):
        """ Search for some alarms in the interval of time determined by some parameters (after, in_the_next_X_seconds, ...)
            :param one_date: date of the event to check (not the same that in the event browse if recurrent)
            :param event: Event browse record
            :param event_maxdelta: biggest duration from alarms for this event
            :param in_the_next_X_seconds: looking in the future (in seconds)
            :param after: if not False: will return alert if after this date (date as string - todo: change in master)
            :param missing: if not False: will return alert even if we are too late
            :param notif: Looking for type notification
            :param mail: looking for type email
        """
        result = []
        event_maxdelta = False
        # TODO: remove event_maxdelta and if using it
        #if one_date - timedelta(minutes=(missing and 0 or event_maxdelta)) < datetime.datetime.now() + timedelta(seconds=in_the_next_X_seconds):  # if an alarm is possible for this date
        if one_date:
            for alarm in event.alarm_ids:
                if alarm.alarm_type == alarm_type and \
                    one_date - timedelta(minutes=(missing and 0 or alarm.duration_minutes)) < datetime.datetime.now() + timedelta(seconds=in_the_next_X_seconds) and \
                        (not after or one_date - timedelta(minutes=alarm.duration_minutes) > fields.Datetime.from_string(after)):
                        alert = {
                            'alarm_id': alarm.id,
                            'event_id': event.id,
                            'notify_at': one_date - timedelta(minutes=alarm.duration_minutes),
                        }
                        result.append(alert)
        return result

    def do_notif_reminder(self, alert):
        alarm = self.env['calendar.alarm'].browse(alert['alarm_id'])
        meeting = self.env['maturity.report'].browse(alert['event_id'])

        if alarm.alarm_type == 'notification':
            message = meeting.display_time

            delta = alert['notify_at'] - datetime.datetime.now()
            delta = delta.seconds + delta.days * 3600 * 24

            return {
                'alarm_id': alarm.id,
                'event_id': False,
                'title': meeting.name,
                'message': message,
                'timer': delta,
                'notify_at': fields.Datetime.to_string(alert['notify_at']),
            }

    @api.model
    def get_next_notif(self):
        partner = self.env.user.partner_id
        all_notif = []

        if not partner:
            return []

        time_limit = 3600 * 24  # return alarms of the next 24 hours
        for meeting in self.env['maturity.report'].search([('partner_id','!=',False),('display_time','!=',False)]):
            max_delta = 0
            in_date_format = fields.Datetime.from_string(meeting.start)
            last_found = self.do_check_alarm_for_one_date(in_date_format, meeting, max_delta, time_limit, 'notification', after=partner.calendar_last_notif_ack)
            if last_found:
                for alert in last_found:
                    all_notif.append(self.do_notif_reminder(alert))
        return all_notif

    def _notify_next_alarm(self, partner_ids):
        """ Sends through the bus the next alarm of given partners """
        notifications = []
        users = self.env['res.users'].search([('partner_id', 'in', tuple(partner_ids))])
        for user in users:
            notif = self.with_user(user).get_next_notif()
            notifications.append([(self._cr.dbname, 'calendar.alarm', user.partner_id.id), notif])
        if len(notifications) > 0:
            self.env['bus.bus'].sendmany(notifications)

class CalendarPaymentRegistration(models.Model):

    _inherit = 'calendar.payment.regis'

    @api.model
    def create(self, vals):
        res = super(CalendarPaymentRegistration, self).create(vals)
        maturity_obj = self.env['maturity.report']
        if res.type_pay == 'Non Business Day' and res.date:
            mat_rec = maturity_obj.search([('date', '=', res.date),
                                           ('non_business_day', '=', True)], limit=1)
            if not mat_rec:
                maturity_obj.create({
                    'name': 'Non Business Day',
                    'non_business_day': True,
                    'date': res.date,
                    'type': 'non_business_day'
                })
        return res

    def write(self, vals):
        res = super(CalendarPaymentRegistration, self).write(vals)
        maturity_obj = self.env['maturity.report']
        for rec in self:
            if vals.get('type_pay') and vals.get('type_pay') == 'Non Business Day' and rec.date:
                mat_rec = maturity_obj.search([('date', '=', rec.date),
                                               ('non_business_day', '=', True)], limit=1)
                if not mat_rec:
                    maturity_obj.create({
                        'name': 'Non Business Day',
                        'non_business_day': True,
                        'date': rec.date,
                        'type': 'non_business_day'
                    })
            elif vals.get('type_pay') and vals.get('type_pay') == 'Payment schedule' and rec.date:
                mat_rec = maturity_obj.search([('date', '=', rec.date),
                                               ('non_business_day', '=', True)], limit=1)
                if mat_rec:
                    mat_rec.unlink()
        
        return res

    def unlink(self):
        maturity_obj = self.env['maturity.report']
        for rec in self:
            if rec.type_pay == 'Non Business Day' and rec.date:
                mat_rec = maturity_obj.search([('date', '=', rec.date),
                                               ('non_business_day', '=', True)], limit=1)
                if mat_rec:
                    mat_rec.unlink()
        return super(CalendarPaymentRegistration, self).unlink()

    def create_maturity_report(self):
        maturity_obj = self.env['maturity.report']
        for rec in self:
            if rec.type_pay == 'Non Business Day' and rec.date:
                mat_rec = maturity_obj.search([('date', '=', rec.date),
                                     ('non_business_day', '=', True)], limit=1)
                if not mat_rec:
                    maturity_obj.create({
                        'name': 'Non Business Day',
                        'non_business_day': True,
                        'date': rec.date,
                        'type': 'non_business_day'
                    })

