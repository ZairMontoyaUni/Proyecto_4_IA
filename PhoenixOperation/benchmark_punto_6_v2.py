#!/usr/bin/env python3
"""
Script de benchmarking optimizado para recopilar métricas reales de los algoritmos de planificación.
Versión 2: Con manejo inteligente de timeouts y combinaciones costosas.

Creado para el análisis del Punto 6 del Taller 4.
"""

import sys
import time
import json
import csv
import signal
from pathlib import Path
from contextlib import contextmanager

# Importar módulos del proyecto
import world.rescue_layout as rescue_layout
from planning.problems import SimpleRescueProblem, MultiRescueProblem
from planning.planner import forwardBFS, backwardSearch, aStarPlanner
from planning.heuristics import ignorePreconditionsHeuristic, ignoreDeleteListsHeuristic, nullHeuristic
from planning.htn import hierarchicalSearch, build_htn_hierarchy


# ============================================================================
# Timeout handler
# ============================================================================

class TimeoutException(Exception):
    pass


@contextmanager
def time_limit(seconds):
    """Context manager para timeout."""
    def signal_handler(signum, frame):
        raise TimeoutException("Timeout alcanzado")

    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)


# ============================================================================
# Configuración del benchmark
# ============================================================================

# Layouts a evaluar (selección representativa de cada categoría)
LAYOUTS_CONFIG = {
    # Layout: (problem_class, max_complexity)
    # max_complexity: tiny, small, medium, large
    "tinyBase": (SimpleRescueProblem, "tiny"),
    "smallRescue": (SimpleRescueProblem, "small"),
    "openRescue": (SimpleRescueProblem, "medium"),
    "cornerRescue": (SimpleRescueProblem, "small"),
    "warehouseRescue": (SimpleRescueProblem, "large"),
    "mediumRescue": (SimpleRescueProblem, "medium"),
    "tinyMulti": (MultiRescueProblem, "small"),
    "duoRescue": (MultiRescueProblem, "medium"),
}

# Algoritmos con su costo computacional estimado
ALGORITHMS_CONFIG = {
    "forwardBFS": {
        "function": forwardBFS,
        "description": "Búsqueda hacia adelante (BFS sin heurística)",
        "params": {},
        "cost": "medium",  # Costo computacional: low, medium, high, very_high
    },
    "backwardSearch": {
        "function": backwardSearch,
        "description": "Búsqueda regresiva desde el objetivo",
        "params": {},
        "cost": "low",
    },
    "aStarPlanner_ignorePreconditions": {
        "function": aStarPlanner,
        "description": "A* con heurística de ignorar precondiciones",
        "params": {"heuristic": ignorePreconditionsHeuristic},
        "cost": "very_high",  # Esta heurística es muy costosa
    },
    "aStarPlanner_ignoreDeleteLists": {
        "function": aStarPlanner,
        "description": "A* con heurística de ignorar listas de borrado",
        "params": {"heuristic": ignoreDeleteListsHeuristic},
        "cost": "high",
    },
    "aStarPlanner_nullHeuristic": {
        "function": aStarPlanner,
        "description": "A* sin heurística (UCS - baseline)",
        "params": {"heuristic": nullHeuristic},
        "cost": "medium",
    },
}

# Matriz de compatibilidad: qué combinaciones ejecutar
# very_high cost algorithms + medium/large layouts = skip
SKIP_COMBINATIONS = [
    ("aStarPlanner_ignorePreconditions", "openRescue"),
    ("aStarPlanner_ignorePreconditions", "mediumRescue"),
    ("aStarPlanner_ignorePreconditions", "warehouseRescue"),
    ("aStarPlanner_ignorePreconditions", "duoRescue"),
    ("aStarPlanner_ignoreDeleteLists", "mediumRescue"),
    ("aStarPlanner_ignoreDeleteLists", "warehouseRescue"),
    ("aStarPlanner_ignoreDeleteLists", "duoRescue"),
]

# Timeouts por complejidad (en segundos)
TIMEOUTS = {
    "tiny": 10,
    "small": 30,
    "medium": 60,
    "large": 120,
}


# ============================================================================
# Funciones auxiliares
# ============================================================================

def run_algorithm_with_timeout(algorithm_name, algorithm_info, problem, timeout_seconds):
    """
    Ejecuta un algoritmo sobre un problema con timeout.

    Returns:
        dict con las métricas
    """
    result = {
        "algorithm": algorithm_name,
        "success": False,
        "plan_length": 0,
        "plan_cost": 0,
        "states_expanded": 0,
        "execution_time": 0.0,
        "error": None,
        "timeout": False,
    }

    try:
        # Resetear contador
        problem._expanded = 0

        # Ejecutar con timeout
        start_time = time.time()

        with time_limit(timeout_seconds):
            planner_func = algorithm_info["function"]
            params = algorithm_info["params"]
            plan = planner_func(problem, **params)

        end_time = time.time()
        execution_time = end_time - start_time

        # Recopilar métricas
        result["success"] = plan is not None and len(plan) > 0
        result["plan_length"] = len(plan) if plan else 0
        result["plan_cost"] = problem.getCostOfActions(plan) if plan else 0
        result["states_expanded"] = problem._expanded
        result["execution_time"] = execution_time

        # Validar plan
        if plan:
            from planning.pddl import is_applicable, apply_action
            state = problem.initial_state
            valid = True
            for action in plan:
                if not is_applicable(state, action):
                    valid = False
                    result["error"] = "Plan inválido"
                    result["success"] = False
                    break
                state = apply_action(state, action)

            if valid and not problem.isGoalState(state):
                result["error"] = "Plan no alcanza objetivo"
                result["success"] = False

    except TimeoutException:
        result["error"] = f"Timeout ({timeout_seconds}s)"
        result["timeout"] = True
        result["states_expanded"] = problem._expanded
        result["execution_time"] = timeout_seconds

    except Exception as e:
        result["error"] = str(e)
        result["success"] = False

    return result


def run_htn_with_timeout(problem, timeout_seconds):
    """Ejecuta HTN con timeout."""
    result = {
        "algorithm": "hierarchicalSearch_HTN",
        "success": False,
        "plan_length": 0,
        "plan_cost": 0,
        "states_expanded": 0,
        "execution_time": 0.0,
        "error": None,
        "timeout": False,
    }

    try:
        problem._expanded = 0
        start_time = time.time()

        with time_limit(timeout_seconds):
            hlas = build_htn_hierarchy(problem)
            if not hlas:
                result["error"] = "No se pudieron construir HLAs"
                return result
            plan = hierarchicalSearch(problem, hlas)

        end_time = time.time()
        result["success"] = plan is not None and len(plan) > 0
        result["plan_length"] = len(plan) if plan else 0
        result["plan_cost"] = problem.getCostOfActions(plan) if plan else 0
        result["states_expanded"] = problem._expanded
        result["execution_time"] = end_time - start_time

    except TimeoutException:
        result["error"] = f"Timeout ({timeout_seconds}s)"
        result["timeout"] = True
        result["execution_time"] = timeout_seconds

    except Exception as e:
        result["error"] = str(e)

    return result


def benchmark_layout(layout_name, problem_class, complexity):
    """Ejecuta todos los algoritmos sobre un layout."""
    print(f"\n{'='*70}")
    print(f"Evaluando layout: {layout_name} (complejidad: {complexity})")
    print(f"{'='*70}")

    # Cargar layout
    layout = rescue_layout.get_layout(layout_name)
    if layout is None:
        print(f"  ERROR: Layout no encontrado")
        return []

    # Crear problema
    problem = problem_class(layout)

    print(f"  Dimensiones: {layout.width}×{layout.height}")
    print(f"  Pacientes: {len(problem.objects['patients'])}")
    print(f"  Suministros: {len(problem.objects['supplies'])}")

    results = []
    timeout = TIMEOUTS[complexity]

    # Ejecutar cada algoritmo
    for algo_name, algo_info in ALGORITHMS_CONFIG.items():
        # Verificar si debemos saltar esta combinación
        if (algo_name, layout_name) in SKIP_COMBINATIONS:
            print(f"\n  {algo_name}... SALTADO (combinación muy costosa)")
            result = {
                "layout": layout_name,
                "problem_type": problem_class.__name__,
                "algorithm": algo_name,
                "success": False,
                "plan_length": 0,
                "plan_cost": 0,
                "states_expanded": 0,
                "execution_time": 0.0,
                "error": "Saltado por costo computacional",
                "timeout": False,
                "skipped": True,
            }
            results.append(result)
            continue

        print(f"\n  {algo_name}...", end=" ", flush=True)

        problem_instance = problem_class(layout)
        result = run_algorithm_with_timeout(algo_name, algo_info, problem_instance, timeout)

        result["layout"] = layout_name
        result["problem_type"] = problem_class.__name__
        result["skipped"] = False

        if result["success"]:
            print(f"✓ Plan: {result['plan_length']} acc, "
                  f"Estados: {result['states_expanded']}, "
                  f"Tiempo: {result['execution_time']:.3f}s")
        elif result["timeout"]:
            print(f"⏱ TIMEOUT ({timeout}s), Estados: {result['states_expanded']}")
        else:
            print(f"✗ {result['error']}")

        results.append(result)

    # HTN
    print(f"\n  hierarchicalSearch_HTN...", end=" ", flush=True)
    problem_instance = problem_class(layout)
    result = run_htn_with_timeout(problem_instance, timeout)
    result["layout"] = layout_name
    result["problem_type"] = problem_class.__name__
    result["skipped"] = False

    if result["success"]:
        print(f"✓ Plan: {result['plan_length']} acc, "
              f"Tiempo: {result['execution_time']:.3f}s")
    else:
        print(f"✗ {result['error']}")

    results.append(result)

    return results


# ============================================================================
# Main benchmark
# ============================================================================

def main():
    print("\n" + "="*70)
    print("  BENCHMARK DE ALGORITMOS DE PLANIFICACIÓN - PUNTO 6 (v2)")
    print("="*70)
    print("\nEsta versión maneja inteligentemente los timeouts y combinaciones costosas.")
    print("\nResultados se guardarán en:")
    print("  - resultados_punto_6.json")
    print("  - resultados_punto_6.csv")

    all_results = []

    # Ejecutar todos los layouts
    for layout_name, (problem_class, complexity) in LAYOUTS_CONFIG.items():
        results = benchmark_layout(layout_name, problem_class, complexity)
        all_results.extend(results)

    # ========================================================================
    # Guardar resultados
    # ========================================================================
    print("\n" + "="*70)
    print("GUARDANDO RESULTADOS")
    print("="*70)

    # JSON
    output_json = Path("resultados_punto_6.json")
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    print(f"\n✓ JSON: {output_json}")

    # CSV
    output_csv = Path("resultados_punto_6.csv")
    if all_results:
        fieldnames = list(all_results[0].keys())
        with open(output_csv, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_results)
        print(f"✓ CSV: {output_csv}")

    # ========================================================================
    # Resumen
    # ========================================================================
    print("\n" + "="*70)
    print("RESUMEN")
    print("="*70)

    total = len(all_results)
    successful = sum(1 for r in all_results if r["success"])
    timeouts = sum(1 for r in all_results if r.get("timeout", False))
    skipped = sum(1 for r in all_results if r.get("skipped", False))
    failed = total - successful - skipped

    print(f"\nTotal: {total}")
    print(f"  Exitosas: {successful} ({successful/total*100:.1f}%)")
    print(f"  Timeouts: {timeouts} ({timeouts/total*100:.1f}%)")
    print(f"  Saltadas: {skipped} ({skipped/total*100:.1f}%)")
    print(f"  Fallidas: {failed} ({failed/total*100:.1f}%)")

    # Mejores algoritmos
    algo_stats = {}
    for r in all_results:
        if r["success"]:
            algo = r["algorithm"]
            if algo not in algo_stats:
                algo_stats[algo] = {"times": [], "states": []}
            algo_stats[algo]["times"].append(r["execution_time"])
            algo_stats[algo]["states"].append(r["states_expanded"])

    if algo_stats:
        print("\nTiempo promedio por algoritmo (solo exitosos):")
        for algo in sorted(algo_stats.keys(), key=lambda a: sum(algo_stats[a]["times"])/len(algo_stats[a]["times"])):
            stats = algo_stats[algo]
            avg_time = sum(stats["times"]) / len(stats["times"])
            avg_states = sum(stats["states"]) / len(stats["states"]) if stats["states"] else 0
            print(f"  {algo:42s}: {avg_time:7.3f}s  (estados: {avg_states:8.1f})")

    print("\n" + "="*70)
    print("BENCHMARK COMPLETADO")
    print("="*70)
    print("\nPróximo paso: ejecutar generate_graphs.py")


if __name__ == "__main__":
    main()
