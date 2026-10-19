"""This module contains the widget of the tab that displays the information about the customers of a work item."""

from dataclasses import dataclass, field
import logging
from typing import Any

from rich.text import Text
from textual.containers import VerticalScroll
from textual.reactive import Reactive, reactive
from textual.widgets import Label, Link, Static

from jiratui.api_controller.controller import APIController, APIControllerResponse
from jiratui.config import ApplicationConfiguration
from jiratui.constants import LOGGER_NAME
from jiratui.models import JiraIssue


@dataclass
class WorkItemCustomers:
    """The information about the customers of a work item."""

    work_item_key: str
    customers: list[str] = field(default_factory=list)
    ticket_ids: list[str] = field(default_factory=list)
    ticket_link: str | None = None


def format_field_values(value: Any) -> list[str]:
    """Converts the value of a field, e.g. labels, options or users, into a list of strings.

    Args:
        value: the value of the field.

    Returns:
        The list of values of the field; an empty list if the field has no value.
    """

    if value is None:
        return []
    if isinstance(value, list):
        return [item for element in value for item in format_field_values(element)]
    if isinstance(value, dict):
        for key in ('value', 'name', 'displayName', 'key'):
            if value.get(key):
                return [str(value[key])]
        return []
    text = str(value).strip()
    return [text] if text else []


async def get_work_item_customers(
    work_item: JiraIssue, api: APIController, config: ApplicationConfiguration
) -> WorkItemCustomers | None:
    """Retrieves the information about the customers of a work item.

    The fields of the information are identified by the settings `customer_field`, `customer_ticket_id_field` and
    `customer_ticket_link_field`.

    Args:
        work_item: the work item.
        api: the API controller used to find the IDs of the fields.
        config: the configuration of the application.

    Returns:
        The information about the customers of the work item or `None` if none of the settings is set.
    """

    settings: dict[str, str] = {
        name: (value or '').strip()
        for name, value in (
            ('customers', config.customer_field),
            ('ticket_ids', config.customer_ticket_id_field),
            ('ticket_link', config.customer_ticket_link_field),
        )
    }
    if not (fields := [value for value in settings.values() if value]):
        return None
    field_ids: dict[str, str | None] = {}
    response: APIControllerResponse = await api.get_field_ids(fields)
    if response.success:
        field_ids = response.result or {}
    else:
        logging.getLogger(LOGGER_NAME).warning(
            'Unable to find the fields of the customers', extra={'error': response.error}
        )

    def get_values(setting: str) -> list[str]:
        if (setting_field := settings[setting]) and (field_id := field_ids.get(setting_field)):
            return format_field_values(work_item.get_custom_field_value(field_id))
        return []

    ticket_links: list[str] = get_values('ticket_link')
    return WorkItemCustomers(
        work_item_key=work_item.key,
        customers=get_values('customers'),
        ticket_ids=get_values('ticket_ids'),
        ticket_link=ticket_links[0] if ticket_links else None,
    )


class WorkItemCustomersWidget(VerticalScroll):
    """Displays the information about the customers of the selected work item: the customers, the ID of the ticket of
    the customer and the link to the ticket of the customer. It is displayed in the Info tab, after the description."""

    HELP = 'See Work Items with Customers section in the help'

    customers: Reactive[WorkItemCustomers | None] = reactive(None, always_update=True)
    """The information about the customers of the selected work item."""

    def __init__(self):
        super().__init__(id='work_item_customers')

    @property
    def help_anchor(self) -> str:
        return '#work-items-with-customers'

    def watch_customers(self, customers: WorkItemCustomers | None = None) -> None:
        self.remove_children()
        if customers is None:
            return
        ticket_link: Static = (
            Link(
                customers.ticket_link,
                url=customers.ticket_link,
                tooltip='open link in the default browser',
            )
            if customers.ticket_link
            else Static(Text('-'))
        )
        self.mount_all(
            [
                Label('Customers', classes='work-item-customers-label'),
                Static(Text(', '.join(customers.customers) or '-')),
                Label('Customer ticket ID', classes='work-item-customers-label'),
                Static(Text(', '.join(customers.ticket_ids) or '-')),
                Label('Customer ticket link', classes='work-item-customers-label'),
                ticket_link,
            ]
        )
