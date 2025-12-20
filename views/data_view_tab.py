"""データ閲覧タブ - 未実装のプレースホルダを提供"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTableWidget
from PySide6.QtCore import Qt
import logging

logger = logging.getLogger(__name__)


class DataViewTab(QWidget):
    """データ閲覧タブ"""

    def __init__(self, database):
        super().__init__()
        self.database = database
        self.conn = None
        try:
            self.conn = database.connect()
        except Exception:
            # コネクション未取得の場合でもUIは壊さない
            logger.exception("Failed to connect to database in DataViewTab")

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        info = QLabel("データ閲覧タブ（未実装のプレースホルダ）")
        info.setAlignment(Qt.AlignCenter)
        layout.addWidget(info)

        # 将来の実装用のテーブルプレースホルダ
        self.table = QTableWidget()
        layout.addWidget(self.table)

    def refresh(self):
        """表示更新（現状はプレースホルダ）"""
        if self.conn is None:
            return
        self.table.clearContents()


