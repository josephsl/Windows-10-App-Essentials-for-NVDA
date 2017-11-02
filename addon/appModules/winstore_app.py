# Windows 10 Store
# Part of Windows 10 App Essentials collection
# Copyright 2016-2017 Joseph Lee, released under GPL

# Enhancements to support Windows Store.

import appModuleHandler
import ui
import controlTypes
from NVDAObjects.UIA import UIA

class AppModule(appModuleHandler.AppModule):

	def event_NVDAObject_init(self, obj):
		# Workarounds for vairous lists.
		if isinstance(obj, UIA) and obj.role == controlTypes.ROLE_LISTITEM and obj.firstChild:
			childElement = obj.firstChild.UIAElement
			# Extraneous information announced when going through apps to be updated/installed, so use a grandchild's name.
			if childElement.cachedAutomationID == "InstallControl":
				obj.name = obj.firstChild.firstChild.name
			# Navigation menu items with generic class name as the label (seen in certain variants of 11710 release).
			elif childElement.cachedClassName == "AppBarButton" and obj.parent.UIAElement.cachedAutomationID == "MenuItemsHost":
				obj.name = obj.firstChild.name

	# just like Settings app, have a cache of download progress text handy.
	_appInstallProgress = ""

	def event_liveRegionChange(self, obj, nextHandler):
		if isinstance(obj, UIA) and obj.UIAElement.cachedAutomationID == "_progressText":
			if obj.name != self._appInstallProgress:
				self._appInstallProgress = obj.name
				# Don't forget to announce product title.
				productTitle = obj.parent.previous
				# Since March 2017 update, it is no longer the product name, but a progress button.
				if productTitle and productTitle.role == controlTypes.ROLE_BUTTON:
					# But since September 2017 update, the title is next door.
					possibleProductTitle = productTitle.parent.previous
					productTitle = productTitle.previous if possibleProductTitle is None else productTitle.parent.previous
				if productTitle and isinstance(productTitle, UIA) and productTitle.UIAElement.cachedAutomationID == "_productTitle":
					ui.message(" ".join([productTitle.name, obj.name]))
			return
		nextHandler()
