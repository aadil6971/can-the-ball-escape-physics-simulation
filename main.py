#!/usr/bin/env python3
import argparse
import pygame
import pymunk
import pymunk.pygame_util
import random
import math
import sys
from pymunk import Vec2d

# -------------------- Utility Functions --------------------
def parse_color(s):
    """Parse a comma-separated string of three integers into an (R, G, B) tuple."""
    try:
        return tuple(int(x.strip()) for x in s.split(","))
    except Exception:
        return (255, 255, 255)

def parse_aspect_ratio(s):
    """
    Parse an aspect ratio given as a string.
    For example: "16:9" returns 16/9, "1:1" returns 1.0.
    If s does not contain a colon, try to convert it to float.
    """
    if ":" in s:
        parts = s.split(":")
        return float(parts[0]) / float(parts[1])
    else:
        return float(s)

def angle_in_range(angle, start, end):
    """
    Return True if 'angle' is in the interval [start, end] modulo 2π.
    Handles wrap-around.
    """
    angle %= (2 * math.pi)
    start %= (2 * math.pi)
    end %= (2 * math.pi)
    if start < end:
        return start <= angle <= end
    else:
        return angle >= start or angle <= end

# -------------------- Classes --------------------
class RotatingArcCircle:
    """
    A rotating arc acting as a physical barrier.
    Each arc covers between 80% and 90% of the circle's circumference.
    The arc is approximated using a number of segments (arc smoothness).
    """
    def __init__(self, radius, arc_start, arc_length, angular_velocity, center, space, color, segments=20):
        self.radius = radius
        self.arc_start = arc_start
        self.arc_length = arc_length  # in radians
        self.gap_length = 2 * math.pi - arc_length
        self.angular_velocity = angular_velocity
        self.center = center
        self.color = color

        # Create a kinematic body and add it to the space.
        self.body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        self.body.position = center
        self.body.angle = 0
        self.body.angular_velocity = angular_velocity
        space.add(self.body)

        self.segments = []
        self.points = []  # Local coordinates along the arc.
        for i in range(segments + 1):
            a = arc_start + (arc_length * i / segments)
            x = radius * math.cos(a)
            y = radius * math.sin(a)
            self.points.append((x, y))
        for i in range(segments):
            seg = pymunk.Segment(self.body, self.points[i], self.points[i+1], 2)
            seg.friction = 1.0
            seg.elasticity = 1.0
            seg.collision_type = 2
            space.add(seg)
            self.segments.append(seg)
        self.active = True

    def remove(self, space):
        """Remove the arc's collision segments from the space."""
        for seg in self.segments:
            space.remove(seg)
        self.active = False

    def draw(self, surface):
        if not self.active:
            return
        pts = []
        for point in self.points:
            wp = self.body.local_to_world(point)
            pts.append((int(wp[0]), int(wp[1])))
        if len(pts) > 1:
            pygame.draw.lines(surface, self.color, False, pts, 2)

    def get_gap_angles(self):
        gap_start = (self.arc_start + self.arc_length + self.body.angle) % (2 * math.pi)
        gap_end = (self.arc_start + 2 * math.pi + self.body.angle) % (2 * math.pi)
        return gap_start, gap_end

class Ball:
    """
    A dynamic ball with improved physics (damping).
    """
    def __init__(self, position, radius, space, color, speed, damping):
        self.radius = radius
        self.color = color
        mass = 1
        inertia = pymunk.moment_for_circle(mass, 0, radius)
        self.body = pymunk.Body(mass, inertia)
        self.body.position = position
        angle = random.uniform(0, 2 * math.pi)
        self.body.velocity = (speed * math.cos(angle), speed * math.sin(angle))
        self.body.damping = damping
        self.shape = pymunk.Circle(self.body, radius)
        self.shape.elasticity = 1.0
        self.shape.friction = 0.5
        self.shape.collision_type = 1
        space.add(self.body, self.shape)

    def draw(self, surface):
        pos = self.body.position
        pygame.draw.circle(surface, self.color, (int(pos.x), int(pos.y)), self.radius)

class Particle:
    """
    A small particle used for vanish effects.
    """
    def __init__(self, pos, vel, lifetime, color, radius):
        self.pos = Vec2d(*pos)
        self.vel = Vec2d(*vel)
        self.lifetime = lifetime
        self.color = color
        self.radius = radius

    def update(self, dt):
        self.pos += self.vel * dt
        self.lifetime -= dt

    def draw(self, surface):
        if self.lifetime > 0:
            pygame.draw.circle(surface, self.color, (int(self.pos.x), int(self.pos.y)), self.radius)

# -------------------- Main Function --------------------
def main(num_arcs, ball_radius, initial_balls, base_multiplier, particle_size,
         particle_count, ball_color, countdown, ball_speed, bg_color, arc_color,
         particle_color, aspect_ratio, ball_damping, arc_smoothness):
    
    pygame.init()
    pygame.mixer.init()

    # Load sound effects.
    try:
        random_hit_sounds = [
            pygame.mixer.Sound("./sounds/do.mp3"),
            pygame.mixer.Sound("./sounds/re.mp3"),
            pygame.mixer.Sound("./sounds/mi.mp3"),
            pygame.mixer.Sound("./sounds/fa.mp3"),
            pygame.mixer.Sound("./sounds/si.mp3")
        ]
        vanish_sound = pygame.mixer.Sound("./sounds/vanish.mp3")
    except Exception as e:
        print("Error loading sound files:", e)
        random_hit_sounds = []
        vanish_sound = None

    # Get available screen resolution.
    info = pygame.display.Info()
    avail_w, avail_h = info.current_w, info.current_h
    # Calculate window size based on the desired aspect ratio.
    if aspect_ratio and aspect_ratio > 0:
        # Try using the full available height.
        new_width = int(avail_h * aspect_ratio)
        if new_width > avail_w:
            new_width = avail_w
            new_height = int(avail_w / aspect_ratio)
        else:
            new_height = avail_h
        width, height = new_width, new_height
    else:
        width, height = avail_w, avail_h

    # Open full-screen.
    screen = pygame.display.set_mode((width, height), pygame.FULLSCREEN)
    pygame.display.set_caption("Full-Screen Circle Collision Simulation")
    clock = pygame.time.Clock()

    bg_color = bg_color
    arc_color = arc_color

    ball_hits = 0

    # Create physics space.
    space = pymunk.Space()
    space.gravity = (0, 0)
    center = (width // 2, height // 2)

    # Collision handler for ball–arc collisions.
    def ball_arc_collision(arbiter, space, data):
        nonlocal ball_hits
        ball_hits += 1
        if random_hit_sounds:
            random.choice(random_hit_sounds).play()
        return True

    space.add_collision_handler(1, 2).begin = ball_arc_collision

    # --- Create Balls ---
    balls = []
    base_radius_val = ball_radius * base_multiplier
    # Distribute initial balls evenly along the inner arc.
    for i in range(initial_balls):
        theta = (2 * math.pi * i) / initial_balls
        pos = (center[0] + base_radius_val * math.cos(theta),
               center[1] + base_radius_val * math.sin(theta))
        balls.append(Ball(pos, ball_radius, space, ball_color, ball_speed, ball_damping))

    # Collision handler for ball–ball collisions.
    def ball_ball_collision(arbiter, space, data):
        nonlocal ball_hits
        if len(data["balls"]) < 100:
            ball_hits += 1
            if random_hit_sounds:
                random.choice(random_hit_sounds).play()
            b1 = arbiter.shapes[0].body
            b2 = arbiter.shapes[1].body
            # Spawn new ball at a random location within the enclosing circle,
            # but far from both parents.
            if active_circle_index < len(circles):
                R_enclosing = circles[active_circle_index].radius
            else:
                R_enclosing = base_radius_val + (num_arcs - 1) * ball_radius
            candidate = None
            min_dist = 3 * ball_radius
            attempts = 0
            while attempts < 20:
                theta = random.uniform(0, 2 * math.pi)
                r = random.uniform(R_enclosing * 0.5, R_enclosing)
                candidate = (center[0] + r * math.cos(theta), center[1] + r * math.sin(theta))
                d1 = Vec2d(*candidate).get_distance(b1.position)
                d2 = Vec2d(*candidate).get_distance(b2.position)
                if d1 >= min_dist and d2 >= min_dist:
                    break
                attempts += 1
            new_ball = Ball(candidate, ball_radius, space, ball_color, ball_speed, ball_damping)
            data["balls"].append(new_ball)
        return True

    handler = space.add_collision_handler(1, 1)
    handler.data["balls"] = balls
    handler.begin = ball_ball_collision

    # --- Create Concentric Arcs ---
    radius_increment = ball_radius  # Distance between arcs equals ball radius.
    circles = []
    for i in range(num_arcs):
        radius = base_radius_val + i * radius_increment
        arc_fraction = random.uniform(0.8, 0.9)
        arc_length = 2 * math.pi * arc_fraction
        arc_start = random.uniform(0, 2 * math.pi)
        rot_speed = random.uniform(math.pi/4, math.pi/2)
        if random.choice([True, False]):
            rot_speed = -rot_speed
        circles.append(RotatingArcCircle(radius, arc_start, arc_length, rot_speed, center, space, arc_color, segments=arc_smoothness))

    active_circle_index = 0
    particles = []

    time_left = float(countdown)
    dt = 1 / 60.0

    font = pygame.font.SysFont("Arial", 30)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        time_left -= dt

        # Apply a small random impulse to each ball.
        for ball in balls:
            impulse_strength = 100 * dt
            angle = random.uniform(0, 2 * math.pi)
            impulse = (impulse_strength * math.cos(angle), impulse_strength * math.sin(angle))
            ball.body.apply_impulse_at_local_point(impulse)

        space.step(dt)

        # Check for outer escape.
        max_escape_index = active_circle_index
        for ball in balls:
            ball_pos = ball.body.position
            dx = ball_pos.x - center[0]
            dy = ball_pos.y - center[1]
            radial = Vec2d(dx, dy)
            if radial.length > 0 and ball.body.velocity.dot(radial) > 0:
                ball_outer = radial.length + ball.radius
                escape_index = int((ball_outer - base_radius_val) // radius_increment)
                if escape_index > max_escape_index:
                    max_escape_index = escape_index

        if max_escape_index > active_circle_index:
            for i in range(active_circle_index, min(max_escape_index, len(circles))):
                if circles[i].active:
                    circles[i].remove(space)
                    if vanish_sound:
                        vanish_sound.play()
                    for _ in range(particle_count):
                        part_angle = random.uniform(
                            circles[i].arc_start + circles[i].body.angle,
                            circles[i].arc_start + circles[i].arc_length + circles[i].body.angle
                        )
                        pos = (center[0] + circles[i].radius * math.cos(part_angle),
                               center[1] + circles[i].radius * math.sin(part_angle))
                        particle_speed = random.uniform(50, 150)
                        vel = (particle_speed * math.cos(part_angle), particle_speed * math.sin(part_angle))
                        particles.append(Particle(pos, vel, lifetime=1.0, color=particle_color, radius=particle_size))
            active_circle_index = max_escape_index
        else:
            if active_circle_index < len(circles):
                current_circle = circles[active_circle_index]
                if current_circle.active:
                    for ball in balls:
                        ball_pos = ball.body.position
                        dx = ball_pos.x - center[0]
                        dy = ball_pos.y - center[1]
                        radial = Vec2d(dx, dy)
                        if (radial.length + ball.radius) >= current_circle.radius and ball.body.velocity.dot(radial) > 0:
                            ball_angle = math.atan2(dy, dx) % (2 * math.pi)
                            gap_start, gap_end = current_circle.get_gap_angles()
                            if angle_in_range(ball_angle, gap_start, gap_end):
                                current_circle.remove(space)
                                if vanish_sound:
                                    vanish_sound.play()
                                for _ in range(particle_count):
                                    part_angle = random.uniform(
                                        current_circle.arc_start + current_circle.body.angle,
                                        current_circle.arc_start + current_circle.arc_length + current_circle.body.angle
                                    )
                                    pos = (center[0] + current_circle.radius * math.cos(part_angle),
                                           center[1] + current_circle.radius * math.sin(part_angle))
                                    particle_speed = random.uniform(50, 150)
                                    vel = (particle_speed * math.cos(part_angle), particle_speed * math.sin(part_angle))
                                    particles.append(Particle(pos, vel, lifetime=1.0, color=particle_color, radius=particle_size))
                                active_circle_index += 1
                                for ball in balls:
                                    vx, vy = ball.body.velocity
                                    ball.body.velocity = (vx * 1.1, vy * 1.1)
                                break

        for p in particles:
            p.update(dt)
        particles = [p for p in particles if p.lifetime > 0]

        screen.fill(bg_color)
        for circle in circles:
            circle.draw(screen)
        for ball in balls:
            ball.draw(screen)
        for p in particles:
            p.draw(screen)

        hits_text = font.render(f"Hits: {ball_hits}", True, (255,255,255))
        screen.blit(hits_text, (20, 20))
        arcs_left = len(circles) - active_circle_index
        arcs_text = font.render(f"Arcs Left: {arcs_left}", True, (255,255,255))
        screen.blit(arcs_text, (20, 50))
        timer_text = font.render(f"Time: {max(0, int(time_left))} sec", True, (255,255,255))
        screen.blit(timer_text, (width - 220, 20))
        ball_color_text = font.render(f"Ball Color: {ball_color}", True, (255,255,255))
        screen.blit(ball_color_text, (20, 80))

        pygame.display.flip()
        clock.tick(60)

        if active_circle_index >= len(circles) and arcs_left < -100:
            running = False
            game_won = True
        elif time_left <= 0:
            running = False
            game_won = False
    # Before showing the end message, restore windowed mode (remove FULLSCREEN)
    screen = pygame.display.set_mode((width, height))
    end_font = pygame.font.SysFont("Arial", 60)
    end_text = end_font.render("The End", True, (0,255,0) if game_won else (255,0,0))
    end_rect = end_text.get_rect(center=(width//2, height//2))
    end_display_time = 3
    end_timer = 0
    while end_timer < end_display_time:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        screen.fill(bg_color)
        screen.blit(end_text, end_rect)
        pygame.display.flip()
        dt_end = clock.tick(60) / 1000.0
        end_timer += dt_end

    pygame.quit()
    sys.exit()

# -------------------- Command-Line Argument Parsing --------------------
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Circle Collision Simulation with configurable parameters.")
    parser.add_argument("--arcs", "-a", type=int, default=100,
                        help="Number of concentric arcs (default: 100)")
    parser.add_argument("--ball_size", "-b", type=int, default=6,
                        help="Ball radius (default: 6)")
    parser.add_argument("--initial_balls", "-n", type=int, default=2,
                        help="Number of initial balls (default: 2)")
    parser.add_argument("--base_multiplier", "-m", type=int, default=50,
                        help="Inner arc radius multiplier relative to ball size (default: 50)")
    parser.add_argument("--particle_size", "-ps", type=int, default=2,
                        help="Particle size (default: 2)")
    parser.add_argument("--particle_count", "-pc", type=int, default=20,
                        help="Number of particles spawned when an arc vanishes (default: 20)")
    parser.add_argument("--ball_color", "-bc", type=str, default="255,255,0",
                        help="Ball color as R,G,B (default: 255,255,0)")
    parser.add_argument("--countdown", "-cd", type=int, default=60,
                        help="Countdown timer duration in seconds (default: 60)")
    parser.add_argument("--ball_speed", "-s", type=int, default=150,
                        help="Initial ball speed (default: 150)")
    parser.add_argument("--bg_color", "-bg", type=str, default="20,20,30",
                        help="Background color as R,G,B (default: 20,20,30)")
    parser.add_argument("--arc_color", "-ac", type=str, default="255,255,255",
                        help="Arc color as R,G,B (default: 255,255,255)")
    parser.add_argument("--particle_color", "-pcolor", type=str, default="255,255,255",
                        help="Particle color as R,G,B (default: 255,255,255)")
    parser.add_argument("--aspect_ratio", "-ar", type=str, default="16:9",
                        help="Aspect ratio of screen (e.g., '16:9', default: 16:9)")
    parser.add_argument("--ball_damping", "-bd", type=float, default=0.99,
                        help="Ball damping (default: 0.99)")
    parser.add_argument("--arc_smoothness", "-as", type=int, default=20,
                        help="Arc smoothness (number of segments; default: 20)")
    args = parser.parse_args()

    ball_color = parse_color(args.ball_color)
    bg_color = parse_color(args.bg_color)
    arc_color = parse_color(args.arc_color)
    particle_color = parse_color(args.particle_color)
    aspect_ratio = parse_aspect_ratio(args.aspect_ratio)

    main(args.arcs, args.ball_size, args.initial_balls, args.base_multiplier,
         args.particle_size, args.particle_count, ball_color, args.countdown,
         args.ball_speed, bg_color, arc_color, particle_color, aspect_ratio, args.ball_damping, args.arc_smoothness)
