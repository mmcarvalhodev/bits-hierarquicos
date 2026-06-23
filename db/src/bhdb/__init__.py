"""BH DB — prova de generalidade do paradigma BH em consulta de dados."""
from .table import Table, make_dataset
from .tree import AggregateTree

__all__ = ["Table", "make_dataset", "AggregateTree"]
