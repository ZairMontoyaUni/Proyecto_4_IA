from __future__ import annotations
from planning import utils

from collections.abc import Callable

from planning.pddl import (
    Action,
    ActionSchema,
    Problem,
    State,
    Objects,
    apply_action,
    get_all_groundings,
    is_applicable,
)
from planning.utils import Queue, PriorityQueue
from planning.heuristics import nullHeuristic


# ---------------------------------------------------------------------------
# Reference implementation – read and understand before coding the rest.
# ---------------------------------------------------------------------------


def tinyBaseSearch(problem: Problem) -> list[Action]:
    """
    Hardcoded plan for the tinyBase layout.
    The robot at (1,4) must: pick up supplies at (1,3), set them up at (1,2),
    pick up the patient at (1,1), bring them to (1,2), and execute Rescue.

    Useful to understand the Action object format and plan structure.
    """
    robot = "robot"
    supplies = "supplies_0"
    patient = "patient_0"

    c14 = (1, 4)  # robot start
    c13 = (1, 3)  # supplies
    c12 = (1, 2)  # medical post
    c11 = (1, 1)  # patient

    plan = [
        Action(
            "Move(robot,(1,4),(1,3))",
            [("At", robot, c14), ("Adjacent", c14, c13), ("Free", c13)],
            [],
            [("At", robot, c13), ("Free", c14)],
            [("At", robot, c14), ("Free", c13)],
        ),
        Action(
            "PickUp(robot,supplies_0,(1,3))",
            [
                ("At", robot, c13),
                ("At", supplies, c13),
                ("HandsFree", robot),
                ("Pickable", supplies),
            ],
            [],
            [("Holding", robot, supplies)],
            [("At", supplies, c13), ("HandsFree", robot)],
        ),
        Action(
            "Move(robot,(1,3),(1,2))",
            [("At", robot, c13), ("Adjacent", c13, c12), ("Free", c12)],
            [],
            [("At", robot, c12), ("Free", c13)],
            [("At", robot, c13), ("Free", c12)],
        ),
        Action(
            "SetupSupplies(robot,supplies_0,(1,2))",
            [("At", robot, c12), ("MedicalPost", c12), ("Holding", robot, supplies)],
            [("SuppliesReady", c12)],
            [("SuppliesReady", c12), ("HandsFree", robot)],
            [("Holding", robot, supplies)],
        ),
        Action(
            "Move(robot,(1,2),(1,1))",
            [("At", robot, c12), ("Adjacent", c12, c11), ("Free", c11)],
            [],
            [("At", robot, c11), ("Free", c12)],
            [("At", robot, c12), ("Free", c11)],
        ),
        Action(
            "PickUp(robot,patient_0,(1,1))",
            [
                ("At", robot, c11),
                ("At", patient, c11),
                ("HandsFree", robot),
                ("Pickable", patient),
            ],
            [],
            [("Holding", robot, patient)],
            [("At", patient, c11), ("HandsFree", robot)],
        ),
        Action(
            "Move(robot,(1,1),(1,2))",
            [("At", robot, c11), ("Adjacent", c11, c12), ("Free", c12)],
            [],
            [("At", robot, c12), ("Free", c11)],
            [("At", robot, c11), ("Free", c12)],
        ),
        Action(
            "PutDown(robot,patient_0,(1,2))",
            [("At", robot, c12), ("Holding", robot, patient)],
            [],
            [("At", patient, c12), ("HandsFree", robot)],
            [("Holding", robot, patient)],
        ),
        Action(
            "Rescue(robot,patient_0,(1,2))",
            [
                ("At", robot, c12),
                ("At", patient, c12),
                ("MedicalPost", c12),
                ("SuppliesReady", c12),
            ],
            [],
            [("Rescued", patient)],
            [("At", patient, c12)],
        ),
    ]
    return plan


# ---------------------------------------------------------------------------
# Punto 2 – Forward Planning
# ---------------------------------------------------------------------------


def forwardBFS(problem: Problem) -> list[Action]:
    """
    Forward BFS in state space.

    Explore states reachable from the initial state by applying actions,
    in breadth-first order, until a goal state is found.

    Returns a list of Action objects forming a valid plan, or [] if no plan exists.

    Tip: The state is a frozenset of fluents. Use problem.getSuccessors(state)
         to get (next_state, action, cost) triples. Track visited states to
         avoid revisiting the same state twice (graph search, not tree search).
    """
    ### Your code here ###

    """
    PRIMERA VERSIÓN DEL CÓDIGO (NO ESCRITO POR IA)

    cola = utils.Queue()
    visitados = set()

    inicio = problem.getStartState()

    # En la cola voy a meter el nodo con la lista de acciones para llegar hasta ahí. 
    cola.push((inicio, []))
    visitados.add(inicio)

    while not cola.isEmpty():

        estadoActual, listaAcciones = cola.pop()
        
        if problem.isGoalState(estadoActual):
            return listaAcciones
        
        for siguienteEstado, accion, costo in problem.getSuccessors(estadoActual):
            if siguienteEstado not in visitados:
                visitados.add(siguienteEstado)
                nuevaListaAcciones = listaAcciones + [accion]
                cola.push((siguienteEstado, nuevaListaAcciones))

    return []
    """

    """
    SEGUNDA VERSIÓN DE CÓDIGO (CON AYUDA DE IA)

    prompt: Quiero a este código le pongas comentarios para que sea más fácil de entender y 
    dime qué refinamientos harías y por qué. Si tiene algún error también dímelo.

    (Código original pegado)
    """
    cola = utils.Queue()
    visitados = set()

    inicio = problem.getStartState()

    # Cada elemento de la cola es (estado, lista_de_acciones_para_llegar_aquí)
    # Empezamos desde el estado inicial con un plan vacío
    cola.push((inicio, []))
    visitados.add(inicio)

    while not cola.isEmpty():

        estadoActual, listaAcciones = cola.pop()
        
        # Si el estado actual satisface el objetivo, el plan está completo
        if problem.isGoalState(estadoActual):
            return listaAcciones
        
        # Expandir el nodo: obtener todos los estados alcanzables desde aquí
        for siguienteEstado, accion, costo in problem.getSuccessors(estadoActual):
            if siguienteEstado not in visitados:
                # Marcar como visitado al insertar evita duplicados en la cola
                visitados.add(siguienteEstado)
                # Crear el nuevo historial de acciones extendiendo el actual
                nuevaListaAcciones = listaAcciones + [accion]
                cola.push((siguienteEstado, nuevaListaAcciones))

    # No se encontró ningún plan válido
    return []

    """
    ANÁLISIS (Punto 2c):
    
    Para este análisis se va a tomar el layout tinyBase (5x7) y el layout warehouseRescue (15x12)

    Para tinyBase se hizo una exploración de 345 estados y se encontró un plan de 9 pasos,
    mientras que para warehouseRescue se hizo una eploración de 11428 estados y se encontró
    un plan de 31 pasos.

    Como se puede ver, el número de estados incrementó aproximadamente 33 veces para un plan que
    solo aumentó aproximadamente 4 veces. Esto muestra que el crecimiento de los estados a explorar
    es mucho mayor que el crecimiento del espacio en sí y el plan generado debido a que cada vez existen 
    muchas más combinaciones de estados que se pueden hacer para llegar a un estado específico. 
    Esto hace que los problemas donde el espaco es muy grande sean intratables sin heurísticas. 

    Búsqueda hacia adelante sin heurísticas es completo y siempre encuentra el mejor camino pero 
    claramente no es escalable. 
    """

    ### End of your code ###


# ---------------------------------------------------------------------------
# Punto 3 – Backward Planning
# ---------------------------------------------------------------------------


def regress(goal_set: State, action: Action) -> State | None:
    """
    Compute the regression of goal_set through action.

    Given a goal description (set of fluents that must be true) and an action,
    return the new goal description that, if satisfied, guarantees the original
    goal is satisfied after executing action.

    REGRESS(g, a) = (g − ADD(a)) ∪ PRECOND_pos(a)
        IF:  ADD(a) ∩ g ≠ ∅   (action is relevant: contributes to the goal)
        AND: DEL(a) ∩ g = ∅   (action does not undo any goal fluent)
    Returns None if the action is not relevant or creates a contradiction.

    Tip: Use frozenset operations: intersection (&), difference (-), union (|).
         Check relevance first, then check for contradictions, then compute.
    """
    ### Your code here ###
    if action.add_list.isdisjoint(goal_set):
        return None
    if not action.del_list.isdisjoint(goal_set):
        return None

    regressed_goal = (goal_set - action.add_list) | action.precond_pos
    if not action.precond_neg.isdisjoint(regressed_goal):
        return None
    return frozenset(regressed_goal)
    ### End of your code ###


def backwardSearch(problem: Problem) -> list[Action]:
    """
    Backward search (regression search) from the goal.

    Start from the goal description and apply action regressions until
    the resulting goal is satisfied by the initial state.

    Returns a list of Action objects forming a valid plan (in forward order),
    or [] if no plan exists.

    Tip: The "state" in backward search is a frozenset of fluents that must
         be true (a partial goal description). The initial state is reached
         when all fluents in the current goal are satisfied by problem.initial_state.
         Only consider actions whose add_list has at least one unsatisfied goal fluent
         (relevant actions). Use regress() to compute the new subgoal.
         Skip subgoals that contain static predicates (MedicalPost, Adjacent,
         Pickable) that are false in the initial state — these are dead ends.
    """
    ### Your code here ###
    static_predicates = {"Adjacent", "MedicalPost", "Pickable"}

    def normalize_goal(goal: State) -> State | None:
        normalized = set()
        for fluent in goal:
            if fluent[0] in static_predicates:
                if fluent not in problem.initial_state:
                    return None
                continue
            normalized.add(fluent)
        return frozenset(normalized)

    def is_consistent(goal: State) -> bool:
        at_by_entity = {}
        holding_by_robot = {}
        holding_objects = set()
        hands_free_robots = set()
        free_cells = set()
        rescued_patients = set()

        for fluent in goal:
            predicate = fluent[0]

            if predicate == "At":
                entity, cell = fluent[1], fluent[2]
                if entity in at_by_entity and at_by_entity[entity] != cell:
                    return False
                at_by_entity[entity] = cell

            elif predicate == "Holding":
                robot, obj = fluent[1], fluent[2]
                if robot in holding_by_robot and holding_by_robot[robot] != obj:
                    return False
                holding_by_robot[robot] = obj
                holding_objects.add(obj)

            elif predicate == "HandsFree":
                hands_free_robots.add(fluent[1])

            elif predicate == "Free":
                free_cells.add(fluent[1])

            elif predicate == "Rescued":
                rescued_patients.add(fluent[1])

        robot_cell = at_by_entity.get("robot")
        if robot_cell in free_cells:
            return False

        if not hands_free_robots.isdisjoint(holding_by_robot):
            return False

        if not holding_objects.isdisjoint(at_by_entity):
            return False

        if not rescued_patients.isdisjoint(at_by_entity):
            return False

        if not rescued_patients.isdisjoint(holding_objects):
            return False

        return True

    def plan_is_valid(plan: list[Action]) -> bool:
        state = problem.initial_state
        for action in plan:
            if not is_applicable(state, action):
                return False
            state = apply_action(state, action)
        return problem.isGoalState(state)

    initial_at = {
        fluent[1]: fluent[2]
        for fluent in problem.initial_state
        if fluent[0] == "At"
    }
    adjacency = {}
    for fluent in problem.initial_state:
        if fluent[0] == "Adjacent":
            adjacency.setdefault(fluent[1], []).append(fluent[2])
    distance_cache = {}

    def distances_to_targets(targets: set) -> dict:
        key = frozenset(targets)
        if key in distance_cache:
            return distance_cache[key]

        distances = {}
        queue = Queue()
        for target in targets:
            distances[target] = 0
            queue.push(target)

        while not queue.isEmpty():
            cell = queue.pop()
            for neighbor in adjacency.get(cell, []):
                if neighbor in distances:
                    continue
                distances[neighbor] = distances[cell] + 1
                queue.push(neighbor)

        distance_cache[key] = distances
        return distances

    def object_known_locations(goal: State, obj: object) -> set:
        locations = {fluent[2] for fluent in goal if fluent[0] == "At" and fluent[1] == obj}
        if obj in initial_at:
            locations.add(initial_at[obj])
        return locations

    def select_subgoal(goal: State) -> object:
        unsatisfied = goal - problem.initial_state

        for fluent in unsatisfied:
            if fluent[0] == "Rescued":
                return fluent

        for fluent in unsatisfied:
            if fluent[0] == "At" and fluent[1] != "robot":
                return fluent

        has_holding_goal = any(fluent[0] == "Holding" for fluent in goal)
        if not has_holding_goal:
            for fluent in unsatisfied:
                if fluent[0] == "SuppliesReady" and ("At", "robot", fluent[1]) in goal:
                    return fluent

        robot_locations = {
            fluent[2] for fluent in goal if fluent[0] == "At" and fluent[1] == "robot"
        }
        for fluent in unsatisfied:
            if fluent[0] == "Holding":
                obj_locations = object_known_locations(goal, fluent[2])
                if robot_locations & obj_locations:
                    return fluent

        for fluent in unsatisfied:
            if fluent[0] == "At" and fluent[1] == "robot":
                return fluent

        for fluent in unsatisfied:
            if fluent[0] == "Holding":
                return fluent

        for fluent in unsatisfied:
            if fluent[0] == "SuppliesReady":
                return fluent

        return next(iter(unsatisfied))

    def navigation_targets(goal: State) -> set:
        for fluent in goal:
            if fluent[0] == "Holding":
                locations = object_known_locations(goal, fluent[2])
                if locations:
                    return locations

        for fluent in goal:
            if fluent[0] == "SuppliesReady":
                return {fluent[1]}

        robot_start = initial_at.get("robot")
        return {robot_start} if robot_start is not None else set()

    def move_gets_closer_to_target(action: Action, selected_goal: object, goal: State) -> bool:
        if selected_goal[0] != "At" or selected_goal[1] != "robot":
            return True
        if not action.name.startswith("Move("):
            return True

        to_cell = selected_goal[2]
        from_cells = [
            fluent[2]
            for fluent in action.precond_pos
            if fluent[0] == "At" and fluent[1] == "robot"
        ]
        if not from_cells:
            return True

        targets = navigation_targets(goal)
        if not targets:
            return True

        distances = distances_to_targets(targets)
        from_distance = distances.get(from_cells[0], float("inf"))
        to_distance = distances.get(to_cell, float("inf"))
        return from_distance < to_distance

    start_goal = normalize_goal(problem.goal)
    if start_goal is None or not is_consistent(start_goal):
        return []

    actions = sorted(
        [
            action
            for action in get_all_groundings(problem.domain, problem.objects)
            if all(
                fluent in problem.initial_state
                for fluent in action.precond_pos
                if fluent[0] in static_predicates
            )
        ],
        key=lambda action: {
            "Rescue": 0,
            "PutDown": 1,
            "SetupSupplies": 2,
            "PickUp": 3,
            "Move": 4,
        }.get(action.name.split("(", 1)[0], 5),
    )

    queue = Queue()
    queue.push((start_goal, []))
    visited = {start_goal}

    while not queue.isEmpty():
        current_goal, plan = queue.pop()

        if current_goal.issubset(problem.initial_state):
            if plan_is_valid(plan):
                return plan
            continue

        problem._expanded += 1
        selected_goal = select_subgoal(current_goal)

        for action in actions:
            if selected_goal not in action.add_list:
                continue
            if not move_gets_closer_to_target(action, selected_goal, current_goal):
                continue

            next_goal = regress(current_goal, action)
            if next_goal is None:
                continue

            next_goal = normalize_goal(next_goal)
            if next_goal is None or next_goal in visited:
                continue
            if not is_consistent(next_goal):
                continue

            visited.add(next_goal)
            queue.push((next_goal, [action] + plan))

    return []
    ### End of your code ###


# ---------------------------------------------------------------------------
# Punto 4 – A* Planner
# ---------------------------------------------------------------------------

# Heuristic signature:  heuristic(state, goal, domain, objects) -> float
Heuristic = Callable[[State, State, list[ActionSchema], Objects], float]


def aStarPlanner(
    problem: Problem,
    heuristic: Heuristic = nullHeuristic,
) -> list[Action]:
    """
    Forward A* search guided by a heuristic.

    Combines the real accumulated cost g(n) with the heuristic estimate h(n)
    to prioritize which state to expand next: f(n) = g(n) + h(n).

    Returns a list of Action objects forming a valid plan, or [] if no plan exists.

    Tip: The heuristic signature is heuristic(state, goal, domain, objects) → float.
         Use PriorityQueue with priority = g + h(next_state).
         Track the best g-cost seen for each state to avoid stale expansions.
    """
    ### Your code here ###

    """
    PRIMERA VERSIÓN DEL CÓDIGO (NO ESCRITO POR IA). Basada en implementación anterior del punto 2.

    cola = utils.PriorityQueue()
    visitados = set()

    inicio = problem.getStartState()
    hInicio = heuristic(inicio, problem.goal, problem.domain, problem.objects)

    cola.push((inicio, [], 0), 0 + hInicio)
    visitados.add(inicio)

    while not cola.isEmpty():

        estadoActual, listaAcciones, costoAcumulado = cola.pop()
        
        if problem.isGoalState(estadoActual):
            return listaAcciones
        
        for siguienteEstado, accion, costo in problem.getSuccessors(estadoActual):
            if siguienteEstado not in visitados:
                visitados.add(siguienteEstado)
                nuevaListaAcciones = listaAcciones + [accion]
                h = heuristic(siguienteEstado, problem.goal, problem.domain, problem.objects)
                nuevoCosto = costoAcumulado + costo
                cola.push((siguienteEstado, nuevaListaAcciones, nuevoCosto), nuevoCosto + h)

    return []

    """
    """
    SEGUNDA VERSIÓN DE CÓDIGO (CON AYUDA DE IA)

    prompt: Escribí este código para A*. Ayúdame a mejorarlo e identificar errores. Lo que corrijas dime 
    por qué lo corregiste e incluye comentarios:

    (Código original pegado)
    """

    cola = PriorityQueue()
    # Diccionario estado -> mejor costo g visto, para evitar expansiones subóptimas
    mejor_g = {}

    inicio = problem.getStartState()
    h_inicio = heuristic(inicio, problem.goal, problem.domain, problem.objects)

    cola.push((inicio, [], 0), 0 + h_inicio)
    mejor_g[inicio] = 0

    while not cola.isEmpty():

        estadoActual, listaAcciones, costoAcumulado = cola.pop()

        # Si ya encontramos un camino más barato a este estado, ignorar
        if costoAcumulado > mejor_g.get(estadoActual, float('inf')):
            continue

        if problem.isGoalState(estadoActual):
            return listaAcciones

        for siguienteEstado, accion, costo in problem.getSuccessors(estadoActual):
            nuevoCosto = costoAcumulado + costo

            # Solo explorar si encontramos un camino más barato al siguiente estado
            if nuevoCosto < mejor_g.get(siguienteEstado, float('inf')):
                mejor_g[siguienteEstado] = nuevoCosto
                nuevaListaAcciones = listaAcciones + [accion]
                h = heuristic(siguienteEstado, problem.goal, problem.domain, problem.objects)
                # Prioridad = costo real acumulado + estimación heurística
                cola.push((siguienteEstado, nuevaListaAcciones, nuevoCosto), nuevoCosto + h)

    return []
    ### End of your code ###


# Aliases used by the command-line argument parser
tinyBaseSearch = tinyBaseSearch
forwardBFS = forwardBFS
backwardSearch = backwardSearch
aStarPlanner = aStarPlanner
