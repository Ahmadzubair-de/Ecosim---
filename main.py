import pygame
import random
import math

print('Hello, World!') # Very important DONT DELETE!!!

# --- Settings ---
WIDTH, HEIGHT = 1600, 1200
FPS = 120
LIFE_SIZE = 40

# Colors
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
ORANGE = (255, 165, 0)
GRAY = (128, 128, 128)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
PURPLE = (160, 32, 240)
PINK = (255, 105, 180)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)
BROWN = (165, 42, 42)
LIME = (50, 205, 50)
TEAL = (0, 128, 128)
MAROON = (128, 0, 0)
NAVY = (0, 0, 128)
OLIVE = (128, 128, 0)
CORAL = (255, 127, 80)

# --- Classes ---
class Source:
    def __init__(self, x, y, size, color, type_name, uses=-1, respawn_time=0):
        self.x = x
        self.y = y
        self.size = size
        self.color = color
        self.type_name = type_name
        self.uses = uses
        self.original_uses = uses
        self.respawn_time = respawn_time
        self.respawn_timer = 0
        self.active = True

    def use(self):
        if not self.active:
            return False
            
        if self.uses > 0:
            self.uses -= 1
            if self.uses <= 0:
                self.active = False
                self.respawn_timer = self.respawn_time
            return True
        elif self.uses == -1:
            return True
        return False

    def update(self, dt):
        if not self.active and self.respawn_time > 0:
            self.respawn_timer -= dt
            if self.respawn_timer <= 0:
                self.active = True
                self.uses = self.original_uses

    def draw(self, screen):
        if not self.active:
            return
            
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.size, self.size))
        if self.uses != -1:
            font = pygame.font.SysFont(None, 20)
            uses_text = font.render(str(self.uses), True, WHITE)
            screen.blit(uses_text, (self.x + self.size//2 - 10, self.y + self.size//2 - 10))


class Creature:
    def __init__(self, x, y, color, shape, sight_radius=120, damage=10, parent1=None, parent2=None):
        self.x = x
        self.y = y
        self.size = LIFE_SIZE
        self.speed = 2.5
        self.thirst = 100
        self.hunger = 100
        self.love = random.uniform(0, 30)
        self.hp = 100  # Neue HP-Stat
        self.damage = damage  # Neue Damage-Stat
        self.target = None
        self.dead = False
        self.color = color
        self.shape = shape  # "square" oder "triangle"
        self.sight_radius = sight_radius
        self.original_sight_radius = sight_radius  # Für Altersverschlechterung
        self.recently_drunk = False
        self.recently_ate = False
        self.mating = False
        self.mating_timer = 0
        self.mating_partner = None
        self.parent1 = parent1
        self.parent2 = parent2
        self.child_created = False
        self.age = 0
        self.age_in_years = 0
        self.mating_cooldown = 0
        self.children_count = 0
        self.generation = 0 if parent1 is None else max(parent1.generation, parent2.generation) + 1
        self.combat_cooldown = 0  # Cooldown nach Kampf
        self.last_hp_regeneration = 0  # Timer für HP-Regeneration
        self.kills = 0  # Anzahl der getöteten Feinde

        self.hunger_decay = 0.008 + (self.sight_radius / 10000)
        self.thirst_decay = 0.012 + (self.sight_radius / 8000)
        self.love_increase = 0.05

    def _rect_distance_to_rect(self, rx, ry, rw, rh):
        cx = self.x + self.size / 2
        cy = self.y + self.size / 2
        nearest_x = max(rx, min(cx, rx + rw))
        nearest_y = max(ry, min(cy, ry + rh))
        dx = nearest_x - cx
        dy = nearest_y - cy
        return math.hypot(dx, dy)

    def _rect_distance_to_creature(self, other_creature):
        return self._rect_distance_to_rect(other_creature.x, other_creature.y, other_creature.size, other_creature.size)

    def can_fight(self):
        return (self.hunger > 50 and self.thirst > 50 and 
                self.hp > 0 and self.combat_cooldown <= 0)

    def can_mate(self):
        return (self.love >= 90 and self.hunger > 40 and self.thirst > 40 and 
                self.mating_cooldown <= 0 and self.hp == 100)

    def update(self, sources, all_creatures):
        if self.dead:
            return
            
        self.age += 1
        # Alter in Jahren (5 Sekunden = 1 Jahr bei FPS=120)
        if self.age % (5 * FPS) == 0:
            self.age_in_years += 1
            # Altersbedingte Sichtverschlechterung alle 10 Jahre
            if self.age_in_years % 10 == 0 and self.age_in_years > 0:
                self.sight_radius = max(20, self.sight_radius - 5)
        
        # HP-Regeneration alle 30 Sekunden - JETZT 30 HP
        if self.age - self.last_hp_regeneration > 30 * FPS and self.hp < 100:
            self.hp = min(100, self.hp + 30)  # 30 HP statt 1 HP
            self.last_hp_regeneration = self.age
        
        if self.combat_cooldown > 0:
            self.combat_cooldown -= 1
        
        if self.mating_cooldown > 0:
            self.mating_cooldown -= 1

        if not self.mating:
            self.hunger -= self.hunger_decay
            self.thirst -= self.thirst_decay
            self.love = min(100, self.love + self.love_increase)

        if self.hunger <= 0 or self.thirst <= 0 or self.hp <= 0 or self.age > 250 * FPS:
            self.hunger = max(0, self.hunger)
            self.thirst = max(0, self.thirst)
            self.hp = max(0, self.hp)
            self.dead = True
            if self.mating and self.mating_partner:
                self.mating_partner.mating = False
                self.mating_partner.mating_timer = 0
                self.mating_partner.mating_partner = None
                self.mating_partner.child_created = False
            return

        if self.mating:
            self.mating_timer -= 1
            if self.mating_timer <= 0:
                if not self.child_created and not self.mating_partner.child_created:
                    self._create_child(all_creatures)
                    self.child_created = True
                    self.mating_partner.child_created = True
                    self.mating_cooldown = 5 * FPS
                    self.mating_partner.mating_cooldown = 5 * FPS
                
                self.mating = False
                self.mating_partner = None
                self.love = 20
            return

        # Prioritäten: Kampf > Grundbedürfnisse > Fortpflanzung > Wandern
        if self.can_fight():
            enemy = self._seek_enemy(all_creatures)
            if enemy:
                self.target = enemy
            elif self.thirst <= 60 and not self.recently_drunk:
                self._seek("water", sources)
            elif self.hunger <= 60 and not self.recently_ate:
                self._seek("food", sources)
            elif self.can_mate():
                self._seek_mate(all_creatures)
            elif self.target is None:
                self._wander()
        else:
            if self.thirst <= 60 and not self.recently_drunk:
                self._seek("water", sources)
            elif self.hunger <= 60 and not self.recently_ate:
                self._seek("food", sources)
            elif self.can_mate():
                self._seek_mate(all_creatures)
            elif self.target is None:
                self._wander()

        # Bewegung
        if self.target:
            if isinstance(self.target, Source):
                target_x = max(self.target.x, min(self.x, self.target.x + self.target.size - self.size))
                target_y = max(self.target.y, min(self.y, self.target.y + self.target.size - self.size))
            elif isinstance(self.target, Creature):
                target_x = self.target.x
                target_y = self.target.y
            else:
                target_x, target_y = self.target

            dx = target_x - self.x
            dy = target_y - self.y
            dist = math.hypot(dx, dy)

            # KAMPF BEGINNT FRÜHER - bei 15 Pixel statt 1 Pixel
            if dist > 15:
                move_speed = min(self.speed, dist / 8)
                self.x += dx / dist * move_speed
                self.y += dy / dist * move_speed
                self.x = max(0, min(WIDTH - self.size, self.x))
                self.y = max(0, min(HEIGHT - self.size, self.y))
            else:
                if isinstance(self.target, Source):
                    if self.target.use():
                        if self.target.type_name == "water":
                            self.thirst = 100
                            self.recently_drunk = True
                        elif self.target.type_name == "food":
                            self.hunger = 100
                            self.recently_ate = True
                    self.target = None
                elif isinstance(self.target, Creature):
                    other = self.target
                    # Kampf nur wenn verschiedene Arten und beide kampfbereit
                    if (self.shape != other.shape and 
                        self.can_fight() and other.can_fight()):
                        # Kampf durchführen
                        self.hp -= other.damage
                        other.hp -= self.damage
                        self.combat_cooldown = 0.1 * FPS  # 1 Sekunde Cooldown
                        other.combat_cooldown = 0.1* FPS
                        
                        # Prüfen, ob der Gegner gestorben ist
                        if other.hp <= 0:
                            self.kills += 1
                            if self.shape == "square":
                                global square_kills
                                square_kills += 1
                            else:
                                global triangle_kills
                                triangle_kills += 1
                        
                        self.target = None
                        other.target = None
                    # Verfolgung wenn nur einer kampfbereit ist
                    elif (self.shape != other.shape and 
                          self.can_fight() and not other.can_fight()):
                        # Verfolge weiterhin den Feind
                        pass
                    # Paarung nur bei gleicher Art
                    elif (self.shape == other.shape and 
                          other.can_mate() and not other.mating):
                        self.mating = True
                        self.mating_partner = other
                        other.mating = True
                        other.mating_partner = self
                        self.mating_timer = 2 * FPS
                        other.mating_timer = 2 * FPS
                        other.target = None
                        self.target = None
                        self.child_created = False
                        self.mating_partner.child_created = False

        if self.recently_drunk and self.thirst < 50:
            self.recently_drunk = False
        if self.recently_ate and self.hunger < 60:
            self.recently_ate = False

    def _seek(self, type_name, sources):
        active_sources = [s for s in sources if s.active]
        in_sight = [
            s for s in active_sources
            if s.type_name == type_name and self._rect_distance_to_rect(s.x, s.y, s.size, s.size) <= self.sight_radius
        ]
        if in_sight:
            self.target = min(in_sight, key=lambda s: self._rect_distance_to_rect(s.x, s.y, s.size, s.size))
        else:
            self._wander()

    def _seek_mate(self, all_creatures):
        potential_mates = [
            creature for creature in all_creatures
            if (creature is not self and not creature.dead and not creature.mating and
                creature.shape == self.shape and  # Nur gleiche Art
                creature.can_mate() and
                self._rect_distance_to_creature(creature) <= self.sight_radius)
        ]
        if potential_mates:
            self.target = min(potential_mates, key=lambda creature: self._rect_distance_to_creature(creature))
        else:
            self._wander()

    def _seek_enemy(self, all_creatures):
        enemies = [
            creature for creature in all_creatures
            if (creature is not self and not creature.dead and
                creature.shape != self.shape and  # Nur verschiedene Arten
                self._rect_distance_to_creature(creature) <= self.sight_radius)  # VERBESSERUNG: -2 Puffer
        ]
        if enemies:
            return min(enemies, key=lambda creature: self._rect_distance_to_creature(creature))
        return None

    def _wander(self):
        angle = random.uniform(0, 2 * math.pi)
        radius = random.uniform(0, self.sight_radius / 2)
        target_x = self.x + math.cos(angle) * radius
        target_y = self.y + math.sin(angle) * radius
        target_x = max(0, min(WIDTH - self.size, target_x))
        target_y = max(0, min(HEIGHT - self.size, target_y))
        self.target = (target_x, target_y)

    def _create_child(self, all_creatures):
        child_x = (self.x + self.mating_partner.x) / 2 + random.uniform(-30, 30)
        child_y = (self.y + self.mating_partner.y) / 2 + random.uniform(-30, 30)
        child_x = max(0, min(WIDTH - LIFE_SIZE, child_x))
        child_y = max(0, min(HEIGHT - LIFE_SIZE, child_y))
        
        if random.random() < 0.7:
            r = (self.color[0] + self.mating_partner.color[0]) // 2
            g = (self.color[1] + self.mating_partner.color[1]) // 2
            b = (self.color[2] + self.mating_partner.color[2]) // 2
            child_color = (r, g, b)
        else:
            child_color = random.choice([self.color, self.mating_partner.color])
        
        base_sight = (self.sight_radius + self.mating_partner.sight_radius) / 2
        child_sight_radius = base_sight + random.uniform(-20, 20)
        child_sight_radius = max(20, min(200, child_sight_radius))
        
        base_damage = (self.damage + self.mating_partner.damage) / 2
        child_damage = base_damage + random.uniform(-2, 2)
        child_damage = max(5, min(30, child_damage))
        
        child = Creature(child_x, child_y, child_color, self.shape, child_sight_radius, child_damage, self, self.mating_partner)
        all_creatures.append(child)
        self.children_count += 1
        self.mating_partner.children_count += 1

    def draw(self, screen):
        color = GRAY if self.dead else self.color
        
        if self.shape == "square":
            pygame.draw.rect(screen, color, (self.x, self.y, self.size, self.size))
        else:  # triangle
            points = [
                (self.x + self.size // 2, self.y),
                (self.x, self.y + self.size),
                (self.x + self.size, self.y + self.size)
            ]
            pygame.draw.polygon(screen, color, points)
        
        if not self.dead:
            # Sichtfeld basierend auf Status - PARUNGSMODUS JETZT LILA
            if self.mating:
                sight_color = PURPLE  # Jetzt Lila statt Pink
            elif self.can_fight():
                sight_color = (255, 0, 0)  # Rot bei Kampfbereitschaft
            else:
                sight_color = (0, 200, 0)
                
            sight_surface = pygame.Surface((self.sight_radius * 2, self.sight_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(sight_surface, (*sight_color, 20), (self.sight_radius, self.sight_radius), self.sight_radius)
            screen.blit(sight_surface, (self.x + self.size/2 - self.sight_radius, self.y + self.size/2 - self.sight_radius))
            
            pygame.draw.circle(screen, sight_color, (int(self.x + self.size/2), int(self.y + self.size/2)), self.sight_radius, 2)
            
            # HP-Balken
            hp_width = (self.hp / 100) * self.size
            pygame.draw.rect(screen, RED, (self.x, self.y - 10, self.size, 5))
            pygame.draw.rect(screen, GREEN, (self.x, self.y - 10, hp_width, 5))
            
            if self.mating:
                heart_size = 8
                heart_x = self.x + self.size/2 - heart_size/2
                heart_y = self.y - heart_size - 15
                self._draw_heart(screen, heart_x, heart_y, heart_size, PURPLE)  # Jetzt Lila statt Pink

    def _draw_heart(self, screen, x, y, size, color):
        points = []
        for i in range(0, 360, 10):
            angle = math.radians(i)
            heart_x = 16 * (math.sin(angle) ** 3)
            heart_y = 13 * math.cos(angle) - 5 * math.cos(2*angle) - 2 * math.cos(3*angle) - math.cos(4*angle)
            points.append((x + heart_x * size/16, y - heart_y * size/16))
        
        if len(points) > 2:
            pygame.draw.polygon(screen, color, points)


# --- Pygame Setup ---
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Ökosystem-Simulation: Survival of the Fittest")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 24)
small_font = pygame.font.SysFont(None, 20)

# --- Global variables ---
total_deaths = 0
square_deaths = 0
triangle_deaths = 0
square_kills = 0
triangle_kills = 0
square_natural_deaths = 0
triangle_natural_deaths = 0
paused = False

# --- Creatures ---
creatures = [
    # Squares
    Creature(800, 400, GREEN, "square", sight_radius=180, damage=18),
    Creature(600, 400, GREEN, "square", sight_radius=160, damage=16),
    Creature(400, 100, GREEN, "square", sight_radius=190, damage=14),
    
    # Triangles
    Creature(1500, 150, RED, "triangle", sight_radius=190, damage=17),
    Creature(1200, 100, RED, "triangle", sight_radius=160, damage=15),
    Creature(1450, 350, RED, "triangle", sight_radius=180, damage=16),
]

# --- Food and water sources---
sources = []

water_positions = [
    # (x, y, size, uses, respawn_time)
    (800, 600, 60, 20, 1200000),
    (400, 600, 50, 30, 1500000),
    (1200, 600, 50, 30, 1500000),
    (800, 300, 45, 25, 1800000),
]

food_positions = [
    # (x, y, size, uses, respawn_time)
    (800, 400, 60, 20, 1200000),
    (500, 400, 50, 30, 1500000),
    (1100, 400, 50, 30, 1500000),
]

for pos in water_positions:
    x, y, size, uses, respawn_time = pos
    sources.append(Source(x, y, size, BLUE, "water", uses, respawn_time))

for pos in food_positions:
    x, y, size, uses, respawn_time = pos
    sources.append(Source(x, y, size, ORANGE, "food", uses, respawn_time))

# --- Game Loop ---
running = True
selected_creature = None

while running:
    dt = clock.tick(FPS)
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                selected_creature = None
                for creature in creatures:
                    if (creature.x <= mouse_x <= creature.x + creature.size and 
                        creature.y <= mouse_y <= creature.y + creature.size):
                        selected_creature = creature
                        break
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:
                paused = not paused

    if not paused:
        for source in sources:
            source.update(dt)

        for creature in creatures:
            creature.update(sources, creatures)

        new_creatures = []
        for creature in creatures:
            if creature.dead:
                total_deaths += 1
                if creature.hp <= 0:
                    # Kampftod
                    if creature.shape == "square":
                        square_deaths += 1
                    else:
                        triangle_deaths += 1
                else:
                    if creature.shape == "square":
                        square_natural_deaths += 1
                    else:
                        triangle_natural_deaths += 1
            else:
                new_creatures.append(creature)
        creatures = new_creatures

    screen.fill(WHITE)

    for s in sources:
        if s.active:
            s.draw(screen)

    for creature in creatures:
        creature.draw(screen)

    y_offset = 10
    
    squares = len([c for c in creatures if c.shape == "square"])
    triangles = len([c for c in creatures if c.shape == "triangle"])
    
    stats = [
        f"Population: {len(creatures)}",
        f"Squares: {squares}",
        f"Triangles: {triangles}",
        f"--- Death Statistics ---",
        f"Total Deaths: {total_deaths}",
        f"Square Deaths: {square_deaths}",
        f"  - Combat: {square_deaths - square_natural_deaths}",
        f"  - Natural: {square_natural_deaths}",
        f"Triangle Deaths: {triangle_deaths}",
        f"  - Combat: {triangle_deaths - triangle_natural_deaths}",
        f"  - Natural: {triangle_natural_deaths}",
        f"--- Kill Statistics ---",
        f"Square Kills: {square_kills}",
        f"Triangle Kills: {triangle_kills}",
        f"--- Simulation ---",
        f"FPS: {int(clock.get_fps())}",
        f"Status: {'PAUSED' if paused else 'RUNNING'}",
        f"Press P to pause"
]

    for i, stat in enumerate(stats):
        text = small_font.render(stat, True, BLACK)
        screen.blit(text, (WIDTH - 270, 15 + i * 22))

    if selected_creature is not None and not selected_creature.dead:
        shape_name = "Square" if selected_creature.shape == "square" else "Triangle"
        stats = [
            f"{shape_name} - Gen: {selected_creature.generation}",
            f"Hunger: {int(selected_creature.hunger)}%",
            f"Thirst: {int(selected_creature.thirst)}%",
            f"Love: {int(selected_creature.love)}%",
            f"HP: {int(selected_creature.hp)}%",
            f"Damage: {int(selected_creature.damage)}",
            f"Kills: {selected_creature.kills}",
            f"Children: {selected_creature.children_count}",
            f"Age: {selected_creature.age_in_years} years",
            f"Sight Radius: {int(selected_creature.sight_radius)}",
            f"Status: {'Mating' if selected_creature.mating else 'Normal'}",
        ]
        
        pygame.draw.rect(screen, selected_creature.color, (10, 10, 20, 20))
        
        for i, stat in enumerate(stats):
            text = small_font.render(stat, True, BLACK)
            screen.blit(text, (35, 15 + i * 22))

    pygame.display.flip()

pygame.quit()