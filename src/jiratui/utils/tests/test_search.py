from jiratui.utils.search import (
    get_work_item_search_fields,
    get_work_item_search_results_table_columns,
)


def test_get_work_item_search_fields_without_search_results_columns():
    # WHEN
    fields = get_work_item_search_fields([])
    # THEN
    assert fields == ['id', 'key', 'issuetype', 'priority', 'status', 'summary', 'assignee']


def test_get_work_item_search_fields_with_search_results_columns():
    # WHEN
    fields = get_work_item_search_fields(
        ['Status', 'a', 'parent ', 'issuetype', 'summary', 'assignee', 'reporter', 'Priority']
    )
    # THEN
    assert fields == [
        'id',
        'key',
        'status',
        'parent',
        'issuetype',
        'summary',
        'assignee',
        'reporter',
        'priority',
    ]


def test_get_work_item_search_results_table_columns_without_search_results_columns():
    # WHEN
    columns = get_work_item_search_results_table_columns([])
    # THEN
    assert columns == ['Key', 'Type', 'Priority', 'Status', 'Summary', 'Assignee']


def test_get_work_item_search_results_table_columns_with_search_results_columns():
    # WHEN
    columns = get_work_item_search_results_table_columns(
        ['Status', 'a', 'parent ', 'issuetype', 'summary', 'assignee', 'reporter']
    )
    # THEN
    assert columns == ['Key', 'Status', 'Parent', 'Type', 'Summary', 'Assignee', 'Reporter']
