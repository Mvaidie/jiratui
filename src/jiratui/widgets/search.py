"""This module contains widgets for implementing work item search functionality."""

from typing import cast

from rich.cells import cell_len
from rich.text import Text
from textual import on
from textual.binding import Binding
from textual.containers import Container
from textual.message import Message
from textual.reactive import Reactive, reactive
from textual.widgets import DataTable, Input
from textual.widgets._data_table import RowDoesNotExist

from jiratui.actions.constants import SupportedActions
from jiratui.actions.keys import get_application_key_bindings
from jiratui.api_controller.controller import APIControllerResponse
from jiratui.models import JiraIssue, JiraIssueSearchResponse
from jiratui.utils.search import (
    MAP_WORK_ITEM_SEARCH_FIELD_TO_SEARCH_RESULTS_COLUMNS,
    SearchFieldId,
    get_work_item_search_fields,
    get_work_item_search_results_table_columns,
)
from jiratui.utils.styling import (
    get_style_for_work_item_priority,
    get_style_for_work_item_status,
    get_style_for_work_item_type,
)
from jiratui.utils.ui_actions import Actionable, UIAction
from jiratui.utils.urls import build_external_url_for_issue
from jiratui.widgets.messages import SearchWorkItem
from jiratui.widgets.screens.confirmation import ConfirmationScreen
from jiratui.widgets.screens.goto import GoToScreen
from jiratui.widgets.screens.work_item_quick_view import WorkItemQuickViewScreen


class DataTableSearchInput(Input):
    """An input field that allows users to perform searches in the currently active search results page.

    The feature to search within search results pages is controlled by these settings:

    - `search_results_page_filtering_enabled`
    - `search_results_page_filtering_minimum_term_length`
    """

    BINDINGS = [Binding('escape', 'hide', 'Hide search input', show=False)]

    total: Reactive[int | None] = reactive(None)
    """Keeps track of the total number of records after filtering them based on the input value."""

    def __init__(
        self,
        placeholder: str | None = None,
        border_title: str | None = None,
        hide: bool | None = True,
    ):
        super().__init__(id='searchable-datatable-input-field')
        self.placeholder = placeholder or 'Type to filter items in the current page...'
        self.border_title = border_title or 'Filter'
        self.styles.display = 'none' if hide else 'block'

    def action_hide(self) -> None:
        # hide the input widget
        self.styles.display = 'none'
        screen = cast('MainScreen', self.screen)  # type:ignore[name-defined] # noqa: F821
        # reset the results to the initial result set
        screen.search_results_table.search_results = (
            screen.search_results_table.get_initial_results_set()
        )
        # give focus back to the data table
        screen.search_results_table.focus()

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        """Check if an action may run."""
        if action == 'hide' and not self.app.config.search_results_page_filtering_enabled:  # type:ignore[attr-defined]
            return False
        return True

    def watch_total(self, value: int | None = None) -> None:
        if value is not None:
            self.border_subtitle = f'Found: {value}'
        else:
            self.border_subtitle = None

    @on(Input.Changed)
    async def on_input_changed(self, event: Input.Changed) -> None:
        screen = cast('MainScreen', self.screen)  # type:ignore[name-defined] # noqa: F821
        cleaned = event.value.strip() if event.value else None
        if not cleaned or (
            len(cleaned) < self.app.config.search_results_page_filtering_minimum_term_length  # type:ignore[attr-defined]
        ):
            screen.search_results_table.search_results = (
                screen.search_results_table.get_initial_results_set()
            )
            self.total = 0
        else:
            cleaned = cleaned.lower()
            if (initial_results_set := screen.search_results_table.get_initial_results_set()) and (
                issues := initial_results_set.issues
            ):
                filtered: list[JiraIssue] = [
                    record
                    for record in issues
                    if (
                        cleaned in record.summary.lower()
                        or cleaned in record.key.lower()
                        or cleaned in record.parent_key
                    )
                ]
                screen.search_results_table.search_results = JiraIssueSearchResponse(
                    issues=filtered
                )
                self.total = len(filtered)


class IssuesSearchResultsTable(Actionable, DataTable, inherit_bindings=False):  # type:ignore[call-arg]
    """The widget that displays the results of a search.

    This widget provides a reactive attribute, `search_results`, that contains the issues that the table will
    display.

    The widget can post a message of type [IssuesSearchResultsTable.WorkItemDeleted](#jiratui.widgets.search.IssuesSearchResultsTable.WorkItemDeleted)
    when the user deletes an item from the table.

    ```{important}
    Deleting an item will delete the item from Jira. After a successful deletion the datatable will remove the row
    related to the item that was deleted. In addition, the widget will send the message
    [IssuesSearchResultsTable.WorkItemDeleted](#jiratui.widgets.search.IssuesSearchResultsTable.WorkItemDeleted) to
    notify other widgets so they can update the relevant widgets.
    ```

    This widget is actionable and so it can handle different actions.

    **See Also**:
    - [Use Case: Open Go-To Screen](#use-case-search-results-goto-screen)
    - Use Case: Open Quick-View Screen
    - Use Case: Filter Search Results
    - Use Case: Fetch Next Page
    - Use Case: Fetch Previous Page
    - [Use Case: Search and Fetch using Go-To Screen](#use-case-search-and-fetch-item-goto-screen)
    """

    search_results: Reactive[JiraIssueSearchResponse | None] = reactive(None, always_update=True)

    ACTIONS: list[UIAction] = []
    # set up the key-bindings based on the configuration selected by the user
    key_bindings: dict[str, dict] = get_application_key_bindings()
    for supported_action_id in [
        SupportedActions.VIEW_WORK_ITEM,
        SupportedActions.OPEN_IN_BROWSER,
        SupportedActions.DELETE_WORK_ITEM,
        SupportedActions.OPEN_GO_TO_SCREEN,
        SupportedActions.SELECT_CURSOR,
        SupportedActions.CURSOR_UP,
        SupportedActions.CURSOR_DOWN,
        SupportedActions.PAGE_UP,
        SupportedActions.PAGE_DOWN,
        SupportedActions.SCROLL_TOP,
        SupportedActions.SCROLL_BOTTOM,
        SupportedActions.FILTER,
        SupportedActions.PREVIOUS_ISSUES_PAGE,
        SupportedActions.NEXT_ISSUES_PAGE,
        SupportedActions.CURSOR_LEFT,
        SupportedActions.CURSOR_RIGHT,
    ]:
        data = key_bindings.get(supported_action_id.value, {})
        ACTIONS.append(
            UIAction(
                action=supported_action_id.value,
                keys=data.get('keys', []),
                show=data.get('show', False),
                description=data.get('description'),
                tooltip=data.get('tooltip', ''),
            )
        )

    BINDINGS = [  # type:ignore[assignment]
        Binding(
            key=','.join(action.keys),
            action=action.action,
            show=action.show,
            description=action.description or '',
            tooltip=action.tooltip,
        )
        for action in ACTIONS
        if isinstance(action.action, str)
    ] + [Binding('escape', 'hide', 'Hide search input', show=False)]

    SMALLEST_MAXIMUM_WIDTH_FOR_SUMMARY_COLUMN = 20
    """The minimum width of the summary column. Otherwise, the summary column uses the width left by the other columns."""

    class WorkItemDeleted(Message):
        def __init__(self, work_item_key: str) -> None:
            self._work_item_key = work_item_key
            super().__init__()

        @property
        def work_item_key(self) -> str:
            return self._work_item_key

    def __init__(self):
        super().__init__(id='search_results', cursor_type='row')
        # stores the next page's token by page number
        # e.g.: {2: 'token-a', 3: 'token-b'}
        # to fetch the results page
        #   2: we need to use the token 'token-a'
        #   3: we need to use the token 'token-b'
        self.token_by_page: dict[int, str] = {}
        self.page = 1
        self.current_work_item_key: str | None = None
        self.current_work_item_id: str | None = None
        self._initial_results_set: JiraIssueSearchResponse | None = None

    def set_initial_results_set(self, data: JiraIssueSearchResponse | None = None):
        self._initial_results_set = data

    def get_initial_results_set(self) -> JiraIssueSearchResponse | None:
        return self._initial_results_set

    def watch_search_results(self, response: JiraIssueSearchResponse | None = None) -> None:
        """Watches the content of a reactive attribute that contains the details of the work item selected by the user.

        Args:
            response: an instance of `JiraIssueSearchResponse` with the work item selected by the user.

        Returns:
            None
        """

        if response is None:
            return

        # clear the existing data
        self.clear(columns=True)

        # update next search tokens
        if response.next_page_token:
            # there is a token to fetch the next page
            self.token_by_page[self.page + 1] = response.next_page_token

        # set the columns in the same order as the fields
        columns: list[str] = get_work_item_search_results_table_columns(
            self.app.config.search_results_columns  # type:ignore[attr-defined]
        )
        self.add_column(label='#', key='index')
        for column in columns:
            self.add_column(label=column, key=column)

        work_item_search_fields: list[str] = get_work_item_search_fields(
            self.app.config.search_results_columns  # type:ignore[attr-defined]
        )

        # build the rows; the summary is truncated afterward to fit in the width left by the other columns
        rows: list[dict] = [
            self._build_row_for_work_item(issue, work_item_search_fields)
            for issue in response.issues
        ]
        summary_column = MAP_WORK_ITEM_SEARCH_FIELD_TO_SEARCH_RESULTS_COLUMNS[
            SearchFieldId.SUMMARY.value
        ]
        if rows and summary_column in rows[0]:
            maximum_summary_column_width = (
                self.app.config.search_results_truncate_work_item_summary  # type:ignore[attr-defined]
                or self._get_maximum_summary_column_width(rows, summary_column)
            )
            for issue, cells in zip(response.issues, rows, strict=True):
                cells[summary_column] = Text(issue.cleaned_summary(maximum_summary_column_width))
        for index, (issue, cells) in enumerate(zip(response.issues, rows, strict=True)):
            self.add_row(index + 1, *cells.values(), key=f'{issue.id}#{issue.key}')

    def move_cursor_to_work_item(self, row_key: str | None) -> None:
        """Moves the cursor to the row of a work item, if the work item is in the search results.

        Args:
            row_key: the key of the row of the work item, i.e. `<id>#<key>`.

        Returns:
            None
        """

        if row_key and row_key in self.rows:
            self.move_cursor(row=self.get_row_index(row_key))

    def _get_maximum_summary_column_width(self, rows: list[dict], summary_column: str) -> int:
        """Calculates the width left by the other columns of the search results for the summary column.

        Args:
            rows: the cells of every row of the search results by column name.
            summary_column: the name of the summary column.

        Returns:
            The maximum width of the summary column.
        """

        def cell_width(cell) -> int:
            return cell.cell_len if isinstance(cell, Text) else cell_len(str(cell))

        padding = 2 * self.cell_padding
        # the width of a column is the width of its widest cell, including its label, plus the padding of the cells
        used_width = max(len('#'), len(str(len(rows)))) + padding
        for column in rows[0] if rows else {}:
            if column != summary_column:
                used_width += max(cell_width(column), *(cell_width(row[column]) for row in rows))
                used_width += padding
        # the padding of the summary column and the vertical scrollbar take space too
        available_width = (
            self.parent.container_size.width  # type:ignore[attr-defined]
            - used_width
            - padding
            - 1
        )
        return max(self.SMALLEST_MAXIMUM_WIDTH_FOR_SUMMARY_COLUMN, available_width)

    def _build_row_for_work_item(self, item: JiraIssue, work_item_search_fields: list[str]) -> dict:
        cells: dict = {}
        for field_name in work_item_search_fields:
            column_name = MAP_WORK_ITEM_SEARCH_FIELD_TO_SEARCH_RESULTS_COLUMNS.get(field_name)
            if field_name == SearchFieldId.KEY.value:
                cells[column_name] = item.key
            elif field_name == SearchFieldId.PRIORITY.value:
                cells[column_name] = Text(
                    item.show_priority(10),
                    style=get_style_for_work_item_priority(item.priority_name),
                )
            elif field_name == SearchFieldId.PARENT.value:
                cells[column_name] = item.parent_key
            elif field_name == SearchFieldId.STATUS.value:
                style_status = ''
                if self.app.config.search_results_style_work_item_status:  # type:ignore[attr-defined]
                    style_status = get_style_for_work_item_status(item.status.name.lower())
                cells[column_name] = Text(item.status.name, style=style_status)
            elif field_name == SearchFieldId.ISSUE_TYPE.value:
                style_work_type = ''
                if self.app.config.search_results_style_work_item_type:  # type:ignore[attr-defined]
                    style_work_type = get_style_for_work_item_type(item.issue_type.name.lower())
                cells[column_name] = Text(item.show_work_item_type(8), style=style_work_type)
            elif field_name == SearchFieldId.SUMMARY.value:
                cells[column_name] = Text(item.cleaned_summary())
            elif field_name == SearchFieldId.ASSIGNEE.value:
                cells[column_name] = item.show_assignee(10)
            elif field_name == SearchFieldId.REPORTER.value:
                cells[column_name] = item.show_reporter(10)
        # the cells follow the order of the fields, i.e. the order of the columns
        return cells

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Fetches the details of the currently-selected item."""
        if event.row_key:
            screen = cast('MainScreen', self.screen)  # type:ignore[name-defined] # noqa: F821
            self.current_work_item_id, self.current_work_item_key = event.row_key.value.split('#')
            # use exclusive=True to make sure that if the user selects another work item before the worker finishes
            # retrieving the data of the previously selected the correct data is fetched
            # the exclusive flag tells Textual to cancel all previous workers before starting the new one.
            self.run_worker(screen.fetch_issue(self.current_work_item_key), exclusive=True)

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        """Stores the key of the currently-selected item."""
        if event.row_key:
            self.current_work_item_id, self.current_work_item_key = event.row_key.value.split('#')

    async def action_view_work_item(self) -> None:
        """Opens the quick-view screen for the currently selected work item."""
        if self.current_work_item_key:
            await self.app.push_screen(
                WorkItemQuickViewScreen(self.current_work_item_key),
                callback=self._load_work_item_after_viewing,
            )

    def action_open_in_browser(self) -> None:
        """Opens the currently-selected item in the default browser."""
        if self.current_work_item_key:
            self.notify('Opening Work Item in the browser...')
            self.app.open_url(build_external_url_for_issue(self.current_work_item_key))

    def action_delete_work_item(self) -> None:
        """Deletes the currently-selected item."""

        if self.current_work_item_key:
            self.run_worker(
                self._open_work_item_deletion_screen(self.current_work_item_key), exclusive=True
            )

    async def _open_work_item_deletion_screen(self, work_item_key: str) -> None:
        """Opens a modal screen to let the user decided whether to delete the work item or not.

        Args:
            work_item_key: key of the work item to delete.

        Returns:
            None
        """

        await self.app.push_screen(
            ConfirmationScreen(
                message='Are you sure you want to delete this item?',
                title=f'Delete Work Item {work_item_key}',
                warning_message=f'Warning: if the work item {work_item_key} has subtasks, deleting it will also delete all its subtasks!',
            ),
            callback=self._delete_work_item,
        )

    async def _delete_work_item(self, delete_item: bool = False) -> None:
        """Deletes the currently-selected item.

        Args:
            delete_item: if `True` the user confirmed deleting the item in the modal screen; otherwise the user
            canceled the operation.

        Returns:
            None.
        """

        if delete_item and self.current_work_item_key:
            response: APIControllerResponse = await self.app.api.delete_work_item(  # type:ignore[attr-defined]
                self.current_work_item_key
            )
            if response.success:
                try:
                    self.remove_row(f'{self.current_work_item_id}#{self.current_work_item_key}')
                except RowDoesNotExist:
                    pass
                else:
                    # post the message to the parent container can update the pagination legend
                    self.post_message(self.WorkItemDeleted(self.current_work_item_key))
                    # force the table to highlight another item to avoid RowDoesNotExist exceptions with the next delete
                    # attempt
                    self.action_cursor_up()
                    self.action_cursor_down()
                self.notify(f'Deleted {self.current_work_item_key}', title='Delete Work Item')
            else:
                self.notify(
                    f'Failed to delete the item {self.current_work_item_key}.',
                    title='Delete Work Item',
                    severity='error',
                )
                if response.error:
                    self.notify(
                        response.error,
                        title='Delete Work Item',
                        severity='error',
                    )

    def action_filter(self) -> None:
        if not self.app.config.search_results_page_filtering_enabled:  # type:ignore[attr-defined]
            return
        screen = cast('MainScreen', self.screen)  # type:ignore[name-defined] # noqa: F821
        widget = screen.search_results_filter_input
        widget.styles.display = 'block'
        widget.focus(True)
        widget.total = 0
        widget.value = ''
        self.refresh_bindings()

    def action_hide(self) -> None:
        if not self.app.config.search_results_page_filtering_enabled:  # type:ignore[attr-defined]
            return
        screen = cast('MainScreen', self.screen)  # type:ignore[name-defined] # noqa: F821
        # hide the input widget
        screen.search_results_filter_input.styles.display = 'none'
        # reset the results to the initial result set
        self.search_results = self.get_initial_results_set()
        # give focus back to the data table
        self.focus()
        self.refresh_bindings()

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        """Check if an action may run."""

        if action == 'filter' and not self.app.config.search_results_page_filtering_enabled:  # type:ignore[attr-defined]
            return False
        if action == 'hide' and not self.app.config.search_results_page_filtering_enabled:  # type:ignore[attr-defined]
            return False
        if action == 'previous_issues_page':
            if self.page > 1:
                return True
            return False
        if action == 'next_issues_page':
            if self.token_by_page.get(self.page + 1):
                return True
            return False
        return True

    async def action_previous_issues_page(self):
        if self.page > 1:
            # if there is no token then the 1st page wil be retrieved; otherwise the page with the given token is
            # fetched
            previous_page_token = self.token_by_page.get(self.page - 1)
            self.page -= 1
            screen = cast('MainScreen', self.screen)  # type:ignore[name-defined] # noqa: F821
            await screen.search_issues(previous_page_token, page=self.page)
            self.refresh_bindings()

    async def action_next_issues_page(self):
        if next_page_token := self.token_by_page.get(self.page + 1):
            self.page += 1
            screen = cast('MainScreen', self.screen)  # type:ignore[name-defined] # noqa: F821
            await screen.search_issues(next_page_token, page=self.page)
            self.refresh_bindings()

    def action_open_go_to_screen(self) -> None:
        """Opens a modal screen to show the work items related to the work item selected by the user in the search
        results table.

        The screen will be opened only if `config.enable_goto == True` and there is a work item selected.

        Returns:
            None
        """

        if self.app.config.enable_goto and self.current_work_item_key:  # type:ignore[attr-defined]
            self.app.push_screen(
                GoToScreen(self.current_work_item_key, self.app.api),  # type:ignore[attr-defined]
                callback=self._close_goto_screen,
            )
        elif not self.current_work_item_key:
            self.notify('Select/Highlight an item to view its related items')
        else:
            self.notify('This feature is disabled. Check config.enable_goto', severity='warning')

    def _close_goto_screen(self, work_item_key: str) -> None:
        # sends a message to request the handler, the Main Screen, to search for the work item with the given key
        if work_item_key:
            self.post_message(SearchWorkItem(work_item_key))

    def _load_work_item_after_viewing(self, work_item_key: str | None = None) -> None:
        """Posts a message to fetch a work item after the user selects it from the quick-view screen."""

        if work_item_key:
            self.post_message(SearchWorkItem(work_item_key))


class SearchResultsContainer(Container):
    """The container that holds the DataTable widget with the search results.

    This widget provides a reactive attribute called `pagination`. The attribute accepts a dictionary with the details
    of the search results' pagination. This includes `current_page_number` and `total`. When this attribute is updated
    the widget will update the legend in the border subtitle to display the number of results and the page number.
    """

    pagination: Reactive[dict | None] = reactive(None)
    """Reactive attribute that contains pagination details associated to the search results. This is used setting the
    widget's border subtitle with the page number and total records in the result."""
    auto_refresh_legend: Reactive[str | None] = reactive(None, init=False)
    """A legend that describes the state of the auto-refresh of the search results. It is displayed in the border
    subtitle after the pagination details."""

    def __init__(self, *args, **kwargs):
        border_title = kwargs.pop('border_title', None)
        super().__init__(*args, **kwargs)
        self.border_title = border_title or 'Work Items'
        self._total_results = None
        self._page_number = None
        self._total_pages: int | None = None

    def _update_border_subtitle(self) -> None:
        legend: str | None
        if self._total_results is None:
            legend = None if self._page_number is None else f'Page {self._page_number}'
        else:
            self._total_pages = self._total_results // self.app.config.search_results_per_page  # type:ignore[attr-defined]
            if (self._total_results % self.app.config.search_results_per_page) > 0:  # type:ignore[attr-defined]
                self._total_pages += 1
            if self._page_number is not None:
                legend = f'Page {self._page_number} of {self._total_pages} (total: {self._total_results})'
            else:
                legend = None
        if self.auto_refresh_legend:
            legend = (
                f'{legend} | {self.auto_refresh_legend}' if legend else self.auto_refresh_legend
            )
        self.border_subtitle = legend

    def watch_auto_refresh_legend(self, value: str | None = None) -> None:
        self._update_border_subtitle()

    def watch_pagination(self, response: dict) -> None:
        if response:
            self._page_number = max(1, response.get('current_page_number'))
            self._total_results = response.get('total', 0)
            self._update_border_subtitle()

    @on(IssuesSearchResultsTable.WorkItemDeleted)
    def update_pagination_details_after_delete(
        self, message: IssuesSearchResultsTable.WorkItemDeleted
    ) -> None:
        # update the total number of records and the border legend
        self._total_results = 0 if self._total_results is None else self._total_results - 1
        self._update_border_subtitle()
