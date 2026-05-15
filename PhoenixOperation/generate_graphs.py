#!/usr/bin/env python3
"""
Script para generar gráficas comparativas de los resultados del benchmark.
Lee resultados_punto_6.json y genera visualizaciones en la carpeta graficas_punto_6/
"""

import json
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from pathlib import Path

# Configuración de estilo
plt.style.use('seaborn-v0_8-darkgrid')
COLORS = {
    "forwardBFS": "#3498db",
    "backwardSearch": "#2ecc71",
    "aStarPlanner_ignorePreconditions": "#e74c3c",
    "aStarPlanner_ignoreDeleteLists": "#f39c12",
    "aStarPlanner_nullHeuristic": "#9b59b6",
    "hierarchicalSearch_HTN": "#1abc9c",
}

# Crear directorio para gráficas
output_dir = Path("graficas_punto_6")
output_dir.mkdir(exist_ok=True)

# Cargar datos
with open("resultados_punto_6.json", "r", encoding="utf-8") as f:
    results = json.load(f)

print("Generando gráficas comparativas...")

# ============================================================================
# Gráfica 1: Tiempo de ejecución por algoritmo (solo exitosos)
# ============================================================================

print("\n1. Gráfica de tiempo de ejecución por algoritmo...")

algo_times = {}
for r in results:
    if r["success"] and not r.get("skipped", False):
        algo = r["algorithm"]
        if algo not in algo_times:
            algo_times[algo] = []
        algo_times[algo].append(r["execution_time"])

if algo_times:
    algos = sorted(algo_times.keys(), key=lambda a: np.mean(algo_times[a]))
    means = [np.mean(algo_times[a]) for a in algos]
    stds = [np.std(algo_times[a]) if len(algo_times[a]) > 1 else 0 for a in algos]

    plt.figure(figsize=(12, 6))
    bars = plt.bar(range(len(algos)), means, yerr=stds, capsize=5,
                   color=[COLORS.get(a, "#95a5a6") for a in algos],
                   edgecolor='black', linewidth=1.2)
    plt.xlabel("Algoritmo", fontsize=12, fontweight='bold')
    plt.ylabel("Tiempo de ejecución promedio (s)", fontsize=12, fontweight='bold')
    plt.title("Tiempo de Ejecución Promedio por Algoritmo (solo ejecuciones exitosas)",
              fontsize=14, fontweight='bold')
    plt.xticks(range(len(algos)), algos, rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(output_dir / "tiempo_por_algoritmo.png", dpi=300, bbox_inches='tight')
    plt.close()
    print("   ✓ tiempo_por_algoritmo.png")

# ============================================================================
# Gráfica 2: Estados expandidos por algoritmo (solo exitosos)
# ============================================================================

print("2. Gráfica de estados expandidos por algoritmo...")

algo_states = {}
for r in results:
    if r["success"] and not r.get("skipped", False) and r["states_expanded"] > 0:
        algo = r["algorithm"]
        if algo not in algo_states:
            algo_states[algo] = []
        algo_states[algo].append(r["states_expanded"])

if algo_states:
    algos = sorted(algo_states.keys(), key=lambda a: np.mean(algo_states[a]))
    means = [np.mean(algo_states[a]) for a in algos]
    stds = [np.std(algo_states[a]) if len(algo_states[a]) > 1 else 0 for a in algos]

    plt.figure(figsize=(12, 6))
    plt.bar(range(len(algos)), means, yerr=stds, capsize=5,
            color=[COLORS.get(a, "#95a5a6") for a in algos],
            edgecolor='black', linewidth=1.2)
    plt.xlabel("Algoritmo", fontsize=12, fontweight='bold')
    plt.ylabel("Estados expandidos promedio", fontsize=12, fontweight='bold')
    plt.title("Estados Expandidos Promedio por Algoritmo (solo ejecuciones exitosas)",
              fontsize=14, fontweight='bold')
    plt.xticks(range(len(algos)), algos, rotation=45, ha='right')
    plt.yscale('log')  # Escala logarítmica por las diferencias grandes
    plt.tight_layout()
    plt.savefig(output_dir / "estados_por_algoritmo.png", dpi=300, bbox_inches='tight')
    plt.close()
    print("   ✓ estados_por_algoritmo.png")

# ============================================================================
# Gráfica 3: Comparación de layouts (tiempo)
# ============================================================================

print("3. Gráfica comparativa por layout (tiempo)...")

# Agrupar por layout y algoritmo
layout_algo_time = {}
for r in results:
    if r["success"] and not r.get("skipped", False):
        layout = r["layout"]
        algo = r["algorithm"]
        if layout not in layout_algo_time:
            layout_algo_time[layout] = {}
        layout_algo_time[layout][algo] = r["execution_time"]

# Filtrar solo layouts simple (no multi) para esta gráfica
simple_layouts = [l for l in layout_algo_time.keys() if "Multi" not in l and "duo" not in l.lower()]

if simple_layouts and len(simple_layouts) >= 3:
    # Seleccionar 3-4 layouts representativos
    selected_layouts = simple_layouts[:4] if len(simple_layouts) >= 4 else simple_layouts

    algos = list(set(algo for layout_data in layout_algo_time.values() for algo in layout_data.keys()))
    algos.sort()

    fig, ax = plt.subplots(figsize=(14, 7))
    x = np.arange(len(selected_layouts))
    width = 0.12
    multiplier = 0

    for algo in algos:
        offset = width * multiplier
        times = [layout_algo_time[layout].get(algo, 0) for layout in selected_layouts]
        ax.bar(x + offset, times, width, label=algo,
               color=COLORS.get(algo, "#95a5a6"), edgecolor='black', linewidth=0.8)
        multiplier += 1

    ax.set_xlabel("Layout", fontsize=12, fontweight='bold')
    ax.set_ylabel("Tiempo de ejecución (s)", fontsize=12, fontweight='bold')
    ax.set_title("Comparación de Tiempo de Ejecución por Layout",
                 fontsize=14, fontweight='bold')
    ax.set_xticks(x + width * (len(algos) - 1) / 2)
    ax.set_xticks(x)
    ax.set_xticklabels(selected_layouts, rotation=45, ha='right')
    ax.legend(loc='upper left', fontsize=9)
    plt.tight_layout()
    plt.savefig(output_dir / "tiempo_por_layout.png", dpi=300, bbox_inches='tight')
    plt.close()
    print("   ✓ tiempo_por_layout.png")

# ============================================================================
# Gráfica 4: Eficiencia de backwardSearch vs forwardBFS
# ============================================================================

print("4. Gráfica comparativa backwardSearch vs forwardBFS...")

forward_data = {}
backward_data = {}

for r in results:
    if r["success"] and not r.get("skipped", False):
        layout = r["layout"]
        if r["algorithm"] == "forwardBFS":
            forward_data[layout] = r["states_expanded"]
        elif r["algorithm"] == "backwardSearch":
            backward_data[layout] = r["states_expanded"]

# Solo layouts donde ambos tuvieron éxito
common_layouts = set(forward_data.keys()) & set(backward_data.keys())
common_layouts = sorted(list(common_layouts))

if common_layouts:
    forward_vals = [forward_data[l] for l in common_layouts]
    backward_vals = [backward_data[l] for l in common_layouts]

    x = np.arange(len(common_layouts))
    width = 0.35

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.bar(x - width/2, forward_vals, width, label='forwardBFS',
           color=COLORS["forwardBFS"], edgecolor='black', linewidth=1.2)
    ax.bar(x + width/2, backward_vals, width, label='backwardSearch',
           color=COLORS["backwardSearch"], edgecolor='black', linewidth=1.2)

    ax.set_xlabel("Layout", fontsize=12, fontweight='bold')
    ax.set_ylabel("Estados expandidos", fontsize=12, fontweight='bold')
    ax.set_title("Comparación de Eficiencia: Forward vs Backward Search",
                 fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(common_layouts, rotation=45, ha='right')
    ax.legend(fontsize=11)
    ax.set_yscale('log')
    plt.tight_layout()
    plt.savefig(output_dir / "forward_vs_backward.png", dpi=300, bbox_inches='tight')
    plt.close()
    print("   ✓ forward_vs_backward.png")

# ============================================================================
# Gráfica 5: Tasa de éxito por algoritmo
# ============================================================================

print("5. Gráfica de tasa de éxito por algoritmo...")

algo_stats = {}
for r in results:
    if not r.get("skipped", False):
        algo = r["algorithm"]
        if algo not in algo_stats:
            algo_stats[algo] = {"success": 0, "timeout": 0, "failed": 0}
        if r["success"]:
            algo_stats[algo]["success"] += 1
        elif r.get("timeout", False):
            algo_stats[algo]["timeout"] += 1
        else:
            algo_stats[algo]["failed"] += 1

if algo_stats:
    algos = sorted(algo_stats.keys())
    success_counts = [algo_stats[a]["success"] for a in algos]
    timeout_counts = [algo_stats[a]["timeout"] for a in algos]
    failed_counts = [algo_stats[a]["failed"] for a in algos]

    fig, ax = plt.subplots(figsize=(12, 6))
    x = np.arange(len(algos))
    width = 0.6

    p1 = ax.bar(x, success_counts, width, label='Exitosas',
                color='#2ecc71', edgecolor='black', linewidth=1.2)
    p2 = ax.bar(x, timeout_counts, width, bottom=success_counts, label='Timeouts',
                color='#f39c12', edgecolor='black', linewidth=1.2)
    p3 = ax.bar(x, failed_counts, width,
                bottom=[success_counts[i] + timeout_counts[i] for i in range(len(algos))],
                label='Fallidas', color='#e74c3c', edgecolor='black', linewidth=1.2)

    ax.set_xlabel("Algoritmo", fontsize=12, fontweight='bold')
    ax.set_ylabel("Número de ejecuciones", fontsize=12, fontweight='bold')
    ax.set_title("Tasa de Éxito por Algoritmo", fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(algos, rotation=45, ha='right')
    ax.legend(fontsize=11)
    plt.tight_layout()
    plt.savefig(output_dir / "tasa_exito.png", dpi=300, bbox_inches='tight')
    plt.close()
    print("   ✓ tasa_exito.png")

# ============================================================================
# Gráfica 6: Problemas simples vs multi-paciente (HTN vs otros)
# ============================================================================

print("6. Gráfica de rendimiento en problemas multi-paciente...")

multi_results = [r for r in results if "Multi" in r["layout"] or "duo" in r["layout"].lower()]

algo_multi_success = {}
for r in multi_results:
    if not r.get("skipped", False):
        algo = r["algorithm"]
        if algo not in algo_multi_success:
            algo_multi_success[algo] = {"success": 0, "total": 0}
        algo_multi_success[algo]["total"] += 1
        if r["success"]:
            algo_multi_success[algo]["success"] += 1

if algo_multi_success:
    algos = sorted(algo_multi_success.keys())
    success_rates = [
        100 * algo_multi_success[a]["success"] / algo_multi_success[a]["total"]
        for a in algos
    ]

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(range(len(algos)), success_rates,
                  color=[COLORS.get(a, "#95a5a6") for a in algos],
                  edgecolor='black', linewidth=1.2)

    # Resaltar HTN
    for i, algo in enumerate(algos):
        if "HTN" in algo:
            bars[i].set_color('#1abc9c')
            bars[i].set_linewidth(2.5)

    ax.set_xlabel("Algoritmo", fontsize=12, fontweight='bold')
    ax.set_ylabel("Tasa de éxito (%)", fontsize=12, fontweight='bold')
    ax.set_title("Rendimiento en Problemas Multi-Paciente", fontsize=14, fontweight='bold')
    ax.set_xticks(range(len(algos)))
    ax.set_xticklabels(algos, rotation=45, ha='right')
    ax.set_ylim(0, 105)
    ax.axhline(y=50, color='red', linestyle='--', linewidth=1, alpha=0.5)
    plt.tight_layout()
    plt.savefig(output_dir / "multi_paciente_exito.png", dpi=300, bbox_inches='tight')
    plt.close()
    print("   ✓ multi_paciente_exito.png")

# ============================================================================
# Gráfica 7: Heatmap de rendimiento
# ============================================================================

print("7. Gráfica heatmap de tiempo de ejecución...")

# Crear matriz layout x algoritmo
layouts_list = sorted(set(r["layout"] for r in results if not r.get("skipped", False)))
algos_list = sorted(set(r["algorithm"] for r in results if not r.get("skipped", False)))

matrix = np.zeros((len(layouts_list), len(algos_list)))
for i, layout in enumerate(layouts_list):
    for j, algo in enumerate(algos_list):
        for r in results:
            if r["layout"] == layout and r["algorithm"] == algo and not r.get("skipped", False):
                if r["success"]:
                    matrix[i, j] = r["execution_time"]
                elif r.get("timeout", False):
                    matrix[i, j] = -1  # Marcador especial para timeout
                else:
                    matrix[i, j] = -2  # Marcador para falla
                break

# Aplicar log solo a valores positivos
matrix_display = np.copy(matrix)
matrix_display[matrix_display > 0] = np.log10(matrix_display[matrix_display > 0] + 1)

fig, ax = plt.subplots(figsize=(14, 10))
im = ax.imshow(matrix_display, cmap='YlOrRd', aspect='auto')

ax.set_xticks(np.arange(len(algos_list)))
ax.set_yticks(np.arange(len(layouts_list)))
ax.set_xticklabels(algos_list, rotation=45, ha='right')
ax.set_yticklabels(layouts_list)

# Añadir texto en cada celda
for i in range(len(layouts_list)):
    for j in range(len(algos_list)):
        val = matrix[i, j]
        if val > 0:
            text = f"{val:.2f}s"
            color = "white" if matrix_display[i, j] > matrix_display[matrix_display > 0].mean() else "black"
        elif val == -1:
            text = "TIMEOUT"
            color = "blue"
        elif val == -2:
            text = "FALLÓ"
            color = "red"
        else:
            text = ""
            color = "black"

        if text:
            ax.text(j, i, text, ha="center", va="center", color=color, fontsize=7, weight='bold')

ax.set_title("Heatmap de Tiempo de Ejecución por Layout y Algoritmo",
             fontsize=14, fontweight='bold', pad=20)
plt.colorbar(im, ax=ax, label="log10(Tiempo + 1)")
plt.tight_layout()
plt.savefig(output_dir / "heatmap_rendimiento.png", dpi=300, bbox_inches='tight')
plt.close()
print("   ✓ heatmap_rendimiento.png")

# ============================================================================
# Resumen
# ============================================================================

print("\n" + "="*70)
print("GRÁFICAS GENERADAS")
print("="*70)
print(f"\nTodas las gráficas se guardaron en: {output_dir}/")
print("\nArchivos generados:")
for img in sorted(output_dir.glob("*.png")):
    print(f"  - {img.name}")

print("\n" + "="*70)
print("Próximo paso: revisar las gráficas y crear resultados_punto_6.md")
print("="*70)
