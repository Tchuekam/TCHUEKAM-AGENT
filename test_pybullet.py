import pybullet as p
import pybullet_data
import imageio
import numpy as np

print("Generating simulation...")
p.connect(p.DIRECT)
p.setAdditionalSearchPath(pybullet_data.getDataPath())
p.loadURDF("plane.urdf")
p.setGravity(0, 0, -10)
boxId = p.loadURDF("cube.urdf", [0, 0, 5])

frames = []
for i in range(100):
    p.stepSimulation()
    width, height, rgbImg, depthImg, segImg = p.getCameraImage(
        320, 240, 
        viewMatrix=p.computeViewMatrixFromYawPitchRoll([0,0,0], 5, 0, -20, 0, 2), 
        projectionMatrix=p.computeProjectionMatrixFOV(60, 320/240, 0.1, 100)
    )
    # Extract RGB
    rgb = np.reshape(rgbImg, (240, 320, 4))[:, :, :3]
    frames.append(rgb)

output_file = 'simulation_test.gif'
imageio.mimsave(output_file, frames, fps=30)
p.disconnect()
print(f"Exported successfully to {output_file}")
