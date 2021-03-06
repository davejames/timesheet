# Copyright 2015 Camptocamp SA - Guewen Baconnier
# Copyright 2017 Tecnativa, S.L. - Luis M. Ontalba
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from datetime import timedelta

from odoo import _, api, exceptions, fields, models
from odoo.tools.float_utils import float_compare


class AccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"

    time_start = fields.Float(string="Begin Hour")
    time_stop = fields.Float(string="End Hour")

    @api.constrains("time_start", "time_stop", "unit_amount")
    def _check_time_start_stop(self):
        value_to_html = self.env["ir.qweb.field.float_time"].value_to_html
        for record in self:
            start = timedelta(hours=record.time_start)
            stop = timedelta(hours=record.time_stop)
            if stop < start:
                raise exceptions.ValidationError(
                    _("The beginning hour (%s) must " "precede the ending hour (%s).")
                    % (
                        value_to_html(record.time_start, None),
                        value_to_html(record.time_stop, None),
                    )
                )
            hours = (stop - start).seconds / 3600
            if hours and float_compare(hours, record.unit_amount, precision_digits=4):
                raise exceptions.ValidationError(
                    _(
                        "The duration (%s) must be equal to the difference "
                        "between the hours (%s)."
                    )
                    % (value_to_html(record.unit_amount, None), value_to_html(hours, None))
                )
            # check if lines overlap
            others = self.search(
                [
                    ("id", "!=", record.id),
                    ("user_id", "=", record.user_id.id),
                    ("date", "=", record.date),
                    ("time_start", "<", record.time_stop),
                    ("time_stop", ">", record.time_start),
                ]
            )
            if others:
                message = _("Lines can't overlap:\n")
                message += "\n".join(
                    [
                        "%s - %s"
                        % (
                            value_to_html(line.time_start, None),
                            value_to_html(line.time_stop, None),
                        )
                        for line in (record + others).sorted(lambda l: l.time_start)
                    ]
                )
                raise exceptions.ValidationError(message)

    @api.onchange("time_start", "time_stop")
    def onchange_hours_start_stop(self):
        start = timedelta(hours=self.time_start)
        stop = timedelta(hours=self.time_stop)
        if stop < start:
            return
        self.unit_amount = (stop - start).seconds / 3600

    def merge_timesheets(self):  # pragma: no cover
        """This method is needed in case hr_timesheet_sheet is installed"""
        lines = self.filtered(lambda l: not l.time_start and not l.time_stop)
        if lines:
            return super(AccountAnalyticLine, lines).merge_timesheets()
        return self[0]
