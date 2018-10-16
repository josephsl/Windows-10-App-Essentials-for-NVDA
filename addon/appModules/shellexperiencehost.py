#A part of NonVisual Desktop Access (NVDA)
#Copyright (C) 2015-2018 NV Access Limited
#This file is covered by the GNU General Public License.
#See the file COPYING for more details.
# Borrowed directly from NVDA Core (2016-2018 Joseph Lee)

from nvdaBuiltin.appModules.shellexperiencehost import *
from NVDAObjects.UIA import UIA
import controlTypes
import ui
import wx

# NVDA Core issue 8845: there are "toggle buttons" that are not really toggle controls and exposes additional values via UIA.
statusActions = ("Brightness", "QuietHours")

class AppModule(AppModule):

	def event_NVDAObject_init(self, obj):
		if isinstance(obj, UIA):
			if obj.name == "" and obj.UIAElement.cachedAutomationID == "TextBoxPinEntry":
				obj.name = obj.previous.name

	def event_liveRegionChange(self, obj, nextHandler):
		# No, do not let Start menu size be announced.
		if isinstance(obj, UIA) and obj.UIAElement.cachedAutomationID == "FrameSizeAccessibilityField": return
		nextHandler()

	def event_UIA_itemStatus(self, obj, nextHandler):
		if isinstance(obj, UIA):
			if obj.UIAElement.cachedAutomationID.endswith(statusActions):
				itemStatus = obj.UIAElement.currentItemStatus
				if itemStatus: ui.message("{0}: {1}".format(obj.name, itemStatus))
		nextHandler()
