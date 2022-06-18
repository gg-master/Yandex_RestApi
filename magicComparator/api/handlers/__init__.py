from .delete import DeleteUnitView
from .imports import ImportsView
from .units_nodes import NodesUnitView

HANDLERS = (
    ImportsView, DeleteUnitView, NodesUnitView
)
