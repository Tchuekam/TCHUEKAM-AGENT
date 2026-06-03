import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

print("Generating physics simulation (matplotlib)...")
fig, ax = plt.subplots()
ax.set_xlim(0, 10)
ax.set_ylim(0, 10)
circle = plt.Circle((5, 10), 0.5, fc='b')
ax.add_patch(circle)

v, y = 0, 10
def update(frame):
    global v, y
    v -= 9.8 * 0.03
    y += v * 0.03
    if y <= 0.5:
        y, v = 0.5, -v * 0.8
    circle.set_center((5, y))
    return circle,

anim = animation.FuncAnimation(fig, update, frames=100, blit=True)
output_file = 'simulation_test.gif'
anim.save(output_file, fps=30)
print(f"Exported successfully to {output_file}")
