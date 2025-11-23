import pygame, sys, math, time
from datetime import datetime
import psutil

pygame.init()
size = 480
screen = pygame.display.set_mode((size,size))
pygame.display.set_caption("Touchscreen Mini Watch OS")
clock = pygame.time.Clock()

# Colors
BG = (10,10,30)
FACE = (20,20,50)
HOUR = (255,210,127)
MINUTE = (255,255,255)
SECOND = (255,100,100)
TEXT = (200,230,255)
ICON_BG = (30,50,80)
ICON_HIGHLIGHT = (60,100,150)
BTN_BG = (50,50,80)
BTN_HIGHLIGHT = (100,100,150)
TOGGLE_ON = (50,200,50)
TOGGLE_OFF = (200,50,50)

font_large = pygame.font.SysFont("arial", 36)
font_small = pygame.font.SysFont("arial", 20)

# Apps
apps = ["Timer","Stopwatch","Heart","Settings"]
current_app = None
watch_state = "lock"  # lock, home, app
next_state = None
fade_alpha = 0

# Timer / Stopwatch states
timer_running = False
timer_start = 0
stopwatch_running = False
stopwatch_start = 0

# Settings
clock_24h = False
wifi_on = True

# Tweening helper
def tween(start,end,progress):
    return start + (end-start)*progress

# Helper to check if mouse is over a circle
def is_over_circle(mouse,pos,radius):
    mx,my = mouse
    cx,cy = pos
    return (mx-cx)**2 + (my-cy)**2 <= radius**2

# Helper to check if mouse is over rectangle
def is_over_rect(mouse, rect):
    return rect.collidepoint(mouse)

def draw_status_bar(top_y=10, right_padding=10):
    """
    Draws BOTH time and battery side by side.
    Safest universal function for lock, home, and apps.
    """

    # ----- TIME -----
    now = datetime.now().strftime("%H:%M")
    ttext = font_small.render(now, True, TEXT)

    # ----- BATTERY -----
    battery = psutil.sensors_battery()
    if battery:
        percent = battery.percent

        bw, bh = 50, 20
        bx = size - right_padding - bw
        by = top_y

        # background
        pygame.draw.rect(screen, (80,80,80), (bx,by,bw,bh))
        # fill
        pygame.draw.rect(screen, (50,200,50), (bx,by,int(bw*(percent/100)),bh))
        # border
        pygame.draw.rect(screen, TEXT, (bx,by,bw,bh), 2)

        # percent text
        btext = font_small.render(f"{int(percent)}%", True, TEXT)
        screen.blit(btext, (bx + bw//2 - btext.get_width()//2,
                            by + bh//2 - btext.get_height()//2))

        # TIME goes LEFT of battery
        tx = bx - 10 - ttext.get_width()
        ty = by + (bh//2 - ttext.get_height()//2)

    else:
        # no battery → put time on right
        tx = size - right_padding - ttext.get_width()
        ty = top_y

    # draw time
    screen.blit(ttext, (tx, ty))


# Draw Lock Screen
def draw_lock_screen(progress=1.0):
    screen.fill(BG)
    cx,cy = size//2,size//2
    r = size*0.45
    s = pygame.Surface((size,size),pygame.SRCALPHA)
    pygame.draw.circle(s,(20,20,50,int(255*progress)),(cx,cy),int(r))
    screen.blit(s,(0,0))
    now = datetime.now()
    sec = now.second + now.microsecond/1_000_000
    minute = now.minute + sec/60
    hour = (now.hour%12)+minute/60
    def hand(angle,length,color,width):
        rad = math.radians(angle-90)
        x = cx + math.cos(rad)*length
        y = cy + math.sin(rad)*length
        pygame.draw.line(screen,color,(cx,cy),(x,y),width)
    hand(hour/12*360,r*0.5,HOUR,6)
    hand(minute/60*360,r*0.7,MINUTE,4)
    hand(sec/60*360,r*0.8,SECOND,2)
    # Digital time
    time_str = now.strftime("%H:%M" if clock_24h else "%I:%M %p")
    text = font_large.render(time_str.lstrip("0"), True, TEXT)
    screen.blit(text,(cx-text.get_width()//2, cy+r*0.4))
    hint = font_small.render("Tap to Unlock", True, TEXT)
    screen.blit(hint,(cx-hint.get_width()//2, cy+r*0.8))
    draw_status_bar()

# Draw Home Screen
def draw_home_screen(progress=1.0):
    screen.fill(BG)
    cx,cy = size//2,size//2
    r = size*0.4
    for i,app in enumerate(apps):
        angle = i*360/len(apps)
        rad = math.radians(angle-90)
        x = cx + math.cos(rad)*r
        y = cy + math.sin(rad)*r
        scale = tween(0.5,1,progress)
        pygame.draw.circle(screen,ICON_BG,(int(x),int(y)),int(40*scale))
        text = font_small.render(app, True, TEXT)
        screen.blit(text,(int(x-text.get_width()/2),int(y-text.get_height()/2)))
    draw_status_bar()

def draw_app_screen(name, progress=1.0):
    screen.fill(BG)
    cx, cy = size // 2, size // 2
    r = size * 0.45
    title = font_large.render(name, True, TEXT)
    screen.blit(title, (cx - title.get_width() // 2, cy - r * 0.4))
    buttons = []

    # Home button at bottom
    home_rect = pygame.Rect(cx - 50, size - 60, 100, 40)
    pygame.draw.rect(screen, BTN_BG, home_rect)
    home_text = font_small.render("Home", True, TEXT)
    screen.blit(home_text, (home_rect.x + (home_rect.width - home_text.get_width()) // 2,
                            home_rect.y + (home_rect.height - home_text.get_height()) // 2))
    buttons.append(("home", home_rect))

    # App-specific content
    if name == "Heart":
        bpm = 70 + int(math.sin(time.time() * 3) * 10)
        bpm_text = font_large.render(f"{bpm} BPM", True, (255, 100, 100))
        screen.blit(bpm_text, (cx - bpm_text.get_width() // 2, cy))
    elif name == "Timer":
        global timer_running, timer_start
        t = int(time.time() - timer_start) if timer_running else 0
        t_text = font_large.render(f"{t:02d}s", True, (200, 200, 50))
        screen.blit(t_text, (cx - t_text.get_width() // 2, cy))
        btn = pygame.Rect(cx - 50, cy + 60, 100, 40)
        pygame.draw.rect(screen, BTN_HIGHLIGHT if timer_running else BTN_BG, btn)
        btext = font_small.render("Stop" if timer_running else "Start", True, TEXT)
        screen.blit(btext, (cx - btext.get_width() // 2, cy + 70))
        buttons.append(("timer", btn))
    elif name == "Stopwatch":
        global stopwatch_running, stopwatch_start
        t = int(time.time() - stopwatch_start) if stopwatch_running else 0
        m, s = divmod(t, 60)
        sw_text = font_large.render(f"{m:02d}:{s:02d}", True, (100, 255, 200))
        screen.blit(sw_text, (cx - sw_text.get_width() // 2, cy))
        btn = pygame.Rect(cx - 50, cy + 60, 100, 40)
        pygame.draw.rect(screen, BTN_HIGHLIGHT if stopwatch_running else BTN_BG, btn)
        btext = font_small.render("Stop" if stopwatch_running else "Start", True, TEXT)
        screen.blit(btext, (cx - btext.get_width() // 2, cy + 70))
        buttons.append(("stopwatch", btn))
    elif name == "Settings":
        # WiFi toggle
        wifi_rect = pygame.Rect(cx - 60, cy - 20, 140, 40)
        pygame.draw.rect(screen, TOGGLE_ON if wifi_on else TOGGLE_OFF, wifi_rect)
        wtext = font_small.render("WiFi", True, TEXT)
        screen.blit(wtext, (wifi_rect.x + 10, wifi_rect.y + 10))
        buttons.append(("wifi", wifi_rect))

        # Clock format toggle
        clk_rect = pygame.Rect(cx - 60, cy + 30, 140, 40)
        pygame.draw.rect(screen, TOGGLE_ON if clock_24h else TOGGLE_OFF, clk_rect)
        ctext = font_small.render("24h Clock", True, TEXT)
        screen.blit(ctext, (clk_rect.x + 10, clk_rect.y + 10))
        buttons.append(("clock", clk_rect))

        # OS Version (LABEL ONLY)
        version_text = font_small.render("LuminOS 1", True, TEXT)
        screen.blit(version_text, (cx - version_text.get_width() // 2, cy + 90))

    # Draw status bar with battery & time
    draw_status_bar()
    return buttons


# Main loop
running = True
app_buttons = []
while running:
    mouse_pressed = pygame.mouse.get_pressed()[0]
    mouse_pos = pygame.mouse.get_pos()
    for event in pygame.event.get():
        if event.type==pygame.QUIT:
            running=False
        elif event.type==pygame.MOUSEBUTTONDOWN:
            if watch_state=="lock":
                watch_state="home"
            elif watch_state=="home":
                cx,cy = size//2,size//2
                r = size*0.4
                for i,app in enumerate(apps):
                    angle = i*360/len(apps)
                    rad = math.radians(angle-90)
                    x = cx + math.cos(rad)*r
                    y = cy + math.sin(rad)*r
                    if is_over_circle(mouse_pos,(x,y),40):
                        current_app = app
                        watch_state="app"
                        break
            elif watch_state=="app":
                for name, rect in app_buttons:
                    if is_over_rect(mouse_pos, rect):
                        if name=="home":
                            watch_state="home"
                            current_app=None
                        elif name=="timer":
                            if timer_running:
                                timer_running=False
                            else:
                                timer_start = time.time()
                                timer_running=True
                        elif name=="stopwatch":
                            if stopwatch_running:
                                stopwatch_running=False
                            else:
                                stopwatch_start = time.time()
                                stopwatch_running=True
                        elif name=="wifi":
                            wifi_on = not wifi_on
                        elif name=="clock":
                            clock_24h = not clock_24h

    # Tween fade effect
    fade_alpha = min(fade_alpha + 0.05, 1.0)

    if watch_state=="lock":
        draw_lock_screen(fade_alpha)
        app_buttons=[]
    elif watch_state=="home":
        draw_home_screen(fade_alpha)
        app_buttons=[]
    elif watch_state=="app":
        app_buttons = draw_app_screen(current_app, fade_alpha)

    pygame.display.flip()
    clock.tick(30)

pygame.quit()
sys.exit()
