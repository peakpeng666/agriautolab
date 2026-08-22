"""田块各个域只由 FieldGeometry 一处导出，避免各处各自计算可作业区。"""

from agriautolab.geometry.kernel import FieldGeometry

__all__ = ["FieldGeometry"]
