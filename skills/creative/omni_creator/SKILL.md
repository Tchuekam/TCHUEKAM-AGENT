---
name: omni_creator
description: Generates 3D models (STL/OBJ), physics simulations (MP4/GIF), and arbitrary visual models by writing and executing Python scripts using trimesh, matplotlib, and scipy.
platforms: [macos, linux, windows]
parameters:
  type: object
  properties:
    prompt:
      type: string
      description: The natural language request of what 3D design, simulation, or model to generate.
    output_type:
      type: string
      description: The desired output type (e.g., 'stl', 'mp4', 'gif', 'png').
  required: [prompt, output_type]
---

# Omni-Creator Skill

This skill empowers you to create complex 3D geometry, physics simulations, and generative mathematical models natively without external CAD or rendering GUI software.

## Instructions

When the user asks you to create a 3D design, model, or simulation, you must follow these exact steps:

1. **Understand the Request**: Read the user's `prompt` carefully. Determine if this requires:
   - **3D Geometry (STL/OBJ)**: Use the `trimesh` library.
   - **Physics Simulation / Math Model (MP4/GIF/PNG)**: Use `numpy` for the physics/math and `matplotlib.animation` for rendering.

2. **Write the Python Script**: Use your `write_to_file` or `run_command` tool to create a Python script (e.g., `generate_asset.py` in the current workspace or `/tmp`).
   - The script must be completely self-contained.
   - It must save the final artifact to the current directory with the requested `output_type`.
   - *For `trimesh`:* Build geometry using primitives (boxes, cylinders) or CSG (boolean operations). Export using `mesh.export('output.stl')`.
   - *For animations:* Use `matplotlib.animation.FuncAnimation`, then save via `anim.save('output.mp4', writer='ffmpeg', fps=30)` or `'output.gif'` if ffmpeg is missing.

3. **Execute the Script**: Use your `run_command` tool to run the python script (e.g., `python generate_asset.py`).
   - If the script fails, read the stack trace, fix the script, and run it again.

4. **Deliver the Result**: Once the script completes successfully and the artifact (e.g., `output.stl` or `output.gif`) exists, embed the result in a markdown artifact if it's an image/video, or provide the exact file path to the user.

## Examples

**Example 1: Generating a 3D Gear (trimesh)**
```python
import trimesh
import numpy as np

# Procedurally generate a gear or complex shape...
base = trimesh.creation.cylinder(radius=10, height=5)
teeth = [trimesh.creation.box(extents=[2, 4, 5], transform=trimesh.transformations.translation_matrix([10*np.cos(a), 10*np.sin(a), 0])) for a in np.linspace(0, 2*np.pi, 12, endpoint=False)]
for tooth in teeth:
    base = base.union(tooth)
base.export('gear.stl')
```

**Example 2: Physics Simulation (matplotlib)**
```python
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

fig, ax = plt.subplots()
ax.set_xlim(0, 10)
ax.set_ylim(0, 10)
circle = plt.Circle((5, 10), 0.5, fc='b')
ax.add_patch(circle)

# Basic gravity simulation
v, y = 0, 10
def update(frame):
    global v, y
    v -= 9.8 * 0.03
    y += v * 0.03
    if y <= 0.5:
        y, v = 0.5, -v * 0.8 # Bounce
    circle.set_center((5, y))
    return circle,

anim = animation.FuncAnimation(fig, update, frames=100, blit=True)
anim.save('simulation.gif', fps=30)
```

By strictly writing and running code, you are capable of generating *anything* the user requests.
