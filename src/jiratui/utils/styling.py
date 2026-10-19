import colorsys
import re

from jiratui.config import CONFIGURATION

WORK_ITEM_STATUS_STYLES = {
    'done': 'green',
    'in_review': 'darkolivegreen',
    'in_progress': 'blue',
    'to_do': 'yellow',
}
"""The default colors to use to display/style the status of tasks, e.g. tasks listed in the search results tab."""

WORK_ITEM_TYPE_STYLES = {
    'bug': '#F15B50',
    'documentation': '#6A9A23',
    'epic': 'yellow',
    'qa': '#4688EC',
    'spike': '#E06C00',
    'story': '#BF63F3',
    'task': '#4CB0EC',
    'technical_story': '#4688EC',
}
"""The default colors to use to display/style the type of tasks, e.g. tasks listed in the search results tab. Except
for epics, these are the colors of the icons of the types in Jira."""

WORK_ITEM_PRIORITY_RANKS = {
    'highest': 1,
    'high': 2,
    'medium': 3,
    'low': 4,
    'lowest': 5,
}
"""The rank of the default priorities of Jira, from the highest (1) to the lowest (5)."""
WORK_ITEM_PRIORITY_LEVELS = 5
"""The number of levels of priority of the gradient of colors used to display the priority of tasks."""


def get_style_for_work_item_status(status_name: str) -> str:
    """Gets the style definition for displaying the status of a work item in the search results.

    ```{important}
    It assumes that the id/key of the status values defined in the config file's `styling` section are expressed in
    lowercase and w/o blank spaces.
    ```

    Args:
        status_name: the name of the status as defined by Jira.

    Returns:
        A color name or CSS-style definition; e.g. #FF0000 or 'red'
    """

    if not status_name:
        return ''
    status_key = status_name.lower().replace(' ', '_')
    if (styling := CONFIGURATION.get().styling) and (
        custom_colors := styling.work_item_status_colors
    ):
        color = custom_colors.get(status_key, WORK_ITEM_STATUS_STYLES.get(status_key, ''))
        return color or WORK_ITEM_STATUS_STYLES.get(status_key, '')
    return WORK_ITEM_STATUS_STYLES.get(status_key, '')


def get_style_for_work_item_type(type_name: str) -> str:
    """Gets the style definition for displaying the type of work item in the search results.

    ```{important}
    It assumes that the id/key of the status values defined in the config file's `styling` section are expressed in
    lowercase and w/o blank spaces.
    ```

    Args:
        type_name: the name of the type.

    Returns:
        A color name or CSS-style definition; e.g. #FF0000 or 'red'
    """

    if not type_name:
        return ''
    type_key = type_name.lower().replace(' ', '_')
    if (styling := CONFIGURATION.get().styling) and (
        custom_colors := styling.work_item_type_colors
    ):
        color = custom_colors.get(type_key, WORK_ITEM_TYPE_STYLES.get(type_key, ''))
        return color or WORK_ITEM_TYPE_STYLES.get(type_key, '')
    return WORK_ITEM_TYPE_STYLES.get(type_key, '')


def get_work_item_priority_rank(priority_name: str) -> int | None:
    """Gets the rank of a priority, from the highest priority (1) to the lowest one.

    The rank is the number of priorities whose name starts with a code like `P1` (e.g. `P1: Blocker`); otherwise it is
    the rank of the default priorities of Jira (`Highest`, `High`, `Medium`, `Low`, `Lowest`).

    Args:
        priority_name: the name of the priority.

    Returns:
        The rank of the priority or `None` if the rank of the priority is unknown.
    """

    if match := re.match(r'\s*p(\d+)\b', priority_name, flags=re.IGNORECASE):
        return int(match.group(1))
    return WORK_ITEM_PRIORITY_RANKS.get(priority_name.strip().lower())


def get_color_for_work_item_priority_rank(rank: int) -> str:
    """Gets the color of a rank of priority in a gradient from red (the highest priority) to blue (the lowest one).

    Args:
        rank: the rank of the priority; 1 is the highest priority.

    Returns:
        An RGB color, e.g. `#F25555`.
    """

    position = (min(max(rank, 1), WORK_ITEM_PRIORITY_LEVELS) - 1) / (WORK_ITEM_PRIORITY_LEVELS - 1)
    # the hue goes from red (0) to blue (2/3) through yellow, green and cyan
    red, green, blue = colorsys.hsv_to_rgb(position * 2 / 3, 0.65, 0.95)
    return f'#{round(red * 255):02X}{round(green * 255):02X}{round(blue * 255):02X}'


def get_style_for_work_item_priority(priority_name: str) -> str:
    """Gets the color style definition for displaying the priority of work items.

    The colors defined in the config file's `styling` section have precedence. Otherwise, the color depends on the rank
    of the priority: from red for the highest priority to blue for the lowest one.

    ```{important}
    It assumes that the id/key of the priority values defined in the config file's `styling` section are expressed in
    lowercase and w/o blank spaces. For priorities whose name starts with a code, e.g. `P1: Blocker`, the key can also
    be the code, e.g. `p1`.
    ```

    Args:
        priority_name: the name of the priority.

    Returns:
        A color name or CSS-style definition; e.g. #FF0000 or 'red'
    """

    if not priority_name:
        return ''
    if (styling := CONFIGURATION.get().styling) and (
        custom_colors := styling.work_item_priority_colors
    ):
        priority_key = priority_name.lower().replace(' ', '_')
        code_key = priority_name.split(':', 1)[0].strip().lower()
        if color := custom_colors.get(priority_key) or custom_colors.get(code_key):
            return color
    if (rank := get_work_item_priority_rank(priority_name)) is not None:
        return get_color_for_work_item_priority_rank(rank)
    return ''
