import asyncio
from datetime import datetime
import logging
from aiogram import Bot, Dispatcher, types, Router
from aiogram.filters.command import Command
from config_reader import config
from aiogram import F
from aiogram.types import Message
from aiogram.filters import Command, CommandObject
from aiogram.enums import ParseMode
from aiogram.types import FSInputFile, URLInputFile, BufferedInputFile


from aiogram import types
import os

from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton



# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)
# Объект бота
bot = Bot(token=config.bot_token.get_secret_value()) 

# Диспетчер
dp = Dispatcher()
dp["started_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")



# New code
from short_model import get_categories_rn, get_categories_vit
from gimages_dl import download_gimages, get_random_gimage
new_images = []

from aiogram.filters import Command
from aiogram.types import FSInputFile, Message
from aiogram.utils.media_group import MediaGroupBuilder
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from random import randint

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

@dp.message(Command("random"))
async def cmd_random(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="Нажми меня",
        callback_data="random_value")
    )
    await message.answer(
        "Нажмите на кнопку, чтобы бот отправил число от 1 до 10",
        reply_markup=builder.as_markup()
    )

@dp.callback_query(F.data == "random_value")
async def send_random_value(callback: types.CallbackQuery):
    await callback.message.answer(str(randint(1, 10)))

def model_keyboard():
    buttons = [
        [
            types.InlineKeyboardButton(text="RESNET", callback_data="model_RESNET"),
            types.InlineKeyboardButton(text="VIT", callback_data="model_VIT")
        ],
        [types.InlineKeyboardButton(text="Подтвердить", callback_data="model_SELECT")]
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


user_data = {}
new_images = []

async def update_num_text(message: types.Message, new_value: int):
    await message.edit_text(
        f"Выберите модель: {new_value}",
        reply_markup=model_keyboard()
    )

@dp.message(F.photo)
async def download_photo(message: Message,  bot: Bot):
    await bot.download(
        message.photo[-1],
        destination = f"./tmp/{message.photo[-1].file_id}.jpg" if os.name == 'nt' else f"/tmp/{message.photo[-1].file_id}.jpg"
    )

    new_image = f"./tmp/{message.photo[-1].file_id}.jpg" if os.name == 'nt' else f"/tmp/{message.photo[-1].file_id}.jpg"
    new_images.append(new_image)
    print(new_images)

    user_data[message.from_user.id] = 0
    await message.answer(
        f"Hello, <b>{message.from_user.full_name}</b>, images saved",
        parse_mode=ParseMode.HTML
    )
    await message.answer("Выберите модель: -", reply_markup=model_keyboard())

@dp.callback_query(F.data.startswith("model_"))
async def callbacks_num(callback: types.CallbackQuery):
    user_value = user_data.get(callback.from_user.id, 0)
    action = callback.data.split("_")[1]

    if action == "RESNET":
        user_data[callback.from_user.id] = action
        user_value = action
        await update_num_text(callback.message, user_value)
    elif action == "VIT":
        user_data[callback.from_user.id] = action
        user_value = action
        await update_num_text(callback.message, user_value)
    elif action == "SELECT":
        await callback.message.edit_text(f"Выбрана модель: {user_value}")
        
        if user_value == "RESNET":
            await callback.message.edit_text(
                str(get_categories_rn(new_images[-1])),
                parse_mode=ParseMode.HTML
            )
        elif user_value == "VIT":
            await callback.message.edit_text(
                str(get_categories_vit(new_images[-1])),
                parse_mode=ParseMode.HTML
            )
        else:
            await callback.message.edit_text(
                "Error",
                parse_mode=ParseMode.HTML
            )



@dp.message(Command('random_image'))
async def analyze_random_image(message: Message, command: CommandObject):
    # Сюда будем помещать file_id отправленных файлов, чтобы потом ими воспользоваться
    file_ids = []

    if command.args is None:
        await message.answer(
            "Нет аргументов, выбираем случайную картинку"
        )
        
        download_gimages('жираф')
    else:
        category = command.args
        download_gimages(category)


    random_image = get_random_gimage()
    new_images.append(random_image)
    image_to_send = FSInputFile(random_image)
    print(random_image)


    if command.args is None:
        await message.answer(f"Вот случайная картинка по одной из категорий животных")
    else:
        await message.answer(f"Вот случайная картинка по вашему запросу - {category}")

    
    await bot.send_photo(message.chat.id, image_to_send)
    await message.answer("Выберите модель: -", reply_markup=model_keyboard())


    '''
    # Отправка файла из файловой системы
    result = await message.answer_photo(
        random_image,
        caption="Случайное изображение из Google Image Search"
    )
    file_ids.append(result.photo[-1].file_id)
    '''



'''
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

'''
# Хэндлер на команду /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Hello!")


@dp.message(Command("info"))
async def cmd_info(message: types.Message, started_at: str):
    await message.answer(f"Бот запущен {started_at}")
# Запуск процесса поллинга новых апдейтов
async def main():
    await dp.start_polling(bot, mylist=[1, 2, 3])

if __name__ == "__main__":
    asyncio.run(main())
