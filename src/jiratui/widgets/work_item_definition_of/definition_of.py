"""This module contains the widget of the tab that displays the Definition of Ready and the Definition of Done of a
work item."""

from dataclasses import dataclass, field
import logging

from rich.text import Text
from textual.containers import VerticalScroll
from textual.reactive import Reactive, reactive
from textual.widgets import Label, Static

from jiratui.api_controller.controller import APIController, APIControllerResponse
from jiratui.config import ApplicationConfiguration
from jiratui.constants import LOGGER_NAME
from jiratui.models import JiraIssue
from jiratui.widgets.work_item_customers.customers import format_field_values

CHECKED_ITEM_MARKER = '☑'
UNCHECKED_ITEM_MARKER = '☐'
CHECKED_ITEM_STYLE = '#55F255'


@dataclass
class DefinitionOfChecklist:
    """A checklist of a work item, e.g. its Definition of Ready."""

    title: str
    items: list[tuple[str, bool]] = field(default_factory=list)
    """The items of the checklist with whether they are checked or not."""

    @property
    def checked_count(self) -> int:
        return sum(1 for _, checked in self.items if checked)


@dataclass
class WorkItemDefinitionOf:
    """The Definition of Ready and the Definition of Done of a work item."""

    work_item_key: str
    checklists: list[DefinitionOfChecklist] = field(default_factory=list)


def build_checklist(
    title: str, work_item: JiraIssue, field_id: str | None
) -> DefinitionOfChecklist:
    """Builds the checklist of a work item from the value of a field, e.g. a field with checkboxes.

    The items of the checklist are the options of the field, as defined by the edit metadata of the work item; the
    checked items are the values of the field. When the field is not in the edit metadata the checklist only contains
    the checked items.

    Args:
        title: the title of the checklist.
        work_item: the work item.
        field_id: the ID of the field; `None` if the field does not exist.

    Returns:
        The checklist.
    """

    if not field_id:
        return DefinitionOfChecklist(title=title)
    checked: list[str] = format_field_values(work_item.get_custom_field_value(field_id))
    metadata: dict = work_item.get_field_edit_metadata(field_id) or {}
    options: list[str] = format_field_values(metadata.get('allowedValues'))
    items: list[tuple[str, bool]] = [(option, option in checked) for option in options]
    # values that are not options anymore are displayed as well
    items.extend((value, True) for value in checked if value not in options)
    return DefinitionOfChecklist(title=title, items=items)


async def get_work_item_definition_of(
    work_item: JiraIssue, api: APIController, config: ApplicationConfiguration
) -> WorkItemDefinitionOf | None:
    """Retrieves the Definition of Ready and the Definition of Done of a work item.

    The fields are identified by the settings `definition_of_ready_field` and `definition_of_done_field`.

    Args:
        work_item: the work item.
        api: the API controller used to find the IDs of the fields.
        config: the configuration of the application.

    Returns:
        The checklists of the work item or `None` if none of the settings is set.
    """

    settings: list[tuple[str, str]] = [
        (title, (value or '').strip())
        for title, value in (
            ('Definition of Ready', config.definition_of_ready_field),
            ('Definition of Done', config.definition_of_done_field),
        )
        if value and value.strip()
    ]
    if not settings:
        return None
    field_ids: dict[str, str | None] = {}
    response: APIControllerResponse = await api.get_field_ids([value for _, value in settings])
    if response.success:
        field_ids = response.result or {}
    else:
        logging.getLogger(LOGGER_NAME).warning(
            'Unable to find the fields of the Definition of Ready and Done',
            extra={'error': response.error},
        )
    return WorkItemDefinitionOf(
        work_item_key=work_item.key,
        checklists=[
            build_checklist(title, work_item, field_ids.get(value)) for title, value in settings
        ],
    )


class WorkItemDefinitionOfWidget(VerticalScroll):
    """Displays the Definition of Ready and the Definition of Done of the selected work item as checklists. It is
    displayed in the Info tab, after the customers."""

    HELP = 'See Definition of Ready and Done section in the help'

    definition_of: Reactive[WorkItemDefinitionOf | None] = reactive(None, always_update=True)
    """The checklists of the selected work item."""

    def __init__(self):
        super().__init__(id='work_item_definition_of')

    @property
    def help_anchor(self) -> str:
        return '#definition-of-ready-and-done'

    def watch_definition_of(self, definition_of: WorkItemDefinitionOf | None = None) -> None:
        self.remove_children()
        if definition_of is None:
            return
        widgets: list[Static] = []
        for checklist in definition_of.checklists:
            widgets.append(
                Label(
                    f'{checklist.title} ({checklist.checked_count}/{len(checklist.items)})',
                    classes='work-item-definition-of-label',
                )
            )
            if not checklist.items:
                widgets.append(Static(Text('-')))
            for item, checked in checklist.items:
                widgets.append(
                    Static(
                        Text.assemble(
                            (
                                f'{CHECKED_ITEM_MARKER if checked else UNCHECKED_ITEM_MARKER} ',
                                CHECKED_ITEM_STYLE if checked else 'dim',
                            ),
                            item,
                        )
                    )
                )
        self.mount_all(widgets)
