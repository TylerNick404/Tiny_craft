# import modules
from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from perlin_noise import PerlinNoise
from math import floor
import os
import random
import json
from datetime import datetime

# detect the time
now = datetime.now().time()
hour = now.hour

# run game
game = Ursina()

# Create a parent entity
root = Entity()

# Load textures (Standardized to lowercase paths for cross-platform compatibility)
grass_texture = load_texture('assets/block_tex/grass.jpg')
stone_texture = load_texture('assets/block_tex/stone.png')
brick_texture = load_texture('assets/block_tex/brick.png')
dirt_texture = load_texture('assets/block_tex/dirt.png')
wood_texture = load_texture('assets/block_tex/wood_block.png')
glass_texture = load_texture('assets/block_tex/glass1.png')
obsidan_texture = load_texture('assets/block_tex/obsidan.png')
ice_texture = load_texture('assets/block_tex/ice.png')
sand_texture = load_texture('assets/block_tex/sand.png')
white_stone_texture = load_texture('assets/block_tex/white_stone.png')
hand_texture = load_texture("assets/block_tex/Hand_Texture.png")

# Load log and leaf textures for tree generation
oak_log_texture = load_texture('assets/block_tex/wood')
birch_log_texture = load_texture('assets/block_tex/birch_log')
leaf_texture = load_texture('assets/block_tex/leaf')
leaf2_texture = load_texture('assets/block_tex/leaf2')

# Load Audios
put_sound = Audio('assets/sound/put', loop=False, autoplay=False)
crack_sound = Audio('assets/sound/crack', loop=False, autoplay=False)
glass_sound = Audio('assets/sound/glass_break', loop=False, autoplay=False)
backmus = Audio('assets/sound/Minecraft.mp3', loop=True, autoplay=True)
backmus.play()

# default block
block_pick = 4

# sky texture
sky_texture = 'assets/time/day.png'

# detect the time
pod = "day"

if hour >= 6 and hour < 20:
    print("Day started!")
else:
    print("Night started!")
    pod = "night"
    grass_texture = load_texture('assets/night_tex/grass.jpg')
    stone_texture = load_texture('assets/night_tex/stone.png')
    brick_texture = load_texture('assets/night_tex/brick.png')
    dirt_texture = load_texture('assets/night_tex/dirt.png')
    wood_texture = load_texture('assets/night_tex/wood_block.png')
    glass_texture = load_texture('assets/night_tex/glass1.png')
    obsidan_texture = load_texture('assets/night_tex/obsidan.png')
    ice_texture = load_texture('assets/night_tex/ice.png')
    sand_texture = load_texture('assets/night_tex/sand.png')
    white_stone_texture = load_texture('assets/night_tex/white_stone.png')
    
    oak_log_texture = load_texture('assets/night_tex/wood')
    birch_log_texture = load_texture('assets/night_tex/birch_log')
    leaf_texture = load_texture('assets/night_tex/leaf')
    leaf2_texture = load_texture('assets/night_tex/leaf2')

    sky_texture = 'assets/time/night.png'	

Sky(texture=sky_texture, parent=root)

# Texture lookup mappings for serialization
TEXTURES = {
    "grass": grass_texture,
    "stone": stone_texture,
    "brick": brick_texture,
    "dirt": dirt_texture,
    "wood": wood_texture,
    "glass": glass_texture,
    "obsidian": obsidan_texture,
    "ice": ice_texture,
    "sand": sand_texture,
    "white_stone": white_stone_texture,
    "oak_log": oak_log_texture,
    "birch_log": birch_log_texture,
    "leaf": leaf_texture,
    "leaf2": leaf2_texture
}

BLOCK_KEYS = {
    1: "grass",
    2: "stone",
    3: "brick",
    4: "dirt",
    5: "wood",
    6: "glass",
    7: "obsidian",
    8: "ice",
    9: "sand",
    10: "white_stone"
}

# --- SAVE/LOAD SYSTEM CONFIGURATION ---
SAVE_FILE = "world_save.json"
world_data = {"placed": {}, "removed": []}

if os.path.exists(SAVE_FILE):
    try:
        with open(SAVE_FILE, "r") as sf:
            world_data = json.load(sf)
    except (json.JSONDecodeError, ValueError):
        pass

# Fallback structure initialization
if "placed" not in world_data:
    world_data["placed"] = {}
if "removed" not in world_data:
    world_data["removed"] = []

# Convert 'removed' to a Python set for high-speed lookups during map building
removed_set = set(world_data["removed"])

def save_world():
    world_data["removed"] = list(removed_set)
    with open(SAVE_FILE, "w") as sf:
        json.dump(world_data, sf)

# window settings
window.entity_counter.enabled = False
window.collider_counter.enabled = False
window.fullscreen = True
window.exit_button.enabled = False
window.fps_counter.enabled = False
window.cog_button.enabled = False
window.title = 'TINY-craft 1.5.0 version'


# --- CHUNK SETUP & CORE ENGINE ---
CHUNK_SIZE = 16
chunks = {}       # Dictionary to store combined chunk sub-mesh structures: {(cx, cz): [Entities]}
world_blocks = {} # Structured by chunk: {(cx, cz): {(x, y, z): texture_key}}

# Optimization variables
cull_frame_counter = 0
CHUNK_RENDER_DIST = 1  # Radius of 1 chunk (renders a 3x3 chunk area around player)

# Crouching state tracking
crouching = False

# Block list HUD variables
hide_timer = None


# --- MEMORY HELPER FUNCTIONS ---
def add_block_to_memory(bx, by, bz, tex_key):
    cx = floor(bx / CHUNK_SIZE)
    cz = floor(bz / CHUNK_SIZE)
    if (cx, cz) not in world_blocks:
        world_blocks[(cx, cz)] = {}
    world_blocks[(cx, cz)][(bx, by, bz)] = tex_key

def remove_block_from_memory(bx, by, bz):
    cx = floor(bx / CHUNK_SIZE)
    cz = floor(bz / CHUNK_SIZE)
    if (cx, cz) in world_blocks:
        if (bx, by, bz) in world_blocks[(cx, cz)]:
            del world_blocks[(cx, cz)][(bx, by, bz)]
            if not world_blocks[(cx, cz)]:
                del world_blocks[(cx, cz)]


# --- CHUNK REBUILD SYSTEM ---
def rebuild_chunk(cx, cz):
    # 1. Clean up existing visual meshes inside this chunk if they exist
    if (cx, cz) in chunks:
        for sub_mesh in chunks[(cx, cz)]:
            destroy(sub_mesh)
        del chunks[(cx, cz)]

    chunks[(cx, cz)] = []

    # 2. Retrieve blocks belonging strictly to this chunk
    blocks_in_chunk = world_blocks.get((cx, cz), {})
    if not blocks_in_chunk:
        return

    # Group chunk coordinates by their texture types
    chunk_blocks = {}
    for (bx, by, bz), tex_key in blocks_in_chunk.items():
        if tex_key not in chunk_blocks:
            chunk_blocks[tex_key] = []
        chunk_blocks[tex_key].append((bx, by, bz))

    # 3. Create a unified combined mesh parent for each unique texture type in the chunk
    for tex_key, coords in chunk_blocks.items():
        tex = TEXTURES.get(tex_key, grass_texture)
        
        # Explicitly assign the texture to the parent chunk BEFORE combining so it is preserved
        sub_parent = Entity(model=None, collider=None, texture=tex)
        
        # Instantiate children representing individual blocks
        for bx, by, bz in coords:
            # Seed a local random instance based on coordinate to ensure consistent block shading
            block_seed = int(bx * 73856093 ^ by * 19349663 ^ bz * 83492791)
            local_rand = random.Random(block_seed)
            r = local_rand.uniform(0.85, 1.0)
            g = local_rand.uniform(0.85, 1.0)
            b = local_rand.uniform(0.85, 1.0)

            Entity(
                parent=sub_parent,
                model='cube',
                position=Vec3(bx, by, bz),
                texture=tex,
                color=color.Color(r, g, b, 1)
            )
            
        # Merge individual meshes together into a single master mesh and delete temporary children
        sub_parent.combine(auto_destroy=True)
        sub_parent.collider = 'mesh' # Generate mesh collider so player can stand on and interact with it
        chunks[(cx, cz)].append(sub_parent)


# --- CROUCH CONTROLLER FUNCTIONS ---
def crouch_player():
    global crouching
    if crouching:
        return
    crouching = True
    player.height = 1.0          
    player.camera_pivot.y = 1.0  
    player.speed = 2.5           

def uncrouch_player():
    global crouching
    if not crouching:
        return
    crouching = False
    player.height = 2.0          
    player.camera_pivot.y = 2.0  
    player.speed = 5.0           

# --- JUMP OVERRIDE FUNCTION ---
def player_jump_override(self):
    if not self.grounded or crouching: 
        return
    
    head_pos = self.position + Vec3(0, self.height, 0)
    ceiling_ray = raycast(head_pos, Vec3(0, 1, 0), ignore=(self,), distance=self.jump_height)
    
    self.grounded = False
    self.jumping = True
    
    if ceiling_ray.hit:
        space_above = ceiling_ray.world_point.y - (self.y + self.height)
        safe_jump = max(0.0, space_above - 0.15)  
        self.animate_y(self.y + safe_jump, self.jump_up_duration * (safe_jump / self.jump_height), curve=curve.out_expo)
    else:
        self.animate_y(self.y + self.jump_height, self.jump_up_duration, curve=curve.out_expo)
        
    invoke(self.start_fall, delay=self.fall_after)

# --- VISUAL HELD BLOCK UPDATE ---
def update_held_block():
    tex_key = BLOCK_KEYS.get(block_pick, "dirt")
    held_block.texture = TEXTURES.get(tex_key, dirt_texture)

# --- BLOCK LIST HUD CONTROL ---
def hide_block_list():
    block_list_text.enabled = False

def show_block_list():
    global hide_timer
    block_list_text.enabled = True
    if hide_timer:
        hide_timer.kill()
    hide_timer = invoke(hide_block_list, delay=4.0)

# --- INSTANT INPUT EVENT LISTENER ---
def input(key):
    global block_pick, player

    if key in ('1', '2', '3', '4', '5', '6', '7', '8', '9', '0'):
        val = int(key)
        block_pick = 10 if val == 0 else val
        update_held_block()

    elif key == 'f':
        window.fps_counter.enabled = not window.fps_counter.enabled

    elif key == 'left control':
        crouch_player()

    elif key == 'h':
        show_block_list()

    elif key == 'r':
        player = FirstPersonController(x=25, z=25, y=25)
        player.jump = lambda: player_jump_override(player)
        uncrouch_player()

    elif key == 'm':
        backmus.stop()
    
    elif key == 'g':
        window.fullscreen = False
    
    elif key == 'escape':
        exit()

    # --- BLOCK PLACEMENT SYSTEM ---
    elif key == 'left mouse down':
        hit_info = raycast(camera.world_position, camera.forward, distance=5, ignore=(player,))
        if hit_info.hit:
            put_sound.play()

            # Find placement coordinates relative to surface hit normal using world coordinates
            spawn_pos = hit_info.world_point + hit_info.world_normal * 0.5
            spawn_pos = Vec3(round(spawn_pos.x), round(spawn_pos.y), round(spawn_pos.z))

            bx, by, bz = int(spawn_pos.x), int(spawn_pos.y), int(spawn_pos.z)
            tex_key = BLOCK_KEYS.get(block_pick, "dirt")
            pos_key = f"{bx},{by},{bz}"

            # Save coordinates to memory and storage
            add_block_to_memory(bx, by, bz, tex_key)
            world_data["placed"][pos_key] = tex_key
            save_world()

            # Rebuild chunk of placement coordinate
            rebuild_chunk(floor(spawn_pos.x / CHUNK_SIZE), floor(spawn_pos.z / CHUNK_SIZE))

    # --- BLOCK REMOVAL SYSTEM ---
    elif key == 'right mouse down':
        hit_info = raycast(camera.world_position, camera.forward, distance=5, ignore=(player,))
        if hit_info.hit:
            # Find center coordinate of the targeted block face using world coordinates
            block_pos = hit_info.world_point - hit_info.world_normal * 0.5
            block_pos = Vec3(round(block_pos.x), round(block_pos.y), round(block_pos.z))
            
            bx, by, bz = int(block_pos.x), int(block_pos.y), int(block_pos.z)
            cx = floor(bx / CHUNK_SIZE)
            cz = floor(bz / CHUNK_SIZE)

            # Check if block exists in memory before attempting removal
            if (cx, cz) in world_blocks and (bx, by, bz) in world_blocks[(cx, cz)]:
                # Play correct break audio depending on block type
                tex_key = world_blocks[(cx, cz)][(bx, by, bz)]
                if tex_key == "glass":
                    glass_sound.play()
                else:
                    crack_sound.play()

                # Remove from memory
                remove_block_from_memory(bx, by, bz)

                # Sync coordinate state with save files
                pos_key = f"{bx},{by},{bz}"
                if pos_key in world_data["placed"]:
                    del world_data["placed"][pos_key]
                removed_set.add(pos_key)
                save_world()

                # Rebuild chunk of the mined block
                rebuild_chunk(cx, cz)

def update():
    global cull_frame_counter, player, crouching

    if held_keys["left mouse"] or held_keys["right mouse"]:
        hand.active()
        held_block.active()   
    else:
        hand.passive()
        held_block.passive()  
    
    if crouching and not held_keys['left control']:
        ceiling_ray = raycast(player.position + Vec3(0, 0.1, 0), Vec3(0, 1, 0), ignore=(player,), distance=1.9)
        if not ceiling_ray.hit:
            uncrouch_player()

    # --- DYNAMIC CHUNK GENERATION & CACHING LOOP ---
    cull_frame_counter += 1
    if cull_frame_counter >= 15:  # Check player position every 15 frames
        cull_frame_counter = 0
        px, pz = player.x, player.z
        
        # Calculate which chunk coordinates the player is in
        pcx = floor(px / CHUNK_SIZE)
        pcz = floor(pz / CHUNK_SIZE)
        
        visible_chunks = set()
        
        # Identify chunks currently inside render range
        for dx in range(-CHUNK_RENDER_DIST, CHUNK_RENDER_DIST + 1):
            for dz in range(-CHUNK_RENDER_DIST, CHUNK_RENDER_DIST + 1):
                cx = pcx + dx
                cz = pcz + dz
                # Ensure we only track chunks inside map boundaries
                if 0 <= cx < (terrain_width // CHUNK_SIZE) and 0 <= cz < (terrain_width // CHUNK_SIZE):
                    visible_chunks.add((cx, cz))
                    # Build the chunk if it isn't rendered yet, otherwise ensure it is visible
                    if (cx, cz) not in chunks:
                        rebuild_chunk(cx, cz)
                    else:
                        for sub_mesh in chunks[(cx, cz)]:
                            sub_mesh.enabled = True
                        
        # Disable chunk meshes that fall out of range (instead of destroying them)
        # This keeps them cached in memory to eliminate frame rate stutter during movement
        for chunk_coords in list(chunks.keys()):
            if chunk_coords not in visible_chunks:
                for sub_mesh in chunks[chunk_coords]:
                    sub_mesh.enabled = False

# Hand
class Hand(Entity):
    def __init__(self):
        super().__init__(
            parent=camera.ui,
            model="assets/models/arm",
            texture=hand_texture,
            scale=0.2,
            rotation=Vec3(150, -10, 0),
            position=Vec2(0.4, -0.6)
        )
    
    def active(self):
        self.position = Vec2(0.3, -0.5)

    def passive(self):
        self.position = Vec2(0.4, -0.6)
hand = Hand()

# HeldBlock
class HeldBlock(Entity):
    def __init__(self):
        super().__init__(
            parent=camera.ui,               
            model='cube',                   
            texture=dirt_texture,           
            scale=Vec3(0.1, 0.1, 0.1),       
            position=Vec3(0.24, -0.17, -0.5), 
            rotation=Vec3(25, -35, 10),     
            unlit=True                      
        )
    
    def active(self):
        self.position = Vec3(0.14, -0.07, -0.5)

    def passive(self):
        self.position = Vec3(0.24, -0.17, -0.5)
held_block = HeldBlock()

# Block list HUD
block_list_text = Text(
    text=(
        "     --- BLOCK LIST ---\n\n"
        "  1: Grass      |  2: Stone\n"
        "  3: Brick      |  4: Dirt\n"
        "  5: Wood       |  6: Glass\n"
        "  7: Obsidian   |  8: Ice\n"
        "  9: Sand       |  0: White Stone\n"
        ),
    font='VeraMono.ttf',               
    origin=(-0.5, 0.5),                
    position=(-0.28, 0.38),            
    scale=1.4,
    background=True,
    enabled=False
)

# terrain settings (Seeded for deterministic world loading)
random.seed(300)
noise = PerlinNoise(octaves=2, seed=300)
freq = 30
amp = 8
terrain_width = 96 # Balanced map width (96 * 96 = 9,216 block locations), extremely lightweight

# --- MAP INITIAL GENERATION IN MEMORY ---
for i in range(terrain_width * terrain_width):
    x = floor(i / terrain_width)
    z = floor(i % terrain_width)
    y = floor(noise([x / freq, z / freq]) * amp)
    
    pos_key = f"{int(x)},{int(y)},{int(z)}"
    
    # Save base terrain blocks into memory dictionary
    if pos_key not in removed_set:
        add_block_to_memory(x, y, z, "grass")

    # Spawning Oak/Birch Trees
    if 4 < x < terrain_width - 5 and 4 < z < terrain_width - 5:
        # Reduced tree generation probability from 1.5% to 0.35% per block
        if random.random() < 0.0035:
            is_birch = random.random() < 0.35
            log_key = "birch_log" if is_birch else "oak_log"
            leaf_key = "leaf2" if is_birch else "leaf"
            
            # Trunk
            for h in range(1, 5):
                t_key = f"{int(x)},{int(y + h)},{int(z)}"
                if t_key not in removed_set:
                    add_block_to_memory(x, y + h, z, log_key)
            
            # Leaf Canopy
            for lx in range(-1, 2):
                for lz in range(-1, 2):
                    for ly in range(4, 7):
                        if ly == 6 and (abs(lx) + abs(lz) > 1):
                            continue
                        if lx == 0 and lz == 0 and ly < 5:
                            continue
                        lf_key = f"{int(x + lx)},{int(y + ly)},{int(z + lz)}"
                        if lf_key not in removed_set:
                            add_block_to_memory(x + lx, y + ly, z + lz, leaf_key)

# --- OVERLAY SAVED PLACED BLOCKS ---
for pos_str, tex_key in world_data["placed"].items():
    pos_coords = [int(c) for c in pos_str.split(",")]
    add_block_to_memory(pos_coords[0], pos_coords[1], pos_coords[2], tex_key)


# --- PRE-LOAD IMMEDIATE CHUNKS AROUND STARTING POSITION ---
start_x = terrain_width // 2 # 48
start_z = terrain_width // 2 # 48
start_y = floor(noise([start_x / freq, start_z / freq]) * amp) + 5 # Spawn player safely on the ground

pcx = floor(start_x / CHUNK_SIZE)
pcz = floor(start_z / CHUNK_SIZE)

for dx in range(-CHUNK_RENDER_DIST, CHUNK_RENDER_DIST + 1):
    for dz in range(-CHUNK_RENDER_DIST, CHUNK_RENDER_DIST + 1):
        cx = pcx + dx
        cz = pcz + dz
        if 0 <= cx < (terrain_width // CHUNK_SIZE) and 0 <= cz < (terrain_width // CHUNK_SIZE):
            rebuild_chunk(cx, cz)


# player (Spawns at map center on ground)
player = FirstPersonController(x=start_x, z=start_z, y=start_y)
player.jump = lambda: player_jump_override(player)

# run game
game.run()