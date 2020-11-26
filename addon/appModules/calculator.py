# appModules/calculator.py
# A part of NonVisual Desktop Access (NVDA)
# Copyright (C) 2015-2020 NV Access Limited, Joseph Lee
# This file is covered by the GNU General Public License.
# See the file COPYING for more details.

"""App module for Windows 10 Calculator"""

import appModuleHandler
import api
from NVDAObjects.UIA import UIA
import queueHandler
import ui
import scriptHandler

# NVDA Core issue 9428: do not announce current values until calculations are done
# in order to avoid repetitions.
noCalculatorEntryAnnouncements = [
	# Display field with Calculator set to full screen mode.
	"CalculatorResults",
	# In the middle of a calculation expression entry.
	"CalculatorExpression",
	# Results display with Calculator set to compact overlay i.e. always on top mode.
	"CalculatorAlwaysOnTopResults",
	# Calculator expressions with Calculator set to always on top mode.
	"ExpressionContainer",
	# Date range selector.
	"ContentPresenter",
	# Briefly shown when closing date calculation calendar.
	"Light Dismiss",
]


class AppModule(appModuleHandler.AppModule):

	def event_NVDAObject_init(self, obj):
		if not isinstance(obj, UIA):
			return
		# Version 10.2009 introduces a regression where history items have no names
		# but can be fetched through its children.
		if not obj.name and obj.parent.UIAAutomationId == "HistoryListView":
			obj.name = "".join([item.name for item in obj.children])

	_shouldAnnounceResult = False
	# Name change says the same thing multiple times for some items.
	_resultsCache = ""

	def event_nameChange(self, obj, nextHandler):
		if not isinstance(obj, UIA):
			return
		# No, announce value changes immediately except for calculator results and expressions.
		if (
			obj.UIAElement.cachedAutomationId in noCalculatorEntryAnnouncements
			or obj.UIAElement.cachedClassName == "LandmarkTarget"
		):
			self._shouldAnnounceResult = False
		# For the rest:
		elif (
			obj.UIAElement.cachedAutomationId not in noCalculatorEntryAnnouncements
			and obj.name != self._resultsCache
		):
			# For unit conversion, UIA notification event presents much better messages.
			# For date calculation, live region change event is also fired for difference between dates.
			if obj.UIAElement.cachedAutomationId not in ("Value1", "Value2", "DateDiffAllUnitsResultLabel"):
				ui.message(obj.name)
			self._resultsCache = obj.name
		if not self._shouldAnnounceResult:
			return
		self._shouldAnnounceResult = False
		nextHandler()

	def event_UIA_notification(self, obj, nextHandler, displayString=None, activityId=None, **kwargs):
		# Some notification messages are repeated (most notable being graph view change notification).
		if activityId == "GraphViewChanged" and self._resultsCache == displayString:
			return
		self._resultsCache = displayString
		# From May 2018 onwards, unit converter uses a different automation iD.
		# Changed significantly in July 2018 thanks to UI redesign, and as a result, attribute error is raised.
		try:
			shouldAnnounceNotification = obj.previous.UIAElement.cachedAutomationId in (
				"numberPad", "UnitConverterRootGrid"
			)
		except AttributeError:
			# Another UI redesign in 2019, causing attribute error when changing categories.
			resultElement = api.getForegroundObject().children[1].lastChild
			# Another redesign in 2019 due to introduction of "always on top" i.e. picture-in-picture mode.
			if resultElement.UIAElement.cachedClassName != "LandmarkTarget":
				resultElement = resultElement.parent.children[1]
			shouldAnnounceNotification = (
				resultElement and resultElement.firstChild
				and resultElement.firstChild.UIAElement.cachedAutomationId not in noCalculatorEntryAnnouncements
			)
		# Announce activity ID's other than "DisplayUpdate" as this is redundant if speak typed characters is on
		# (activity ID's courtesy of Microsoft Calculator source code hosted on GitHub, MIT license).
		if shouldAnnounceNotification or activityId != "DisplayUpdated":
			nextHandler()

	# A list of native commands to handle calculator result announcement.
	_calculatorResultGestures = ("kb:enter", "kb:numpadEnter", "kb:escape")

	@scriptHandler.script(gestures=_calculatorResultGestures)
	def script_calculatorResult(self, gesture):
		# To prevent double focus announcement, check where we are.
		focus = api.getFocusObject()
		gesture.send()
		# In redstone, calculator result keeps firing name change,
		# so tell it to do so if and only if enter has been pressed.
		self._shouldAnnounceResult = True
		# Hack: only announce display text when an actual calculator button (usually equals button) is pressed.
		# In redstone, pressing enter does not move focus to equals button.
		if isinstance(focus, UIA):
			if focus.UIAElement.cachedAutomationId == "CalculatorResults":
				queueHandler.queueFunction(queueHandler.eventQueue, focus.reportFocus)
			else:
				resultsScreen = api.getForegroundObject().children[1].lastChild
				if isinstance(resultsScreen, UIA) and resultsScreen.UIAElement.cachedClassName == "LandmarkTarget":
					# And no, do not allow focus to move.
					queueHandler.queueFunction(queueHandler.eventQueue, resultsScreen.firstChild.reportFocus)
