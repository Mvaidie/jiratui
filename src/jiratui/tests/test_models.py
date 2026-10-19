import pytest

from jiratui.models import (
    AgileBoard,
    AgileBoardTypes,
    IssuePriority,
    IssueStatus,
    IssueType,
    JiraIssue,
    JiraUser,
    RelatedJiraIssue,
    WorkItemsSearchOrderBy,
)


def _jira_issue(summary: str) -> JiraIssue:
    return JiraIssue(
        id='1',
        key='TEST-1',
        summary=summary,
        status=IssueStatus(id='1', name='To Do'),
    )


def _related_jira_issue(summary: str) -> RelatedJiraIssue:
    return RelatedJiraIssue(
        id='1',
        key='TEST-1',
        summary=summary,
        status=IssueStatus(id='1', name='To Do'),
        issue_type=IssueType(id='1', name='Task'),
    )


@pytest.mark.parametrize('issue_factory', [_jira_issue, _related_jira_issue])
@pytest.mark.parametrize(
    'summary, max_length, expected',
    [
        ('  a summary  ', None, 'a summary'),  # strips whitespace, no truncation
        ('a summary', 0, 'a summary'),  # zero disables truncation
        ('a summary', -3, 'a summary'),  # negative values disable truncation
        ('short', 10, 'short'),  # shorter than the limit stays untouched
        ('exactlyten', 10, 'exactlyten'),  # exactly the limit stays untouched
        ('a summary that is quite long', 20, 'a summary that is...'),  # truncated to max_length
        ('long summary here', 4, 'l...'),  # suffix fits within max_length
        ('long summary here', 3, 'lon'),  # max_length <= len('...') cuts without suffix
        ('long summary here', 2, 'lo'),
        ('   ', None, ''),
    ],
)
def test_cleaned_summary(issue_factory, summary, max_length, expected):
    assert issue_factory(summary).cleaned_summary(max_length) == expected


def test_jira_issue_show_assignee():
    # GIVEN
    issue = JiraIssue(
        id='1',
        assignee=JiraUser(
            account_id='1', active=True, display_name='Bart', email='bart@simpson.com'
        ),
        key='WI-1',
        summary='Test',
        status=IssueStatus(id='WI-1', name='Done'),
    )
    # THEN
    assert issue.show_assignee() == 'Bart'


def test_jira_issue_show_assignee_with_length():
    # GIVEN
    issue = JiraIssue(
        id='1',
        assignee=JiraUser(
            account_id='1', active=True, display_name='Bart Simpson', email='bart@simpson.com'
        ),
        key='WI-1',
        summary='Test',
        status=IssueStatus(id='WI-1', name='Done'),
    )
    # THEN
    assert issue.show_assignee(10) == 'Bart Simps...'


def test_jira_issue_show_assignee_with_smaller_length():
    # GIVEN
    issue = JiraIssue(
        id='1',
        assignee=JiraUser(
            account_id='1', active=True, display_name='Bart', email='bart@simpson.com'
        ),
        key='WI-1',
        summary='Test',
        status=IssueStatus(id='WI-1', name='Done'),
    )
    # THEN
    assert issue.show_assignee(20) == 'Bart'


def test_jira_issue_show_assignee_no_assignee():
    # GIVEN
    issue = JiraIssue(
        id='1',
        assignee=None,
        key='WI-1',
        summary='Test',
        status=IssueStatus(id='WI-1', name='Done'),
    )
    # THEN
    assert issue.show_assignee() == ''


def test_jira_issue_show_assignee_no_name():
    # GIVEN
    issue = JiraIssue(
        id='1',
        assignee=JiraUser(account_id='1', active=True, display_name='', email='bart@simpson.com'),
        key='WI-1',
        summary='Test',
        status=IssueStatus(id='WI-1', name='Done'),
    )
    # THEN
    assert issue.show_assignee() == 'bart@simpson.com'


def test_jira_issue_show_assignee_no_name_with_length():
    # GIVEN
    issue = JiraIssue(
        id='1',
        assignee=JiraUser(account_id='1', active=True, display_name='', email='bart@simpson.com'),
        key='WI-1',
        summary='Test',
        status=IssueStatus(id='WI-1', name='Done'),
    )
    # THEN
    assert issue.show_assignee(10) == 'bart@simps...'


def test_jira_issue_show_assignee_no_name_with_smaller_length():
    # GIVEN
    issue = JiraIssue(
        id='1',
        assignee=JiraUser(account_id='1', active=True, display_name='', email='bart@simpson.com'),
        key='WI-1',
        summary='Test',
        status=IssueStatus(id='WI-1', name='Done'),
    )
    # THEN
    assert issue.show_assignee(30) == 'bart@simpson.com'


def test_jira_issue_show_reporter():
    # GIVEN
    issue = JiraIssue(
        id='1',
        reporter=JiraUser(
            account_id='1', active=True, display_name='Bart', email='bart@simpson.com'
        ),
        key='WI-1',
        summary='Test',
        status=IssueStatus(id='WI-1', name='Done'),
    )
    # THEN
    assert issue.show_reporter() == 'Bart'


def test_jira_issue_show_reporter_with_length():
    # GIVEN
    issue = JiraIssue(
        id='1',
        reporter=JiraUser(
            account_id='1', active=True, display_name='Bart Simpson', email='bart@simpson.com'
        ),
        key='WI-1',
        summary='Test',
        status=IssueStatus(id='WI-1', name='Done'),
    )
    # THEN
    assert issue.show_reporter(10) == 'Bart Simps...'


def test_jira_issue_show_reporter_with_smaller_length():
    # GIVEN
    issue = JiraIssue(
        id='1',
        reporter=JiraUser(
            account_id='1', active=True, display_name='Bart', email='bart@simpson.com'
        ),
        key='WI-1',
        summary='Test',
        status=IssueStatus(id='WI-1', name='Done'),
    )
    # THEN
    assert issue.show_reporter(20) == 'Bart'


def test_jira_issue_show_reporter_no_reporter():
    # GIVEN
    issue = JiraIssue(
        id='1',
        reporter=None,
        key='WI-1',
        summary='Test',
        status=IssueStatus(id='WI-1', name='Done'),
    )
    # THEN
    assert issue.show_reporter() == ''


def test_jira_issue_show_reporter_no_name():
    # GIVEN
    issue = JiraIssue(
        id='1',
        reporter=JiraUser(account_id='1', active=True, display_name='', email='bart@simpson.com'),
        key='WI-1',
        summary='Test',
        status=IssueStatus(id='WI-1', name='Done'),
    )
    # THEN
    assert issue.show_reporter() == 'bart@simpson.com'


def test_jira_issue_show_reporter_no_name_with_length():
    # GIVEN
    issue = JiraIssue(
        id='1',
        reporter=JiraUser(account_id='1', active=True, display_name='', email='bart@simpson.com'),
        key='WI-1',
        summary='Test',
        status=IssueStatus(id='WI-1', name='Done'),
    )
    # THEN
    assert issue.show_reporter(10) == 'bart@simps...'


def test_jira_issue_show_reporter_no_name_with_smaller_length():
    # GIVEN
    issue = JiraIssue(
        id='1',
        reporter=JiraUser(account_id='1', active=True, display_name='', email='bart@simpson.com'),
        key='WI-1',
        summary='Test',
        status=IssueStatus(id='WI-1', name='Done'),
    )
    # THEN
    assert issue.show_reporter(30) == 'bart@simpson.com'


def test_work_items_search_order_by_choices_include_status():
    # WHEN
    choices = WorkItemsSearchOrderBy.to_choices()
    # THEN
    assert ('Status Asc', 'status asc') in choices
    assert ('Status Desc', 'status desc') in choices


@pytest.mark.parametrize(
    'priority, length, expected',
    [
        (None, 10, ''),
        (IssuePriority(id='1', name='High'), 10, 'High'),
        (IssuePriority(id='1', name='Medium priority level'), 10, 'Medium pri...'),
        (IssuePriority(id='1', name='P2: Mandatory / Critical'), 10, 'P2'),
        (IssuePriority(id='1', name='P2: Mandatory / Critical'), None, 'P2'),
        (IssuePriority(id='1', name=': no code'), None, ': no code'),
    ],
)
def test_jira_issue_show_priority(priority, length, expected):
    # GIVEN
    issue = JiraIssue(
        id='1',
        key='WI-1',
        summary='Test',
        status=IssueStatus(id='1', name='Done'),
        priority=priority,
    )
    # THEN
    assert issue.show_priority(length) == expected


@pytest.mark.parametrize(
    'issue_type, length, expected',
    [
        (None, 8, ''),
        (IssueType(id='1', name='Bug'), 8, 'Bug'),
        (IssueType(id='1', name='Technical Story'), 8, 'Technica...'),
        (IssueType(id='1', name='Technical Story'), None, 'Technical Story'),
    ],
)
def test_jira_issue_show_work_item_type(issue_type, length, expected):
    # GIVEN
    issue = JiraIssue(
        id='1',
        key='WI-1',
        summary='Test',
        status=IssueStatus(id='1', name='Done'),
        issue_type=issue_type,
    )
    # THEN
    assert issue.show_work_item_type(length) == expected


@pytest.mark.parametrize(
    'board_type, expected',
    [
        (AgileBoardTypes.SCRUM, 'Team board (Scrum)'),
        (AgileBoardTypes.KANBAN, 'Team board (Kanban)'),
        (AgileBoardTypes.SIMPLE, 'Team board (Simple)'),
    ],
)
def test_agile_board_display_name(board_type: AgileBoardTypes, expected: str):
    # GIVEN
    board = AgileBoard(id=1, name='Team board', board_type=board_type)
    # THEN
    assert board.display_name == expected
