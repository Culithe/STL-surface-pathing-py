from vedo import Plotter, Mesh, Point

class STLViewer:
    def __init__(self, stl_path):
        self.stl_path = stl_path
        self.mesh = Mesh(stl_path).c("lightblue")
        self.plotter = Plotter(title=stl_path, axes=1)
        self.plotter.add_callback("mouse click", self.on_click)

    def on_click(self, event):
        if event.actor:
            picked_point = event.picked3d
            print(f"Picked point: {picked_point}")
            point_marker = Point(picked_point, r=10, c='red')
            self.plotter += point_marker
            self.plotter.render()

    def start(self):
        self.plotter.show(self.mesh, viewup="z", interactive=True)

# Run the viewer
if __name__ == "__main__":
    viewer = STLViewer("TestPlate.stl")
    viewer.start()
