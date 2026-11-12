Код-ревью · DmitryPrigodich/hwrm-mp-patch · коммит 433b4fd

# hwrm-mp-patch

HWMP Patch 2.4.5 «Cataclysm»: самостоятельный мультиплеерный патч для Homeworld Remastered на базе Players Patch 2.3 Test build 21, с исходными четырьмя расами и новым режимом Support Units.

- **571** файл в Git
- **≈12 200** строк Python в tools
- **≈21 200** строк Lua в overrides
- **131** файл Markdown
- **29** коммитов, 23–30 октября 2026

## Вердикт

Проект нормальный. По инженерной дисциплине он выше среднего для мода к игре.

Сборка воспроизводима, проверок много, установщик безопасный. Слабых мест два, и оба не про качество кода. Первое: лимит SU в Cataclysm, судя по замерам самого проекта, не ограничивает большую часть флота, а документация описывает это мягче, чем есть. Второе: процесс держится без CI, документации больше, чем кода, и читается она тяжело.

Как проверялось: код прочитан вручную. Прогнаны black (замечаний нет) и pyflakes (21 неиспользуемый импорт, 3 неиспользуемые переменные, неопределённых имён нет). Собственные проверки проекта не запускались, им нужны файлы игры. В игре ничего не проверялось.

## Что уже хорошо

- ### Архитектура патча

  Исходник Test21 закреплён по sha256: и весь `.big`, и каждый файл по инвентарю. Правки вносятся точечными текстовыми патчами с проверкой `count == 1`. Ассеты игры в Git не попадают, `.gitignore` написан тщательно.
- ### Настоящие баги апстрима

  В Lua 0 считается истиной, отсюда исправления `Player_IsAlive(i) == 1` и `SobGroup_IsDocked(...) == 0`. Ещё найдены неверная группа у `kus_cloakedfighter`, потерянная привязка weaponfire у Medium missile и дублирующийся `SuperUtilityArmour`.
- ### Владение эффектами

  Блокировки способностей и скорости считаются по владельцам, у каждой хранится исходное значение. Пересекающиеся гравиколодцы корректно отпускают друг друга. Журнал для save/load хранится в составе нативных SobGroup, формат и зарезервированные имена описаны.
- ### Осторожный установщик

  По умолчанию только показывает план. Проверяет путь и маркер владения, отказывается при посторонних файлах и ссылках. Делает бэкап со сверкой хешей, копирует через staging, следит, чтобы другие моды и защищённые архивы не изменились, и не ставит при запущенной игре.
- ### Проверки сборки

  Lua-моки через lupa с прямой оговоркой, что это не проверка движком. После упаковки все семь BIG распаковываются целиком, и хеши сверяются с исходниками.
- ### Честность

  Квитанции несут флаги `engine_tested: false`, есть отдельный Known issues, тексты не обещают непроверенного. Авторы апстрима указаны в credits и в меню.

## Что улучшить

По убыванию приоритета. Ссылки ведут на коммит 433b4fd на GitHub.

1. ### Лимит SU в Cataclysm не учитывает большую часть флота

   Высокий

   Корабль получает нативный вес, равный цене в SU, делённой на 32. В Known issues записан замер самого проекта: вес до 0.5 включительно вносит 0, а вес от 0.5 до 1 вносит целую единицу, то есть 32 SU. Значит, всё, что стоит 16 SU и дешевле, для движка бесплатно, а корабли за 17–31 SU считаются как 32.

   | Пример | Цена, SU | Вес (÷32) | Учитывается как |
   | --- | --- | --- | --- |
   | `hgn_interceptor` | 15 | 0.469 | 0 SU |
   | `hgn_marinefrigate` | 20 | 0.625 | 32 SU |
   | `hgn_destroyer` | 80 | 2.5 | копится, сумма округляется вниз |

   Платные типы кораблей по тому, как их видит движок

   Цены из `design/cataclysm.json`, порог из замеров в Known issues. Корабли с ценой 0 не показаны.

   бесплатны (≤ 16 SU) переплачивают (17–31 SU → 32) учитываются (≥ 32 SU)

   Hiigaran

   13 · 2 · 4 из 19

   Vaygr

   15 · 1 · 4 из 20

   Kushan

   24 · 2 · 4 из 30

   Taiidan

   24 · 2 · 4 из 30

   0 10 20 30

   типов

   | Раса | Бесплатны для движка | Считаются как 32 SU |
   | --- | --- | --- |
   | Hiigaran | все истребители и корветы, `hgn_assaultfrigate`, `hgn_ioncannonfrigate`, `hgn_torpedofrigate`, сборщики, контроллер, турели | `hgn_defensefieldfrigate`, `hgn_marinefrigate` |
   | Vaygr | все истребители и корветы, `vgr_assaultfrigate`, `vgr_heavymissilefrigate`, сборщики, контроллер, платформы | `vgr_infiltratorfrigate` |
   | Kushan | все истребители и корветы, Assault и Ion фрегаты, сборщики, контроллер, исследовательские корабли, сенсорный массив, генераторы невидимости и гравиполя | `kus_dronefrigate`, `kus_supportfrigate` |
   | Taiidan | то же, что у Kushan | `tai_fieldfrigate`, `tai_supportfrigate` |

   При этом `cataclysm.py` снимает обычные классовые лимиты: остаются только layout и явно перечисленные семейства. Выходит, что истребители, корветы и большинство фрегатов ограничены только ресурсами. Это вывод из данных проекта, в игре он не проверялся. Его подтверждает замер, где флот на 1885 номинальных SU дал нативное значение 2.

   Что сделать
   - Сразу: заменить в README, Known issues и описании Workshop фразу «some compositions can exceed» прямой: корабли дешевле 17 SU движок не учитывает.
   - Дешёвая страховка: оставить в Cataclysm обычные классовые лимиты как верхнюю границу.
   - Исправление: считать SU в скрипте правил и закрывать постройку через `Player_RestrictBuildOption`, которая уже вызывается в `deathmatch.lua`. Скрипт правил детерминирован в мультиплеере, а перебор ограничен содержимым очереди.

   [cataclysm.py:62–77](https://github.com/DmitryPrigodich/hwrm-mp-patch/blob/433b4fd/tools/cataclysm.py#L62-L77) [KNOWN_ISSUES.md:7](https://github.com/DmitryPrigodich/hwrm-mp-patch/blob/433b4fd/docs/KNOWN_ISSUES.md#L7) [deathmatch.lua:87](https://github.com/DmitryPrigodich/hwrm-mp-patch/blob/433b4fd/hwmp-patch-2.4/overrides/scripts/rules/deathmatch/deathmatch.lua#L87) [design/cataclysm.json](https://github.com/DmitryPrigodich/hwrm-mp-patch/blob/433b4fd/design/cataclysm.json)
2. ### Проверки и пины держатся на assert

   Средний

   В `tools` 468 `assert` против 145 `raise`. При запуске с `python -O` или с переменной `PYTHONOPTIMIZE` все `assert` вырезаются: исчезают и проверки `verify_hwmp24`, и сверка закреплённых хешей. Отчёт при этом всё равно пишет `"status": "passed"`, а установщик проверяет именно это поле. Вероятность невысокая, последствие неприятное, исправить дёшево.

   Что сделать
   - Завести хелпер `require(cond, msg)`, который бросает `RuntimeError`, и заменить им `assert` в проверках и сверке пинов.

   [hwmp24.py:236](https://github.com/DmitryPrigodich/hwrm-mp-patch/blob/433b4fd/tools/hwmp24.py#L236) [hwmp24.py:427](https://github.com/DmitryPrigodich/hwrm-mp-patch/blob/433b4fd/tools/hwmp24.py#L427) [verify_hwmp24.py:560](https://github.com/DmitryPrigodich/hwrm-mp-patch/blob/433b4fd/tools/verify_hwmp24.py#L560) [install_hwmp24.py:42](https://github.com/DmitryPrigodich/hwrm-mp-patch/blob/433b4fd/tools/install_hwmp24.py#L42)
3. ### Release и candidate переключаются через глобальные переменные

   Средний

   `RELEASE` переприсваивается в блоке `__main__` и подменяется снаружи в `native_checks.py`, а установщик импортирует обычный `RELEASE`. Каталог `WORK` общий, поэтому сборка candidate затирает квитанции обычного релиза, и установщик потом отказывает с ошибкой «verification is stale». README велит собирать с `--candidate`, а LOCAL_INSTALLATION собирает без него. Кроме того, `package()` не очищает каталог релиза, и старые файлы попадают в ZIP и SHA256SUMS. Установщик это ловит, но ZIP к тому моменту уже собран.

   Что сделать
   - Передавать каталог релиза параметром, а не через глобальную переменную.
   - Держать `WORK` отдельно для каждого релиза и очищать каталог релиза в начале сборки.
   - Свести инструкции по сборке и установке к одной.

   [hwmp24.py:596](https://github.com/DmitryPrigodich/hwrm-mp-patch/blob/433b4fd/tools/hwmp24.py#L596) [native_checks.py:13](https://github.com/DmitryPrigodich/hwrm-mp-patch/blob/433b4fd/tools/native_checks.py#L13) [install_hwmp24.py:17](https://github.com/DmitryPrigodich/hwrm-mp-patch/blob/433b4fd/tools/install_hwmp24.py#L17) [hwmp24.py:506](https://github.com/DmitryPrigodich/hwrm-mp-patch/blob/433b4fd/tools/hwmp24.py#L506)
4. ### Сгенерированные и ручные файлы лежат вместе

   Средний

   В `overrides` 225 файлов, и только 7 из них помечены как сгенерированные. Ручной `transport.lua` лежит рядом со сгенерированным `effects.lua`, и правка сгенерированного файла молча пропадёт при следующей сборке. Вдобавок `effect_journal.py` патчит строками собственные шаблоны проекта, например `block.replace("return record", ...)`.

   Что сделать
   - Добавить шапку «GENERATED, не редактировать» или вынести сгенерированное в отдельную папку.
   - Функции с журналом написать прямо в шаблоне, без строковых вставок.
   - Добавить проверку «пересобрать и `git diff --exit-code`».

   [effect_journal.py](https://github.com/DmitryPrigodich/hwrm-mp-patch/blob/433b4fd/tools/effect_journal.py) [hwmp-patch-2.4/overrides](https://github.com/DmitryPrigodich/hwrm-mp-patch/tree/433b4fd/hwmp-patch-2.4/overrides)
5. ### Нет CI

   Средний

   Полной сборке нужны файлы игры, но часть проверок без них обходится: black, pyflakes, ссылки в документации, синтаксис Lua, юнит-тесты генераторов (`patch_ship`, `equal_collector_start`, `lua_quote`) и Lua-моки для `effects_base`, который собирается только из шаблонов. Сейчас тесты написаны скриптом на `assert`: первая ошибка останавливает прогон, отчёта нет.

   Что сделать
   - Перевести проверки без ассетов на pytest и запускать их в GitHub Actions на каждый push.
6. ### Документация тяжёлая и с опечатками

   Низкий

   131 файл Markdown на двух языках, датированные копии и 33 файла-редиректа. Текст очень плотный, например «Both-mode113type checks,214runtime Lua4parses». С первого коммита между словами и числами пропадают пробелы, в том числе в публичном описании Workshop (`build21`, `Vaygr6/6`) и в README (`multiplier1.2`, `old2.4.1`). Похоже, что где-то в пайплайне текста съедаются неразрывные пробелы.

   Что сделать
   - Вернуть пробелы и добавить в `verify_documentation.py` проверку на склейку буквы с цифрой.
   - Переписать README и описание Workshop для игроков простым языком, а служебные заметки оставить в AGENTS и NEXT_SESSION.

   [description.en.bbcode:35](https://github.com/DmitryPrigodich/hwrm-mp-patch/blob/433b4fd/workshop/description.en.bbcode#L35) [README.md:18](https://github.com/DmitryPrigodich/hwrm-mp-patch/blob/433b4fd/README.md#L18)

## Мелочи

- `read_text()` без `encoding` в [hwmp24.py:238](https://github.com/DmitryPrigodich/hwrm-mp-patch/blob/433b4fd/tools/hwmp24.py#L238) и далее: на Windows файл читается в cp1252, хотя рядом везде явно указан ascii.
- Часть `.replace()` не проверяет число замен ([hwmp24.py:263–298](https://github.com/DmitryPrigodich/hwrm-mp-patch/blob/433b4fd/tools/hwmp24.py#L263-L298)). Lua-тесты покрывают это частично.
- `__import__("hashlib")` в [hwmp24.py:457](https://github.com/DmitryPrigodich/hwrm-mp-patch/blob/433b4fd/tools/hwmp24.py#L457), а `builder.ROOT` подменяется без `try/finally`.
- `HWMP_BlockGroup` для каждого корабля линейно обходит записи с двумя вызовами движка и `HWJ_Sync`, то есть O(корабли × записи) на каждый тик гравиколодца. Стоит замерить на большом скоплении истребителей.
- `examples/native-testgrounds` хранит замороженную копию 50 скриптов, 39 из них совпадают с текущими: около 9 тысяч строк дублей. Тег или отдельная ветка справились бы с этим лучше.
- Стоит упомянуть в README `git config core.longpaths true`: в длинном пути клон падает на Windows.

Ревью по коммиту 433b4fd от 30 октября 2026 года. Подготовлено 1 ноября 2026 года.