import pytest
from unittest.mock import MagicMock, AsyncMock
from final import save_task, format_deadline, get_activity_data, add_task, list_tasks

@pytest.fixture
def mock_cursor():
    """Мок для курсора базы данных."""
    return MagicMock()

@pytest.fixture
def mock_conn(mock_cursor):
    """Мок для подключения к базе данных."""
    conn = MagicMock()
    conn.cursor.return_value = mock_cursor
    return conn

@pytest.fixture
def user_id():
    """Тестовый ID пользователя."""
    return 12345

@pytest.fixture
def test_task_data():
    """Тестовые данные задачи."""
    return {
        'title': 'Test Task',
        'description': 'This is a test task',
        'deadline': '15.12.2024 14:00',
        'priority': 3,
    }

def test_save_task(mock_cursor, user_id, test_task_data):
    """Тест для функции сохранения задачи."""
    save_task(user_id, test_task_data)
    mock_cursor.execute.assert_called_once_with(
        '''INSERT INTO tasks (user_id, title, description, deadline, priority, status, creation_date)
           VALUES (?, ?, ?, ?, ?, ?, ?)''',
        (user_id, 'Test Task', 'This is a test task', '15.12.2024 14:00', 3, 'active', pytest.any(str))
    )

def test_format_deadline_valid_date():
    """Тест для функции форматирования дедлайна с корректной датой."""
    result = format_deadline("15.12.2024 14:00")
    assert result == "15.12.2024 14:00"

def test_format_deadline_invalid_date():
    """Тест для функции форматирования дедлайна с некорректной датой."""
    with pytest.raises(ValueError, match="Неверный формат даты"):
        format_deadline("invalid_date")

def test_get_activity_data(mock_cursor, user_id):
    """Тест для функции получения данных активности."""
    mock_cursor.fetchone.side_effect = [(5,), (20,), (100,), (300,)]
    tasks_week, tasks_month, tasks_all_time, pomodoro_minutes = get_activity_data(user_id)
    assert tasks_week == 5
    assert tasks_month == 20
    assert tasks_all_time == 100
    assert pomodoro_minutes == 300
    assert mock_cursor.execute.call_count == 4

@pytest.fixture
def mock_update():
    """Мок для объекта Update."""
    update = MagicMock()
    update.message.reply_text = AsyncMock()
    update.message.text = "Test"
    return update

@pytest.fixture
def mock_context():
    """Мок для объекта ContextTypes."""
    context = MagicMock()
    context.user_data = {}
    return context

@pytest.mark.asyncio
async def test_add_task(mock_update, mock_context):
    """Тест для обработки команды добавления задачи."""
    result = await add_task(mock_update, mock_context)
    assert result == 0  # Проверяем переход на этап TITLE
    mock_update.message.reply_text.assert_called_with(
        "Введите название задачи:"
    )

@pytest.mark.asyncio
async def test_list_tasks_empty(mock_update, mock_context, mock_cursor):
    """Тест для функции отображения списка задач (если список пуст)."""
    mock_cursor.fetchall.return_value = []
    await list_tasks(mock_update, mock_context)
    mock_update.message.reply_text.assert_called_once_with("У вас нет активных задач.")

@pytest.mark.asyncio
async def test_list_tasks_with_data(mock_update, mock_context, mock_cursor):
    """Тест для функции отображения списка задач с существующими задачами."""
    mock_cursor.fetchall.return_value = [
        ('Task 1', 'Description 1', '15.12.2024 18:00', 3),
        ('Task 2', 'Description 2', '16.12.2024 12:00', 2)
    ]
    await list_tasks(mock_update, mock_context)
    mock_update.message.reply_text.assert_called_once_with(
        "📌 *Task 1*\n📝 Description 1\n⏰ Дедлайн: 15.12.2024 18:00\n🔥 Приоритет: 3\n\n"
        "📌 *Task 2*\n📝 Description 2\n⏰ Дедлайн: 16.12.2024 12:00\n🔥 Приоритет: 2",
        parse_mode='Markdown'
    )