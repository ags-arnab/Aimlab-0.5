from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import time
import random
import math
from OpenGL.GLUT import GLUT_BITMAP_HELVETICA_18, GLUT_BITMAP_TIMES_ROMAN_24



STATE_MENU = 0
STATE_PLAYING = 1
STATE_GAME_OVER = 2
current_state = STATE_MENU


menu_options = { "mode": ["Easy", "Medium", "Hard", "Practice"], 
    "time": ["30s", "60s", "90s", "N/A"] }
selected_mode_idx = 0
selected_time_idx = 0 
menu_cursor_pos = 0  


score = 0 
misses = 0 
shots_fired = 0 
successful_hits = 0 
accuracy = 0.0
game_timer = 0
game_start_time = 0
selected_game_duration = 30  


PRACTICE_TARGET_GOAL = 100
practice_targets_hit = 0
PRACTICE_MODE_INDEX = 3 

cheat_mode_active = False


player_pos = [0, 50, 100]  
player_yaw = 0.0  
player_pitch = 0.0 
camera_offset_z = 200 
fovY = 70 
targets = []
TARGET_WALL_Z = -300 
TARGET_MAX_X = 250
TARGET_MAX_Y = 200 
TARGET_BASE_RADIUS = 20
TARGET_SHRINK_RATE_MEDIUM = 0.1
TARGET_SHRINK_RATE_HARD = 0.3
TARGET_SPAWN_INTERVAL = 2.0 
last_target_spawn_time = 0


mouse_x, mouse_y = 500, 400 
crosshair_world_coords = [0,0,0]


bullet_tracers = []
TRACER_DURATION = 0.07 
TRACER_LENGTH = 50 


hit_effects = []
HIT_EFFECT_DURATION = 0.2 


def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18, r=1.0, g=1.0, b=1.0):
    glColor3f(r, g, b)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)  
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_menu():
    draw_text(450, 700, "AIMLAB 0.5", font=GLUT_BITMAP_HELVETICA_18)
    
    
    draw_text(300, 550, "Game Mode:", font=GLUT_BITMAP_HELVETICA_18)
    for i, mode in enumerate(menu_options["mode"]):
        is_persisted_selection = (i == selected_mode_idx)
        is_row_hovered = (menu_cursor_pos == 0)
        
        color_r, color_g, color_b = (1,1,1) 
        if is_persisted_selection:
            color_r, color_g, color_b = (0,1,0) 
        if is_row_hovered and is_persisted_selection: 
            color_r, color_g, color_b = (1,0,0) 

        draw_text(450 + i * 100, 550, mode, font=GLUT_BITMAP_HELVETICA_18, r=color_r, g=color_g, b=color_b)

    
    time_label_color_tuple = (1,1,1) if selected_mode_idx != PRACTICE_MODE_INDEX else (0.5,0.5,0.5)
    draw_text(300, 500, "Game Time:", font=GLUT_BITMAP_HELVETICA_18, r=time_label_color_tuple[0], g=time_label_color_tuple[1], b=time_label_color_tuple[2])
    
    for i, t_opt in enumerate(menu_options["time"]):
        display_this_time_opt = True
        if selected_mode_idx == PRACTICE_MODE_INDEX and t_opt != "N/A":
            display_this_time_opt = False
        elif selected_mode_idx != PRACTICE_MODE_INDEX and t_opt == "N/A":
            display_this_time_opt = False
        
        if not display_this_time_opt:
            continue

        is_persisted_selection = (i == selected_time_idx)
        is_row_hovered = (menu_cursor_pos == 1)

        color_r, color_g, color_b = (1,1,1) 
        
        if selected_mode_idx == PRACTICE_MODE_INDEX: 
            if t_opt == "N/A": 
                color_r, color_g, color_b = (0,1,0) 
                if is_row_hovered:
                    color_r, color_g, color_b = (1,0,0) 
            else:
                color_r, color_g, color_b = (0.5,0.5,0.5)
        else: 
            if is_persisted_selection:
                color_r, color_g, color_b = (0,1,0) 
            if is_row_hovered and is_persisted_selection: 
                color_r, color_g, color_b = (1,0,0) 
        
        draw_text(450 + i * 100, 500, t_opt, font=GLUT_BITMAP_HELVETICA_18, r=color_r, g=color_g, b=color_b)

    start_button_text = "START GAME"
    if selected_mode_idx == PRACTICE_MODE_INDEX:
        start_button_text = "START PRACTICE"
    
    color_r, color_g, color_b = (0.7,0.7,0.7) 
    if menu_cursor_pos == 2:
        color_r, color_g, color_b = (1,0,0) 
    draw_text(450, 400, start_button_text, font=GLUT_BITMAP_HELVETICA_18, r=color_r, g=color_g, b=color_b)

    draw_text(10, 50, "Controls: W/S (Navigate Menu), A/D (Change Options), Enter (Select/Start)", font=GLUT_BITMAP_HELVETICA_18)


def draw_targets():
    for target_obj in targets: 
        if target_obj['active']:
            glPushMatrix()
            glTranslatef(target_obj['x'], target_obj['y'], target_obj['z'])
            
            if target_obj.get('max_health', 1) == 2 and target_obj.get('current_health', 1) == 1:
                
                glColor3f(1.0, 0.5, 0.0) 
                gluSphere(gluNewQuadric(), target_obj['radius'], 20, 20)
            else:
                
                glColor3f(0.0, 0.7, 0.7) 
                gluSphere(gluNewQuadric(), target_obj['radius'], 20, 20)
            glPopMatrix()

def draw_wall():
    glColor3f(0.5, 0.5, 0.5) 
    glPushMatrix()
    glTranslatef(0, player_pos[1] + 50, TARGET_WALL_Z) 
    glScalef(TARGET_MAX_X * 2.5, TARGET_MAX_Y * 2.5, 10) 
    glutSolidCube(1)
    glPopMatrix()

def draw_game_ui():
    
    if selected_mode_idx == PRACTICE_MODE_INDEX:
        time_display_text = "Time: N/A"
        
    else:
        time_display_text = f"Time: {max(0, int(selected_game_duration - game_timer))}"
    
    draw_text(10, 770, time_display_text, font=GLUT_BITMAP_HELVETICA_18)
    draw_text(10, 740, f"Score: {score}", font=GLUT_BITMAP_HELVETICA_18)
    
    misses_y_pos = 710
    shots_fired_y_pos = 680
    accuracy_y_pos = 650

    if cheat_mode_active:
        draw_text(10, misses_y_pos, "Cheat Mode: ON", font=GLUT_BITMAP_HELVETICA_18, r=1.0, g=0.5, b=0.0)
        misses_y_pos -= 30
        shots_fired_y_pos -= 30
        accuracy_y_pos -= 30

    draw_text(10, misses_y_pos, f"Misses: {misses}", font=GLUT_BITMAP_HELVETICA_18)
    draw_text(10, shots_fired_y_pos, f"Shots Fired: {shots_fired}", font=GLUT_BITMAP_HELVETICA_18)
    
    calc_accuracy = 0.0
    if shots_fired > 0:
        calc_accuracy = (successful_hits / shots_fired) * 100 
    else: 
        calc_accuracy = 0.0 
    draw_text(10, accuracy_y_pos, f"Accuracy: {calc_accuracy:.2f}%", font=GLUT_BITMAP_HELVETICA_18)

    
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800) 
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
   
    glDisable(GL_DEPTH_TEST)

    glColor3f(0, 1, 0) 
    glPointSize(6)
    glBegin(GL_LINES)
   
    glVertex2f(mouse_x - 7, 800 - mouse_y)
    glVertex2f(mouse_x + 7, 800 - mouse_y)
    
    glVertex2f(mouse_x, 800 - mouse_y - 7)
    glVertex2f(mouse_x, 800 - mouse_y + 7)
    glEnd()
    glPointSize(1) 

    glPopMatrix() 
    glMatrixMode(GL_PROJECTION)
    glPopMatrix() 
    glMatrixMode(GL_MODELVIEW) 


def draw_game_over_screen():
    draw_text(400, 600, "GAME OVER", font=GLUT_BITMAP_HELVETICA_18)
    draw_text(400, 550, f"Final Score: {score}", font=GLUT_BITMAP_HELVETICA_18)
    draw_text(400, 520, f"Total Shots: {shots_fired}", font=GLUT_BITMAP_HELVETICA_18)
    calc_accuracy = 0.0
    if shots_fired > 0:
        calc_accuracy = (successful_hits / shots_fired) * 100 
    else:
        calc_accuracy = 0.0
    
    if selected_mode_idx == PRACTICE_MODE_INDEX:
        draw_text(380, 500, f"Targets Destroyed: {score}/{PRACTICE_TARGET_GOAL}", font=GLUT_BITMAP_HELVETICA_18) 
        draw_text(380, 470, f"Accuracy: {calc_accuracy:.2f}%", font=GLUT_BITMAP_HELVETICA_18)
        draw_text(350, 400, "Practice Complete! Press 'R' for Menu", font=GLUT_BITMAP_HELVETICA_18)
    else:
        draw_text(400, 490, f"Accuracy: {calc_accuracy:.2f}%", font=GLUT_BITMAP_HELVETICA_18)
        draw_text(350, 400, "Press 'R' to return to Menu", font=GLUT_BITMAP_HELVETICA_18)


def update_targets():
    global last_target_spawn_time, targets
    
    new_targets = []
    spawn_new_due_to_vanish_medium = False
    for target_obj in targets: 
        if not target_obj['active']:
            new_targets.append(target_obj)
            continue

        
        if selected_mode_idx == 1 or selected_mode_idx == 2: 
            target_obj['x'] += target_obj.get('vx', 0)
            target_obj['y'] += target_obj.get('vy', 0)

            
            if (target_obj['x'] - target_obj['radius']) < -TARGET_MAX_X:
                target_obj['x'] = -TARGET_MAX_X + target_obj['radius']
                target_obj['vx'] *= -1
            elif (target_obj['x'] + target_obj['radius']) > TARGET_MAX_X:
                target_obj['x'] = TARGET_MAX_X - target_obj['radius']
                target_obj['vx'] *= -1
            
            
            min_y_bounce = player_pos[1] - (TARGET_MAX_Y / 2)
            max_y_bounce = player_pos[1] + (TARGET_MAX_Y / 2)
            if (target_obj['y'] - target_obj['radius']) < min_y_bounce:
                target_obj['y'] = min_y_bounce + target_obj['radius']
                target_obj['vy'] *= -1
            elif (target_obj['y'] + target_obj['radius']) > max_y_bounce:
                target_obj['y'] = max_y_bounce - target_obj['radius']
                target_obj['vy'] *= -1

        
        shrunk_this_frame = False
        
        if selected_mode_idx == 0 or selected_mode_idx == PRACTICE_MODE_INDEX: 
            pass
        elif selected_mode_idx == 1: 
            target_obj['radius'] -= TARGET_SHRINK_RATE_MEDIUM
            shrunk_this_frame = True
        elif selected_mode_idx == 2: 
            target_obj['radius'] -= TARGET_SHRINK_RATE_HARD
            shrunk_this_frame = True
        
        if target_obj['radius'] <= 1:
            target_obj['active'] = False
            if selected_mode_idx == 1 and shrunk_this_frame: 
                spawn_new_due_to_vanish_medium = True
            elif selected_mode_idx == 2 and shrunk_this_frame:
                spawn_target()
        else:
            new_targets.append(target_obj)
    targets = new_targets

    if spawn_new_due_to_vanish_medium:
        spawn_target()


def spawn_target():
    global targets, last_target_spawn_time
    
    active_targets_count = sum(1 for t in targets if t['active'])

    if selected_mode_idx == 0 or selected_mode_idx == 1: 
        if active_targets_count >= 1:
            return
    elif selected_mode_idx == 2:
        if active_targets_count >= 3:
            return

    target_x = random.uniform(-TARGET_MAX_X, TARGET_MAX_X)
    target_y = player_pos[1] + random.uniform(-TARGET_MAX_Y/2, TARGET_MAX_Y) 
    
    
   
    is_multi_shot = random.random() < 0.2 
    max_hp = 2 if is_multi_shot else 1
    current_hp = max_hp

    
    vx, vy = 0, 0
    if selected_mode_idx == 1 or selected_mode_idx == 2: 
        speed_scale = 0.5 if selected_mode_idx == 1 else 1.0 
        vx = random.uniform(-1.5, 1.5) * speed_scale
        vy = random.uniform(-1.0, 1.0) * speed_scale
        if abs(vx) < 0.3: vx = 0.3 * (1 if vx >=0 else -1)
        if abs(vy) < 0.2: vy = 0.2 * (1 if vy >=0 else -1)


    targets.append({
        'x': target_x, 'y': target_y, 'z': TARGET_WALL_Z,
        'radius': TARGET_BASE_RADIUS,
        'active': True,
        'id': random.randint(0, 100000),
        'max_health': max_hp,
        'current_health': current_hp,
        'vx': vx,
        'vy': vy
    })

def reset_game():
    global score, misses, shots_fired, successful_hits, game_timer, game_start_time, targets, player_pos, player_yaw, player_pitch, current_state, selected_game_duration, practice_targets_hit
    score = 0
    misses = 0
    shots_fired = 0
    successful_hits = 0 
    game_timer = 0
    practice_targets_hit = 0 

    if selected_mode_idx == PRACTICE_MODE_INDEX:
        selected_game_duration = float('inf') 
    else:
        selected_duration_str = menu_options["time"][selected_time_idx].replace('s','')
        selected_game_duration = int(selected_duration_str)
        
    game_start_time = time.time()
    targets = []
    player_pos = [0, 50, 100] 
    player_yaw = 0.0
    player_pitch = 0.0
    last_target_spawn_time = time.time() 
    current_state = STATE_PLAYING
    spawn_target() 
    glutSetCursor(GLUT_CURSOR_NONE) 

def keyboardListener(key, x, y):
    global current_state, selected_mode_idx, selected_time_idx, menu_cursor_pos, player_pos, player_yaw, cheat_mode_active

    if current_state == STATE_MENU:
        if key == b'\r':
            if menu_cursor_pos == 2: 
                if selected_mode_idx == PRACTICE_MODE_INDEX:
                    
                    selected_time_idx = menu_options["time"].index("N/A")
                reset_game()
        elif key == b'w': 
            if selected_mode_idx == PRACTICE_MODE_INDEX and menu_cursor_pos == 2: 
                menu_cursor_pos = 0 
            else:
                menu_cursor_pos = (menu_cursor_pos - 1) % 3
        elif key == b's': 
            if selected_mode_idx == PRACTICE_MODE_INDEX and menu_cursor_pos == 0: 
                menu_cursor_pos = 2 
            else:
                menu_cursor_pos = (menu_cursor_pos + 1) % 3
        elif key == b'a': 
            if menu_cursor_pos == 0: 
                selected_mode_idx = (selected_mode_idx - 1) % len(menu_options["mode"])
                if selected_mode_idx == PRACTICE_MODE_INDEX: 
                    selected_time_idx = menu_options["time"].index("N/A")
            elif menu_cursor_pos == 1 and selected_mode_idx != PRACTICE_MODE_INDEX: 
                
                valid_times = [t for t in menu_options["time"] if t != "N/A"]
                current_time_value = menu_options["time"][selected_time_idx]
                try:
                    current_idx_in_valid = valid_times.index(current_time_value)
                    new_idx_in_valid = (current_idx_in_valid - 1 + len(valid_times)) % len(valid_times)
                    selected_time_idx = menu_options["time"].index(valid_times[new_idx_in_valid])
                except ValueError:
                    selected_time_idx = 0 

        elif key == b'd': 
            if menu_cursor_pos == 0: 
                selected_mode_idx = (selected_mode_idx + 1) % len(menu_options["mode"])
                if selected_mode_idx == PRACTICE_MODE_INDEX: 
                    selected_time_idx = menu_options["time"].index("N/A")
            elif menu_cursor_pos == 1 and selected_mode_idx != PRACTICE_MODE_INDEX: 
                valid_times = [t for t in menu_options["time"] if t != "N/A"]
                current_time_value = menu_options["time"][selected_time_idx]
                try:
                    current_idx_in_valid = valid_times.index(current_time_value)
                    new_idx_in_valid = (current_idx_in_valid + 1) % len(valid_times)
                    selected_time_idx = menu_options["time"].index(valid_times[new_idx_in_valid])
                except ValueError:
                     selected_time_idx = 0

    elif current_state == STATE_PLAYING:
        speed = 10.0
        
        if key == b'w':
            player_pos[2] -= speed * math.cos(player_yaw)
            player_pos[0] -= speed * math.sin(player_yaw)
        if key == b's':
            player_pos[2] += speed * math.cos(player_yaw)
            player_pos[0] += speed * math.sin(player_yaw)
        
        if key == b'a': 
            player_pos[0] -= speed * math.cos(player_yaw) 
            player_pos[2] += speed * math.sin(player_yaw) 
        if key == b'd': 
            player_pos[0] += speed * math.cos(player_yaw) 
            player_pos[2] -= speed * math.sin(player_yaw) 
        
        
        
        if key == b'm' or key == b'M':
            current_state = STATE_MENU
            glutSetCursor(GLUT_CURSOR_INHERIT)
        elif (key == b'c' or key == b'C'):
            cheat_mode_active = not cheat_mode_active
            if cheat_mode_active:
                print("Cheat Mode: ON")
            else:
                print("Cheat Mode: OFF")


    elif current_state == STATE_GAME_OVER:
        if key == b'r' or key == b'R': 
            current_state = STATE_MENU
            glutSetCursor(GLUT_CURSOR_INHERIT) 

    if key == b'\x1b': 
        glutLeaveMainLoop()


def specialKeyListener(key, x, y):
    
    pass

def passiveMouseMotion(x,y):
    global mouse_x, mouse_y, player_yaw, player_pitch
    if current_state != STATE_PLAYING:
        return

    
    mouse_x = x
    mouse_y = y 

   
    sensitivity = 0.002
    
    win_center_x = glutGet(GLUT_WINDOW_WIDTH) // 2
    win_center_y = glutGet(GLUT_WINDOW_HEIGHT) // 2

    if x == win_center_x and y == win_center_y: 
        return

    dx = x - win_center_x
    dy = y - win_center_y

    player_yaw -= dx * sensitivity 
    player_pitch -= dy * sensitivity 
    
    max_pitch = math.pi / 2 - 0.01 
    player_pitch = max(-max_pitch, min(max_pitch, player_pitch))

    glutWarpPointer(win_center_x, win_center_y)


def get_aim_vector():
    aim_x = -math.sin(player_yaw) * math.cos(player_pitch)
    aim_y = math.sin(player_pitch)
    aim_z = -math.cos(player_yaw) * math.cos(player_pitch)
    
    
    length = math.sqrt(aim_x**2 + aim_y**2 + aim_z**2)
    if length == 0: return (0,0,-1) 
    return (aim_x/length, aim_y/length, aim_z/length)


def perform_shot(aim_direction_override=None):
    global score, misses, shots_fired, successful_hits, targets, bullet_tracers, hit_effects

    shots_fired += 1
    if aim_direction_override:
        aim_dir = aim_direction_override
    else:
        aim_dir = get_aim_vector()

    muzzle_offset_forward = 10
    muzzle_offset_right = 3
    muzzle_offset_down = -2

    cam_right_x = math.cos(player_yaw)
    cam_right_z = -math.sin(player_yaw)

    tracer_start_pos = [
        player_pos[0] + aim_dir[0] * muzzle_offset_forward + cam_right_x * muzzle_offset_right,
        player_pos[1] + aim_dir[1] * muzzle_offset_forward + muzzle_offset_down, 
        player_pos[2] + aim_dir[2] * muzzle_offset_forward + cam_right_z * muzzle_offset_right
    ]
    
    tracer_end_pos = [
        tracer_start_pos[0] + aim_dir[0] * TRACER_LENGTH,
        tracer_start_pos[1] + aim_dir[1] * TRACER_LENGTH,
        tracer_start_pos[2] + aim_dir[2] * TRACER_LENGTH
    ]
    bullet_tracers.append({'start': tracer_start_pos, 'end': tracer_end_pos, 'time': time.time()})

    shot_hit_target = False

    for target_obj in list(targets): 
        if not target_obj['active']:
            continue

        oc_x = target_obj['x'] - player_pos[0]
        oc_y = target_obj['y'] - player_pos[1]
        oc_z = target_obj['z'] - player_pos[2]
        
        tca = oc_x * aim_dir[0] + oc_y * aim_dir[1] + oc_z * aim_dir[2]
        
        if tca < 0:
            continue
        
        d_squared = (oc_x**2 + oc_y**2 + oc_z**2) - tca**2
        radius_squared = target_obj['radius']**2
        
        if d_squared > radius_squared:
            continue
        
        thc = math.sqrt(radius_squared - d_squared)
        t0 = tca - thc

        if t0 > 0:
            shot_hit_target = True
            successful_hits += 1
            
            target_obj['current_health'] -= 1
            
            impact_point = [
                player_pos[0] + aim_dir[0] * t0,
                player_pos[1] + aim_dir[1] * t0,
                player_pos[2] + aim_dir[2] * t0
            ]
            effect_radius_multiplier = 0.15 if target_obj['current_health'] > 0 else 0.3
            hit_effects.append({'pos': impact_point, 'time': time.time(), 'radius': target_obj['radius'] * effect_radius_multiplier})

            if target_obj['current_health'] <= 0:
                target_obj['active'] = False
                score += 1 
                
                if selected_mode_idx == PRACTICE_MODE_INDEX:
                    practice_targets_hit += 1
                    if practice_targets_hit < PRACTICE_TARGET_GOAL:
                        spawn_target()
                elif selected_mode_idx == 0:  
                    spawn_target()
                elif selected_mode_idx == 1:  
                    spawn_target()
                elif selected_mode_idx == 2:  
                    spawn_target()
            break 

    if not shot_hit_target:
        misses += 1

def mouseListener(button, state, x, y):
    global score, misses, shots_fired, successful_hits, targets, bullet_tracers, hit_effects 
    if current_state != STATE_PLAYING:
        return

    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        perform_shot() 


def setupCamera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fovY, 1000.0/800.0, 0.1, 2000.0) 
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    
    
    look_at_x = player_pos[0] - math.sin(player_yaw) * math.cos(player_pitch) * 100 
    look_at_y = player_pos[1] + math.sin(player_pitch) * 100                     
    look_at_z = player_pos[2] - math.cos(player_yaw) * math.cos(player_pitch) * 100 
    gluLookAt(player_pos[0], player_pos[1], player_pos[2],  
              look_at_x, look_at_y, look_at_z,             
              0, 1, 0)                                     


def idle():
    global game_timer, current_state, last_target_spawn_time, practice_targets_hit, targets, player_pos, player_yaw, player_pitch, cheat_mode_active
    if current_state == STATE_PLAYING:
        current_time = time.time()

        if cheat_mode_active:
            active_targets = [t for t in targets if t['active']]
            if active_targets:
                target_to_aim = active_targets[0]
                
                direction_to_target = [
                    target_to_aim['x'] - player_pos[0],
                    target_to_aim['y'] - player_pos[1],
                    target_to_aim['z'] - player_pos[2]
                ]
                
                player_yaw = math.atan2(-direction_to_target[0], -direction_to_target[2])
                
                horizontal_dist = math.sqrt(direction_to_target[0]**2 + direction_to_target[2]**2)
                if horizontal_dist == 0: 
                    player_pitch = math.pi / 2 if direction_to_target[1] > 0 else -math.pi / 2
                else:
                    player_pitch = math.atan2(direction_to_target[1], horizontal_dist)
                
                max_pitch_val = math.pi / 2 - 0.01 
                player_pitch = max(-max_pitch_val, min(max_pitch_val, player_pitch))

                perform_shot() 
        
        if selected_mode_idx != PRACTICE_MODE_INDEX: 
            game_timer = current_time - game_start_time
            if game_timer >= selected_game_duration:
                current_state = STATE_GAME_OVER
                glutSetCursor(GLUT_CURSOR_INHERIT) 
                return 

        
        if (current_time - last_target_spawn_time > TARGET_SPAWN_INTERVAL):
            should_spawn_timed = False
            if selected_mode_idx == 2: 
                should_spawn_timed = True
            elif selected_mode_idx == PRACTICE_MODE_INDEX: 
                 active_targets_count = sum(1 for t in targets if t['active'])
                 if active_targets_count == 0 and practice_targets_hit < PRACTICE_TARGET_GOAL:
                    should_spawn_timed = True
            else: 
                active_targets_count = sum(1 for t in targets if t['active'])
                if active_targets_count == 0: 
                    should_spawn_timed = True
            
            if should_spawn_timed:
                spawn_target()
                last_target_spawn_time = current_time 
        
        
        current_tm = time.time() 
        bullet_tracers[:] = [tr for tr in bullet_tracers if current_tm - tr['time'] < TRACER_DURATION]
        hit_effects[:] = [eff for eff in hit_effects if current_tm - eff['time'] < HIT_EFFECT_DURATION]

        update_targets() 

        
        if selected_mode_idx == PRACTICE_MODE_INDEX and practice_targets_hit >= PRACTICE_TARGET_GOAL:
            current_state = STATE_GAME_OVER
            glutSetCursor(GLUT_CURSOR_INHERIT)

    glutPostRedisplay()


def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
     

    if current_state == STATE_MENU:
        
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(0, 1000, 0, 800)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        draw_menu()
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

    elif current_state == STATE_PLAYING:
        setupCamera()
        draw_wall()
        draw_targets()

        
        glColor3f(1, 1, 0.5) 
        glLineWidth(2.0)
        for tracer in bullet_tracers:
            glBegin(GL_LINES)
            glVertex3fv(tracer['start'])
            glVertex3fv(tracer['end'])
            glEnd()
        glLineWidth(1.0) 
        for effect in hit_effects:
            glPushMatrix()
            glTranslatef(effect['pos'][0], effect['pos'][1], effect['pos'][2])
            effect_age = time.time() - effect['time'] 
            effect_progress = min(1.0, effect_age / HIT_EFFECT_DURATION) 
            current_effect_radius = effect['radius'] * (1.0 - effect_progress)
            
            if current_effect_radius > 0.1: 
                glColor4f(1, 0.7, 0.1, 1.0) 
                gluSphere(gluNewQuadric(), current_effect_radius, 8, 8)
            glPopMatrix()
        
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluPerspective(fovY, 1000.0/800.0, 0.05, 50) 
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        
        glTranslatef(0.25, -0.20, -0.7) 
        
        
        glRotatef(player_pitch * 180 / math.pi, 1, 0, 0) 
        
        glRotatef(-5, 1, 0, 0) 
        glRotatef(5, 0, 1, 0)  

        
        glColor3f(0.82, 0.71, 0.55) 
        glPushMatrix()
        
        glTranslatef(0.0, -0.03, 0.05) 
        glPushMatrix()
        glRotatef(75, 1,0,0) 
        glRotatef(-15, 0,1,0) 
        gluCylinder(gluNewQuadric(), 0.03, 0.025, 0.15, 8, 2) 
        glPopMatrix()
        
        glTranslatef(0.0, -0.02, 0.12) 
        gluSphere(gluNewQuadric(), 0.04, 10, 10) 
        glPopMatrix()

        
        glColor3f(0.1, 0.1, 0.1) 
        glPushMatrix()
        
        glScalef(0.04, 0.04, 0.20) 
        glTranslatef(0, 0, 0) 
        glutSolidCube(1)    
        glPopMatrix()

        
        glColor3f(0.08, 0.08, 0.08) 
        glPushMatrix()
        glTranslatef(0, -0.03, -0.03) 
        glScalef(0.03, 0.07, 0.03) 
        glutSolidCube(1)
        glPopMatrix()

        glPopMatrix() 
        glMatrixMode(GL_PROJECTION)
        glPopMatrix() 
        glMatrixMode(GL_MODELVIEW) 

        draw_game_ui() 

    elif current_state == STATE_GAME_OVER:
        
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(0, 1000, 0, 800)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        draw_game_over_screen()
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

    glutSwapBuffers()


def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(1000, 800)
    glutInitWindowPosition(0, 0)
    wind = glutCreateWindow(b"AimLab 0.5")
    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutSpecialFunc(specialKeyListener) 
    glutMouseFunc(mouseListener)
    glutPassiveMotionFunc(passiveMouseMotion) 
    glutIdleFunc(idle)
    
    glutSetCursor(GLUT_CURSOR_INHERIT) 
    
    print("Starting AimLab 0.5...")
    print("Menu Controls: W/S (Navigate), A/D (Change Options), Enter (Select/Start)")
    print("Game Controls: W/A/S/D (Move), Mouse (Aim), Left Click (Shoot)")

    glutMainLoop()

if __name__ == "__main__":
    main()
