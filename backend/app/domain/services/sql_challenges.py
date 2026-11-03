"""Original basic SQL tasks and synthetic datasets; never use the application database."""
TABLES = {"customers": ["id", "name"], "orders": ["id", "customer_id", "total", "status"]}
DATASETS = [
    {"customers": [[1, "Ana"], [2, "Luis"], [3, "Maya"]], "orders": [[1, 1, 100, "paid"], [2, 1, 50, "paid"], [3, 2, 200, "pending"], [4, 3, 90, "paid"]]},
    {"customers": [[10, "Noa"], [20, "Iván"], [30, "Sara"], [40, "Sol"]], "orders": [[10, 10, 99, "paid"], [20, 20, 100, "paid"], [30, 30, 75, "paid"], [40, 30, 75, "paid"], [50, 10, 500, "cancelled"]]},
    {"customers": [[7, "Sin pedidos"], [8, "Solo pendientes"]], "orders": [[6, 8, 500, "pending"]]},
]

CHALLENGES = {
    "sql-paid-totals-v1": {
        "title": "Totales de pedidos pagados", "skill": "sql", "version": "1", "minutes": 15,
        "prompt": "Devuelve una fila por cliente cuyo total de pedidos con status='paid' sea al menos 100. Devuelve su nombre como customer y la suma como total. No incluyas pedidos pendientes o cancelados. El orden de las filas no importa. Debe funcionar con otros datos, sin escribir resultados fijos.",
        "columns": ["customer", "total"], "datasets": DATASETS,
        "expected": [[["Ana", 150]], [["Iván", 100], ["Sara", 150]], []],
    },
    "sql-paid-counts-v1": {
        "title": "Clientes sin pedidos pagados", "skill": "sql", "version": "1", "minutes": 15,
        "prompt": "Devuelve todos los clientes, incluso quienes no tienen pedidos pagados. Devuelve su nombre como customer y la cantidad de pedidos con status='paid' como paid_orders, usando cero cuando corresponda. El orden de las filas no importa. Debe funcionar con otros datos, sin escribir resultados fijos.",
        "columns": ["customer", "paid_orders"], "datasets": DATASETS,
        "expected": [[["Ana", 2], ["Luis", 0], ["Maya", 1]], [["Noa", 1], ["Iván", 1], ["Sara", 2], ["Sol", 0]], [["Sin pedidos", 0], ["Solo pendientes", 0]]],
    },
    "sql-paid-average-v1": {
        "title": "Informe de totales y promedios", "skill": "sql", "version": "1", "minutes": 15,
        "prompt": "Devuelve todos los clientes, incluso sin pedidos pagados: nombre como customer, suma de pedidos con status='paid' como paid_total y promedio de esos pedidos, redondeado a dos decimales, como paid_average. Usa cero en ambas métricas si no hay pedidos pagados. El orden no importa; no escribas resultados fijos.",
        "columns": ["customer", "paid_total", "paid_average"], "datasets": DATASETS,
        "expected": [[["Ana", 150, 75], ["Luis", 0, 0], ["Maya", 90, 90]],
                     [["Noa", 99, 99], ["Iván", 100, 100], ["Sara", 150, 75], ["Sol", 0, 0]],
                     [["Sin pedidos", 0, 0], ["Solo pendientes", 0, 0]]],
    },
    "sql-latest-order-v1": {
        "title": "Último pedido por cliente", "skill": "sql", "version": "1", "minutes": 15,
        "prompt": "Devuelve el pedido con mayor id de cada cliente que tenga pedidos, sin filtrar por estado. Columnas: nombre del cliente como customer, id del pedido como last_order, importe como total y estado como status. Omite clientes sin pedidos. El orden no importa; debe funcionar con otros datos.",
        "columns": ["customer", "last_order", "total", "status"], "datasets": DATASETS,
        "expected": [[["Ana", 2, 50, "paid"], ["Luis", 3, 200, "pending"], ["Maya", 4, 90, "paid"]],
                     [["Noa", 50, 500, "cancelled"], ["Iván", 20, 100, "paid"], ["Sara", 40, 75, "paid"]],
                     [["Solo pendientes", 6, 500, "pending"]]],
    },
}


def catalog():
    return [{key: bank[key] for key in ("title", "skill", "minutes")} | {"id": challenge_id} for challenge_id, bank in CHALLENGES.items()]
