# Punto 3d: Comparacion entre busqueda regresiva y busqueda hacia adelante

## Pregunta

Compare el numero de estados u objetivos explorados por la busqueda regresiva contra la busqueda hacia adelante en los mismos layouts. Indique en que tipos de problemas se espera que la busqueda regresiva sea mas eficiente.

## Resultados empiricos

Las pruebas se realizaron con `SimpleRescueProblem` sobre dos layouts de `layouts/simple/`, usando los planificadores `forwardBFS` y `backwardSearch`.

| Layout | Planificador | Estados/objetivos expandidos | Longitud del plan |
|--------|--------------|-------------------------------|-------------------|
| `tinyBase` | `forwardBFS` | 345 estados | 9 acciones |
| `tinyBase` | `backwardSearch` | 9 objetivos | 9 acciones |
| `smallRescue` | `forwardBFS` | 1427 estados | 23 acciones |
| `smallRescue` | `backwardSearch` | 46 objetivos | 23 acciones |

En ambos casos, la busqueda regresiva encontro planes de la misma longitud que la busqueda hacia adelante, pero expandio una cantidad mucho menor de nodos. En `tinyBase`, paso de 345 estados expandidos a 9 objetivos expandidos. En `smallRescue`, paso de 1427 estados expandidos a 46 objetivos expandidos.

## Analisis

La diferencia se explica por la direccion de la busqueda. `forwardBFS` empieza desde el estado inicial y expande todas las acciones aplicables en cada estado. Esto incluye muchas acciones que son validas pero que no contribuyen directamente al objetivo final, por ejemplo movimientos hacia celdas que no acercan al robot a los suministros, al paciente o al puesto medico.

En cambio, `backwardSearch` empieza desde el objetivo, por ejemplo `Rescued(patient_0)`, y solo considera acciones relevantes para lograr algun fluente pendiente. La regresion usa la regla:

```text
REGRESS(g, a) = (g - ADD(a)) U PRECOND(a)
```

siempre que la accion agregue algun fluente del objetivo y no borre ningun fluente requerido. Por eso, desde `Rescued(patient_0)` la busqueda se concentra primero en acciones como `Rescue`, luego en las precondiciones necesarias para rescatar, como que el paciente este en el puesto medico, que los suministros esten listos y que el robot este en la ubicacion correcta. Esto reduce el factor de ramificacion porque descarta acciones aplicables que no ayudan a satisfacer el objetivo actual.

## Cuando es mas eficiente la busqueda regresiva

La busqueda regresiva tiende a ser mas eficiente cuando:

- El objetivo es especifico y tiene pocos fluentes, como `Rescued(patient_0)`.
- Hay muchas acciones aplicables desde el estado inicial, pero pocas son relevantes para alcanzar el objetivo.
- Las acciones tienen efectos positivos claros que permiten identificar facilmente que operadores pueden lograr cada subobjetivo.
- El dominio tiene una estructura causal marcada, como en este proyecto: para rescatar primero deben cumplirse precondiciones como mover al paciente, preparar suministros y ubicarse en el puesto medico.

En cambio, puede ser menos ventajosa cuando el objetivo es muy amplio, cuando muchos operadores pueden lograr los mismos fluentes, o cuando la regresion genera muchos subobjetivos alternativos dificiles de satisfacer. En esos casos, el espacio de objetivos regresados puede crecer de forma similar o incluso peor que el espacio de estados hacia adelante.

## Conclusion

Para los layouts probados, la busqueda regresiva fue mas eficiente que `forwardBFS` porque aprovecho la informacion del objetivo para explorar solo acciones relevantes. Esto redujo drasticamente el numero de nodos expandidos sin aumentar la longitud del plan encontrado.
