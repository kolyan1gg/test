import asyncio
import os
import logging

from datetime import datetime
from random import randint, choice

from config_reader import config
from short_model import (get_categories_rn, get_categories_vit,
                         save_result_as_chart)
from gimages_dl import download_gimages, get_random_gimage

from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, FSInputFile
from aiogram.filters import Command, CommandObject
from aiogram.enums import ParseMode
from aiogram.utils.keyboard import InlineKeyboardBuilder


# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)
# Объект бота
bot = Bot(token=config.bot_token.get_secret_value())

# Диспетчер
dp = Dispatcher()
dp["started_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")

# Animal list
animal_list = ['Bear', 'Brown bear', 'Bull', 'Camel', 'Canary', 'Cat',
               'Caterpillar',
               'Cattle',
               'Centipede', 'Cheetah', 'Chicken', 'Crab',
               'Crocodile', 'Deer', 'Dog', 'Duck',
               'Eagle', 'Elephant', 'Fish', 'Fox', 'Frog',
               'Giraffe', 'Goat', 'Goldfish', 'Goose',
               'Hamster', 'Harbor seal', 'Hedgehog',
               'Hippopotamus', 'Horse', 'Jaguar', 'Jellyfish',
               'Kangaroo', 'Koala', 'Ladybug', 'Leopard',
               'Lion', 'Lizard', 'Lynx', 'Magpie',
               'Monkey', 'Moths and butterflies', 'Mouse',
               'Mule', 'Ostrich', 'Otter', 'Owl', 'Panda',
               'Parrot', 'Penguin', 'Pig', 'Polar bear',
               'Rabbit', 'Raccoon', 'Raven', 'Red panda',
               'Rhinoceros', 'Scorpion', 'Sea lion',
               'Sea turtle', 'Seahorse', 'Shark', 'Sheep',
               'Shrimp', 'Snail', 'Snake', 'Sparrow',
               'Spider', 'Squid', 'Squirrel', 'Starfish',
               'Swan', 'Tick', 'Tiger', 'Tortoise',
               'Turkey', 'Turtle', 'Whale', 'Woodpecker',
               'Worm', 'Zebra']

new_images = []


# Хэндлер на команду /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        'Привет! Я определяю зверушку по фотографии. '
        'Отправь мне фотографию, и я скажу кто на ней'
        'изображен.'
        ' \nНапиши /help, и я покажу пример, как я работаю')
    await message.answer(
        'Для справки список всех '
        'команд: \n/help \n/info \n/example \n/help '
        '\n/g [запрос] \n/g')
    await message.answer(
        'Если лень искать картинку, можешь написать /g [запрос] - '
        'например, "/g злой тигр", я найду 20 картинок по твоему '
        'запросу в Google Images, выберу случайную и определю её класс')
    await message.answer(
        'Если совсем влом, напиши просто /g, я загуглю картинку '
        'случайного животного и потом определю, кто это')
    await message.answer(
        'Или напиши /example, и я достану случайную картинку '
        'из своей библиотеки')


# Хэндлер на команду /help
@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer("Вот пример того, как cо мной взаимодейстовавать...")
    # тут должен быть скриншот уже готового бота (последний шаг)
    photo_1 = "https://disk.yandex.ru/i/0nJvrpXn1mjSyg"
    photo_2 = "https://disk.yandex.ru/i/QvJuz5j3Kimg9g"
    await bot.send_photo(message.chat.id, photo_1)
    await message.answer('Выбираем модель и нажимаем кнопку "Подтвердить"')
    await bot.send_photo(message.chat.id, photo_2)
    await message.answer(
        'Если хочешь протестировать, вот команда /example, отправлю '
        'тебе фотографию, которую ты можешь использовать '
        'для моего тестирования.')


# Хэндлер на команду /example
@dp.message(Command("example"))
async def cmd_example(message: types.Message):
    await message.answer("Вот случайная картинка из моей библиотеки")
    selection = randint(1, 10)
    file_name = (f"./sample/{selection}.jpg"
                 if os.name == 'nt'
                 else f"sample/{selection}.jpg")
    print(file_name)

    image_to_send = FSInputFile(file_name)
    await bot.send_photo(message.chat.id, image_to_send)

    new_images.append(file_name)
    await message.answer(
        "Я могу определить, кто на ней изображён. 'Выберите модель: -",
        reply_markup=model_keyboard())


@dp.message(Command("info"))
async def cmd_info(message: types.Message, started_at: str):
    await message.answer(f"Бот запущен {started_at}")


# New code
new_images = []


# Взаимодействие с пользователем после отправки им фотографии
def model_keyboard():
    # выбираем модель для предсказывания
    buttons = [
        [
            types.InlineKeyboardButton(text="RESNET",
                                       callback_data="model_RESNET"),
            types.InlineKeyboardButton(text="VIT",
                                       callback_data="model_VIT")
        ],
        [types.InlineKeyboardButton(text="Подтвердить",
                                    callback_data="model_SELECT")]
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


user_data = {}


# кнопка для подтверждения выбора модели пользователем
async def update_num_text(message: types.Message, new_value: int):
    await message.edit_text(
        f"Выберите модель: {new_value}",
        reply_markup=model_keyboard()
    )


# Скачивание фотографии пользователя
@dp.message(F.photo)
async def download_photo(message: Message,  bot: Bot):
    await bot.download(
        message.photo[-1],
        destination=(f"./tmp/{message.photo[-1].file_id}.jpg"
                     if os.name == 'nt'
                     else f"/tmp/{message.photo[-1].file_id}.jpg")
    )
    new_image = (f"./tmp/{message.photo[-1].file_id}.jpg"
                 if os.name == 'nt'
                 else f"/tmp/{message.photo[-1].file_id}.jpg")
    new_images.append(new_image)
    print(new_images)

    user_data[message.from_user.id] = 0
    await message.answer(
        "Сохраняю вашу картинку и начинаю думать, кто на ней...",
        parse_mode=ParseMode.HTML
    )
    # активация инлайн кнопок
    await message.answer("Выберите модель: -", reply_markup=model_keyboard())


# выбор модели и загрузка нейросети для предсказывания
@dp.callback_query(F.data.startswith("model_"))
async def callbacks_num(callback: types.CallbackQuery):
    user_value = user_data.get(callback.from_user.id, 0)
    action = callback.data.split("_")[1]

    # Активация различных моделей в зависимости от выбора пользователя
    if action == "RESNET":
        user_data[callback.from_user.id] = action
        user_value = action
        await update_num_text(callback.message, user_value)
    elif action == "VIT":
        user_data[callback.from_user.id] = action
        user_value = action
        await update_num_text(callback.message, user_value)
    elif action == "SELECT":
        await callback.message.edit_text(
            f"Выбрана модель: {user_value}, "
            "начинаю думать, кто на ней изображен...")

        # отправка картинки в нейросеть,
        # получение ответа и передача пользователю
        if user_value == "RESNET":

            full_answer = get_categories_rn(new_images[-1])
            short_answer = full_answer['Category ID'][0]
            image_to_send = FSInputFile(save_result_as_chart(full_answer))

            await callback.message.edit_text(
                f"Я думаю, что это {str(short_answer)}",
                parse_mode=ParseMode.HTML
            )
            await callback.message.answer(
                "А вот все топ классы",
                parse_mode=ParseMode.HTML
            )

            await callback.message.answer_photo(image_to_send)

            # обратная свяь от пользователя
            builder = InlineKeyboardBuilder()
            builder.add(types.InlineKeyboardButton(
                text="Я прав",
                callback_data="true_answer")
            )
            builder.add(types.InlineKeyboardButton(
                text="Я не прав",
                callback_data="false_answer")
            )
            await callback.message.answer('Обратная связь',
                                          reply_markup=builder.as_markup())

        # отправка картинки в нейросеть, получение ответа
        # и передача пользователю
        elif user_value == "VIT":

            full_answer = get_categories_vit(new_images[-1])
            short_answer = full_answer['Category ID'][0]
            image_to_send = FSInputFile(save_result_as_chart(full_answer))

            await callback.message.edit_text(
                f"Я думаю, что это {str(short_answer)}",
                parse_mode=ParseMode.HTML
            )
            await callback.message.answer(
                "А вот все топ классы",
                parse_mode=ParseMode.HTML
            )

            await callback.message.answer_photo(image_to_send)

            # обратная связь от пользователя
            builder = InlineKeyboardBuilder()
            builder.add(types.InlineKeyboardButton(
                text="Я прав",
                callback_data="true_answer")
            )
            builder.add(types.InlineKeyboardButton(
                text="Я не прав",
                callback_data="false_answer")
            )
            await callback.message.answer('Обратная связь',
                                          reply_markup=builder.as_markup())

        else:
            await callback.message.edit_text(
                "Error",
                parse_mode=ParseMode.HTML
            )


# Приём ответа 1 от Callback кнопки
@dp.callback_query(F.data == "true_answer")
async def true_answer(callback: types.CallbackQuery):
    await callback.message.answer("Ура! Я так и знал.")


# Приём ответа 2 от Callback кнопки
@dp.callback_query(F.data == "false_answer")
async def false_answer(callback: types.CallbackQuery):
    await callback.message.answer(
        "Спасибо за фидбек. Меня обновят, и я стану умнее.")


@dp.message(Command('g'))
async def analyze_random_image(message: Message, command: CommandObject):
    # Сюда будем помещать file_id отправленных файлов,
    # чтобы потом ими воспользоваться

    if command.args is None:
        await message.answer(
            "Нет аргументов, выбираем случайную картинку"
        )
        category = choice(animal_list)
        print(category)
        download_gimages(category)
    else:
        category = command.args
        download_gimages(category)

    random_image = get_random_gimage()
    new_images.append(random_image)
    image_to_send = FSInputFile(random_image)
    print(random_image)

    if command.args is None:
        await message.answer(
            "Вот случайная картинка по одной из категорий животных")
    else:
        await message.answer(
            f"Вот случайная картинка по вашему запросу - {category}")

    await bot.send_photo(message.chat.id, image_to_send)
    await message.answer("Выберите модель: -",
                         reply_markup=model_keyboard())


# Запуск процесса поллинга новых апдейтов
async def main():
    await dp.start_polling(bot, mylist=[1, 2, 3])

if __name__ == "__main__":
    asyncio.run(main())
