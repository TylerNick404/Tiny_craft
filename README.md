# ◼️ TINY-CRAFT v1.5.0 ◼️ 

## DESCRIPTION:
TINY-craft is a lightweight, first-person sandbox game built in Python using the Ursina Engine. It provides a simple voxel building environment inspired by Minecraft, scaled down into an optimized, lightweight build. 

The game features procedurally generated terrain, automatic real-time environment changes, and a fully functional save system.

### 🌟 What's New in v1.5.0:
* **Procedural Terrain Generation:** Generates natural hills and valleys using Perlin Noise instead of flat terrain, complete with randomized Oak and Birch tree generation.
* **Combined Chunk Mesh Rendering:** Divides the 96x96 world into 16x16 chunks. It utilizes chunk combining and caching techniques to render blocks as a single unified mesh, keeping draw calls low and maintaining high frame rates.
* **Persistent Saving & Loading:** Your creations are no longer just saved to text logs! The game features a fully integrated save system that reads and writes your world state directly to a local JSON file (`world_save.json`), preserving your builds between game sessions.
* **Dynamic Time of Day:** Automatically reads your system clock on startup to load either a bright day theme or an atmospheric night theme with adapted textures and a custom skybox.
* **Stable Shading & Optimization:** Features coordinate-seeded block shading to eliminate visual flickering during block placement/removal, along with standardized asset paths for full compatibility across Windows, macOS, and Linux.

---

## SCREENSHOTS:
<img src="https://github.com/TylerNick404/Tiny_craft/blob/main/Assets/screenshots/1.png" width="800">
<img src="https://github.com/TylerNick404/Tiny_craft/blob/main/Assets/screenshots/2.png" width="800">
<img src="https://github.com/TylerNick404/Tiny_craft/blob/main/Assets/screenshots/3.png" width="800">

---

## CONTROLS:

### Player & Interaction
* **WASD** - Move around
* **Space** - Jump
* **Left Ctrl** - Crouch (slow movement, slides under 1-block gaps)
* **Left Click** - Place held block
* **Right Click** - Mine / Break targeted block

### System & Interface
* **1 to 0** - Hotbar block selection (10 total block types)
* **H** - Toggle block list HUD overlay
* **M** - Toggle background music (Mute / Unmute)
* **F** - Toggle FPS and performance counter
* **R** - Respawn at map center
* **G** - Exit fullscreen mode
* **ESC** - Exit game

---

## USAGE & RUNNING:

### Prerequisites:
To run this game, you must have Python installed on your system. You will also need `git` and `pip` configured.

### 1. Clone the repository:
```bash
git clone https://github.com/TylerNick404/Tiny_craft.git
cd Tiny_craft
```
### 2. Install dependencies:
```bash
pip install -r requirements.txt
```

### 3. Run the game:
```bash
python Tiny-craft.py
```
