from typing import cast
from unittest.mock import AsyncMock, MagicMock, Mock, PropertyMock, call, patch

from pydantic import SecretStr
import pytest
from textual.widgets import Select

from jiratui.api_controller.controller import APIController, APIControllerResponse
from jiratui.app import JiraApp
from jiratui.config import ApplicationConfiguration
from jiratui.models import (
    AgileBoard,
    AgileBoardTypes,
    IssueStatus,
    IssueType,
    JiraBaseIssue,
    JiraIssue,
    JiraIssueSearchResponse,
    JiraUser,
    Project,
    WorkItemsSearchOrderBy,
)
from jiratui.widgets.attachments.attachments import IssueAttachmentsWidget
from jiratui.widgets.comments.comments import IssueCommentsWidget
from jiratui.widgets.commons.users import JiraUserInput
from jiratui.widgets.create_work_item.screen import AddWorkItemScreen
from jiratui.widgets.filters import (
    ActiveSprintCheckbox,
    BoardSelectionInput,
    IssueSearchCreatedFromWidget,
    IssueSearchCreatedUntilWidget,
    IssueStatusSelectionInput,
    IssueTypeSelectionInput,
    JQLSearchWidget,
    OrderByWidget,
    ProjectSelectionInput,
    WorkItemInputWidget,
)
from jiratui.widgets.messages import SearchWorkItem
from jiratui.widgets.related_work_items.related_issues import (
    RelatedIssuesWidget,
)
from jiratui.widgets.remote_links.links import IssueRemoteLinksWidget
from jiratui.widgets.screen import MainScreen, WorkItemSearchCriteria, WorkItemSearchResult
from jiratui.widgets.screens.quit import QuitScreen
from jiratui.widgets.screens.work_item_quick_view import WorkItemQuickViewScreen
from jiratui.widgets.search import IssuesSearchResultsTable, SearchResultsContainer
from jiratui.widgets.work_item_details.details import IssueDetailsWidget
from jiratui.widgets.work_item_info.info import WorkItemInfoContainer
from jiratui.widgets.work_item_subtasks.subtasks import (
    SubtasksWidget,
)


@pytest.fixture()
def jira_users() -> list[JiraUser]:
    return [
        Mock(spec=JiraUser, display_name='Bart', account_id='1'),
        Mock(spec=JiraUser, display_name='Lisa', account_id='2'),
    ]


@pytest.fixture()
def app() -> JiraApp:
    config_mock = Mock(spec=ApplicationConfiguration)
    config_mock.configure_mock(
        jira_api_base_url='foo.bar',
        jira_api_username='foo',
        jira_api_token=SecretStr('bar'),
        jira_api_version=3,
        use_bearer_authentication=False,
        use_cert_authentication=False,
        cloud=True,
        ignore_users_without_email=True,
        default_project_key_or_id=None,
        fetch_single_project=False,
        active_sprint_on_startup=False,
        jira_account_id=None,
        tui_title=None,
        tui_custom_title=None,
        tui_title_include_jira_server_title=False,
        on_start_up_only_fetch_projects=False,
        log_file='',
        log_level='ERROR',
        enable_logging=False,
        theme=None,
        search_results_page_filtering_enabled=False,
        ssl=None,
        search_results_default_order=WorkItemsSearchOrderBy.CREATED_DESC,
        search_results_truncate_work_item_summary=15,
        search_results_style_work_item_status=None,
        search_results_style_work_item_type=None,
        search_results_per_page=10,
        search_on_startup=False,
        show_keybinding_hints=False,
        enable_recent_history=False,
        enable_goto=False,
        search_results_columns=None,
        stale_work_items_statuses=None,
        customer_field=None,
        search_results_auto_refresh_interval=None,
        styling=None,
    )
    app = JiraApp(config_mock)
    app.api = APIController(config_mock)
    app._setup_logging = MagicMock()  # type:ignore[method-assign]
    return app


@pytest.mark.parametrize(
    'key, widget',
    [
        ('p', ProjectSelectionInput),
        ('t', IssueTypeSelectionInput),
        ('s', IssueStatusSelectionInput),
        ('a', JiraUserInput),
        ('k', WorkItemInputWidget),
        ('f', IssueSearchCreatedFromWidget),
        ('u', IssueSearchCreatedUntilWidget),
        ('o', OrderByWidget),
        ('v', ActiveSprintCheckbox),
        ('j', JQLSearchWidget),
        ('1', IssuesSearchResultsTable),
        ('2', WorkItemInfoContainer),
        ('3', IssueDetailsWidget),
        ('4', IssueCommentsWidget),
        ('5', RelatedIssuesWidget),
        ('6', IssueAttachmentsWidget),
        ('7', IssueRemoteLinksWidget),
        ('8', SubtasksWidget),
    ],
)
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_quick_access_keys(
    search_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    key: str,
    widget,
    app,
):
    """Test pressing certain keys focus the correct widget."""
    async with app.run_test() as pilot:
        await pilot.press(key)
        main_screen = cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        assert isinstance(main_screen.focused, widget)


@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_show_keybinding_hints(
    search_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    app,
):
    # GIVEN
    app.config.show_keybinding_hints = True
    async with app.run_test():
        main_screen = cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        # THEN
        assert main_screen.work_item_tabs_titles == {
            'search_results_container': 'Work Items (1)',
            'work_item_info_container': 'Info (2)',
            'issue_details': 'Details (3)',
            'issue_comments': 'Comments (4)',
            'related_issues': 'Related (5)',
            'attachments': 'Attachments (6)',
            'issue_remote_links': 'Links (7)',
            'issue_subtasks': 'Subtasks (8)',
        }
        widget = main_screen.query_one(SearchResultsContainer)
        assert widget.border_title == 'Work Items (1)'


@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_show_keybinding_hints_disabled(
    search_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    app,
):
    # GIVEN
    app.config.show_keybinding_hints = False
    async with app.run_test():
        main_screen = cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        # THEN
        assert main_screen.work_item_tabs_titles == {}
        widget = main_screen.query_one(SearchResultsContainer)
        assert widget.border_title == 'Work Items'


@patch('jiratui.widgets.screen.APIController.search_projects')
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@pytest.mark.asyncio
async def test_fetch_projects(
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    search_projects_mock: AsyncMock,
    jira_api_controller,
    app,
):
    search_projects_mock.return_value = APIControllerResponse(
        result=[
            Project(id='2', name='Project B', key='P2'),
            Project(id='1', name='Project A', key='P1'),
        ]
    )
    async with app.run_test():
        main_screen = cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        assert main_screen.project_selector.selection is None
        assert main_screen.project_selector._options == [
            ('', Select.NULL),
            ('(P1) Project A', 'P1'),
            ('(P2) Project B', 'P2'),
        ]


@patch('jiratui.widgets.screen.APIController.search_projects')
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@pytest.mark.asyncio
async def test_fetch_projects_notifies_the_user_when_the_request_fails(
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    search_projects_mock: AsyncMock,
    app,
):
    """A failed request must not look like "you have no projects"."""

    # GIVEN a request that fails, e.g. because the TLS handshake could not be completed
    search_projects_mock.return_value = APIControllerResponse(
        success=False, result=[], error='ConnectError: certificate verify failed'
    )
    async with app.run_test():
        main_screen = cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        notify_mock = MagicMock()
        main_screen.notify = notify_mock  # type:ignore[method-assign]
        # WHEN
        await main_screen.fetch_projects()
        # THEN the dropdown is empty and the user is told why
        assert main_screen.project_selector._options == [('', Select.NULL)]
        notify_mock.assert_called_once_with(
            'Failed to fetch the list of projects: ConnectError: certificate verify failed',
            severity='error',
        )


@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch.object(APIController, 'search_projects')
@pytest.mark.asyncio
async def test_fetch_projects_without_initial_project_key(
    search_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    app,
):
    # GIVEN
    search_projects_mock.return_value = APIControllerResponse(
        result=[
            Project(id='2', name='Project B', key='P2'),
            Project(id='1', name='Project A', key='P1'),
        ]
    )
    async with app.run_test():
        screen = MainScreen()
        screen.initial_project_key = ''
        screen.config.fetch_single_project = True
        # WHEN
        await app.push_screen(screen)
        await app.workers.wait_for_complete()
        # THEN
        search_projects_mock.assert_has_calls([call(keys=[])])
        assert screen.project_selector.selection is None
        assert screen.project_selector._options == [
            ('', Select.NULL),
            ('(P1) Project A', 'P1'),
            ('(P2) Project B', 'P2'),
        ]


@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch.object(APIController, 'search_projects')
@pytest.mark.asyncio
async def test_fetch_projects_with_initial_project_key_fetch_single_project_true(
    search_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    app,
):
    # GIVEN
    search_projects_mock.return_value = APIControllerResponse(
        result=[
            Project(id='1', name='Project A', key='P1'),
        ]
    )
    async with app.run_test():
        screen = MainScreen()
        screen.initial_project_key = 'P1'
        screen.config.fetch_single_project = True
        # WHEN
        await app.push_screen(screen)
        await app.workers.wait_for_complete()
        # THEN
        search_projects_mock.assert_has_calls([call(keys=['P1'])])
        assert screen.project_selector.selection == 'P1'
        assert screen.project_selector._options == [
            ('', Select.NULL),
            ('(P1) Project A', 'P1'),
        ]


@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch.object(APIController, 'search_projects')
@pytest.mark.asyncio
async def test_fetch_projects_with_initial_project_key_fetch_single_project_false(
    search_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    app,
):
    # GIVEN
    search_projects_mock.return_value = APIControllerResponse(
        result=[
            Project(id='1', name='Project A', key='P1'),
            Project(id='2', name='Project B', key='P2'),
        ]
    )
    async with app.run_test():
        screen = MainScreen()
        screen.initial_project_key = 'P1'
        screen.config.fetch_single_project = False
        # WHEN
        await app.push_screen(screen)
        await app.workers.wait_for_complete()
        # THEN
        search_projects_mock.assert_has_calls([call(keys=[])])
        assert screen.project_selector.selection == 'P1'
        assert screen.project_selector._options == [
            ('', Select.NULL),
            ('(P1) Project A', 'P1'),
            ('(P2) Project B', 'P2'),
        ]


@patch('jiratui.widgets.screen.APIController.status')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_mount_fetch_statuses_without_initial_project_key_without_using_project_workflow(
    search_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    status_mock: AsyncMock,
    jira_api_controller,
    app,
):
    # GIVEN
    app.config.on_start_up_only_fetch_projects = False
    status_mock.return_value = APIControllerResponse(
        result=[
            IssueStatus(id='2', name='To Do', description='A task to do'),
            IssueStatus(id='1', name='Done', description='A task done'),
        ]
    )
    # WHEN
    async with app.run_test():
        main_screen = cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        # THEN
        assert main_screen.initial_project_key is None
        assert main_screen.project_selector.selection is None
        status_mock.assert_called_once()
        assert main_screen.available_issues_status == [('Done', '1'), ('To Do', '2')]
        assert main_screen.issue_status_selector.statuses == [('Done', '1'), ('To Do', '2')]


@patch('jiratui.widgets.screen.APIController.status')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_mount_fetch_statuses_without_initial_project_key_using_project_workflow(
    search_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    status_mock: AsyncMock,
    jira_api_controller,
    app,
):
    # GIVEN
    app.config.on_start_up_only_fetch_projects = True
    status_mock.return_value = APIControllerResponse(
        result=[
            IssueStatus(id='2', name='To Do', description='A task to do'),
            IssueStatus(id='1', name='Done', description='A task done'),
        ]
    )
    # WHEN
    async with app.run_test():
        main_screen = cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        # THEN
        assert main_screen.initial_project_key is None
        assert main_screen.project_selector.selection is None
        status_mock.assert_not_called()
        assert main_screen.available_issues_status == []
        assert main_screen.issue_status_selector.statuses is None


@patch('jiratui.widgets.screen.APIController.status')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_mount_fetch_statuses_without_initial_project_key_status_error(
    search_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    status_mock: AsyncMock,
    jira_api_controller,
    app,
):
    # GIVEN
    status_mock.return_value = APIControllerResponse(success=False)
    app.config.on_start_up_only_fetch_projects = False
    # WHEN
    async with app.run_test():
        main_screen = cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        # THEN
        assert main_screen.initial_project_key is None
        assert main_screen.project_selector.selection is None
        status_mock.assert_called_once()
        assert main_screen.available_issues_status == []
        assert main_screen.issue_status_selector.statuses == []


@patch('jiratui.widgets.screen.APIController.get_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_mount_fetch_issues_types_without_initial_project_key(
    search_projects_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    get_issue_types_mock: AsyncMock,
    jira_api_controller,
    app,
):
    # GIVEN
    app.config.on_start_up_only_fetch_projects = False
    get_issue_types_mock.return_value = APIControllerResponse(
        result=[
            IssueType(
                id='1',
                name='Task',
                scope_project=None,
            )
        ]
    )
    # WHEN
    async with app.run_test():
        main_screen = cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        # THEN
        assert main_screen.initial_project_key is None
        assert main_screen.project_selector.selection is None
        get_issue_types_mock.assert_called_once()
        assert main_screen.issue_type_selector._options == [('', Select.NULL), ('Task', '1')]


@patch('jiratui.widgets.screen.APIController.get_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_mount_fetch_issues_types_without_initial_project_key_fetch_types_error(
    search_projects_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    get_issue_types_mock: AsyncMock,
    jira_api_controller,
    app,
):
    # GIVEN
    app.config.on_start_up_only_fetch_projects = False
    get_issue_types_mock.return_value = APIControllerResponse(success=False)
    # WHEN
    async with app.run_test():
        main_screen = cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        # THEN
        assert main_screen.initial_project_key is None
        assert main_screen.project_selector.selection is None
        get_issue_types_mock.assert_called_once()
        assert main_screen.issue_type_selector._options == [('', Select.NULL)]


@pytest.mark.parametrize('expression_id, expected_expression', [(1, 'sprint=2'), (2, None)])
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_mount_without_initial_project_key_set_jql_expression(
    search_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    expression_id: int,
    expected_expression: str,
    jira_api_controller,
    app,
):
    # GIVEN
    app.initial_jql_expression_id = expression_id
    app.config.pre_defined_jql_expressions = {1: {'expression': 'sprint=2'}}
    # WHEN
    async with app.run_test():
        main_screen = cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        # THEN
        assert main_screen.jql_expression_input.expression == expected_expression


@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.APIController.search_projects')
@pytest.mark.asyncio
async def test_select_project(
    search_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    jira_api_controller,
    app,
):
    # GIVEN
    app.config.on_start_up_only_fetch_projects = False
    search_projects_mock.return_value = APIControllerResponse(
        result=[
            Project(id='2', name='Project B', key='P2'),
            Project(id='1', name='Project A', key='P1'),
        ]
    )
    fetch_issue_types_mock.return_value = [(1, 'Task')]
    fetch_statuses_mock.return_value = [(1, 'Done')]
    async with app.run_test():
        main_screen = cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        # WHEN
        main_screen.project_selector.value = 'P1'
        # THEN
        fetch_issue_types_mock.assert_called_once()
        fetch_statuses_mock.assert_called_once()
        assert main_screen.issue_type_selector._options == [('', Select.NULL)]
        assert main_screen.issue_status_selector.statuses is None
        assert main_screen.available_issues_status == []
        assert main_screen.project_selector.selection == 'P1'


@patch('jiratui.widgets.screen.MainScreen.action_search')
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_search_button_triggers_issue_search(
    search_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    action_search_mock: AsyncMock,
    app,
):
    async with app.run_test() as pilot:
        cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        # WHEN
        await pilot.press('ctrl+r')
        # THEN
        action_search_mock.assert_called_once()


@patch('jiratui.widgets.screen.MainScreen.search_issues')
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_click_search_button_resets_widgets(
    search_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    search_issues_mock: AsyncMock,
    app,
):
    async with app.run_test() as pilot:
        main_screen = cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        # WHEN
        await pilot.press('ctrl+r')
        # THEN
        search_issues_mock.assert_called_once()
        assert main_screen.issue_comments_widget.comments is None
        assert main_screen.issue_comments_widget._work_item_key is None
        assert main_screen.related_issues_widget.issues is None
        assert main_screen.related_issues_widget._issue_key is None
        assert main_screen.issue_remote_links_widget.issue_key is None
        assert main_screen.issue_attachments_widget.attachments is None
        assert main_screen.issue_attachments_widget.issue_key is None
        assert main_screen.issue_child_work_items_widget.issues is None
        assert main_screen.issue_child_work_items_widget._work_item_key is None
        assert main_screen.issue_child_work_items_widget._work_item_project_key is None
        assert main_screen.search_results_table.token_by_page == {}
        assert main_screen.search_results_table.page == 1
        assert main_screen.issue_info_container.issue_summary_widget.visible is False


@patch.object(JiraApp, 'copy_to_clipboard')
@patch('jiratui.widgets.screen.MainScreen._search_work_items')
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_copy_work_item_key_to_clipboard(
    search_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    search_work_items_mock: AsyncMock,
    copy_to_clipboard: Mock,
    jira_issues: list[JiraIssue],
    app,
):
    search_work_items_mock.return_value = WorkItemSearchResult(
        total=1, start=1, end=1, response=JiraIssueSearchResponse(issues=jira_issues)
    )
    async with app.run_test() as pilot:
        cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        # WHEN
        await pilot.press('ctrl+r')
        await pilot.press('ctrl+k')
        await pilot.app.workers.wait_for_complete()
        # THEN
        search_work_items_mock.assert_called_once()
        copy_to_clipboard.assert_called_once_with('key-1')


@patch.object(JiraApp, 'copy_to_clipboard')
@patch('jiratui.widgets.screen.MainScreen._search_work_items')
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_copy_work_item_key_to_clipboard_no_item_to_copy(
    search_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    search_work_items_mock: AsyncMock,
    copy_to_clipboard: Mock,
    app,
):
    search_work_items_mock.return_value = WorkItemSearchResult(
        total=1, start=1, end=1, response=JiraIssueSearchResponse(issues=[])
    )
    async with app.run_test() as pilot:
        cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        # WHEN
        await pilot.press('ctrl+r')
        await pilot.press('ctrl+k')
        await pilot.app.workers.wait_for_complete()
        # THEN
        search_work_items_mock.assert_called_once()
        copy_to_clipboard.assert_not_called()


@patch('jiratui.widgets.screen.build_external_url_for_issue')
@patch.object(JiraApp, 'copy_to_clipboard')
@patch('jiratui.widgets.screen.MainScreen._search_work_items')
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_copy_work_item_url_to_clipboard(
    search_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    search_work_items_mock: AsyncMock,
    copy_to_clipboard: Mock,
    build_external_url_for_issue_mock: Mock,
    jira_issues: list[JiraIssue],
    app,
):
    build_external_url_for_issue_mock.return_value = 'http://foo.bar'
    search_work_items_mock.return_value = WorkItemSearchResult(
        total=1, start=1, end=1, response=JiraIssueSearchResponse(issues=jira_issues)
    )
    async with app.run_test() as pilot:
        cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        # WHEN
        await pilot.press('ctrl+r')
        await pilot.press('ctrl+j')
        await pilot.app.workers.wait_for_complete()
        # THEN
        search_work_items_mock.assert_called_once()
        copy_to_clipboard.assert_called_once_with('http://foo.bar')


@patch('jiratui.widgets.screen.build_external_url_for_issue')
@patch.object(JiraApp, 'copy_to_clipboard')
@patch('jiratui.widgets.screen.MainScreen._search_work_items')
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_copy_work_item_url_to_clipboard_without_results(
    search_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    search_work_items_mock: AsyncMock,
    copy_to_clipboard: Mock,
    build_external_url_for_issue_mock: Mock,
    app,
):
    build_external_url_for_issue_mock.return_value = 'http://foo.bar'
    search_work_items_mock.return_value = WorkItemSearchResult(
        total=1, start=1, end=1, response=JiraIssueSearchResponse(issues=[])
    )
    async with app.run_test() as pilot:
        cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        # WHEN
        await pilot.press('ctrl+r')
        await pilot.press('ctrl+j')
        await pilot.app.workers.wait_for_complete()
        # THEN
        search_work_items_mock.assert_called_once()
        copy_to_clipboard.assert_not_called()


@patch('jiratui.widgets.screen.build_external_url_for_issue')
@patch.object(JiraApp, 'copy_to_clipboard')
@patch('jiratui.widgets.screen.MainScreen._search_work_items')
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_copy_work_item_url_to_clipboard_without_url(
    search_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    search_work_items_mock: AsyncMock,
    copy_to_clipboard: Mock,
    build_external_url_for_issue_mock: Mock,
    jira_issues: list[JiraIssue],
    app,
):
    build_external_url_for_issue_mock.return_value = ''
    search_work_items_mock.return_value = WorkItemSearchResult(
        total=1, start=1, end=1, response=JiraIssueSearchResponse(issues=jira_issues)
    )
    async with app.run_test() as pilot:
        cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        # WHEN
        await pilot.press('ctrl+r')
        await pilot.press('ctrl+j')
        await pilot.app.workers.wait_for_complete()
        # THEN
        search_work_items_mock.assert_called_once()
        copy_to_clipboard.assert_not_called()


@patch.object(ProjectSelectionInput, 'selection', PropertyMock(return_value=None))
@patch.object(APIController, 'search_users')
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_search_users_with_custom_search_function_by_query(
    fetch_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    search_users_mock: AsyncMock,
    app,
):
    async with app.run_test() as pilot:
        # WHEN
        await pilot.press('tab')
        await pilot.press('tab')
        await pilot.press('tab')
        await pilot.press('t')
        await pilot.press('e')
        await pilot.press('s')
        # THEN
        search_users_mock.assert_called_once_with(email_or_name='tes')


@patch.object(ProjectSelectionInput, 'selection', PropertyMock(return_value='PR1'))
@patch.object(APIController, 'search_users_assignable_to_issue')
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_search_users_with_custom_search_function_by_project(
    fetch_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    search_users_assignable_to_issue_mock: AsyncMock,
    app,
):
    async with app.run_test() as pilot:
        # WHEN
        await pilot.press('tab')
        await pilot.press('tab')
        await pilot.press('tab')
        await pilot.press('t')
        await pilot.press('e')
        await pilot.press('s')
        # THEN
        search_users_assignable_to_issue_mock.assert_called_once_with(
            project_id_or_key='PR1', query='tes'
        )


@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_create_work_item_subtask(
    fetch_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    app,
):
    async with app.run_test() as pilot:
        # WHEN
        app.screen.post_message(
            SubtasksWidget.CreateSubtask(project_key='PR1', parent_work_item_key='key-1')
        )
        await pilot.pause()
        # THEN
        assert isinstance(app.screen, AddWorkItemScreen)


@patch('jiratui.widgets.screen.MainScreen.action_search')
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_load_related_work_item_with_key(
    fetch_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    action_search_mock: AsyncMock,
    app,
):
    async with app.run_test() as pilot:
        cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        # WHEN
        app.screen.issue_key_input.value = ''
        app.screen.post_message(SearchWorkItem('key-1'))
        await pilot.pause()
        # THEN
        assert isinstance(app.screen, MainScreen)
        assert app.screen.issue_key_input.value == 'key-1'
        action_search_mock.assert_called_once()


@patch('jiratui.widgets.screen.MainScreen.action_search')
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_load_related_work_item_without_key(
    fetch_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    action_search_mock: AsyncMock,
    app,
):
    async with app.run_test() as pilot:
        cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        # WHEN
        app.screen.issue_key_input.value = ''
        app.screen.post_message(SearchWorkItem(''))
        await pilot.pause()
        # THEN
        assert isinstance(app.screen, MainScreen)
        assert app.screen.issue_key_input.value == ''
        action_search_mock.assert_not_called()


@patch('jiratui.widgets.screen.MainScreen.fetch_issue')
@patch('jiratui.widgets.screen.MainScreen.action_search')
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_handle_search_work_item_message_with_key_search_and_fetch(
    fetch_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    action_search_mock: AsyncMock,
    fetch_issue_mock: AsyncMock,
    app,
):
    async with app.run_test() as pilot:
        cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        # WHEN
        app.screen.issue_key_input.value = ''
        app.screen.post_message(SearchWorkItem('key-1'))
        await pilot.pause()
        # THEN
        assert isinstance(app.screen, MainScreen)
        assert app.screen.issue_key_input.value == 'key-1'
        action_search_mock.assert_called_once()
        fetch_issue_mock.assert_called_once_with('key-1')


@patch('jiratui.widgets.screen.MainScreen.fetch_issue')
@patch('jiratui.widgets.screen.MainScreen.action_search')
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_handle_search_work_item_message_without_key_no_search_no_fetching(
    fetch_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    action_search_mock: AsyncMock,
    fetch_issue_mock: AsyncMock,
    app,
):
    async with app.run_test() as pilot:
        cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        # WHEN
        app.screen.issue_key_input.value = ''
        app.screen.post_message(SearchWorkItem(''))
        await pilot.pause()
        # THEN
        assert isinstance(app.screen, MainScreen)
        assert app.screen.issue_key_input.value == ''
        action_search_mock.assert_not_called()
        fetch_issue_mock.assert_not_called()


@patch.object(APIController, 'create_work_item')
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_show_quick_view_screen_after_creating_work_item_view_work_item_after_creation_enabled(
    fetch_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    create_work_item_mock: AsyncMock,
    app,
):
    # GIVEN
    app.config.view_work_item_after_creation = True
    create_work_item_mock.return_value = APIControllerResponse(
        result=JiraBaseIssue(id='2', key='key-2')
    )
    async with app.run_test() as pilot:
        screen = cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        # WHEN
        await screen.create_work_item({'summary': 'some value here'})
        await pilot.pause()
        # THEN
        assert isinstance(app.screen, WorkItemQuickViewScreen)
        create_work_item_mock.assert_called_once_with({'summary': 'some value here'})


@patch('jiratui.widgets.screen.MainScreen._add_item_to_recent_history')
@patch.object(APIController, 'create_work_item')
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_create_work_item_with_recent_history_enabled(
    fetch_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    create_work_item_mock: AsyncMock,
    add_item_to_recent_history_mock: Mock,
    app,
):
    # GIVEN
    app.config.view_work_item_after_creation = False
    app.config.enable_recent_history = True
    create_work_item_mock.return_value = APIControllerResponse(
        result=JiraBaseIssue(id='2', key='key-2')
    )
    async with app.run_test() as pilot:
        cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        # WHEN
        await app.screen.create_work_item({'summary': 'some value here'})
        await pilot.pause()
        # THEN
        add_item_to_recent_history_mock.assert_called_once_with('key-2', '', '', '')


@patch.object(APIController, 'transition_issue_status')
@patch.object(APIController, 'create_work_item')
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_create_work_item_with_status_transition(
    fetch_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    create_work_item_mock: AsyncMock,
    transition_issue_status_mock: AsyncMock,
    app,
):
    """Creating a work item when the status field is set will request the API to transition the status of the recently
    created work item."""
    # GIVEN
    app.config.view_work_item_after_creation = False
    app.config.enable_recent_history = False
    create_work_item_mock.return_value = APIControllerResponse(
        result=JiraBaseIssue(id='2', key='key-2')
    )
    async with app.run_test() as pilot:
        screen = cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        # WHEN
        await screen.create_work_item({'summary': 'some value here', 'status': '1'})
        await pilot.pause()
        # THEN
        transition_issue_status_mock.assert_called_once_with('key-2', '1')


@patch.object(APIController, 'transition_issue_status')
@patch.object(APIController, 'create_work_item')
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_create_work_item_without_status_transition(
    fetch_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    create_work_item_mock: AsyncMock,
    transition_issue_status_mock: AsyncMock,
    app,
):
    """Creating a work item when the status field is not set will not request the API to transition the status of the
    recently created work item."""
    # GIVEN
    app.config.view_work_item_after_creation = False
    app.config.enable_recent_history = False
    create_work_item_mock.return_value = APIControllerResponse(
        result=JiraBaseIssue(id='2', key='key-2')
    )
    async with app.run_test() as pilot:
        screen = cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        # WHEN
        await screen.create_work_item({'summary': 'some value here'})
        await pilot.pause()
        # THEN
        transition_issue_status_mock.assert_not_called()


@patch('jiratui.widgets.screen.MainScreen._add_item_to_recent_history')
@patch('jiratui.widgets.screen.MainScreen._open_quick_view_screen')
@patch.object(APIController, 'transition_issue_status')
@patch.object(APIController, 'create_work_item')
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_create_work_item_fails_to_create_item(
    fetch_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    create_work_item_mock: AsyncMock,
    transition_issue_status_mock: AsyncMock,
    open_quick_view_screen_mock: AsyncMock,
    add_item_to_recent_history_mock: Mock,
    app,
):
    """When the API fails to create the work item then the work item's status is not transitioned and the app does not
    open the quick view and does not update the recent history."""
    # GIVEN
    app.config.view_work_item_after_creation = True
    app.config.enable_recent_history = True
    create_work_item_mock.return_value = APIControllerResponse(success=False, result=None)
    async with app.run_test() as pilot:
        screen = cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        # WHEN
        await screen.create_work_item({'summary': 'some value here', 'status': '1'})
        await pilot.pause()
        # THEN
        transition_issue_status_mock.assert_not_called()
        open_quick_view_screen_mock.assert_not_called()
        add_item_to_recent_history_mock.assert_not_called()
        assert not screen.loading_container.display


@patch('jiratui.widgets.screen.MainScreen._add_item_to_recent_history')
@patch.object(APIController, 'create_work_item')
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_create_work_item_with_recent_history_disabled(
    fetch_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    create_work_item_mock: AsyncMock,
    add_item_to_recent_history_mock: Mock,
    app,
):
    # GIVEN
    app.config.view_work_item_after_creation = False
    app.config.enable_recent_history = False
    create_work_item_mock.return_value = APIControllerResponse(
        result=JiraBaseIssue(id='2', key='key-2')
    )
    async with app.run_test() as pilot:
        screen = cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        # WHEN
        await screen.create_work_item({'summary': 'some value here'})
        await pilot.pause()
        # THEN
        add_item_to_recent_history_mock.assert_not_called()


@patch.object(APIController, 'create_work_item')
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_show_quick_view_screen_after_creating_work_item_view_work_item_after_creation_disabled(
    fetch_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    create_work_item_mock: AsyncMock,
    app,
):
    # GIVEN
    app.config.view_work_item_after_creation = False
    create_work_item_mock.return_value = APIControllerResponse(
        result=JiraBaseIssue(id='2', key='key-2')
    )
    async with app.run_test() as pilot:
        screen = cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        # WHEN
        await screen.create_work_item({'summary': 'some value here'})
        await pilot.pause()
        # THEN
        assert isinstance(app.screen, MainScreen)
        create_work_item_mock.assert_called_once_with({'summary': 'some value here'})


@patch.object(MainScreen, '_load_work_item')
@patch.object(APIController, 'create_work_item')
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_show_quick_view_screen_after_creating_work_dismiss_with_search(
    fetch_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    create_work_item_mock: AsyncMock,
    load_work_item_mock: Mock,
    app,
):
    # GIVEN
    app.config.view_work_item_after_creation = True
    create_work_item_mock.return_value = APIControllerResponse(
        result=JiraBaseIssue(id='2', key='key-2')
    )
    async with app.run_test() as pilot:
        screen = cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        # WHEN
        await screen.create_work_item({'summary': 'some value here'})
        await pilot.pause()
        assert isinstance(app.screen, WorkItemQuickViewScreen)
        await pilot.press('ctrl+r')  # hit search to dismiss and search
        # THEN
        assert isinstance(app.screen, MainScreen)
        create_work_item_mock.assert_called_once_with({'summary': 'some value here'})
        load_work_item_mock.assert_called_once_with('key-2')


@patch('jiratui.widgets.screens.work_item_quick_view.get_style_for_work_item_priority')
@patch('jiratui.widgets.screens.work_item_quick_view.get_style_for_work_item_type')
@patch('jiratui.widgets.screens.work_item_quick_view.get_style_for_work_item_status')
@patch.object(APIController, 'get_issue')
@patch.object(MainScreen, '_load_work_item')
@patch.object(APIController, 'create_work_item')
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_show_quick_view_screen_after_creating_work_dismiss_with_row_selection_issue_key(
    fetch_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    create_work_item_mock: AsyncMock,
    load_work_item_mock: Mock,
    get_issue_mock: AsyncMock,
    get_style_for_work_item_status_mock: Mock,
    get_style_for_work_item_type_mock: Mock,
    get_style_for_work_item_priority_mock: Mock,
    jira_issues: list[JiraIssue],
    app,
):
    # GIVEN
    get_style_for_work_item_status_mock.return_value = ''
    get_style_for_work_item_type_mock.return_value = ''
    get_style_for_work_item_priority_mock.return_value = ''
    app.config.view_work_item_after_creation = True
    create_work_item_mock.return_value = APIControllerResponse(
        result=JiraBaseIssue(id='2', key='key-2')
    )
    get_issue_mock.return_value = APIControllerResponse(
        result=JiraIssueSearchResponse(issues=[jira_issues[1]])
    )
    async with app.run_test() as pilot:
        screen = cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        # WHEN
        await screen.create_work_item({'summary': 'some value here'})
        await pilot.pause()
        assert isinstance(app.screen, WorkItemQuickViewScreen)
        await pilot.press('tab')
        await pilot.press('enter')
        # THEN
        assert isinstance(app.screen, MainScreen)
        create_work_item_mock.assert_called_once_with({'summary': 'some value here'})
        load_work_item_mock.assert_called_once_with('key-2')


@patch('jiratui.widgets.screens.work_item_quick_view.get_style_for_work_item_priority')
@patch('jiratui.widgets.screens.work_item_quick_view.get_style_for_work_item_type')
@patch('jiratui.widgets.screens.work_item_quick_view.get_style_for_work_item_status')
@patch.object(APIController, 'get_issue')
@patch.object(MainScreen, '_load_work_item')
@patch.object(APIController, 'create_work_item')
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_show_quick_view_screen_after_creating_work_dismiss_with_row_selection_parent_key(
    fetch_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    create_work_item_mock: AsyncMock,
    load_work_item_mock: Mock,
    get_issue_mock: AsyncMock,
    get_style_for_work_item_status_mock: Mock,
    get_style_for_work_item_type_mock: Mock,
    get_style_for_work_item_priority_mock: Mock,
    jira_issues: list[JiraIssue],
    app,
):
    # GIVEN
    get_style_for_work_item_status_mock.return_value = ''
    get_style_for_work_item_type_mock.return_value = ''
    get_style_for_work_item_priority_mock.return_value = ''
    app.config.view_work_item_after_creation = True
    create_work_item_mock.return_value = APIControllerResponse(
        result=JiraBaseIssue(id='2', key='key-2')
    )
    get_issue_mock.return_value = APIControllerResponse(
        result=JiraIssueSearchResponse(issues=[jira_issues[1]])
    )
    async with app.run_test() as pilot:
        screen = cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        # WHEN
        await screen.create_work_item({'summary': 'some value here'})
        await pilot.pause()
        assert isinstance(app.screen, WorkItemQuickViewScreen)
        await pilot.press('tab')
        await pilot.press('down')
        await pilot.press('enter')
        # THEN
        assert isinstance(app.screen, MainScreen)
        create_work_item_mock.assert_called_once_with({'summary': 'some value here'})
        load_work_item_mock.assert_called_once_with('P2')


@patch.object(MainScreen, '_load_work_item')
@patch.object(APIController, 'create_work_item')
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_show_quick_view_screen_after_creating_work_dismiss_with_escape(
    fetch_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    create_work_item_mock: AsyncMock,
    load_work_item_mock: Mock,
    app,
):
    # GIVEN
    app.config.view_work_item_after_creation = True
    create_work_item_mock.return_value = APIControllerResponse(
        result=JiraBaseIssue(id='2', key='key-2')
    )
    async with app.run_test() as pilot:
        screen = cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        # WHEN
        await screen.create_work_item({'summary': 'some value here'})
        await pilot.pause()
        assert isinstance(app.screen, WorkItemQuickViewScreen)
        await pilot.press('escape')  # dismiss with escape does not trigger search
        # THEN
        assert isinstance(app.screen, MainScreen)
        create_work_item_mock.assert_called_once_with({'summary': 'some value here'})
        load_work_item_mock.assert_not_called()


# @patch.object(APIController, 'transition_issue_status')
@patch.object(APIController, 'create_work_item')
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_create_work_item_without_data_to_add(
    fetch_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    create_work_item_mock: AsyncMock,
    # transition_issue_status_mock: AsyncMock,
    app,
):
    """Creating a work item when the status field is not set will not request the API to transition the status of the
    recently created work item."""
    # GIVEN
    app.config.view_work_item_after_creation = False
    app.config.enable_recent_history = False
    create_work_item_mock.return_value = APIControllerResponse(
        result=JiraBaseIssue(id='2', key='key-2')
    )
    async with app.run_test() as pilot:
        screen = cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        # WHEN
        await screen.create_work_item({})
        await pilot.pause()
        # THEN
        create_work_item_mock.assert_not_called()


@patch.object(APIController, 'create_work_item')
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_create_work_item_with_data_to_add(
    fetch_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    create_work_item_mock: AsyncMock,
    app,
):
    """Creating a work item when the status field is not set will not request the API to transition the status of the
    recently created work item."""
    # GIVEN
    app.config.view_work_item_after_creation = False
    app.config.enable_recent_history = False
    create_work_item_mock.return_value = APIControllerResponse(
        result=JiraBaseIssue(id='2', key='key-2')
    )
    async with app.run_test() as pilot:
        screen = cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        # WHEN
        await screen.create_work_item(
            {
                'summary': 'some value here',
                'project_key': 'P1',
                'parent_key': 'WI-100',
                'issue_type_id': '1000',
                'assignee_account_id': '12345',
                'reporter_account_id': '09876',
                'description': 'some text here',
                'duedate': '2026-12-31',
                'priority': '1',
                'status': '10001',
                'field_1': '1',
            }
        )
        await pilot.pause()
        # THEN
        create_work_item_mock.assert_awaited_once_with(
            {
                'summary': 'some value here',
                'project_key': 'P1',
                'parent_key': 'WI-100',
                'issue_type_id': '1000',
                'assignee_account_id': '12345',
                'reporter_account_id': '09876',
                'description': 'some text here',
                'duedate': '2026-12-31',
                'priority': '1',
                'status': '10001',
            },
            field_1='1',
        )


@patch('jiratui.widgets.screen.MainScreen._add_item_to_recent_history')
@patch.object(APIController, 'get_issue')
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_fetch_issue_with_recent_history_enabled(
    fetch_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    get_issue_mock: AsyncMock,
    add_item_to_recent_history_mock: Mock,
    jira_issues: list[JiraIssue],
    app,
):
    # GIVEN
    app.config.show_issue_web_links = False
    app.config.enable_updating_additional_fields = False
    app.config.enable_recent_history = True
    get_issue_mock.return_value = APIControllerResponse(
        result=JiraIssueSearchResponse(issues=[jira_issues[1]])
    )
    async with app.run_test():
        cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        # WHEN
        await app.screen.fetch_issue('key-2')
        await app.workers.wait_for_complete()
        # THEN
        add_item_to_recent_history_mock.assert_called_once_with(
            key='key-2', item_type='Bug', status='Done', summary='qwerty'
        )


@patch('jiratui.widgets.screen.MainScreen._add_item_to_recent_history')
@patch.object(APIController, 'get_issue')
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_fetch_issue_with_recent_history_disabled(
    fetch_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    get_issue_mock: AsyncMock,
    add_item_to_recent_history_mock: Mock,
    jira_issues: list[JiraIssue],
    app,
):
    # GIVEN
    app.config.show_issue_web_links = False
    app.config.enable_updating_additional_fields = False
    app.config.enable_recent_history = False
    get_issue_mock.return_value = APIControllerResponse(
        result=JiraIssueSearchResponse(issues=[jira_issues[1]])
    )
    async with app.run_test():
        cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        # WHEN
        await app.screen.fetch_issue('key-2')
        await app.workers.wait_for_complete()
        # THEN
        add_item_to_recent_history_mock.assert_not_called()


@patch('jiratui.widgets.screen.MainScreen._add_item_to_recent_history')
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_process_message_update_recent_history_with_recent_history_enabled(
    fetch_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    # get_issue_mock: AsyncMock,
    add_item_to_recent_history_mock: Mock,
    app,
):
    # GIVEN
    app.config.enable_recent_history = True
    async with app.run_test() as pilot:
        cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        # WHEN
        await app.workers.wait_for_complete()
        app.screen.post_message(
            IssueDetailsWidget.UpdateRecentHistory(
                work_item_key='key-2', item_type='Bug', status='Done', summary='qwerty'
            )
        )
        await pilot.pause()
        # THEN
        add_item_to_recent_history_mock.assert_called_once_with('key-2', 'Bug', 'Done', 'qwerty')


@patch('jiratui.widgets.screen.MainScreen._add_item_to_recent_history')
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_process_message_update_recent_history_with_recent_history_disabled(
    fetch_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    # get_issue_mock: AsyncMock,
    add_item_to_recent_history_mock: Mock,
    app,
):
    # GIVEN
    app.config.enable_recent_history = False
    async with app.run_test() as pilot:
        cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        # WHEN
        await app.workers.wait_for_complete()
        app.screen.post_message(
            IssueDetailsWidget.UpdateRecentHistory(
                work_item_key='key-2', item_type='Bug', status='Done', summary='qwerty'
            )
        )
        await pilot.pause()
        # THEN
        add_item_to_recent_history_mock.assert_not_called()


@patch('jiratui.widgets.screen.MainScreen._load_work_item')
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_handle_search_work_item_message(
    fetch_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    # get_issue_mock: AsyncMock,
    load_work_item_mock: Mock,
    app,
):
    # GIVEN
    app.config.enable_recent_history = True
    async with app.run_test() as pilot:
        cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        # WHEN
        await app.workers.wait_for_complete()
        app.screen.post_message(SearchWorkItem('key-2'))
        await pilot.pause()
        # THEN
        load_work_item_mock.assert_called_once_with('key-2')


@patch('jiratui.widgets.screen.MainScreen._load_work_item')
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_handle_search_work_item_message_without_work_item_key(
    fetch_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    # get_issue_mock: AsyncMock,
    load_work_item_mock: Mock,
    app,
):
    # GIVEN
    app.config.enable_recent_history = True
    async with app.run_test() as pilot:
        cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        # WHEN
        await app.workers.wait_for_complete()
        app.screen.post_message(SearchWorkItem(''))
        await pilot.pause()
        # THEN
        load_work_item_mock.assert_not_called()


@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_board_selector_is_disabled_without_project(
    fetch_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    app,
):
    async with app.run_test():
        main_screen = cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        # THEN
        assert main_screen.board_selector.disabled is True
        assert main_screen.board_selector.selection is None


@patch.object(APIController, 'get_project_boards')
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_selecting_a_project_fetches_its_boards(
    fetch_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    get_project_boards_mock: AsyncMock,
    app,
):
    # GIVEN
    get_project_boards_mock.return_value = APIControllerResponse(
        result=[AgileBoard(id=84, name='scrum board', board_type=AgileBoardTypes.SCRUM)]
    )
    async with app.run_test() as pilot:
        main_screen = cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        # WHEN
        main_screen.project_selector.projects = {
            'projects': [Project(id='1', name='Project 1', key='P1')],
            'selection': 'P1',
        }
        await pilot.pause()
        await app.workers.wait_for_complete()
        await pilot.pause()
        await pilot.press('b')
        # THEN
        get_project_boards_mock.assert_awaited_once_with('P1')
        assert main_screen.board_selector.disabled is False
        assert isinstance(app.focused, BoardSelectionInput)
        main_screen.board_selector.value = 84
        assert main_screen.board_selector.selection == 84


@patch.object(APIController, 'count_issues')
@patch.object(APIController, 'search_issues')
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_search_work_items_by_board(
    fetch_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    search_issues_mock: AsyncMock,
    count_issues_mock: AsyncMock,
    app,
):
    # GIVEN
    search_issues_mock.return_value = APIControllerResponse(
        result=JiraIssueSearchResponse(issues=[])
    )
    count_issues_mock.return_value = APIControllerResponse(result=0)
    app.config.enable_advanced_full_text_search = False
    async with app.run_test() as pilot:
        main_screen = cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        main_screen.board_selector.boards = [('scrum board', 84)]
        await pilot.pause()
        main_screen.board_selector.value = 84
        # WHEN
        await main_screen._search_work_items()
        # THEN
        assert search_issues_mock.call_args.kwargs['board_id'] == 84
        assert count_issues_mock.call_args.kwargs['board_id'] == 84


def _work_items_search_result(keys: list[str]) -> WorkItemSearchResult:
    issues = [
        JiraIssue(
            id=key.split('-')[1],
            key=key,
            summary=f'summary of {key}',
            status=IssueStatus(id='1', name='To Do'),
            issue_type=IssueType(id='1', name='Task'),
        )
        for key in keys
    ]
    return WorkItemSearchResult(
        total=len(issues),
        start=1,
        end=len(issues),
        response=JiraIssueSearchResponse(issues=issues),
    )


@patch('jiratui.widgets.screen.MainScreen._search_work_items')
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_refresh_search_results_keeps_highlighted_work_item_and_focus(
    fetch_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    search_work_items_mock: AsyncMock,
    app,
):
    # GIVEN
    app.config.search_results_truncate_work_item_summary = 0
    app.config.search_results_style_work_item_status = False
    app.config.search_results_style_work_item_type = False
    search_work_items_mock.side_effect = [
        _work_items_search_result(['WI-1', 'WI-2', 'WI-3']),
        # a new work item is found when refreshing the results
        _work_items_search_result(['WI-4', 'WI-1', 'WI-2', 'WI-3']),
    ]
    async with app.run_test() as pilot:
        main_screen = cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        table = main_screen.search_results_table
        await main_screen.search_issues()
        await pilot.pause()
        table.move_cursor(row=1)
        await pilot.pause()
        main_screen.jql_expression_input.focus()
        await pilot.pause()
        # WHEN
        await main_screen.search_issues(refresh=True)
        await pilot.pause()
        # THEN
        assert table.row_count == 4
        assert table.cursor_row == 2
        assert table.current_work_item_key == 'WI-2'
        assert app.focused is main_screen.jql_expression_input


@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_toggle_auto_refresh(
    fetch_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    app,
):
    async with app.run_test() as pilot:
        main_screen = cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        assert main_screen.search_results_container.auto_refresh_legend is None
        # WHEN
        await main_screen.run_action('toggle_auto_refresh')
        await pilot.pause()
        # THEN
        assert main_screen.search_results_container.auto_refresh_legend == 'auto-refresh: 60s'
        # WHEN
        await main_screen.run_action('toggle_auto_refresh')
        await pilot.pause()
        # THEN
        assert main_screen.search_results_container.auto_refresh_legend is None


@pytest.mark.parametrize(
    'interval, expected_legend', [(30, 'auto-refresh: 30s'), (5, 'auto-refresh: 10s')]
)
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_auto_refresh_enabled_on_startup_with_configured_interval(
    fetch_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    interval: int,
    expected_legend: str,
    app,
):
    # GIVEN
    app.config.search_results_auto_refresh_interval = interval
    async with app.run_test():
        main_screen = cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        # THEN
        assert main_screen.search_results_container.auto_refresh_legend == expected_legend


@patch('jiratui.widgets.screen.MainScreen.search_issues')
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_auto_refresh_repeats_the_last_search(
    fetch_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    search_issues_mock: AsyncMock,
    app,
):
    async with app.run_test() as pilot:
        main_screen = cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        # WHEN: no search was done yet
        main_screen._auto_refresh_search_results()
        await pilot.pause()
        # THEN
        search_issues_mock.assert_not_called()
        # WHEN
        criteria = WorkItemSearchCriteria(project_key='P1', jql_expression='status = Done')
        main_screen._last_search = {
            'next_page_token': 'token',
            'search_term': 'abc',
            'page': 2,
            'criteria': criteria,
        }
        main_screen._auto_refresh_search_results()
        await app.workers.wait_for_complete()
        # THEN
        search_issues_mock.assert_called_once_with(
            next_page_token='token', search_term='abc', page=2, criteria=criteria, refresh=True
        )


@patch('jiratui.widgets.screen.MainScreen.search_issues')
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_auto_refresh_is_skipped_when_another_screen_is_displayed(
    fetch_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    search_issues_mock: AsyncMock,
    app,
):
    async with app.run_test() as pilot:
        main_screen = cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        main_screen._last_search = {'next_page_token': None, 'search_term': None, 'page': 1}
        # WHEN
        await app.push_screen(QuitScreen())
        await pilot.pause()
        main_screen._auto_refresh_search_results()
        await pilot.pause()
        # THEN
        search_issues_mock.assert_not_called()


@patch('jiratui.widgets.screen.MainScreen._search_work_items')
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_auto_refresh_ignores_filters_modified_after_the_last_search(
    fetch_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    search_work_items_mock: AsyncMock,
    app,
):
    # GIVEN
    app.config.search_results_truncate_work_item_summary = 0
    app.config.search_results_style_work_item_status = False
    app.config.search_results_style_work_item_type = False
    search_work_items_mock.return_value = _work_items_search_result(['WI-1'])
    async with app.run_test() as pilot:
        main_screen = cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        main_screen.jql_expression_input.value = 'status = Done'
        await main_screen.search_issues()
        # the user types a JQL expression but does not search yet
        main_screen.jql_expression_input.value = 'status ='
        await pilot.pause()
        # WHEN
        main_screen._auto_refresh_search_results()
        await app.workers.wait_for_complete()
        # THEN
        assert search_work_items_mock.await_count == 2
        refresh_criteria = search_work_items_mock.await_args.kwargs['criteria']
        assert refresh_criteria.jql_expression == 'status = Done'


@patch.object(ProjectSelectionInput, 'selection', PropertyMock(return_value='CP'))
@patch.object(APIController, 'get_project_boards')
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_fetch_boards_displays_the_type_of_the_boards(
    fetch_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    get_project_boards_mock: AsyncMock,
    app,
):
    # GIVEN
    get_project_boards_mock.return_value = APIControllerResponse(
        result=[
            AgileBoard(id=27, name='CP — Backlog', board_type=AgileBoardTypes.KANBAN),
            AgileBoard(id=84, name='Team Core', board_type=AgileBoardTypes.SCRUM),
        ]
    )
    async with app.run_test():
        main_screen = cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        # WHEN
        boards = await main_screen.fetch_boards()
        # THEN
        assert boards == [('CP — Backlog (Kanban)', 27), ('Team Core (Scrum)', 84)]
        get_project_boards_mock.assert_awaited_once_with('CP')


def _work_item_with_status(key: str, status: str) -> JiraIssue:
    return JiraIssue(
        id=key.split('-')[1],
        key=key,
        summary=f'summary of {key}',
        status=IssueStatus(id='1', name=status),
        issue_type=IssueType(id='1', name='Task'),
    )


@patch.object(APIController, 'find_stale_work_items')
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_find_stale_work_items_checks_the_work_items_in_the_configured_statuses(
    fetch_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    find_stale_work_items_mock: AsyncMock,
    app,
):
    # GIVEN
    app.config.stale_work_items_statuses = ['In Development', ' blocked ']
    app.config.stale_work_items_days = 7
    find_stale_work_items_mock.return_value = APIControllerResponse(result={'WI-1'})
    response = JiraIssueSearchResponse(
        issues=[
            _work_item_with_status('WI-1', 'In Development'),
            _work_item_with_status('WI-2', 'Done'),
            _work_item_with_status('WI-3', 'Blocked'),
        ]
    )
    async with app.run_test():
        main_screen = cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        # WHEN
        stale_work_items = await main_screen._find_stale_work_items(response)
        # THEN
        assert stale_work_items == {'WI-1'}
        find_stale_work_items_mock.assert_awaited_once_with(['WI-1', 'WI-3'], days=7)


@pytest.mark.parametrize('statuses', [None, []])
@patch.object(APIController, 'find_stale_work_items')
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_find_stale_work_items_is_disabled_without_statuses(
    fetch_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    find_stale_work_items_mock: AsyncMock,
    statuses,
    app,
):
    # GIVEN
    app.config.stale_work_items_statuses = statuses
    response = JiraIssueSearchResponse(issues=[_work_item_with_status('WI-1', 'In Development')])
    async with app.run_test():
        main_screen = cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        # WHEN
        stale_work_items = await main_screen._find_stale_work_items(response)
        # THEN
        assert stale_work_items == set()
        find_stale_work_items_mock.assert_not_called()


@patch.object(APIController, 'find_stale_work_items')
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_find_stale_work_items_ignores_errors(
    fetch_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    find_stale_work_items_mock: AsyncMock,
    app,
):
    # GIVEN
    app.config.stale_work_items_statuses = ['In Development']
    app.config.stale_work_items_days = 7
    find_stale_work_items_mock.return_value = APIControllerResponse(success=False, error='error')
    response = JiraIssueSearchResponse(issues=[_work_item_with_status('WI-1', 'In Development')])
    async with app.run_test():
        main_screen = cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        # WHEN
        stale_work_items = await main_screen._find_stale_work_items(response)
        # THEN
        assert stale_work_items == set()


@patch.object(APIController, 'find_work_items_with_customers')
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_find_work_items_with_customers_checks_all_the_work_items(
    fetch_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    find_work_items_with_customers_mock: AsyncMock,
    app,
):
    # GIVEN
    app.config.customer_field = ' Customer '
    find_work_items_with_customers_mock.return_value = APIControllerResponse(result={'WI-2'})
    response = JiraIssueSearchResponse(
        issues=[
            _work_item_with_status('WI-1', 'Done'),
            _work_item_with_status('WI-2', 'In Development'),
        ]
    )
    async with app.run_test():
        main_screen = cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        # WHEN
        work_items = await main_screen._find_work_items_with_customers(response)
        # THEN
        assert work_items == {'WI-2'}
        find_work_items_with_customers_mock.assert_awaited_once_with(
            ['WI-1', 'WI-2'], customer_field='Customer'
        )


@pytest.mark.parametrize('customer_field', [None, '', '  '])
@patch.object(APIController, 'find_work_items_with_customers')
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_find_work_items_with_customers_is_disabled_without_field(
    fetch_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    find_work_items_with_customers_mock: AsyncMock,
    customer_field,
    app,
):
    # GIVEN
    app.config.customer_field = customer_field
    response = JiraIssueSearchResponse(issues=[_work_item_with_status('WI-1', 'Done')])
    async with app.run_test():
        main_screen = cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        # WHEN
        work_items = await main_screen._find_work_items_with_customers(response)
        # THEN
        assert work_items == set()
        find_work_items_with_customers_mock.assert_not_called()
