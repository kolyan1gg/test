import asyncio
from datetime import datetime
import logging
from aiogram import Bot, Dispatcher, types, Router
from aiogram.filters.command import Command
from config_reader import config
from aiogram import F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.types import FSInputFile, URLInputFile, BufferedInputFile

from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InlineKeyboardButton, KeyboardBuilder


# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)
# Объект бота
bot = Bot(token=config.bot_token.get_secret_value()) 

# Диспетчер
dp = Dispatcher()
dp["started_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")

# Роутер
router = Router()

dp.include_router(router)


# New code
from short_model import get_categories
new_images = []

from aiogram.filters import Command
from aiogram.types import FSInputFile, Message
from aiogram.utils.media_group import MediaGroupBuilder
from aiogram.utils.keyboard import ReplyKeyboardBuilder

@dp.message(Command("special_buttons"))
async def cmd_special_buttons(message: types.Message):
    builder = ReplyKeyboardBuilder()
    # метод row позволяет явным образом сформировать ряд
    # из одной или нескольких кнопок. Например, первый ряд
    # будет состоять из двух кнопок...
    builder.row(
        types.KeyboardButton(text="Запросить геолокацию", request_location=True),
        types.KeyboardButton(text="Запросить контакт", request_contact=True)
    )
    # ... второй из одной ...
    builder.row(types.KeyboardButton(
        text="Создать викторину",
        request_poll=types.KeyboardButtonPollType(type="quiz"))
    )
    # ... а третий снова из двух
    builder.row(
        types.KeyboardButton(
            text="Выбрать премиум пользователя",
            request_user=types.KeyboardButtonRequestUser(
                request_id=1,
                user_is_premium=True
            )
        ),
        types.KeyboardButton(
            text="Выбрать супергруппу с форумами",
            request_chat=types.KeyboardButtonRequestChat(
                request_id=2,
                chat_is_channel=False,
                chat_is_forum=True
            )
        )
    )
    # WebApp-ов пока нет, сорри :(

    await message.answer(
        "Выберите действие:",
        reply_markup=builder.as_markup(resize_keyboard=True),
    )
@dp.message(Command("album"))
async def cmd_album(message: Message):
    album_builder = MediaGroupBuilder(
        caption="Общая подпись для будущего альбома"
    )
    album_builder.add(
        type="photo",
        media=FSInputFile("image_from_pc.jpg")
        # caption="Подпись к конкретному медиа"

    )
    # Если мы сразу знаем тип, то вместо общего add
    # можно сразу вызывать add_<тип>
    album_builder.add_photo(
        # Для ссылок или file_id достаточно сразу указать значение
        media="https://picsum.photos/seed/groosha/400/300"
    )
    album_builder.add_photo(
        media="AgACAgIAAxkDAAMIZYGKISIjylV7sEfb23im0GEzqn8AAmLPMRvphwlIWXLl0_ISWp8BAAMCAAN4AAMzBA"
    )
    await message.answer_media_group(
        # Не забудьте вызвать build()
        media=album_builder.build()
    )

@dp.message(Command('images'))
async def upload_photo(message: Message):
    # Сюда будем помещать file_id отправленных файлов, чтобы потом ими воспользоваться
    file_ids = []

    # Чтобы продемонстрировать BufferedInputFile, воспользуемся "классическим"
    # открытием файла через `open()`. Но, вообще говоря, этот способ
    # лучше всего подходит для отправки байтов из оперативной памяти
    # после проведения каких-либо манипуляций, например, редактированием через Pillow
    with open("image_from_pc.jpg", "rb") as image_from_buffer:
        result = await message.answer_photo(
            BufferedInputFile(
                image_from_buffer.read(),
                filename="image from buffer.jpg"
            ),
            caption="Изображение из буфера"
        )
        file_ids.append(result.photo[-1].file_id)

    # Отправка файла из файловой системы
    image_from_pc = FSInputFile("image_from_pc.jpg")
    result = await message.answer_photo(
        image_from_pc,
        caption="Изображение из файла на компьютере"
    )
    file_ids.append(result.photo[-1].file_id)

    # Отправка файла по ссылке
    image_from_url = URLInputFile("https://picsum.photos/seed/groosha/400/300")
    result = await message.answer_photo(
        image_from_url,
        caption="Изображение по ссылке"
    )
    file_ids.append(result.photo[-1].file_id)
    await message.answer("Отправленные файлы:\n"+"\n".join(file_ids))


@dp.message(F.photo)
async def download_photo(message: Message, bot: Bot):
    await bot.download(
        message.photo[-1],
        destination=f"/tmp/{message.photo[-1].file_id}.jpg" # Linux
        # destination=f"./tmp/{message.photo[-1].file_id}.jpg" # Windows

    )
    await message.answer(
        f"Hello, <b>{message.from_user.full_name}</b>, images saved",
        parse_mode=ParseMode.HTML
    )

    '''
    # Create InlineKeyboard
    markup = InlineKeyboardMarkup()
    button1 = InlineKeyboardButton("Option 1", callback_data='button1')
    button2 = InlineKeyboardButton("Option 2", callback_data='button2')
    markup.add(button1, button2)
    '''

    def genmarkup(data):
        builder = KeyboardBuilder()
        for i in data:
            button = InlineKeyboardButton(text=i[1], callback_data=i[2])
            builder.add(button)
        return builder.as_markup()

    # Create InlineKeyboard
    markup = genmarkup(['button1', 'button2', 'button3'])

    # Send a message with the buttons
    await message.answer("Choose an option:", reply_markup=markup)

    
    new_image = f"/tmp/{message.photo[-1].file_id}.jpg" # Linux
    # new_image = f"./tmp/{message.photo[-1].file_id}.jpg" # Windows
    new_images.append(new_image)
    print(new_images)
    await message.answer(
        f"New image saved: <b> {new_image}</b>",
        parse_mode=ParseMode.HTML
    )
    await message.answer(
        str(get_categories(new_image)),
        parse_mode=ParseMode.HTML
    )


@router.callback_query(lambda c: c.data.startswith('button'))
async def process_callback_button(callback_query: types.CallbackQuery):
    await callback_query.bot.answer_callback_query(callback_query.id)
    _, button_type, new_image = callback_query.data.split('_')

    if button_type == 'button1':
        response = str(get_categories(new_image))
    else:
        response = str(get_categories2(new_image))

    await callback_query.message.answer(response, parse_mode=types.ParseMode.HTML)

@dp.message(F.sticker)
async def download_sticker(message: Message, bot: Bot):
    await bot.download(
        message.sticker,
        # для Windows пути надо подправить
        destination=f"./tmp/{message.sticker.file_id}.webp"
    )


@dp.message(Command("hello"))
async def cmd_hello(message: Message):
    await message.answer(
        f"Hello, <b>{message.from_user.full_name}</b>",
        parse_mode=ParseMode.HTML
    )

@dp.message(F.text, Command("test"))
async def any_message(message: Message):
    await message.answer(
        "Hello, <b>worldd</b>!",
        parse_mode=ParseMode.HTML
    )
    await message.answer(
        "Hello, *world*\!",
        parse_mode=ParseMode.MARKDOWN_V2
    )


# Хэндлер на команду /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Hello!")

# Хэндлер на команду /test1
@dp.message(Command("test1"))
async def cmd_test1(message: types.Message):
    await message.reply("Test 1")

# Хэндлер на команду /test2
@dp.message(Command("test2"))
async def cmd_test2(message: types.Message):
    await message.reply("Test 2")

@dp.message(Command("dice"))
async def cmd_dice(message: types.Message):
    await message.answer_dice(emoji="🎲")


@dp.message(Command("add_to_list"))
async def cmd_add_to_list(message: types.Message, mylist: list[int]):
    mylist.append(7)
    await message.answer("Добавлено число 7")


@dp.message(Command("show_list"))
async def cmd_show_list(message: types.Message, mylist: list[int]):
    await message.answer(f"Ваш список: {mylist}")


@dp.message(Command("info"))
async def cmd_info(message: types.Message, started_at: str):
    await message.answer(f"Бот запущен {started_at}")
# Запуск процесса поллинга новых апдейтов
async def main():
    await dp.start_polling(bot, mylist=[1, 2, 3])

if __name__ == "__main__":
    asyncio.run(main())
