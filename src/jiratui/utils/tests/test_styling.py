from unittest.mock import MagicMock, patch

import pytest

from jiratui.utils.styling import (
    get_color_for_work_item_priority_rank,
    get_style_for_work_item_priority,
    get_style_for_work_item_status,
    get_style_for_work_item_type,
    get_work_item_priority_rank,
)


@pytest.fixture()
def mock_configuration():
    with patch('jiratui.utils.styling.CONFIGURATION') as mock_config_var:
        mock_config = MagicMock()
        mock_styling = MagicMock()
        mock_config.styling = mock_styling
        mock_config_var.get.return_value = mock_config
        yield mock_styling


@pytest.mark.parametrize(
    'status_name, expected_result',
    [
        ('done', 'green'),
        ('in review', 'darkolivegreen'),
        ('in progress', 'blue'),
        ('to do', 'yellow'),
        ('other', ''),
    ],
)
def test_get_style_for_work_item_status(mock_configuration, status_name, expected_result):
    mock_configuration.work_item_status_colors = None
    result = get_style_for_work_item_status(status_name)
    assert result == expected_result


@pytest.mark.parametrize(
    'custom_colors, status_name, expected_result',
    [
        ({'done': 'bright_green'}, 'done', 'bright_green'),  # custom overrides default
        ({'blocked': 'red'}, 'blocked', 'red'),  # custom adds new status
        ({'blocked': 'red'}, 'done', 'green'),  # default preserved when not overridden
        (None, 'done', 'green'),  # fallback to defaults when config is None
        ({'blocked': 'red'}, 'unknown_status', ''),  # unknown returns empty string
    ],
)
def test_get_style_for_work_item_status_with_custom_config(
    mock_configuration, custom_colors, status_name, expected_result
):
    mock_configuration.work_item_status_colors = custom_colors
    result = get_style_for_work_item_status(status_name)
    assert result == expected_result


@pytest.mark.parametrize(
    'type_name, expected_result',
    [
        ('bug', '#F15B50'),
        ('Documentation', '#6A9A23'),
        ('epic', 'yellow'),
        ('QA', '#4688EC'),
        ('Spike', '#E06C00'),
        ('Story', '#BF63F3'),
        ('task', '#4CB0EC'),
        ('Technical Story', '#4688EC'),
        ('other', ''),
    ],
)
def test_get_style_for_work_item_type(mock_configuration, type_name, expected_result):
    mock_configuration.work_item_type_colors = None
    result = get_style_for_work_item_type(type_name)
    assert result == expected_result


@pytest.mark.parametrize(
    'custom_colors, type_name, expected_result',
    [
        ({'bug': 'bright_red'}, 'bug', 'bright_red'),  # custom overrides default
        ({'story': 'cyan'}, 'story', 'cyan'),  # custom adds new type
        ({'story': 'cyan'}, 'bug', '#F15B50'),  # default preserved when not overridden
        (None, 'bug', '#F15B50'),  # fallback to defaults when config is None
        ({'story': 'cyan'}, 'unknown_type', ''),  # unknown returns empty string
    ],
)
def test_get_style_for_work_item_type_with_custom_config(
    mock_configuration, custom_colors, type_name, expected_result
):
    mock_configuration.work_item_type_colors = custom_colors
    result = get_style_for_work_item_type(type_name)
    assert result == expected_result


@pytest.mark.parametrize(
    'priority_name, expected_rank',
    [
        ('P1: Blocker / No workaround', 1),
        ('P3: Needed', 3),
        ('p5', 5),
        ('Highest', 1),
        ('medium', 3),
        ('Lowest', 5),
        ('Urgent', None),
        ('Priority 1', None),
    ],
)
def test_get_work_item_priority_rank(priority_name, expected_rank):
    assert get_work_item_priority_rank(priority_name) == expected_rank


@pytest.mark.parametrize(
    'rank, expected_color',
    [
        (1, '#F25555'),  # red
        (2, '#F2F255'),
        (3, '#55F255'),
        (4, '#55F2F2'),
        (5, '#5555F2'),  # blue
        (0, '#F25555'),  # ranks are clamped
        (9, '#5555F2'),
    ],
)
def test_get_color_for_work_item_priority_rank(rank, expected_color):
    assert get_color_for_work_item_priority_rank(rank) == expected_color


@pytest.mark.parametrize(
    'custom_colors, priority_name, expected_result',
    [
        (None, 'P1: Blocker / No workaround', '#F25555'),
        (None, 'Lowest', '#5555F2'),
        (None, 'Urgent', ''),
        (None, '', ''),
        ({'p1': 'magenta'}, 'P1: Blocker / No workaround', 'magenta'),  # the code is a valid key
        ({'highest': 'magenta'}, 'Highest', 'magenta'),
        ({'urgent': 'magenta'}, 'Urgent', 'magenta'),
        ({'p1': 'magenta'}, 'P2: Mandatory / Critical', '#F2F255'),  # gradient when not overridden
    ],
)
def test_get_style_for_work_item_priority(
    mock_configuration, custom_colors, priority_name, expected_result
):
    mock_configuration.work_item_priority_colors = custom_colors
    assert get_style_for_work_item_priority(priority_name) == expected_result
