# Assault/Flak/платформы: исходные контрольные данные

Генерируется tools/audit_antistrike.py --write-tables. Показаны оригинальные входы Classic/HWRM/PP/Test; подготовленный HWMP дополнительно исправляет правую ракетную пусковую до5500.

Анализ и ограничения — [ANTISTRIKE_AUDIT.md](ANTISTRIKE_AUDIT.md).

| Корпус | Версия | RU | Базовые с | HP | Скорость | Разгон | Поворот |
|---|---|---:|---:|---:|---:|---:|---:|
| hgn_assaultfrigate | classic | 700 | 50 | 16000 | 161 | 8 | 22 |
| hgn_assaultfrigate | remastered | 700 | 50 | 18000 | 178 | 8 | 22 |
| hgn_assaultfrigate | pp23 | 700 | 50 | 18500 | 178 | 8 | 22 |
| hgn_assaultfrigate | test21 | 700 | 40 | 20000 | 210 | 4 | 45 |
| vgr_assaultfrigate | classic | 650 | 45 | 16000 | 161 | 8 | 22 |
| vgr_assaultfrigate | remastered | 650 | 45 | 17000 | 176 | 8 | 25 |
| vgr_assaultfrigate | pp23 | 650 | 45 | 18500 | 176 | 8 | 25 |
| vgr_assaultfrigate | test21 | 650 | 40 | 20000 | 210 | 4 | 45 |
| hgn_gunturret | classic | 300 | 20 | 5000 | 125 | 2.6 | 120 |
| hgn_gunturret | remastered | 300 | 20 | 5000 | 100 | 5.2 | 120 |
| hgn_gunturret | pp23 | 300 | 20 | 5000 | 125 | 5.2 | 120 |
| hgn_gunturret | test21 | 275 | 17 | 5250 | 200 | 5.2 | 120 |
| vgr_weaponplatform_gun | classic | 300 | 20 | 5000 | 125 | 2.6 | 120 |
| vgr_weaponplatform_gun | remastered | 300 | 20 | 5000 | 100 | 5.2 | 120 |
| vgr_weaponplatform_gun | pp23 | 300 | 20 | 5000 | 125 | 5.2 | 120 |
| vgr_weaponplatform_gun | test21 | 275 | 17 | 5250 | 200 | 5.2 | 120 |
| hgn_ionturret | classic | 300 | 20 | 5000 | 125 | 2.6 | 120 |
| hgn_ionturret | remastered | 300 | 20 | 5000 | 100 | 5.2 | 120 |
| hgn_ionturret | pp23 | 300 | 20 | 5000 | 125 | 5.2 | 120 |
| hgn_ionturret | test21 | 325 | 21 | 5000 | 125 | 5.2 | 120 |
| vgr_weaponplatform_missile | classic | 300 | 20 | 5000 | 125 | 2.6 | 120 |
| vgr_weaponplatform_missile | remastered | 300 | 20 | 5000 | 100 | 5.2 | 120 |
| vgr_weaponplatform_missile | pp23 | 300 | 20 | 5000 | 125 | 5.2 | 120 |
| vgr_weaponplatform_missile | test21 | 325 | 21 | 5000 | 125 | 5.2 | 120 |

## Коэффициентный индекс одиночной пушки

Индекс = средний DamageHealth × объявленный множитель брони × объявленная точность / базовый интервал. **Это не DPS корабля и не TTK:** отсутствуют дистанция, скорость, стойки, наука, геометрия, число событий и физические попадания. По Flak/лучам/очередям значение не выдумывается. Старую баллистику нельзя сравнивать с процентной моделью как прямой рост/падение DPS.

| Пушка | Версия | Hgn Interceptor | Hgn Pulsar | Vgr Missile Corvette | Hgn Torpedo Frigate |
|---|---|---:|---:|---:|---:|
| vgr_flechettecannonassaultfrigateleft | classic | 11.78 | 4.94 | 4.94 | 30.4 |
| vgr_flechettecannonassaultfrigateleft | remastered | 18 | 7.798 | 7.798 | 40 |
| vgr_flechettecannonassaultfrigateleft | pp23 | 18 | 7.798 | 7.798 | 40 |
| vgr_flechettecannonassaultfrigateleft | test21 | 12.67 | 9.5 | 9.5 | 53.83 |
| hgn_vulcankineticturretlongrange | classic | 1.28 | 1.6 | 1.6 | 8 |
| hgn_vulcankineticturretlongrange | remastered | 6.8 | 6 | 6 | 3.2 |
| hgn_vulcankineticturretlongrange | pp23 | 6.8 | 6 | 6 | 3.2 |
| hgn_vulcankineticturretlongrange | test21 | 3 | 2.5 | 2.5 | 4 |
| vgr_vulcankineticturretlongrange | classic | 1.28 | 1.6 | 1.6 | 8 |
| vgr_vulcankineticturretlongrange | remastered | 6.8 | 6 | 6 | 3.2 |
| vgr_vulcankineticturretlongrange | pp23 | 6.8 | 6 | 6 | 3.2 |
| vgr_vulcankineticturretlongrange | test21 | 3 | 2.5 | 2.5 | 4 |
