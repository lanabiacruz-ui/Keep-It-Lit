"""Logica del inventario personalizado de la tienda (sin pygame).

La tienda arma un "plan" de compra con la misma forma que el HUD:

    casilleros 0..N-1        -> hotbar de items
    casilleros N..N+P-1      -> hotbar de pociones
    ultimo casillero         -> la luz

Cada casillero del plan es None o [item_id, cantidad]. La cantidad del plan
puede ser mayor que lo que entra en un casillero real: al comprar entra una
pila en el inventario y el resto sale por la boca del vendedor al piso.

Este modulo no depende de pygame para poder usarse (y probarse) desde
cualquier lado: la vista previa de la tienda y la compra real de la partida
usan exactamente las mismas funciones, asi nunca se contradicen.
"""

KIND_ITEM = "item"
KIND_POTION = "potion"
KIND_LIGHT = "light"

# Maximo que se puede pedir por casillero en una compra
MAX_PLAN_ITEM = 55
MAX_PLAN_POTION = 5
MAX_PLAN_LIGHT = 1


def plan_cap(kind):
    """Cantidad maxima que se puede pedir en un casillero de ese tipo."""

    if kind == KIND_LIGHT:
        return MAX_PLAN_LIGHT

    if kind == KIND_POTION:
        return MAX_PLAN_POTION

    return MAX_PLAN_ITEM


def total_slots(n_items, n_potions):

    return n_items + n_potions + 1


def light_index(n_items, n_potions):

    return n_items + n_potions


def slot_kind(n, n_items, n_potions):
    """Tipo de casillero que es la posicion n del plan."""

    if n < n_items:
        return KIND_ITEM

    if n < n_items + n_potions:
        return KIND_POTION

    return KIND_LIGHT


def kind_range(kind, n_items, n_potions):
    """(desde, hasta) de las posiciones del plan para ese tipo."""

    if kind == KIND_ITEM:
        return 0, n_items

    if kind == KIND_POTION:
        return n_items, n_items + n_potions

    return n_items + n_potions, n_items + n_potions + 1


def migrate_raw(raw, n_items, n_potions):
    """Pasa una lista guardada al formato actual.

    Las partidas viejas guardaban [items..., luz] sin casilleros de
    pociones: se les insertan vacios para que la luz siga siendo la luz.
    """

    raw = list(raw or [])

    if len(raw) == n_items + 1:
        raw = raw[:n_items] + [None] * n_potions + [raw[n_items]]

    total = total_slots(n_items, n_potions)

    raw = raw[:total]
    raw += [None] * (total - len(raw))

    return raw


def sanitize_draft(raw, n_items, n_potions, kind_of, allowed):
    """Devuelve un plan limpio (largo fijo) a partir de cualquier cosa.

    kind_of(item_id) -> KIND_*     allowed(item_id) -> bool

    Descarta lo que no esta permitido (bloqueado, skins, bolsa...), lo que
    esta en un casillero de otro tipo y limita las cantidades.
    """

    slots = [None] * total_slots(n_items, n_potions)

    for n, entry in enumerate(migrate_raw(raw, n_items, n_potions)):

        try:
            item_id, qty = entry[0], int(entry[1])
        except (TypeError, ValueError, IndexError, KeyError):
            continue

        if not allowed(item_id):
            continue

        kind = kind_of(item_id)

        if kind != slot_kind(n, n_items, n_potions):
            continue

        qty = min(qty, plan_cap(kind))

        if qty > 0:
            slots[n] = [item_id, qty]

    return slots


def plan_delivery(
    draft, held_items, held_counts, n_items, n_potions, limit_of, kind_of
):
    """Reparte lo comprado entre el inventario y el piso.

    Por cada casillero del plan entra como mucho UNA pila (limit_of) en el
    inventario real: primero completa pilas que ya tengas del mismo item y
    despues usa casilleros libres (el mismo del plan si esta libre). Todo
    lo demas cae al piso.

    held_items / held_counts: lo que llevas puesto (largo n_items+n_potions).

    Devuelve un dict:
        items, counts  -> como queda el inventario real
        drops          -> lista de item_id que caen al piso (uno por unidad)
        light          -> id de la luz comprada o None
        per_slot       -> {posicion del plan: (a_inventario, al_piso)}
    """

    hud_total = n_items + n_potions

    items = list(held_items)[:hud_total]
    items += [None] * (hud_total - len(items))

    counts = [int(c) for c in list(held_counts)[:hud_total]]
    counts += [0] * (hud_total - len(counts))

    drops = []
    per_slot = {}
    light = None

    for n, slot in enumerate(draft):

        if not slot:
            continue

        item_id, qty = slot[0], int(slot[1])

        if qty <= 0:
            continue

        kind = kind_of(item_id)

        if kind == KIND_LIGHT:
            light = item_id
            per_slot[n] = (1, 0)
            continue

        lo, hi = kind_range(kind, n_items, n_potions)

        limit = max(1, int(limit_of(item_id)))

        left = min(qty, limit)
        wanted = left

        for i in range(lo, hi):

            if left <= 0:
                break

            if items[i] == item_id and counts[i] < limit:

                take = min(left, limit - counts[i])

                counts[i] += take
                left -= take

        # primero el mismo casillero que armaste en la tienda (si esta
        # libre), asi lo que ordenas es lo que recibis
        order = list(range(lo, hi))

        if lo <= n < hi:
            order.remove(n)
            order.insert(0, n)

        for i in order:

            if left <= 0:
                break

            if items[i] is None or counts[i] <= 0:

                take = min(left, limit)

                items[i] = item_id
                counts[i] = take
                left -= take

        placed = wanted - left
        floor = qty - placed

        drops.extend([item_id] * floor)

        per_slot[n] = (placed, floor)

    return {
        "items": items,
        "counts": counts,
        "drops": drops,
        "light": light,
        "per_slot": per_slot,
    }