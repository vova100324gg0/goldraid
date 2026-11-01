"""Локализация игры: русский — исходный язык, английский — перевод.

Строки в коде пишутся по-русски и оборачиваются в :func:`t`. Для русского
языка ``t`` возвращает строку как есть, для английского — ищет её в словаре
``EN``. Если перевода нет, показывается русский оригинал, поэтому игра
никогда не остаётся с пустыми подписями.
"""

from __future__ import annotations

# Код языка -> название на самом языке (для переключателя в настройках).
LANGUAGES = {
    "ru": "Русский",
    "en": "English",
}

DEFAULT_LANGUAGE = "ru"

_current = DEFAULT_LANGUAGE


def get_language() -> str:
    return _current


def set_language(code: str) -> str:
    """Меняет текущий язык. Неизвестный код откатывается на русский."""
    global _current
    _current = code if code in LANGUAGES else DEFAULT_LANGUAGE
    return _current


def language_name(code: str) -> str:
    return LANGUAGES.get(code, code)


def t(text: str) -> str:
    """Переводит русскую строку на текущий язык."""
    if _current == "ru":
        return text
    return EN.get(text, text)


# ---------------------------------------------------------------------------
# Английский словарь. Ключ — русская строка из кода.
# ---------------------------------------------------------------------------
EN: dict[str, str] = {
    # --- общее -----------------------------------------------------------
    "ЗОЛОТОЙ РЕЙД": "GOLDEN RAID",
    "ЗАКРЫТЬ": "CLOSE",
    "НАЗАД": "BACK",
    "ПРОДОЛЖИТЬ": "CONTINUE",
    "ЗАНОВО": "RESTART",
    "В МЕНЮ": "TO MENU",
    "ИГРАТЬ": "PLAY",
    "ЗАКРЫТО": "LOCKED",
    "ИГРАТЬ СНОВА": "PLAY AGAIN",
    "К ВЫБОРУ КАРТЫ": "MAP SELECT",
    "МАКС.": "MAX.",
    "макс.": "max",
    " з.": " g.",
    # --- постройки -------------------------------------------------------
    "Шахта": "Mine",
    "ШАХТА": "MINE",
    "Добывает золото": "Produces gold",
    "Башня": "Tower",
    "БАШНЯ": "TOWER",
    "Стреляет по врагам": "Shoots enemies",
    "Казармы": "Barracks",
    "КАЗАРМЫ": "BARRACKS",
    "Готовит бойцов": "Trains fighters",
    "Тотем": "Totem",
    "ТОТЕМ": "TOTEM",
    "Усиливает башни и бойцов рядом": "Boosts nearby towers and fighters",
    # --- улучшения -------------------------------------------------------
    "Орудие": "Weapon",
    "+7 к урону героя": "+7 hero damage",
    "Броня": "Armor",
    "+30 к здоровью героя": "+30 hero health",
    "Отряд": "Squad",
    "+1 боец в казарме": "+1 fighter in barracks",
    "Стены": "Walls",
    "+120 к прочности базы": "+120 base HP",
    # --- магазин ---------------------------------------------------------
    "Лечение героя": "Heal hero",
    "Восстановить 50% здоровья": "Restore 50% health",
    "Ремонт базы": "Repair base",
    "+180 прочности базы": "+180 base HP",
    "Боевой клич": "Battle cry",
    "+60% урона героя на 20 с": "+60% hero damage for 20 s",
    "Нанять бойца": "Hire fighter",
    "+1 боец к казармам": "+1 fighter to barracks",
    "Лимит найма исчерпан": "Hire limit reached",
    "Отряд уже полон": "Squad is full",
    "осталось {left}/{limit}": "{left}/{limit} left",
    # --- враги -----------------------------------------------------------
    "Гоблин": "Goblin",
    "Бегун": "Runner",
    "Громила": "Brute",
    "Щитоносец": "Shieldbearer",
    "Лучник": "Archer",
    "Шаман": "Shaman",
    "Бомбист": "Bomber",
    "Вожак": "Chief",
    "Алый босс": "Crimson Boss",
    # --- карты -----------------------------------------------------------
    "Обучение": "Tutorial",
    "Первые шаги защитника": "A defender's first steps",
    "Короткая тренировка: движение, золото, первая башня и первая волна.": (
        "A short drill: movement, gold, your first tower and first wave."
    ),
    "Зелёная долина": "Green Valley",
    "Три дороги к воротам": "Three roads to the gates",
    "Спокойные подступы: учись строить оборону и собирать золото.": (
        "Calm approaches: learn to build defenses and gather gold."
    ),
    "Каменный перевал": "Stone Pass",
    "Теснина и три дороги": "A gorge and three roads",
    "Враги идут по узким проходам между скал — держи башни на дороге.": (
        "Enemies march through narrow rocky passes — keep towers on the road."
    ),
    "Пепельная пустошь": "Ashen Waste",
    "Четыре дороги, орды и боссы": "Four roads, hordes and bosses",
    "Выжженная земля. Врагов много, и каждый второй отряд ведёт вожак.": (
        "Scorched land. Enemies are many, and every other squad is led by a chief."
    ),
    "Дремучий лес": "Deep Forest",
    "Четыре тропы сквозь чащу": "Four trails through the thicket",
    "Густая чаща скрывает подходы: врагов видно поздно, зато деревья теснят их строй.": (
        "The dense thicket hides approaches: enemies appear late, yet the trees cramp their ranks."
    ),
    "Студёная теснина": "Frozen Gorge",
    "Скользкие тропы меж скал": "Slippery trails among rocks",
    "Камни покрыты льдом, а дорога узкая. Враги идут волна за волной без передышки.": (
        "Rocks are ice-coated and the road is narrow. Wave after wave comes with no respite."
    ),
    "Пылающий кратер": "Burning Crater",
    "Пять дорог и бесконечные орды": "Five roads and endless hordes",
    "Раскалённая земля выжжена дотла. Пять дорог ведут к воротам, и конца ордам не видно.": (
        "The scorched land is burnt to ash. Five roads lead to the gates, and the hordes have no end."
    ),
    # --- подсказки обучения ---------------------------------------------
    "Тяни палец по полю — герой идёт за ним": (
        "Drag your finger across the field — the hero follows it"
    ),
    "Наступай на золотые монеты, чтобы собирать золото": (
        "Step on gold coins to gather gold"
    ),
    "Выбери БАШНЮ внизу и нажми на свободную площадку": (
        "Pick TOWER below and tap a free slot"
    ),
    "Кнопка ВОЛНА вызовет врагов раньше — за это дают золото": (
        "The WAVE button calls enemies early — you get gold for it"
    ),
    "Не дай врагам снести ворота — и ты готов к настоящим картам!": (
        "Don't let enemies break the gates — and you're ready for real maps!"
    ),
    # --- музыка ----------------------------------------------------------
    "Главное меню": "Main Menu",
    "Зелёные земли": "Green Lands",
    # --- HUD -------------------------------------------------------------
    "БАЗА": "BASE",
    "ЗОЛОТО": "GOLD",
    "ВОЛНА": "WAVE",
    "ГЕРОЙ": "HERO",
    "БОСС": "BOSS",
    "ПОСЛЕДНЯЯ ВОЛНА": "FINAL WAVE",
    "Строй и защищай базу": "Build and defend the base",
    "УЛУЧШ.\n+": "UPGR.\n+",
    "возрождение {n} с": "respawn {n} s",
    " · ярость {n}с": " · rage {n}s",
    "{level} · волна {wave} через {left} с · {preview}": (
        "{level} · wave {wave} in {left} s · {preview}"
    ),
    "{level} · волна {wave} · врагов: {enemies}": (
        "{level} · wave {wave} · enemies: {enemies}"
    ),
    " · база {arrow}{dist}": " · base {arrow}{dist}",
    "{name}: {hp}": "{name}: {hp}",
    "{short}\n{cost} з.": "{short}\n{cost} g.",
    "{name}: выбери свободную площадку · нажми кнопку ещё раз, чтобы отменить": (
        "{name}: pick a free slot · tap the button again to cancel"
    ),
    "ПОСТРОИТЬ": "BUILD",
    "выбери площадку и жми «Построить»": "pick a slot and tap Build",
    "{name}: выбери площадку и жми «Построить»": (
        "{name}: pick a slot and tap Build"
    ),
    "Свободных площадок нет": "No free slots left",
    "Сначала выбери постройку": "Pick a building first",
    "ВОЛНА {wave} ЧЕРЕЗ {left} С": "WAVE {wave} IN {left} S",
    "{caption}\nВЫЗВАТЬ РАНЬШЕ · +{bonus} З.": (
        "{caption}\nCALL EARLY · +{bonus} G."
    ),
    # --- меню ------------------------------------------------------------
    "ОБОРОНА · ВОЛНЫ · ЗОЛОТО": "DEFENSE · WAVES · GOLD",
    "ИГРАТЬ · ВЫБОР КАРТЫ": "PLAY · MAP SELECT",
    "ОБ АВТОРЕ": "ABOUT",
    "КАМПАНИЯ": "CAMPAIGN",
    "ЕЖЕДНЕВНАЯ": "DAILY",
    "БЕСКОНЕЧНЫЙ": "ENDLESS",
    "{n} КАРТ": "{n} MAPS",
    "НОВАЯ КАРТА ДНЯ": "NEW MAP TODAY",
    "ПРОЙДЕНА · ВОЛНА {n}": "DONE · WAVE {n}",
    "РЕКОРД: ВОЛНА {n}": "BEST: WAVE {n}",
    "БЕЗ КОНЦА ВОЛН": "WAVES NEVER STOP",
    "{done} ИЗ {total}": "{done} OF {total}",
    "СНАЧАЛА — КОРОТКОЕ ОБУЧЕНИЕ · 3 ВОЛНЫ": (
        "FIRST — A SHORT TUTORIAL · 3 WAVES"
    ),
    "ОТКРЫТО КАРТ: {unlocked} ИЗ {total}": "MAPS UNLOCKED: {unlocked} OF {total}",
    "  ·  обучение пройдено": "  ·  tutorial complete",
    "Ссылка открыта в браузере": "Link opened in the browser",
    "Ссылка скопирована в буфер": "Link copied to clipboard",
    "Не удалось открыть ссылку": "Could not open the link",
    # --- экран выбора карты ---------------------------------------------
    "ВЫБОР КАРТЫ": "MAP SELECT",
    "ОБУЧЕНИЕ · короткая карта\nдвижение · золото · первая башня": (
        "TUTORIAL · a short map\nmovement · gold · first tower"
    ),
    "ОБУЧЕНИЕ · пройдено\nможно повторить в любой момент": (
        "TUTORIAL · complete\nreplay it any time"
    ),
    "КАРТЫ": "MAPS",
    "ОТКРЫТО {unlocked} ИЗ {total}": "UNLOCKED {unlocked} OF {total}",
    "{waves} волн · {roads} дороги": "{waves} waves · {roads} roads",
    "пройди предыдущую": "clear the previous one",
    "лучшая {best}/{total}": "best {best}/{total}",
    "ещё не пройдена": "not cleared yet",
    "открыто": "open",
    "закрыто": "closed",
    "{name}\n{waves} волн · {state}": "{name}\n{waves} waves · {state}",
    # --- окно «Об авторе» -----------------------------------------------
    "версия {version} · {title}": "version {version} · {title}",
    "Защищай ворота: собирай золото, строй башни, шахты, казармы и тотемы, отбивай волны врагов.": (
        "Defend the gates: gather gold, build towers, mines, barracks and totems, repel enemy waves."
    ),
    "Автор: {author}": "Author: {author}",
    "© 2026 elsty. Все права защищены.\nПроприетарная лицензия: копирование, изменение\nи распространение игры запрещены.": (
        "© 2026 elsty. All rights reserved.\nProprietary license: copying, modifying\nand distributing the game is prohibited."
    ),
    "Тяни палец по полю — герой идёт за ним.\nСобирай золото и строй обороны вокруг базы.": (
        "Drag your finger across the field — the hero follows it.\nGather gold and build defenses around the base."
    ),
    # --- пауза / улучшения / магазин / постройка -------------------------
    "ПАУЗА": "PAUSED",
    "УЛУЧШЕНИЯ": "UPGRADES",
    "Золото: {gold}": "Gold: {gold}",
    "{name}  ур. {level}/{max}\n{desc} · {price}": (
        "{name}  lvl {level}/{max}\n{desc} · {price}"
    ),
    "{cost} з.": "{cost} g.",
    "МАГАЗИН": "SHOP",
    "{name} · {cost} з.\n{desc}": "{name} · {cost} g.\n{desc}",
    "{name} · ур. {level}": "{name} · lvl {level}",
    "Прочность {hp} / {max}": "Durability {hp} / {max}",
    "Максимальный уровень": "Maximum level",
    "УЛУЧШИТЬ": "UPGRADE",
    "УЛУЧШИТЬ · {cost} з.": "UPGRADE · {cost} g.",
    "ПРОДАТЬ": "SELL",
    "ПРОДАТЬ · +{refund} з.": "SELL · +{refund} g.",
    # --- финал боя -------------------------------------------------------
    "БАЗА ВЫСТОЯЛА!": "BASE HELD!",
    "БАЗА ПАЛА": "BASE FALLEN",
    "ЗВЁЗДЫ: {stars} / 3": "STARS: {stars} / 3",
    "Открыта новая карта: {name}!": "New map unlocked: {name}!",
    "Отбито волн: {waves} / {total}\nДобыто золота: {gold} · Побед: {kills}\nПостроек осталось: {buildings}": (
        "Waves repelled: {waves} / {total}\nGold earned: {gold} · Victories: {kills}\nBuildings left: {buildings}"
    ),
    "Новая оборона началась": "A new defense has begun",
    "ОБУЧЕНИЕ ПРОЙДЕНО!": "TUTORIAL COMPLETE!",
    "Дальше — первая настоящая карта": "Next — your first real map",
    "НАЧАТЬ ДОЛИНУ": "START THE VALLEY",
    "ПОПРОБУЙ ЕЩЁ": "TRY AGAIN",
    "ПОВТОРИТЬ ОБУЧЕНИЕ": "REPLAY TUTORIAL",
    "{name}: нажми на свободную площадку": "{name}: tap a free slot",
    "{name}: {desc}": "{name}: {desc}",
    # --- тосты арены -----------------------------------------------------
    "Неизвестная постройка": "Unknown building",
    "Неверная площадка": "Invalid slot",
    "Площадка занята": "Slot is occupied",
    "Не хватает золота": "Not enough gold",
    "{name} построена": "{name} built",
    "{name} улучшена до ур. {level}": "{name} upgraded to lvl {level}",
    "Постройка разрушена": "Building destroyed",
    "Неизвестное улучшение": "Unknown upgrade",
    "{name} улучшен": "{name} upgraded",
    "Скорость боя x{n}": "Battle speed x{n}",
    "Бой уже окончен": "Battle is already over",
    "Волна уже идёт": "A wave is already underway",
    "Волна {wave} началась · +{bonus} золота": "Wave {wave} started · +{bonus} gold",
    "Постройка уже разрушена": "Building is already destroyed",
    "Неизвестный товар": "Unknown item",
    "Куплено: {name}": "Purchased: {name}",
    "Выбери постройку на нижней панели": "Pick a building on the bottom panel",
    "+{amount} золота": "+{amount} gold",
    "Герой вернулся в бой": "The hero is back in the fight",
    "Герой пал! Вернётся через {n} с": "The hero has fallen! Back in {n} s",
    "Герой пал от взрыва! Вернётся через {n} с": (
        "The hero fell in an explosion! Back in {n} s"
    ),
    "База под атакой!": "The base is under attack!",
    "{name} разрушена!": "{name} destroyed!",
    "Босс повержен!": "Boss defeated!",
    "Вожак повержен!": "Chief defeated!",
    "Тёмный владыка повержен!": "The Dark Warlord is defeated!",
    "АЛЫЙ БОСС ВЕДЁТ АРМИЮ!": "THE CRIMSON BOSS LEADS THE ARMY!",
    "Вожак ведёт отряд!": "A chief leads the squad!",
    "Волна {wave} отбита! +{bonus} золота": "Wave {wave} repelled! +{bonus} gold",
    "{name} продана · +{refund} золота": "{name} sold · +{refund} gold",
    "ВОЛНА {wave} · врагов: {count}": "WAVE {wave} · enemies: {count}",
    "ВОЛНА {wave} · БОСС И {count} ВРАГОВ": (
        "WAVE {wave} · BOSS AND {count} ENEMIES"
    ),
    "ВОЛНА {wave} · ВОЖАК И {count} ВРАГОВ": (
        "WAVE {wave} · CHIEF AND {count} ENEMIES"
    ),
    " · +{bonus} золота": " · +{bonus} gold",
    # --- подсказки состава волны ----------------------------------------
    "{count} врагов{extra}": "{count} enemies{extra}",
    " · {labels}": " · {labels}",
    "босс": "boss",
    "вожак": "chief",
    "шаманы": "shamans",
    "лучники": "archers",
    # --- арена: детали построек -----------------------------------------
    "{income} золота каждые {period} с": "{income} gold every {period} s",
    "далее: {income} за {period} с": "next: {income} per {period} s",
    "Урон {damage} · дальность {range}": "Damage {damage} · range {range}",
    "далее: урон {damage}, дальность {range}": (
        "next: damage {damage}, range {range}"
    ),
    "+{boost}% урона в радиусе {aura}": "+{boost}% damage within {aura}",
    "далее: +{boost}% в радиусе {aura}": "next: +{boost}% within {aura}",
    "Бойцов {squad} · урон {damage}": "Fighters {squad} · damage {damage}",
    "далее: {squad} бойцов, урон {damage}": (
        "next: {squad} fighters, damage {damage}"
    ),
    "Герой возрождается": "The hero is respawning",
    "Герой полон сил": "The hero is at full health",
    "База не повреждена": "The base is undamaged",
    "Сначала построй казармы": "Build barracks first",
    # --- настройки -------------------------------------------------------
    "НАСТРОЙКИ": "SETTINGS",
    "ЯЗЫК": "LANGUAGE",
    "МУЗЫКА": "MUSIC",
    "КАЧЕСТВО ГРАФИКИ": "GRAPHICS QUALITY",
    "РУССКИЙ": "RUSSIAN",
    "АНГЛИЙСКИЙ": "ENGLISH",
    "ВКЛ": "ON",
    "ВЫКЛ": "OFF",
    "АВТО": "AUTO",
    "ВЫСОКОЕ": "HIGH",
    "НИЗКОЕ": "LOW",
    "СБРОСИТЬ ПРОГРЕСС": "RESET PROGRESS",
    "ТОЧНО СБРОСИТЬ?": "RESET EVERYTHING?",
    "Прогресс сброшен": "Progress reset",
    "ЧТО НОВОГО": "WHAT'S NEW",
    "Настройки": "Settings",
    # --- достижения ------------------------------------------------------
    "ДОСТИЖЕНИЯ": "ACHIEVEMENTS",
    "Первые шаги": "First Steps",
    "Пройди обучение": "Complete the tutorial",
    "Защитник ворот": "Gate Defender",
    "Выиграй первую карту": "Win your first map",
    "Безупречная оборона": "Flawless Defense",
    "Получи 3 звезды на любой карте": "Earn 3 stars on any map",
    "Убийца боссов": "Boss Slayer",
    "Победи босса": "Defeat a boss",
    "Строитель": "Builder",
    "Построй 50 построек за всё время": "Build 50 structures in total",
    "Золотая жила": "Gold Mine",
    "Добудь 5000 золота за всё время": "Earn 5000 gold in total",
    "Стойкий защитник": "Steadfast Defender",
    "Отбей 100 волн": "Repel 100 waves",
    "Покоритель карт": "Map Conqueror",
    "Пройди все карты": "Clear every map",
    "Достижения: {names}": "Achievements: {names}",
    # --- что нового ------------------------------------------------------
    "ЧТО НОВОГО · {version}": "WHAT'S NEW · {version}",
    "• Русский и английский языки — переключаются в настройках": (
        "• Russian and English languages — switch them in Settings"
    ),
    "• Новый экран настроек: язык, музыка, качество графики": (
        "• New Settings screen: language, music, graphics quality"
    ),
    "• Достижения: 8 наград за победы, боссов и стройку": (
        "• Achievements: 8 rewards for wins, bosses and building"
    ),
    "• Раздел «Что нового» — история изменений": (
        "• What's New section — the changelog"
    ),
    "• Версионирование сохранений: старый прогресс не потеряется": (
        "• Save versioning: your old progress is preserved"
    ),
    "• Сброс прогресса с подтверждением": (
        "• Progress reset with confirmation"
    ),
    "• Мелкие исправления интерфейса": "• Minor interface fixes",
    # --- режимы 1.4.0 ----------------------------------------------------
    "ИГРАТЬ · КАРТЫ И РЕЖИМЫ": "PLAY · MAPS & MODES",
    "РЕЖИМЫ": "MODES",
    "БЕСКОНЕЧНЫЙ РЕЖИМ": "ENDLESS MODE",
    "БЕСКОНЕЧНЫЙ РЕЖИМ\nбез конца волн": "ENDLESS MODE\nwaves never stop",
    "БЕСКОНЕЧНЫЙ РЕЖИМ\nрекорд: волна {n}": "ENDLESS MODE\nbest: wave {n}",
    "ЕЖЕДНЕВНАЯ КАРТА": "DAILY MAP",
    "ЕЖЕДНЕВНАЯ КАРТА\nновая карта дня": "DAILY MAP\nnew map today",
    "ЕЖЕДНЕВНАЯ КАРТА\nпройдена · волна {n}": "DAILY MAP\ndone · wave {n}",
    "Бесконечный режим: держись как можно дольше": (
        "Endless mode: hold out as long as you can"
    ),
    "Ежедневная карта: {name}": "Daily map: {name}",
    "БЕСКОНЕЧНЫЙ РЕЖИМ · ВОЛНА {n}": "ENDLESS MODE · WAVE {n}",
    "ЕЖЕДНЕВНАЯ КАРТА · ВОЛНА {n}": "DAILY MAP · WAVE {n}",
    "ЕЩЁ РАЗ": "AGAIN",
    "ПОПЫТКА ИСПОЛЬЗОВАНА": "ATTEMPT USED",
    "Новый рекорд!": "New record!",
    "Лучший результат: волна {n}": "Best result: wave {n}",
    "Возвращайся завтра за новой картой": (
        "Come back tomorrow for a new map"
    ),
    "Отбито волн: {waves}\n"
    "Добыто золота: {gold} · Побед: {kills}\n"
    "Построек осталось: {buildings}": (
        "Waves repelled: {waves}\n"
        "Gold earned: {gold} · Victories: {kills}\n"
        "Buildings left: {buildings}"
    ),
    # --- звуки -----------------------------------------------------------
    "ЗВУКИ": "SOUND",
    # --- что нового 1.4.0 ------------------------------------------------
    "• Бесконечный режим: волны без конца и рекорд": (
        "• Endless mode: waves never stop, chase the record"
    ),
    "• Ежедневная карта: новая карта каждый день": (
        "• Daily map: a fresh map every day"
    ),
    "• Звуковые эффекты и переключатель «Звуки»": (
        "• Sound effects and a Sound toggle"
    ),
    "• Отдельные рекорды режимов": "• Separate records for each mode",
    # --- контент 1.5.0 ---------------------------------------------------
    "Забытые руины": "Forgotten Ruins",
    "Четыре дороги сквозь камни": "Four roads through the stone",
    "Древние стены рассыпались, но дороги остались. Здесь много золота и очень много врагов.": (
        "The ancient walls have crumbled, but the roads remain. "
        "Plenty of gold and even more enemies."
    ),
    "Тёмная цитадель": "Dark Citadel",
    "Пять дорог во тьме": "Five roads in the dark",
    "Последний рубеж. Пять дорог, бесконечные орды и Тёмный владыка у самых ворот.": (
        "The last stand. Five roads, endless hordes, "
        "and the Dark Warlord at the gates."
    ),
    "Берсерк": "Berserker",
    "Голем": "Golem",
    "Некромант": "Necromancer",
    "Тёмный владыка": "Dark Warlord",
    "владыка": "warlord",
    "големы": "golems",
    "некроманты": "necromancers",
    "берсерки": "berserkers",
    "ТЁМНЫЙ ВЛАДЫКА ПРОБУДИЛСЯ!": "THE DARK WARLORD AWAKENS!",
    "ВОЛНА {wave} · ВЛАДЫКА И {count} ВРАГОВ": (
        "WAVE {wave} · WARLORD AND {count} ENEMIES"
    ),
    "Пепельный след": "Ashen Trail",
    "Пройди «Забытые руины»": "Clear the Forgotten Ruins",
    "Владыка пепла": "Lord of Ashes",
    "Пройди «Тёмную цитадель»": "Clear the Dark Citadel",
    "Несокрушимый": "Unbreakable",
    "Дойди до 25-й волны в бесконечном режиме": (
        "Reach wave 25 in endless mode"
    ),
    "Истребитель": "Destroyer",
    "Уничтожь 1000 врагов за всё время": "Destroy 1000 enemies in total",
    "• Две новые карты: «Забытые руины» и «Тёмная цитадель»": (
        "• Two new maps: Forgotten Ruins and Dark Citadel"
    ),
    "• Новые враги: берсерк, голем и некромант": (
        "• New enemies: berserker, golem and necromancer"
    ),
    "• Тёмный владыка — финальный босс цитадели": (
        "• The Dark Warlord — the Citadel's final boss"
    ),
    "• Четыре новых достижения": "• Four new achievements",
    "• Крупные золотые жилы на новых картах": (
        "• Rich gold veins on the new maps"
    ),
    "• Новый шрифт кнопок и обновлённое меню": (
        "• A new button font and a refreshed menu"
    ),
    # --- рекорды и достижения 1.6.0 --------------------------------------
    "РЕКОРДЫ": "RECORDS",
    "Лучшая волна (бесконечный): {n}": "Best wave (endless): {n}",
    "Золото за один бой: {n}": "Gold in one run: {n}",
    "Убийств за один бой: {n}": "Kills in one run: {n}",
    "Самая быстрая победа: {v}": "Fastest victory: {v}",
    "Всего золота: {n}": "Total gold: {n}",
    "Всего убийств: {n}": "Total kills: {n}",
    "Отбито волн: {n}": "Waves repelled: {n}",
    "Карт пройдено: {done} из {total}": "Maps cleared: {done} of {total}",
    "Звёзд собрано: {n}": "Stars earned: {n}",
    "  ·  НОВЫХ: {n}": "  ·  NEW: {n}",
    "Золотой поток": "Golden Flow",
    "Заработай 800 золота за один бой": "Earn 800 gold in a single run",
    "Постоянство": "Consistency",
    "Открывай ежедневную карту 3 дня подряд": "Play the daily map 3 days in a row",
    "Молниеносный": "Lightning Fast",
    "Пройди любую карту быстрее 4 минут": "Clear any map in under 4 minutes",
    # --- боевые удобства 1.6.0 -------------------------------------------
    "Герой бьёт ближайшего врага сам — подведи его ближе": (
        "The hero strikes the nearest enemy — just get him close"
    ),
    "Бой на паузе, пока окно не в фокусе": (
        "The battle pauses while the window is unfocused"
    ),
    # --- что нового 1.6.0 ------------------------------------------------
    "• Обновлённое меню-витрина с крупными карточками режимов": (
        "• A refreshed showcase menu with large mode cards"
    ),
    "• Понятная боёвка героя: замах меча, метка цели и цифры урона": (
        "• Clearer hero combat: sword swings, target marker and damage numbers"
    ),
    "• Герой больше не проходит сквозь постройки и замок": (
        "• The hero no longer walks through buildings and the castle"
    ),
    "• Кнопка «Ещё раз» после боя и автопауза при сворачивании": (
        "• A Play Again button after battle and auto-pause when minimized"
    ),
    "• Экран рекордов: волны, золото, убийства и время": (
        "• Records screen: waves, gold, kills and time"
    ),
    "• Три новых достижения и значок «новое» в меню": (
        "• Three new achievements and a New badge in the menu"
    ),
    # --- сюжет кампании 1.7.0 --------------------------------------------
    "ПРОПУСТИТЬ": "SKIP",
    "ДАЛЕЕ": "NEXT",
    "ПОНЯТНО": "GOT IT",
    "Рассказчик": "Narrator",
    "ВСТУПЛЕНИЕ": "PROLOGUE",
    "СЮЖЕТ · вступление и путь героя": "STORY · prologue and the hero's path",
    "Рейн": "Rayn",
    "Старейшина": "Elder",
    "Мира": "Mira",
    "Гракх": "Grakh",
    "Владыка Мор": "Warlord Mor",
    # --- вступление ------------------------------------------------------
    "Векá золото лежало под зелёными холмами, и векá никто не тревожил эти земли.": (
        "For ages gold lay beneath the green hills, and for ages no one troubled these lands."
    ),
    "Рейн, беда. Гоблины сбиваются в орды у самых границ. Они идут за нашим золотом.": (
        "Rayn, trouble. Goblins are gathering into hordes at our very borders. They come for our gold."
    ),
    "Значит, будем держать ворота. Я не отдам им ни одной монеты.": (
        "Then we'll hold the gates. I won't give them a single coin."
    ),
    "И это ещё не всё. Я видела знамёна Тёмного владыки. Он пробуждается на востоке.": (
        "And that's not all. I've seen the Dark Warlord's banners. He is awakening in the east."
    ),
    "Тогда слушай. Восемь рубежей отделяют нас от его цитадели. Пройди их все.": (
        "Then listen. Eight frontiers stand between us and his citadel. Cross them all."
    ),
    "Начнём с долины. Строй башни, собирай золото — и не пускай врагов к воротам.": (
        "We start with the valley. Build towers, gather gold — and keep the enemies from the gates."
    ),
    "Сколько их там, за холмами?": (
        "How many are there, beyond the hills?"
    ),
    "Сотни. Может, больше. Но дороги узкие — по одной орде за раз.": (
        "Hundreds. Maybe more. But the roads are narrow — one horde at a time."
    ),
    "И запомни: золото — не награда, а топливо. Без него не будет ни стен, ни башен.": (
        "And remember: gold isn't a reward, it's fuel. Without it there are no walls and no towers."
    ),
    # --- брифинги карт ---------------------------------------------------
    "Зелёная долина — спокойные подступы. Три дороги ведут к воротам.": (
        "Green Valley — calm approaches. Three roads lead to the gates."
    ),
    "Первые отряды гоблинов уже близко. Учись ставить башни вдоль дорог.": (
        "The first goblin squads are near. Learn to place towers along the roads."
    ),
    "Понял. Здесь я и построю первую линию обороны.": (
        "Understood. This is where I'll build the first line of defense."
    ),
    "Не гонись за каждой монетой. Сначала стены, потом богатство.": (
        "Don't chase every coin. Walls first, wealth later."
    ),
    "Каменный перевал. Узкие проходы меж скал — врагам негде развернуться.": (
        "Stone Pass. Narrow gaps between the cliffs — no room for the enemy to spread out."
    ),
    "Держи башни на самих дорогах: в теснине каждый выстрел бьёт в цель.": (
        "Keep towers right on the roads: in the gorge every shot hits home."
    ),
    "Теснина станет им могилой.": "The gorge will be their grave.",
    "Только не запрись в ней сам. Оставь себе путь к отходу.": (
        "Just don't trap yourself in it. Keep yourself a way out."
    ),
    "Выжженная пустошь дышит жаром. Четыре дороги — и по каждой идёт орда.": (
        "The scorched waste breathes heat. Four roads — and a horde on each."
    ),
    "Здесь много вожаков. Гоблины идут злыми и упорными.": (
        "There are many chiefs here. The goblins come vicious and stubborn."
    ),
    "Пусть идут. Чем больше врагов — тем больше золота.": (
        "Let them come. The more enemies — the more gold."
    ),
    "Береги бойцов. В пустоши они дороже золота.": (
        "Take care of your fighters. In the waste they're worth more than gold."
    ),
    "Дремучий лес. Чаща скрывает подходы — врагов увидишь поздно.": (
        "Deep Forest. The thicket hides the approaches — you'll see enemies late."
    ),
    "Зато деревья теснят их строй. Ставь башни на тропах и держи бойцов наготове.": (
        "But the trees cramp their ranks. Place towers on the trails and keep fighters ready."
    ),
    "Проберёмся сквозь чащу.": "We'll make it through the thicket.",
    "В лесу тишина обманчива. Если птицы замолчали — жди беды.": (
        "In the forest, silence is deceptive. If the birds go quiet — expect trouble."
    ),
    "Студёная теснина. Камни покрыты льдом, дорога узкая, а враги не дают передышки.": (
        "Frozen Gorge. Stones are ice-coated, the road is narrow, and enemies give no respite."
    ),
    "Волна за волной, без остановки. Не успеешь собрать золото — останешься без обороны.": (
        "Wave after wave, without pause. Fail to gather gold — and you're left without defenses."
    ),
    "Холод им не помеха, но крепкие стены — помеха.": (
        "Cold doesn't stop them, but solid walls do."
    ),
    "На льду враги скользят. Бей, пока они не встали ровно.": (
        "Enemies slip on the ice. Strike before they steady themselves."
    ),
    "Пылающий кратер. Пять дорог, раскалённая земля и бесконечные орды.": (
        "Burning Crater. Five roads, scorched land and endless hordes."
    ),
    "Здесь погибла не одна оборона. Держись: конец пути уже близок.": (
        "More than one defense has fallen here. Hold on: the end of the road is near."
    ),
    "Я выстою. Ради каждого, кто остался дома.": (
        "I will hold. For everyone who stayed home."
    ),
    "Пять дорог — и ни одного безопасного отхода. Держи центр, Рейн.": (
        "Five roads — and not one safe retreat. Hold the center, Rayn."
    ),
    "Забытые руины. Древние стены рассыпались, но дороги и золото остались.": (
        "Forgotten Ruins. The ancient walls have crumbled, but roads and gold remain."
    ),
    "Здесь золота больше, чем где-либо. И врагов — тоже.": (
        "There's more gold here than anywhere. And more enemies, too."
    ),
    "Соберу всё до последней монеты.": "I'll gather every last coin.",
    "Древние строили эти стены не от гоблинов. Но и они пали.": (
        "The ancients didn't build these walls against goblins. Yet they fell too."
    ),
    "Тёмная цитадель. Небо затянуто гарью, и сам владыка ждёт у ворот.": (
        "Dark Citadel. The sky is choked with soot, and the Warlord himself waits at the gates."
    ),
    "Смертный, ты зашёл слишком далеко. Здесь твоя оборона и закончится.": (
        "Mortal, you have come too far. This is where your defense ends."
    ),
    "Нет. Здесь закончится твоё владычество.": (
        "No. This is where your reign ends."
    ),
    "Рейн, на последней волне придёт он сам. Не дрогни.": (
        "Rayn, he will come himself on the final wave. Do not waver."
    ),
    "Войска владыки уже в воротах. Отступать некуда — и не нужно.": (
        "The Warlord's troops are already at the gates. No retreat — and none needed."
    ),
    # --- эпилоги ---------------------------------------------------------
    "Долина свободна. Гоблины отступили к перевалу.": (
        "The valley is free. The goblins have fallen back to the pass."
    ),
    "Идём дальше. Каждая монета — ещё один камень в нашей стене.": (
        "Onward. Every coin is another stone in our wall."
    ),
    "По дорогам уже идут первые обозы. Люди поверили, что мы удержимся.": (
        "The first supply carts are already on the roads. People believe we can hold."
    ),
    "Перевал наш. Теснина приняла врагов, но не пропустила.": (
        "The pass is ours. The gorge took the enemies but let none through."
    ),
    "Один рубеж позади. Впереди — выжженная пустошь.": (
        "One frontier behind us. Ahead lies the scorched waste."
    ),
    "Пустошь очищена. Пепел врагов развеял ветер.": (
        "The waste is cleared. The wind scattered the enemies' ashes."
    ),
    "Здесь не растёт ничего, но золото лежит даже под пеплом.": (
        "Nothing grows here, but gold lies even under the ash."
    ),
    "Лес снова молчит. Чаща нам помогла.": (
        "The forest is silent again. The thicket helped us."
    ),
    "Птицы вернулись. Значит, можно идти дальше.": (
        "The birds have returned. That means we can move on."
    ),
    "Студёная теснина выстояла. Даже холод не остановил тебя.": (
        "The Frozen Gorge held. Even the cold didn't stop you."
    ),
    "Половина пути позади. Дыши глубже — впереди жар кратера.": (
        "Half the road is behind us. Breathe deep — the heat of the crater lies ahead."
    ),
    "Кратер затих. Раскалённая земля впервые остывает.": (
        "The crater has gone quiet. The scorched land cools for the first time."
    ),
    "Слишком близко к цитадели. Дальше будет тяжелее.": (
        "Too close to the citadel. It only gets harder from here."
    ),
    "Передохни, Рейн. За кратером начинаются древние руины.": (
        "Rest a while, Rayn. Beyond the crater the ancient ruins begin."
    ),
    "Руины снова молчат. Дороги наши, и золото — тоже.": (
        "The ruins are silent again. The roads are ours, and the gold too."
    ),
    "Древние не смогли удержаться. Ты смог. Впереди — последний рубеж.": (
        "The ancients couldn't hold. You did. Ahead lies the final frontier."
    ),
    "Тёмный владыка пал. Небо над цитаделью впервые за годы очистилось.": (
        "The Dark Warlord has fallen. The sky above the citadel clears for the first time in years."
    ),
    "Мы выстояли.": "We held.",
    "Ворота открыты. Города ждут своего героя.": (
        "The gates are open. The cities await their hero."
    ),
    # --- развязка --------------------------------------------------------
    "Рейн, вся земля говорит о тебе. Восемь рубежей — и ни одного промаха.": (
        "Rayn, the whole land speaks of you. Eight frontiers — and not a single miss."
    ),
    "Золотые жилы снова наши. Люди возвращаются в родные дома.": (
        "The gold veins are ours again. People are returning to their homes."
    ),
    "Это не конец. Пусть только попробуют прийти снова — ворота выстоят.": (
        "This isn't the end. Let them try to come again — the gates will hold."
    ),
    "Ты не просто защитил золото. Ты вернул нам надежду.": (
        "You didn't just defend the gold. You gave us back our hope."
    ),
    "Кампания пройдена. Теперь ты — легенда Золотого рейда.": (
        "Campaign complete. Now you are a legend of the Golden Raid."
    ),
    # --- что нового 1.7.0 ------------------------------------------------
    "• Сюжет в кампании: вступление, брифинги и финалы карт": (
        "• A campaign story: prologue, briefings and map finales"
    ),
    "• Атмосферные катсцены с портретами героев и врагов": (
        "• Atmospheric cutscenes with hero and enemy portraits"
    ),
    "• Аккуратная граница карты — декор больше не выходит за край": (
        "• A neat map border — decor no longer spills over the edge"
    ),
    "• Интерфейс не растягивается на широком экране ПК": (
        "• The interface no longer stretches on a wide PC screen"
    ),
    "• С экрана «КАМПАНИЯ» убраны дублирующие режимы": (
        "• Duplicate modes removed from the Campaign screen"
    ),
    "• Исправлен номер карты в медальоне": (
        "• Fixed the map number inside the medallion"
    ),
    # --- что нового 1.9.0 ------------------------------------------------
    "• Бой при больших ордах стал заметно быстрее": (
        "• Battle with large hordes is noticeably faster"
    ),
    "• Сюжет вырос: новые реплики в брифингах, эпилогах и развязке": (
        "• More story: new lines in briefings, epilogues and the finale"
    ),
    "• Починен доход золота — раньше он рос вдвое быстрее задуманного": (
        "• Gold income fixed — it used to grow twice as fast as intended"
    ),
    "• Богатые жилы больше не мешают появляться обычным кучкам золота": (
        "• Rich veins no longer stop normal gold piles from appearing"
    ),
    "• Обучение не засчитывается как настоящая победа и не пишет рекорды": (
        "• The tutorial no longer counts as a real win and writes no records"
    ),
    "• Серия ежедневной карты считает подряд сыгранные дни": (
        "• The daily streak now counts consecutive days played"
    ),
    "• Кнопка вызова волны не налезает на панель стройки на телефоне": (
        "• The wave-call button no longer overlaps the build bar on phones"
    ),
    "• Горячие клавиши не срабатывают под открытыми окнами боя": (
        "• Hotkeys no longer fire while battle windows are open"
    ),
    "• Бойцы из казармы на дальних площадках снова реагируют на врагов": (
        "• Barracks fighters on distant slots now engage nearby enemies"
    ),
    # --- что нового 1.8.0 ------------------------------------------------
    "• Постройки качаются до 5 уровня — поздние волны больше не стена": (
        "• Buildings upgrade to level 5 — late waves are no longer a wall"
    ),
    "• Больше общих улучшений: оружие, броня и стены": (
        "• More global upgrades: weapon, armor and walls"
    ),
    "• Урон врагов после 15-й волны растёт мягче": (
        "• Enemy damage grows more gently after wave 15"
    ),
    "• Баланс-патч: Кратер, Руины и Цитадель мягче, финальные волны — по силам": (
        "• Balance patch: Crater, Ruins and Citadel eased, final waves are fair"
    ),
    "• Первые карты стали чуть сложнее — интереснее с самого начала": (
        "• Early maps are slightly harder — more engaging from the start"
    ),
    "• Руины: дороги стали извилистее — башни дольше держат врагов под огнём": (
        "• Ruins: winding roads keep enemies under tower fire longer"
    ),
    "• Наём бойцов ограничен шестью за бой — остаток виден на кнопке": (
        "• Hiring is capped at six per battle — the remainder is shown on the button"
    ),
    "• Портреты героев в катсценах: Рейн, Старейшина, Мира, Гракх и Владыка Мор": (
        "• Hero portraits in cutscenes: Rein, the Elder, Mira, Grakh and Lord Mor"
    ),
    "• Оптимизация боя: орды врагов и отряды не тормозят кадр": (
        "• Combat optimization: enemy hordes and squads no longer drop frames"
    ),
}


__all__ = ["LANGUAGES", "DEFAULT_LANGUAGE", "EN", "t", "get_language", "set_language", "language_name"]