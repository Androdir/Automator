from ui_automator import Ui_MainWindow

from PyQt5 import QtCore, QtGui, QtWidgets
from ctypes import windll, Structure, c_long, byref
import json
import sys
from threading import Thread
import time
import re
import os
import keyboard
import mouse

inputs = []
inputs_text = []
automations = []
selected_automation = {}
selected_automation_name = ""

settings = json.load(open("data/settings.json", "r"))

def capitalise(string):
	return string[0].upper() + string[1:]

def update_inputs_text():
	for input in inputs:
		inputs_text.append(input.text)

def key_is_held(key):
	update_inputs_text()

	press = f"Key Press - {key}"
	release = f"Key Release - {key}"

	try:
		press_index = inputs_text.index(press)
	except:
		press_index = -1

	try:
		release_index = inputs_text.index(release)
	except:
		release_index = -1

	if press_index > release_index:
		return True
	
	return False

class Cursor(Structure):
	_fields_ = [("x", c_long), ("y", c_long)]

def get_cursor_pos():
	cursor = Cursor()
	windll.user32.GetCursorPos(byref(cursor))
	return [cursor.x, cursor.y]

class InputListViewItem(QtWidgets.QWidget):
	def __init__(self, parent: QtWidgets.QWidget = None, item_id: int = None, text: str = None, model: QtGui.QStandardItemModel = None, gui = None):
		super(InputListViewItem, self).__init__(parent)

		if not (item_id or text or model or window):
			raise ValueError("item_id, text, and model must all be specified.")

		self.text = text
		self.gui = gui
		self.item_id = item_id
		self.model = model

		self.checkbox = QtWidgets.QCheckBox()
		self.label = QtWidgets.QLabel(f"{item_id + 1}) {text}")
		self.edit_button = QtWidgets.QPushButton("Edit")
		self.edit_button.setToolTip("Edit this input")
		self.delete_button = QtWidgets.QPushButton("Delete")
		self.delete_button.setToolTip("Delete this input")

		self.widget_layout = QtWidgets.QHBoxLayout(self)
		self.widget_layout.addWidget(self.label)
		self.widget_layout.addItem(QtWidgets.QSpacerItem(10, 1, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding))
		self.widget_layout.addWidget(self.edit_button)
		self.widget_layout.addWidget(self.delete_button)
		self.widget_layout.addWidget(self.checkbox)

		self.widget_layout.setContentsMargins(0, 0, 0, 0)

		self.delete_button.clicked.connect(self.delete)
		self.edit_button.clicked.connect(self.edit)

	def execute(self):
		t = self.text.lower()
		if t.startswith("mouse move"):
			t = t.split("-")[1].replace(" ", "")
			t = re.sub("[()]", "", t).split(",")
			x = int(t[0])
			y = int(t[1])
			mouse.move(x, y)
		elif t.startswith("mouse click"):
			t = t.split(" ")[3:]
			if t[0] == "double":
				mouse.double_click(t[1])
			else:
				mouse.click(t[0])
		elif t.startswith("mouse press"):
			t = t.split(" ")[-1]
			mouse.press(button=t)
		elif t.startswith("mouse release"):
			t = t.split(" ")[-1]
			mouse.release(button=t)
		elif t.startswith("key press"):
			t = t.split(" ")[-1]
			keyboard.press(t)
		elif t.startswith("key release"):
			t = t.split(" ")[-1]
			keyboard.release(t)
		elif t.startswith("keystroke"):
			t = t.split(" ")[-1]
			keyboard.send(t)
		elif t.startswith("pause"):
			t = t.split(" ")[-1]
			time.sleep(float(t) / self.gui.loopspeedinput.value())

	def delete(self):
		self.model.removeRow(self.item_id)
		del inputs[self.item_id]
		for i in range(len(inputs)):
			inputs[i].update(i)

		self.gui.update_spin_boxes()

	def update(self, item_id, text: str = ""):
		if not text:
			text = self.text

		self.item_id = item_id
		self.label.setText(f"{self.item_id + 1}) {text}")			

	def edit(self):
		dialog = QtWidgets.QDialog(self.gui.main_window)
		dialog.setWindowFlags(dialog.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)
		dialog.setWindowTitle("Edit Input")

		mousemove = QtWidgets.QPushButton("Change to Mouse Move")
		mouseclick = QtWidgets.QPushButton("Change to Mouse Click")
		mousepress = QtWidgets.QPushButton("Change to Mouse Press")
		mouserelease = QtWidgets.QPushButton("Change to Mouse Release")
		keypress = QtWidgets.QPushButton("Change to Key Press")
		keyrelease = QtWidgets.QPushButton("Change to Key Release")
		keystroke = QtWidgets.QPushButton("Change to Keystroke")
		pause = QtWidgets.QPushButton("Change to Pause")

		grid = QtWidgets.QGridLayout(dialog)
		grid.addWidget(mousemove, 0, 0)
		grid.addWidget(mouseclick, 0, 1)
		grid.addWidget(mousepress, 0, 2)
		grid.addWidget(mouserelease, 1, 0)
		grid.addWidget(keypress, 1, 1)
		grid.addWidget(keyrelease, 1, 2)
		grid.addWidget(keystroke, 2, 0)
		grid.addWidget(pause, 2, 1)

		mousemove.clicked.connect(lambda: self.gui.add_mouse_move_input(self))
		mouseclick.clicked.connect(lambda: self.gui.add_mouse_click_input(self))
		mousepress.clicked.connect(lambda: self.gui.add_mouse_press_input(self))
		mouserelease.clicked.connect(lambda: self.gui.add_mouse_release_input(self))
		keypress.clicked.connect(lambda: self.gui.add_key_press_input(self))
		keyrelease.clicked.connect(lambda: self.gui.add_key_release_input(self))
		keystroke.clicked.connect(lambda: self.gui.add_keystroke_input(self))
		pause.clicked.connect(lambda: self.gui.add_pause(self))

		dialog.exec()

class AutomationListViewItem(QtWidgets.QWidget):
	def __init__(self, parent: QtWidgets.QWidget = None, text: str = None, model: QtGui.QStandardItemModel = None, gui=None):
		super(AutomationListViewItem, self).__init__(parent)

		if not (text or model or gui):
			raise ValueError("text, model, and gui must all be specified.")

		self.text = text
		self.model = model
		self.gui = gui

		self.setToolTip("Click on an empty space to select this automation.")

		self.label = QtWidgets.QLabel(text)
		self.rename_button = QtWidgets.QPushButton("Rename")
		self.rename_button.setToolTip("Rename this automation")
		self.delete_button = QtWidgets.QPushButton("Delete")
		self.delete_button.setToolTip("Delete this automation")

		self.widget_layout = QtWidgets.QHBoxLayout(self)
		self.widget_layout.addWidget(self.label)
		self.widget_layout.addItem(QtWidgets.QSpacerItem(10, 1, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding))
		self.widget_layout.addWidget(self.rename_button)
		self.widget_layout.addWidget(self.delete_button)

		self.widget_layout.setContentsMargins(0, 0, 0, 0)

		self.delete_button.clicked.connect(self.delete)
		self.rename_button.clicked.connect(self.rename)
		self.mousePressEvent = self.select_self

	def select_self(self, event=None):
		global selected_automation, selected_automation_name, inputs
		selected_automation = json.load(open(f"data/automations/{self.text}.json", "r"))
		selected_automation_name = self.text

		inputs_to_remove = []
		for input in inputs:
			inputs_to_remove.append(input)
		for input in inputs_to_remove:
			input.delete()

		for input in selected_automation["inputs"]:
			self.gui.create_input(len(inputs), input)

		self.gui.currentautomation.setEnabled(True)
		self.gui.tab.setCurrentWidget(self.gui.currentautomation)

		self.gui.loop.setEnabled(True)
		self.gui.loopcheckbox.setEnabled(True)

		if selected_automation["loop"]:
			self.gui.loopdelay.setEnabled(True)
			self.gui.loopdelayinput.setEnabled(True)
			self.gui.loopiterations.setEnabled(True)
			self.gui.loopiterationsinput.setEnabled(True)
			self.gui.loopspeed.setEnabled(True)
			self.gui.loopspeedinput.setEnabled(True)

		self.gui.loopcheckbox.setChecked(selected_automation["loop"])
		self.gui.loopdelayinput.setValue(selected_automation["loopDelay"])
		self.gui.loopiterationsinput.setValue(selected_automation["loopIterations"])
		self.gui.loopspeedinput.setValue(selected_automation["loopSpeed"])

		self.gui.update_spin_boxes()

	def delete(self):
		index = automations.index(self)
		msg_box = QtWidgets.QMessageBox(self.gui.main_window)
		msg_box.setWindowTitle("Confirm Delete")
		msg_box.setText("Are you sure you want to delete this automation? Your actions can't be undone.")

		msg_box.addButton("Cancel", 0)
		msg_box.addButton("Delete", 1)

		result = msg_box.exec()

		if result == 1:  # delete
			os.remove(f"data/automations/{self.text}.json")
			self.model.removeRow(index)
			del automations[index]
			self.gui.automationnum.setText(f"You have {len(automations)} saved automations.")


	def rename(self):
		dialog = QtWidgets.QDialog(self.gui.main_window)
		dialog.setWindowFlags(dialog.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)
		dialog.setWindowTitle("Rename Automation")
		

		label1 = QtWidgets.QLabel("Rename this automation to")
		line_edit = QtWidgets.QLineEdit()

		vertical = QtWidgets.QVBoxLayout(dialog)
		horizontal = QtWidgets.QHBoxLayout()
		horizontal.addWidget(label1, alignment=QtCore.Qt.AlignRight)
		horizontal.addWidget(line_edit)

		ok = QtWidgets.QPushButton("OK")
		vertical.addLayout(horizontal)
		vertical.addWidget(ok)

		def re():
			new_name = line_edit.text()
			os.rename(f"data/automations/{self.text}.json", f"data/automations/{new_name}.json")
			self.text = new_name
			self.label.setText(self.text)
			dialog.close()
		
		ok.clicked.connect(re)

		dialog.exec()

class InputSender:
	def __init__(self, gui):
		self.gui = gui
		self._running = False

		self.iterations = 0
		self.loops = self.gui.loopiterationsinput.value()

	def run(self):
		while True:
			if not self._running or not (self.loops == 0 or self.iterations < self.loops):
				self.gui.is_playing = False
				self.gui.startstopbutton.setText(f"Start [{settings['startStopAutomationKey']}]")
				time.sleep(0.1)
				continue

			for input in inputs:
				if not self._running:
					break
				input.execute()
				
			self.iterations += 1
			time.sleep(max(self.gui.loopdelayinput.value(), 0.005))

	def play(self):
		self._running = True

		self.iterations = 0
		self.loops = self.gui.loopiterationsinput.value()

		self.gui.is_playing = True
		self.gui.startstopbutton.setText(f"Stop [{settings['startStopAutomationKey']}]")

	def stop(self):
		self._running = False

		self.gui.is_playing = False
		self.gui.startstopbutton.setText(f"Start [{settings['startStopAutomationKey']}]")

class Window(Ui_MainWindow):
	class CreateInputSignal(QtCore.QObject):
		trigger = QtCore.pyqtSignal(str)

		def __init__(self, window):
			super().__init__()
			self.window = window
			self._connect_trigger()
		
		def _connect_trigger(self):
			self.trigger.connect(self.handle_trigger)

		def emit_trigger(self, text):
			self.trigger.emit(text)
		
		def handle_trigger(self, text):
			self.window.create_input(len(inputs), text)

	def setup_ui(self, main_window):
		super().setupUi(main_window)

		self.main_window = main_window
		if settings["windowStaysOnTop"]:
			self.main_window.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)  # so window always stays on top unless minimised

		self.main_window.closeEvent = self.closeEvent

		self.input_model = QtGui.QStandardItemModel()
		self.inputlist.setModel(self.input_model)

		scroll_bar = QtWidgets.QScrollBar(self.main_window)
		self.inputlist.setVerticalScrollBar(scroll_bar)

		self.deleteinputs.clicked.connect(self.delete_inputs)
		self.selectall.clicked.connect(self.select_all)

		self.mousemovebutton.clicked.connect(self.add_mouse_move_input)
		self.mouseclickbutton.clicked.connect(self.add_mouse_click_input)
		self.mousepressbutton.clicked.connect(self.add_mouse_press_input)
		self.mousereleasebutton.clicked.connect(self.add_mouse_release_input)

		self.keypressbutton.clicked.connect(self.add_key_press_input)
		self.keyreleasebutton.clicked.connect(self.add_key_release_input)
		self.keystrokebutton.clicked.connect(self.add_keystroke_input)

		self.pause.clicked.connect(self.add_pause)

		self.startstopbutton.setText(f"Start [{settings['startStopAutomationKey']}]")
		self.startstopbutton.clicked.connect(self.start_stop_automation)

		self.picking_pos = False
		self.is_playing = False

		self.automation_model = QtGui.QStandardItemModel()
		self.automationlist.setModel(self.automation_model)
		for file in os.listdir("data/automations"):
			if file.endswith(".json"):
				item = QtGui.QStandardItem()
				self.automation_model.appendRow(item)
				list_item = AutomationListViewItem(text=file[:-5], model=self.automation_model, gui=self)
				automations.append(list_item)
				self.automationlist.setIndexWidget(item.index(), list_item)

		self.automationnum.setText(f"You have {len(automations)} saved automations.")
		self.createautomation.clicked.connect(self.create_new_automation)
		self.startstopinput.mousePressEvent = self.change_start_stop_keybind
		self.stoprecordinginput.mousePressEvent = self.change_stop_recording_keybind
		self.windowstaysontopinput.setChecked(settings["windowStaysOnTop"])
		self.windowstaysontopinput.stateChanged.connect(self.change_window_stays_on_top)
		self.loopcheckbox.clicked.connect(self.enable_disable_loop_settings)
		self.recordbutton.clicked.connect(self.record)

		# load settings
		self.startstopinput.setText(settings["startStopAutomationKey"])
		self.stoprecordinginput.setText(settings["stopRecordingKey"])
		self.recorddelayinput.setValue(settings["recordDelay"])

		self.create_input_signal = self.CreateInputSignal(self)

		self.input_sender = InputSender(self)
		self.input_thread = Thread(target=self.input_sender.run, daemon=True)
		self.input_thread.start()

	def record(self):
		dialog = QtWidgets.QDialog(self.main_window)
		dialog.setWindowFlags(dialog.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)
		dialog.setWindowTitle("Record Inputs")
	
		pause_checkbox = QtWidgets.QCheckBox("Record Pauses")
		key_checkbox = QtWidgets.QCheckBox("Record Key Input")
		mouse_checkbox = QtWidgets.QCheckBox("Record Mouse Input")

		pause_checkbox.setChecked(True)
		key_checkbox.setChecked(True)
		mouse_checkbox.setChecked(True)

		horiz_layout = QtWidgets.QHBoxLayout()
		horiz_layout.addWidget(pause_checkbox)
		horiz_layout.addWidget(key_checkbox)
		horiz_layout.addWidget(mouse_checkbox)

		start_button = QtWidgets.QPushButton("Start Recording")

		vert_layout = QtWidgets.QVBoxLayout(dialog)
		vert_layout.addLayout(horiz_layout)
		vert_layout.addWidget(start_button)

		time_to_start = self.recorddelayinput.value()
		label = QtWidgets.QLabel(f"Your recording will start in {time_to_start} seconds")
		label.setVisible(False)
		vert_layout.addWidget(label)

		def start():
			nonlocal label
			pause_checkbox.setEnabled(False)
			key_checkbox.setEnabled(False)
			mouse_checkbox.setEnabled(False)
			start_button.setEnabled(False)

			label.setVisible(True)
			def run():
				nonlocal time_to_start
				stop = False
				last_action_time = time.time_ns() / 1e+9  # get sec time with decimal

				while time_to_start > 0:
					time.sleep(1)
					time_to_start -= 1
					label.setText(f"Your recording will start in {time_to_start} seconds")

				if key_checkbox.isChecked():
					def record_key(event):
						nonlocal last_action_time, stop
						t = event.event_type
						if t == keyboard.KEY_DOWN:
							if event.name == self.stoprecordinginput.text():
								stop = True
								keyboard.unhook(keyboard_hook)
								dialog.close()
								return

							if key_is_held(event.name):
								return

							if pause_checkbox.isChecked():
								pause_length = event.time - last_action_time
								last_action_time = event.time
								self.create_input_signal.emit_trigger(f"Pause - {round(pause_length, 2)}")

							self.create_input_signal.emit_trigger(f"Key Press - {event.name}")
						else:
							if pause_checkbox.isChecked():
								pause_length = event.time - last_action_time
								last_action_time = event.time
								self.create_input_signal.emit_trigger(f"Pause - {round(pause_length, 2)}")

							self.create_input_signal.emit_trigger(f"Key Release - {event.name}")
						
					keyboard_hook = keyboard.hook(record_key)

				if mouse_checkbox.isChecked():
					last_mouse_move_time = time.time_ns() / 1e+9  # get sec time with decimal

					def record_mouse(event):
						nonlocal last_action_time, stop, last_mouse_move_time
						if stop:
							mouse.unhook(mouse_hook)
							return
							
						if isinstance(event, mouse.ButtonEvent):
							if event.event_type == "down":
								if pause_checkbox.isChecked():
									pause_length = event.time - last_action_time
									last_action_time = event.time
									self.create_input_signal.emit_trigger(f"Pause - {round(pause_length, 2)}")

								self.create_input_signal.emit_trigger(f"Mouse Press - {capitalise(event.button)}")
							elif event.event_type == "up":

								if pause_checkbox.isChecked():
									pause_length = event.time - last_action_time
									last_action_time = event.time
									self.create_input_signal.emit_trigger(f"Pause - {round(pause_length, 2)}")

								self.create_input_signal.emit_trigger(f"Mouse Release - {capitalise(event.button)}")
						elif isinstance(event, mouse.MoveEvent):
							if last_mouse_move_time + 0.1 > event.time:
								return

							self.create_input_signal.emit_trigger(f"Mouse Move - ({event.x}, {event.y})")

							if pause_checkbox.isChecked() and last_mouse_move_time + 0.15 < event.time:
								pause_length = event.time - last_action_time
								last_action_time = event.time
								self.create_input_signal.emit_trigger(f"Pause - {round(pause_length, 2)}")

							last_mouse_move_time = event.time

					mouse_hook = mouse.hook(record_mouse)

				label.setText(f"Your recording has started. Press {settings['stopRecordingKey']} to stop recording.")
			
			thread = Thread(target=run, daemon=True)
			thread.start()
			

		start_button.clicked.connect(start)

		dialog.exec()

	def change_window_stays_on_top(self):
		if self.windowstaysontopinput.isChecked():
			self.main_window.setWindowFlags(self.main_window.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
		else:
			self.main_window.setWindowFlags(self.main_window.windowFlags() & ~QtCore.Qt.WindowStaysOnTopHint)

		self.main_window.show()

	def change_start_stop_keybind(self, event=None):

		dialog = QtWidgets.QDialog(self.main_window)
		dialog.setWindowFlags(dialog.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)
		dialog.setWindowTitle("Change Start/Stop Automation Keybind")
		

		label1 = QtWidgets.QLabel("Change the keybind to start/stop automations to")
		line_edit = QtWidgets.QLineEdit()
		line_edit.setReadOnly(True)

		vertical = QtWidgets.QVBoxLayout(dialog)
		horizontal = QtWidgets.QHBoxLayout()
		horizontal.addWidget(label1, alignment=QtCore.Qt.AlignRight)
		horizontal.addWidget(line_edit)

		ok = QtWidgets.QPushButton("OK")
		vertical.addLayout(horizontal)
		vertical.addWidget(ok)

		def set_key(event):
			line_edit.setText(event.name)

		hook = keyboard.on_press(set_key)

		def change_keybind():
			text = line_edit.text()

			keyboard.unhook(hook)
			self.startstopinput.setText(text)
			if self.is_playing:
				self.startstopbutton.setText(f"Stop [{text}]")
			else:
				self.startstopbutton.setText(f"Start [{text}]")
				
			dialog.close()
		
		ok.clicked.connect(change_keybind)

		dialog.exec()

	def change_stop_recording_keybind(self, event=None):

		dialog = QtWidgets.QDialog(self.main_window)
		dialog.setWindowFlags(dialog.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)
		dialog.setWindowTitle("Change Stop Recording Keybind")
		

		label1 = QtWidgets.QLabel("Change the keybind to stop recording to")
		line_edit = QtWidgets.QLineEdit()
		line_edit.setReadOnly(True)

		vertical = QtWidgets.QVBoxLayout(dialog)
		horizontal = QtWidgets.QHBoxLayout()
		horizontal.addWidget(label1, alignment=QtCore.Qt.AlignRight)
		horizontal.addWidget(line_edit)

		ok = QtWidgets.QPushButton("OK")
		vertical.addLayout(horizontal)
		vertical.addWidget(ok)

		def set_key(event):
			line_edit.setText(event.name)

		hook = keyboard.on_press(set_key)

		def change_keybind():
			text = line_edit.text()

			keyboard.unhook(hook)
			self.stoprecordinginput.setText(text)
				
			dialog.close()
		
		ok.clicked.connect(change_keybind)

		dialog.exec()

	def create_new_automation(self):
		dialog = QtWidgets.QDialog(self.main_window)
		dialog.setWindowFlags(dialog.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)
		dialog.setWindowTitle("Create Automation")
		

		label1 = QtWidgets.QLabel("Create an automation with the name")
		line_edit = QtWidgets.QLineEdit()

		vertical = QtWidgets.QVBoxLayout(dialog)
		horizontal = QtWidgets.QHBoxLayout()
		horizontal.addWidget(label1, alignment=QtCore.Qt.AlignRight)
		horizontal.addWidget(line_edit)

		ok = QtWidgets.QPushButton("OK")
		vertical.addLayout(horizontal)
		vertical.addWidget(ok)

		def new():
			name = line_edit.text()

			try:
				if not os.path.exists(f"data/automations/{name}.json") and name != "":
					with open(f"data/automations/{name}.json", "w") as file:  # create a json file for the automation
						json.dump({"inputs": [], "loop": True, "loopIterations": 0, "loopDelay": 0.1, "loopSpeed": 1}, file)
				else:
					raise FileExistsError("An automation with that name already exists.")
			except (FileExistsError, OSError) as e:
				dialog.close()
				msg_box = QtWidgets.QMessageBox(self.main_window)
				msg_box.setWindowFlags(msg_box.windowFlags() & ~QtCore.Qt.WindowStaysOnTopHint)
				msg_box.setWindowTitle("Error")
				msg_box.setText("Make sure your OS allows you to create files with that name and that the name is not empty.")
				msg_box.setInformativeText(str(e))
				msg_box.setIcon(QtWidgets.QMessageBox.Critical)
				msg_box.exec()
				return

			item = QtGui.QStandardItem()
			self.automation_model.appendRow(item)
			list_item = AutomationListViewItem(text=name, model=self.automation_model, gui=self)
			automations.append(list_item)
			self.automationlist.setIndexWidget(item.index(), list_item)
			self.automationnum.setText(f"You have {len(automations)} saved automations.")

			dialog.close()
		
		ok.clicked.connect(new)

		dialog.exec()

	def start_stop_automation(self, event=None):
		if not self.is_playing:
			self.input_sender.play()
		else:
			self.input_sender.stop()

	def add_pause(self, edit=None):
		dialog = QtWidgets.QDialog(self.main_window)
		dialog.setWindowFlags(dialog.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)

		if not edit:
			dialog.setWindowTitle("Add Pause")
		else:
			dialog.setWindowTitle("Edit to Pause")
		
		label1 = QtWidgets.QLabel("Pause for")
		label2 = QtWidgets.QLabel("seconds")
		spinbox = QtWidgets.QDoubleSpinBox()
		spinbox.setRange(0, 1000000)
		spinbox.setSingleStep(0.1)
		spinbox.setValue(1)
		spinbox.setDecimals(2)
		ok_button = QtWidgets.QPushButton("OK")

		vertical_layout = QtWidgets.QVBoxLayout(dialog)
		horizontal_layout = QtWidgets.QHBoxLayout()
		horizontal_layout.addWidget(label1)
		horizontal_layout.addWidget(spinbox)
		horizontal_layout.addWidget(label2)
		vertical_layout.addLayout(horizontal_layout)
		vertical_layout.addWidget(ok_button)

		def add_input():
			if not edit:
				self.create_input(len(inputs), f"Pause - {round(spinbox.value(), 2)}")
			else:
				edit.update(edit.item_id, f"Pause - {round(spinbox.value(), 2)}")
			dialog.close()

		ok_button.clicked.connect(add_input)
		
		dialog.exec()

	def add_keystroke_input(self, edit=None):
		dialog = QtWidgets.QDialog(self.main_window)
		dialog.setWindowFlags(dialog.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)

		if not edit:
			dialog.setWindowTitle("Add Keystroke")
		else:
			dialog.setWindowTitle("Edit to Keystroke")

		label1 = QtWidgets.QLabel("Press and release the")
		line_edit = QtWidgets.QLineEdit()
		line_edit.setReadOnly(True)
		label2 = QtWidgets.QLabel("key")

		vertical = QtWidgets.QVBoxLayout(dialog)
		horizontal = QtWidgets.QHBoxLayout()
		horizontal.addWidget(label1, alignment=QtCore.Qt.AlignRight)
		horizontal.addWidget(line_edit)
		horizontal.addWidget(label2)

		ok = QtWidgets.QPushButton("OK")
		vertical.addLayout(horizontal)
		vertical.addWidget(ok)

		def set_key(event):
			line_edit.setText(event.name)

		hook = keyboard.on_press(set_key)

		def add_input():
			text = line_edit.text()
			if not text:
				msg_box = QtWidgets.QMessageBox(self.main_window)
				msg_box.setWindowTitle("No key selected")
				msg_box.setText("Select a key by pressing it.")
				msg_box.show()
				return

			if not edit:
				self.create_input(len(inputs), f"Keystroke - {text}")
			else:
				edit.update(edit.item_id, f"Keystroke - {text}")

			keyboard.unhook(hook)
			dialog.close()

		ok.clicked.connect(add_input)
		dialog.exec()

	def add_key_release_input(self, edit=False):
		dialog = QtWidgets.QDialog(self.main_window)
		dialog.setWindowFlags(dialog.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)
		
		if not edit:
			dialog.setWindowTitle("Add Key Release")
		else:
			dialog.setWindowTitle("Edit to Key Release")
		

		label1 = QtWidgets.QLabel("Release the")
		line_edit = QtWidgets.QLineEdit()
		line_edit.setReadOnly(True)
		label2 = QtWidgets.QLabel("key")

		vertical = QtWidgets.QVBoxLayout(dialog)
		horizontal = QtWidgets.QHBoxLayout()
		horizontal.addWidget(label1, alignment=QtCore.Qt.AlignRight)
		horizontal.addWidget(line_edit)
		horizontal.addWidget(label2)

		ok = QtWidgets.QPushButton("OK")
		vertical.addLayout(horizontal)
		vertical.addWidget(ok)

		def set_key(event):
			line_edit.setText(event.name)

		hook = keyboard.on_press(set_key)

		def add_input():
			text = line_edit.text()
			if not text:
				msg_box = QtWidgets.QMessageBox(self.main_window)
				msg_box.setWindowTitle("No key selected")
				msg_box.setText("Select a key by pressing it.")
				msg_box.show()
				return

			if not edit:
				self.create_input(len(inputs), f"Key Release - {text}")
			else:
				edit.update(edit.item_id, f"Key Release - {text}")
			keyboard.unhook(hook)
			dialog.close()

		ok.clicked.connect(add_input)
		dialog.exec()

	def add_key_press_input(self, edit=None):
		dialog = QtWidgets.QDialog(self.main_window)
		dialog.setWindowFlags(dialog.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)

		if not edit:	
			dialog.setWindowTitle("Add Key Press")
		else:
			dialog.setWindowTitle("Edit to Key Press")

		label1 = QtWidgets.QLabel("Press the")
		line_edit = QtWidgets.QLineEdit()
		line_edit.setReadOnly(True)
		label2 = QtWidgets.QLabel("key")

		vertical = QtWidgets.QVBoxLayout(dialog)
		horizontal = QtWidgets.QHBoxLayout()
		horizontal.addWidget(label1, alignment=QtCore.Qt.AlignRight)
		horizontal.addWidget(line_edit)
		horizontal.addWidget(label2)

		ok = QtWidgets.QPushButton("OK")
		vertical.addLayout(horizontal)
		vertical.addWidget(ok)

		def set_key(event):
			line_edit.setText(event.name)

		hook = keyboard.on_press(set_key)

		def add_input():
			text = line_edit.text()
			if not text:
				msg_box = QtWidgets.QMessageBox(self.main_window)
				msg_box.setWindowTitle("No key selected")
				msg_box.setText("Select a key by pressing it.")
				msg_box.show()
				return

			if not edit:
				self.create_input(len(inputs), f"Key Press - {text}")
			else:
				edit.update(edit.item_id, f"Key Press - {text}")

			keyboard.unhook(hook)
			dialog.close()

		ok.clicked.connect(add_input)
		dialog.exec()

	def add_mouse_release_input(self, edit=None):
		dialog = QtWidgets.QDialog(self.main_window)
		dialog.setWindowFlags(dialog.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)
		
		if not edit:
			dialog.setWindowTitle("Add Mouse Release")
		else:
			dialog.setWindowTitle("Edit to Mouse Release")

		label1 = QtWidgets.QLabel("Release the")
		select = QtWidgets.QComboBox()
		select.addItem("Left")
		select.addItem("Right")
		select.addItem("Middle")
		label2 = QtWidgets.QLabel("button")

		vertical = QtWidgets.QVBoxLayout(dialog)
		horizontal = QtWidgets.QHBoxLayout()
		horizontal.addWidget(label1, alignment=QtCore.Qt.AlignRight)
		horizontal.addWidget(select)
		horizontal.addWidget(label2)

		ok = QtWidgets.QPushButton("OK")
		vertical.addLayout(horizontal)
		vertical.addWidget(ok)

		def add_input():
			if not edit:
				self.create_input(len(inputs), f"Mouse Release - {select.currentText()}")
			else:
				edit.update(edit.item_id, f"Mouse Release - {select.currentText()}")
			dialog.close()

		ok.clicked.connect(add_input)
		dialog.exec()

	def add_mouse_press_input(self, edit=None):
		dialog = QtWidgets.QDialog(self.main_window)
		dialog.setWindowFlags(dialog.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)
		
		if not edit:
			dialog.setWindowTitle("Add Mouse Press")
		else:
			dialog.setWindowTitle("Edit to Mouse Press")

		label1 = QtWidgets.QLabel("Press the")
		select = QtWidgets.QComboBox()
		select.addItem("Left")
		select.addItem("Right")
		select.addItem("Middle")
		label2 = QtWidgets.QLabel("button")

		vertical = QtWidgets.QVBoxLayout(dialog)
		horizontal = QtWidgets.QHBoxLayout()
		horizontal.addWidget(label1, alignment=QtCore.Qt.AlignRight)
		horizontal.addWidget(select)
		horizontal.addWidget(label2)

		ok = QtWidgets.QPushButton("OK")
		vertical.addLayout(horizontal)
		vertical.addWidget(ok)

		def add_input():
			if not edit:
				self.create_input(len(inputs), f"Mouse Press - {select.currentText()}")
			else:
				edit.update(edit.item_id, f"Mouse Press - {select.currentText()}")
			dialog.close()

		ok.clicked.connect(add_input)
		dialog.exec()

	def add_mouse_click_input(self, edit=None):
		dialog = QtWidgets.QDialog(self.main_window)
		dialog.setWindowFlags(dialog.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)

		if not edit:
			dialog.setWindowTitle("Add Mouse Click")
		else:
			dialog.setWindowTitle("Edit to Mouse Click")

		label1 = QtWidgets.QLabel("Do a")
		select = QtWidgets.QComboBox()
		select.addItem("Left")
		select.addItem("Right")
		select.addItem("Middle")
		select.addItem("Double Left")
		label2 = QtWidgets.QLabel("click")

		vertical = QtWidgets.QVBoxLayout(dialog)
		horizontal = QtWidgets.QHBoxLayout()
		horizontal.addWidget(label1, alignment=QtCore.Qt.AlignRight)
		horizontal.addWidget(select)
		horizontal.addWidget(label2)

		ok = QtWidgets.QPushButton("OK")
		vertical.addLayout(horizontal)
		vertical.addWidget(ok)

		def add_input():
			if not edit:
				self.create_input(len(inputs), f"Mouse Click - {select.currentText()}")
			else:
				edit.update(edit.item_id, f"Mouse Click - {select.currentText()}")
			dialog.close()

		ok.clicked.connect(add_input)
		dialog.exec()

	def add_mouse_move_input(self, edit=None):
		dialog = QtWidgets.QDialog(self.main_window)
		dialog.setWindowFlags(dialog.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)

		if not edit:
			dialog.setWindowTitle("Add Mouse Move")
		else:
			dialog.setWindowTitle("Edit to Mouse Move")

		label1 = QtWidgets.QLabel("Move my mouse at X:")
		x_input = QtWidgets.QSpinBox()
		x_input.setMaximum(9999)
		label2 = QtWidgets.QLabel(", Y:")
		y_input = QtWidgets.QSpinBox()
		y_input.setMaximum(9999)

		vertical = QtWidgets.QVBoxLayout(dialog)
		horizontal = QtWidgets.QHBoxLayout()
		horizontal.addWidget(label1)
		horizontal.addWidget(x_input)
		horizontal.addWidget(label2)
		horizontal.addWidget(y_input)

		ok = QtWidgets.QPushButton("OK")
		pick_pos = QtWidgets.QPushButton("Pick Location")
		pick_pos.setToolTip("Press any key to select the current location")
		vertical.addLayout(horizontal)
		vertical.addWidget(pick_pos)
		vertical.addWidget(ok)

		def add_input():
			if not edit:
				self.create_input(len(inputs), f"Mouse Move - ({x_input.value()}, {y_input.value()})")
			else:
				edit.update(edit.item_id, f"Mouse Move - ({x_input.value()}, {y_input.value()})")

			dialog.close()

		ok.clicked.connect(add_input)

		def pick_location():
			def upd():
				self.picking_pos = True
				while self.picking_pos:
					pos = get_cursor_pos()
					x_input.setValue(pos[0])
					y_input.setValue(pos[1])
					time.sleep(0.1)
			t = Thread(target=upd, daemon=True)
			t.start()

			def stop(event):
				self.picking_pos = False
				keyboard.unhook(hook)

			hook = keyboard.hook(stop)  # wait for any key to be pressed

		pick_pos.clicked.connect(pick_location)

		dialog.exec()

	def create_input(self, id, text):
		item = QtGui.QStandardItem()
		self.input_model.appendRow(item)
		list_item = InputListViewItem(text=f"{text}", item_id=id, model=self.input_model, gui=self)
		inputs.append(list_item)
		self.inputlist.setIndexWidget(item.index(), list_item)

		self.startnum.setMaximum(len(inputs) - 1)
		self.endnum.setMaximum(len(inputs))

	def select_all(self):
		checked = self.selectall.isChecked()
	
		for input in inputs:
			input.checkbox.setChecked(checked)

	def update_spin_boxes(self):
		ins = len(inputs)

		if ins > 0:
			self.startnum.setMinimum(1)
			self.endnum.setMinimum(1)
		else:
			self.startnum.setMinimum(0)
			self.endnum.setMinimum(0)

		self.startnum.setMaximum(max(ins, self.startnum.minimum()))
		self.endnum.setMaximum(max(ins, self.endnum.minimum()))

	def delete_inputs(self):
		if len(inputs) == 0:
			return False

		# get checked checkboxes
		checked = []
		for i in range(len(inputs)):
			input = inputs[i]
			checkbox = input.checkbox
			if checkbox.isChecked():
				checked.append(i)

		if len(checked) == 0:  # delete inputs between start-end
			start = self.startnum.value() - 1
			end = self.endnum.value()  # don't remove 1 because the end value of splice is excluded
			for input in inputs[start:end]:
				input.delete()
		else:
			inputs_to_remove = []
			for i in checked:
				inputs_to_remove.append(inputs[i])
				
			for input in inputs_to_remove:
				input.delete()

		return True
				
	def closeEvent(self, event):
		# check if there are any unsaved changes, if there aren't any just quit
		if  settings["windowStaysOnTop"] == self.windowstaysontopinput.isChecked() and \
			settings["startStopAutomationKey"] == self.startstopinput.text() and \
			settings["stopRecordingKey"] == self.stoprecordinginput.text() and \
			settings["recordDelay"] == self.recorddelayinput.value():
			if selected_automation != {}:
				update_inputs_text()
				if  selected_automation["inputs"] == inputs_text and \
					selected_automation["loopIterations"] == self.loopiterationsinput.value() and \
					selected_automation["loopDelay"] == self.loopdelayinput.value() and \
					selected_automation["loopSpeed"] == self.loopspeedinput.value():
					event.accept()
					quit()
			else:
				event.accept()
				quit()

		msg_box = QtWidgets.QMessageBox(self.main_window)
		msg_box.setWindowTitle("Discard changes?")
		msg_box.setText("You have unsaved changes. If you quit without saving, you will lose them.")

		msg_box.addButton("Save and exit", 0)
		msg_box.addButton("Cancel", 2)
		msg_box.addButton("Exit without saving", 3)

		result = msg_box.exec()

		if result == 0:  # save and exit
			self.save()
			event.accept()

		elif result == 1:  # cancel
			event.ignore()

		elif result == 2:  # exit without saving
			event.accept()
 
	def save(self):
		settings_json = {
			"windowStaysOnTop": self.windowstaysontopinput.isChecked(),
			"startStopAutomationKey": self.startstopinput.text(),
			"stopRecordingKey": self.stoprecordinginput.text(),
			"recordDelay": self.recorddelayinput.value(),
			}

		json.dump(settings_json, open("data/settings.json", "w"))

		if selected_automation_name == "":
			return False

		automation_json = {"inputs": []}

		for inp in inputs:
			automation_json["inputs"].append(inp.text)
		
		automation_json["loop"] = self.loopcheckbox.isChecked()
		automation_json["loopIterations"] = self.loopiterationsinput.value()
		automation_json["loopDelay"] = self.loopdelayinput.value()
		automation_json["loopSpeed"] = self.loopspeedinput.value()

		json.dump(automation_json, open(f"data/automations/{selected_automation_name}.json", "w"))
		
	def enable_disable_loop_settings(self):
		c = self.loopcheckbox.isChecked()

		self.loopiterations.setEnabled(c)
		self.loopiterationsinput.setEnabled(c)
		self.loopdelay.setEnabled(c)
		self.loopdelayinput.setEnabled(c)
		self.loopspeed.setEnabled(c)
		self.loopspeedinput.setEnabled(c)


if __name__ == "__main__":
	app = QtWidgets.QApplication(sys.argv)
	
	main_window = QtWidgets.QMainWindow()
	window = Window()
	window.setup_ui(main_window)

	keyboard.on_press_key(settings["startStopAutomationKey"], window.start_stop_automation)
	keyboard.add_hotkey("ctrl+s", window.save)

	main_window.show()
	exec = app.exec()

	sys.exit(exec)