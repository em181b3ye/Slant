from ursina import *
import random
import math
from datetime import datetime
import saved_progress
import copy

app = Ursina()

# Game state
score = 0
score_text = None
high_score_record = None
game_running = False
high_score = {} #1
for i in range(2):
    for s in range(2):
        for j in range(2):
            for b in range(2):
                high_score[(float(i == 0), float(s == 0), float(j == 0), float(b == 0))] = 0
high_score_text = None
speed_text = None

camera.position = (0, 1.5, -10)
trail = None

tiles = []
obstacles = []
moving_obstacles = []
ramps = []
ghosts = []
ghost_color = (0.5, 255, 0, 0.025)

inf_mode = False
speed_mode = False
jump_mode = False
backward_mode = False

inf_m = False
speed_m = False
jump_m = False
backward_m = False

# Physics
speed = 10
velocity_x = 0
velocity_y = 0
gravity = -9.8
is_grounded = False

# Trackers
last_tile_z = 0
first_tile_z = 0
last_speedup_z = 0
last_ramp_z = 0
last_gap = 0
last_obstacle_z = 0
gap_pending = False
speed_change = False
just_bounced = False
bounce_cooldown = 0.1  # seconds
bounce_timer = 0
time_difference = 0
time_elapsed = 0

# Constants
tile_length = 1
tile_buffer = 100
max_speed = 50
base_acceleration = 10
base_friction = 5
fall_limit = -3
ramp_angle_deg = 20
ramp_angle_rad = math.radians(ramp_angle_deg)

# Records
unlock_inf_mode = False #2
unlock_speed_mode = False #3
unlock_jump_mode = False #4
unlock_backward_mode = False #5
unlock_azure = False #6
unlock_violet = False #7
unlock_olive = False #8
unlock_salmon = False #9
unlock_smoke = False #10
unlock_clear = False #11
unlock_vignette = False #12
unlock_noise = False #13
history = [] #14
logged_in = False
in_game = False
started = False
save_data = saved_progress.saved_data
username = None
password = None


# Temporary Indicators
just_inf = False #15
just_speed = False #16
just_jump = False #17
just_backward = False #18
just_unlock = False #19

# Player
player = Entity(
    model='sphere',
    color=color.green,
    texture='brick',
    scale=0.5,
    position=(0, 2, 1),
    collider='sphere'
)

class Ghost(Entity):
    def __init__(self, position, scale, color):
        super().__init__(
            model='sphere',
            color=color,
            position=position,
            scale=scale,
            parent=scene
        )
        self.fade_speed = 0.05  # opacity fade rate

    def update(self, dt=time.dt):
        self.color[3] -= dt * self.fade_speed
        if self.color[3] <= 0:
            destroy(self)

def setup_ui():
    global score_text, high_score_text, speed_text, speed, inf_mode, speed_mode, jump_mode, backward_mode, just_inf, just_speed, just_jump, just_backward
    Sky(texture='sky_default')
    if score_text:
        destroy(score_text)
    if high_score_text:
        destroy(high_score_text)
    if speed_text:
        destroy(speed_text)

    score_text = Text(
        text='Score: 0',
        position=(-0.70, 0.44),
        scale=2,
        color=color.white,
        background=True
    )

    mode = (float(inf_mode), float(speed_mode), float(jump_mode), float(backward_mode))

    high_score_text = Text(
        text=f'High Score: {high_score[mode]}',
        position=(0.45, 0.44),
        scale=1.5,
        color=color.yellow,
        background=True
    )

    speed_text = Text(
        text=f'Speed: {speed} km/hr',
        position=(-0.70, 0.3),
        scale=1,
        color=color.lime,
        background=True
    )

    if inf_mode:
        Text(
            text='Uncapped',
            position=(-0.4, 0.44),
            scale=1,
            color=color.violet,
            background=True
        )
        if just_inf:
            line = Text(
                text='Keep going until the end!',
                position=(0, 0.3),
                scale=2,
                color=color.clear
            )
            Text(
                text='Keep going until the end!',
                position=(-line.width, 0.3),
                scale=2,
                color=color.red
            )
    
    if speed_mode:
        Text(
            text='Speed',
            position=(-0.15, 0.44),
            scale=1,
            color=color.olive,
            background=True
        )
        if just_speed:
            line = Text(
                text='Try the w and s keys or up and down arrows!',
                position=(0, 0.3),
                scale=2,
                color=color.clear   
            )
            Text(
                text='Try the w and s keys or up and down arrows!',
                position=(-line.width, 0.3),
                scale=2,
                color=color.red   
            )
    
    if jump_mode:
        Text(
            text='Jump',
            position=(0.05, 0.44),
            scale=1,
            color=color.salmon,
            background=True
        )
        if just_jump:
            line = Text(
                text='Try the space bar!',
                position=(0, 0.3),
                scale=2,
                color=color.clear
            )
            Text(
                text='Try the space bar!',
                position=(-line.width, 0.3),
                scale=2,
                color=color.red
            )
    
    if backward_mode:
        Text(
            text='Backward',
            position=(0.25, 0.44),
            scale=1,
            color=color.smoke,
            background=True
        )
        if just_backward:
            height = 0.3
            if (inf_mode and just_inf) or (speed_mode and just_speed) or (jump_mode and just_jump):
                height -= 0.2
            line = Text(
                text='Going negative is good!',
                position=(0, height),
                scale=2,
                color=color.clear
            )
            Text(
                text='Going negative is good!',
                position=(-line.width, height),
                scale=2,
                color=color.red
            )
    

    score_text.world_parent = camera.ui
    high_score_text.world_parent = camera.ui
    speed_text.world_parent = camera.ui
    score_text.z = -1
    high_score_text.z = -1
    speed_text.z = -1

def generate_initial_tiles():
    global last_tile_z
    last_tile_z = 0
    for i in range(25):
        tile = Entity(
            model='cube',
            texture='brick',
            scale=(100, 0.2, 4 * tile_length),
            position=(0, 0, i * tile_length),
            origin=(0, 0.5, 0),
            color=rgb(ghost_color[0], ghost_color[1], ghost_color[2]),
            collider='box'
        )
        tiles.append(tile)
        last_tile_z = tile.z

class MovingObstacle(Entity):
    def __init__(self, axis='y', amplitude=1, speed=1, **kwargs):
        super().__init__(**kwargs)
        self.base_pos = self.position
        self.axis = axis  # 'x' for horizontal, 'y' for vertical
        self.amplitude = amplitude
        self.speed = speed

def spawn_obstacle(z_pos):
    random_x = random.uniform(-1.5, 1.5)
    is_moving = random.random() < 0.25 or speed_mode
    if is_moving:
        axis = random.choice(['x', 'y'])
        amp = random.uniform(0.5, 1)
        obstacle = MovingObstacle(
            axis=axis,
            amplitude=amp,
            speed=random.uniform(1, 2),
            model='cube',
            texture='perlin_noise',
            scale=(1, 1, 1),
            color=color.azure if axis == 'x' else color.violet,
            position=(random_x, 1, z_pos) if axis == 'x' else (random_x, 1 + amp, z_pos),
            origin=(0, 0.5, 0),
            collider='box'
        )
        moving_obstacles.append(obstacle)
    else:
        obstacle = Entity(
            model='cube',
            texture='perlin_noise',
            scale=(1, 1, 1),
            color=color.red,
            position=(random_x, 1, z_pos),
            origin=(0, 0.5, 0),
            collider='box'
        )
        obstacles.append(obstacle)
    
    return obstacle

def spawn_tile():
    global last_tile_z, first_tile_z, last_ramp_z, last_gap, last_obstacle_z, gap_pending, speed

    if speed > 0:
        last_tile_z += tile_length
        first_tile_z += tile_length
        next_tile_z = last_tile_z
    elif speed < 0:
        last_tile_z -= tile_length
        first_tile_z -= tile_length
        next_tile_z = first_tile_z

    # Only allow ramp if far enough from the last one
    can_spawn_ramp = abs(next_tile_z - last_ramp_z) >= 15 and abs(next_tile_z - last_obstacle_z) >= 5 and abs(speed) < 100 - tile_buffer/10
    is_ramp = can_spawn_ramp and random.random() < math.pow(1.5, (2 * (len(obstacles) + len(moving_obstacles)) - len(ramps)))/200

    if is_ramp:
        ramp_width = random.uniform(0.5, 4)
        ramp_x = random.uniform(-2, 2)
        if speed > 0:
            tilt = -1
        else:
            tilt = 1
        ramp = Entity(
            model='cube',
            texture='white_cube',
            scale=(ramp_width, 0.2, 5),
            position=(ramp_x, 0, next_tile_z),
            origin=(0, 0.5, 0),
            color=color.orange,
            rotation=(tilt * ramp_angle_deg, 0, 0),
        )
        ramp.collider = 'box'
        ramps.append(ramp)
        if speed > 0:
            last_ramp_z = last_tile_z
        if speed < 0:
            last_ramp_z = first_tile_z
        gap_pending = True
    else:
        tile_width = random.uniform(2, 4)
        tile_x = random.uniform(-2, 2)
        skip =  speed/abs(speed) * random.uniform(abs(speed)/4, abs(speed)/2)
        gap_pending = gap_pending or (jump_mode and random.random() < 0.05 and ((speed > 0 and abs(last_gap - last_tile_z) >= 2 * skip) or (speed < 0 and abs(last_gap - first_tile_z) >= 2 * skip)))
        if gap_pending == True:
            tile_width = 1/random.randint(1, 5)
            if random.random() < 0.6:
                last_tile_z += skip * tile_length
                first_tile_z += skip * tile_length
                if speed > 0:
                    last_gap = last_tile_z
                if speed < 0:
                    last_gap = first_tile_z
            gap_pending = False
        tile = Entity(
            model='cube',
            texture='brick',
            scale=(tile_width, 0.2, 4 * tile_length),
            position=(tile_x, 0, next_tile_z),
            origin=(0, 0.5, 0),
            color=rgb(ghost_color[0], ghost_color[1], ghost_color[2])
        )
        tile.collider = 'box'
        tiles.append(tile)

    # Chance of obstacle increases the farther it is from the last one
    can_spawn_obstacle = abs(next_tile_z - last_ramp_z) >= 6
    is_obstacle = can_spawn_obstacle and random.random() < abs(next_tile_z - last_obstacle_z)/(10 * abs(speed))

    if is_obstacle:
        spawn_obstacle(next_tile_z)
        last_obstacle_z = next_tile_z

def game_over():
    global game_running, just_unlock, time_elapsed, logged_in
    game_running = False
    time_elapsed = time.time() - time_elapsed

    Text("GAME OVER", origin=(0,0), scale=2, color=color.red, z=0)
    Text(f"Final Score: {score}", origin=(0, -2), scale=1.5, color=color.black)

    history.append((float(inf_mode), float(speed_mode), float(jump_mode), float(backward_mode), score, player.color, ghost_color, datetime.now().strftime("%-I:%M %p, %-m/%-d/%-y"), time_elapsed))
    if len(history) > 100:
        history.remove(history[0])

    if not just_unlock:
        Button(
            text='Restart',
            scale=(0.2, 0.1),
            y=-0.1,
            color=color.azure,
            on_click=restart_game
        )

    Button(
        text='Return Home',
        scale=(0.2, 0.1),
        y=-0.225,
        color=color.magenta,
        on_click=home_page
    )

    if logged_in:
        save()

def input(key):
            if not game_running and in_game:
                if (key == 'r' or key == 'space') and not just_unlock:
                    restart_game()
                elif key == 'h' or key == 'backspace' or key == 'escape':
                    home_page()

def restart_game():
        global game_running, score, velocity_x, velocity_y, speed, last_speedup_z, last_ramp_z, last_gap, last_tile_z, last_obstacle_z, gap_pending, speed_change, just_bounced, time_difference, first_tile_z, backward_mode, time_elapsed

        game_running = True

        score = 0
        velocity_x = 0
        velocity_y = 0
        speed = 10
        if backward_mode:
            speed = -10
        last_speedup_z = 0
        last_ramp_z = 0
        last_gap = 0
        last_obstacle_z = 0
        last_tile_z = 0
        first_tile_z = 0
        gap_pending = False
        speed_change = False
        just_bounced = False
        time_difference = 0
        time_elapsed = time.time()

        for e in scene.entities[:]:
            if e not in (player, camera.ui):
                destroy(e)

        player.position = (0, 2, 1)
        tiles.clear()
        ramps.clear()
        obstacles.clear()
        moving_obstacles.clear()

        generate_initial_tiles()
        setup_ui()

def enter_skins():
        global unlock_azure, unlock_violet, unlock_olive, unlock_salmon, unlock_smoke, unlock_clear, unlock_vignette, unlock_noise
        for e in scene.entities[:]:
            if e not in (player, camera.ui):
                destroy(e)
        Button(
            text='Return Home',
            scale=(0.2, 0.1),
            y=0,
            color=color.magenta,
            on_click=home_page
            )
        Button(
            text='Normal',
            text_color=color.black,
            scale=(0.2, 0.1),
            y=0.4,
            x=-0.6,
            color=color.green,
            on_click=set_green,
            )
        if unlock_azure:
            Button(
                text='Azure',
                text_color=color.black,
                scale=(0.2, 0.1),
                y=0.4,
                x=0.6,
                color=color.azure,
                on_click=set_azure,
                )
        if unlock_violet:
            Button(
                text='Violet',
                scale=(0.2, 0.1),
                y=0.2,
                x=-0.6,
                color=color.violet,
                on_click=set_violet,
                )
        if unlock_olive:
            Button(
                text='Olive',
                scale=(0.2, 0.1),
                y=0.2,
                x=0.6,
                color=color.olive,
                on_click=set_olive,
                )
        if unlock_salmon:
            Button(
                text='Salmon',
                text_color=color.black,
                scale=(0.2, 0.1),
                y=0,
                x=-0.6,
                color=color.salmon,
                on_click=set_salmon,
                )
        if unlock_smoke:
            Button(
                text='Smoke',
                text_color=color.black,
                scale=(0.2, 0.1),
                y=0,
                x=0.6,
                color=color.smoke,
                on_click=set_smoke,
                )
        if unlock_vignette:
            Button(
                text='Vignette',
                scale=(0.2, 0.1),
                y=-0.2,
                x=-0.3,
                color=color.gray,
                on_click=set_vignette,
                )
        if unlock_noise:
            Button(
                text='Noise',
                scale=(0.2, 0.1),
                y=-0.2,
                x=0.3,
                color=color.black,
                on_click=set_noise,
                )
        if unlock_clear:
            Button(
                text='Clear',
                text_color=color.white,
                scale=(0.2, 0.1),
                y=-0.4,
                x=0,
                color=color.white,
                on_click=set_clear,
                highlight_color=color.clear
                )
    
def set_green():
    global ghost_color
    player.color = color.green
    ghost_color = (0.5, 255, 0, 0.025)
    player.texture = 'brick'
    home_page()

def set_azure():
    global ghost_color
    player.color = color.azure
    ghost_color = (0, 130, 255, 0.025)
    home_page()

def set_violet():
    global ghost_color
    player.color = color.violet
    ghost_color = (141, 0, 255, 0.025)
    home_page()

def set_olive():
    global ghost_color
    player.color = color.olive
    ghost_color = (128, 128, 0, 0.025)
    home_page()

def set_salmon():
    global ghost_color
    player.color = color.salmon
    ghost_color = (255, 119, 108, 0.025)
    home_page()

def set_smoke():
    global ghost_color
    player.color = color.smoke
    ghost_color = (255, 255, 255, 0.025)
    home_page()

def set_vignette():
    player.texture = 'vignette'
    home_page()

def set_noise():
    player.texture = 'noise'
    home_page()

def set_clear():
    player.color = color.clear
    home_page()

def enter_info():
        global unlock_inf_mode, unlock_speed_mode, unlock_jump_mode, unlock_backward_mode, inf_b, speed_b, jump_b, backward_b, high_score_record
        for e in scene.entities[:]:
            if e not in (player, camera.ui):
                destroy(e)
        Text("Info", origin=(0,-2), scale=2, color=color.black, z=0)
        Button(
            text='Return Home',
            scale=(0.2, 0.1),
            y=-0.225,
            color=color.magenta,
            on_click=home_page
        )
        Button(
            text='History',
            scale=(0.2, 0.1),
            y=0,
            color=color.olive,
            on_click=enter_history
        )
        Text("Keep playing, you might unlock something!", origin=(0, -18), scale=1, color=color.azure, z=0)
        if unlock_inf_mode:
            Text("Uncapped Mode: Play until there are no more tiles, there's no speed limit!", origin=(0, -16), scale=1, color=color.violet, z=0)
        if unlock_speed_mode:
            Text("Speed Mode: Up arrow or w to fast forward, down arrow or s to slo-mo!", origin=(-0.3, -14), scale=1, color=color.olive, z=0)
        if unlock_jump_mode:
            Text("Jump Mode: Space to jump!", origin=(1.3, -14), scale=1, color=color.salmon, z=0)
        if unlock_backward_mode:
            Text("Backward Mode: Time to go backward!", origin=(0, -12), scale=1, color=color.smoke, z=0)
        
        inf_c = color.violet
        if inf_m:
            inf_c = hsv(0, 0, 0.5)

        def set_inf():
            global inf_m, inf_b, inf_c, high_score_record, mode
            inf_m = not inf_m
            destroy(inf_b)
            destroy(high_score_record)
            mode = (float(inf_m), float(speed_m), float(jump_m), float(backward_m))
            inf_c = color.violet
            if inf_m:
                inf_c = hsv(0, 0, 0.5)
            inf_b = Button(
                text='Uncapped',
                scale=(0.2, 0.1),
                x=-0.6,
                y=-0.1125,
                color=inf_c,
                on_click=set_inf,
                )
            high_score_record = Text(f"High Score: {high_score[mode]}", origin=(0, -10), scale=1, color=color.yellow, z=0)

        speed_c = color.olive
        if speed_m:
            speed_c = hsv(0, 0, 0.5)

        def set_speed():
            global speed_m, speed_b, speed_c, high_score_record, mode
            speed_m = not speed_m
            destroy(speed_b)
            destroy(high_score_record)
            mode = (float(inf_m), float(speed_m), float(jump_m), float(backward_m))
            speed_c = color.olive
            if speed_m:
                speed_c = hsv(0, 0, 0.5)
            speed_b = Button(
                text='Speed',
                scale=(0.2, 0.1),
                x=-0.25,
                y=-0.1125,
                color=speed_c,
                on_click=set_speed
                )
            high_score_record = Text(f"High Score: {high_score[mode]}", origin=(0, -10), scale=1, color=color.yellow, z=0)
        
        jump_c = color.salmon
        if jump_m:
            jump_c = hsv(0, 0, 0.5)

        def set_jump():
            global jump_m, jump_b, jump_c, high_score_record, mode
            jump_m = not jump_m
            destroy(jump_b)
            destroy(high_score_record)
            mode = (float(inf_m), float(speed_m), float(jump_m), float(backward_m))
            jump_c = color.salmon
            if jump_m:
                jump_c = hsv(0, 0, 0.5)
            jump_b = Button(
                    text='Jump',
                    scale=(0.2, 0.1),
                    x=0.25,
                    y=-0.1125,
                    color=jump_c,
                    on_click=set_jump,
                )
            high_score_record = Text(f"High Score: {high_score[mode]}", origin=(0, -10), scale=1, color=color.yellow, z=0)
        
        backward_c = color.smoke
        if backward_m:
            backward_c = hsv(0, 0, 0.5)

        def set_backward():
            global backward_m, backward_b, backward_c, high_score_record, mode
            backward_m = not backward_m
            destroy(backward_b)
            destroy(high_score_record)
            mode = (float(inf_m), float(speed_m), float(jump_m), float(backward_m))
            backward_c = color.smoke
            if backward_m:
                backward_c = hsv(0, 0, 0.5)
            backward_b = Button(
                    text='Backward',
                    text_color=color.black,
                    scale=(0.2, 0.1),
                    x=0.6,
                    y=-0.1125,
                    color=backward_c,
                    on_click=set_backward,
                )
            high_score_record = Text(f"High Score: {high_score[mode]}", origin=(0, -10), scale=1, color=color.yellow, z=0)
        
        mode = (float(inf_m), float(speed_m), float(jump_m), float(backward_m))

        if unlock_inf_mode:
            inf_b = Button(
                text='Uncapped',
                scale=(0.2, 0.1),
                x=-0.6,
                y=-0.1125,
                color=inf_c,
                on_click=set_inf,
                )
        if unlock_speed_mode:
            speed_b = Button(
                    text='Speed',
                    scale=(0.2, 0.1),
                    x=-0.25,
                    y=-0.1125,
                    color=speed_c,
                    on_click=set_speed,
                )
        if unlock_jump_mode:
            jump_b = Button(
                    text='Jump',
                    scale=(0.2, 0.1),
                    x=0.25,
                    y=-0.1125,
                    color=jump_c,
                    on_click=set_jump,
                )
        if unlock_backward_mode:
            backward_b = Button(
                    text='Backward',
                    text_color=color.black,
                    scale=(0.2, 0.1),
                    x=0.6,
                    y=-0.1125,
                    color=backward_c,
                    on_click=set_backward,
                )        
        
        high_score_record = Text(f"High Score: {high_score[mode]}", origin=(0, -10), scale=1, color=color.yellow, z=0)

def enter_history():
        for e in scene.entities[:]:
            if e not in (player, camera.ui):
                destroy(e)
        Button(
            text='Return Home',
            scale=(0.2, 0.1),
            y=0.4,
            x=-0.6,
            color=color.magenta,
            on_click=home_page
        )
        def list_modes(history):
            modes = ""
            if history[0]:
                modes += "Uncapped"
            if history[1]:
                modes += "Speed"
            if history[2]:
                modes += "Jump"
            if history[3]:
                modes += "Backward"
            modes += f"Score: {history[4]}"
            result = modes[0]
            for i in range (1, len(modes)):
                if modes[i].isupper():
                    result += ", " + modes[i]
                else:
                    result += modes[i]
            result += f", Survived: {time.strftime('%H:%M:%S', time.gmtime(history[8]))}, {history[7]}"
            return result
        
        scroller = Button(model='quad', color=color.clear, scale=(2,8), collider='box', origin=(0, 0), position=(0, 0))
        Button(parent=scroller, model='quad', color=color.clear, scale=(2, 8), position=(0, 0), collider='box')
        for i in range(8):
            Button(parent=scroller, model='quad', color=color.white, scale=(0.01, 0.02), position=(0.38, 0.13 - 0.065 * i), collider='box')

        for i in range(len(history)):
            if history[len(history) - 1 - i][5] == color.clear:
                line = Text(
                    text=list_modes(history[len(history) - 1 - i]),
                    position=(0, 0.05 - 0.005 * i),
                    scale=1,
                    color=color.clear,
                    z=0)
                Button(
                    parent=scroller,
                    text=list_modes(history[len(history) - 1 - i]),
                    position=(0, 0.05 - 0.005 * i),
                    scale=(line.width/2, 0.005),
                    text_color=color.white,
                    color=rgb(history[len(history) - 1 - i][6][0], history[len(history) - 1 - i][6][1], history[len(history) - 1 - i][6][2]),
                    z=0,
                    collider='box')
            else:
                Button(
                parent=scroller,
                text=list_modes(history[len(history) - 1 - i]),
                position=(0, 0.05 - 0.005 * i),
                scale=1,
                text_color=history[len(history) - 1 - i][5],
                color=color.clear,
                z=0,
                collider='box')
            
            scroller.add_script(Scrollable(max=2, min=0))

def enter_leaderboard():
    global unlock_inf_mode, unlock_speed_mode, unlock_jump_mode, unlock_backward_mode, inf_b, speed_b, jump_b, backward_b
    for e in scene.entities[:]:
        if e not in (player, camera.ui):
            destroy(e)

    def show_leaderboard(mode):
        leaders = min(10, len(save_data))
        temp_data = {}
        for user in save_data:
            temp_data[user] = save_data[user][1].get(mode)
        top = sorted(temp_data, key=temp_data.get, reverse=True)[0:leaders]
        for i in range(leaders):
            Text(f"{i + 1} --- {top[i]}: {temp_data[top[i]]}", x = 0.3, y = 0.36 - 0.08 * i, scale = 1, color=color.red, background=True, z = 0)
    Button(
            text='Return Home',
            scale=(0.2, 0.1),
            y=0.4,
            x=0,
            color=color.magenta,
            on_click=home_page
        )
    
    inf_c = color.violet
    if inf_m:
        inf_c = hsv(0, 0, 0.5)

    def set_inf():
        global inf_m, inf_b, inf_c, mode
        inf_m = not inf_m
        destroy(inf_b)
        mode = (float(inf_m), float(speed_m), float(jump_m), float(backward_m))
        inf_c = color.violet
        if inf_m:
            inf_c = hsv(0, 0, 0.5)
        inf_b = Button(
            text='Uncapped',
            scale=(0.2, 0.1),
            x=-0.6,
            y=0.3,
            color=inf_c,
            on_click=set_inf,
            )
        enter_leaderboard()

    speed_c = color.olive
    if speed_m:
        speed_c = hsv(0, 0, 0.5)

    def set_speed():
        global speed_m, speed_b, speed_c, mode
        speed_m = not speed_m
        destroy(speed_b)
        mode = (float(inf_m), float(speed_m), float(jump_m), float(backward_m))
        speed_c = color.olive
        if speed_m:
            speed_c = hsv(0, 0, 0.5)
        speed_b = Button(
            text='Speed',
            scale=(0.2, 0.1),
            x=-0.6,
            y=0.1,
            color=speed_c,
            on_click=set_speed
            )
        enter_leaderboard()

    jump_c = color.salmon
    if jump_m:
        jump_c = hsv(0, 0, 0.5)

    def set_jump():
        global jump_m, jump_b, jump_c, mode
        jump_m = not jump_m
        destroy(jump_b)
        mode = (float(inf_m), float(speed_m), float(jump_m), float(backward_m))
        jump_c = color.salmon
        if jump_m:
            jump_c = hsv(0, 0, 0.5)
        jump_b = Button(
                text='Jump',
                scale=(0.2, 0.1),
                x=-0.6,
                y=-0.1,
                color=jump_c,
                on_click=set_jump,
            )
        enter_leaderboard()
    
    backward_c = color.smoke
    if backward_m:
        backward_c = hsv(0, 0, 0.5)

    def set_backward():
        global backward_m, backward_b, backward_c, mode
        backward_m = not backward_m
        destroy(backward_b)
        mode = (float(inf_m), float(speed_m), float(jump_m), float(backward_m))
        backward_c = color.smoke
        if backward_m:
            backward_c = hsv(0, 0, 0.5)
        backward_b = Button(
                text='Backward',
                text_color=color.black,
                scale=(0.2, 0.1),
                x=-0.6,
                y=-0.3,
                color=backward_c,
                on_click=set_backward,
            )
        enter_leaderboard()
    
    mode = (float(inf_m), float(speed_m), float(jump_m), float(backward_m))

    if unlock_inf_mode: 
        inf_b = Button(
            text='Uncapped',
            scale=(0.2, 0.1),
            x=-0.6,
            y=0.3,
            color=inf_c,
            on_click=set_inf,
            )
    if unlock_speed_mode:
        speed_b = Button(
                text='Speed',
                scale=(0.2, 0.1),
                x=-0.6,
                y=0.1,
                color=speed_c,
                on_click=set_speed,
            )
    if unlock_jump_mode:
        jump_b = Button(
                text='Jump',
                scale=(0.2, 0.1),
                x=-0.6,
                y=-0.1,
                color=jump_c,
                on_click=set_jump,
            )
    if unlock_backward_mode:
        backward_b = Button(
                text='Backward',
                text_color=color.black,
                scale=(0.2, 0.1),
                x=-0.6,
                y=-0.3,
                color=backward_c,
                on_click=set_backward,
            )
    
    show_leaderboard(mode)
    
def home_page():
    global just_unlock, inf_button, speed_button, jump_button, backward_button, in_game, started
    
    in_game = True
    started = True

    inf_color = color.violet
    if inf_mode:
        inf_color = hsv(270, 0.5, 0.5)

    def set_inf_mode():
        global inf_mode, inf_button, inf_color
        inf_mode = not inf_mode
        destroy(inf_button)
        inf_color = color.violet
        if inf_mode:
            inf_color = hsv(270, 0.5, 0.5)
        inf_button = Button(
            text='Uncapped',
            scale=(0.2, 0.1),
            y=-0.225,
            color=inf_color,
            on_click=set_inf_mode,
            )

    speed_color = color.olive
    if speed_mode:
        speed_color = color.rgba(128, 128, 0, 0.4)

    def set_speed_mode():
        global speed_mode, speed_button, speed_color
        speed_mode = not speed_mode
        destroy(speed_button)
        speed_color = color.olive
        if speed_mode:
            speed_color = color.rgba(128, 128, 0, 0.4)
        speed_button = Button(
            text='Speed',
            scale=(0.2, 0.1),
            x = -0.25,
            y=-0.35,
            color=speed_color,
            on_click=set_speed_mode
            )
    
    jump_color = color.salmon
    if jump_mode:
        jump_color = color.rgba(250, 128, 114, 0.4)

    def set_jump_mode():
        global jump_mode, jump_button, jump_color
        jump_mode = not jump_mode
        destroy(jump_button)
        jump_color = color.salmon
        if jump_mode:
            jump_color = color.rgba(250, 128, 114, 0.4)
        jump_button = Button(
                text='Jump',
                scale=(0.2, 0.1),
                x = 0.25,
                y=-0.35,
                color=jump_color,
                on_click=set_jump_mode,
            )
    
    backward_color = color.smoke
    if backward_mode:
        backward_color = hsv(0, 0, 0.5)

    def set_backward_mode():
        global backward_mode, backward_button, backward_color
        backward_mode = not backward_mode
        destroy(backward_button)
        backward_color = color.smoke
        if backward_mode:
            backward_color = hsv(0, 0, 0.5)
        backward_button = Button(
                text='Backward',
                text_color=color.black,
                scale=(0.2, 0.1),
                y=-0.4,
                color=backward_color,
                on_click=set_backward_mode,
            )
   
    for e in scene.entities[:]:
        if e not in (player, camera.ui):
            destroy(e)
    Sky(texture='sky_default')
    Text("Home", origin=(0,-2), scale=2, color=color.black, z=0,)
    if unlock_inf_mode and unlock_speed_mode and unlock_jump_mode and unlock_backward_mode and unlock_azure and unlock_violet and unlock_olive and unlock_salmon and unlock_smoke and unlock_clear and unlock_vignette and unlock_noise:
        Text("You Unlocked Everything!", origin=(0,0), scale=2, color=color.red, z=0,)
    elif just_unlock:
        Text("You Unlocked Something!", origin=(0,0), scale=2, color=color.red, z=0,)
    just_unlock = False
    Button(
        text='Play',
        scale=(0.2, 0.1),
        y=-0.1,
        color=color.azure,
        on_click=restart_game,
        )
    if unlock_inf_mode:
        inf_button = Button(
            text='Uncapped',
            scale=(0.2, 0.1),
            y=-0.225,
            color=inf_color,
            on_click=set_inf_mode,
            )
    if unlock_speed_mode:
        speed_button = Button(
                text='Speed',
                scale=(0.2, 0.1),
                x = -0.25,
                y=-0.35,
                color=speed_color,
                on_click=set_speed_mode,
            )
    if unlock_jump_mode:
        jump_button = Button(
                text='Jump',
                scale=(0.2, 0.1),
                x = 0.25,
                y=-0.35,
                color=jump_color,
                on_click=set_jump_mode,
            )
    if unlock_backward_mode:
        backward_button = Button(
                text='Backward',
                text_color=color.black,
                scale=(0.2, 0.1),
                y=-0.4,
                color=backward_color,
                on_click=set_backward_mode,
            )
    Button(
            text='Info',
            text_color=color.white,
            scale=(0.2, 0.1),
            y=0.4,
            color=color.magenta,
            on_click=enter_info
        )
    Button(
            text='Skins',
            text_color=color.white,
            scale=(0.2, 0.1),
            y=0.25,
            color=color.blue,
            on_click=enter_skins
        )
    if logged_in:
        Button(
                text='Log Out',
                text_color=color.white,
                scale=(0.2, 0.1),
                y=0.4,
                x=0.6,
                color=color.pink,
                on_click=start_page
            )
    else:
        Button(
            text='Create Account',
            text_color=color.white,
            scale=(0.2, 0.1),
            y=0.4,
            x=0.6,
            color=color.pink,
            on_click=create_account
        )
    Button(
            text='Leaderboard',
            text_color=color.black,
            scale=(0.2, 0.1),
            y=0.4,
            x=-0.6,
            color=color.green,
            on_click=enter_leaderboard
        )
    
def save():
        global save_data, username, password
        save_data[str(username)] = [str(password), 
                               high_score, 
                               unlock_inf_mode,
                               unlock_speed_mode,
                               unlock_jump_mode,
                               unlock_backward_mode,
                               unlock_azure,
                               unlock_violet,
                               unlock_olive,
                               unlock_salmon,
                               unlock_smoke,
                               unlock_clear,
                               unlock_vignette,
                               unlock_noise,
                               history,
                               just_inf,
                               just_speed,
                               just_jump,
                               just_backward,
                               just_unlock]
        with open('/Users/user/PythonProjects/ML/Slope/Slant Progression/saved_progress.py', 'w') as file: 
            file.write("from ursina import Vec4\n")
            file.write(f"saved_data = {save_data}\n")

def account_made():
    global logged_in, save_data, username
    if username in save_data or username is None or password is None:
        Text("Username taken, try again.", y = 0.4, color=color.red, z=0)
    else:
        logged_in = True
        save()
        home_page()

def create_account():
    global in_game

    in_game = False
    
    for e in scene.entities[:]:
        if e not in (player, camera.ui):
            destroy(e)

    Text("Enter Username", y = 0.2, color=color.white, z=0,)

    input_username = InputField(y=0.1)
    def submit_username():
        global username
        username = input_username.text
    
    input_username.on_value_changed = submit_username

    Text("Enter Password", y = 0, color=color.white, z=0,)

    input_password = InputField(y=-0.1)
    def submit_password():
        global password
        password = input_password.text
    
    input_password.on_value_changed = submit_password

    Button(
        text='Confirm',
        scale=(0.2, 0.1),
        y=-0.25,
        color=color.magenta,
        on_click=account_made,
        )

    if not started:
        Button(
            text='Back',
            scale=(0.2, 0.1),
            y=-0.4,
            color=color.azure,
            on_click=start_page,
            )
    else:
        Button(
            text='Back',
            scale=(0.2, 0.1),
            y=-0.4,
            color=color.azure,
            on_click=home_page,
            )

def verify():
    global logged_in, save_data, username, password, high_score, unlock_inf_mode, unlock_speed_mode, unlock_jump_mode, unlock_backward_mode, unlock_azure, unlock_violet, unlock_olive, unlock_salmon, unlock_smoke, unlock_clear, unlock_vignette, unlock_noise, history, just_inf, just_speed, just_jump, just_backward, just_unlock
    if (username in save_data) and save_data[username][0] == password:
        info = save_data[username]
        high_score = info[1] #1
        unlock_inf_mode = info[2] #2
        unlock_speed_mode = info[3] #3
        unlock_jump_mode = info[4] #4
        unlock_backward_mode = info[5] #5
        unlock_azure = info[6] #6
        unlock_violet = info[7] #7
        unlock_olive = info[8] #8
        unlock_salmon = info[9] #9
        unlock_smoke = info[10] #10
        unlock_clear = info[11] #11
        unlock_vignette = info[12] #12
        unlock_noise = info[13] #13
        history = info[14] #14
        just_inf = info[15] #15
        just_speed = info[16] #16
        just_jump = info[17] #17
        just_backward = info[18] #18
        just_unlock = info[19] #19
        logged_in = True
        save()
        home_page()
    else:
        Text("Wrong username or password, try again.", y = 0.4, color=color.red, z=0)

def log_in():
    global logged_in, in_game

    in_game = False
    
    for e in scene.entities[:]:
        if e not in (player, camera.ui):
            destroy(e)

    Text("Enter Username", y = 0.2, color=color.white, z=0,)

    input_username = InputField(y=0.1)
    def submit_username():
        global username
        username = input_username.text
    
    input_username.on_value_changed = submit_username

    Text("Enter Password", y = 0, color=color.white, z=0,)

    input_password = InputField(y=-0.1)
    def submit_password():
        global password
        password = input_password.text
    
    input_password.on_value_changed = submit_password

    Button(
        text='Confirm',
        scale=(0.2, 0.1),
        y=-0.25,
        color=color.magenta,
        on_click=verify,
        )

    Button(
        text='Back',
        scale=(0.2, 0.1),
        y=-0.4,
        color=color.azure,
        on_click=start_page,
        )

def start_page():
    global username, password, in_game, started
    for e in scene.entities[:]:
        if e not in (player, camera.ui):
            destroy(e)
    
    username = None
    password = None
    in_game = False
    started = False

    Button(
        text='Guest',
        scale=(0.2, 0.1),
        y=-0.1,
        color=color.azure,
        on_click=home_page,
        )
    
    Button(
            text='Create Account',
            text_color=color.white,
            scale=(0.2, 0.1),
            y=0.4,
            color=color.magenta,
            on_click=create_account
        )
    
    Button(
            text='Log In',
            text_color=color.white,
            scale=(0.2, 0.1),
            y=0.25,
            color=color.blue,
            on_click=log_in
        )

def update():
    global speed, velocity_y, is_grounded, game_running, score, velocity_x, last_speedup_z, speed_change, high_score, speed_text, just_bounced, bounce_timer, tile_buffer, time_difference, unlock_inf_mode, unlock_speed_mode, unlock_jump_mode, unlock_backward_mode, unlock_azure, unlock_violet, unlock_olive, unlock_salmon, unlock_smoke, unlock_clear, unlock_vignette, unlock_noise, just_unlock, just_inf, just_speed, just_jump, just_backward

    ramp_launch_velocity = 2  # Tweak this for higher/lower jump

    game_speed = 1
    if speed_mode:
        if held_keys['w'] or held_keys['up arrow']:
            game_speed = 2
            
        elif held_keys['s'] or held_keys['down arrow']:
            game_speed = 0.5

    dt = time.dt * game_speed
    if speed_mode:
        time_difference -= (8/3 - 29/(6 * game_speed)) * time.dt
    time_passed = time.time() + time_difference
    bounce_timer += dt

    tile_buffer = max(100, (speed ** 2) // 25)

    if not game_running:
        return
    
    # Score and speed-up logic
    score = (10 + int(player.z)) // 20
    if score_text:
        score_text.text = f'Score: {score}'

    player.z += dt * speed

    if int(time.time() * 10) % 2 == 0:  # every 0.1s
        ghost = Ghost(player.position, player.scale, ghost_color)
        ghosts.append(ghost)

    for g in ghosts[:]:
        g.update(dt)
        if g.color[3] <= 0:
            ghosts.remove(g)

    for mo in moving_obstacles[:]:
        offset = math.sin(time_passed * mo.speed) * mo.amplitude
        if mo.axis == 'y':
            mo.y = mo.base_pos.y + offset
        elif mo.axis == 'x':
            mo.x = mo.base_pos.x + offset

    if abs(player.z - last_speedup_z) >= 40:
        if inf_mode:
            speed = speed * (1 + 2.5/abs(speed))
        else:
            speed = speed/abs(speed) * min(abs(speed * 1.25), max_speed)
        last_speedup_z = player.z

    # X-axis input
    if held_keys['a'] or held_keys['left arrow']:
        velocity_x -= base_acceleration * dt
    elif held_keys['d'] or held_keys['right arrow']:
        velocity_x += base_acceleration * dt
    elif is_grounded:
        # Friction
        velocity_x -= math.copysign(base_friction * dt, velocity_x)
        if abs(velocity_x) < 0.1:
            velocity_x = 0

    player.x += velocity_x * dt

    # ==== Smarter Ground Detection & Ramp Launch ====
    ground_y = None
    tile_ground_y = None
    is_grounded = False
    on_ramp = False
    tile_before = False

    for ramp in ramps:

        # Check if player is on ramp
        if abs(player.x - ramp.x) < (ramp.scale_x + player.scale_x)/2 and abs(player.z - ramp.z) < (ramp.scale_z + player.scale_z)/2:
            dz = speed/abs(speed) * (player.z - ramp.z)
            ramp_height = math.tan(ramp_angle_rad) * dz
            ground_y = ramp.y + 0.5 + ramp_height
            on_ramp = True

            if abs(player.y - ground_y) < 0.3 and not abs(player.z - ramp.z - (speed/abs(speed) * ramp.scale_z/2)) < 0.3:
                is_grounded = True
                player.y = ground_y
                velocity_y = 0
                just_bounced = False
                break
        elif abs(player.z - ramp.z - ramp.scale_z/2) < 0.1 and abs(player.z - ramp.z) < ramp.scale_z / 2 and player.y < ramp.y:
            velocity_x = -0.5 * velocity_x
            break

        # Launch off end of ramp
        if ground_y is not None and on_ramp and abs(player.z - ramp.z - (speed/abs(speed) * ramp.scale_z/2)) < 0.3:
            velocity_y = ramp_launch_velocity
            player.y += 0.1
            is_grounded = False
            just_bounced = False
            on_ramp = False

    for tile in tiles:

        if not is_grounded:
            if abs(player.x - tile.x) < tile.scale_x/(2 - 0.1) and abs(player.z - tile.z) < tile.scale_z/(2 - 0.1):
                if abs(player.y - (tile.y + 0.5)) < 0.1:
                    tile_ground_y = tile.y + 0.5
                    is_grounded = True
                    speed_change = False
                    break

        if abs(player.x - tile.x) < tile.scale_x/(2 - 0.1) + 0.1:
            if abs(player.z - (tile.z - player.scale_z)) < tile.scale.z + 0.1:
                if abs(player.y - tile.y - 0.3) < 0.25:
                    tile_before = True
            if abs(player.z - tile.z) < tile.scale.z + 0.1:
                if player.y <= tile.y and not speed_change and not tile_before and player.intersects(tile):
                    speed = - speed/abs(speed) * 5
                    speed_change = True
                    player.z += speed/abs(speed) * 0.5
                elif player.y < tile.y + 0.1 and not speed_change and not on_ramp and player.intersects(tile):
                    speed = (1 + abs(player.y - tile.y)) * speed
                    speed_change = True
                    velocity_y = 0.5
                    player.y = tile.y + 0.5
                elif player.intersects(tile) and not on_ramp:
                    player.y = tile.y + player.scale.y

    if is_grounded and tile_ground_y is not None:
        if velocity_y < -1 and not just_bounced:
            velocity_y = -0.3 * velocity_y
            player.y = tile_ground_y + 0.1
            is_grounded = False
            just_bounced = True
            bounce_timer = 0
        elif bounce_timer >= bounce_cooldown:
            velocity_y = 0
            player.y = tile_ground_y
            just_bounced = False
    else:
        just_bounced = False  # Reset flag when airborne
        velocity_y += gravity * dt
        player.y += velocity_y * dt
    
    if jump_mode and is_grounded and held_keys['space']:
        velocity_y = 5
        player.y += 0.2
        is_grounded = False

    # Check fall
    if player.y < fall_limit:
        game_over()

    # Obstacle collision
    for obstacle in obstacles:
        if player.intersects(obstacle) or (abs((player.z + 1) - obstacle.z) < 1.75 and speed/abs(speed) * player.z < speed/abs(speed) * obstacle.z and abs(player.x - obstacle.x) < 0.45 and abs((obstacle.y - 0.5) - player.y) < 0.7):
            game_over()
            break
    
    for obstacle in moving_obstacles:
        if player.intersects(obstacle) or (abs((player.z + 1) - obstacle.z) < 1.75 and speed/abs(speed) * player.z < speed/abs(speed) * obstacle.z and abs(player.x - obstacle.x) < 0.45 and abs((obstacle.y - 0.5) - player.y) < 0.7):
            game_over()
            break

    # Rolling rotation
    movement_vector = Vec3(velocity_x, 0, speed) * dt
    distance_moved = movement_vector.length()
    if distance_moved > 0:
        rotation_axis = Vec3(0, 1, 0).cross(movement_vector.normalized())
        rotation_degrees = math.degrees(distance_moved / player.scale_x)
        player.rotation += rotation_axis * rotation_degrees

    camera_dist = 10
    if speed < -10 and camera_dist < abs(speed) * 1.5:
        camera_dist += (abs(speed) ** 2)/10 * dt
    elif speed > -10 and camera_dist > 10:
        camera_dist -= (abs(speed) ** 2) * dt
    elif camera_dist < 10:
        camera_dist = 10
    camera.z = player.z - camera_dist

    # Tile & obstacle spawning
    if player.z + tile_buffer * tile_length > last_tile_z and speed > 0:
        spawn_tile()

    if player.z - tile_buffer * tile_length < first_tile_z and speed < 0:
        spawn_tile()

    # Cleanup old entities
    for collection in (tiles, ramps, obstacles, moving_obstacles):
        for e in collection[:]:
            if (e.z < player.z - 20 and speed > 0) or (e.z > player.z + 2 * tile_buffer and speed < 0):
                destroy(e)
                collection.remove(e)

    mode = (float(inf_mode), float(speed_mode), float(jump_mode), float(backward_mode))

    if (not backward_mode and score > high_score[mode]) or (backward_mode and score < high_score[mode]):
        high_score[mode] = score
        if high_score_text:
            high_score_text.text = f'High Score: {high_score[mode]}'
    
    if speed_text:
        speed_value = (speed ** 2 + velocity_x ** 2 + velocity_y ** 2) ** 0.5
        speed_text.text = f'Speed: {speed_value:.1f} km/hr'
    
    if speed >= 50 and not unlock_azure:
        unlock_azure = True
        just_unlock = True
    
    if abs(score) >= 100 and not unlock_inf_mode:
        unlock_inf_mode = True
        just_inf = True
        just_unlock = True
    
    if score >= 100 and inf_mode and not unlock_violet:
        unlock_violet = True
        just_unlock = True
    
    if len(tiles) == 0 and inf_mode and not unlock_speed_mode:
        unlock_speed_mode = True
        just_speed = True
        just_unlock = True
    
    if abs(score) >= 100 and speed_mode and not unlock_olive:
        unlock_olive = True
        just_unlock = True
    
    if len(tiles) == 0 and speed_mode and inf_mode and not unlock_jump_mode:
        unlock_jump_mode = True
        just_jump = True
        just_unlock = True
    
    if abs(score) >= 100 and jump_mode and not unlock_salmon:
        unlock_salmon = True
        just_unlock = True
    
    if abs(score) >= 100 and speed_mode and jump_mode and not unlock_vignette:
        unlock_vignette = True
        just_unlock = True
    
    if len(tiles) == 0 and speed_mode and jump_mode and inf_mode and not unlock_noise:
        unlock_noise = True
        just_unlock = True
    
    if score < 0 and not unlock_backward_mode:
        unlock_backward_mode = True
        just_backward = True
        just_unlock = True
    
    if speed <= -50 and speed < 0 and not unlock_smoke:
        unlock_smoke = True
        just_unlock = True
    
    if len(tiles) == 0 and speed_mode and jump_mode and backward_mode and speed < 0 and not unlock_clear:
        unlock_clear = True
        just_unlock = True
    
    if inf_mode and just_inf:
        just_inf = False
    
    if speed_mode and just_speed:
        just_speed = False

    if jump_mode and just_jump:
        just_jump = False
    
    if backward_mode and just_backward:
        just_backward = False

window.fps_counter.enabled = False
window.entity_counter.enabled = False
window.collider_counter.enabled = False
start_page()
app.run()