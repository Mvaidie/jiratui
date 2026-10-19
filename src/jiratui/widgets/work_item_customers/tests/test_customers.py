from unittest.mock import AsyncMock, Mock

import pytest

from jiratui.api_controller.controller import APIControllerResponse
from jiratui.models import IssueStatus, JiraIssue
from jiratui.widgets.work_item_customers.customers import (
    WorkItemCustomers,
    format_field_values,
    get_work_item_customers,
)


def _work_item(custom_fields: dict | None = None) -> JiraIssue:
    return JiraIssue(
        id='1',
        key='WI-1',
        summary='summary',
        status=IssueStatus(id='1', name='To Do'),
        custom_fields=custom_fields,
    )


def _config(customer_field=None, ticket_id_field=None, ticket_link_field=None) -> Mock:
    return Mock(
        customer_field=customer_field,
        customer_ticket_id_field=ticket_id_field,
        customer_ticket_link_field=ticket_link_field,
    )


@pytest.mark.parametrize(
    'value, expected',
    [
        (None, []),
        ('', []),
        (' https://example.com ', ['https://example.com']),
        (['ATOS', 'CNAM'], ['ATOS', 'CNAM']),
        ({'value': 'Gold'}, ['Gold']),
        ([{'displayName': 'Bart'}, {'name': 'Lisa'}], ['Bart', 'Lisa']),
        ({'id': '1'}, []),
        (26663, ['26663']),
    ],
)
def test_format_field_values(value, expected):
    assert format_field_values(value) == expected


@pytest.mark.asyncio
async def test_get_work_item_customers():
    # GIVEN
    api = Mock()
    api.get_field_ids = AsyncMock(
        return_value=APIControllerResponse(
            result={
                'Customer': 'customfield_10085',
                'Customer ticket ID': 'customfield_10087',
                'customfield_10069': 'customfield_10069',
            }
        )
    )
    work_item = _work_item(
        {
            'customfield_10085': ['ATOS', 'CNAM'],
            'customfield_10087': ['26663'],
            'customfield_10069': 'https://example.com/tickets/26663',
        }
    )
    config = _config(' Customer ', 'Customer ticket ID', 'customfield_10069')
    # WHEN
    customers = await get_work_item_customers(work_item, api, config)
    # THEN
    assert customers == WorkItemCustomers(
        work_item_key='WI-1',
        customers=['ATOS', 'CNAM'],
        ticket_ids=['26663'],
        ticket_link='https://example.com/tickets/26663',
    )
    api.get_field_ids.assert_awaited_once_with(
        ['Customer', 'Customer ticket ID', 'customfield_10069']
    )


@pytest.mark.asyncio
async def test_get_work_item_customers_without_settings():
    # GIVEN
    api = Mock()
    api.get_field_ids = AsyncMock()
    # WHEN
    customers = await get_work_item_customers(_work_item(), api, _config(None, '', '  '))
    # THEN
    assert customers is None
    api.get_field_ids.assert_not_called()


@pytest.mark.asyncio
async def test_get_work_item_customers_with_unknown_fields_and_errors():
    # GIVEN
    api = Mock()
    api.get_field_ids = AsyncMock(return_value=APIControllerResponse(success=False, error='error'))
    # WHEN
    customers = await get_work_item_customers(
        _work_item({'customfield_10085': ['ATOS']}), api, _config('Customer')
    )
    # THEN
    assert customers == WorkItemCustomers(work_item_key='WI-1')
