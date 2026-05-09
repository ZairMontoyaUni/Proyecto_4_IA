from __future__ import annotations

from planning.pddl import ActionSchema, State, Objects, get_all_groundings, get_applicable_actions


def nullHeuristic(
    state: State,
    goal: State,
    domain: list[ActionSchema],
    objects: Objects,
) -> float:
    """Trivial heuristic — always returns 0 (equivalent to uniform-cost search)."""
    return 0


# ---------------------------------------------------------------------------
# Punto 4a – Ignore-Preconditions Heuristic
# ---------------------------------------------------------------------------


def ignorePreconditionsHeuristic(
    state: State,
    goal: State,
    domain: list[ActionSchema],
    objects: Objects,
) -> float:
    """
    Estimate the number of actions needed to satisfy all goal fluents,
    ignoring all action preconditions.

    With no preconditions, any action can be applied at any time.
    Each action can satisfy all goal fluents in its add_list in one step.
    The minimum number of actions to cover all unsatisfied goal fluents is
    a lower bound on the true plan length → this heuristic is admissible.

    Algorithm (greedy set cover):
      1. Compute unsatisfied = goal − state  (fluents still needed).
      2. Ground all actions ignoring preconditions and collect their add_lists.
      3. Greedily pick the action whose add_list covers the most unsatisfied fluents.
      4. Repeat until all fluents are covered; count the actions used.

    Tip: frozenset supports set difference (-) and intersection (&).
         You only need to ground actions once per call (use get_applicable_actions
         with the initial state, or generate all groundings regardless of state).
         Remember: with no preconditions, every grounding is "applicable".
    """
    ### Your code here ###

    """
    PRIMERA VERSIÓN DEL CÓDIGO (NO ESCRITO POR IA).

    insatisfechos = goal - state
    todasLasAcciones = get_all_groundings(domain, objects)
    contador = 0

    while insatisfechos:

        mejorAccion = None
        mejorCobertura = 0

        for accion in todasLasAcciones:
            cobertura = len(accion.add_list & insatisfechos)
            if cobertura > mejorCobertura:
                mejorCobertura = cobertura
                mejorAccion = accion
        
        if mejorAccion == None or mejorCobertura == 0:
            return float('inf')
        
        insatisfechos = insatisfechos - mejorAccion.add_list
        contador += 1
    
    return contador
    """
    """
    SEGUNDA VERSIÓN DE CÓDIGO (CON AYUDA DE IA)

    prompt: Para este código incluye comentarios y cualquier error o mejora que veas dime cómo corregirlo o qué cambios
    hacer y por qué.

    (Código original pegado)
    """

    # Paso 1: fluentes del goal que aún no están satisfechos en el estado actual
    insatisfechos = goal - state

    # Paso 2: obtener todas las acciones instanciadas ignorando precondiciones
    # (no usamos get_applicable_actions porque ignoramos precondiciones)
    todasLasAcciones = get_all_groundings(domain, objects)
    
    contador = 0

    # Paso 3: greedy set cover - repetir hasta cubrir todos los fluentes
    while insatisfechos:

        mejorAccion = None
        mejorCobertura = 0

        # Encontrar la acción que cubre más fluentes insatisfechos
        for accion in todasLasAcciones:
            cobertura = len(accion.add_list & insatisfechos)
            if cobertura > mejorCobertura:
                mejorCobertura = cobertura
                mejorAccion = accion
        
        # Si ninguna acción cubre ningún fluente, no hay solución desde aquí
        if mejorAccion is None or mejorCobertura == 0:
            return float('inf')
        
        # Restar los fluentes que cubre la mejor acción y contar un paso
        insatisfechos = insatisfechos - mejorAccion.add_list
        contador += 1
    
    return contador

    """
    ANÁLISIS (punto 4a a):

    Usando esta heurística para resolver el layour smallRescue, se puede ver que se encuentra
    una soluci+on de 23 pasos, expandiendo solo 1316. El plan real, al probar con nullHeuristic tiene
    23 acciones. Una heurística admisible nunca puede estimar más de 23 desde el estado inicial. Si
    ignorePreconditionsHeuristic hubiera sobreestimado, A* hubiera encontrado un plan no óptimo o
    incorrecto. 
    """
    ### End of your code ###

# ---------------------------------------------------------------------------
# Punto 4b – Ignore-Delete-Lists Heuristic
# ---------------------------------------------------------------------------


def ignoreDeleteListsHeuristic(
    state: State,
    goal: State,
    domain: list[ActionSchema],
    objects: Objects,
) -> float:
    """
    Estimate the plan cost by solving a relaxed problem where no action
    has a delete list (effects never remove fluents from the state).

    In this monotone relaxation, the state only grows over time (fluents are
    never removed), so hill-climbing always makes progress and cannot loop.

    Algorithm (hill-climbing on the relaxed problem):
      1. Start from the current state with a relaxed (monotone) apply function.
      2. At each step, pick the grounded action that adds the most unsatisfied
         goal fluents (greedy hill-climbing).
      3. Count steps until all goal fluents are satisfied (or until no progress).

    Tip: In the relaxed problem, apply_action never removes fluents.
         You can implement this by treating del_list as empty for all actions.
         Use get_applicable_actions to enumerate applicable grounded actions at
         each step (preconditions still apply in the relaxed model).
    """
    ### Your code here ###

    """
    PRIMERA VERSIÓN DEL CÓDIGO (NO ESCRITO POR IA).

    estadoRelajado = state

    contador = 0

    while state is not goal:
        accionesAplicables = get_applicable_actions(estadoRelajado, domain, objects)

        if accionesAplicables == []:
            return float('inf')
        
        mejorAccion = None
        mejorCobertura = 0
        
        for accion in accionesAplicables:
            cobertura = len(accion.add_list & (goal - estadoRelajado))
            if cobertura > mejorCobertura:
                mejorCobertura = cobertura
                mejorAccion = accion
        
        if mejorAccion is None or mejorCobertura == 0:
            return float('inf')
        
        contador += 1
    """

    """
    SEGUNDA VERSIÓN DE CÓDIGO (CON AYUDA DE IA)

    prompt: Con el código que escribí ayúdame a ver por qué no funciona y a corregirlo. Cualquier correción que hagas dime
    por qué es e incluye comentarios. 

    (Código original pegado)
    """

    # En el problema relajado el estado solo crece, nunca pierde fluentes
    # Iniciamos desde el estado actual
    estadoRelajado = state

    contador = 0

    # Repetir hasta que todos los fluentes del goal estén en el estado relajado
    while not goal.issubset(estadoRelajado):

        # Obtener acciones aplicables en el estado relajado actual
        # (precondiciones SÍ aplican, solo ignoramos delete lists)
        accionesAplicables = get_applicable_actions(estadoRelajado, domain, objects)

        # Si no hay acciones aplicables, no hay solución desde aquí
        if accionesAplicables == []:
            return float('inf')
        
        mejorAccion = None
        mejorCobertura = 0
        
        # Encontrar la acción que cubre más fluentes del goal aún no satisfechos
        for accion in accionesAplicables:
            # goal - estadoRelajado son los fluentes que aún faltan por satisfacer
            cobertura = len(accion.add_list & (goal - estadoRelajado))
            if cobertura > mejorCobertura:
                mejorCobertura = cobertura
                mejorAccion = accion
        
        # Si ninguna acción hace progreso hacia el goal, no hay solución
        if mejorAccion is None or mejorCobertura == 0:
            return float('inf')
        
        # Aplicar la acción de forma relajada: solo añadir, nunca eliminar
        estadoRelajado = estadoRelajado | mejorAccion.add_list

        contador += 1
    
    return contador

    """
    ANÁLISIS (punto 4b b y c):

    a: Número de estados heurísticas vs búsqueda hacia adelante
    tinyBase:
        forwardBFS: 345
        ignorePreconditionsHeuristic: 252
        ignoreDeleteListsHeuristic: 138

    Las heurísticas reducen significativamente la cantidad de nodos explorados. En este caso,
    guiar la búsqueda con información del dominio funciona bien para el problema. 

    b: Heurística más informativa

    ignoreDeleteListsHeuristic es la heurística más informativa. En el caso de este problema,
    las precondiciones en realidad afectan mucho el problema, por lo que un plan generado 
    ignorando las precondiciones puede llegar a ser muy diferente a un plan que sí las haya
    tomado en cuenta. Es decir, se pierde mucha información si se ignoran las precondiciones.
    Ignorar las delete lists es una manera de relajar el problema más cercana al problema real.
    Esto se refleja en los resultados obtenidos en el punto anterior. Como se puede ver, la cantidad
    de estados explorados reduce mucho más cuando se ignoran las delete lists. 
    """
    ### End of your code ###
