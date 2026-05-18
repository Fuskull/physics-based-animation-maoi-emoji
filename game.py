import pygame
import math
import random

# Initialize Pygame
pygame.init()
WIDTH, HEIGHT = 1280, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Swing & Shoot Game")
clock = pygame.time.Clock()

# Game state
game = {
    'score': 0,
    'health': 100,
    'shake_x': 0,
    'shake_y': 0,
    'shake_magnitude': 0,
    'state': 'menu'  # menu, playing, dead
}

class Vec2:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    
    def add(self, v):
        return Vec2(self.x + v.x, self.y + v.y)
    
    def sub(self, v):
        return Vec2(self.x - v.x, self.y - v.y)
    
    def mul(self, s):
        return Vec2(self.x * s, self.y * s)
    
    def length(self):
        return math.sqrt(self.x ** 2 + self.y ** 2)
    
    def normalize(self):
        l = self.length()
        return Vec2(self.x / l, self.y / l) if l > 0 else Vec2(0, 0)
    
    def dot(self, v):
        return self.x * v.x + self.y * v.y
    
    def cross(self, v):
        return self.x * v.y - self.y * v.x

class Particle:
    def __init__(self, x, y, mass=1, fixed=False):
        self.pos = Vec2(x, y)
        self.old_pos = Vec2(x, y)
        self.mass = mass
        self.fixed = fixed
    
    def update(self, dt):
        if self.fixed:
            return
        vel = self.pos.sub(self.old_pos)
        self.old_pos = Vec2(self.pos.x, self.pos.y)
        self.pos = self.pos.add(vel.mul(0.99))
        self.pos.y += 980 * dt * dt

class DistanceConstraint:
    def __init__(self, p1, p2, distance=None):
        self.p1 = p1
        self.p2 = p2
        self.distance = distance if distance else p1.pos.sub(p2.pos).length()
    
    def solve(self):
        delta = self.p2.pos.sub(self.p1.pos)
        dist = delta.length()
        if dist == 0:
            return
        diff = (dist - self.distance) / dist
        offset = delta.mul(diff * 0.5)
        if not self.p1.fixed:
            self.p1.pos = self.p1.pos.add(offset)
        if not self.p2.fixed:
            self.p2.pos = self.p2.pos.sub(offset)

class Rope:
    def __init__(self, x, y, length, segments):
        self.particles = []
        self.constraints = []
        seg_len = length / segments
        for i in range(segments + 1):
            fixed = i == 0
            self.particles.append(Particle(x, y + i * seg_len, 1, fixed))
        for i in range(len(self.particles) - 1):
            self.constraints.append(DistanceConstraint(self.particles[i], self.particles[i + 1]))
    
    def update(self, dt):
        for p in self.particles:
            p.update(dt)
        for _ in range(3):
            for c in self.constraints:
                c.solve()
    
    def draw(self, screen):
        for i in range(len(self.particles) - 1):
            p1 = self.particles[i]
            p2 = self.particles[i + 1]
            pygame.draw.line(screen, (139, 69, 19), (int(p1.pos.x), int(p1.pos.y)), 
                           (int(p2.pos.x), int(p2.pos.y)), 3)

class Cloth:
    def __init__(self, x, y, width, height, cols, rows):
        self.particles = []
        self.constraints = []
        self.cols = cols
        self.rows = rows
        dx = width / (cols - 1)
        dy = height / (rows - 1)
        
        for row in range(rows):
            for col in range(cols):
                fixed = row == 0 and (col == 0 or col == cols - 1)
                self.particles.append(Particle(x + col * dx, y + row * dy, 1, fixed))
        
        for row in range(rows):
            for col in range(cols):
                idx = row * cols + col
                if col < cols - 1:
                    self.constraints.append(DistanceConstraint(self.particles[idx], self.particles[idx + 1]))
                if row < rows - 1:
                    self.constraints.append(DistanceConstraint(self.particles[idx], self.particles[idx + cols]))
    
    def update(self, dt):
        for p in self.particles:
            p.update(dt)
        for _ in range(3):
            for c in self.constraints:
                c.solve()
    
    def check_collision(self, player_pos, player_radius):
        """Check if player is touching the cloth"""
        for p in self.particles:
            dist = player_pos.sub(p.pos).length()
            if dist < player_radius + 5:
                return True
        return False
    
    def draw(self, screen):
        for c in self.constraints:
            pygame.draw.line(screen, (74, 144, 226), (int(c.p1.pos.x), int(c.p1.pos.y)),
                           (int(c.p2.pos.x), int(c.p2.pos.y)), 1)

class RigidBody:
    def __init__(self, x, y, width, height, mass=1):
        self.pos = Vec2(x, y)
        self.vel = Vec2(0, 0)
        self.angle = 0
        self.angular_vel = 0
        self.mass = mass
        self.inv_mass = 1 / mass if mass > 0 else 0
        self.inertia = (mass * (width ** 2 + height ** 2)) / 12
        self.inv_inertia = 1 / self.inertia if self.inertia > 0 else 0
        self.width = width
        self.height = height
        self.restitution = 0.5
        self.friction = 0.3
        self.force = Vec2(0, 0)
        self.torque = 0
    
    def apply_force(self, force, point=None):
        self.force = self.force.add(force)
        if point:
            r = point.sub(self.pos)
            self.torque += r.cross(force)
    
    def update(self, dt):
        if self.inv_mass == 0:
            return
        acc = self.force.mul(self.inv_mass)
        acc.y += 980
        self.vel = self.vel.add(acc.mul(dt))
        self.pos = self.pos.add(self.vel.mul(dt))
        
        ang_acc = self.torque * self.inv_inertia
        self.angular_vel += ang_acc * dt
        self.angular_vel *= 0.98
        self.angle += self.angular_vel * dt
        
        self.force = Vec2(0, 0)
        self.torque = 0
    
    def get_vertices(self):
        cos = math.cos(self.angle)
        sin = math.sin(self.angle)
        hw = self.width / 2
        hh = self.height / 2
        return [
            Vec2(self.pos.x + (-hw * cos - -hh * sin), self.pos.y + (-hw * sin + -hh * cos)),
            Vec2(self.pos.x + (hw * cos - -hh * sin), self.pos.y + (hw * sin + -hh * cos)),
            Vec2(self.pos.x + (hw * cos - hh * sin), self.pos.y + (hw * sin + hh * cos)),
            Vec2(self.pos.x + (-hw * cos - hh * sin), self.pos.y + (-hw * sin + hh * cos))
        ]
    
    def draw(self, screen):
        verts = self.get_vertices()
        points = [(int(v.x), int(v.y)) for v in verts]
        pygame.draw.polygon(screen, (149, 165, 166), points)
        pygame.draw.polygon(screen, (127, 140, 141), points, 2)

class KinematicChain:
    def __init__(self, x, y, segments, segment_length):
        self.base_pos = Vec2(x, y)
        self.segments = []
        self.angles = [0] * segments
        self.segment_length = segment_length
        self.update_fk()
    
    def update_fk(self):
        self.segments = [self.base_pos]
        current_pos = Vec2(self.base_pos.x, self.base_pos.y)
        cumulative_angle = 0
        for angle in self.angles:
            cumulative_angle += angle
            current_pos = Vec2(
                current_pos.x + math.cos(cumulative_angle) * self.segment_length,
                current_pos.y + math.sin(cumulative_angle) * self.segment_length
            )
            self.segments.append(current_pos)
    
    def solve_ik(self, target, iterations=10):
        for _ in range(iterations):
            for i in range(len(self.segments) - 1, 0, -1):
                prev = self.segments[i - 1]
                target_pos = target if i == len(self.segments) - 1 else self.segments[i + 1]
                direction = target_pos.sub(prev).normalize()
                self.segments[i] = prev.add(direction.mul(self.segment_length))
            
            self.segments[0] = self.base_pos
            for i in range(1, len(self.segments)):
                direction = self.segments[i].sub(self.segments[i - 1]).normalize()
                self.segments[i] = self.segments[i - 1].add(direction.mul(self.segment_length))
    
    def update(self, target):
        self.solve_ik(target)
        self.update_fk()
    
    def draw(self, screen):
        for i in range(len(self.segments) - 1):
            pygame.draw.line(screen, (230, 126, 34), 
                           (int(self.segments[i].x), int(self.segments[i].y)),
                           (int(self.segments[i + 1].x), int(self.segments[i + 1].y)), 6)
        for i, seg in enumerate(self.segments):
            color = (192, 57, 43) if i == 0 else (211, 84, 0)
            pygame.draw.circle(screen, color, (int(seg.x), int(seg.y)), 5)

class Player:
    def __init__(self, x, y):
        self.pos = Vec2(x, y)
        self.vel = Vec2(0, 0)
        self.radius = 15
        self.rope = None
        self.on_ground = False
    
    def update(self, dt):
        if self.rope:
            end = self.rope.particles[-1]
            self.pos = Vec2(end.pos.x, end.pos.y)
            self.vel = end.pos.sub(end.old_pos).mul(1 / dt)
            self.on_ground = False
        else:
            self.vel.y += 980 * dt
            self.pos = self.pos.add(self.vel.mul(dt))
            
            # GAME OVER if touching ground
            if self.pos.y + self.radius > HEIGHT - 50:
                self.on_ground = True
                return True  # Signal game over
            else:
                self.on_ground = False
        return False
    
    def attach_rope(self, rope):
        self.rope = rope
        end = rope.particles[-1]
        # Pin the end particle to player position
        end.pos = Vec2(self.pos.x, self.pos.y)
        end.old_pos = Vec2(self.pos.x, self.pos.y)
        end.fixed = False
    
    def detach_rope(self):
        if self.rope:
            end = self.rope.particles[-1]
            # Use the actual velocity of the rope's end particle
            self.vel = end.pos.sub(end.old_pos).mul(60)
            self.rope = None
    
    def draw(self, screen):
        pygame.draw.circle(screen, (255, 107, 107), (int(self.pos.x), int(self.pos.y)), self.radius)
        pygame.draw.circle(screen, (255, 255, 255), (int(self.pos.x), int(self.pos.y)), self.radius, 2)

class Bullet:
    def __init__(self, x, y, vx, vy, is_enemy=False):
        self.pos = Vec2(x, y)
        self.vel = Vec2(vx, vy)
        self.radius = 4
        self.dead = False
        self.is_enemy = is_enemy  # Track if bullet is from enemy
    
    def update(self, dt):
        self.pos = self.pos.add(self.vel.mul(dt))
        if self.pos.x < 0 or self.pos.x > WIDTH or self.pos.y < 0 or self.pos.y > HEIGHT:
            self.dead = True
    
    def draw(self, screen):
        color = (255, 100, 100) if self.is_enemy else (255, 255, 0)
        pygame.draw.circle(screen, color, (int(self.pos.x), int(self.pos.y)), self.radius)

class Enemy:
    def __init__(self, x, y):
        self.pos = Vec2(x, y)
        self.vel = Vec2((random.random() - 0.5) * 100, 0)
        self.radius = 20
        self.dead = False
        self.health = 2
        self.shoot_timer = 0
    
    def update(self, dt, player_pos, player_vel):
        self.vel.y += 980 * dt
        self.pos = self.pos.add(self.vel.mul(dt))
        
        if self.pos.y + self.radius > HEIGHT - 50:
            self.pos.y = HEIGHT - 50 - self.radius
            self.vel.y = 0
        
        if self.pos.x < self.radius or self.pos.x > WIDTH - self.radius:
            self.vel.x *= -1
        
        # Check if player is moving slowly
        player_speed = player_vel.length()
        if player_speed < 50:  # Player is nearly stationary
            self.shoot_timer += dt
        else:
            self.shoot_timer = 0
        
        # Shoot at player if they haven't moved for 0.5 seconds
        if self.shoot_timer >= 0.5:
            self.shoot_timer = 0
            return True  # Signal to shoot
        return False
    
    def hit(self):
        self.health -= 1
        if self.health <= 0:
            self.dead = True
            return True
        return False
    
    def draw(self, screen):
        pygame.draw.circle(screen, (231, 76, 60), (int(self.pos.x), int(self.pos.y)), self.radius)
        pygame.draw.circle(screen, (192, 57, 43), (int(self.pos.x), int(self.pos.y)), self.radius, 2)

class ParticleEffect:
    def __init__(self, x, y, color):
        self.particles = []
        for _ in range(20):
            angle = random.random() * math.pi * 2
            speed = random.random() * 200 + 100
            self.particles.append({
                'pos': Vec2(x, y),
                'vel': Vec2(math.cos(angle) * speed, math.sin(angle) * speed),
                'life': 1,
                'color': color
            })
    
    def update(self, dt):
        for p in self.particles:
            p['vel'].y += 500 * dt
            p['pos'] = p['pos'].add(p['vel'].mul(dt))
            p['life'] -= dt * 2
        self.particles = [p for p in self.particles if p['life'] > 0]
    
    def draw(self, screen):
        for p in self.particles:
            alpha = int(p['life'] * 255)
            surf = pygame.Surface((6, 6), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*p['color'], alpha), (3, 3), 3)
            screen.blit(surf, (int(p['pos'].x - 3), int(p['pos'].y - 3)))

# Game objects
first_rope = Rope(100, 50, 200, 10)
player = Player(100, 200)
player.attach_rope(first_rope)

ropes = [first_rope]
cloths = []
bullets = []
enemies = []
particles = []
rigid_bodies = []
kinematic_chains = [
    KinematicChain(100, HEIGHT - 50, 4, 40),
    KinematicChain(WIDTH - 100, HEIGHT - 50, 3, 50)
]

# Level generation
camera_x = 0
level_progress = 0
next_obstacle_x = 300

def generate_obstacles():
    """Generate ropes, cloths, and platforms as player progresses"""
    global next_obstacle_x
    
    while next_obstacle_x < camera_x + WIDTH + 500:
        obstacle_type = random.choice(['rope', 'rope', 'platform'])
        
        if obstacle_type == 'rope':
            rope_x = next_obstacle_x
            rope_y = random.randint(50, 150)
            rope_length = random.randint(150, 250)
            ropes.append(Rope(rope_x, rope_y, rope_length, 10))
            next_obstacle_x += random.randint(250, 400)
        
        elif obstacle_type == 'platform':
            platform_x = next_obstacle_x
            platform_y = random.randint(250, 450)
            new_platform = RigidBody(platform_x, platform_y, 120, 20, 0)
            rigid_bodies.append(new_platform)
            
            # Spawn enemy on this platform
            enemy_x = platform_x + random.randint(-40, 40)
            enemy_y = platform_y - 30
            enemies.append(Enemy(enemy_x, enemy_y))
            
            next_obstacle_x += random.randint(200, 350)

# Initial obstacles
generate_obstacles()

enemy_spawn_timer = 0

def shake(magnitude):
    game['shake_magnitude'] = magnitude

def reset_game():
    """Reset game to initial state"""
    global player, ropes, cloths, bullets, enemies, particles, rigid_bodies
    global camera_x, level_progress, next_obstacle_x, enemy_spawn_timer
    
    # Create first rope
    first_rope = Rope(100, 50, 200, 10)
    ropes = [first_rope]
    
    # Create player attached to first rope
    player = Player(100, 200)
    player.attach_rope(first_rope)
    
    cloths = []
    bullets = []
    enemies = []
    particles = []
    rigid_bodies = []
    camera_x = 0
    level_progress = 0
    next_obstacle_x = 300
    enemy_spawn_timer = 0
    
    game['score'] = 0
    game['health'] = 100
    game['shake_magnitude'] = 0
    
    generate_obstacles()

def draw_menu(screen):
    """Draw start menu"""
    screen.fill((15, 52, 96))
    
    # Title
    title_font = pygame.font.Font(None, 96)
    title_text = title_font.render('SWING & SHOOT', True, (255, 255, 255))
    title_rect = title_text.get_rect(center=(WIDTH // 2, HEIGHT // 3))
    screen.blit(title_text, title_rect)
    
    # Subtitle
    subtitle_font = pygame.font.Font(None, 48)
    subtitle_text = subtitle_font.render('Physics Adventure', True, (74, 144, 226))
    subtitle_rect = subtitle_text.get_rect(center=(WIDTH // 2, HEIGHT // 3 + 80))
    screen.blit(subtitle_text, subtitle_rect)
    
    # Instructions
    inst_font = pygame.font.Font(None, 32)
    instructions = [
        "SPACE - Grab/Release ropes",
        "CLICK - Shoot enemies",
        "A/D - Control swing",
        "",
        "DON'T TOUCH THE LAVA!",
        "",
        "Press SPACE to Start"
    ]
    
    y_offset = HEIGHT // 2 + 50
    for i, line in enumerate(instructions):
        color = (255, 200, 0) if "LAVA" in line else (255, 255, 255)
        if "Press SPACE" in line:
            color = (100, 255, 100)
            # Blinking effect
            if pygame.time.get_ticks() % 1000 < 500:
                color = (150, 255, 150)
        
        text = inst_font.render(line, True, color)
        text_rect = text.get_rect(center=(WIDTH // 2, y_offset + i * 40))
        screen.blit(text, text_rect)

def draw_death_screen(screen):
    """Draw death screen"""
    screen.fill((20, 20, 30))
    
    # Game Over
    game_over_font = pygame.font.Font(None, 120)
    game_over_text = game_over_font.render('GAME OVER', True, (255, 50, 50))
    game_over_rect = game_over_text.get_rect(center=(WIDTH // 2, HEIGHT // 3))
    screen.blit(game_over_text, game_over_rect)
    
    # Stats
    stats_font = pygame.font.Font(None, 48)
    score_text = stats_font.render(f'Score: {game["score"]}', True, (255, 255, 255))
    score_rect = score_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    screen.blit(score_text, score_rect)
    
    distance_text = stats_font.render(f'Distance: {int(level_progress)}m', True, (255, 255, 255))
    distance_rect = distance_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 60))
    screen.blit(distance_text, distance_rect)
    
    # Restart prompt
    restart_font = pygame.font.Font(None, 36)
    restart_text = restart_font.render('Press SPACE to Restart', True, (100, 255, 100))
    if pygame.time.get_ticks() % 1000 < 500:
        restart_text = restart_font.render('Press SPACE to Restart', True, (150, 255, 150))
    restart_rect = restart_text.get_rect(center=(WIDTH // 2, HEIGHT - 100))
    screen.blit(restart_text, restart_rect)
    
    # Quit prompt
    quit_text = restart_font.render('Press ESC to Quit', True, (200, 200, 200))
    quit_rect = quit_text.get_rect(center=(WIDTH // 2, HEIGHT - 50))
    screen.blit(quit_text, quit_rect)

# Main game loop
running = True
dt = 1/60
keys = pygame.key.get_pressed()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            
            if event.key == pygame.K_SPACE:
                if game['state'] == 'menu':
                    game['state'] = 'playing'
                    reset_game()
                elif game['state'] == 'dead':
                    game['state'] = 'playing'
                    reset_game()
        
        if event.type == pygame.MOUSEBUTTONDOWN and game['state'] == 'playing':
            mouse_pos = Vec2(*pygame.mouse.get_pos())
            player_screen_x = player.pos.x - camera_x
            player_screen_pos = Vec2(player_screen_x, player.pos.y)
            direction = mouse_pos.sub(player_screen_pos).normalize()
            bullets.append(Bullet(player.pos.x, player.pos.y, direction.x * 800, direction.y * 800))
    
    keys = pygame.key.get_pressed()
    
    # Handle different game states
    if game['state'] == 'menu':
        draw_menu(screen)
        pygame.display.flip()
        clock.tick(60)
        continue
    
    if game['state'] == 'dead':
        draw_death_screen(screen)
        pygame.display.flip()
        clock.tick(60)
        continue
    
    # Game is playing
    # Player controls
    if player.rope:
        # Player is attached to rope - control the swing with A/D
        end = player.rope.particles[-1]
        
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            # Apply force to swing left
            end.pos.x -= 300 * dt
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            # Apply force to swing right
            end.pos.x += 300 * dt
    else:
        # Air control - player can move left/right
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            player.vel.x -= 500 * dt
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            player.vel.x += 500 * dt
        
        # Clamp horizontal velocity
        max_air_speed = 400
        if player.vel.x < -max_air_speed:
            player.vel.x = -max_air_speed
        if player.vel.x > max_air_speed:
            player.vel.x = max_air_speed
        
        # Add slight rightward drift
        player.vel.x += 50 * dt
    
    if keys[pygame.K_SPACE] and not player.rope:
        closest = None
        min_dist = 300
        for rope in ropes:
            dist = player.pos.sub(rope.particles[0].pos).length()
            if dist < min_dist:
                min_dist = dist
                closest = rope
        if closest:
            player.attach_rope(closest)
    elif not keys[pygame.K_SPACE] and player.rope:
        player.detach_rope()
    
    # Update camera to follow player
    camera_x = player.pos.x - WIDTH // 3
    level_progress = player.pos.x
    
    # Generate new obstacles
    generate_obstacles()
    
    # Update
    for r in ropes:
        r.update(dt)
    for c in cloths:
        c.update(dt)
    
    # Check if player touches ground
    game_over = player.update(dt)
    if game_over:
        game['health'] = 0
        game['state'] = 'dead'
    
    # Check if player can grab cloth
    for cloth in cloths:
        if cloth.check_collision(player.pos, player.radius) and not player.rope:
            # Player is on cloth, safe!
            player.vel.y = min(player.vel.y, 100)
    
    for b in bullets:
        b.update(dt)
    
    # Update enemies and handle their shooting
    for e in enemies:
        should_shoot = e.update(dt, player.pos, player.vel)
        if should_shoot:
            # Enemy shoots at player
            direction = player.pos.sub(e.pos).normalize()
            bullets.append(Bullet(e.pos.x, e.pos.y, direction.x * 600, direction.y * 600, is_enemy=True))
    
    for p in particles:
        p.update(dt)
    
    # Update rigid bodies
    for rb in rigid_bodies:
        rb.update(dt)
        verts = rb.get_vertices()
        for v in verts:
            if v.y > HEIGHT - 50:
                rb.pos.y -= (v.y - (HEIGHT - 50))
                rb.vel.y *= -rb.restitution
                rb.vel.x *= (1 - rb.friction)
        
        if rb.pos.x < rb.width / 2:
            rb.pos.x = rb.width / 2
            rb.vel.x *= -rb.restitution
        if rb.pos.x > WIDTH - rb.width / 2:
            rb.pos.x = WIDTH - rb.width / 2
            rb.vel.x *= -rb.restitution
        
        # Player collision
        if not player.rope:
            for v in verts:
                dist = player.pos.sub(v).length()
                if dist < player.radius + 10:
                    normal = player.pos.sub(v).normalize()
                    player.pos = v.add(normal.mul(player.radius + 10))
                    if normal.y < -0.5:
                        player.vel.y = max(0, player.vel.y)
                        player.vel.x += rb.vel.x * 0.5
                        player.on_ground = True
                    rb.apply_force(normal.mul(-500), v)
    
    # Update kinematic chains
    for chain in kinematic_chains:
        target = None
        min_dist = 250
        for enemy in enemies:
            dist = enemy.pos.sub(chain.base_pos).length()
            if dist < min_dist:
                min_dist = dist
                target = enemy
        
        if target:
            chain.update(target.pos)
            end_pos = chain.segments[-1]
            grab_dist = end_pos.sub(target.pos).length()
            if grab_dist < 25:
                pull_dir = chain.base_pos.sub(target.pos).normalize()
                target.vel = target.vel.add(pull_dir.mul(300 * dt))
                if random.random() < 0.05:
                    if target.hit():
                        game['score'] += 5
                        particles.append(ParticleEffect(target.pos.x, target.pos.y, (230, 126, 34)))
        else:
            idle_target = Vec2(chain.base_pos.x + math.sin(pygame.time.get_ticks() * 0.001) * 100,
                             chain.base_pos.y - 100)
            chain.update(idle_target)
    
    # Collisions
    for bullet in bullets:
        # Player bullets hit enemies
        if not bullet.is_enemy:
            for enemy in enemies:
                if not bullet.dead and not enemy.dead:
                    dist = bullet.pos.sub(enemy.pos).length()
                    if dist < bullet.radius + enemy.radius:
                        bullet.dead = True
                        if enemy.hit():
                            game['score'] += 10
                            particles.append(ParticleEffect(enemy.pos.x, enemy.pos.y, (255, 107, 107)))
        
        # Enemy bullets hit player
        else:
            if not bullet.dead:
                dist = bullet.pos.sub(player.pos).length()
                if dist < bullet.radius + player.radius:
                    bullet.dead = True
                    game['health'] -= 15
                    shake(15)
                    particles.append(ParticleEffect(player.pos.x, player.pos.y, (255, 200, 0)))
                    if game['health'] <= 0:
                        game['state'] = 'dead'
        
        # Bullets hit rigid bodies
        for rb in rigid_bodies:
            if not bullet.dead and rb.inv_mass > 0:
                for v in rb.get_vertices():
                    dist = bullet.pos.sub(v).length()
                    if dist < bullet.radius + 5:
                        bullet.dead = True
                        impulse = bullet.vel.mul(0.5)
                        rb.apply_force(impulse.mul(100), v)
                        particles.append(ParticleEffect(bullet.pos.x, bullet.pos.y, (255, 255, 0)))
    
    for enemy in enemies:
        dist = player.pos.sub(enemy.pos).length()
        if dist < player.radius + enemy.radius:
            game['health'] -= 10
            enemy.dead = True
            shake(20)
            particles.append(ParticleEffect(enemy.pos.x, enemy.pos.y, (255, 0, 0)))
            if game['health'] <= 0:
                game['state'] = 'dead'
    
    # Cleanup
    bullets = [b for b in bullets if not b.dead]
    enemies = [e for e in enemies if not e.dead]
    particles = [p for p in particles if len(p.particles) > 0]
    
    # Spawn enemies on the lava occasionally
    enemy_spawn_timer += dt
    if enemy_spawn_timer > 3:
        enemy_spawn_timer = 0
        spawn_x = camera_x + WIDTH + random.randint(0, 300)
        spawn_y = HEIGHT - 70
        enemies.append(Enemy(spawn_x, spawn_y))
    
    # Remove off-screen objects
    ropes = [r for r in ropes if r.particles[0].pos.x > camera_x - 200]
    rigid_bodies = [rb for rb in rigid_bodies if rb.pos.x > camera_x - 200]
    enemies = [e for e in enemies if e.pos.x > camera_x - 200]
    
    # Screen shake
    if game['shake_magnitude'] > 0:
        game['shake_x'] = (random.random() - 0.5) * game['shake_magnitude']
        game['shake_y'] = (random.random() - 0.5) * game['shake_magnitude']
        game['shake_magnitude'] *= 0.9
        if game['shake_magnitude'] < 0.5:
            game['shake_magnitude'] = 0
    
    # Draw
    screen.fill((15, 52, 96))
    
    # Apply camera offset
    cam_offset_x = int(camera_x)
    
    # Ground (LAVA - deadly!)
    pygame.draw.rect(screen, (200, 50, 20), (0, HEIGHT - 50, WIDTH, 50))
    # Lava effect
    for i in range(0, WIDTH, 40):
        pygame.draw.circle(screen, (255, 100, 0), (i + int(pygame.time.get_ticks() * 0.1) % 40, HEIGHT - 25), 15)
    
    for r in ropes:
        draw_x = int(r.particles[0].pos.x - cam_offset_x)
        if -200 < draw_x < WIDTH + 200:
            for i in range(len(r.particles) - 1):
                p1 = r.particles[i]
                p2 = r.particles[i + 1]
                pygame.draw.line(screen, (139, 69, 19), 
                               (int(p1.pos.x - cam_offset_x), int(p1.pos.y)), 
                               (int(p2.pos.x - cam_offset_x), int(p2.pos.y)), 3)
    
    for rb in rigid_bodies:
        if -200 < rb.pos.x - cam_offset_x < WIDTH + 200:
            verts = rb.get_vertices()
            points = [(int(v.x - cam_offset_x), int(v.y)) for v in verts]
            pygame.draw.polygon(screen, (149, 165, 166), points)
            pygame.draw.polygon(screen, (127, 140, 141), points, 2)
    
    for kc in kinematic_chains:
        for i in range(len(kc.segments) - 1):
            pygame.draw.line(screen, (230, 126, 34), 
                           (int(kc.segments[i].x - cam_offset_x), int(kc.segments[i].y)),
                           (int(kc.segments[i + 1].x - cam_offset_x), int(kc.segments[i + 1].y)), 6)
        for i, seg in enumerate(kc.segments):
            color = (192, 57, 43) if i == 0 else (211, 84, 0)
            pygame.draw.circle(screen, color, (int(seg.x - cam_offset_x), int(seg.y)), 5)
    
    # Player
    pygame.draw.circle(screen, (255, 107, 107), (int(player.pos.x - cam_offset_x), int(player.pos.y)), player.radius)
    pygame.draw.circle(screen, (255, 255, 255), (int(player.pos.x - cam_offset_x), int(player.pos.y)), player.radius, 2)
    
    for b in bullets:
        color = (255, 100, 100) if b.is_enemy else (255, 255, 0)
        pygame.draw.circle(screen, color, (int(b.pos.x - cam_offset_x), int(b.pos.y)), b.radius)
    
    for e in enemies:
        pygame.draw.circle(screen, (231, 76, 60), (int(e.pos.x - cam_offset_x), int(e.pos.y)), e.radius)
        pygame.draw.circle(screen, (192, 57, 43), (int(e.pos.x - cam_offset_x), int(e.pos.y)), e.radius, 2)
    
    for p in particles:
        for part in p.particles:
            alpha = int(part['life'] * 255)
            surf = pygame.Surface((6, 6), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*part['color'], alpha), (3, 3), 3)
            screen.blit(surf, (int(part['pos'].x - cam_offset_x - 3), int(part['pos'].y - 3)))
    
    # UI
    font = pygame.font.Font(None, 36)
    health_text = font.render(f'Health: {max(0, game["health"])}', True, (255, 255, 255))
    score_text = font.render(f'Score: {game["score"]}', True, (255, 255, 255))
    distance_text = font.render(f'Distance: {int(level_progress)}m', True, (255, 255, 255))
    screen.blit(health_text, (20, 20))
    screen.blit(score_text, (20, 60))
    screen.blit(distance_text, (20, 100))
    
    # Warning text
    warning_font = pygame.font.Font(None, 28)
    warning_text = warning_font.render("DON'T TOUCH THE LAVA!", True, (255, 200, 0))
    screen.blit(warning_text, (WIDTH // 2 - 150, HEIGHT - 80))
    
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
