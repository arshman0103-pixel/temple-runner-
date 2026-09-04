import pygame
import random
import math
import os
import json

# ==========================================
# CONSTANTS & CONFIGURATION
# ==========================================
WIDTH, HEIGHT = 800, 600
FPS = 60

# Colors
COLOR_BG = (20, 15, 30)
COLOR_SKY = (40, 25, 50)
COLOR_TEMPLE = (70, 55, 45)
COLOR_PATH = (100, 80, 60)
COLOR_PATH_LINE = (130, 105, 80)
COLOR_WHITE = (255, 255, 255)
COLOR_GOLD = (255, 215, 0)
COLOR_RED = (220, 50, 50)
COLOR_GREEN = (50, 200, 80)

# Game Parameters
VANISHING_X = WIDTH // 2
VANISHING_Y = 220
PATH_BOTTOM_WIDTH = 500
PATH_TOP_WIDTH = 40
LANES = [-1, 0, 1]  # Left, Center, Right

HIGH_SCORE_FILE = "highscore.json"

# ==========================================
# ASSET GENERATOR (Procedural Graphics/Audio)
# ==========================================
def create_synthesized_sound(freq, duration, type_wave="square"):
    """Generates simple sound effects using Pygame arrays."""
    sample_rate = 22050
    n_samples = int(sample_rate * duration)
    buf = bytearray()
    
    for i in range(n_samples):
        t = float(i) / sample_rate
        if type_wave == "square":
            val = 127 if (int(t * freq * 2) % 2) == 0 else -128
        elif type_wave == "saw":
            val = int((t * freq % 1.0) * 255 - 128)
        else:
            val = int(math.sin(2 * math.pi * freq * t) * 127)
        
        # Fade out to prevent clicks
        attenuation = max(0.0, 1.0 - (i / n_samples))
        val = int(val * attenuation)
        buf.append(val & 0xFF)
        
    try:
        return pygame.mixer.Sound(buffer=bytes(buf))
    except Exception:
        return None

# ==========================================
# HELPER FUNCTIONS
# ==========================================
def project_3d(lane, z, height_offset=0):
    """
    Transforms 3D game coordinates into 2D screen coordinates.
    z ranges from 1.0 (far vanishing point) to 0.0 (closest to screen).
    """
    scale = 1.0 - z
    
    # Path width at depth z
    current_path_w = PATH_TOP_WIDTH + (PATH_BOTTOM_WIDTH - PATH_TOP_WIDTH) * scale
    
    # Calculate X position based on lane
    lane_spacing = current_path_w / 3.0
    x_center = VANISHING_X + (lane * lane_spacing)
    
    # Calculate Y position along the perspective line
    y_center = VANISHING_Y + (HEIGHT - VANISHING_Y) * scale - (height_offset * scale * 120)
    
    return x_center, y_center, scale

def load_high_score():
    if os.path.exists(HIGH_SCORE_FILE):
        try:
            with open(HIGH_SCORE_FILE, "r") as f:
                return json.load(f).get("high_score", 0)
        except Exception:
            return 0
    return 0

def save_high_score(score):
    try:
        with open(HIGH_SCORE_FILE, "w") as f:
            json.dump({"high_score": score}, f)
    except Exception:
        pass

# ==========================================
# GAME ENTITIES
# ==========================================
class Player:
    def __init__(self):
        self.lane = 0  # -1: Left, 0: Center, 1: Right
        self.target_lane = 0
        self.lane_x_offset = 0.0  # Smooth transition factor (-1.0 to 1.0)
        
        # Action states
        self.is_jumping = False
        self.jump_v = 0.0
        self.y_height = 0.0  # Height off ground
        
        self.is_sliding = False
        self.slide_timer = 0
        
        # Animation frame counter
        self.anim_frame = 0

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_LEFT, pygame.K_a) and self.target_lane > -1:
                self.target_lane -= 1
            elif event.key in (pygame.K_RIGHT, pygame.K_d) and self.target_lane < 1:
                self.target_lane += 1
            elif event.key in (pygame.K_UP, pygame.K_w, pygame.K_SPACE) and not self.is_jumping:
                self.is_jumping = True
                self.jump_v = 0.08  # Initial jump velocity
                self.is_sliding = False
            elif event.key in (pygame.K_DOWN, pygame.K_s) and not self.is_sliding:
                self.is_sliding = True
                self.slide_timer = 30
                if self.is_jumping:  # Quick-drop if sliding mid-air
                    self.y_height = 0.0
                    self.is_jumping = False

    def update(self):
        # Smooth lane transition
        self.lane += (self.target_lane - self.lane) * 0.25
        
        # Jump physics
        if self.is_jumping:
            self.y_height += self.jump_v
            self.jump_v -= 0.005  # Gravity
            if self.y_height <= 0:
                self.y_height = 0
                self.is_jumping = False
                
        # Slide timer
        if self.is_sliding:
            self.slide_timer -= 1
            if self.slide_timer <= 0:
                self.is_sliding = False
                
        self.anim_frame += 1

    def draw(self, surface):
        x, y, scale = project_3d(self.lane, 0.05, self.y_height)
        
        # Player size scaling
        pw = int(60 * scale)
        ph = int((30 if self.is_sliding else 90) * scale)
        
        rect = pygame.Rect(0, 0, pw, ph)
        rect.midbottom = (int(x), int(y))
        
        # Draw shadow
        shadow_x, shadow_y, _ = project_3d(self.lane, 0.05, 0)
        shadow_rect = pygame.Rect(0, 0, int(pw * 1.1), int(12 * scale))
        shadow_rect.center = (int(shadow_x), int(shadow_y))
        pygame.draw.ellipse(surface, (10, 10, 15), shadow_rect)
        
        # Draw Player Body (Simple stylized avatar)
        body_color = COLOR_GREEN if not self.is_sliding else (40, 160, 60)
        pygame.draw.rect(surface, body_color, rect, border_radius=int(6 * scale))
        
        # Head (if standing)
        if not self.is_sliding:
            head_radius = int(14 * scale)
            head_center = (int(x), int(rect.top - head_radius + 4 * scale))
            pygame.draw.circle(surface, (230, 190, 150), head_center, head_radius)
            
            # Animated running legs
            leg_offset = math.sin(self.anim_frame * 0.3) * 10 * scale
            pygame.draw.line(surface, (20, 20, 20), (x - 8 * scale, rect.bottom), (x - 8 * scale + leg_offset, rect.bottom + 10 * scale), int(4 * scale))
            pygame.draw.line(surface, (20, 20, 20), (x + 8 * scale, rect.bottom), (x + 8 * scale - leg_offset, rect.bottom + 10 * scale), int(4 * scale))

class WorldObject:
    def __init__(self, lane, obj_type):
        self.lane = lane
        self.z = 1.0  # Spawns far away at the horizon
        self.type = obj_type  # 'coin', 'high_obstacle', 'low_obstacle'

    def update(self, speed):
        self.z -= speed

    def draw(self, surface):
        x, y, scale = project_3d(self.lane, self.z, 0)
        
        if self.type == 'coin':
            radius = int(15 * scale)
            if radius > 1:
                pygame.draw.circle(surface, COLOR_GOLD, (int(x), int(y - radius)), radius)
                pygame.draw.circle(surface, (200, 160, 0), (int(x), int(y - radius)), max(1, int(radius * 0.7)), 2)
                
        elif self.type == 'low_obstacle':
            # Hurdle / Barrier to jump over
            w = int(100 * scale)
            h = int(40 * scale)
            rect = pygame.Rect(0, 0, w, h)
            rect.midbottom = (int(x), int(y))
            pygame.draw.rect(surface, COLOR_RED, rect, border_radius=4)
            pygame.draw.rect(surface, (150, 30, 30), rect, int(3 * scale), border_radius=4)
            
        elif self.type == 'high_obstacle':
            # Overhead arch/tree trunk to slide under
            w = int(120 * scale)
            h = int(80 * scale)
            rect = pygame.Rect(0, 0, w, h)
            rect.midbottom = (int(x), int(y - 35 * scale))  # Elevated position
            pygame.draw.rect(surface, COLOR_TEMPLE, rect, border_radius=4)
            # Pillars
            pygame.draw.line(surface, COLOR_TEMPLE, (x - w//2 + 5, y), (x - w//2 + 5, y - 35 * scale), int(6 * scale))
            pygame.draw.line(surface, COLOR_TEMPLE, (x + w//2 - 5, y), (x + w//2 - 5, y - 35 * scale), int(6 * scale))

# ==========================================
# MAIN GAME CLASS
# ==========================================
class TempleRunner:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Temple Runner 3D")
        self.clock = pygame.time.Clock()
        
        # Audio Initialization
        self.snd_coin = create_synthesized_sound(880, 0.1, "sine")
        self.snd_hit = create_synthesized_sound(120, 0.3, "saw")
        
        self.high_score = load_high_score()
        self.reset_game()
        
        self.state = "MENU"  # MENU, PLAYING, PAUSED, GAME_OVER
        self.font_large = pygame.font.SysFont("Arial", 48, bold=True)
        self.font_medium = pygame.font.SysFont("Arial", 28, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 20)

    def reset_game(self):
        self.player = Player()
        self.objects = []
        self.score = 0
        self.coins_collected = 0
        self.lives = 3
        self.game_speed = 0.012
        self.spawn_timer = 0
        self.distance = 0.0

    def spawn_objects(self):
        self.spawn_timer += 1
        if self.spawn_timer > max(20, int(50 - self.game_speed * 1000)):
            self.spawn_timer = 0
            lane = random.choice(LANES)
            
            # Decide what to spawn
            choice = random.random()
            if choice < 0.5:
                self.objects.append(WorldObject(lane, 'coin'))
            elif choice < 0.8:
                self.objects.append(WorldObject(lane, 'low_obstacle'))
            else:
                self.objects.append(WorldObject(lane, 'high_obstacle'))

    def check_collisions(self):
        for obj in self.objects[:]:
            # Collision zone check (when object is near player's z position)
            if 0.02 <= obj.z <= 0.09:
                # Check lane proximity
                if abs(self.player.lane - obj.lane) < 0.5:
                    
                    if obj.type == 'coin':
                        self.coins_collected += 1
                        self.score += 50
                        if self.snd_coin:
                            self.snd_coin.play()
                        self.objects.remove(obj)
                        
                    elif obj.type == 'low_obstacle':
                        # Hit if not jumping high enough
                        if self.player.y_height < 0.2:
                            self.handle_hit(obj)
                            
                    elif obj.type == 'high_obstacle':
                        # Hit if not sliding
                        if not self.player.is_sliding:
                            self.handle_hit(obj)

    def handle_hit(self, obj):
        if obj in self.objects:
            self.objects.remove(obj)
        if self.snd_hit:
            self.snd_hit.play()
        self.lives -= 1
        if self.lives <= 0:
            self.state = "GAME_OVER"
            if self.score > self.high_score:
                self.high_score = self.score
                save_high_score(self.high_score)

    def update(self):
        if self.state != "PLAYING":
            return
            
        self.player.update()
        
        # Increase speed progressively
        self.game_speed += 0.000005
        self.distance += self.game_speed
        self.score += 1
        
        # Update objects
        for obj in self.objects[:]:
            obj.update(self.game_speed)
            if obj.z <= 0.0:
                self.objects.remove(obj)
                
        self.spawn_objects()
        self.check_collisions()

    def draw_environment(self):
        self.screen.fill(COLOR_BG)
        
        # Sky background
        pygame.draw.rect(self.screen, COLOR_SKY, (0, 0, WIDTH, VANISHING_Y))
        
        # Distant Temple silhouette
        temple_pts = [
            (VANISHING_X - 120, VANISHING_Y),
            (VANISHING_X - 80, VANISHING_Y - 40),
            (VANISHING_X - 40, VANISHING_Y - 40),
            (VANISHING_X - 30, VANISHING_Y - 70),
            (VANISHING_X + 30, VANISHING_Y - 70),
            (VANISHING_X + 40, VANISHING_Y - 40),
            (VANISHING_X + 80, VANISHING_Y - 40),
            (VANISHING_X + 120, VANISHING_Y),
        ]
        pygame.draw.polygon(self.screen, COLOR_TEMPLE, temple_pts)
        
        # Perspective Runway (Path)
        path_polygon = [
            (VANISHING_X - PATH_TOP_WIDTH // 2, VANISHING_Y),
            (VANISHING_X + PATH_TOP_WIDTH // 2, VANISHING_Y),
            (VANISHING_X + PATH_BOTTOM_WIDTH // 2, HEIGHT),
            (VANISHING_X - PATH_BOTTOM_WIDTH // 2, HEIGHT)
        ]
        pygame.draw.polygon(self.screen, COLOR_PATH, path_polygon)
        
        # Animated pathway grid lines (creates movement perception)
        offset = (self.distance * 10) % 1.0
        for i in range(12):
            z_line = (i / 12.0) - (offset / 12.0)
            if z_line <= 0:
                continue
            _, y_line, scale = project_3d(0, z_line)
            w_line = (PATH_TOP_WIDTH + (PATH_BOTTOM_WIDTH - PATH_TOP_WIDTH) * (1.0 - z_line))
            pygame.draw.line(self.screen, COLOR_PATH_LINE, 
                             (VANISHING_X - w_line // 2, y_line), 
                             (VANISHING_X + w_line // 2, y_line), 
                             max(1, int(2 * scale)))

    def draw_ui(self):
        # HUD Panel
        score_text = self.font_medium.render(f"Score: {self.score}", True, COLOR_WHITE)
        coins_text = self.font_medium.render(f"Coins: {self.coins_collected}", True, COLOR_GOLD)
        lives_text = self.font_medium.render(f"Lives: {'♥ ' * self.lives}", True, COLOR_RED)
        high_text = self.font_small.render(f"High Score: {self.high_score}", True, COLOR_WHITE)
        
        self.screen.blit(score_text, (20, 20))
        self.screen.blit(coins_text, (20, 55))
        self.screen.blit(lives_text, (20, 90))
        self.screen.blit(high_text, (WIDTH - high_text.get_width() - 20, 20))

    def draw_overlay(self, title, subtitle):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        t_surf = self.font_large.render(title, True, COLOR_WHITE)
        s_surf = self.font_medium.render(subtitle, True, COLOR_GOLD)
        
        self.screen.blit(t_surf, (WIDTH//2 - t_surf.get_width()//2, HEIGHT//2 - 60))
        self.screen.blit(s_surf, (WIDTH//2 - s_surf.get_width()//2, HEIGHT//2 + 10))

    def draw(self):
        self.draw_environment()
        
        # Sort objects by Z so furthest draw first
        for obj in sorted(self.objects, key=lambda o: o.z, reverse=True):
            obj.draw(self.screen)
            
        self.player.draw(self.screen)
        self.draw_ui()
        
        if self.state == "MENU":
            self.draw_overlay("TEMPLE RUNNER 3D", "Press SPACE to Run | ESC to Quit")
        elif self.state == "PAUSED":
            self.draw_overlay("PAUSED", "Press P to Resume")
        elif self.state == "GAME_OVER":
            self.draw_overlay("GAME OVER", f"Final Score: {self.score} | Press SPACE to Restart")
            
        pygame.display.flip()

    def run(self):
        running = True
        while running:
            self.clock.tick(FPS)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    
                if event.type == pygame.KEYDOWN:
                    if self.state == "MENU" and event.key == pygame.K_SPACE:
                        self.reset_game()
                        self.state = "PLAYING"
                    elif self.state == "PLAYING":
                        if event.key == pygame.K_p:
                            self.state = "PAUSED"
                        else:
                            self.player.handle_input(event)
                    elif self.state == "PAUSED" and event.key == pygame.K_p:
                        self.state = "PLAYING"
                    elif self.state == "GAME_OVER" and event.key == pygame.K_SPACE:
                        self.reset_game()
                        self.state = "PLAYING"
                    elif event.key == pygame.K_ESCAPE:
                        running = False
                        
            self.update()
            self.draw()
            
        pygame.quit()

if __name__ == "__main__":
    game = TempleRunner()
    game.run()
