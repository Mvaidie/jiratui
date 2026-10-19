from datetime import datetime

import pytest

from jiratui.api.utils import (
    build_issue_search_jql,
    build_jql_field_reference,
    parse_required_fields_from_meta,
)
from jiratui.models import WorkItemsSearchOrderBy


def test_build_issue_search_jql():
    # WHEN
    result = build_issue_search_jql()
    # THEN
    assert result == ''


def test_build_issue_search_jql_with_parameters():
    # WHEN
    result = build_issue_search_jql(
        project_key='P1',
        created_from=datetime(2025, 12, 1).date(),
        created_until=datetime(2025, 12, 2).date(),
        updated_from=datetime(2025, 12, 3).date(),
        updated_until=datetime(2025, 12, 4).date(),
        status=1,
        assignee='1',
        issue_type=2,
    )
    # THEN
    assert result == (
        'project = "P1" and created >= "2025-12-01" and created <= "2025-12-02" and updated >= "2025-12-03" and updated <= "2025-12-04" and status = "1" and assignee = "1" and type = 2'
    )


def test_build_issue_search_jql_with_parameters_and_jql_query():
    # WHEN
    result = build_issue_search_jql(
        project_key='P1',
        created_from=datetime(2025, 12, 1).date(),
        created_until=datetime(2025, 12, 2).date(),
        updated_from=datetime(2025, 12, 3).date(),
        updated_until=datetime(2025, 12, 4).date(),
        status=1,
        assignee='1',
        issue_type=2,
        jql_query='q=5',
    )
    # THEN
    assert result == (
        'project = "P1" and created >= "2025-12-01" and created <= "2025-12-02" and updated >= "2025-12-03" and updated <= "2025-12-04" and status = "1" and assignee = "1" and type = 2 and q=5'
    )


def test_build_issue_search_jql_without_parameters_and_jql_query():
    # WHEN
    result = build_issue_search_jql(jql_query='q=5')
    # THEN
    assert result == ('q=5')


def test_build_issue_search_jql_without_parameters_and_jql_query_with_order():
    # WHEN
    result = build_issue_search_jql(jql_query='q=5', order_by=WorkItemsSearchOrderBy.KEY_ASC)
    # THEN
    assert result == ('q=5 order by key asc')


@pytest.mark.parametrize(
    'order_by, expected',
    [
        (WorkItemsSearchOrderBy.STATUS_ASC, 'project = "P1" order by status asc'),
        (WorkItemsSearchOrderBy.STATUS_DESC, 'project = "P1" order by status desc'),
    ],
)
def test_build_issue_search_jql_order_by_status(order_by: WorkItemsSearchOrderBy, expected: str):
    # WHEN
    result = build_issue_search_jql(project_key='P1', order_by=order_by)
    # THEN
    assert result == expected


def test_build_issue_search_jql_with_filter_id():
    # WHEN
    result = build_issue_search_jql(project_key='P1', filter_id='10001', jql_query='q=5')
    # THEN
    assert result == 'project = "P1" and filter = 10001 and q=5'


def test_build_issue_search_jql_with_parameters_and_jql_query_with_order():
    # WHEN
    result = build_issue_search_jql(
        project_key='P1',
        created_from=datetime(2025, 12, 1).date(),
        created_until=datetime(2025, 12, 2).date(),
        updated_from=datetime(2025, 12, 3).date(),
        updated_until=datetime(2025, 12, 4).date(),
        status=1,
        assignee='1',
        issue_type=2,
        jql_query='q=5',
        order_by=WorkItemsSearchOrderBy.KEY_ASC,
    )
    # THEN
    assert result == (
        'project = "P1" and created >= "2025-12-01" and created <= "2025-12-02" and updated >= "2025-12-03" and updated <= "2025-12-04" and status = "1" and assignee = "1" and type = 2 and q=5 order by key asc'
    )


def test_parse_required_fields_from_meta():
    # GIVEN
    metadata = {
        'fields': [
            {
                'required': True,
                'key': 'value 1',
            },
            {
                'required': False,
                'key': 'value 2',
            },
        ]
    }
    # WHEN
    result = parse_required_fields_from_meta(metadata)
    # THEN
    assert result == ['value 1']


def test_parse_required_fields_from_meta_with_no_fields():
    # GIVEN
    metadata = {'fields': []}
    # WHEN
    result = parse_required_fields_from_meta(metadata)
    # THEN
    assert result == []


def test_parse_required_fields_from_meta_with_all_fields_not_required():
    # GIVEN
    metadata = {
        'fields': [
            {
                'required': False,
                'key': 'value 1',
            },
            {
                'required': False,
                'key': 'value 2',
            },
        ]
    }
    # WHEN
    result = parse_required_fields_from_meta(metadata)
    # THEN
    assert result == []


@pytest.mark.parametrize(
    'field, expected',
    [
        ('Customer', '"Customer"'),
        (' Customer segments ', '"Customer segments"'),
        ('customfield_10085', 'cf[10085]'),
        ('a "quoted" name', '"a \\"quoted\\" name"'),
    ],
)
def test_build_jql_field_reference(field: str, expected: str):
    assert build_jql_field_reference(field) == expected


@pytest.mark.parametrize(
    'field_with_value, expected',
    [
        ('Customer', 'project = "P1" and "Customer" is not EMPTY'),
        ('customfield_10085', 'project = "P1" and cf[10085] is not EMPTY'),
        ('  ', 'project = "P1"'),
    ],
)
def test_build_issue_search_jql_with_field_with_value(field_with_value: str, expected: str):
    # WHEN
    result = build_issue_search_jql(project_key='P1', field_with_value=field_with_value)
    # THEN
    assert result == expected
