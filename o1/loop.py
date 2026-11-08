from __future__ import annotations

import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .bandit import ucb1_select, update_arm
from .budget import Budget
from .mutate import apply_arm
from .policies import backup_menus, default_island_policies
from .select import select_parent
from .store import O1Store
from .survive import survive_topk
from .tasks.demo_fit import DemoTask, build_demo_task, init_program
from .types import IslandPolicy, IslandState, Program


@dataclass
class O1Config:
    budget_total: int = 120
    seed: int = 0
    migrate_every: int = 20
    stall_patience: int = 12
    policy_trial_len: int = 10
    out_dir: str = "runs/o1_demo"
    ucb_c: float = 1.414
    # island ticket weights (renormalized); weak islands keep a floor via sharing
    island_weight_floor: float = 0.15


@dataclass
class O1Result:
    tip_version: str
    tip_public: float
    tip_gate: float
    tip_sealed: float
    candidates: int
    policy_trials: int
    migrations: int
    out_dir: str
    budget: dict[str, Any]


@dataclass
class _Trial:
    island_id: str
    old_policy: IslandPolicy
    new_policy: IslandPolicy
    remaining: int
    start_best: float


def _public_score(task: DemoTask, program: Program) -> float:
    return task.judge.mean(program, task.split.public)


def _gate_score(task: DemoTask, program: Program) -> float:
    return task.judge.mean(program, task.split.gate)


def _sealed_score(task: DemoTask, program: Program) -> float:
    return task.judge.mean(program, task.split.sealed)


def _snapshot_island(island: IslandState) -> dict[str, Any]:
    return {
        "island_id": island.island_id,
        "policy": island.policy,
        "best_fitness": island.best_fitness,
        "stall_steps": island.stall_steps,
        "generations": island.generations,
        "population": island.population,
        "arm_stats": {k: v.as_dict() for k, v in island.arm_stats.items()},
    }


def run_o1(cfg: O1Config, task: DemoTask | None = None) -> O1Result:
    rng = random.Random(cfg.seed)
    task = task or build_demo_task(seed=cfg.seed)
    store = O1Store(Path(cfg.out_dir))
    budget = Budget(total=cfg.budget_total)

    policies = default_island_policies()
    islands: dict[str, IslandState] = {}
    parent_pulls: dict[str, dict[str, int]] = {}
    cand_i = 0
    tip = init_program(task.dim, version="c000000")
    tip_public = _public_score(task, tip)
    # charge nothing for init synthetic score (no eval ticket — weights known);
    # first real children spend island_search.

    for pol in policies:
        seed_prog = init_program(task.dim, version=f"c{cand_i:06d}", island_id=pol.island_id)
        cand_i += 1
        island = IslandState(island_id=pol.island_id, policy=pol, population=[seed_prog])
        island.ensure_arm_stats()
        island.best_fitness = _public_score(task, seed_prog)
        islands[pol.island_id] = island
        parent_pulls[pol.island_id] = {}
        store.save_policy(pol.version, {"policy": pol, "note": "bootstrap"})
        store.save_island(pol.island_id, _snapshot_island(island))

    store.save_tip(tip, {"public": tip_public, "note": "init"})
    store.log({"phase": "bootstrap", "islands": list(islands.keys()), "budget": budget.snapshot()})

    backups = backup_menus()
    trial: _Trial | None = None
    policy_trials = 0
    migrations = 0
    steps = 0

    tip_gate = _gate_score(task, tip)

    def consider_tip(prog: Program, account: str) -> None:
        nonlocal tip, tip_public, tip_gate
        pub = _public_score(task, prog)
        if pub <= tip_public:
            return
        # thin admit: public up and gate not clearly worse (no extra ticket;
        # gate mean is free relative to the already-charged child eval in this toy)
        gate = _gate_score(task, prog)
        if gate + 1e-12 < tip_gate - 0.02:
            store.log(
                {
                    "phase": "tip_reject_gate",
                    "version": prog.version,
                    "public": pub,
                    "gate": gate,
                    "tip_gate": tip_gate,
                    "account": account,
                }
            )
            return
        tip = prog
        tip_public = pub
        tip_gate = gate
        store.save_tip(tip, {"public": tip_public, "gate": tip_gate, "account": account})
        store.log(
            {
                "phase": "tip_update",
                "version": tip.version,
                "public": tip_public,
                "gate": tip_gate,
                "account": account,
            }
        )

    while budget.remaining_total() > 0:
        # pick island proportional to recent best (with floor)
        ids = list(islands.keys())
        raw = [max(islands[i].best_fitness, 1e-6) for i in ids]
        floor = cfg.island_weight_floor
        weights = [max(w, floor) for w in raw]
        total_w = sum(weights)
        r = rng.random() * total_w
        acc = 0.0
        island_id = ids[-1]
        for i, w in zip(ids, weights):
            acc += w
            if acc >= r:
                island_id = i
                break

        island = islands[island_id]
        account = "policy_trial" if (trial and trial.island_id == island_id) else "island_search"
        if not budget.can_afford(account, 1):
            # try any remaining island_search
            if account != "island_search" and budget.can_afford("island_search", 1):
                account = "island_search"
            elif budget.remaining_total() <= 0:
                break
            else:
                # spend sealed leftover only at end
                break

        island.ensure_arm_stats()
        parent = select_parent(
            island.population,
            island.policy.select_style,
            lambda p: _public_score(task, p),
            rng,
            parent_pulls=parent_pulls[island_id],
        )
        parent_pulls[island_id][parent.version] = parent_pulls[island_id].get(parent.version, 0) + 1

        arm = ucb1_select(island.policy.arm_menu, island.arm_stats, rng, c=cfg.ucb_c)
        child = apply_arm(
            parent,
            arm,
            rng,
            version=f"c{cand_i:06d}",
            island_id=island_id,
            peers=island.population,
        )
        cand_i += 1

        budget.charge(account, 1)
        parent_fit = _public_score(task, parent)
        child_fit = _public_score(task, child)
        # one charge covers the child official mean on public; parent already known
        reward = child_fit - parent_fit
        update_arm(island.arm_stats, arm, reward=reward, cost=1.0)

        island.population = survive_topk(
            island.population, child, island.policy.survive_k, lambda p: _public_score(task, p)
        )
        island.generations += 1
        steps += 1

        improved = child_fit > island.best_fitness + 1e-12
        if improved:
            island.best_fitness = child_fit
            island.stall_steps = 0
        else:
            island.stall_steps += 1

        store.log(
            {
                "phase": "search",
                "step": steps,
                "island": island_id,
                "arm": arm,
                "parent": parent.version,
                "child": child.version,
                "reward": reward,
                "child_public": child_fit,
                "account": account,
                "policy": island.policy.version,
            }
        )
        consider_tip(child, account=account)

        # policy trial countdown
        if trial and trial.island_id == island_id:
            trial.remaining -= 1
            if trial.remaining <= 0:
                # admit if island best improved vs trial start
                if island.best_fitness > trial.start_best + 1e-12:
                    island.policy = IslandPolicy(
                        island_id=trial.new_policy.island_id,
                        arm_menu=trial.new_policy.arm_menu,
                        select_style=trial.new_policy.select_style,
                        survive_k=trial.new_policy.survive_k,
                        behavior_tag=trial.new_policy.behavior_tag,
                        version=trial.new_policy.version,
                        parent_version=trial.old_policy.version,
                        status="active",
                    )
                    store.log(
                        {
                            "phase": "policy_admit",
                            "island": island_id,
                            "from": trial.old_policy.version,
                            "to": island.policy.version,
                            "best": island.best_fitness,
                        }
                    )
                else:
                    island.policy = trial.old_policy
                    store.log(
                        {
                            "phase": "policy_rollback",
                            "island": island_id,
                            "restored": trial.old_policy.version,
                            "best": island.best_fitness,
                            "start_best": trial.start_best,
                        }
                    )
                island.ensure_arm_stats()
                store.save_policy(island.policy.version, {"policy": island.policy})
                trial = None

        # stall → start policy trial (only if no active trial)
        if (
            trial is None
            and island.stall_steps >= cfg.stall_patience
            and budget.can_afford("policy_trial", cfg.policy_trial_len)
        ):
            alt_menu = backups.get(island_id)
            if alt_menu and alt_menu != island.policy.arm_menu:
                policy_trials += 1
                new_pol = IslandPolicy(
                    island_id=island_id,
                    arm_menu=alt_menu,
                    select_style=island.policy.select_style,
                    survive_k=island.policy.survive_k,
                    behavior_tag=island.policy.behavior_tag + "+trial",
                    version=f"{island.policy.version}-T{policy_trials}",
                    parent_version=island.policy.version,
                    status="temp",
                )
                trial = _Trial(
                    island_id=island_id,
                    old_policy=island.policy,
                    new_policy=new_pol,
                    remaining=cfg.policy_trial_len,
                    start_best=island.best_fitness,
                )
                island.policy = new_pol
                island.ensure_arm_stats()
                island.stall_steps = 0
                store.save_policy(new_pol.version, {"policy": new_pol, "note": "temp_trial"})
                store.log(
                    {
                        "phase": "policy_trial_start",
                        "island": island_id,
                        "old": trial.old_policy.version,
                        "new": new_pol.version,
                        "len": cfg.policy_trial_len,
                    }
                )

        # migration
        if steps > 0 and steps % cfg.migrate_every == 0 and budget.can_afford("migrate", 1):
            budget.charge("migrate", 1)
            migrations += 1
            src = max(islands.values(), key=lambda x: x.best_fitness)
            dst_candidates = [x for x in islands.values() if x.island_id != src.island_id]
            if src.population and dst_candidates:
                dst = min(dst_candidates, key=lambda x: x.best_fitness)
                elite = max(src.population, key=lambda p: _public_score(task, p))
                migrant = Program(
                    weights=elite.weights,
                    version=f"c{cand_i:06d}",
                    parent_version=elite.version,
                    island_id=dst.island_id,
                    arm_id="migrate",
                )
                cand_i += 1
                # evaluate migrant on public once (ticket already migrate)
                m_fit = _public_score(task, migrant)
                dst.population = survive_topk(
                    dst.population, migrant, dst.policy.survive_k, lambda p: _public_score(task, p)
                )
                if m_fit > dst.best_fitness:
                    dst.best_fitness = m_fit
                    dst.stall_steps = 0
                store.log(
                    {
                        "phase": "migrate",
                        "from": src.island_id,
                        "to": dst.island_id,
                        "elite": elite.version,
                        "migrant": migrant.version,
                        "migrant_public": m_fit,
                    }
                )
                consider_tip(migrant, account="migrate")

        store.save_island(island_id, _snapshot_island(island))
        store.save_budget(budget.snapshot())

        if budget.remaining("island_search") <= 0 and trial is None:
            break

    # sealed report (does not flow back into search decisions beyond logging)
    sealed = None
    if budget.can_afford("sealed", 1):
        budget.charge("sealed", 1)
        sealed = _sealed_score(task, tip)
        store.log({"phase": "sealed", "tip": tip.version, "sealed": sealed})

    gate = _gate_score(task, tip)
    pub = _public_score(task, tip)
    report = {
        "framework": "O1",
        "tip_version": tip.version,
        "tip_public": pub,
        "tip_gate": gate,
        "tip_sealed": sealed,
        "candidates": cand_i,
        "policy_trials": policy_trials,
        "migrations": migrations,
        "budget": budget.snapshot(),
        "islands": {i: _snapshot_island(s) for i, s in islands.items()},
    }
    store.save_report(report)
    store.save_tip(tip, {"public": pub, "gate": gate, "sealed": sealed})
    store.save_budget(budget.snapshot())

    return O1Result(
        tip_version=tip.version,
        tip_public=pub,
        tip_gate=gate,
        tip_sealed=float(sealed) if sealed is not None else float("nan"),
        candidates=cand_i,
        policy_trials=policy_trials,
        migrations=migrations,
        out_dir=str(Path(cfg.out_dir)),
        budget=budget.snapshot(),
    )
