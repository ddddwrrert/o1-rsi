# O1 · 框架六件套

**半句命题：** Plugin 装配 harness；ORGANON 热换裸 provider；**O1 用多岛不同臂菜单抗搜法单文化，用岛内 Bandit 解配比僵死——日常调权，停滞才试用换菜单。**

**病（切口）：** 搜法中途僵死（与 ORGANON 同病，解法不同）。

| 件 | O1 |
| --- | --- |
| 切口 | 搜法中途僵死 / 单套 composition 单文化 |
| 公民 | L1 `IslandPolicy`；L2 每岛 `ArmStat` |
| 运行体 | 多岛搜索运行时（非 Arena、非裸单 loop） |
| 主环 | 抽岛→选父→UCB臂→变异→记账→迁移；停滞→Temp菜单→Admit/Rollback |
| 累积 | 岛种群 + 臂统计 + 策略版本谱系 + tip |
| 冻面 | 官方 \(V\)；总 \(B\)；`evaluate` 语义；`meta=0`；sealed 不回流 |

**防假阴性：** tip 连续 public 超 tip 却被 gate 拒满 \(k\) 次 → streak 保底晋级；菜单 Temp 在 `policy_admit_slack` 内不显著变差可软 Admit。

实现：本仓库（`python -m o1 run`）。
