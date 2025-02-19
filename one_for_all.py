import os
import open3d as o3d
import xml.etree.ElementTree as ET
import tkinter as tk
from tkinter import filedialog, ttk, messagebox

# Initialize Tkinter (hide root window)
root = tk.Tk()
root.title("File Merger")
root.geometry("300x150")  # Set window size

def parse_osm(file_path):
    """Parse OSM XML file and return its elements."""
    tree = ET.parse(file_path)
    root = tree.getroot()
    
    nodes, ways, relations = {}, {}, {}
    for elem in root:
        if elem.tag == "node":
            nodes[elem.attrib["id"]] = elem
        elif elem.tag == "way":
            ways[elem.attrib["id"]] = elem
        elif elem.tag == "relation":
            relations[elem.attrib["id"]] = elem
    
    return nodes, ways, relations

def merge_pcd_files():
    """Merge selected PCD files."""
    pcd_files = filedialog.askopenfilenames(title="Select PCD Files", filetypes=[("Point Cloud Files", "*.pcd")])

    if not pcd_files:
        return

    output_path = filedialog.asksaveasfilename(
        title="Save Merged PCD File As",
        defaultextension=".pcd",
        filetypes=[("Point Cloud Files", "*.pcd")]
    )

    if not output_path:
        return

    merged_pcd = o3d.geometry.PointCloud()

    for file in pcd_files:
        try:
            pcd = o3d.io.read_point_cloud(file)
            merged_pcd += pcd
        except Exception as e:
            messagebox.showerror("Error", f"Error reading {file}: {e}")
            return

    o3d.io.write_point_cloud(output_path, merged_pcd)
    messagebox.showinfo("Success", f"Merged PCD file saved as {output_path}")

def merge_osm_files():
    """Merge selected OSM XML files while avoiding ID conflicts."""
    file_paths = filedialog.askopenfilenames(title="Select OSM Files", filetypes=[("OSM Files", "*.osm")])

    if not file_paths:
        return

    all_nodes, all_ways, all_relations = {}, {}, {}
    max_node_id, max_way_id, max_relation_id = 0, 0, 0

    for file_path in file_paths:
        nodes, ways, relations = parse_osm(file_path)

        if nodes:
            max_node_id = max(max_node_id, max(map(int, nodes.keys())))
        if ways:
            max_way_id = max(max_way_id, max(map(int, ways.keys())))
        if relations:
            max_relation_id = max(max_relation_id, max(map(int, relations.keys())))

        id_mapping = {}

        for node_id in list(nodes.keys()):
            new_id = str(max_node_id + 1)
            id_mapping[node_id] = new_id
            nodes[new_id] = nodes.pop(node_id)
            nodes[new_id].attrib["id"] = new_id
            max_node_id += 1

        for way_id in list(ways.keys()):
            new_id = str(max_way_id + 1)
            id_mapping[way_id] = new_id
            ways[new_id] = ways.pop(way_id)
            ways[new_id].attrib["id"] = new_id
            max_way_id += 1
            
            for nd in ways[new_id].findall("nd"):
                if nd.attrib["ref"] in id_mapping:
                    nd.attrib["ref"] = id_mapping[nd.attrib["ref"]]

        for relation_id in list(relations.keys()):
            new_id = str(max_relation_id + 1)
            id_mapping[relation_id] = new_id
            relations[new_id] = relations.pop(relation_id)
            relations[new_id].attrib["id"] = new_id
            max_relation_id += 1

            for member in relations[new_id].findall("member"):
                if member.attrib["ref"] in id_mapping:
                    member.attrib["ref"] = id_mapping[member.attrib["ref"]]

        all_nodes.update(nodes)
        all_ways.update(ways)
        all_relations.update(relations)

    output_path = filedialog.asksaveasfilename(title="Save Merged OSM File As", defaultextension=".osm", filetypes=[("OSM Files", "*.osm")])

    if not output_path:
        return

    merged_root = ET.Element("osm", {"generator": "MergedOSM", "version": "0.6"})
    merged_root.extend(all_nodes.values())
    merged_root.extend(all_ways.values())
    merged_root.extend(all_relations.values())

    tree = ET.ElementTree(merged_root)
    tree.write(output_path, encoding="utf-8", xml_declaration=True)

    messagebox.showinfo("Success", f"Merged OSM file saved as {output_path}")

def handle_selection(event):
    """Handle dropdown selection and call the appropriate function."""
    selection = dropdown_var.get()
    if selection == "PCD Merge":
        merge_pcd_files()
    elif selection == "OSM Merge":
        merge_osm_files()

# Create dropdown menu
dropdown_var = tk.StringVar()
dropdown = ttk.Combobox(root, textvariable=dropdown_var, state="readonly")
dropdown["values"] = ["PCD Merge", "OSM Merge"]
dropdown.current(0)  # Default selection
dropdown.pack(pady=20)

# Run function when selection is made
dropdown.bind("<<ComboboxSelected>>", handle_selection)

# Run the Tkinter main loop
root.mainloop()