# Ракетное оружие: контрольные данные

Генерируется tools/audit_missiles.py --write-tables из закреплённых входов. Числа — номинальные записи оружия, не измеренный урон, DPS или размер залпа.

Основной разбор и границы расчёта — [MISSILE_AUDIT.md](MISSILE_AUDIT.md).

| Пусковая | Версия | Дальность | Интервал в .wepn | Базовый урон | Unarmoured | LightArmour |
|---|---|---:|---:|---:|---:|---:|
| vgr_heavyfusionmissilelauncher | classic | 3500 | 16 | 2700 | 2700 | 270 |
| vgr_heavyfusionmissilelauncher | remastered | 4000 | 16 | 2700 | 2700 | 2700 |
| vgr_heavyfusionmissilelauncher | pp23 | 3750 | 16 | 2700 | 2700 | 2700 |
| vgr_heavyfusionmissilelauncher | test21 | 3750 | 16 | 2700 | 27 | 270 |
| vgr_heavyfusionmissilelauncherweak | classic | 4500 | 20 | 2700 | 2700 | 2700 |
| vgr_heavyfusionmissilelauncherweak | remastered | 4500 | 20 | 2700 | 2700 | 2700 |
| vgr_heavyfusionmissilelauncherweak | pp23 | 4500 | 20 | 2700 | 2700 | 2700 |
| vgr_heavyfusionmissilelauncherweak | test21 | 4500 | 20 | 2700 | 27 | 270 |
| vgr_heavyfusionmissilelauncherbc | classic | 6000 | 30 | 5000 | 5000 | 5000 |
| vgr_heavyfusionmissilelauncherbc | remastered | 6000 | 25 | 5000 | 5000 | 5000 |
| vgr_heavyfusionmissilelauncherbc | pp23 | 5500 | 25 | 5000 | 5000 | 5000 |
| vgr_heavyfusionmissilelauncherbc | test21 | 5500 | 25 | 5000 | 50 | 500 |
| vgr_heavyfusionmissilelauncherturret | classic | 6000 | 15 | 950 | 950 | 950 |
| vgr_heavyfusionmissilelauncherturret | remastered | 6000 | 11 | 1000 | 1000 | 1000 |
| vgr_heavyfusionmissilelauncherturret | pp23 | 6000 | 15 | 950 | 950 | 950 |
| vgr_heavyfusionmissilelauncherturret | test21 | 6000 | 15 | 950 | 950 | 950 |
| vgr_heavyfusionmissilelauncherturretleft | remastered | 6000 | 11 | 1000 | 1000 | 1000 |
| vgr_heavyfusionmissilelauncherturretleft | pp23 | 6000 | 11 | 1000 | 1000 | 1000 |
| vgr_heavyfusionmissilelauncherturretleft | test21 | 5500 | 11 | 1000 | 1000 | 1000 |

Данные таблицы — исходный Test21 до наших двух правок. В HWMP правая пусковая платформы получает 5500 вместо 6000; её урон 950 и интервал 15 сохраняются. Дублированный коэффициент корвета сводится к одному 0.85.

Нулевая точность по Fighter/Corvette и таблица урона отвечают на разные вопросы. Значения в последних столбцах не доказывают возможность прямого огня по этим целям. Смысл weaponName при фактическом попадании требует движка.
