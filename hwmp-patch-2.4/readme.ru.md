# HWMP Patch 2.4

[English — основной README](README.md)

Самостоятельный патч Homeworld Remastered на полной основе **Players Patch 2.3Test build21**. Оригинальные четыре расы, общие исправления механик и узкие принятые изменения баланса. Это **кандидат для полевых испытаний**: нативные автотесты проверяют отдельные случаи, сетевую приёмку ещё предстоит пройти.

## Что изменилось

- Исходные гравиполя корректно освобождают пересекающиеся ограничения, в том числе после проверенных загрузок. Сохраняются прежние запреты способностей и скорость.
- Перевозка возвращает выживших пассажиров; захват сохраняет исходное разрешение самоуничтожения каждого корабля; Dock-таймеры независимы по ship ID.
- Защитный истребитель обновляет набор ракет при замене целей с прежним счётчиком. Восстановлена недостающая привязка Vaygr Medium missile weaponfire.
- Принятые изменения: **старт Hgn/Vgr 6/6 сборщиков**, последний скоростной множитель трёх пушек Assault **4 → 1,2**. Исправлены два ранее разобранных ракетных несоответствия; общего нового перебаланса нет.
- Подсказки стройки/науки показывают действительное базовое время на выбранном языке. Поддерживаются English, French, German, Italian, Spanish и Russian. Основной язык документации и CMD — английский.
- Меню: родной фон HW2 с планетой, ряд знаков хиигарян/вэйгров/таиидан, подпись HWMP 2.4 и музыка **Inhibitors**. [Подробности](https://github.com/DmitryPrigodich/hwrm-mp-patch/blob/codex/hwrm-mp-patch/docs/ru/MENU_BRANDING.md).

## Что осталось тестерам

Два реальных MP-клиента с одинаковыми архивами; стандартные/2x старты и интерфейс; видимые корпуса и ремонт отрядов; оплаченный гиперпрыжок и отмена зарядки; реальный возврат к охране; полные Hgn↔Vgr матчи со сменой сторон и карт. [Подробный список](https://github.com/DmitryPrigodich/hwrm-mp-patch/blob/codex/hwrm-mp-patch/docs/ru/CLOSURE_CHECKLIST.md).

## Сборка и запуск

```powershell
python -m pip install -r requirements.txt
python tools/prepare_inputs.py
python tools/hwmp24.py --package
python tools/install_hwmp24.py --install
```

Готовый пакет: `local/HWMPPatch24-release`. Для русского CMD-запуска: `HWMP Patch 2.4.cmd -Language Russian`. [Штатный лаунчер и обратимый переключатель слота](https://github.com/DmitryPrigodich/hwrm-mp-patch/blob/codex/hwrm-mp-patch/docs/ru/LOCAL_INSTALLATION.md). Опубликовано в [Steam Workshop](https://steamcommunity.com/sharedfiles/filedetails/?id=3827773780) как **HWMP Patch 2.4 - Field Test**. Для сетевых испытаний всем участникам нужна одна версия Workshop: хеши архивов Toolkit отличаются от локальной сборки разработчика.

Поверх полного пакета не нужен второй Players Patch. Совместимость старых сохранений с уже активными полями не гарантируется. Новые проверки загрузки не означают приёмку всех кампаний и переходов уровней.

[Порядок обновления](https://github.com/DmitryPrigodich/hwrm-mp-patch/blob/codex/hwrm-mp-patch/docs/ru/UPDATE_WORKFLOW.md) · [Устройство патча](https://github.com/DmitryPrigodich/hwrm-mp-patch/blob/codex/hwrm-mp-patch/docs/ru/PATCH_ENGINEERING.md) · [Локализация](https://github.com/DmitryPrigodich/hwrm-mp-patch/blob/codex/hwrm-mp-patch/docs/ru/LOCALIZATION.md) · [Архив полигонов](examples/native-testgrounds/README.ru.md).

Основа → новые расы → Vast Reaches. Сборка основы не обновляет потребителей автоматически. Авторы: команда Players Patch 2.3; 2.3Test — Fear/Novaras; HWMP 2.4 — AmDDRed, Hix, Twofoxich. [Полные благодарности и авторы карт](https://github.com/DmitryPrigodich/hwrm-mp-patch/blob/codex/hwrm-mp-patch/docs/ru/CREDITS.md). В Git входят код и документы; ассеты, BIG, личные журналы и сохранения остаются локально.
