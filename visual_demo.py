#!/usr/bin/env python3
"""Visual Physics Engine Demo using Pygame"""

import pygame
import sys
import math

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 800, 600
FPS = 60
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (76, 175, 80)
BLUE = (33, 150, 243)
RED = (244, 67, 54)
YELLOW = (255, 235, 59)

class Vector2D:
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y
    
    def add(self, v):
        return Vector2D(self.x + v.x, self.y + v.y)
    
    def subtract(self, v):
        return Vector2D(self.x - v.x, self.y - v.y)
    
    def multiply(self, scalar):
        return Vector2D(self.x * scalar, self.y * scalar)
    
    def magnitude(self):
        return math.sqrt(self.x**2 + self.y**2)
    
    def normalize(self):
        mag = self.magnitude()
        return Vector2D(self.x / mag, self.y / mag) if mag > 0 else Vector2D(0, 0)

class Particle:
    def __init__(self, x, y, mass=1.0):
        self.position = Vector2D(x, y)
        self.velocity = Vector2D(0, 0)
        self.mass = mass
        self.force = Vector2D(0, 0)
        self.pinned = False
    
    def clear_forces(self):
        self.force = Vector2D(0, 0)
    
    def add_force(self, force):
        self.force = self.force.add(force)
    
    def integrate(self, dt):
        if self.pinned:
            return
        acceleration = self.force.multiply(1 / self.mass)
        self.velocity = self.velocity.add(acceleration.multiply(dt))
        # Dampen velocity to prevent instability
        self.velocity = self.velocity.multiply(0.999)
        self.position = self.position.add(self.velocity.multiply(dt))
        
        # Keep particles in bounds
        if self.position.x < 0:
            self.position.x = 0
            self.velocity.x *= -0.5
        if self.position.x > WIDTH:
            self.position.x = WIDTH
            self.velocity.x *= -0.5
        if self.position.y > HEIGHT:
            self.position.y = HEIGHT
            self.velocity.y *= -0.5

class Spring:
    def __init__(self, pa, pb, rest_length, stiffness=100, damping=0.9):
        self.pa = pa
        self.pb = pb
        self.rest_length = rest_length
        self.stiffness = stiffness
        self.damping = damping
    
    def apply_force(self):
        diff = self.pb.position.subtract(self.pa.position)
        distance = diff.magnitude()
        if distance < 0.1:
            return
        
        direction = diff.normalize()
        displacement = distance - self.rest_length
        
        # Limit displacement to prevent explosion
        max_displacement = self.rest_length * 2
        if abs(displacement) > max_displacement:
            displacement = max_displacement if displacement > 0 else -max_displacement
        
        spring_force = direction.multiply(self.stiffness * displacement)
        
        rel_vel = self.pb.velocity.subtract(self.pa.velocity)
        damping_force = direction.multiply(
            (rel_vel.x * direction.x + rel_vel.y * direction.y) * self.damping
        )
        
        total_force = spring_force.add(damping_force)
        self.pa.add_force(total_force)
        self.pb.add_force(total_force.multiply(-1))

class ParticleSystem:
    def __init__(self):
        self.particles = []
    
    def emit(self, x, y, count=1):
        for i in range(count):
            p = Particle(x, y, 1.0)
            angle = (i / count) * 2 * math.pi
            speed = 100
            p.velocity = Vector2D(math.cos(angle) * speed, math.sin(angle) * speed)
            self.particles.append(p)
    
    def update(self, dt, gravity):
        for p in self.particles:
            p.clear_forces()
            p.add_force(gravity)
            p.integrate(dt)
        
        # Remove out of bounds particles
        self.particles = [p for p in self.particles if p.position.y < HEIGHT + 100]

class MassSpringSystem:
    def __init__(self):
        self.particles = []
        self.springs = []
    
    def create_rope(self, x, y, length, segments, stiffness=200, damping=5.0):
        segment_length = length / segments
        for i in range(segments + 1):
            p = Particle(x, y + i * segment_length, 0.5)
            if i == 0:
                p.pinned = True
            self.particles.append(p)
            
            if i > 0:
                spring = Spring(self.particles[i-1], self.particles[i], 
                              segment_length, stiffness, damping)
                self.springs.append(spring)
    
    def update(self, dt, gravity):
        for p in self.particles:
            p.clear_forces()
            if not p.pinned:
                p.add_force(gravity)
        
        for s in self.springs:
            s.apply_force()
        
        for p in self.particles:
            p.integrate(dt)

class PhysicsDemo:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Physics Engine Demo - Phases 1, 2, 3")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 36)
        
        self.gravity = Vector2D(0, 500)
        self.current_demo = 'particles'
        self.particle_system = ParticleSystem()
        self.spring_system = None
        self.dragged_particle = None
        
        self.setup_demo()
    
    def setup_demo(self):
        if self.current_demo == 'particles':
            self.particle_system = ParticleSystem()
            self.particle_system.emit(WIDTH // 2, 50, 10)
            self.spring_system = None
        elif self.current_demo == 'rope':
            self.particle_system = None
            self.spring_system = MassSpringSystem()
            self.spring_system.create_rope(WIDTH // 2, 50, 250, 12, 200, 5.0)
        elif self.current_demo == 'cloth':
            self.particle_system = None
            self.spring_system = MassSpringSystem()
            # Create cloth
            rows, cols = 10, 12
            width_cloth, height_cloth = 300, 250
            dx = width_cloth / (cols - 1)
            dy = height_cloth / (rows - 1)
            x_start, y_start = 250, 50
            
            particles_grid = []
            for row in range(rows):
                particles_grid.append([])
                for col in range(cols):
                    p = Particle(x_start + col * dx, y_start + row * dy, 0.3)
                    if row == 0 and (col == 0 or col == cols - 1):
                        p.pinned = True
                    particles_grid[row].append(p)
                    self.spring_system.particles.append(p)
            
            # Create springs
            for row in range(rows):
                for col in range(cols):
                    if col < cols - 1:
                        spring = Spring(particles_grid[row][col], 
                                      particles_grid[row][col + 1], dx, 150, 3.0)
                        self.spring_system.springs.append(spring)
                    if row < rows - 1:
                        spring = Spring(particles_grid[row][col], 
                                      particles_grid[row + 1][col], dy, 150, 3.0)
                        self.spring_system.springs.append(spring)
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    self.current_demo = 'particles'
                    self.setup_demo()
                elif event.key == pygame.K_2:
                    self.current_demo = 'rope'
                    self.setup_demo()
                elif event.key == pygame.K_3:
                    self.current_demo = 'cloth'
                    self.setup_demo()
                elif event.key == pygame.K_r:
                    self.setup_demo()
                elif event.key == pygame.K_SPACE:
                    if self.particle_system:
                        self.particle_system.emit(WIDTH // 2, 50, 5)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.find_dragged_particle(event.pos)
            elif event.type == pygame.MOUSEBUTTONUP:
                self.dragged_particle = None
            elif event.type == pygame.MOUSEMOTION:
                if self.dragged_particle:
                    self.dragged_particle.position = Vector2D(event.pos[0], event.pos[1])
                    self.dragged_particle.velocity = Vector2D(0, 0)
        
        return True
    
    def find_dragged_particle(self, pos):
        particles = []
        if self.particle_system:
            particles = self.particle_system.particles
        elif self.spring_system:
            particles = self.spring_system.particles
        
        for p in particles:
            dist = math.sqrt((p.position.x - pos[0])**2 + (p.position.y - pos[1])**2)
            if dist < 20:
                self.dragged_particle = p
                break
    
    def update(self, dt):
        # Limit dt to prevent instability
        dt = min(dt, 0.02)
        
        if self.particle_system:
            self.particle_system.update(dt, self.gravity)
            if len(self.particle_system.particles) < 5:
                self.particle_system.emit(WIDTH // 2, 50, 3)
        elif self.spring_system:
            self.spring_system.update(dt, self.gravity)
    
    def draw(self):
        self.screen.fill(BLACK)
        
        # Draw title
        if self.current_demo == 'particles':
            title = "Particle System (Phase 1)"
            color = YELLOW
        elif self.current_demo == 'rope':
            title = "Mass-Spring Rope (Phase 2)"
            color = GREEN
        else:
            title = "Mass-Spring Cloth (Phase 2)"
            color = GREEN
        
        title_surf = self.title_font.render(title, True, color)
        self.screen.blit(title_surf, (WIDTH // 2 - title_surf.get_width() // 2, 10))
        
        # Draw springs
        if self.spring_system:
            for spring in self.spring_system.springs:
                start_pos = (int(spring.pa.position.x), int(spring.pa.position.y))
                end_pos = (int(spring.pb.position.x), int(spring.pb.position.y))
                pygame.draw.line(self.screen, GREEN, start_pos, end_pos, 2)
        
        # Draw particles
        particles = []
        if self.particle_system:
            particles = self.particle_system.particles
        elif self.spring_system:
            particles = self.spring_system.particles
        
        for p in particles:
            if p.pinned:
                pygame.draw.circle(self.screen, RED, 
                                 (int(p.position.x), int(p.position.y)), 8)
            elif p == self.dragged_particle:
                pygame.draw.circle(self.screen, YELLOW, 
                                 (int(p.position.x), int(p.position.y)), 7)
            else:
                pygame.draw.circle(self.screen, WHITE, 
                                 (int(p.position.x), int(p.position.y)), 5)
        
        # Draw instructions
        instructions = [
            "Press 1: Particle System | 2: Rope | 3: Cloth",
            "Press R: Reset | SPACE: Add Particles",
            "Click and drag particles to interact"
        ]
        y_offset = HEIGHT - 70
        for instruction in instructions:
            text = self.font.render(instruction, True, WHITE)
            self.screen.blit(text, (10, y_offset))
            y_offset += 25
        
        # Draw particle count
        count_text = f"Particles: {len(particles)}"
        count_surf = self.font.render(count_text, True, GREEN)
        self.screen.blit(count_surf, (WIDTH - 150, HEIGHT - 30))
        
        pygame.display.flip()
    
    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            running = self.handle_events()
            self.update(dt)
            self.draw()
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    demo = PhysicsDemo()
    demo.run()
