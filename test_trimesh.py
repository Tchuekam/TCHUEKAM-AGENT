import trimesh
import numpy as np
import os

print("Generating 3D model...")
# Procedurally generate a gear
base = trimesh.creation.cylinder(radius=10, height=5)
teeth = []
for a in np.linspace(0, 2*np.pi, 12, endpoint=False):
    t = trimesh.creation.box(extents=[2, 4, 5])
    t.apply_translation([10*np.cos(a), 10*np.sin(a), 0])
    teeth.append(t)

for tooth in teeth:
    base = base.union(tooth)

output_file = 'gear_test.stl'
base.export(output_file)
print(f"Exported successfully to {output_file}")
