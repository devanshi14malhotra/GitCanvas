# AI-generated fix (fallback):
```diff
PR: Fix extra <text> element on application page, Closes #65

diff --git a/app.py b/app.py
index 34a6b6c..f2b7c4a 100644
--- a/app.py
+++ b/app.py
@@ -1,6 +1,5 @@
-from xml.etree import ElementTree as ET
 import tkinter as tk

-def create_text_element():
-    return ET.Element("text")
 
 class Application(tk.Frame):
     def __init__(self, master=None):
         super().__init__(master)
         self.master = master
-        self.text_element = create_text_element()
         self.pack()
         self.create_widgets()
```

Note: The above diff assumes that the `create_text_element` function is responsible for creating the extra `<text>` element. The actual fix may vary depending on the implementation of the `app.py` file.
