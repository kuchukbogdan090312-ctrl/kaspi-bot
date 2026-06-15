# бот игра про эко назв: таяние льда. юз @melting_of_the_glacier_bot

import sqlite3
import asyncio
import io
import sys 
import time
import random 

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import (
    BufferedInputFile,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InputMediaPhoto
)

TOKEN = "8690937191:AAH1uPvqhcSVKIUPpgu7GSZ7GM3GDTTHsMk"
bot = Bot(token=TOKEN)
dp = Dispatcher()
code2 = "1111"

# ВИЗУАЛ ЗАПУСКА (консоль)
print("ENTER CODE:")
konsol_visual = input()
if konsol_visual == code2:
    print(r"""
    __        __   _                             
    \ \      / /__| | ___ ___  _  __  __  ___      
     \ \ /\ / / _ \ |/ __/ _ \| '_  '_  \/ _ \     
      \ V  V /  __/ | (_| (_) | | | | | |  __/     
       \_/\_/ \___|_|\___\___/|_| |_| |_|\___|     
                    A D M I N ^^
        """)

    def slow_print(text, delay=0.05):
        for char in text:
            sys.stdout.write(char)
            sys.stdout.flush()
            time.sleep(delay)
        print()

    slow_print("[ SYSTEM INITIALIZING... ]")    # визуал!
    time.sleep(1)

    slow_print("[ LOADING WORD DATABASE... ]")  # визуал!
    time.sleep(1)

    slow_print("[ STATUS: READY ]")     # визуал!

    for i in range(101):
        bar = "█" * (i // 4) + "░" * (25 - (i // 4))
        print(f"\r[{bar}] {i}%", end="")
        time.sleep(0.03)        # загрузка
        
    # загружен!
    print("\n the game is loaded! can be launched in telegram")
    
else:
    print("code uncorrect")
    sys.exit()       

# ------------------ DB ------------------

conn = sqlite3.connect("game.db") # подключение к базе данных 
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    lang TEXT DEFAULT 'ru',
    username TEXT,
    points INTEGER DEFAULT 0
)
""") # работы с командами
conn.commit()


cursor.execute("""
CREATE TABLE IF NOT EXISTS used_codes (
    user_id INTEGER,
    code TEXT
)
""") # Создание таблицы

conn.commit()

# codes 
ADMIN_CODE = "ICEADMIN777"

admin_sessions = set()

luck_users = {}

CODES = {
    "ICE100": 100,
    "COOL250": 250,
    "GLACIER500": 500
}


# ===== ADMIN / USERS HELPERS =====

def is_admin(user_id: int) -> bool:
    return user_id in admin_sessions # Проверка админа


def get_user_by_username(username: str): # Поиск пользователя по username
    username = username.replace("@", "") # Удаление @

    cursor.execute("""
    SELECT user_id
    FROM users
    WHERE username = ?
    """, (username,))  # запрос в таблицу 

    return cursor.fetchone()


def get_lang(user_id):  # Получает язык чела 
    cursor.execute("SELECT lang FROM users WHERE user_id=?", (user_id,)) # Ищет язык по id
    row = cursor.fetchone()
    return row[0] if row else "ru"


def set_lang(user_id, lang): #Смена языка 
    cursor.execute("UPDATE users SET lang=? WHERE user_id=?", (lang, user_id))  # меняет тольео у нужного 
    conn.commit()           # сохраняет изменения 
    

def add_points(user_id, amount):  # Добавляет очки игроку

    cursor.execute("""
    UPDATE users
    SET points = points + ?
    WHERE user_id = ?
    """, (amount, user_id))

    conn.commit()

def ensure_user(user_id, username=None): 
    if username is None:    # Проверка юзера 
        username = "player"

    cursor.execute("""
    INSERT OR IGNORE INTO users (
        user_id,
        lang,
        username,
        points
    )
    VALUES (?, 'ru', ?, 0)
    """, (user_id, username))  

    cursor.execute("""
    UPDATE users
    SET username = ?
    WHERE user_id = ?
    """, (username, user_id))    # Вставка значений

    conn.commit()
    
# ------------------ TEXT ------------------

LANG_TEXT = {
    "ru": {
        "lose": "💀 Ты проиграл!",
        "eco": "🌍 Эко-совет:"
    },
    "en": {
        "lose": "💀 You lost!",
        "eco": "🌍 Eco tip:"
    }       
}

ECO_TIPS = {
    "ru": [
        "Сортируй мусор — пластик, стекло и бумага перерабатываются ♻️",
        "Используй многоразовую бутылку вместо пластиковой",
        "Выключай свет, когда выходишь из комнаты",
        "Не выбрасывай батарейки в обычный мусор",
        "Старайся меньше использовать пакеты",
        "Экономь воду — закрывай кран во время чистки зубов",
        "Сажай деревья или ухаживай за растениями 🌱"
    ],
    "en": [
        "Sort waste — plastic, glass and paper can be recycled ♻️",
        "Use a reusable bottle instead of plastic",
        "Turn off the lights when leaving a room",
        "Do not throw batteries in regular trash",
        "Try to use fewer plastic bags",
        "Save water — turn off the tap while brushing teeth",
        "Plant trees or take care of plants 🌱"
    ]
}                # перевод + советы 

def get_random_tip(lang):
    return random.choice(ECO_TIPS.get(lang, ECO_TIPS["ru"]))

TEXT = {
    "ru": {
        "start": "Привет! Ты попал в симулятор климата.\n\nГотов спасти планету? ^^\nпосмотреть все команды /help ",
        "about": (
            "🌍 Climate Survival Game\n\n"
            "Ты управляешь климатом планеты и пытаешься спасти ледник.\n\n"
            "❄️ Лёд тает\n"
            "💨 CO2 растёт\n"
            "🔥 Чем больше CO2 — тем быстрее конец\n\n"
            "🏆 Лидерборд скоро появится\n"
        ),
        "code_usage": "🔑 /code НАЗВАНИЕ",
        "code_not_found": "❌ Код не найден",
        "code_used": "❌ Код уже использован",
        "code_success": "🎁 Код активирован!\n+{reward} 🧊",
        "enter_code": "🔑 /code НАЗВАНИЕ",
        "game_start": "Игра началась! Действуй!",
        "tap": "Охладил! ^^",
        "need_start": "Сначала начни игру",
        "game_over": "⌛ КАТАСТРОФА! Лёд растаял полностью. Попробуй ещё раз: /start",
        "top": "🏆 Есть глобальный лидерборд\n",
        "top_cleared_global": "🏆 Глобальный топ был очищен",
        "help": (
            "📜 Помощь\n\n"
            "Команды:\n"
            "/start — начать игру\n"
            "/about — информация\n"
            "/help — помощь\n"
            "/lang — язык\n"
            "/top — лидерборд\n"
            "/code — коды (скоро)\n\n"
        ),
        "code": "🔑 Система кодов появился !",
        "lang": "🌍 Выбери язык:",
        "lang_changed": "🌍 Язык изменён",
        "admin_give": "🛠 Админ выдал вам {amount} 🧊 очков",
        "admin_remove": "🛠 Админ снял у вас {amount} 🧊 очков",
        "admin_x2": "🛠 Админ дал вам x2 бонус на {minutes} минут"
    },

    "en": {
        "start": "Hi! You entered climate simulator.\n\nReady to save the planet? ^^\nview all commands /help",
        "about": (
            "🌍 Climate Survival Game\n\n"
            "You control the planet climate and try to save the glacier.\n\n"
            "❄️ Ice is melting\n"
            "💨 CO2 is rising\n"
            "🔥 More CO2 = faster end\n\n"
            "🏆 Leaderboard coming soon\n"
        ),
        "code_usage": "🔑 /code NAME",
        "code_not_found": "❌ Code not found",
        "code_used": "❌ Code already used",
        "code_success": "🎁 Code activated!\n+{reward} 🧊",
        "enter_code": "🔑 /code NAME",
        "game_start": "Game started! Act now!",
        "tap": "Cooled! ^^",
        "need_start": "Start the game first",
        "game_over": "⌛ DISASTER! Ice fully melted. Try again: /start",
        "top": "🏆 Global leaderboard available\n",
        "top_cleared_global": "🏆 Global leaderboard was cleared",
        "help": (
            "📜 Help\n\n"
            "Commands:\n"
            "/start — start game\n"
            "/about — info\n"
            "/help — help\n"
            "/lang — language\n"
            "/top — leaderboard\n"
            "/code — codes (soon)\n\n"
        ),
        "code": "🔑 Code system active!",
        "lang": "🌍 Choose language:",
        "lang_changed_en": "🌍 Language changed",
        "admin_give": "🛠 Admin gave you {amount} 🧊 points",
        "admin_remove": "🛠 Admin removed {amount} 🧊 points",
        "admin_x2": "🛠 Admin gave you x2 bonus for {minutes} minutes"
    }
}
# перевод 
def t(user_id, key):
    lang = get_lang(user_id)
    return TEXT.get(lang, TEXT["ru"]).get(key, key)    # переводит на ru en 


# ------------------ GAME ------------------
# настройки игры 
game = {
    "ice": 100,
    "co2": 10,
    "history_ice": [100],
    "history_co2": [10],
    "active": False,
    "msg_obj": None,
    "user_id": None
}


def create_visual():            # подсчет 
    ice = int(game["ice"])
    co2 = int(game["co2"])

    def bar(value):
        blocks = value // 10
        blocks = max(0, min(10, blocks))
        return "█" * blocks + "░" * (10 - blocks)        #шкала с02 и льда

    # статус
    if co2 < 30:
        status = "🟢 Stable"
    elif co2 < 70:
        status = "🟡 Warning"
    else:
        status = "🔴 Critical"

    text = (
        "🌍 CLIMATE SIMULATION\n\n"
        f"🧊 Ice: {ice}%\n"
        f"{bar(ice)}\n\n"
        f"💨 CO2: {co2}\n"
        f"{bar(co2)}\n\n"
        f"⚠️ Status: {status}"
    )            # интерфейс 

    return text

# ------------------ KEYBOARDS ------------------
def get_start_kb():
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🚀 start game", callback_data="start_game") # кнопка под соо (start)
    ]])

def get_game_kb():
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="❄️ cool ", callback_data="tap")        # кнопка под соо (охлождение)
    ]])

def get_about_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🏆 top", callback_data="top"),
            InlineKeyboardButton(text="🔑 code", callback_data="code")
        ]
    ])                                                                        # кнопка под соо (about)
# ------------------ START GAME ------------------

@dp.callback_query(lambda c: c.data == "start_game") # если нажата кнопка то он выдает начало игры и экран с следущими командами... 
async def start_game(callback: types.CallbackQuery):
    game["ice"] = 100
    game["co2"] = 10
    game["history_ice"] = [100]
    game["history_co2"] = [10]
    game["active"] = True
    game["user_id"] = callback.from_user.id

    text = create_visual()            # показывает лед баллы и т.д 

    
    game["msg_obj"] = await callback.message.answer(
        text,
        reply_markup=get_game_kb()
    )                               # отправляет соо 

    await callback.message.delete()
# ------------------ START ------------------

@dp.message(Command("start"))                # начало через команду start 
async def start(message: types.Message):

    ensure_user(message.from_user.id, message.from_user.username)         # обновляет юзера 

    game["active"] = False            # игра сейчас не запущена

    await message.answer(
        t(message.from_user.id, "start"),
        reply_markup=get_start_kb()
    )                        # риправляет соо из одной из папок на ru или en 
    
# ------------------ LANG ------------------

@dp.message(Command("lang"))            # команда через /
async def lang(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇷🇺 RU", callback_data="lang_ru"),
            InlineKeyboardButton(text="🇬🇧 EN", callback_data="lang_en")
        ]
    ])                    # кнопка под соо

    await message.answer(
        t(message.from_user.id, "lang"),
        reply_markup=kb   
    )               # отправка соо из базы ru en 

@dp.callback_query(lambda c: c.data.startswith("lang_"))        #когда нажимашь на inline кнопку 
async def set_language(callback: types.CallbackQuery):
    lang = callback.data.split("_")[1]
    set_lang(callback.from_user.id, lang)

    await callback.answer()

    key = "lang_changed" if lang == "ru" else "lang_changed_en"        # выбор текста 

    await callback.message.edit_text(
        t(callback.from_user.id, key)
    )                # язык из базы 

# ------------------ TAP ------------------

@dp.callback_query(lambda c: c.data == "tap")
async def tap(callback: types.CallbackQuery):

    if not game["active"]:
        return await callback.answer(
            t(callback.from_user.id, "need_start")
        )

    game["co2"] = max(0, game["co2"] - 12)

    ice_boost = 1
    points_boost = 1

    if callback.from_user.id in luck_users:

        data = luck_users[callback.from_user.id]

        if time.time() < data["expire"]:

            multiplier = data["multiplier"]

            ice_boost = multiplier
            points_boost = multiplier

    game["ice"] = min(100, game["ice"] + ice_boost)

    add_points(callback.from_user.id, points_boost)

    await callback.answer(
        f"❄️ +{ice_boost} ice | +{points_boost} 🧊"
    )

# ------------------ BACKGROUND ------------------

async def background():

    while True:

        if game["active"]:

            game["co2"] += 2
            game["ice"] -= game["co2"] / 18

            game["ice"] = max(0, round(game["ice"], 2))

            game["history_ice"].append(game["ice"])
            game["history_co2"].append(game["co2"])

            if game["ice"] <= 0 or game["co2"] >= 100:

                game["ice"] = 0
                game["active"] = False

                if game["msg_obj"]:

                    try:

                        lang = get_lang(game["user_id"])
                        tip = get_random_tip(lang)

                        await game["msg_obj"].edit_text(
                            f"{LANG_TEXT[lang]['lose']}\n\n"
                            f"{LANG_TEXT[lang]['eco']}\n{tip}"
                        )

                    except:
                        pass

                await asyncio.sleep(3)
                continue

            if game["msg_obj"]:

                try:

                    await game["msg_obj"].edit_text(
                        create_visual(),
                        reply_markup=get_game_kb()
                    )

                except:
                    pass

        await asyncio.sleep(3)
        
@dp.message(Command("start"))            # запуск с команды /
async def cmd_start(message: types.Message):
    game["active"] = False # Сбрасываем старую игру если была
    await message.answer(t(message.from_user.id, "start"))
    reply_markup=get_start_kb()

@dp.message(Command("code"))             # запуск с команды /
async def use_code(message: types.Message):

    args = message.text.split() # проверка все ли написал для вписания кода 

    if len(args) < 2:
        return await message.answer(
            t(message.from_user.id, "code_usage")    
        )    # впиши назв кода 

    code = args[1].upper()

    if code not in CODES:
        return await message.answer(
            t(message.from_user.id, "code_not_found")
        )   # код не найден 

    cursor.execute("""
    SELECT *
    FROM used_codes
    WHERE user_id = ?
    AND code = ?
    """, (message.from_user.id, code))   # использовал ли код?!?!?!!

    used = cursor.fetchone()

    if used:
        return await message.answer(
            t(message.from_user.id, "code_used")
)                # код использован 


    reward = CODES[code]

    add_points(message.from_user.id, reward)    # выдает награду если не использовал 

    cursor.execute("""
    INSERT INTO used_codes (user_id, code)
    VALUES (?, ?)
    """, (message.from_user.id, code))  # добавляет запись в таблицу 

    conn.commit()            # сохраняет 

    await message.answer(
        t(message.from_user.id, "code_success").format(
            reward=reward
        )
    )        # если он выдался пишет заготовленый текст в ru en 
    
@dp.message(Command("top"))             # запуск с команды /
async def top(message: types.Message):

# таблица лидеров + сам определяет где плеер больше получил льда и кидает его на место выше 
    
    cursor.execute("""
    SELECT username, points
    FROM users
    ORDER BY points DESC
    LIMIT 10
    """) # лимит таблицы 10 

    players = cursor.fetchall()

    text = "🏆 TOP\n\n"

    for i in range(10):

        if i == 0:
            place = "🥇"

        elif i == 1:
            place = "🥈"

        elif i == 2:
            place = "🥉"

        else:
            place = f"{i + 1}."
            
        if i < len(players):

            username = players[i][0]
            points = players[i][1]

            if not username:
                username = "player"

            username = username.replace("@", "")

            text += (
                f"{place} "
                f"@{username} — "
                f"{points} 🧊\n"
            ) # инфа о месте лбду и кто 

        else:
            text += f"{place} ???\n" # если нету чела то ???

    await message.answer(text)

@dp.message(Command("help"))                 # запуск с команды /
async def help(message: types.Message):
    await message.answer(t(message.from_user.id, "help"))   # показывает все команды
      
@dp.message(Command("about"))                 # запуск с команды /
async def about_cmd(message: types.Message):
    await message.answer(
        t(message.from_user.id, "about"),
        reply_markup=get_about_kb()
    )          # выдает инфу о игре (что делать тута)
       
@dp.callback_query(lambda c: c.data == "top")                #когда нажимашь на inline кнопку 
async def top_callback(callback: types.CallbackQuery):

# таблица лидеров + сам определяет где плеер больше получил льда и кидает его на место выше
    cursor.execute("""
    SELECT username, points
    FROM users
    ORDER BY points DESC
    LIMIT 10
    """)    # лимит таблицы 10 

    players = cursor.fetchall()

    text = "🏆 TOP\n\n"

    for i in range(10):

        if i == 0:
            place = "🥇"

        elif i == 1:
            place = "🥈"

        elif i == 2:
            place = "🥉"

        else:
            place = f"{i + 1}."

        if i < len(players):

            username = players[i][0]
            points = players[i][1]

            if not username:
                username = "player"

            username = username.replace("@", "")

            text += f"{place} @{username} — {points} 🧊\n"
            # инфа о месте лбду и кто 
        else:
            text += f"{place} ???\n"
            # если нету чела то ???
    
    await callback.message.answer(text)
    await callback.answer()       # срабатывает когда юзер нажимает на кнопку 

@dp.callback_query(lambda c: c.data == "code")                    #когда нажимашь на inline кнопку 
async def code_button(callback: types.CallbackQuery):

    await callback.message.answer(
    t(callback.from_user.id, "enter_code")
)   #ввод кода 

    await callback.answer()

@dp.message(Command("adminlogin"))                 # запуск с команды /
async def admin_login(message: types.Message):

    args = message.text.split()

    if len(args) < 2:
        return await message.answer(
            "/adminlogin code"
        ) # админ код 

    if args[1] != ADMIN_CODE:
        return await message.answer(
            "❌ uncorect code"
        ) # если админ код не правильный 

    admin_sessions.add(message.from_user.id)

    await message.answer(
        "🛠 admin mod revive"
    ) # если правильно написал то он запускается 


@dp.message(Command("adminexit"))                     # запуск с команды /
async def admin_exit(message: types.Message):

    if message.from_user.id in admin_sessions:
        admin_sessions.remove(message.from_user.id)

    await message.answer(
        "🚪 admin mod die"
    ) # выход из админ панели 


@dp.message(Command("admin"))                     # запуск с команды /
async def admin_panel(message: types.Message):

    if not is_admin(message.from_user.id):
        return

    # админ панель с коммандами 
    text = (
        "🛠 ADMIN PANEL\n\n"
        "/give NUMBER\n"
        "/remove NUMBER\n"
        "/cleartop CLEAR TOP\n"
        "/giveluck @username X MINUTE\n"
        "/giveluckall X MINUTE\n"
        "/adminexit EXIT\n"
        "/event text"
    )

    await message.answer(text)


@dp.message(Command("give"))             # запуск с команды /
async def give_points(message: types.Message):

    if not is_admin(message.from_user.id):
        return # если он не админ то игнор 

    args = message.text.split()

    if len(args) < 3:
        return await message.answer("/give @username NUMBER") # попровка если что то не написал 

    username = args[1]
    amount = int(args[2]) # проверка 

    user = get_user_by_username(username) # ищет в базе игроков 

    if not user:
        return await message.answer("❌ people is not found") # ненашел юзера  

    user_id = user[0]

    add_points(user_id, amount) # добавляет поинты сколько он написал 

    try:
        await bot.send_message(
    user_id,
    t(user_id, "admin_give").format(amount=amount) 
) # текст 
    except:
        pass

    await message.answer(f"➕ gived {amount} 🧊 people {username}") # текст админу и кому дал 

@dp.message(Command("remove"))                     # запуск с команды /
async def remove_points(message: types.Message):

    if not is_admin(message.from_user.id):
        return

    args = message.text.split()

    if len(args) < 3:
        return await message.answer(
            "/remove @username NUMBER"
        ) # поправка 

    username = args[1]
    amount = int(args[2])

    user = get_user_by_username(username)  # ищет в базе игроков 

    if not user:
        return await message.answer(
            "❌ people is not found"
        ) # человек не найден 

    user_id = user[0]

    cursor.execute("""
    UPDATE users
    SET points = CASE
        WHEN points - ? < 0 THEN 0
        ELSE points - ?
    END
    WHERE user_id = ?
    """, (amount, amount, user_id)) # если не хватает то будит 0 не будит уходить в -1...

    conn.commit() #сохраняет 

    try:
        await bot.send_message(
    user_id,
    t(user_id, "admin_remove").format(amount=amount)
) # текст
    except:
        pass

    await message.answer(
        f"➖ removed {amount} 🧊 from {username}"
    )  # текст админу и у кого снял 


@dp.message(Command("cleartop"))                 # запуск с команды / 
async def clear_top(message: types.Message):

    if not is_admin(message.from_user.id):
        return 

    cursor.execute("UPDATE users SET points = 0")
    conn.commit()

    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()

    for user in users:
        try:
            await bot.send_message(
                user[0],
                t(user[0], "top_cleared_global")
            ) # текст 
        except:
            pass 
        
@dp.message(Command("giveluck"))
async def give_luck(message: types.Message):

    if not is_admin(message.from_user.id):
        return

    args = message.text.split()

    if len(args) < 4:
        return await message.answer(
            "/giveluck @username X MINUTE\n"
            "example: /giveluck @bogdan 8 30"
        )

    username = args[1]
    multiplier = int(args[2])
    minutes = int(args[3])

    allowed = [2, 4, 8, 16]

    if multiplier not in allowed:
        return await message.answer(
            "❌ only 2 4 8 16"
        )

    user = get_user_by_username(username)

    if not user:
        return await message.answer(
            "❌ people is not found"
        )

    user_id = user[0]

    luck_users[user_id] = {
        "multiplier": multiplier,
        "expire": time.time() + (minutes * 60)
    }

    try:
        await bot.send_message(
            user_id,
            f"🍀 Admin gave you x{multiplier} luck for {minutes} min"
        )
    except:
        pass

    await message.answer(
        f"✅ x{multiplier} luck gived {username}\n"
        f"⏳ for {minutes} min"
    )

@dp.message(Command("giveluckall"))
async def giveluck_all(message: types.Message):

    if not is_admin(message.from_user.id):
        return

    args = message.text.split()

    if len(args) < 3:
        return await message.answer(
            "/giveluckall X MINUTE"
        )

    multiplier = int(args[1])
    minutes = int(args[2])

    allowed = [2, 4, 8, 16]

    if multiplier not in allowed:
        return await message.answer(
            "❌ only 2 4 8 16"
        )

    expire_time = time.time() + minutes * 60

    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()

    for user in users:

        user_id = user[0]

        luck_users[user_id] = {
            "multiplier": multiplier,
            "expire": expire_time
        }

        try:
            await bot.send_message(
                user_id,
                f"🍀 x{multiplier} luck for everyone!\n⏳ {minutes} min"
            )
        except:
            pass

    await message.answer(
        f"✅ x{multiplier} for everyone {minutes} min"
    )

async def delete_later(msg):
    await asyncio.sleep(6)

    try:
        await msg.delete()
    except:
        pass

@dp.message(Command("event"))
async def global_event(message: types.Message):

    if not is_admin(message.from_user.id):
        return

    text = message.text.replace("/event", "").strip()

    if not text:
        return await message.answer(
            "/event TEXT"
        )

    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()

    success = 0
    failed = 0

    for user in users:

        user_id = user[0]

        try:

            msg = await bot.send_message(
                user_id,
                f"🎉 GLOBAL EVENT\n\n{text}"
            )

            # удаление через 6 сек
            asyncio.create_task(delete_later(msg))

            success += 1

            await asyncio.sleep(0.05)

        except:

            failed += 1

    await message.answer(
        f"✅ sent: {success}\n"
        f"❌ failed: {failed}"
    )

# ------------------ RUN ------------------

async def main():                 
    asyncio.create_task(background())
    await dp.start_polling(bot)


if __name__ == "__main__":        # запуск 
    asyncio.run(main())