"""Aplica los cambios de Cenizo (ayudante) sobre TU states/new_game.py.

Uso (desde la raiz del proyecto):
    python aplicar_cenizo.py                 # usa states/new_game.py
    python aplicar_cenizo.py ruta/new_game.py

No cambia nada mas de tu archivo (posiciones, textos de otros pasos, etc.).
Guarda una copia en new_game.py.bak antes de modificar.
"""
import shutil
import sys

path = sys.argv[1] if len(sys.argv) > 1 else "states/new_game.py"

with open(path, encoding="utf-8") as f:
    s = f.read()

if "self.companion = Companion" in s:
    print("Ya estaba aplicado. No se cambia nada.")
    sys.exit(0)

CAMBIOS = []


def rep(old, new):
    global s
    if s.count(old) != 1:
        print(f"ERROR: no encontre (o hay varias) esta parte:\n{old[:80]!r}")
        print("No se modifico nada.")
        sys.exit(1)
    CAMBIOS.append((old, new))


rep("from ui.guide import Guide\n",
    "from ui.guide import Guide\n"
    "from ui.companion import Companion\n"
    "from ui.tutorial_texts import apply_texts\n")

rep("        objective_list = self._build_objectives()\n",
    "        objective_list = self._build_objectives()\n"
    "\n"
    "        # textos, consejos y festejos de Cenizo (ui/tutorial_texts.py)\n"
    "        apply_texts(\n"
    "            objective_list,\n"
    "            countdown=int(NO_LIGHT_COUNTDOWN),\n"
    "            antorcha_wave=SHOP_UNLOCK_WAVES[\"antorcha\"],\n"
    "            creatures=len(EnemyEncyclopedia.ORDER),\n"
    "        )\n")

rep("        self.guide = Guide()\n",
    "        self.guide = Guide()\n"
    "        self.companion = Companion((self.width, self.height))\n"
    "        self._comp_cheered = None\n")

rep('''            elif action in SLOT_ACTIONS:
                name = "slotkey"
''', '''            elif action in ("potion1", "potion2"):
                name = "potkey"

            elif action in SLOT_ACTIONS:
                name = "slotkey"
''')

rep('("Teclas 5 y 6 (pociones)", "slotkey" in g.tuto_flags),',
    '("Teclas 5 y 6 (pociones)", "potkey" in g.tuto_flags),')

rep('''        self.show_message("Tutorial sacado")
''', '''        self.companion.phase = None
        self.companion.priority = 0

        self.show_message("Tutorial sacado")
''')

rep('''            else:

                self._tuto_step_check()

                self.guide.update(dt)

            if self.objectives is not None and self.objectives.finished:

                self._objective_saved = 10 ** 6

                self.objectives = None
''', '''            else:

                self._tuto_step_check()

                self.guide.update(dt)

                self._companion_step(dt)

            if self.objectives is not None and self.objectives.finished:

                # si termino jugando (no por K ni al cargar), Cenizo se despide
                if self.objectives.started and tutorial_hints():
                    self.companion.farewell()

                self._objective_saved = 10 ** 6

                self.objectives = None

        self.companion.update(dt)
''')

rep('''    def _draw_guidance(self):
''', '''    def _companion_step(self, dt):
        """Cenizo festeja los objetivos, da una mano si te trabas y avisa
        si tu luz esta baja."""

        obj = self.objectives

        if (
            obj is None or not obj.started
            or obj.index >= len(obj.objectives)
            or not tutorial_hints()
        ):
            return

        step = obj.objectives[obj.index]

        if obj.phase == "done":

            if self._comp_cheered != obj.index:

                self._comp_cheered = obj.index

                self.companion.cheer(step.get("cheer"))
                self.companion.reset_stuck()

            return

        if (
            self.state == "playing"
            and self.tutorial is None
            and self.pause_view is None
            and self.shop is None
            and self.minigame is None
        ):
            self.companion.observe(dt, self, obj.index, step)

    def _draw_guidance(self):
''')

rep('''            self._draw_guidance()

            self.zone_banner.draw(self.screen)
''', '''            self._draw_guidance()

            if (
                self.tutorial is None
                and self.shop is None
                and self.minigame is None
                and self.pause_view is None
            ):
                self.companion.draw(self.screen)

            self.zone_banner.draw(self.screen)
''')

for old, new in CAMBIOS:
    s = s.replace(old, new)

shutil.copyfile(path, path + ".bak")

with open(path, "w", encoding="utf-8") as f:
    f.write(s)

print(f"Listo: {len(CAMBIOS)} cambios aplicados a {path}")
print(f"Copia de seguridad: {path}.bak")