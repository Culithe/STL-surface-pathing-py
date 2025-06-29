from vedo import Plotter, Mesh, Point
import STL_Parser
import numpy as np

class STLViewer:
    def __init__(self, stl_path):
        self.stl_path = stl_path
        self.mesh = Mesh(stl_path).c("lightblue")
        self.plotter = Plotter(title=stl_path, axes=1)
        
        # Parses the STL for vertices data
        vertices = np.array(STL_Parser.parse_stl(stl_path), dtype=np.float32)

        self.clicked_points = []     # Stores clicked points as [x, y, z]

        self.plotter.add_callback("mouse click", self.on_click)

    def on_click(self, event):
        if event.actor:
            picked_point = event.picked3d
            print(f"Picked point: {picked_point}")
            self.clicked_points.append(picked_point)

            # Add a red point marker to the scene
            point_marker = Point(picked_point, r=10, c='red')
            self.plotter += point_marker

            # If at least 2 points, draw a geodesic line between the last two
            if len(self.clicked_points) >= 2:
                start = self.clicked_points[-2]
                end = self.clicked_points[-1]
                
            self.plotter.render()

    def start(self):
        self.plotter.show(self.mesh, viewup="z", interactive=True)


# Run the viewer
if __name__ == "__main__":
    viewer = STLViewer("TestPlate.stl")
    viewer.start()
