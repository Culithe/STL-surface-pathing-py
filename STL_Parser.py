import numpy as np
import struct

def parse_stl(file_path):
    """
    Parses an STL file, detecting whether it's ASCII or binary,
    and extracts all vertex coordinates.

    Args:
        file_path (str): The path to the STL file.

    Returns:
        numpy.ndarray: A NumPy array of shape (n, 3, 3) containing
                       the vertices of n triangles. Returns None if
                       the file cannot be parsed.
    """
    try:
        with open(file_path, 'rb') as f:
            # Check if the file is ASCII or binary
            # ASCII STL files start with the keyword 'solid'
            header = f.read(5)
            f.seek(0)
            if header == b'solid':
                # Attempt to parse as ASCII
                try:
                    return parse_ascii_stl(file_path)
                except Exception as e:
                    # If ASCII parsing fails, it might be a binary file
                    # that happens to start with 'solid'.
                    print(f"ASCII parsing failed with error: {e}. Attempting binary parse.")
                    f.seek(0)
                    return parse_binary_stl(f)
            else:
                # Parse as binary
                return parse_binary_stl(f)
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

def parse_ascii_stl(file_path):
    """Parses an ASCII STL file."""
    print("Parsing ASCII STL file...")
    vertices = []
    with open(file_path, 'r') as f:
        triangle = []
        for line in f:
            line = line.strip()
            if line.startswith('vertex'):
                parts = line.split()
                # Expecting 'vertex x y z'
                if len(parts) == 4:
                    try:
                        vertex = [float(parts[1]), float(parts[2]), float(parts[3])]
                        triangle.append(vertex)
                        if len(triangle) == 3:
                            vertices.append(triangle)
                            triangle = []
                    except ValueError:
                        print(f"Warning: Could not parse vertex line: {line}")
                        # If a vertex line is malformed, discard the current triangle
                        triangle = []
    
    if not vertices:
        print("Warning: No vertices found in ASCII STL file.")
        return None
        
    print(f"Successfully parsed {len(vertices)} triangles.")
    # Using float32 for memory efficiency with large datasets
    return np.array(vertices, dtype=np.float32)


def parse_binary_stl(f):
    """Parses a binary STL file."""
    print("Parsing binary STL file...")
    # Skip the 80-byte header
    header = f.read(80)
    
    # Read the number of triangles
    num_triangles_bytes = f.read(4)
    if len(num_triangles_bytes) < 4:
        print("Error: Invalid binary STL file. Cannot read number of triangles.")
        return None
    num_triangles = struct.unpack('<I', num_triangles_bytes)[0]
    
    if num_triangles == 0:
        print("Warning: The STL file contains 0 triangles.")
        return np.array([], dtype=np.float32)

    print(f"File contains {num_triangles} triangles.")
    
    # Pre-allocate a NumPy array for efficiency.
    # Each triangle has 3 vertices, each with 3 coordinates (x, y, z).
    # Using float32 is sufficient for precision and saves memory.
    vertices = np.empty((num_triangles, 3, 3), dtype=np.float32)
    
    # Each triangle is represented by 50 bytes
    # 12 bytes for normal vector (3 floats)
    # 36 bytes for 3 vertices (9 floats)
    # 2 bytes for attribute byte count (short)
    triangle_format = '12fH' # 12 floats and 1 unsigned short
    
    for i in range(num_triangles):
        try:
            # Read the 50 bytes for the current triangle
            triangle_data = f.read(50)
            if len(triangle_data) < 50:
                print(f"Warning: Unexpected end of file at triangle {i+1}. "
                      f"Returning {i} triangles.")
                return vertices[:i]

            # Unpack the data. We only need the vertices.
            # Normal vector is parts[0:3]
            # Vertices are parts[3:12]
            parts = struct.unpack(triangle_format, triangle_data)
            
            # Reshape the 9 vertex coordinates into a (3, 3) array
            vertex_data = np.array(parts[3:12], dtype=np.float32).reshape(3, 3)
            vertices[i] = vertex_data
            
        except struct.error as e:
            print(f"Error parsing triangle {i+1}: {e}")
            # Return the vertices that have been successfully parsed so far
            return vertices[:i]
            
    print(f"Successfully parsed {len(vertices)} triangles.")
    return vertices