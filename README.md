# Circle Collision Simulation

A fully configurable physics-based simulation built with Python, Pygame, and Pymunk. In this simulation, multiple concentric arcs vanish as dynamic balls (with improved physics) escape through gaps. The simulation supports extensive command-line configuration—including the number of arcs, ball properties, particle effects, colors, screen aspect ratio, and more. The simulation runs in full-screen mode (using the available display resolution) and displays on-screen statistics (ball hits, arcs remaining, and a countdown timer). When the simulation ends, a final message ("The End") is shown.

## Features

- **Configurable Physics Simulation:**

  - Dynamic balls with collision-based physics and adjustable damping for smoother motion.
  - Concentric arcs that rotate and vanish when a ball escapes through a gap.
  - If a ball escapes to an outer arc, all inner arcs up to that escape index vanish.

- **Customizable Effects:**

  - Particle effects are spawned when an arc vanishes.
  - Collision sounds are played randomly (using MP3 files).
  - The simulation displays the number of ball hits, arcs remaining, and a countdown timer.

- **Command-Line Configuration:**
  - Control the number of arcs, ball radius, number of initial balls, and inner‑arc multiplier.
  - Adjust particle size and count, as well as ball color, background color, arc color, and particle color.
  - Set the simulation duration (countdown), ball speed, and ball damping.
  - Specify the arc smoothness (number of segments) to control visual quality.
  - Specify the screen aspect ratio (e.g. `"16:9"` or `"1:1"`). The simulation window is resized accordingly.
- **Full-Screen Operation:**
  - The simulation automatically runs in full-screen mode using the available display resolution.
  - On termination, the window is restored to windowed mode so your desktop is not left stretched.

## Requirements

- **Python 3.6+**
- **Pygame**
- **Pymunk**
- **CFFI** (usually installed as a dependency for Pymunk)

You also need to have the following sound files in your working directory:

- `do.mp3`
- `re.mp3`
- `mi.mp3`
- `fa.mp3`
- `si.mp3`
- `vanish.mp3`

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/yourusername/circle-collision-simulation.git
   cd circle-collision-simulation
   ```

2. **Set up a virtual environment (optional but recommended):**

   ```bash
   python -m venv venv
   source venv/bin/activate    # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**

   ```bash
   pip install pygame pymunk
   ```

   (Pymunk will automatically install its dependencies, including CFFI.)

4. **Place your sound files** (`do.mp3`, `re.mp3`, `mi.mp3`, `fa.mp3`, `si.mp3`, `vanish.mp3`) in the project’s root directory.

## Usage

You can run the simulation from the command line. The simulation accepts various command-line arguments to configure its behavior.

### Example

```bash
python main.py --arcs 100 --ball_size 6 --initial_balls 2 --base_multiplier 50 \
  --particle_size 2 --particle_count 20 --ball_color 255,255,0 --countdown 60 \
  --ball_speed 150 --bg_color 20,20,30 --arc_color 255,255,255 \
  --particle_color 255,255,255 --aspect_ratio 16:9 --ball_damping 0.99 --arc_smoothness 20
```

If you do not provide any arguments, the following default values are used:

- **--arcs**: 100
- **--ball_size**: 6
- **--initial_balls**: 2
- **--base_multiplier**: 50 (inner arc’s radius = ball_size × 50)
- **--particle_size**: 2
- **--particle_count**: 20
- **--ball_color**: "255,255,0" (yellow)
- **--countdown**: 60 (seconds)
- **--ball_speed**: 150
- **--bg_color**: "20,20,30"
- **--arc_color**: "255,255,255"
- **--particle_color**: "255,255,255"
- **--aspect_ratio**: "16:9"
- **--ball_damping**: 0.99
- **--arc_smoothness**: 20

### Command-Line Arguments

- `--arcs` or `-a`: Number of concentric arcs.
- `--ball_size` or `-b`: Ball radius (in pixels).
- `--initial_balls` or `-n`: Number of initial balls.
- `--base_multiplier` or `-m`: Multiplier for the inner arc's radius relative to the ball size.
- `--particle_size` or `-ps`: Particle size (in pixels).
- `--particle_count` or `-pc`: Number of particles spawned when an arc vanishes.
- `--ball_color` or `-bc`: Ball color, provided as a comma-separated string (e.g., "255,255,0").
- `--countdown` or `-cd`: Duration of the simulation (in seconds).
- `--ball_speed` or `-s`: Initial speed of the balls.
- `--bg_color` or `-bg`: Background color (comma-separated R,G,B).
- `--arc_color` or `-ac`: Arc color (comma-separated R,G,B).
- `--particle_color` or `-pcolor`: Particle color (comma-separated R,G,B).
- `--aspect_ratio` or `-ar`: Desired aspect ratio of the simulation window (e.g., "16:9" or "1:1").
- `--ball_damping` or `-bd`: Damping factor applied to ball physics (default 0.99).
- `--arc_smoothness` or `-as`: Number of segments used to draw each arc (higher value means smoother arcs).

## How It Works

- **Physics & Collisions:**  
  The simulation uses Pymunk (a Chipmunk physics wrapper) to simulate ball movement and collisions. Collisions between balls and arcs (or between balls) trigger sound effects and update counters.

- **Concentric Arcs:**  
  Arcs are drawn as a series of line segments. The inner-most arc's radius is determined by `ball_size * base_multiplier`. The distance between successive arcs equals the ball’s radius by default, and the smoothness of each arc is controlled by the number of segments.

- **Escape Logic:**  
  If a ball’s outer edge (its center plus its radius) reaches an arc farther out than the current active arc, then all arcs up to that escape index vanish immediately (with particle effects and a vanish sound).

- **Rendering & Full-Screen:**  
  The simulation runs in full-screen mode using the available display resolution, adjusted to the specified aspect ratio. Overlay text displays the number of ball hits, arcs remaining, the countdown timer, and the ball color.

- **End-of-Game:**  
  When the simulation ends (either because all arcs have vanished or the countdown timer reaches zero), the program restores the display to windowed mode and shows the message “The End” for 3 seconds.

## Troubleshooting

- **Sound Issues:**  
  If sounds do not play, ensure that the MP3 files are in the correct directory, that `pygame.mixer.init()` is called successfully, and that Windows volume mixer settings are configured correctly.

- **Performance:**  
  If performance is an issue, consider adjusting the simulation parameters (number of arcs, initial ball speed, damping, etc.) or look into GPU acceleration using frameworks such as Taichi (note that this would require significant rewrites).

## Contributing

Contributions are welcome! If you have suggestions or improvements, feel free to fork the repository and submit pull requests. Please include tests and documentation as needed.

## License
