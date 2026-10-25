# hwrm-mp-patch

**HWMP Patch 2.4 dev1** — общие исправления HWRM и оригинальные четыре расы на полном Players Patch 2.3Test build21. Слои проекта: **hwrm-mp-patch → hwrm-hw1-races-reimogined → hwvr-to-hwrm-mod**. Новые расы и кампания принадлежат потребителям; сборка основы их не обновляет.

Вход Test закреплён SHA256 `f12e17bf9c6849599afaefa4d8281c266d637cdfc992a117ec3165891cd58f41` и inventory в `baseline/`. Собственные исправления лежат в `hwmp-patch-2.4/overrides/`. Сохраняются карты, авторские сведения и благодарности Players Patch team, Fear/Novaras и участникам Test.

```powershell
python -m pip install -r requirements.txt
python tools/prepare_inputs.py
python tools/hwmp24.py --package
python tools/verify_hwmp24.py
```

`local/settings.json` или `HWRM_ASSET_CACHE` указывает на локальный кэш игры; пример — `settings.example.json`. Репозиторий содержит код и документы, без моделей, изображений, звука, BIG, кэша и личных журналов. Обычный выпуск — `local/HWMPPatch24-release`. Установка отдельно: `tools/install_hwmp24.py --install`; без флага выводится план. Сборка сама игру не запускает.

Аналитические проходы: [данные и локализация](docs/DATA_AUDIT.md), [экономика](docs/ECONOMY_AUDIT.md), [прогрессия](docs/PROGRESSION_AUDIT.md), [ракеты](docs/MISSILE_AUDIT.md), [Assault/Flak/платформы](docs/ANTISTRIKE_AUDIT.md).

**25 октября: нативная серия и принятая правка Assault.** Последний скоростной множитель трёх пушек 4→1,2 включён в подготовленную основу и проверен обычным кораблём. По чистым 10-минутным прогонам Дмитрий принял старт 6/6; он включён в подготовленную основу. **Область проекта — skirmish/MP без сохранений.** Известное зависание целей после загрузки гравиполя записано как дополнительная совместимость в самом конце очереди. Автозагрузка checkpoint работает; участие человека для очередного такого повтора не требуется. [Результаты, ограничения и рекомендации](docs/AUTO_TEST_RESULTS.md), [методика](docs/AUTO_TESTS.md). Это частичное нативное покрытие; оставшиеся автоматические и сетевые проверки перечислены в отчёте.

Отдельный `HWMPAutoTests` содержит автоматические Extra Missions; `HWMPTestGrounds` — [ручные полигоны](docs/TEST_GROUNDS.md). Обычный установленный HWMP, моды потребителей и их submodule pins этой серией не обновляются. Подробный [ручной план](docs/NATIVE_TESTS.md) сохраняется для непокрытых веток, визуальных проверок и двухклиентского MP. Скриптовые fixtures и CRC дополняют нативные журналы, но не заменяют их.

[Установка и CMD](docs/LOCAL_INSTALLATION.md), [следующий шаг](NEXT_SESSION.md). Занятый слот Vast Reaches/Banana сохранён. Workshop — после завершения патча по решению автора; публикация Workshop не выполнялась.
