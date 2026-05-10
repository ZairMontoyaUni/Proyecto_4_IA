from __future__ import annotations

from collections import deque

from planning.pddl import Action, Problem, apply_action, is_applicable
from planning.domain import MOVE, PICKUP, PUTDOWN, RESCUE, SETUP_SUPPLIES
from planning.utils import Queue


# ---------------------------------------------------------------------------
# HTN Infrastructure
# ---------------------------------------------------------------------------


class HLA:
    """
    A High-Level Action (HLA) in HTN planning.

    An HLA is an abstract task that can be refined into sequences of
    more primitive actions (or other HLAs). Each refinement is a list
    of HLA or Action objects.

    name:        Human-readable name for display
    refinements: List of possible refinements, each a list of HLA/Action objects
    """

    def __init__(self, name: str, refinements: list[list] | None = None) -> None:
        self.name = name
        self.refinements = refinements or []

    def __repr__(self) -> str:
        return f"HLA({self.name})"


def is_primitive(action: Action | HLA) -> bool:
    """Return True if action is a primitive (grounded Action), False if it is an HLA."""
    return isinstance(action, Action)


def is_plan_primitive(plan: list[Action | HLA]) -> bool:
    """Return True if every step in the plan is a primitive action."""
    return all(is_primitive(step) for step in plan)


# ---------------------------------------------------------------------------
# Punto 5a – hierarchicalSearch
# ---------------------------------------------------------------------------


def hierarchicalSearch(problem: Problem, hlas: list[HLA]) -> list[Action]:
    """
    HTN planning via BFS over hierarchical plan refinements.

    Start with an initial plan containing a single top-level HLA.
    At each step, find the first non-primitive step in the plan and
    replace it with one of its refinements. Continue until the plan
    is fully primitive and achieves the goal when executed from the
    initial state.
    """
    if not hlas:
        return []

    queue = Queue()
    queue.push([hlas[0]])

    while not queue.isEmpty():
        plan = queue.pop()

        # Find the first non-primitive step (HLA) in the plan.
        first_hla_idx = None
        for i, step in enumerate(plan):
            if not is_primitive(step):
                first_hla_idx = i
                break

        if first_hla_idx is None:
            # Plan is fully primitive: simulate it from the initial state
            # and check whether the goal is reached.
            state = problem.getStartState()
            executable = True
            for action in plan:
                if not is_applicable(state, action):
                    executable = False
                    break
                state = apply_action(state, action)
            if executable and problem.isGoalState(state):
                return plan
            continue

        # Replace the first HLA with each of its refinements.
        hla = plan[first_hla_idx]
        prefix = plan[:first_hla_idx]
        suffix = plan[first_hla_idx + 1:]
        for refinement in hla.refinements:
            new_plan = prefix + list(refinement) + suffix
            queue.push(new_plan)

    return []


# ---------------------------------------------------------------------------
# Punto 5b – HLA Definitions
# ---------------------------------------------------------------------------


def build_htn_hierarchy(problem: Problem) -> list[HLA]:
    """
    Build HTN HLAs for the rescue domain.

    Hierarchy:
      Navigate(from, to)        → sequence of Move actions along a shortest path
      PrepareSupplies(s, m)     → Navigate, PickUp(s), Navigate, SetupSupplies
      ExtractPatient(p, m)      → Navigate, PickUp(p), Navigate, PutDown(p)
      FullRescueMission(s,p,m)  → PrepareSupplies, ExtractPatient, Rescue

    For MultiRescueProblem the root HLA chains one FullRescueMission per
    patient, in input order, each consuming one supply.
    """
    objects = problem.objects
    initial_state = problem.initial_state

    if not objects.get("robots") or not objects.get("medical_posts"):
        return []

    robot = objects["robots"][0]
    supplies = objects["supplies"]
    patients = objects["patients"]
    medical_post = objects["medical_posts"][0]

    if not patients or not supplies:
        return []

    # Position lookup from initial-state At fluents.
    pos_of: dict[str, tuple[int, int]] = {}
    for fluent in initial_state:
        if fluent[0] == "At":
            pos_of[fluent[1]] = fluent[2]

    # Adjacency map for BFS path finding.
    adjacency: dict[tuple[int, int], list[tuple[int, int]]] = {}
    for fluent in initial_state:
        if fluent[0] == "Adjacent":
            adjacency.setdefault(fluent[1], []).append(fluent[2])

    robot_start = pos_of[robot]

    # ---- helpers ---------------------------------------------------------

    def shortest_path(a: tuple[int, int], b: tuple[int, int]) -> list[tuple[int, int]] | None:
        if a == b:
            return [a]
        visited = {a}
        queue: deque = deque([(a, [a])])
        while queue:
            cell, path = queue.popleft()
            for nb in adjacency.get(cell, []):
                if nb in visited:
                    continue
                visited.add(nb)
                new_path = path + [nb]
                if nb == b:
                    return new_path
                queue.append((nb, new_path))
        return None

    def make_move(from_cell, to_cell) -> Action:
        return MOVE.ground({"r": robot, "from_cell": from_cell, "to_cell": to_cell})

    def make_pickup(obj, loc) -> Action:
        return PICKUP.ground({"r": robot, "obj": obj, "loc": loc})

    def make_putdown(obj, loc) -> Action:
        return PUTDOWN.ground({"r": robot, "obj": obj, "loc": loc})

    def make_setup(s, loc) -> Action:
        return SETUP_SUPPLIES.ground({"r": robot, "s": s, "loc": loc})

    def make_rescue(p, loc) -> Action:
        return RESCUE.ground({"r": robot, "p": p, "loc": loc})

    def navigate_hla(a, b) -> HLA:
        path = shortest_path(a, b)
        if path is None:
            return HLA(f"Navigate({a}->{b})", [])
        moves = [make_move(path[i], path[i + 1]) for i in range(len(path) - 1)]
        return HLA(f"Navigate({a}->{b})", [moves])

    def prepare_supplies_hla(s, m_pos, from_pos) -> HLA:
        s_pos = pos_of[s]
        return HLA(
            f"PrepareSupplies({s}@{m_pos})",
            [[
                navigate_hla(from_pos, s_pos),
                make_pickup(s, s_pos),
                navigate_hla(s_pos, m_pos),
                make_setup(s, m_pos),
            ]],
        )

    def extract_patient_hla(p, m_pos, from_pos) -> HLA:
        p_pos = pos_of[p]
        return HLA(
            f"ExtractPatient({p}@{m_pos})",
            [[
                navigate_hla(from_pos, p_pos),
                make_pickup(p, p_pos),
                navigate_hla(p_pos, m_pos),
                make_putdown(p, m_pos),
            ]],
        )

    def full_rescue_hla(s, p, m_pos, from_pos) -> HLA:
        # After PrepareSupplies the robot is at m_pos, so ExtractPatient
        # starts there.
        return HLA(
            f"FullRescueMission({s},{p}@{m_pos})",
            [[
                prepare_supplies_hla(s, m_pos, from_pos),
                extract_patient_hla(p, m_pos, m_pos),
                make_rescue(p, m_pos),
            ]],
        )

    # ---- root HLA --------------------------------------------------------

    if len(patients) == 1:
        return [full_rescue_hla(supplies[0], patients[0], medical_post, robot_start)]

    # Multi-rescue: chain FullRescueMission per patient (input order).
    # Each rescue consumes its own supply; if there are fewer supplies than
    # patients, the extra patients reuse the last supply (will fail unless
    # SuppliesReady persists — which it does).
    rescues: list[HLA] = []
    current_pos = robot_start
    for i, patient in enumerate(patients):
        supply = supplies[i] if i < len(supplies) else supplies[-1]
        rescues.append(full_rescue_hla(supply, patient, medical_post, current_pos))
        current_pos = medical_post  # robot ends at the medical post after Rescue

    return [HLA("MultiRescue", [rescues])]
