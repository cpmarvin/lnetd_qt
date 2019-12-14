# for argv
import sys
import json
# math
from math import sqrt, cos, sin, radians, pi
from random import random, randint

# parsing
import ast

# PyQt5

from PyQt5.QtCore import Qt, QSize, QTimer, QPointF, QRectF, QMetaObject, QRect , QCoreApplication, QPoint, QLineF ,pyqtSlot
from PyQt5.QtGui import QPainter, QBrush, QPen, QFont, QIcon, QTransform, QPalette, QColor
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QFrame,
    QCheckBox,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QFileDialog,
    QSizePolicy,
    QMenu,
    QSlider,
    QDialog,
    QComboBox,
    QLabel,
    QSpacerItem,
    QMainWindow,
    QMenuBar,
    QOpenGLWidget
)

# graph stuff
from objects.graph import Graph
from objects.node import Node

# utilities stuff
from utilities import *

from l1_model import L1Model
#qt creator ui's
#from add_link import Ui_Form

from dialogs.ui_link_info import Ui_link_info
from dialogs.network_info import Ui_NetworkInfoForm
from dialogs.edit_label import Ui_EditLabel
from dialogs.change_name import Ui_ChangeName
from dialogs.add_link import Ui_AddLink


import OpenGL.GL as gl

class TreeVisualizer(QWidget):

    @pyqtSlot()
    def on_button_clicked(self):
        print('clicked')

    def __init__(self, CenterPanel):
        """Initial configuration."""
        super().__init__()

        # GLOBAL VARIABLES
        #self.CenterPanel = CenterPanel
        self.graph: Graph = Graph(directed=True,weighted=True)
        self.selected_node: Node = None

        self.vertex_positions: List[Tuple[Vector, Tuple[Node, Node]]] = []
        self.selected_vertex: Tuple[Node, Node] = None

        # offset of the mouse from the position of the currently dragged node
        self.mouse_drag_offset: Vector = None

        # position of the mouse; is updated when the mouse moves
        self.mouse_position: Vector = Vector(-1, -1)

        # variables for visualizing the graph
        self.node_radius: float = 15 #20
        self.weight_rectangle_size: float = 15 #self.node_radius / 3

        self.arrowhead_size: float = 2
        self.arrow_separation: float = pi / 7

        self.selected_color = Qt.gray
        self.regular_node_color = Qt.white
        self.regular_vertex_weight_color = Qt.black

        # limit the displayed length of labels for each node
        self.node_label_limit: int = 10

        # UI variables
        self.font_family: str = "Times New Roman"
        self.font_size: int = 18

        self.layout_margins: float = 8
        self.layout_item_spacing: float = 2 * self.layout_margins

        # canvas positioning (scale and translation)
        self.scale: float = 1
        self.scale_coefficient: float = 2  # by how much the scale changes on scroll
        self.translation: float = Vector(0, 0)

        # by how much the rotation of the nodes changes
        self.node_rotation_coefficient: float = 0.7

        # TIMERS
        # timer that runs the simulation (60 times a second... once every ~= 16ms)
        #16 too high for paint, move to 60 for now
        #TODO fix the math in self.update() -> paint
        self.simulation_timer = QTimer(
            interval=16, timeout=self.perform_simulation_iteration
        )

        # WIDGETS
        self.canvas = QFrame(self, minimumSize=QSize(0, 300))
        self.canvas_size: Vector = None
        self.canvas.resizeEvent = self.adjust_canvas_translation

        # WIDGET LAYOUT

        self.main_v_layout = QVBoxLayout(self, margin=0)
        #self.canvas.setStyleSheet("background-color:transparent;");
        self.main_v_layout.addWidget(self.canvas)
        self.setLayout(self.main_v_layout)

        # WINDOW SETTINGS
        '''
        self.setWindowTitle("LnetD")
        self.setFont(QFont(self.font_family, self.font_size))
        self.setWindowIcon(QIcon("icon.ico"))
        '''
        self.show()

        # start the simulation
        self.simulation_timer.start()

    def update_demand_value(self,valueOfSlider):
        """Method to update the demand input value
        with the value of slider"""
        text = str(valueOfSlider)
        self.input_line_demand.setText(text)

    def set_weighted_graph(self):
        """TO BE REMOVED"""
        pass
        """Is called when the weighted checkbox is pressed; sets, whether the graph is
        weighted or not."""
        #self.graph.set_weighted(self.weighted_checkbox.isChecked())

    def adjust_canvas_translation(self, event):
        """Is called when the canvas widget is resized; changes translation so the
        center stays in the center."""
        size = Vector(event.size().width(), event.size().height())

        if self.canvas_size is not None:
            self.translation += self.scale * (size - self.canvas_size) / 2

        self.canvas_size = size

    def repulsion_force(self, distance: float) -> float:
        """Calculates the strength of the repulsion force at the specified distance."""
        return 1 / distance * 10 #if self.forces_checkbox.isChecked() else 0

    def attraction_force(self, distance: float, leash_length=80) -> float:
        """Calculates the strength of the attraction force at the specified distance
        and leash length."""
        return (
            -(distance - leash_length) / 10 #if self.forces_checkbox.isChecked() else 0
        )

    def reset_all_demands(self):
        """Reset all graph demands, usefull for starting over
        without reloading the graph"""
        self.graph.remove_all_demands()


    def load_netflow_demands(self):
        path = QFileDialog.getOpenFileName()[0]
        if path != "":
            try:
                if len(self.graph.nodes) == 0:
                    raise Exception("Demands must be loaded after Network Topology")
                with open(path, "r") as file:
                    demands = json.load(file)
                    #print(demands)
                    for demand in demands:
                        source = demand['source']
                        target = demand['target']
                        demand_value = int(demand['demand'])
                        self.graph.add_demand(source=source,target=target,demand=demand_value)
                    self.demand_report()
                    #self.graph.redeploy_demands()
            except UnicodeDecodeError:
                QMessageBox.critical(self, "Error!", "Can't read binary files!")
            except ValueError:
                QMessageBox.critical(
                        self, "Error!", "The demand file cannot be imported!"
                    )
            except Exception as e:
                print('this is the error when importing netflow', e)
                QMessageBox.critical(
                        self,
                        "Error!",
                        str(e),
                    )

    def update_graph_spf(self, source: Node, target: Node):
        #TODO remove , not needed now
        pass

    def set_checkbox_values(self):
        """Sets the values of the checkboxes from the graph."""
        self.weighted_checkbox.setChecked(self.graph.is_weighted())
        #self.update_directed_toggle_button_text()

    def export_graph(self):
        """Is called when the export button is clicked; exports a graph to a file."""
        path = QFileDialog.getSaveFileName()[0]

        if path != "":
            try:
                with open(path, "w") as file:
                    #TODO redo this
                    graph = {}
                    graph['links'] = []
                    graph['nodes'] = self.graph.export_nodes()
                    # look at every pair of nodes and examine the vertices
                    for i, n1 in enumerate(self.graph.get_nodes()):
                        #print(n1.export_links())
                        graph['links'] += n1.export_links()
                    json.dump(graph, file, sort_keys=True, indent=4)
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error!",
                    "An error occurred when exporting the graph. Make sure that you "
                    "have permission to write to the specified file and try again!",
                )

    def show_help(self):
        """Is called when the help button is clicked; displays basic information about
        the application."""
        message = """
            <p><strong>LnetD QT5 Application</strong>.</p>
            <p>Traffic Model Example.
            It is powered by PyQt5 &ndash; a set of Python bindings for the C++ library Qt.</p>
            <hr />
            <p>The controls are as follows:</p>
            <ul>
            <li><em>Left Mouse Button</em> &ndash; selects nodes and moves them</li>
            <li><em>Mouse Wheel</em> &ndash; zooms in/out</li>
            <li><em>Select Node + Shift + Left Mouse Button</em> &ndash; moves graph</li>
            <li><em>Shift + Mouse Wheel</em> &ndash; rotates nodes around the selected node</li>
            <li><em>For traffic demands , add a source/target node and choose the demand value </em> &ndash; if you want additive demands , check the box</li>
            <li><em>Click on link metric</em> &ndash; will show link information</li>
            </ul>
            <hr />
            <p>Source Code and more information at
            <a href="https://github.com/cpmarvin/lnetd_qt">GitHub repository</a>.</p>
        """

        QMessageBox.information(self, "About", message)

    #@catch_exception
    def deploy_static_demand(self):
        """This is infact deploy demands"""
        #TODO change name and redo
        source_label = self.input_line_source.text()
        source_node = self.graph.get_node_based_on_label(source_label)
        target_label = self.input_line_target.text()
        target_node = self.graph.get_node_based_on_label(target_label)
        demand_value = self.input_line_demand.text()
        demand_unit_text = self.demand_unit_select.currentText()
        if demand_unit_text =='Mbps':
            demand_unit_multiplicate = 1
        elif demand_unit_text =='Gbps':
            demand_unit_multiplicate = 1000
        elif demand_unit_text =='Tbps':
            demand_unit_multiplicate = 1000000

        graph_nodes = self.graph.get_nodes_label()

        can_spf_be_ran = False
        if source_label in graph_nodes and target_label in graph_nodes and source_label != target_label and len(demand_value) > 0:
            can_spf_be_ran = True

        else:
            palette = self.input_line_source.palette()
            palette.setColor(self.input_line_source.backgroundRole(), Qt.red)
            self.input_line_source.setPalette(palette)
            palette = self.input_line_target.palette()
            palette.setColor(self.input_line_target.backgroundRole(), Qt.red)
            self.input_line_target.setPalette(palette)
            message = f"Source or Node not found in Graph , SPF will not run"
            QMessageBox.information(self, "Info", message)

        if can_spf_be_ran:
            palette = self.input_line_source.palette()
            palette.setColor(self.input_line_source.backgroundRole(), Qt.white)
            self.input_line_source.setPalette(palette)
            palette = self.input_line_target.palette()
            palette.setColor(self.input_line_target.backgroundRole(), Qt.white)
            self.input_line_target.setPalette(palette)
            if not self.additive_checkbox.isChecked():
                self.graph.remove_all_demands()
            #get new spf path
            demand = int(demand_value) * demand_unit_multiplicate
            self.graph.add_demand(source_label,target_label,demand)
            #self.graph.redeploy_demands()
            self.demand_report()


    def demand_report(self):
        pass
        '''
        self.graph.redeploy_demands()
        if self.labels_checkbox.isChecked():
            print(self.graph.get_unrouted_demands())
            if len(self.graph.get_unrouted_demands()) > 0:
                message = "there are demands that cannot be deployed in the current model"
                QMessageBox.information(self, "About", message)
                #get list of failed demands
                #Qmessage about them
        else:
            pass
        '''
    def network_info(self):
        self.network_info = QWidget()
        self.ui = Ui_NetworkInfoForm()
        self.ui.setupUi(self.network_info,self.graph)
        self.network_info.show()

    def l1_model(self):
        self.l1_model = L1Model(self.graph)
        self.l1_model.setWindowTitle("LnetD - L1 Model")

    def update_directed_toggle_button_text(self):
        #TODO remove
        """Changes the text of the directed toggle button, according to whether the
        graph is directer or not."""
        self.directed_toggle_button.setText(
            "directed" if self.graph.is_directed() else "undirected"
        )

    def input_line_edit_changed(self, text: str):
        """Is called when the input line edit changes; changes either the label of the
        node selected node, or the value of the selected vertex."""
        palette = self.input_line_edit.palette()
        text = text.strip()

        if self.selected_node is not None:
            pass
            '''
            # text is restricted for rendering and graph export purposes
            if 0 < len(text) < self.node_label_limit and " " not in text:
                self.selected_node.set_label(text)
                palette.setColor(self.input_line_edit.backgroundRole(), Qt.white)
            else:
                palette.setColor(self.input_line_edit.backgroundRole(), Qt.white)
                #palette.setColor(self.input_line_edit.backgroundRole(), Qt.red)
            '''
        elif self.selected_vertex is not None:
            # try to parse the input text either as an integer, or as a float
            weight = None
            try:
                weight = int(text)
                weight = text
            except ValueError:
                try:
                    weight = float(text)
                except ValueError:
                    pass

            # if the parsing was unsuccessful, set the input line edit background to
            # red to indicate this
            if weight is None:
                #pass
                palette.setColor(self.input_line_edit.backgroundRole(), Qt.red)
            else:
                palette.setColor(self.input_line_edit.backgroundRole(), Qt.white)

        self.input_line_edit.setPalette(palette)

    def select_node(self, node: Node):
        """Sets the selected node to the specified node, sets the input line edit to
        its label and enables it."""
        self.selected_node = node
        #self.CenterPanel.input_line_edit.setText(node.get_label())
        #self.CenterPanel.input_line_edit.setEnabled(True)
        #self.CenterPanel.input_line_edit.setFocus()

    def deselect_node(self):
        """Sets the selected node to None and disables the input line edit."""
        self.selected_node = None
        #self.CenterPanel.input_line_edit.setEnabled(False)

    def select_vertex(self, vertex):
        """Sets the selected vertex to the specified vertex, sets the input line edit to
        its weight and enables it."""
        self.selected_vertex = vertex

        #self.input_line_edit.setText(str(self.graph.get_weight(*vertex)))
        self.input_line_edit.setText(str(vertex[2]))
        self.input_line_edit.setEnabled(True)
        self.input_line_edit.setFocus()
        #bring up the link_info window
        self.link_info = QWidget()
        self.link_info.ui = Ui_link_info()
        self.link_info.ui.setupUi(self.link_info,vertex[3])
        self.link_info.show()


    def deselect_vertex(self):
        """Sets the selected vertex to None and disables the input line edit."""
        self.selected_vertex = None
        #self.CenterPanel.setEnabled(False)

    def mousePressEvent(self, event):
        """Is called when a mouse button is pressed; creates and moves
        nodes/vertices."""
        pos = self.get_mouse_position(event)
        #print('do i run here mousePressEvent',pos)

        # if we are not on canvas, don't do anything
        if pos is None:
            return

        # sets the focus to the window (for the keypresses to register)
        self.setFocus()

        # (potentially) find a node that has been pressed
        pressed_node = None
        for node in self.graph.get_nodes():
            #print('node position',node.get_position())
            #print('node radius',node.get_radius())
            #print('distance',distance(pos, node.get_position()))
            if distance(pos, node.get_position()) <= node.get_radius():
                print(node.get_position())
                pressed_node = node
        #print('pressed_node',pressed_node)
        # (potentially) find a vertex that has been pressed
        pressed_vertex = None
        #print('this is the vertex_positions',self.vertex_positions)

        for vertex in self.vertex_positions:
            #print('this is the abs 1', abs(vertex[0][0] - pos[0]) )
            #print('this is the abs 1', abs(vertex[0][1] - pos[1]) )
            if (
                # TODO: finish the selecting of vertices
                #abs(vertex[0][0] - pos[0]) < self.weight_rectangle_size
                #and abs(vertex[0][1] - pos[1]) < self.weight_rectangle_size
                abs(vertex[0][0] - pos[0]) < 3 #diff try with 3
                and abs(vertex[0][1] - pos[1]) < 3 #diff try with 3
            ):

                #pressed_vertex = vertex[1]
                pressed_vertex = vertex

        if event.button() == Qt.LeftButton:
            # nodes have the priority in selection before vertices
            #print('event left button with node ',node)
            if pressed_node is not None:
                self.deselect_vertex()
                self.select_node(pressed_node)

                self.mouse_drag_offset = pos - self.selected_node.get_position()
                self.mouse_position = pos

            elif pressed_vertex is not None:
                self.deselect_node()
                self.select_vertex(pressed_vertex)

            else:
                self.deselect_node()
                self.deselect_vertex()

        elif event.button() == Qt.RightButton:
            cmenu = QMenu(self)
            if pressed_node is not None:
                if pressed_node._failed:
                    unfail_node = cmenu.addAction("Node UP")
                else:
                    fail_node = cmenu.addAction("Node DOWN")
                node_information = cmenu.addAction("Node Info")
                delete_node = cmenu.addAction("Delete Node")
                add_link = cmenu.addAction("Add Link")
                change_name = cmenu.addAction("Change Name")
                action = cmenu.exec_(self.mapToGlobal(event.pos()))
                if action == node_information:
                    print('node information')
                    pass
                elif action == add_link:
                    self.add_link = QWidget()
                    self.add_link.ui = Ui_AddLink()
                    self.add_link.ui.setupUi(self.add_link, pressed_node, self.graph)
                    self.add_link.ui.update_demands.connect(self.demand_report)
                    self.add_link.show()
                elif action == change_name:
                    self.change_name = QWidget()
                    self.change_name.ui = Ui_ChangeName()
                    self.change_name.ui.setupUi(self.change_name,pressed_node,self.graph)
                    self.change_name.ui.update_demands.connect(self.demand_report)
                    self.change_name.show()
                elif action == delete_node:
                    self.graph.remove_node(pressed_node)
                    self.demand_report()
                    self.deselect_node()
                elif not pressed_node._failed and action == fail_node:
                    pressed_node.failNode()
                    self.demand_report()
                elif pressed_node._failed and action == unfail_node:
                    pressed_node.unfailNode()
                    self.demand_report()
            elif pressed_vertex is not None:
                if pressed_vertex[3]._failed:
                    unfail_link = cmenu.addAction("Link UP")
                else:
                    fail_link = cmenu.addAction("Link DOWN")
                link_information = cmenu.addAction("Link Info")
                change_metric = cmenu.addAction("Change Link Metric")
                delete_interface = cmenu.addAction("Delete Interface")
                action = cmenu.exec_(self.mapToGlobal(event.pos()))
                if action == link_information:
                    self.link_info = QWidget()
                    self.link_info.ui = Ui_link_info()
                    self.link_info.ui.setupUi(self.link_info,pressed_vertex[3])
                    self.link_info.ui.update_demands.connect(self.demand_report)
                    self.link_info.show()
                elif action == change_metric:
                    self.change_metric = QWidget()
                    self.change_metric.ui = Ui_EditLabel()
                    self.change_metric.ui.setupUi(self.change_metric,pressed_vertex[3],self.graph)
                    self.change_metric.ui.update_demands.connect(self.demand_report)
                    self.change_metric.show()
                elif not pressed_vertex[3]._failed and action == fail_link:
                    pressed_vertex[3].failInterface()
                    self.demand_report()
                elif pressed_vertex[3]._failed and action == unfail_link:
                    pressed_vertex[3].unfailInterface()
                    self.demand_report()
                elif action == delete_interface:
                    self.graph.remove_interface(pressed_vertex[3])
                    self.demand_report()

            else:
                add_node_action = cmenu.addAction("Add Node")
                action = cmenu.exec_(self.mapToGlobal(event.pos()))
                if action == add_node_action:
                    print("add node",pos)
                    node = self.graph.add_node(pos, self.node_radius)
                    #new node is failed
                    #node.failNode()
                    self.select_node(node)
                    self.deselect_vertex()
                pass
            pass


    def mouseReleaseEvent(self, event):
        """Is called when a mouse button is released; stops node drag."""
        self.mouse_drag_offset = None

    def mouseMoveEvent(self, event):
        """Is called when the mouse is moved across the window; updates mouse
        coordinates."""
        self.mouse_position = self.get_mouse_position(event, scale_down=True)

    def wheelEvent(self, event):
        """Is called when the mouse wheel is moved; node rotation and zoom."""
        # positive/negative for scrolling away from/towards the user
        scroll_distance = radians(event.angleDelta().y() / 8)

        if QApplication.keyboardModifiers() == Qt.ShiftModifier:
            if self.selected_node is not None:
                self.rotate_nodes_around(
                    self.selected_node.get_position(),
                    scroll_distance * self.node_rotation_coefficient,
                )
        else:
            mouse_coordinates = self.get_mouse_position(event)
            # only do something, if we're working on canvas
            if mouse_coordinates is None:
                return

            prev_scale = self.scale
            self.scale *= 2 ** (scroll_distance)

            # adjust translation so the x and y of the mouse stay in the same spot
            self.translation -= mouse_coordinates * (self.scale - prev_scale)

    def rotate_nodes_around(self, point: Vector, angle: float):
        """Rotates coordinates of all of the nodes in the same component as the selected
        node by a certain angle (in radians) around it."""
        for node in self.graph.get_nodes():
            if self.graph.share_component(node, self.selected_node):
                node.set_position((node.position - point).rotated(angle) + point)

    def get_mouse_position(self, event, scale_down=False) -> Vector:
        """Returns mouse coordinates if they are within the canvas and None if they are
        not. If scale_down is True, the function will scale down the coordinates to be
        within the canvas (useful for dragging) and return them instead."""
        x = event.pos().x()
        y = event.pos().y()

        x_on_canvas = 0 <= x <= self.canvas.width()
        y_on_canvas = 0 <= y <= self.canvas.height()

        # scale down the coordinates if scale_down is True, or return None if we are
        # not on canvas
        if scale_down:
            x = x if x_on_canvas else 0 if x <= 0 else self.canvas.width()
            y = y if y_on_canvas else 0 if y <= 0 else self.canvas.height()
        elif not x_on_canvas or not y_on_canvas:
            return None

        # return the mouse coordinates, accounting for canvas translation and scale
        return (Vector(x, y) - self.translation) / self.scale

    def perform_simulation_iteration(self):
        """Performs one iteration of the simulation."""
        # evaluate forces that act upon each pair of nodes

        for i, n1 in enumerate(self.graph.get_nodes()):
            for j, n2 in enumerate(self.graph.get_nodes()[i + 1 :]):
                # if they are not in the same component, no forces act on them
                if not self.graph.share_component(n1, n2):
                    continue

                # if the nodes are right on top of each other, no forces act on them
                d = distance(n1.get_position(), n2.get_position())
                if n1.get_position() == n2.get_position():
                    continue

                uv = (n2.get_position() - n1.get_position()).unit()

                # the size of the repel force between the two nodes
                fr = self.repulsion_force(d)

                # add a repel force to each of the nodes, in the opposite directions
                n1.add_force(-uv * fr)
                n2.add_force(uv * fr)

                # if they are also connected, add the attraction force
                if self.graph.does_vertex_exist(n1, n2, ignore_direction=True):
                    fa = self.attraction_force(d)

                    n1.add_force(-uv * fa)
                    n2.add_force(uv * fa)

            # since this node will not be visited again, we can evaluate the forces
            n1.evaluate_forces()

        # drag the selected node
        if self.selected_node is not None and self.mouse_drag_offset is not None:
            prev_node_position = self.selected_node.get_position()

            self.selected_node.set_position(
                self.mouse_position - self.mouse_drag_offset
            )

            # move the rest of the nodes that are connected to the selected node if
            # shift is pressed
            if QApplication.keyboardModifiers() == Qt.ShiftModifier:
                pos_delta = self.selected_node.get_position() - prev_node_position

                for node in self.graph.get_nodes():
                    if node is not self.selected_node and self.graph.share_component(
                        node, self.selected_node
                    ):
                        node.set_position(node.get_position() + pos_delta)

        self.canvas.update()
        #self.repaint()

    def paintEvent(self,event):
        """Paints the board."""
        painter = QPainter(self)

        painter.setRenderHint(QPainter.Antialiasing, True)

        painter.setPen(QPen(Qt.black, Qt.SolidLine))
        #painter.setBrush(QBrush(Qt.lightGray, Qt.SolidPattern))

        painter.setClipRect(0, 0, self.canvas.width(), self.canvas.height())

        # background
        #painter.drawRect(0, 0, self.canvas.width(), self.canvas.height())

        painter.translate(*self.translation)
        painter.scale(self.scale, self.scale)

        # if the graph is weighted, reset the positions, since they will be re-drawn
        # later on
        # No need , graph is always weighted // REMOVE if self.graph.is_weighted():
        self.vertex_positions = []

        # draw vertices; has to be drawn before nodes, so they aren't drawn on top
        # can this cause CPU spikes ?

        for n1 in self.graph.get_nodes():
            for entry in n1.get_interfaces():
                #print('paint event entry:',entry)
                n2 = entry.target
                weight = entry.metric
                util = entry.utilization()
                label = entry.local_ip
                linknum = entry.link_num
                #TODO move this external and link it with Util Legend
                if entry._failed:
                    link_color = Qt.red
                elif util == 0:
                    link_color = Qt.darkGray
                elif 0 < util < 10:
                    link_color = Qt.blue
                elif 10 <= util < 30:
                    link_color = Qt.green
                elif 30 <= util < 75:
                    link_color = Qt.cyan
                elif 75 <= util < 100:
                    link_color = Qt.yellow
                elif util >= 100:
                    link_color = Qt.magenta
                else:
                    link_color = Qt.gray

                import math
                n1_p = Vector(*n1.get_position())
                n2_p = Vector(*n2.get_position())

                #TODO , this is from JS algrorithm , clean up and move external
                if linknum % 2 ==0:
                    targetDistance = linknum * 3
                else:
                    targetDistance = (-linknum +1 ) * 3

                x1_x0 = n2_p[0] - n1_p[0]
                y1_y0 = n2_p[1] - n1_p[1]
                angle = math.atan((x1_x0) / (y1_y0))
                x2_x0 = -targetDistance * math.cos(angle)
                y2_y0 = targetDistance * math.sin(angle)
                d0x= n1_p[0] + (1 * x2_x0)
                d0y= n1_p[1] + (1 * y2_y0)
                d1x= n2_p[0] + ( 1 * x2_x0)
                d1y= n2_p[1] + (1 * y2_y0)
                dx = d1x - d0x,
                dy = d1y - d0y,
                dr = math.sqrt(dx[0] * dx[0] + dy[0] * dy[0])
                endX = (d1x + d0x) / 2
                endY = (d1y + d0y) / 2
                len1 = dr - ((dr/2) * math.sqrt(3))
                endX = endX + (  len1/dr)
                endY = endY + (  len1/dr)

                #set the new coordinates for line start and end points taking into accound the offset for each
                n1_p = Vector(d0x,d0y)
                n2_p = Vector(endX,endY)

                # create a unit vector from the first to the second node
                uv = (n2_p - n1_p).unit()
                #print('this is the uv',uv)

                #get the distance between two nodes
                d = distance(n1_p, n2_p)
                r = n2.get_radius()

                #draw arrow position
                arrow_head_pos = n2_p #n1_p + uv * (d - r)

                # calculate the two remaining points of the arrow; this is done the
                # same way as the previous calculation (shift by vector)
                d = distance(n1_p, arrow_head_pos)
                uv_arrow = (arrow_head_pos - n1_p).unit()

                # position of the base of the arrow
                arrow_base_pos = n1_p + uv_arrow * (d - self.arrowhead_size * 2)

                # the normal vectors to the unit vector of the arrow head
                nv_arrow = uv_arrow.rotated(pi / 2)

                # draw the tip of the arrow, as the triangle

                painter.setBrush(QBrush(Qt.black, Qt.SolidPattern))
                painter.drawPolygon(
                    QPointF(*arrow_head_pos),
                    QPointF(*(arrow_base_pos + nv_arrow * self.arrowhead_size)),
                    QPointF(*(arrow_base_pos - nv_arrow * self.arrowhead_size)),
                )


                painter.setPen(QPen(link_color, Qt.SolidLine))

                painter.drawLine(QPointF(d0x,d0y),QPointF(endX,endY))
                link_paint = QLineF(QPointF(d0x,d0y), QPointF(endX,endY))

                # the position of the head of the arrow
                arrow_head_pos = n2_p #n1_p + uv * (d - r)

                # calculate the two remaining points of the arrow; this is done the
                # same way as the previous calculation (shift by vector)
                d = distance(n1_p, arrow_head_pos)
                uv_arrow = (arrow_head_pos - n1_p).unit()

                # position of the base of the arrow
                arrow_base_pos = n1_p + uv_arrow * (d - self.arrowhead_size * 2)

                # the normal vectors to the unit vector of the arrow head
                nv_arrow = uv_arrow.rotated(pi / 2)

                # draw the tip of the arrow, as the triangle
                painter.setBrush(QBrush(link_color, Qt.SolidPattern))
                painter.drawPolygon(
                    QPointF(*arrow_head_pos),
                    QPointF(*(arrow_base_pos + nv_arrow * self.arrowhead_size)),
                    QPointF(*(arrow_base_pos - nv_arrow * self.arrowhead_size)),
                )

                if self.graph:
                    #calculate mid point of the link where to place the label
                    mid = (arrow_base_pos + n1_p) /2

                    # if the graph is directed, the vertices are offset (so they
                    # aren't draw on top of each other), so we need to shift them
                    # back to be at the midpoint between the nodes
                    if self.graph.is_directed():
                        mid -= uv * r * (1 - cos(self.arrow_separation))

                    r = self.weight_rectangle_size

                    self.vertex_positions.append((mid, (n1, n2), weight, entry))
                    #print('self.selected_vertex',self.selected_vertex)

                    # make the selected vertex rectangle background different, if
                    # it's selected (for aesthetics)

                    if (
                        self.selected_vertex is not None
                        and n1 is self.selected_vertex[1][0]
                        and n2 is self.selected_vertex[1][1]
                        and self.selected_vertex == weight
                    ):
                        painter.setBrush(
                            QBrush(Qt.black, Qt.SolidPattern)
                        )
                        painter.setPen(QPen(Qt.black, Qt.SolidLine))
                    else:
                        painter.setBrush(
                            QBrush(
                                Qt.black, Qt.SolidPattern
                            )
                        )
                        painter.setPen(QPen(Qt.black, Qt.SolidLine))

                    # the text rectangle
                    w_len = len(str(weight)) / 3 * r + r / 3
                    weight_v = Vector(r if w_len <= r else w_len, r)
                    weight_rectangle = QRectF(*(mid - weight_v), *(2 * weight_v))
                    #Vector(lenght,height)
                    weight_v = Vector(w_len,2)
                    weight_rectangle = QRectF(*(mid - weight_v), *(2 * weight_v))

                    #the text is still upside down but rotation is fine now
                    is_fixed = True

                    if is_fixed :
                        painter.save()
                        if endX - d0x > 0:
                            link_paint = QLineF(QPointF(d0x,d0y), QPointF(endX,endY))
                        else:
                            link_paint = QLineF(QPointF(endX,endY), QPointF(d0x,d0y))

                        center_of_rec_x = weight_rectangle.center().x()
                        #center_of_rec_x = link_paint.center().x()
                        center_of_rec_y  = weight_rectangle.center().y()
                        #center_of_rec_y = link_paint.center().y()

                        painter.translate(center_of_rec_x, center_of_rec_y)


                        rx = -(weight_v[0] * 0.5)
                        ry = -(weight_v[1] )


                        painter.rotate(- link_paint.angle());
                        new_rec = QRect(rx , ry, weight_v[0], 2 * weight_v[1])
                        painter.drawRect(QRect(rx , ry, weight_v[0] , 2 * weight_v[1] ))
                        painter.setFont(QFont(self.font_family, self.font_size / 3))
                        #painter.resetTransform()
                        #painter.restore()
                        painter.setPen(QPen(Qt.white, Qt.SolidLine))
                        #print(new_rec.center().x())
                        #print(dir(painter))
                        #print('this is the metruc in draw text',weight)
                        painter.drawText(new_rec, Qt.AlignCenter, str(weight))
                        #painter.drawText(ry,rx,str(weight))
                        painter.restore()
                        painter.setPen(QPen(Qt.black, Qt.SolidLine))
                        painter.setFont(QFont(self.font_family, self.font_size / 3))
                    else:
                        painter.drawRect(weight_rectangle)
                        painter.setFont(QFont(self.font_family, self.font_size / 3))
                        painter.setPen(QPen(Qt.white, Qt.SolidLine))
                        painter.drawText(weight_rectangle, Qt.AlignCenter, str(weight))
                        painter.setPen(QPen(Qt.black, Qt.SolidLine))


        # draw nodes
        for node in self.graph.get_nodes():

            # set the color according to whether it's selected
            if node._failed:
                painter.setBrush(QBrush(Qt.red,Qt.SolidPattern))
            else:
                painter.setBrush(
                QBrush(
                    self.selected_color
                    if node is self.selected_node
                    else self.regular_node_color,
                    Qt.SolidPattern,
                )
            )

            node_position = node.get_position()
            #print(node_position)
            node_radius = Vector(node.get_radius()).repeat(2)

            painter.drawEllipse(QPointF(*node_position), *node_radius)

            #if self.CenterPanel.labels_checkbox.isChecked():
            label = node.get_label()
            # scale font down, depending on the length of the label of the node
            #painter.setFont(QFont(self.font_family, self.font_size / label))
            painter.setFont(QFont(self.font_family, self.font_size / 3 ))
            # draw the node label within the node dimensions
            painter.drawText(
                QRectF(*(node_position - node_radius), *(2 * node_radius)),
                Qt.AlignCenter,
                label,
            )


'''
    app = QApplication(sys.argv)

    #TODO add some nice css
    #import qdarkstyle
    #app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    #app.setStyle("Fusion")

    #app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    #print(app.styleSheet())

    #f = open("style.css","w+")
    #f.write(app.styleSheet())
    with open('style.css', 'r') as file:
        data = file.read()
    app.setStyleSheet(data)
    ex = TreeVisualizer()
    sys.exit(app.exec_())
'''