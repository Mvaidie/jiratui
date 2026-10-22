from unittest.mock import AsyncMock, Mock

import pytest

from jiratui.api_controller.controller import APIControllerResponse
from jiratui.models import IssueStatus, JiraIssue
from jiratui.widgets.work_item_definition_of.definition_of import (
    DefinitionOfChecklist,
    WorkItemDefinitionOf,
    build_checklist,
    get_work_item_definition_of,
)

DOR_OPTIONS = [{'id': '1', 'value': 'Estimated'}, {'id': '2', 'value': 'Validated'}]


def _work_item(
    custom_fields: dict | None = None, edit_meta_fields: dict | None = None
) -> JiraIssue:
    return JiraIssue(
        id='1',
        key='WI-1',
        summary='summary',
        status=IssueStatus(id='1', name='To Do'),
        custom_fields=custom_fields,
        edit_meta={'fields': edit_meta_fields} if edit_meta_fields is not None else None,
    )


def _config(ready_field=None, done_field=None) -> Mock:
    return Mock(definition_of_ready_field=ready_field, definition_of_done_field=done_field)


def test_build_checklist_with_the_options_of_the_field():
    # GIVEN
    work_item = _work_item(
        custom_fields={'customfield_10878': [{'value': 'Validated'}, {'value': 'Removed option'}]},
        edit_meta_fields={'customfield_10878': {'allowedValues': DOR_OPTIONS}},
    )
    # WHEN
    checklist = build_checklist('Definition of Ready', work_item, 'customfield_10878')
    # THEN
    assert checklist == DefinitionOfChecklist(
        title='Definition of Ready',
        items=[('Estimated', False), ('Validated', True), ('Removed option', True)],
    )
    assert checklist.checked_count == 2


def test_build_checklist_without_edit_metadata():
    # GIVEN
    work_item = _work_item(custom_fields={'customfield_10878': [{'value': 'Validated'}]})
    # WHEN
    checklist = build_checklist('Definition of Ready', work_item, 'customfield_10878')
    # THEN
    assert checklist.items == [('Validated', True)]


def test_build_checklist_without_field():
    # WHEN
    checklist = build_checklist('Definition of Done', _work_item(), None)
    # THEN
    assert checklist == DefinitionOfChecklist(title='Definition of Done')


@pytest.mark.asyncio
async def test_get_work_item_definition_of():
    # GIVEN
    api = Mock()
    api.get_field_ids = AsyncMock(
        return_value=APIControllerResponse(result={'DoR': 'customfield_10878', 'DoD': None})
    )
    work_item = _work_item(
        custom_fields={'customfield_10878': [{'value': 'Estimated'}]},
        edit_meta_fields={'customfield_10878': {'allowedValues': DOR_OPTIONS}},
    )
    # WHEN
    definition_of = await get_work_item_definition_of(work_item, api, _config('DoR', ' DoD '))
    # THEN
    assert definition_of == WorkItemDefinitionOf(
        work_item_key='WI-1',
        checklists=[
            DefinitionOfChecklist(
                title='Definition of Ready', items=[('Estimated', True), ('Validated', False)]
            ),
            DefinitionOfChecklist(title='Definition of Done'),
        ],
    )
    api.get_field_ids.assert_awaited_once_with(['DoR', 'DoD'])


@pytest.mark.asyncio
async def test_get_work_item_definition_of_without_settings():
    # GIVEN
    api = Mock()
    api.get_field_ids = AsyncMock()
    # WHEN
    definition_of = await get_work_item_definition_of(_work_item(), api, _config(None, '  '))
    # THEN
    assert definition_of is None
    api.get_field_ids.assert_not_called()


@pytest.mark.asyncio
async def test_get_work_item_definition_of_with_errors():
    # GIVEN
    api = Mock()
    api.get_field_ids = AsyncMock(return_value=APIControllerResponse(success=False, error='error'))
    # WHEN
    definition_of = await get_work_item_definition_of(_work_item(), api, _config('DoR'))
    # THEN
    assert definition_of == WorkItemDefinitionOf(
        work_item_key='WI-1', checklists=[DefinitionOfChecklist(title='Definition of Ready')]
    )
