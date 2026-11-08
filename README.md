# O1-RSI

方法型 RSI：**同病「搜法中途僵死」**，解法为

> **岛间不同臂菜单（轻量策略档案）+ 岛内 UCB Bandit 混部**

相对 ORGANON（搜一段 ↔ 直接热换 provider）：日常只调臂权重；仅停滞时 Temp 换岛菜单，过门才转正。

## 快速运行

```bash
cd o1_rsi
python -m o1 run --budget 120 --seed 0 --out runs/o1_demo
python -m o1 report runs/o1_demo
python -m pytest -q
```

## 目录

```text
o1/
  loop.py       # 主环：岛内搜 + 迁移 + 菜单试用/转正
  bandit.py     # UCB1
  policies.py   # 三岛默认菜单
  mutate.py     # 臂算子（toy 向量）
  select.py     # fitness / novelty / ucb_parent
  survive.py    # top-k
  budget.py     # 分账，meta=0
  store.py      # runs/ 账本
  tasks/demo_fit.py
tests/
```

## 公民

| 层 | 对象 | 何时变 |
| --- | --- | --- |
| L1 | `IslandPolicy`（臂菜单 + select 风格） | 停滞触发 Temp 试用 → Admit/Rollback |
| L2 | `ArmStat`（每岛分立） | 每个候选后 Bandit 更新 |

程序候选是交付物，不是搜法公民。

## 主环

```text
Bootstrap 三岛不同菜单
→ 加权抽岛 → 选父 → UCB 选臂 → 变异 → 官方 public 分 → 更新臂 → survive
→ 每 T 步精英迁移（迁程序，不覆盖对方菜单）
→ 岛停滞：换备用菜单 Temp → 试用结束 Admit 或 Rollback
→ sealed 报表（不回流）
```

## 不变式

1. 分数只来自 `OfficialJudge`
2. `meta=0`（不花票现场造新 provider）
3. Bandit 调权 ≠ 搜法转正；只有 IslandPolicy 试用走编制
4. 臂统计按岛分立，不全局糊成一锅
5. tip 更新需 public 提升且 gate 不明显变差
