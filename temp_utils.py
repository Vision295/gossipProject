import docker
from gns3fy import Gns3Connector
import tarfile
import io
import os

def osef():
      client = docker.from_env()
      container = client.containers.get("your_container_name_or_id")

      # --------------------------
      # File to copy
      host_file_path = "/path/to/local/file.txt"
      container_dest_path = "/app/file.txt"

      # Create a tar archive in memory with the file
      tarstream = io.BytesIO()
      with tarfile.open(fileobj=tarstream, mode='w') as tar:
            tar.add(host_file_path, arcname=os.path.basename(host_file_path))
      tarstream.seek(0)

      # Copy the tar archive into the container at the desired path
      container.put_archive(os.path.dirname(container_dest_path), tarstream)
      print(f"✅ File copied to {container_dest_path}")

def get_all_tempales():

      server = Gns3Connector(url="http://localhost:3080")
      # Fetch list of templates on the server
      templates = server.get_templates()

      for t in templates:
            print(f"Template name: {t['name']}  —  ID: {t['template_id']}")

get_all_tempales()