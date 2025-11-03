import time
from gns3fy import Gns3Connector, Project

def safe_cleanup_project(project):
    print(f"🔹 Cleaning up project: {project.name}")

    # Fetch latest data
    project.get()
    project.get_nodes()
    project.get_links()

    # Delete all links first
    print(f"Deleting {len(project.links)} links...")
    for link in project.links:
        try:
            link.delete()
            print(f"  ✅ Deleted link {link.link_id}")
            time.sleep(0.2)
        except Exception as e:
            print(f"  ⚠️ Failed to delete link {link.link_id}: {e}")

    # Stop project before node deletion
    try:
        project.stop()
        print("⏹ Project stopped.")
    except Exception:
        print("⚠️ Project was not running or already stopped.")
    time.sleep(0.5)

    # Delete all nodes
    print(f"Deleting {len(project.nodes)} nodes...")
    for node in project.nodes:
        try:
            node.delete()
            print(f"  ✅ Deleted node {node.name}")
            time.sleep(0.5)
        except Exception as e:
            print(f"  ⚠️ Failed to delete node {node.name}: {e}")

    print("🧹 Cleanup complete!")

# Example usage
if __name__ == "__main__":
    server = Gns3Connector("http://localhost:3080")
    project = Project(name="test2", connector=server)
    project.get()
    safe_cleanup_project(project)
