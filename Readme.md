# Keep It Lit

De que trata?

Te despertas en un mundo oscuro con una pequeña luz en la mano. Tu luz es tu vida: la barra naranja se gasta con el tiempo y con cada golpe que das. Si se apaga, tenes 10 segundos para conseguir otra o si no perdes

Para sobrevivir tenes que:

Explorar la cabaña y las salas buscando luces (fosforo, vela, antorcha) y objetos que alimentan tu llama
Pelear contra enemigos en oleadas, usando tu propia luz como arma
Juntar monedas y gemas para comprar mejoras en la tienda
Abrir puertas y cofres para llegar a zonas nuevas

Hay dos modos: en Normal perdés tus objetos al morir, y en Hardcore se borra toda la partida

**Versión 0.2.0**

## Integrantes

- Lautaro Anabia
- Anthony Romero
- Benjamin Zhang

## Como ejecutarlo

Necesitás Python 3.9+ y Pygame 2.x.


run_game.py


## Controles

| Acción | Tecla |
|---|---|
| Moverse | `W` `A` `S` `D` |
| Atacar | Click izquierdo o `Espacio` |
| Agarrar / soltar | `E` / `Q` |
| Elegir casillero | `1`-`4`, `5` (luz) o rueda del mouse |
| Usar objeto | `F` o click derecho |
| Cambiar golpe (antorcha) | `G` |
| Imán | `O` |
| Pausa | `Esc` |
| Tutorial | `F1` |

## Estructura

```
main.py     # Punto de entrada
core/       # Guardado, logros y audio
states/     # Menús y partida
world/      # Enemigos, luces, puertas, cofres y tienda
player/     # Movimiento y animación
ui/         # HUD, tutorial y objetivos
data/       # Configuración en JSON
assets/     # Imágenes y sonidos

```