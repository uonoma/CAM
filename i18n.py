import gettext
import locale
from header import resource_path

(defLang, defEncoding) = locale.getdefaultlocale()

lang = gettext.translation('base', localedir="locales", languages=[defLang])
lang.install()
_ = lang.gettext

#Translatable strings
# Menu
NODESTR = _("Add Node")
LINKSTR = _("Add Link")
ADDULINKSTR = _("Add Unidirectional Link")
ADDBLINKSTR = _("Add Bidirectional Link")
COMMENTSTR = _("Add Comment")
SHEETSTR = _("Sheet")

NEWSTR = _("New")
OPENSTR = _("Open")
SAVESTR = _("Save")
SAVEASSTR = _("Save as...")

FILESTR = _("File")
EDITSTR = _("Edit")

ADDSTR = _("Add")

REMOVESTR = _("Remove")

UNIDIRECTIONAL = _("Unidirectional")
BIDIRECTIONAL = _("Bidirectional")

UNDOSTR = _("Undo")

HELPSTR = _("Help")

VIEWSTR = _("View")
RESIZABLENODESSTR = _("Resizable Nodes")
DEFAULTRADIUSSTR = _("Default Radius For All Nodes")

COMBINEAMBNEUTRALNODESSTR = _("Combine Ambivalent And Neutral Nodes")
AMBNODESSEPARATELYSTR = _("Display Ambivalent Nodes Separately")
AGGREGATESTR = _("Aggregate CAMs")

# Title bar
PROGRAMSTR = "CAMMaker "

# Message boxes

ASKSAVESTR = _("Would you like to save your map?")
ALLFILESSTR = _("All Files")
FILESSTR = _("Files")

SELECTAGGRSTR = _("Select files to aggregate")
SELECTFILESTR = _("Select file")
SELECTPREFILESTR = _("Select pre-CAM file")
SELECTPOSTFILESTR = _("Select post-CAM file")

# Menu buttons
MINUSSTR = _("Subtract CAMs")
RESETSTR = _("Reset node sizes to default")
EXPORTPNGSTR = _("Export as .png")
OPENJSON = _("Read CAM from a JSON file")