from .delete import DeleteUnitView
from .imports import ImportsView
from .sales import SalesOffersView
from .statistic import UnitStatView
from .units_nodes import NodesUnitView

HANDLERS = (
    ImportsView, DeleteUnitView, NodesUnitView, SalesOffersView, UnitStatView
)
