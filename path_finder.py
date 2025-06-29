# Path Finder Application
#
# This script loads an STL file, allows users to select two points on its surface,
# finds a path between these points by traversing adjacent faces,
# and saves the coordinates and normals of the centers of these faces.

import vedo
import trimesh
import numpy as np

# Global variables
STL_FILE = "TestPlate.stl"
trimesh_mesh = None
vedo_mesh = None
plotter = None
selected_faces = [] # To store indices of selected faces (stores face_idx, point_clicked)
MAX_SELECTIONS = 2

# --- Pathfinding and output related globals ---
face_adjacency_graph = None
found_path_faces = [] # Stores face indices of the found path
path_coords_normals = [] # Stores (center_coord, normal_vector) for faces in path

def get_closest_face_to_point(point, mesh_obj):
    """
    Finds the closest face on the trimesh_mesh to a given 3D point.
    Returns the index of the closest face.
    """
    if not hasattr(mesh_obj, 'faces') or not hasattr(mesh_obj, 'vertices'):
        print("Error: Mesh object does not have faces or vertices.")
        return None

    # Calculate face centers
    face_centers = mesh_obj.triangles_center

    # Find the closest face center to the picked point
    distances = np.linalg.norm(face_centers - point, axis=1)
    closest_face_idx = np.argmin(distances)
    return closest_face_idx

def selection_callback(event):
    """Callback function for mouse clicks to select faces."""
    global selected_faces, vedo_mesh, trimesh_mesh, plotter

    if not event.actor or event.actor != vedo_mesh:
        return # Click was not on the main mesh

    picked_point = event.picked3d
    if picked_point is None:
        return

    if len(selected_faces) >= MAX_SELECTIONS:
        print(f"Already selected {MAX_SELECTIONS} points. Please reset if you want to select new points.")
        # Optionally, clear selections or implement a reset mechanism here
        return

    closest_face_idx = get_closest_face_to_point(picked_point, trimesh_mesh)

    if closest_face_idx is not None:
        if any(sf[0] == closest_face_idx for sf in selected_faces):
            print(f"Face {closest_face_idx} already selected.")
            return

        print(f"Selected point: {picked_point}, closest face index: {closest_face_idx}")
        selected_faces.append((closest_face_idx, picked_point))

        # Visual feedback: color the selected face
        # Create a copy of colors if it's the first selection to modify
        if not hasattr(vedo_mesh, "_original_colors"):
            vedo_mesh._original_colors = vedo_mesh.celldata["colors"].copy() if vedo_mesh.celldata.contains("colors") else None

        current_colors = vedo_mesh.celldata["colors"]
        if current_colors is None or len(current_colors) != trimesh_mesh.faces.shape[0]:
            current_colors = np.repeat([vedo_mesh.color()], trimesh_mesh.faces.shape[0], axis=0)

        current_colors[closest_face_idx] = vedo.colors.getColor('red') # Mark selected face in red
        vedo_mesh.celldata["colors"] = current_colors
        vedo_mesh.mapper().SetScalarModeToUseCellData() # Crucial for updating cell colors

        # Add a sphere at the clicked point for better visualization
        clicked_sphere = vedo.Sphere(pos=picked_point, r=vedo_mesh.avg_size()*0.01, c='yellow')
        plotter.add(clicked_sphere)
        plotter.render() # Re-render to show changes

        if len(selected_faces) == MAX_SELECTIONS:
            print("Two points selected. Proceeding to pathfinding.")
            # For now, just print the selected faces
            print(f"Selected faces (index, click_coord): {selected_faces}")
            pathfind_and_display() # This function will be created in the next step

def build_face_adjacency_graph():
    """Builds the face adjacency graph from the trimesh_mesh."""
    global face_adjacency_graph, trimesh_mesh
    if trimesh_mesh is None:
        print("Error: Trimesh mesh not loaded.")
        return
    # face_adjacency is a list of lists, where each inner list contains
    # indices of faces adjacent to the face at the outer list's index.
    face_adjacency_graph = trimesh_mesh.face_adjacency
    print("Face adjacency graph built.")

def bfs_path(graph, start_node, end_node):
    """
    Performs a Breadth-First Search to find the shortest path from start_node to end_node.
    'graph' is a list of lists representing an adjacency list.
    Returns a list of node indices representing the path, or None if no path is found.
    """
    if start_node == end_node:
        return [start_node]

    queue = [(start_node, [start_node])] # Store (node, path_to_node)
    visited = {start_node}

    while queue:
        current_node, path = queue.pop(0)

        for neighbor in graph[current_node]:
            if neighbor == end_node:
                return path + [neighbor]
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))

    return None # No path found

def pathfind_and_display():
    """Finds path between selected faces and prepares for display."""
    global selected_faces, face_adjacency_graph, found_path_faces, plotter, vedo_mesh

    if len(selected_faces) != MAX_SELECTIONS:
        print("Error: Two faces must be selected for pathfinding.")
        return

    start_face_idx = selected_faces[0][0]
    end_face_idx = selected_faces[1][0]

    print(f"Starting pathfinding from face {start_face_idx} to face {end_face_idx}...")

    if face_adjacency_graph is None:
        print("Error: Face adjacency graph not built.")
        return

    found_path_faces = bfs_path(face_adjacency_graph, start_face_idx, end_face_idx)

    if found_path_faces:
        print(f"Path found: {len(found_path_faces)} faces.")
        extract_path_data() # Extract centers and normals
        # Visualization of the path will be handled in a separate step/function
        # Later: call a function like visualize_path(found_path_faces)
    else:
        print("No path found between the selected faces.")
        found_path_faces.clear() # Ensure it's empty if no path

    # Visualization and output will be called from here or after this function returns
    visualize_path()
    print("Path visualized. Press 's' in the graphics window to save path data, 'r' to reset, 'h' for help.")
    # Saving will be triggered by a key press callback.

def save_path_data_to_file(filename="path_data.txt"):
    """Saves the extracted path coordinates and normals to a file."""
    global path_coords_normals

    if not path_coords_normals:
        print("No path data to save.")
        return

    try:
        with open(filename, 'w') as f:
            f.write("# Path data: x, y, z, nx, ny, nz, face_index\n")
            for data in path_coords_normals:
                p = data['point']
                n = data['normal']
                f.write(f"{p[0]},{p[1]},{p[2]},{n[0]},{n[1]},{n[2]},{data['face_index']}\n")
        print(f"Path data saved to {filename}")
    except Exception as e:
        print(f"Error saving path data to file: {e}")

def key_press_callback(event):
    """Callback function for key presses."""
    global plotter
    if not event.actor: return # no actor associated with event

    if event.key == 's' or event.key == 'S':
        if path_coords_normals:
            save_path_data_to_file()
        else:
            print("No path data available to save. First select two points to generate a path.")
    elif event.key == 'r' or event.key == 'R':
        print("Resetting selections and path...")
        selected_faces.clear()
        found_path_faces.clear()
        path_coords_normals.clear()
        plotter.remove("path_lines_actor", "path_points_actor") # Remove visual path
        plotter.remove(plotter.actors[-MAX_SELECTIONS:]) # Remove selection spheres (assuming they are last added)

        # Restore original mesh colors
        if hasattr(vedo_mesh, "_original_colors") and vedo_mesh._original_colors is not None:
            vedo_mesh.celldata["colors"] = vedo_mesh._original_colors.copy()
        else:
            vedo_mesh.color('lightgrey', on='cells')
        vedo_mesh.mapper().SetScalarModeToUseCellData()
        plotter.render()
        print("Selections and path reset. Click two new points.")
    elif event.key == 'h' or event.key == 'H':
        print("\n--- Help ---")
        print("Mouse Click: Select start/end face for pathfinding.")
        print("S: Save current path data to 'path_data.txt'.")
        print("R: Reset selections and current path.")
        print("H: Show this help message.")
        print("Close window to exit.")
        print("------------\n")


def visualize_path():
    """Visualizes the found path on the vedo_mesh."""
    global found_path_faces, vedo_mesh, plotter, path_coords_normals

    if not found_path_faces:
        print("No path to visualize.")
        return

    print("Visualizing path...")

    # Reset colors of previously selected/path faces if any, except for the two main selections
    # This requires a bit more sophisticated color management if we want to keep selections red
    # For now, let's ensure the original colors are restored before highlighting the new path.
    if hasattr(vedo_mesh, "_original_colors") and vedo_mesh._original_colors is not None:
        vedo_mesh.celldata["colors"] = vedo_mesh._original_colors.copy()
    else:
        # Fallback: color all faces lightgrey if no original_colors snapshot
        vedo_mesh.color('lightgrey', on='cells')

    # Highlight current selected faces (start and end)
    current_colors = vedo_mesh.celldata["colors"]
    if current_colors is None or len(current_colors) != trimesh_mesh.faces.shape[0]:
        current_colors = np.repeat([vedo_mesh.color()], trimesh_mesh.faces.shape[0], axis=0)

    for face_idx, _ in selected_faces: # selected_faces stores (idx, click_pos)
        current_colors[face_idx] = vedo.colors.getColor('red') # Keep selections red

    # Highlight faces in the path
    for face_idx in found_path_faces:
        if face_idx != selected_faces[0][0] and face_idx != selected_faces[1][0]: # Don't overwrite start/end
            current_colors[face_idx] = vedo.colors.getColor('green') # Path faces in green

    vedo_mesh.celldata["colors"] = current_colors
    vedo_mesh.mapper().SetScalarModeToUseCellData()

    # Draw lines connecting face centers of the path
    # Remove previous path lines if they exist
    plotter.remove("path_lines_actor", "path_points_actor") # Give names to remove them later

    if path_coords_normals and len(path_coords_normals) > 1:
        path_points = [data['point'] for data in path_coords_normals]
        path_lines = vedo.Line(path_points, c='blue', lw=3)
        path_spheres = vedo.Spheres([data['point'] for data in path_coords_normals], r=vedo_mesh.avg_size()*0.005, c='blue')

        plotter.add(path_lines.name("path_lines_actor"))
        plotter.add(path_spheres.name("path_points_actor"))

    plotter.render()
    print("Path visualized with green faces and blue center lines.")


def extract_path_data():
    """Extracts center points and normals for each face in found_path_faces."""
    global found_path_faces, trimesh_mesh, path_coords_normals

    path_coords_normals.clear() # Clear previous data

    if not found_path_faces:
        print("No path available to extract data from.")
        return

    print("Extracting face centers and normals for the path...")
    for face_idx in found_path_faces:
        center = trimesh_mesh.triangles_center[face_idx]
        normal = trimesh_mesh.face_normals[face_idx]
        path_coords_normals.append({'point': center, 'normal': normal, 'face_index': face_idx})

    print(f"Extracted data for {len(path_coords_normals)} points.")
    # For debugging, print the first few points and normals
    for i, data in enumerate(path_coords_normals[:3]):
        print(f"  Face {data['face_index']}: Center={data['point']}, Normal={data['normal']}")


def load_and_display_stl():
    """Loads the STL file using trimesh and displays it using vedo."""
    global trimesh_mesh, vedo_mesh, plotter

    try:
        # Load the STL file using trimesh for robust processing
        trimesh_mesh = trimesh.load_mesh(STL_FILE)
    except Exception as e:
        print(f"Error loading STL file with trimesh: {e}")
        return

    if not trimesh_mesh.is_watertight:
        print("Warning: Mesh is not watertight. Attempting to fix.")
        # trimesh_mesh.fill_holes() # This can be slow and sometimes problematic
        trimesh_mesh.process(validate=False) # General processing and healing, skip validation if causing issues

    if not trimesh_mesh.faces.shape[0] > 0:
        print("Error: No faces found in the mesh.")
        return

    build_face_adjacency_graph() # Build graph after loading mesh

    # Convert trimesh object to a vedo Mesh object
    # vedo can take vertices and faces directly
    vedo_mesh = vedo.Mesh([trimesh_mesh.vertices, trimesh_mesh.faces])
    vedo_mesh.compute_normals() # Ensure normals are computed for lighting
    vedo_mesh.color('lightgrey').edge_color('black').lw(0.1) # Set appearance

    # Create a vedo Plotter instance
    plotter = vedo.Plotter(title="STL Path Finder", axes=1) # axes=1 for basic grid axes
    plotter.add(vedo_mesh)

    # Add the callback for mouse clicks
    plotter.add_callback('mouse click', selection_callback)
    # Add the callback for key presses
    plotter.add_callback('key press', key_press_callback)
    # Initial instruction when plotter is ready, before full interactive mode
    print("Vedo plotter initialized. Press 'h' in the graphics window for command help.")


    plotter.show(interactive=False) # Show but don't block yet, interaction will be handled by callbacks

if __name__ == "__main__":
    print("------------------------------------")
    print("      STL Path Finder Application      ")
    print("------------------------------------")
    print(f"Attempting to load STL file: {STL_FILE}")
    load_and_display_stl()

    if plotter:
        print("\n--- Initial Instructions ---")
        print("1. Click two distinct points on the 3D model to select start and end faces.")
        print("   - Selected faces turn RED.")
        print("   - Clicked points are marked with YELLOW spheres.")
        print("2. Once two faces are selected, a path (GREEN faces, BLUE lines) will be computed and shown.")
        print("3. Press 'h' IN THE GRAPHICS WINDOW for a list of commands (save, reset, etc.).")
        print("4. Close the graphics window to exit the application.")
        print("----------------------------\n")
        plotter.interactive() # Start interaction loop
    else:
        print("Critical Error: Failed to initialize the Vedo plotter. Exiting.")
