from vedo import Plotter, Mesh

# Load the STL file
stl_path = "TestPlate.stl"
mesh = Mesh(stl_path).c("lightblue")

# Create a Plotter window
plotter = Plotter(title="STL Viewer - Click to Select", axes=1)

# Add mesh to plotter
plotter.show(mesh, __doc__, viewup="z")

# Define what happens when the user clicks
def on_click(event):
    if event.actor:
        picked_point = event.picked3d
        print(f"Picked point: {picked_point}")
        # Optional: highlight the picked point
        plotter.add_point(picked_point, r=5, c='red')

# Add the click callback
plotter.add_callback("mouse click", on_click)

# Start the interactive window
plotter.interactive().close()
