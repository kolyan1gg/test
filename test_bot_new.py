import os

import pytest
from unittest.mock import patch, AsyncMock, call

from aiogram import Bot
from aiogram.filters import Command
from aiogram.types import Message, User, Chat, PhotoSize, CallbackQuery

from aiogram_tests import MockedBot
from aiogram_tests.handler import MessageHandler, CallbackQueryHandler
from aiogram_tests.types.dataset import MESSAGE

from datetime import datetime
from functools import partial

from bot_new import cmd_start, cmd_info, cmd_help, cmd_example
from bot_new import download_photo, model_keyboard, ParseMode
from bot_new import (update_num_text, analyze_random_image,
                     true_answer, false_answer)
from bot_new import callbacks_num, user_data, new_images


# cmd_start


@pytest.mark.asyncio
async def test_start_command():
    # Setup a mocked bot
    request = MockedBot(MessageHandler(cmd_start, Command("start")))

    # Simulate sending the "/start" command
    calls = await request.query(MESSAGE.as_object(text="/start"))

    # Fetch all messages sent by the bot in response
    all_replies = calls.send_message.fetchall()

    # Assert the number of replies matches expectation
    expected_replies_count = 5
    assert len(all_replies) == expected_replies_count, \
        "Bot did not send the expected number of replies."

    # Assert each message content if necessary
    expected_texts = [
        'Привет! Я определяю зверушку по фотографии. '
        'Отправь мне фотографию, и я скажу кто на ней изображен. '
        '\nНапиши /help, и я покажу пример, как я работаю',
        'Для справки список всех команд: \n/help \n/info '
        '\n/example \n/help \n/g [запрос] \n/g',
        'Если лень искать картинку, можешь написать /g [запрос] - '
        'например, "/g злой тигр", я найду 20 картинок по твоему '
        'запросу в Google Images, выберу случайную и определю её класс',
        'Если совсем влом, напиши просто /g, я загуглю картинку '
        'случайного животного и потом определю, кто это',
        'Или напиши /example, и я достану случайную картинку '
        'из своей библиотеки'
        ]

    for i, reply in enumerate(all_replies):
        assert (reply.text == expected_texts[i]), (
            f"Reply {i+1} did not match expected text."
        )

# download_photo


@pytest.mark.asyncio
@patch.object(Message, 'answer', new_callable=AsyncMock)  # Mock
@patch.object(Bot, 'download', new_callable=AsyncMock)  # Mock
async def test_download_photo(mock_answer, mock_download):
    # Create the mock Message object
    mock_bot = AsyncMock(spec=Bot)
    mock_download = mock_bot.download  # Mock download method

    mock_message = Message(
        message_id=1,
        from_user=User(id=123, is_bot=False, first_name="Test User"),
        chat=Chat(id=45683, type="private"),
        photo=[PhotoSize(file_id="testfileid", width=100,
                         height=100, file_unique_id="unique_file_id")],
        date=1611234567
    )

    await download_photo(mock_message, bot=mock_bot)

    mock_answer = mock_message.answer  # Mock the answer method of the bot

    # Print all mock calls to download
    print("Mock calls to download: ")
    print(mock_download)
    print(mock_answer.mock_calls)
    print(mock_download.await_args_list)
    print(mock_download.mock_calls)

    # Assertions
    destination_path = (f"./tmp/{mock_message.photo[-1].file_id}.jpg"
                        if os.name == 'nt'
                        else f"/tmp/{mock_message.photo[-1].file_id}.jpg")
    mock_download.assert_awaited_with(mock_message.photo[-1],
                                      destination=destination_path)

    # Ensure mock_answer was called twice
    assert mock_answer.call_count == 2

    # Ensure keyboard is called as expected
    expected_keyboard = model_keyboard()

    expected_calls = [
        call(
            "Сохраняю вашу картинку и начинаю думать, кто на ней...",
            parse_mode=ParseMode.HTML
        ),
        call(
            "Выберите модель: -",
            reply_markup=expected_keyboard
        )
    ]
    assert mock_answer.mock_calls == expected_calls


# cmd_info

@pytest.fixture
def started_at():
    started_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    return started_at


@pytest.mark.asyncio
async def test_cmd_info(started_at):
    cmd_info_with_started_at = partial(cmd_info, started_at=started_at)
    request = MockedBot(MessageHandler(cmd_info_with_started_at,
                                       Command("info")))
    calls = await request.query(MESSAGE.as_object(text="/info"))
    all_replies = calls.send_message.fetchall()

    expected_replies_count = 1
    assert (len(all_replies) == expected_replies_count), (
        "Bot did not send the expected number of replies."
        )

    expected_texts = [
                    f"Бот запущен {started_at}"
                    ]

    for i, reply in enumerate(all_replies):
        assert (reply.text == expected_texts[i]), (
            f"Reply {i+1} did not match expected text."
        )

# update_num_text


@pytest.fixture
def new_value():
    new_value = 1
    return new_value


@pytest.mark.asyncio
async def test_update_num_text(new_value):
    update_num_text_with_new_value = partial(update_num_text,
                                             new_value=new_value)
    request = MockedBot(MessageHandler(update_num_text_with_new_value))
    calls = await request.query(MESSAGE.as_object(text="/info"))
    all_replies = calls.edit_message_text.fetchall()

    expected_replies_count = 1
    assert len(all_replies) == (expected_replies_count), (
        "Bot did not send the expected number of replies."
    )
    expected_texts = [
                    f"Выберите модель: {new_value}"
                    ]

    for i, reply in enumerate(all_replies):
        assert (reply.text == expected_texts[i]), (
            f"Reply {i+1} did not match expected text."
        )

# analyze_random_image


def create_message(text='/g'):
    return Message(
        message_id=1,
        from_user=User(id=123, is_bot=False,
                       first_name="Test User"),
        chat=Chat(id=45683, type="private"),
        date=1611234567,
        text=text
    )


@pytest.mark.asyncio
@patch.object(Bot, 'send_message', new_callable=AsyncMock)
@patch.object(Bot, 'send_photo', new_callable=AsyncMock)
@pytest.mark.parametrize(
    "command_text,expected_replies_count,expected_texts", [
        ('/g', 3, [
            "Нет аргументов, выбираем случайную картинку",
            "Вот случайная картинка по одной из категорий животных",
            "Выберите модель: -"
        ]),
        ('/g dog', 2, [
            "Вот случайная картинка по вашему запросу - dog",
            "Выберите модель: -"
        ])
    ])
async def test_analyze_random_image(mock_send_photo, mock_send_message,
                                    command_text, expected_replies_count,
                                    expected_texts):

    message = create_message(command_text)
    request = MockedBot(MessageHandler(analyze_random_image, Command("g")))
    calls = await request.query(message)
    all_replies = calls.send_message.fetchall()

    assert len(all_replies) == (expected_replies_count), (
        "Bot did not send the expected number of text replies."
        )
    for i, reply in enumerate(all_replies):
        assert (reply.text == expected_texts[i]), (
            f"Reply {i+1} did not match expected text."
        )
    # Check if send_photo was called
    mock_send_photo.assert_awaited()


# cmd_help


@pytest.fixture
def message():
    return Message(
        message_id=1,
        from_user=User(id=123, is_bot=False,
                       first_name="Test User"),
        chat=Chat(id=45683, type="private"),
        date=1611234567,
        text='/help'
    )


@pytest.mark.asyncio
@patch.object(Bot, 'send_message', new_callable=AsyncMock)
@patch.object(Bot, 'send_photo', new_callable=AsyncMock)
async def test_cmd_help(mock_send_photo, mock_send_message,
                        message):
    request = MockedBot(MessageHandler(cmd_help, Command("help")))
    calls = await request.query(message)

    all_replies = calls.send_message.fetchall()

    expected_replies_count = 3
    assert (len(all_replies) == expected_replies_count), (
        "Bot did not send the expected number of text replies."
    )
    expected_texts = [
        "Вот пример того, как cо мной взаимодейстовавать...",
        'Выбираем модель и нажимаем кнопку "Подтвердить"',
        'Если хочешь протестировать, вот команда /example, '
        'отправлю тебе фотографию, которую ты можешь '
        'использовать для моего тестирования.'
    ]

    for i, reply in enumerate(all_replies):
        assert (reply.text == expected_texts[i]), (
            f"Reply {i+1} did not match expected text."
            )

    # Check if send_photo was called
    mock_send_photo.assert_awaited()


# cmd_example


@pytest.fixture
def message2():
    return Message(
        message_id=1,
        from_user=User(id=123, is_bot=False, first_name="Test User"),
        chat=Chat(id=45683, type="private"),
        date=1611234567,
        text='/example'
    )


@pytest.mark.asyncio
@patch.object(Bot, 'send_message', new_callable=AsyncMock)
@patch.object(Bot, 'send_photo', new_callable=AsyncMock)
async def test_cmd_example(mock_send_photo, mock_send_message, message2):
    request = MockedBot(MessageHandler(cmd_example, Command("example")))
    calls = await request.query(message2)

    all_replies = calls.send_message.fetchall()

    expected_replies_count = 2
    assert (len(all_replies) == expected_replies_count), (
        "Bot did not send the expected number of text replies."
    )
    expected_texts = [
        "Вот случайная картинка из моей библиотеки",
        "Я могу определить, кто на ней изображён. Выберите модель: -"
    ]

    for i, reply in enumerate(all_replies):
        assert (reply.text == expected_texts[i]), (
            f"Reply {i+1} did not match expected text."
        )
    # Check if send_photo was called
    mock_send_photo.assert_awaited()


# true_answer / false_answer

def fake_callback_query(callback_data):
    return CallbackQuery(
        id="unique-id",
        chat_instance='123',
        from_user=User(id=123, is_bot=False, first_name="Test User"),
        message=Message(
            message_id=1,
            date=1611234567,
            chat=Chat(id=45683, type="private"),
            from_user=User(id=123, is_bot=False, first_name="Test User"),
        ),
        data=callback_data
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "callback_data, expected_replies_count, expected_response, "
    "function_used", [
        ("true_answer", 1,
            "Ура! Я так и знал.", true_answer),
        ("false_answer", 1,
            "Спасибо за фидбек. Меня обновят, и я стану умнее.",
            false_answer)  # Assuming no response for this data
    ])
async def test_true_answer(callback_data, expected_replies_count,
                           expected_response, function_used):

    request = MockedBot(CallbackQueryHandler(function_used))

    # Create a fake callback query object with the specified data
    query = fake_callback_query(callback_data)

    calls = await request.query(query)
    all_replies = calls.send_message.fetchall()

    print(f'cb: {callback_data}')
    print(f'exp: {expected_response}')
    print(f'got: {all_replies[0].text}')

    assert (len(all_replies) == expected_replies_count), (
        "Bot did not send the expected number of text replies."
        )
    assert (all_replies[0].text == expected_response), (
        "The reply did not match the expected response."
    )


# callbacks_num


def fake_callback_query2(callback):
    return CallbackQuery(
        id="unique-id",
        chat_instance='123',
        from_user=User(id=123, is_bot=False, first_name="Test User"),
        message=Message(
            message_id=1,
            date=1611234567,
            chat=Chat(id=45683, type="private"),
            from_user=User(id=123, is_bot=False, first_name="Test User"),
        ),
        data=callback
    )


short_answer = 'A'


@patch("bot_new.get_categories_vit", return_value={'Category ID': ['A', 'B'],
                                                   'Probability': [0.8, 0.2]})
@patch("bot_new.get_categories_rn", return_value={'Category ID': ['A', 'B'],
                                                  'Probability': [0.8, 0.2]})
@patch.object(Bot, 'send_message', new_callable=AsyncMock)
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "callback, expected_replies_count, expected_response, "
    "user_value_before, user_value_after", [
        ("model_RESNET", 1, "Выберите модель: RESNET", None, "RESNET"),
        ("model_VIT", 1, "Выберите модель: VIT", None, "VIT"),
        ("model_SELECT", 2,
            ["Выбрана модель: RESNET, начинаю думать, кто на ней изображен...",
                f"Я думаю, что это {str(short_answer)}"], "RESNET",
            "RESNET"),
        ("model_SELECT", 2,
            ["Выбрана модель: VIT, начинаю думать, кто на ней изображен...",
                f"Я думаю, что это {str(short_answer)}"], "VIT",
            "VIT"),
        ("model_SELECT", 2,
            ["Выбрана модель: ERROR, начинаю думать, кто на ней изображен...",
                'Error'],
            "ERROR", "ERROR")
    ])
async def test_callbacks_num(mock_send_message, mock_get_categories_rn,
                             mock_get_categories_vit,
                             callback, expected_replies_count,
                             expected_response, user_value_before,
                             user_value_after):
    # Set initial user data if specified
    user_id = 123
    user_data[user_id] = callback.split("_")[1]

    new_images.clear()  # sample image for testing
    new_images.append('https://disk.yandex.ru/i/0nJvrpXn1mjSyg')  # sample img

    if user_value_before is not None:
        user_data[user_id] = user_value_before

    # Initialize MockedBot with the specific callback query handler
    request = MockedBot(CallbackQueryHandler(callbacks_num))
    query = fake_callback_query2(callback)

    calls = await request.query(query)

    # Fetch all replies sent in response to the callback query
    all_replies1 = calls.edit_message_text.fetchall()
    # all_replies2 = calls.send_message.fetchall()

    print(f'exp: {expected_response}')
    print(f'got: {all_replies1[0].text}')

    assert (len(all_replies1) == expected_replies_count), (
        "Bot did not send the expected number of text replies."
    )
    if expected_replies_count == 1:
        assert (all_replies1[0].text == expected_response), (
            "The reply did not match the expected response."
        )
    if expected_replies_count == 2:
        assert (all_replies1[0].text == expected_response[0]), (
            "The reply did not match the expected response."
        )
        assert (all_replies1[1].text == expected_response[1]), (
            "The reply did not match the expected response."
        )
