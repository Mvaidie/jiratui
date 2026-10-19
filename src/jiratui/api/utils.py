from datetime import date
import re

from jiratui.models import WorkItemsSearchOrderBy


def parse_required_fields_from_meta(metadata: dict) -> list[str]:
    """Extracts required field keys from issue create metadata.

    Args:
        metadata: Response from get_issue_create_meta()

    Returns:
        List of required field keys (e.g., ['summary', 'components', 'customfield_10712'])
    """

    required_fields = []
    for field in metadata.get('fields', []):
        if field.get('required', False):
            required_fields.append(field['key'])
    return required_fields


def build_issue_search_jql(
    project_key: str | None = None,
    created_from: date | None = None,
    created_until: date | None = None,
    updated_from: date | None = None,
    updated_until: date | None = None,
    status: int | None = None,
    assignee: str | None = None,
    issue_type: int | None = None,
    jql_query: str | None = None,
    search_in_active_sprint: bool = False,
    order_by: WorkItemsSearchOrderBy | None = None,
    filter_id: str | None = None,
    field_with_value: str | None = None,
) -> str:
    """Builds a JQL query expression to search issues based on different criteria.

    Args:
        project_key: the case-sensitive key of a project.
        created_from: a date to search for issues.
        created_until: a date to search for issues.
        updated_from: a date to search for issues.
        updated_until: a date to search for issues.
        status: find work items whose status matches this status name/ID.
        assignee: find work items assigned to the given user. The user is specified by the account ID, email address or
        name of a user.
        issue_type: the type of issue.
        jql_query: a string with a JQL query expression.
        search_in_active_sprint: if `True` only work items that belong to the currently active sprint will be
        retrieved.
        order_by: used to specify the fields by whose values the search results will be sorted. This requirement needs
        to be placed at the end of the JQL query, otherwise the JQL will be invalid.
        filter_id: find work items that match the filter (i.e. saved JQL search) with this ID. This is used, for
        example, to search the work items of a board.
        field_with_value: find work items that have a value in this field, identified by its name or by its ID. This is
        used, for example, to search the work items that have customers.

    Returns:
        A string with the JQL query.
    """
    fields: list[str] = []
    if project_key:
        fields.append(f'project = "{project_key}"')
    if filter_id:
        fields.append(f'filter = {filter_id}')
    if field_with_value and field_with_value.strip():
        fields.append(f'{build_jql_field_reference(field_with_value)} is not EMPTY')
    if created_from:
        value = date.strftime(created_from, '%Y-%m-%d')
        fields.append(f'created >= "{value}"')
    if created_until:
        value = date.strftime(created_until, '%Y-%m-%d')
        fields.append(f'created <= "{value}"')
    if updated_from:
        value = date.strftime(updated_from, '%Y-%m-%d')
        fields.append(f'updated >= "{value}"')
    if updated_until:
        value = date.strftime(updated_until, '%Y-%m-%d')
        fields.append(f'updated <= "{value}"')
    if status:
        fields.append(f'status = "{status}"')
    if assignee:
        fields.append(f'assignee = "{assignee}"')
    if issue_type:
        fields.append(f'type = {issue_type}')
    if search_in_active_sprint:
        fields.append('sprint in openSprints()')

    jql: str = ''
    if fields:
        jql = ' and '.join(fields)
    if jql_query:
        if jql:
            jql = f'{jql} and {jql_query}'
        else:
            jql = jql_query
    if order_by and 'order by' not in jql.lower():
        if jql:
            jql = f'{jql} order by {order_by.value}'
        else:
            jql = f'order by {order_by.value}'
    return jql


def build_jql_field_reference(field: str) -> str:
    """Builds the reference to a field in a JQL expression.

    Args:
        field: the name of a field, e.g. `Customer`, or the ID of a custom field, e.g. `customfield_10085`.

    Returns:
        The reference to the field, e.g. `"Customer"` or `cf[10085]`.
    """

    cleaned = field.strip()
    if match := re.fullmatch(r'customfield_(\d+)', cleaned):
        return f'cf[{match.group(1)}]'
    escaped = cleaned.replace('"', '\\"')
    return f'"{escaped}"'
