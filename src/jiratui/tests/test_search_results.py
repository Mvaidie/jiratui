from typing import cast
from unittest.mock import ANY, AsyncMock, MagicMock, Mock, PropertyMock, call, patch

from pydantic import SecretStr
import pytest
from rich.text import Text
from textual.coordinate import Coordinate
from textual.geometry import Size

from jiratui.api_controller.controller import APIController, APIControllerResponse
from jiratui.app import JiraApp
from jiratui.config import ApplicationConfiguration
from jiratui.models import (
    IssuePriority,
    IssueStatus,
    IssueType,
    JiraIssue,
    JiraIssueSearchResponse,
    WorkItemsSearchOrderBy,
)
from jiratui.widgets.screen import MainScreen, WorkItemSearchResult
from jiratui.widgets.screens.goto import GoToScreen
from jiratui.widgets.screens.work_item_quick_view import WorkItemQuickViewScreen
from jiratui.widgets.search import (
    ConfirmationScreen,
    IssuesSearchResultsTable,
    SearchResultsContainer,
)


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


@patch('jiratui.widgets.screen.MainScreen.search_issues')
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_click_filter_datatable_filtering_key_shows_input(
    search_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    search_issues_mock: AsyncMock,
    app,
):
    app.config.search_results_page_filtering_enabled = True
    async with app.run_test() as pilot:
        # GIVEN
        main_screen = cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        main_screen.search_results_table.focus()
        # WHEN
        await pilot.press('.')
        # THEN
        assert main_screen.search_results_filter_input.display is True
        assert main_screen.search_results_table.page == 1


@patch('jiratui.widgets.screen.MainScreen.search_issues')
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_click_filter_datatable_filtering_key_feature_disabled(
    search_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    search_issues_mock: AsyncMock,
    app,
):
    app.config.search_results_page_filtering_enabled = False
    async with app.run_test() as pilot:
        # GIVEN
        main_screen = cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        main_screen.search_results_table.focus()
        # WHEN
        await pilot.press('.')
        # THEN
        assert main_screen.search_results_filter_input.display is False
        assert main_screen.search_results_table.page == 1


@patch('jiratui.widgets.screen.MainScreen.search_issues')
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_search_results_table_with_user_defined_column(
    search_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    search_issues_mock: AsyncMock,
    jira_issues,
    app,
):
    # GIVEN
    app.config.search_results_columns = [
        'assignee',
        'reporter',
        'status',
        'issuetype',
        'parent',
        'summary',
    ]
    app.config.search_results_truncate_work_item_summary = 0
    app.config.search_results_style_work_item_status = False
    app.config.search_results_style_work_item_type = False
    async with app.run_test():
        main_screen = cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        # WHEN
        main_screen.search_results_table.search_results = JiraIssueSearchResponse(
            issues=jira_issues
        )
        # THEN
        # the columns follow the order defined by the user
        assert [str(c.label) for c in main_screen.search_results_table.columns.values()] == [
            '#',
            'Key',
            'Assignee',
            'Reporter',
            'Status',
            'Type',
            'Parent',
            'Summary',
        ]


@patch('jiratui.widgets.screen.MainScreen.search_issues')
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_search_results_table_without_user_defined_column(
    search_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    search_issues_mock: AsyncMock,
    jira_issues,
    app,
):
    # GIVEN
    app.config.search_results_columns = None
    app.config.search_results_truncate_work_item_summary = 0
    app.config.search_results_style_work_item_status = False
    app.config.search_results_style_work_item_type = False
    async with app.run_test():
        main_screen = cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        # WHEN
        main_screen.search_results_table.search_results = JiraIssueSearchResponse(
            issues=jira_issues
        )
        # THEN
        assert [str(c.label) for c in main_screen.search_results_table.columns.values()] == [
            '#',
            'Key',
            'Type',
            'Priority',
            'Status',
            'Summary',
            'Assignee',
        ]


@patch('jiratui.widgets.screen.MainScreen.search_issues')
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_search_results_table_with_unsupported_user_defined_column(
    search_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    search_issues_mock: AsyncMock,
    jira_issues,
    app,
):
    # GIVEN
    app.config.search_results_columns = ['a']
    app.config.search_results_truncate_work_item_summary = 0
    app.config.search_results_style_work_item_status = False
    app.config.search_results_style_work_item_type = False
    async with app.run_test():
        main_screen = cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        # WHEN
        main_screen.search_results_table.search_results = JiraIssueSearchResponse(
            issues=jira_issues
        )
        # THEN
        assert [str(c.label) for c in main_screen.search_results_table.columns.values()] == [
            '#',
            'Key',
        ]


@patch.object(IssuesSearchResultsTable, 'get_initial_results_set')
@patch('jiratui.widgets.screen.MainScreen.search_issues')
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_click_filter_datatable_filtering_key_hides_input(
    search_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    search_issues_mock: AsyncMock,
    get_initial_results_set_mock: Mock,
    app,
):
    app.config.search_results_page_filtering_enabled = True
    async with app.run_test() as pilot:
        # GIVEN
        main_screen = cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        main_screen.search_results_table.focus()
        # WHEN
        await pilot.press('.')
        # THEN
        assert main_screen.search_results_filter_input.display is True
        await pilot.press('escape')
        assert main_screen.search_results_filter_input.display is False
        get_initial_results_set_mock.assert_called_once()


@patch.object(IssuesSearchResultsTable, 'get_initial_results_set')
@patch('jiratui.widgets.screen.MainScreen.search_issues')
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_datatable_filtering_yields_results(
    search_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    search_issues_mock: AsyncMock,
    get_initial_results_set_mock: Mock,
    jira_issues: list[JiraIssue],
    app,
):
    app.config.search_results_page_filtering_enabled = True
    app.config.search_results_page_filtering_minimum_term_length = 3
    app.config.search_results_truncate_work_item_summary = 10
    app.config.search_results_style_work_item_status = False
    app.config.search_results_style_work_item_type = False
    get_initial_results_set_mock.side_effect = [
        JiraIssueSearchResponse(issues=jira_issues[0:]),
        JiraIssueSearchResponse(issues=jira_issues[0:]),
        JiraIssueSearchResponse(issues=jira_issues[0:]),
    ]
    async with app.run_test() as pilot:
        # GIVEN
        main_screen = cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        main_screen.search_results_table.focus()
        # WHEN
        await pilot.press('.')
        await pilot.press('a')
        await pilot.press('b')
        await pilot.press('c')
        # THEN
        assert main_screen.search_results_filter_input.value == 'abc'
        assert main_screen.search_results_table.page == 1
        get_initial_results_set_mock.assert_has_calls([call(), call(), call()])
        assert main_screen.search_results_filter_input.total == 1
        assert main_screen.search_results_filter_input.border_subtitle == 'Found: 1'


@patch.object(IssuesSearchResultsTable, 'get_initial_results_set')
@patch('jiratui.widgets.screen.MainScreen.search_issues')
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_datatable_filtering_yields_no_results(
    search_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    search_issues_mock: AsyncMock,
    get_initial_results_set_mock: Mock,
    jira_issues: list[JiraIssue],
    app,
):
    app.config.search_results_page_filtering_enabled = True
    app.config.search_results_page_filtering_minimum_term_length = 3
    app.config.search_results_truncate_work_item_summary = 10
    app.config.search_results_style_work_item_status = False
    app.config.search_results_style_work_item_type = False
    get_initial_results_set_mock.side_effect = [
        JiraIssueSearchResponse(issues=jira_issues[0:]),
        JiraIssueSearchResponse(issues=jira_issues[0:]),
        JiraIssueSearchResponse(issues=jira_issues[0:]),
    ]
    async with app.run_test() as pilot:
        # GIVEN
        main_screen = cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        main_screen.search_results_table.focus()
        # WHEN
        await pilot.press('.')
        await pilot.press('a')
        await pilot.press('b')
        await pilot.press('d')
        # THEN
        assert main_screen.search_results_filter_input.value == 'abd'
        assert main_screen.search_results_table.page == 1
        get_initial_results_set_mock.assert_has_calls([call(), call(), call()])
        assert main_screen.search_results_filter_input.total == 0
        assert main_screen.search_results_filter_input.border_subtitle == 'Found: 0'


@patch('jiratui.widgets.search.build_external_url_for_issue')
@patch.object(JiraApp, 'open_url')
@patch('jiratui.widgets.screen.MainScreen._search_work_items')
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_open_issue_in_browser(
    search_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    search_work_items_mock: AsyncMock,
    open_url_mock: Mock,
    build_external_url_for_issue_mock: Mock,
    jira_issues: list[JiraIssue],
    app,
):
    app.config.search_results_truncate_work_item_summary = 10
    app.config.search_results_style_work_item_status = False
    app.config.search_results_style_work_item_type = False
    app.config.search_results_per_page = 10
    build_external_url_for_issue_mock.return_value = 'https://foo.bar/key-2'
    async with app.run_test() as pilot:
        # GIVEN
        search_work_items_mock.return_value = WorkItemSearchResult(
            total=2,
            response=JiraIssueSearchResponse(
                issues=jira_issues, next_page_token=None, is_last=None
            ),
        )
        main_screen = cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        # WHEN
        await pilot.press('ctrl+r')
        await pilot.press('down')
        await pilot.press('down')
        await pilot.press('ctrl+o')
        # THEN
        assert main_screen.search_results_table.focus()
        assert main_screen.search_results_table.page == 1
        search_work_items_mock.assert_called_once()
        assert main_screen.search_results_table.search_results == JiraIssueSearchResponse(
            issues=jira_issues, next_page_token=None, is_last=None
        )
        assert main_screen.search_results_table.current_work_item_key == jira_issues[1].key
        open_url_mock.assert_called_once()
        assert main_screen.search_results_container.border_subtitle == 'Page 1 of 1 (total: 2)'


@patch('jiratui.widgets.screen.MainScreen.fetch_issue')
@patch('jiratui.widgets.screen.MainScreen._search_work_items')
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_select_issue_in_search_results_datatable(
    search_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    search_work_items_mock: AsyncMock,
    fetch_issue_mock: AsyncMock,
    jira_issues: list[JiraIssue],
    app,
):
    app.config.search_results_truncate_work_item_summary = 10
    app.config.search_results_style_work_item_status = False
    app.config.search_results_style_work_item_type = False
    app.config.search_results_per_page = 10
    async with app.run_test() as pilot:
        # GIVEN
        search_work_items_mock.return_value = WorkItemSearchResult(
            total=2,
            response=JiraIssueSearchResponse(
                issues=jira_issues, next_page_token=None, is_last=None
            ),
        )
        main_screen = cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        # WHEN
        await pilot.press('ctrl+r')
        await pilot.press('down')
        await pilot.press('enter')
        # THEN
        assert main_screen.search_results_table.page == 1
        search_work_items_mock.assert_called_once()
        assert main_screen.search_results_table.search_results == JiraIssueSearchResponse(
            issues=jira_issues, next_page_token=None, is_last=None
        )
        assert main_screen.search_results_table.current_work_item_key == jira_issues[1].key
        assert main_screen.search_results_container.border_subtitle == 'Page 1 of 1 (total: 2)'
        fetch_issue_mock.assert_called_once_with('key-2')


@patch('jiratui.widgets.screen.MainScreen._search_work_items')
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_open_delete_issue_modal_screen(
    search_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    search_work_items_mock: AsyncMock,
    jira_issues: list[JiraIssue],
    app,
):
    app.config.search_results_truncate_work_item_summary = 10
    app.config.search_results_style_work_item_status = False
    app.config.search_results_style_work_item_type = False
    app.config.search_results_per_page = 10
    async with app.run_test() as pilot:
        # GIVEN
        search_work_items_mock.return_value = WorkItemSearchResult(
            total=2,
            response=JiraIssueSearchResponse(
                issues=jira_issues, next_page_token=None, is_last=None
            ),
        )
        main_screen = cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        # WHEN
        await pilot.press('ctrl+r')
        await pilot.press('down')
        await pilot.press('down')
        await pilot.press('d')
        # THEN
        assert main_screen.search_results_table.focus()
        assert main_screen.search_results_table.page == 1
        search_work_items_mock.assert_called_once()
        assert main_screen.search_results_table.search_results == JiraIssueSearchResponse(
            issues=jira_issues, next_page_token=None, is_last=None
        )
        assert main_screen.search_results_table.current_work_item_key == jira_issues[1].key
        assert isinstance(app.screen, ConfirmationScreen)


@patch.object(SearchResultsContainer, '_update_border_subtitle')
@patch('jiratui.widgets.screen.MainScreen._search_work_items')
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_delete_issue_modal_screen_click_cancel(
    search_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    search_work_items_mock: AsyncMock,
    update_border_subtitle_mock: Mock,
    jira_issues: list[JiraIssue],
    app,
):
    app.config.search_results_truncate_work_item_summary = 10
    app.config.search_results_style_work_item_status = False
    app.config.search_results_style_work_item_type = False
    app.config.search_results_per_page = 10
    async with app.run_test() as pilot:
        # GIVEN
        search_work_items_mock.return_value = WorkItemSearchResult(
            total=2,
            response=JiraIssueSearchResponse(
                issues=jira_issues, next_page_token=None, is_last=None
            ),
        )
        main_screen = cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        # WHEN
        await pilot.press('ctrl+r')
        await pilot.press('down')
        await pilot.press('down')
        await pilot.press('d')
        await pilot.press('tab')
        await pilot.press('enter')
        # THEN
        assert main_screen.search_results_table.focus()
        assert main_screen.search_results_table.page == 1
        search_work_items_mock.assert_called_once()
        assert main_screen.search_results_table.search_results == JiraIssueSearchResponse(
            issues=jira_issues, next_page_token=None, is_last=None
        )
        assert main_screen.search_results_table.current_work_item_key == jira_issues[1].key
        assert isinstance(app.screen, MainScreen)
        update_border_subtitle_mock.assert_called_once()


@patch.object(APIController, 'delete_work_item')
@patch.object(SearchResultsContainer, '_update_border_subtitle')
@patch('jiratui.widgets.screen.MainScreen._search_work_items')
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_delete_issue_modal_screen_click_delete(
    fetch_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    search_work_items_mock: AsyncMock,
    update_border_subtitle_mock: Mock,
    delete_work_item_mock: AsyncMock,
    jira_issues: list[JiraIssue],
    app,
):
    app.config.search_results_truncate_work_item_summary = 10
    app.config.search_results_style_work_item_status = False
    app.config.search_results_style_work_item_type = False
    app.config.search_results_per_page = 10
    delete_work_item_mock.return_value = APIControllerResponse()
    async with app.run_test() as pilot:
        # GIVEN
        search_work_items_mock.return_value = WorkItemSearchResult(
            total=2,
            response=JiraIssueSearchResponse(
                issues=jira_issues, next_page_token=None, is_last=None
            ),
        )
        main_screen = cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        # WHEN
        await pilot.press('ctrl+r')
        await pilot.press('down')
        await pilot.press('down')
        await pilot.press('d')
        await pilot.press('enter')
        # THEN
        assert main_screen.search_results_table.focus()
        assert main_screen.search_results_table.page == 1
        search_work_items_mock.assert_called_once()
        assert main_screen.search_results_table.search_results == JiraIssueSearchResponse(
            issues=jira_issues, next_page_token=None, is_last=None
        )
        delete_work_item_mock.assert_called_once_with(jira_issues[1].key)
        assert main_screen.search_results_table.current_work_item_key != jira_issues[1].key
        assert isinstance(app.screen, MainScreen)
        update_border_subtitle_mock.assert_has_calls([call(), call()])


@patch.object(APIController, 'delete_work_item')
@patch.object(SearchResultsContainer, '_update_border_subtitle')
@patch('jiratui.widgets.screen.MainScreen._search_work_items')
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_delete_issue_modal_screen_click_delete_currently_selected_item(
    fetch_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    search_work_items_mock: AsyncMock,
    update_border_subtitle_mock: Mock,
    delete_work_item_mock: AsyncMock,
    jira_issues: list[JiraIssue],
    app,
):
    """Tests that deleting the currently select item clears the currently selected item key and the details' issue."""
    app.config.search_results_truncate_work_item_summary = 10
    app.config.search_results_style_work_item_status = False
    app.config.search_results_style_work_item_type = False
    app.config.search_results_per_page = 10
    delete_work_item_mock.return_value = APIControllerResponse()
    async with app.run_test() as pilot:
        # GIVEN
        search_work_items_mock.return_value = WorkItemSearchResult(
            total=2,
            response=JiraIssueSearchResponse(
                issues=jira_issues, next_page_token=None, is_last=None
            ),
        )
        main_screen = cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        main_screen.current_loaded_work_item_key = jira_issues[1].key
        # WHEN
        await pilot.press('ctrl+r')
        await pilot.press('down')
        await pilot.press('down')
        await pilot.press('d')
        await pilot.press('enter')
        # THEN
        assert main_screen.search_results_table.focus()
        assert main_screen.search_results_table.page == 1
        search_work_items_mock.assert_called_once()
        assert main_screen.search_results_table.search_results == JiraIssueSearchResponse(
            issues=jira_issues, next_page_token=None, is_last=None
        )
        assert main_screen.search_results_table.current_work_item_key != jira_issues[1].key
        assert isinstance(app.screen, MainScreen)
        delete_work_item_mock.assert_called_once_with(jira_issues[1].key)
        update_border_subtitle_mock.assert_has_calls([call(), call()])
        assert main_screen.current_loaded_work_item_key is None
        assert main_screen.issue_details_widget.issue is None


@patch('jiratui.widgets.screen.MainScreen._search_work_items')
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_open_quick_view_screen_with_item_selected(
    search_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    search_work_items_mock: AsyncMock,
    jira_issues: list[JiraIssue],
    app,
):
    app.config.search_results_truncate_work_item_summary = 10
    app.config.search_results_style_work_item_status = False
    app.config.search_results_style_work_item_type = False
    app.config.search_results_per_page = 10
    app.config.enable_goto = True
    async with app.run_test() as pilot:
        # GIVEN
        search_work_items_mock.return_value = WorkItemSearchResult(
            total=2,
            response=JiraIssueSearchResponse(
                issues=jira_issues, next_page_token=None, is_last=None
            ),
        )
        main_screen = cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        # WHEN
        await pilot.press('ctrl+r')
        await pilot.press('down')
        await pilot.press('down')
        await pilot.press('v')
        # THEN
        assert main_screen.search_results_table.has_focus
        assert isinstance(app.screen, WorkItemQuickViewScreen)


@patch('jiratui.widgets.search.build_external_url_for_issue')
@patch('jiratui.widgets.screen.MainScreen._search_work_items')
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_open_in_browser_selected_item(
    search_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    search_work_items_mock: AsyncMock,
    build_external_url_for_issue_mock: Mock,
    jira_issues: list[JiraIssue],
    app,
):
    app.config.search_results_truncate_work_item_summary = 10
    app.config.search_results_style_work_item_status = False
    app.config.search_results_style_work_item_type = False
    app.config.search_results_per_page = 10
    app.config.enable_goto = True
    build_external_url_for_issue_mock.return_value = 'foo.bar'
    async with app.run_test() as pilot:
        # GIVEN
        app.open_url = AsyncMock()
        search_work_items_mock.return_value = WorkItemSearchResult(
            total=2,
            response=JiraIssueSearchResponse(
                issues=jira_issues, next_page_token=None, is_last=None
            ),
        )
        main_screen = cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        # WHEN
        await pilot.press('ctrl+r')
        await pilot.press('down')
        await pilot.press('down')
        await pilot.press('ctrl+o')
        # THEN
        assert main_screen.search_results_table.has_focus
        app.open_url.assert_called_once_with('foo.bar')


@patch('jiratui.widgets.screen.MainScreen._search_work_items')
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_open_goto_screen_with_goto_enabled(
    search_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    search_work_items_mock: AsyncMock,
    jira_issues: list[JiraIssue],
    app,
):
    app.config.search_results_truncate_work_item_summary = 10
    app.config.search_results_style_work_item_status = False
    app.config.search_results_style_work_item_type = False
    app.config.search_results_per_page = 10
    app.config.enable_goto = True
    async with app.run_test() as pilot:
        # GIVEN
        search_work_items_mock.return_value = WorkItemSearchResult(
            total=2,
            response=JiraIssueSearchResponse(
                issues=jira_issues, next_page_token=None, is_last=None
            ),
        )
        main_screen = cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        # WHEN
        await pilot.press('ctrl+r')
        await pilot.press('down')
        await pilot.press('down')
        await pilot.press('f6')
        # THEN
        assert main_screen.search_results_table.has_focus
        assert isinstance(app.screen, GoToScreen)


@patch('jiratui.widgets.screen.MainScreen._search_work_items')
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_open_goto_screen_with_goto_disabled(
    search_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    search_work_items_mock: AsyncMock,
    jira_issues: list[JiraIssue],
    app,
):
    app.config.search_results_truncate_work_item_summary = 10
    app.config.search_results_style_work_item_status = False
    app.config.search_results_style_work_item_type = False
    app.config.search_results_per_page = 10
    app.config.enable_goto = False
    async with app.run_test() as pilot:
        # GIVEN
        search_work_items_mock.return_value = WorkItemSearchResult(
            total=2,
            response=JiraIssueSearchResponse(
                issues=jira_issues, next_page_token=None, is_last=None
            ),
        )
        main_screen = cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        # WHEN
        await pilot.press('ctrl+r')
        await pilot.press('down')
        await pilot.press('down')
        await pilot.press('f6')
        # THEN
        assert main_screen.search_results_table.has_focus
        assert isinstance(app.screen, MainScreen)


@patch('jiratui.widgets.screen.MainScreen.fetch_issue')
@patch('jiratui.widgets.screen.MainScreen._search_work_items')
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_click_next_page_search_results(
    fetch_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    search_work_items_mock: AsyncMock,
    fetch_issue_mock: AsyncMock,
    jira_issues: list[JiraIssue],
    app,
):
    app.config.search_results_truncate_work_item_summary = 10
    app.config.search_results_style_work_item_status = False
    app.config.search_results_style_work_item_type = False
    app.config.search_results_per_page = 1
    async with app.run_test() as pilot:
        # GIVEN
        search_work_items_mock.side_effect = [
            WorkItemSearchResult(
                total=2,
                response=JiraIssueSearchResponse(
                    issues=[jira_issues[0]], next_page_token='token_a'
                ),
            ),
            WorkItemSearchResult(
                total=2,
                response=JiraIssueSearchResponse(issues=[jira_issues[1]], is_last=True),
            ),
        ]
        main_screen = cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        # WHEN
        await pilot.press('ctrl+r')
        await pilot.press('alt+right')
        # THEN
        search_work_items_mock.assert_has_calls(
            [
                call(next_page_token=None, search_term=None, page=1, criteria=ANY),
                call(next_page_token='token_a', search_term=None, page=2, criteria=ANY),
            ]
        )
        assert main_screen.search_results_table.page == 2
        assert main_screen.search_results_table.current_work_item_key == jira_issues[1].key
        assert main_screen.search_results_container.border_subtitle == 'Page 2 of 2 (total: 2)'


@patch('jiratui.widgets.screen.MainScreen.fetch_issue')
@patch('jiratui.widgets.screen.MainScreen._search_work_items')
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_click_next_page_search_results_with_missing_token(
    fetch_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    search_work_items_mock: AsyncMock,
    fetch_issue_mock: AsyncMock,
    jira_issues: list[JiraIssue],
    app,
):
    app.config.search_results_truncate_work_item_summary = 10
    app.config.search_results_style_work_item_status = False
    app.config.search_results_style_work_item_type = False
    app.config.search_results_per_page = 2
    async with app.run_test() as pilot:
        # GIVEN
        search_work_items_mock.return_value = WorkItemSearchResult(
            total=2,
            response=JiraIssueSearchResponse(
                issues=jira_issues, next_page_token=None, is_last=True
            ),
        )
        main_screen = cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        # WHEN
        await pilot.press('ctrl+r')
        await pilot.press('alt+right')
        # THEN
        assert main_screen.search_results_table.current_work_item_key == jira_issues[0].key
        assert main_screen.search_results_container.border_subtitle == 'Page 1 of 1 (total: 2)'
        search_work_items_mock.assert_has_calls(
            [
                call(next_page_token=None, search_term=None, page=1, criteria=ANY),
            ]
        )
        assert main_screen.search_results_table.page == 1


@patch('jiratui.widgets.screen.MainScreen.fetch_issue')
@patch('jiratui.widgets.screen.MainScreen._search_work_items')
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_click_previous_page_search_results(
    search_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    search_work_items_mock: AsyncMock,
    fetch_issue_mock: AsyncMock,
    jira_issues: list[JiraIssue],
    app,
):
    app.config.search_results_truncate_work_item_summary = 10
    app.config.search_results_style_work_item_status = False
    app.config.search_results_style_work_item_type = False
    app.config.search_results_per_page = 1
    async with app.run_test() as pilot:
        # GIVEN
        search_work_items_mock.side_effect = [
            WorkItemSearchResult(
                total=2,
                response=JiraIssueSearchResponse(
                    issues=[jira_issues[0]], next_page_token='token_a', is_last=False
                ),
            ),
            WorkItemSearchResult(
                total=2, response=JiraIssueSearchResponse(issues=[jira_issues[1]], is_last=True)
            ),
            WorkItemSearchResult(
                total=2,
                response=JiraIssueSearchResponse(
                    issues=[jira_issues[0]], next_page_token='token_a', is_last=False
                ),
            ),
        ]
        main_screen = cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        # WHEN
        await pilot.press('ctrl+r')
        await pilot.press('alt+right')
        await pilot.press('alt+left')
        # THEN
        search_work_items_mock.assert_has_calls(
            [
                call(next_page_token=None, search_term=None, page=1, criteria=ANY),
                call(next_page_token='token_a', search_term=None, page=2, criteria=ANY),
                call(next_page_token=None, search_term=None, page=1, criteria=ANY),
            ]
        )
        assert main_screen.search_results_table.page == 1
        assert main_screen.search_results_table.current_work_item_key == jira_issues[0].key
        assert main_screen.search_results_container.border_subtitle == 'Page 1 of 2 (total: 2)'


@patch('jiratui.widgets.screen.MainScreen.fetch_issue')
@patch('jiratui.widgets.screen.MainScreen._search_work_items')
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_click_previous_page_on_first_page(
    search_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    search_work_items_mock: AsyncMock,
    fetch_issue_mock: AsyncMock,
    jira_issues: list[JiraIssue],
    app,
):
    app.config.search_results_truncate_work_item_summary = 10
    app.config.search_results_style_work_item_status = False
    app.config.search_results_style_work_item_type = False
    app.config.search_results_per_page = 2
    async with app.run_test() as pilot:
        # GIVEN
        search_work_items_mock.return_value = WorkItemSearchResult(
            total=2,
            response=JiraIssueSearchResponse(
                issues=jira_issues, next_page_token=None, is_last=True
            ),
        )
        main_screen = cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        # WHEN
        await pilot.press('ctrl+r')
        await pilot.press('alt+left')
        # THEN
        search_work_items_mock.assert_has_calls(
            [
                call(next_page_token=None, search_term=None, page=1, criteria=ANY),
            ]
        )
        assert main_screen.search_results_table.page == 1
        assert main_screen.search_results_table.current_work_item_key == jira_issues[0].key
        assert main_screen.search_results_container.border_subtitle == 'Page 1 of 1 (total: 2)'


@pytest.mark.parametrize('container_width, expected_width', [(80, 59), (30, 20)])
@patch('jiratui.widgets.screen.MainScreen.search_issues')
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_search_results_table_summary_uses_the_width_left_by_other_columns(
    search_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    search_issues_mock: AsyncMock,
    container_width: int,
    expected_width: int,
    app,
):
    # GIVEN
    rows = [{'Key': 'key-1', 'Status': Text('Done'), 'Summary': Text('a summary')}]
    async with app.run_test():
        main_screen = cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        with patch.object(
            SearchResultsContainer,
            'container_size',
            new_callable=PropertyMock,
            return_value=Size(container_width, 20),
        ):
            # WHEN
            width = main_screen.search_results_table._get_maximum_summary_column_width(
                rows, 'Summary'
            )
        # THEN
        # columns: '#' (1 + 2), 'Key' (5 + 2), 'Status' (6 + 2); summary padding (2) and the scrollbar (1)
        assert width == expected_width


@patch('jiratui.widgets.search.get_style_for_work_item_priority')
@patch('jiratui.widgets.screen.MainScreen.search_issues')
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_search_results_table_priority_column_uses_the_color_of_the_priority(
    search_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    search_issues_mock: AsyncMock,
    get_style_for_work_item_priority_mock: Mock,
    app,
):
    # GIVEN
    get_style_for_work_item_priority_mock.return_value = '#F25555'
    app.config.search_results_truncate_work_item_summary = 0
    app.config.search_results_style_work_item_status = False
    app.config.search_results_style_work_item_type = False
    issue = JiraIssue(
        id='1',
        key='WI-1',
        summary='summary',
        status=IssueStatus(id='1', name='To Do'),
        issue_type=IssueType(id='1', name='Bug'),
        priority=IssuePriority(id='1', name='P1: Blocker / No workaround'),
    )
    async with app.run_test():
        main_screen = cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        table = main_screen.search_results_table
        # WHEN
        table.search_results = JiraIssueSearchResponse(issues=[issue])
        # THEN
        cell = table.get_cell_at(Coordinate(0, 3))
        assert str(cell) == 'P1'
        assert str(cell.style) == '#F25555'
        get_style_for_work_item_priority_mock.assert_called_once_with('P1: Blocker / No workaround')


@patch('jiratui.widgets.screen.MainScreen.search_issues')
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_search_results_table_displays_a_red_dot_before_the_summary_of_stale_work_items(
    search_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    search_issues_mock: AsyncMock,
    app,
):
    # GIVEN
    app.config.search_results_truncate_work_item_summary = 12
    app.config.search_results_style_work_item_status = False
    app.config.search_results_style_work_item_type = False
    issues = [
        JiraIssue(
            id=str(index),
            key=f'WI-{index}',
            summary='a long summary',
            status=IssueStatus(id='1', name='In Development'),
            issue_type=IssueType(id='1', name='Task'),
        )
        for index in (1, 2)
    ]
    async with app.run_test():
        main_screen = cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        table = main_screen.search_results_table
        table.stale_work_item_keys = {'WI-1'}
        # WHEN
        table.search_results = JiraIssueSearchResponse(issues=issues)
        # THEN
        summary_column = [str(c.label) for c in table.columns.values()].index('Summary')
        stale_summary = table.get_cell_at(Coordinate(0, summary_column))
        other_summary = table.get_cell_at(Coordinate(1, summary_column))
        # the red dot is part of the maximum width of the summary
        assert str(stale_summary) == '● a long ...'
        assert str(stale_summary.spans[0].style) == '#F25555'
        assert str(other_summary) == 'a long su...'


@patch('jiratui.widgets.screen.MainScreen.search_issues')
@patch('jiratui.widgets.screen.MainScreen.fetch_statuses')
@patch('jiratui.widgets.screen.MainScreen.fetch_issue_types')
@patch('jiratui.widgets.screen.MainScreen.fetch_projects')
@pytest.mark.asyncio
async def test_search_results_table_displays_a_blue_dot_after_the_type_of_work_items_with_customers(
    search_projects_mock: AsyncMock,
    fetch_issue_types_mock: AsyncMock,
    fetch_statuses_mock: AsyncMock,
    search_issues_mock: AsyncMock,
    app,
):
    # GIVEN
    app.config.search_results_truncate_work_item_summary = 0
    app.config.search_results_style_work_item_status = False
    app.config.search_results_style_work_item_type = False
    issues = [
        JiraIssue(
            id=str(index),
            key=f'WI-{index}',
            summary='summary',
            status=IssueStatus(id='1', name='To Do'),
            issue_type=IssueType(id='1', name='Task'),
        )
        for index in (1, 2)
    ]
    async with app.run_test():
        main_screen = cast('MainScreen', app.screen)  # type:ignore[name-defined] # noqa: F821
        table = main_screen.search_results_table
        table.customer_work_item_keys = {'WI-1'}
        # WHEN
        table.search_results = JiraIssueSearchResponse(issues=issues)
        # THEN
        type_column = [str(c.label) for c in table.columns.values()].index('Type')
        type_with_customer = table.get_cell_at(Coordinate(0, type_column))
        assert str(type_with_customer) == 'Task ●'
        assert str(type_with_customer.spans[-1].style) == '#4688EC'
        assert str(table.get_cell_at(Coordinate(1, type_column))) == 'Task'
        # the key is not modified
        assert str(table.get_cell_at(Coordinate(0, 1))) == 'WI-1'
