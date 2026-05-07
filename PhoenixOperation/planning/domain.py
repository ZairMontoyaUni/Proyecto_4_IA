from __future__ import annotations

from planning.pddl import ActionSchema

# ---------------------------------------------------------------------------
# Punto 1a – Complete the preconditions and effects of each action schema.
#
# Each schema uses string variable names as placeholders:
#   "r"         → the robot
#   "from_cell" → source cell       "to_cell" → destination cell
#   "obj"       → any pickable object
#   "s"         → medical supplies  "p" → patient
#   "loc"       → a cell (used as the robot's current location)
#
# Fluent templates are tuples whose elements are either variable names or
# literal constant strings. get_applicable_actions() will substitute
# variable names with real constants during grounding.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Move(r, from_cell, to_cell)
# Move the robot one step to an adjacent, free cell.
# This one is given as an example. You can use it as a template for the other actions.
# ---------------------------------------------------------------------------

MOVE: ActionSchema = ActionSchema(
    name="Move",
    parameters=["r", "from_cell", "to_cell"],
    precond_pos=[
        ("At", "r", "from_cell"),
        ("Adjacent", "from_cell", "to_cell"),
        ("Free", "to_cell"),
    ],
    precond_neg=[],
    add_list=[
        ("At", "r", "to_cell"),
        ("Free", "from_cell"),
    ],
    del_list=[
        ("At", "r", "from_cell"),
        ("Free", "to_cell"),
    ],
)


# ---------------------------------------------------------------------------
# PickUp(r, obj, loc)
# Pick up a pickable object at the robot's current cell.
# After pickup: the object is no longer At loc, and the robot is no longer HandsFree.
# ---------------------------------------------------------------------------

# TODO: PUNTO 1a - Implementar PickUp action schema
# Precondiciones positivas: El robot debe estar en la ubicación (At(r, loc)),
# el objeto debe estar en esa ubicación (At(obj, loc)), el robot debe tener
# las manos libres (HandsFree(r)), y el objeto debe ser recogible (Pickable(obj))
# Efectos: El robot sostiene el objeto (Holding(r, obj)), el objeto ya no está
# en la ubicación (¬At(obj, loc)), y el robot ya no tiene las manos libres (¬HandsFree(r))
PICKUP: ActionSchema = ActionSchema(
    name="PickUp",
    parameters=["r", "obj", "loc"],
    precond_pos=[
        ("At", "r", "loc"),
        ("At", "obj", "loc"),
        ("HandsFree", "r"),
        ("Pickable", "obj"),
    ],
    precond_neg=[],
    add_list=[
        ("Holding", "r", "obj"),
    ],
    del_list=[
        ("At", "obj", "loc"),
        ("HandsFree", "r"),
    ],
)


# ---------------------------------------------------------------------------
# PutDown(r, obj, loc)
# Place a held object at the robot's current cell.
# After putdown: the object is At loc, and the robot is HandsFree again.
# ---------------------------------------------------------------------------

# TODO: PUNTO 1a - Implementar PutDown action schema
# Precondiciones positivas: El robot debe estar en la ubicación (At(r, loc))
# y debe estar sosteniendo el objeto (Holding(r, obj))
# Efectos: El objeto ahora está en la ubicación (At(obj, loc)), el robot ya no
# sostiene el objeto (¬Holding(r, obj)), y el robot tiene las manos libres (HandsFree(r))
PUTDOWN: ActionSchema = ActionSchema(
    name="PutDown",
    parameters=["r", "obj", "loc"],
    precond_pos=[
        ("At", "r", "loc"),
        ("Holding", "r", "obj"),
    ],
    precond_neg=[],
    add_list=[
        ("At", "obj", "loc"),
        ("HandsFree", "r"),
    ],
    del_list=[
        ("Holding", "r", "obj"),
    ],
)


# ---------------------------------------------------------------------------
# Rescue(r, p, loc)
# Rescue a patient who is at a medical post where supplies are ready.
# After rescue: patient is marked as Rescued and no longer At loc.
# ---------------------------------------------------------------------------

# TODO: PUNTO 1a - Implementar Rescue action schema
# Precondiciones positivas: El robot debe estar en el puesto médico (At(r, loc)),
# el paciente debe estar en el puesto médico (At(p, loc)), la ubicación debe ser
# un puesto médico (MedicalPost(loc)), y los suministros deben estar listos (SuppliesReady(loc))
# Efectos: El paciente es rescatado (Rescued(p)) y ya no está en el puesto médico (¬At(p, loc))
RESCUE: ActionSchema = ActionSchema(
    name="Rescue",
    parameters=["r", "p", "loc"],
    precond_pos=[
        ("At", "r", "loc"),
        ("At", "p", "loc"),
        ("MedicalPost", "loc"),
        ("SuppliesReady", "loc"),
    ],
    precond_neg=[],
    add_list=[
        ("Rescued", "p"),
    ],
    del_list=[
        ("At", "p", "loc"),
    ],
)


# ---------------------------------------------------------------------------
# SetupSupplies(r, s, loc)
# Set up medical supplies at a medical post.
# The robot must be at loc, holding the supplies, and loc must be a MedicalPost.
# Note: there is no At(s, loc) precondition because the robot is carrying s;
# the fluent At(s, loc) was removed when the robot picked it up.
# ---------------------------------------------------------------------------

# TODO: PUNTO 1a - Implementar SetupSupplies action schema
# Precondiciones positivas: El robot debe estar en el puesto médico (At(r, loc)),
# la ubicación debe ser un puesto médico (MedicalPost(loc)), y el robot debe estar
# sosteniendo los suministros (Holding(r, s)). NOTA: NO incluir At(s, loc) porque
# el robot está cargando los suministros (se eliminó con PickUp)
# Efectos: Los suministros están listos en el puesto (SuppliesReady(loc)), el robot
# ya no sostiene los suministros (¬Holding(r, s)), y tiene las manos libres (HandsFree(r))
SETUP_SUPPLIES: ActionSchema = ActionSchema(
    name="SetupSupplies",
    parameters=["r", "s", "loc"],
    precond_pos=[
        ("At", "r", "loc"),
        ("MedicalPost", "loc"),
        ("Holding", "r", "s"),
    ],
    precond_neg=[],
    add_list=[
        ("SuppliesReady", "loc"),
        ("HandsFree", "r"),
    ],
    del_list=[
        ("Holding", "r", "s"),
    ],
)


DOMAIN: list[ActionSchema] = [MOVE, PICKUP, PUTDOWN, RESCUE, SETUP_SUPPLIES]
