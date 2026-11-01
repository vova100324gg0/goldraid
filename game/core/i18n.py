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
    "Герой пал! Вернётся через 4 с": "The hero has fallen! Back in 4 s",
    "Герой пал от взрыва! Вернётся через 4 с": (
        "The hero fell in an explosion! Back in 4 s"
    ),
    "База под атакой!": "The base is under attack!",
    "{name} разрушена!": "{name} destroyed!",
    "Босс повержен!": "Boss defeated!",
    "Вожак повержен!": "Chief defeated!",
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
    "СЕГОДНЯ ПРОЙДЕНО": "DONE TODAY",
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
}


__all__ = ["LANGUAGES", "DEFAULT_LANGUAGE", "EN", "t", "get_language", "set_language", "language_name"]