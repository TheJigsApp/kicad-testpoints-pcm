import logging
import os
import wx
import wx.aui
import wx.lib.buttons as buttons
from pathlib import Path
import pcbnew

from kicad_testpoints import (
    get_pads_by_property,
    build_test_point_report,
    write_csv,
    Settings,
)

_log = logging.getLogger("kicad_testpoints")


class Meta:
    toolname = "kicadtestpoints"
    title = "Test Point Report"
    body = """Choose test points by setting the desired pads 'Fabrication Property' to 'Test Point Pad'. The output default is in the JigsApp test point report style.

Coordinates are Cartesian with x increasing to the right and y increasing upwards. For correct agreement with generated gerbers and the component placement, ensure the origin used is consistent.
    """
    about_text = "This plugin generates TheJigsApp style test points reports. Test more, worry less."
    short_description = "TheJigsApp KiCAD Test Point Report"
    frame_title = "TheJigsApp KiCAD Test Point Report"
    website = "https://www.thejigsapp.com"
    version = "0.1.9"


class SuccessPanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)

        # Static text for success message
        success_text = "Submission successful!"
        success_label = wx.StaticText(self, label=success_text)

        # Sizer for layout
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(success_label, 0, wx.ALL, 5)
        self.SetSizer(sizer)


def setattr_keywords(obj, name, value):
    return setattr(obj, name, value)


class MyPanel(wx.Panel):
    def __init__(self, parent):
        _log.debug("MyPanel.__init__")
        super().__init__(parent)
        self.settings = Settings()

        # Get current working directory
        dir_ = Path(os.getcwd())
        wd = Path(pcbnew.GetBoard().GetFileName()).absolute()
        if wd.exists():
            dir_ = wd.parent
        default_file_path = dir_ / f"{Meta.toolname}-report.csv"

        # File output selector
        file_output_label = wx.StaticText(self, label="File Output:")
        self.file_output_selector = wx.FilePickerCtrl(
            self,
            style=wx.FLP_SAVE | wx.FLP_USE_TEXTCTRL,
            wildcard="CSV files (*.csv)|*.csv",
            path=default_file_path.as_posix(),
        )

        # Lorem Ipsum text
        lorem_text = wx.StaticText(self, label=Meta.body)

        # Buttons
        self.submit_button = buttons.GenButton(self, label="Submit")
        self.cancel_button = buttons.GenButton(self, label="Cancel")
        self.submit_button.SetBackgroundColour(wx.Colour(150, 225, 150))
        self.cancel_button.SetBackgroundColour(wx.Colour(225, 150, 150))
        self.submit_button.Bind(wx.EVT_BUTTON, self.on_submit)
        self.cancel_button.Bind(wx.EVT_BUTTON, self.on_cancel)

        # Horizontal box sizer for buttons
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        button_sizer.Add(self.submit_button, 0, wx.ALL | wx.EXPAND, 5)
        button_sizer.Add(self.cancel_button, 0, wx.ALL, 5)

        # Origin selectiondd
        self.use_aux_origin_cb = wx.CheckBox(self, label="Use drill/place file origin")
        self.use_aux_origin_cb.SetValue(True)
        self.settings.use_aux_origin = self.use_aux_origin_cb.GetValue()

        self.Bind(wx.EVT_CHECKBOX, self.on_checkbox_toggle)

        # Sizer for layout
        # sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.use_aux_origin_cb, 0, wx.ALL, 10)

        sizer.Add(file_output_label, 0, wx.ALL, 5)
        sizer.Add(self.file_output_selector, 0, wx.EXPAND | wx.ALL, 5)
        sizer.Add(lorem_text, 1, wx.EXPAND | wx.ALL, 5)
        sizer.Add(button_sizer, 0, wx.ALIGN_RIGHT | wx.ALL, 5)

        self.SetSizer(sizer)
        # self.SetSizeHints(1000,1000)
        # self.SetMinSize((1000, 1000))  # Set a minimum width and height for the frame
        self.Layout()

    def on_checkbox_toggle(self, event):
        checkbox = event.GetEventObject()
        self.settings.use_aux_origin = checkbox.GetValue()

    def on_submit(self, event):
        file_path = Path(self.file_output_selector.GetPath())
        if file_path:
            print("Submitting...")
            print("File Path:", file_path)

            board = pcbnew.GetBoard()

            pads = get_pads_by_property(board)
            data = build_test_point_report(board, pads=pads, settings=self.settings)
            if not data:
                wx.MessageBox(
                    "No test point pads found, have you set any?",
                    "Error",
                    wx.OK | wx.ICON_ERROR,
                )
            else:
                write_csv(data, filename=file_path)
                self.GetTopLevelParent().EndModal(wx.ID_OK)
                # self.GetParent().ShowSuccessPanel()
        else:
            wx.MessageBox(
                "Please select a file output path.", "Error", wx.OK | wx.ICON_ERROR
            )

    def on_cancel(self, event):
        print("Canceling...")
        self.GetTopLevelParent().EndModal(wx.ID_CANCEL)


class AboutPanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        font = wx.Font(
            12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL
        )
        bold = wx.Font(
            10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD
        )

        # Static text for about information
        message_text = wx.StaticText(self, label=Meta.about_text)
        version_text = wx.StaticText(self, label=f"Version: {Meta.version}")

        pre_link_text = wx.StaticText(self, label="For more information visit: ")
        from wx.lib.agw.hyperlink import HyperLinkCtrl

        link = HyperLinkCtrl(self, wx.ID_ANY, f"{Meta.website}", URL=Meta.website)

        link.SetColours(wx.BLUE, wx.BLUE, wx.BLUE)
        version_text.SetFont(bold)
        message_text.SetFont(font)
        pre_link_text.SetFont(font)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(version_text, 1, wx.EXPAND | wx.ALL, 5)
        sizer.Add(message_text, 1, wx.EXPAND | wx.ALL, 5)

        link_sizer = wx.BoxSizer(wx.HORIZONTAL)
        link_sizer.Add(pre_link_text, 0, wx.EXPAND, 0)
        link_sizer.Add(link, 0, wx.EXPAND, 0)
        sizer.Add(link_sizer, 1, wx.EXPAND | wx.ALL, 5)

        self.SetSizer(sizer)


class MyDialog(wx.Dialog):
    def __init__(self, parent, title):
        super().__init__(
            parent, title=title, style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
        )

        # Create a notebook with two tabs
        notebook = wx.Notebook(self)
        tab_panel = MyPanel(notebook)
        about_panel = AboutPanel(notebook)
        self.success_panel = SuccessPanel(notebook)

        notebook.AddPage(tab_panel, "Main")
        notebook.AddPage(about_panel, "About")

        # Sizer for layout
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(notebook, 1, wx.EXPAND | wx.ALL, 10)
        self.SetSizer(sizer)
        self.SetSizeHints(500, 500)  # Set minimum size hints

    def on_close(self, event):
        self.EndModal(wx.ID_CANCEL)
        event.Skip()

    def ShowSuccessPanel(self):
        self.GetSizer().GetChildren()[0].GetWindow().Destroy()
        self.GetSizer().Insert(0, self.success_panel)
        self.Layout()

    def on_maximize(self, event):
        self.fit_to_screen()

    def on_size(self, event):
        if self.IsMaximized():
            self.fit_to_screen()

    def fit_to_screen(self):
        screen_width, screen_height = wx.DisplaySize()
        self.SetSize(wx.Size(screen_width, screen_height))


class Plugin(pcbnew.ActionPlugin, object):
    def __init__(self):
        super().__init__()

        logging.basicConfig()
        _log.setLevel(logging.DEBUG)
        _log.debug("Loading kicad_testpoints")

        self.logger = None
        self.config_file = None

        self.name = Meta.title
        self.category = "Read PCB"
        self.pcbnew_icon_support = hasattr(self, "show_toolbar_button")
        self.show_toolbar_button = True
        icon_dir = os.path.dirname(__file__)
        self.icon_file_name = os.path.join(icon_dir, "icon.png")
        self.description = Meta.body

    def Run(self):
        try:
            dlg = MyDialog(None, title=Meta.title)
            dlg.ShowModal()

        finally:
            dlg.Destroy()
