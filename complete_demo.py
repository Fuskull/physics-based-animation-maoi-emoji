"""Complete Physics Engine Demo - Phases 1, 2, 3
Press 1-5 to switch demos | P: Toggle PBD/Spring | W: Wind | G: Gravity | C: Collisions | R: Reset
"""
import pygame
import math

pygame.init()

WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Physics Engine - Phases 1, 2, 3")
clock = pygame.time.Clock()

# MODIFIERS
gravity = 500
wind = 0
stiffness = 200
damping = 5.0
pbd_stiffness = 1.0
pbd_iterations = 10
bounce = 0.6
friction = 0.95
ground_y = HEIGHT - 50

# State
demo = 'particles'
use_pbd = False
gravity_on = True
collisions_on = True
particles = []
connections = []
dragging = None

def reset():
    global particles, connections, dragging
    particles = []
    connections = []
    dragging = None
    
    if demo == 'particles':
        for i in range(15):
            angle = (i / 15) * 2 * math.pi
            particles.append({
                'x': WIDTH/2, 'y': 100,
                'vx': math.cos(angle) * 150, 'vy': math.sin(angle) * 150,
                'px': WIDTH/2, 'py': 100, 'pinned': False
            })
    
    elif demo == 'rope':
        seg_len = 15
        for i in range(21):
            particles.append({
                'x': WIDTH/2, 'y': 100 + i*seg_len,
                'vx': 0, 'vy': 0,
                'px': WIDTH/2, 'py': 100 + i*seg_len,
                'pinned': i == 0
            })
        for i in range(20):
            connections.append({'p1': i, 'p2': i+1, 'len': seg_len})
    
    elif demo == 'cloth':
        rows, cols = 12, 15
        w, h = 400, 300
        dx, dy = w/(cols-1), h/(rows-1)
        x0, y0 = 200, 80
        
        for row in range(rows):
            for col in range(cols):
                particles.append({
                    'x': x0 + col*dx, 'y': y0 + row*dy,
                    'vx': 0, 'vy': 0,
                    'px': x0 + col*dx, 'py': y0 + row*dy,
                    'pinned': row == 0 and (col == 0 or col == cols-1)
                })
        
        for row in range(rows):
            for col in range(cols):
                idx = row * cols + col
                if col < cols-1:
                    connections.append({'p1': idx, 'p2': idx+1, 'len': dx})
                if row < rows-1:
                    connections.append({'p1': idx, 'p2': idx+cols, 'len': dy})

reset()

while True:
    dt = min(clock.tick(60) / 1000.0, 0.02)
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1:
                demo, use_pbd = 'particles', False
                reset()
            elif event.key == pygame.K_2:
                demo, use_pbd = 'rope', False
                reset()
            elif event.key == pygame.K_3:
                demo, use_pbd = 'cloth', False
                reset()
            elif event.key == pygame.K_4:
                demo, use_pbd = 'rope', True
                reset()
            elif event.key == pygame.K_5:
                demo, use_pbd = 'cloth', True
                reset()
            elif event.key == pygame.K_p:
                use_pbd = not use_pbd
                reset()
            elif event.key == pygame.K_w:
                wind = 300 if wind == 0 else 0
            elif event.key == pygame.K_g:
                gravity_on = not gravity_on
            elif event.key == pygame.K_c:
                collisions_on = not collisions_on
            elif event.key == pygame.K_r:
                reset()
            elif event.key == pygame.K_SPACE and demo == 'particles':
                for i in range(5):
                    angle = (i/5) * 2 * math.pi
                    particles.append({
                        'x': WIDTH/2, 'y': 100,
                        'vx': math.cos(angle)*100, 'vy': math.sin(angle)*100,
                        'px': WIDTH/2, 'py': 100, 'pinned': False
                    })
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            for i, p in enumerate(particles):
                if math.sqrt((p['x']-event.pos[0])**2 + (p['y']-event.pos[1])**2) < 20:
                    dragging = i
                    break
        
        if event.type == pygame.MOUSEBUTTONUP:
            dragging = None
        
        if event.type == pygame.MOUSEMOTION and dragging is not None:
            particles[dragging]['x'] = event.pos[0]
            particles[dragging]['y'] = event.pos[1]
            particles[dragging]['px'] = event.pos[0]
            particles[dragging]['py'] = event.pos[1]
            particles[dragging]['vx'] = 0
            particles[dragging]['vy'] = 0
    
    # Physics
    if use_pbd:
        # PBD: Predict
        for i, p in enumerate(particles):
            if p['pinned'] or i == dragging:
                continue
            p['px'], p['py'] = p['x'], p['y']
            if gravity_on:
                p['vy'] += dt * gravity
            p['vx'] += dt * wind
            p['x'] += p['vx'] * dt
            p['y'] += p['vy'] * dt
        
        # PBD: Solve
        for _ in range(pbd_iterations):
            for c in connections:
                p1, p2 = particles[c['p1']], particles[c['p2']]
                dx, dy = p2['x']-p1['x'], p2['y']-p1['y']
                dist = math.sqrt(dx*dx + dy*dy)
                if dist < 0.1:
                    continue
                error = (dist - c['len']) / dist * pbd_stiffness * 0.5
                if not p1['pinned']:
                    p1['x'] += dx * error
                    p1['y'] += dy * error
                if not p2['pinned']:
                    p2['x'] -= dx * error
                    p2['y'] -= dy * error
        
        # PBD: Update velocity
        for i, p in enumerate(particles):
            if p['pinned'] or i == dragging:
                continue
            p['vx'] = (p['x'] - p['px']) / dt
            p['vy'] = (p['y'] - p['py']) / dt
    
    else:
        # Spring: Forces
        for i, p in enumerate(particles):
            if p['pinned'] or i == dragging:
                continue
            if gravity_on:
                p['vy'] += dt * gravity
            p['vx'] += dt * wind
        
        # Spring: Apply
        for c in connections:
            p1, p2 = particles[c['p1']], particles[c['p2']]
            dx, dy = p2['x']-p1['x'], p2['y']-p1['y']
            dist = math.sqrt(dx*dx + dy*dy)
            if dist < 0.1:
                continue
            
            force = stiffness * (dist - c['len'])
            fx = (dx/dist) * force + damping * (p2['vx']-p1['vx'])
            fy = (dy/dist) * force + damping * (p2['vy']-p1['vy'])
            
            if not p1['pinned']:
                p1['vx'] += dt * fx
                p1['vy'] += dt * fy
            if not p2['pinned']:
                p2['vx'] -= dt * fx
                p2['vy'] -= dt * fy
        
        # Spring: Update
        for i, p in enumerate(particles):
            if p['pinned'] or i == dragging:
                continue
            p['vx'] *= 0.999
            p['vy'] *= 0.999
            p['x'] += dt * p['vx']
            p['y'] += dt * p['vy']
    
    # Collisions
    if collisions_on:
        for i, p in enumerate(particles):
            if p['pinned'] or i == dragging:
                continue
            
            # Ground
            if p['y'] + 5 >= ground_y:
                p['y'] = ground_y - 5
                p['vy'] *= -bounce
                p['vx'] *= friction
                if abs(p['vy']) < 10:
                    p['vy'] = 0
            
            # Walls
            if p['x'] <= 5:
                p['x'], p['vx'] = 5, -p['vx']*bounce
            if p['x'] >= WIDTH-5:
                p['x'], p['vx'] = WIDTH-5, -p['vx']*bounce
            if p['y'] <= 5:
                p['y'], p['vy'] = 5, -p['vy']*bounce
        
        # Particle collision
        if demo == 'particles':
            for i in range(len(particles)):
                for j in range(i+1, len(particles)):
                    p1, p2 = particles[i], particles[j]
                    dx, dy = p2['x']-p1['x'], p2['y']-p1['y']
                    dist = math.sqrt(dx*dx + dy*dy)
                    if dist < 10 and dist > 0:
                        nx, ny = dx/dist, dy/dist
                        overlap = 10 - dist
                        p1['x'] -= nx * overlap * 0.5
                        p1['y'] -= ny * overlap * 0.5
                        p2['x'] += nx * overlap * 0.5
                        p2['y'] += ny * overlap * 0.5
                        
                        dot = (p2['vx']-p1['vx'])*nx + (p2['vy']-p1['vy'])*ny
                        if dot < 0:
                            p1['vx'] += nx * dot * bounce
                            p1['vy'] += ny * dot * bounce
                            p2['vx'] -= nx * dot * bounce
                            p2['vy'] -= ny * dot * bounce
    
    # Cleanup
    if demo == 'particles':
        particles = [p for p in particles if p['y'] < HEIGHT + 200]
    
    # Draw
    screen.fill((0, 0, 0))
    
    # Ground
    pygame.draw.line(screen, (255, 255, 255), (0, ground_y), (WIDTH, ground_y), 2)
    
    # Connections
    color = (33, 150, 243) if use_pbd else (76, 175, 80)
    for c in connections:
        p1, p2 = particles[c['p1']], particles[c['p2']]
        pygame.draw.line(screen, color, (int(p1['x']), int(p1['y'])), (int(p2['x']), int(p2['y'])), 2)
    
    # Particles
    for i, p in enumerate(particles):
        if p['pinned']:
            color, radius = (244, 67, 54), 8
        elif i == dragging:
            color, radius = (255, 235, 59), 7
        else:
            color, radius = (255, 255, 255), 5
        pygame.draw.circle(screen, color, (int(p['x']), int(p['y'])), radius)
    
    # UI
    font = pygame.font.Font(None, 24)
    
    demo_name = {
        'particles': 'Particle System (Phase 1)',
        'rope': f'Rope (Phase {"3-PBD" if use_pbd else "2-Spring"})',
        'cloth': f'Cloth (Phase {"3-PBD" if use_pbd else "2-Spring"})'
    }
    
    texts = [
        demo_name[demo],
        f"Particles: {len(particles)} | Method: {'PBD' if use_pbd else 'Spring'}",
        f"Gravity: {'ON' if gravity_on else 'OFF'} | Wind: {'ON' if wind else 'OFF'} | Collisions: {'ON' if collisions_on else 'OFF'}",
    ]
    
    for i, text in enumerate(texts):
        surf = font.render(text, True, (0, 255, 255) if i == 0 else (255, 255, 255))
        screen.blit(surf, (10, 10 + i*25))
    
    controls = font.render("1-5: Demos | P: Toggle | W: Wind | G: Gravity | C: Collisions | R: Reset", True, (128, 128, 128))
    screen.blit(controls, (10, HEIGHT - 30))
    
    pygame.display.flip()
