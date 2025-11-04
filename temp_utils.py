from gns3fy import Gns3Connector, Node

def get_all_tempales():
      """get all templates of all gns3 project on a localhost connection"""

      server = Gns3Connector(url="http://localhost:3080")
      # Fetch list of templates on the server
      templates = server.get_templates()

      for t in templates:
            print(f"Template name: {t['name']}  —  ID: {t['template_id']}")

get_all_tempales()