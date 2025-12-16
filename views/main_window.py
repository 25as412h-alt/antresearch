"""
メインウィンドウ
"""
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, 
                               QTabWidget, QStatusBar, QMenuBar, QMenu)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
import logging

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """メインウィンドウクラス"""
    
    def __init__(self, database, config):
        super().__init__()
        self.database = database
        self.config = config
        
        self.setWindowTitle("アリ類群集・植生データ管理システム v1.0")
        
        # ウィンドウサイズ設定
        width = int(config.get('UI', 'window_width', fallback=1400))
        height = int(config.get('UI', 'window_height', fallback=900))
        self.resize(width, height)
        
        # UIの初期化
        self._init_ui()
        self._create_menu_bar()
        self._create_status_bar()
        
        logger.info("Main window initialized")
    
    def _init_ui(self):
        """UI初期化"""
        # 中央ウィジェット
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # メインレイアウト
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # タブウィジェット
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # 各タブを追加
        from views.data_input_tab import DataInputTab
        
        self.data_input_tab = DataInputTab(self.database)
        self.tab_widget.addTab(self.data_input_tab, "データ管理")
        
        # プレースホルダータブ（後で実装）
        self._add_placeholder_tab("データ閲覧")
        self._add_placeholder_tab("解析・出力")
        self._add_placeholder_tab("地図・クラスタ")
        self._add_placeholder_tab("設定・管理")
    
    def _add_placeholder_tab(self, title: str):
        """プレースホルダータブを追加"""
        from PySide6.QtWidgets import QLabel
        placeholder = QWidget()
        layout = QVBoxLayout(placeholder)
        label = QLabel(f"{title}タブ（未実装）")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        self.tab_widget.addTab(placeholder, title)
    
    def _create_menu_bar(self):
        """メニューバーを作成"""
        menubar = self.menuBar()
        
        # ファイルメニュー
        file_menu = menubar.addMenu("ファイル(&F)")
        
        backup_action = QAction("バックアップ作成(&B)", self)
        backup_action.triggered.connect(self._on_backup)
        file_menu.addAction(backup_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("終了(&X)", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 編集メニュー
        edit_menu = menubar.addMenu("編集(&E)")
        
        refresh_action = QAction("表示更新(&R)", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self._on_refresh)
        edit_menu.addAction(refresh_action)
        
        # ヘルプメニュー
        help_menu = menubar.addMenu("ヘルプ(&H)")
        
        about_action = QAction("バージョン情報(&A)", self)
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)
    
    def _create_status_bar(self):
        """ステータスバーを作成"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("準備完了")
    
    def _on_backup(self):
        """バックアップ作成"""
        from pathlib import Path
        from PySide6.QtWidgets import QMessageBox
        
        backup_dir = Path(self.config.get('Database', 'backup_dir', fallback='backups'))
        backup_path = self.database.backup(backup_dir)
        
        if backup_path:
            QMessageBox.information(
                self,
                "バックアップ完了",
                f"バックアップを作成しました:\n{backup_path}"
            )
            self.status_bar.showMessage(f"バックアップ作成完了: {backup_path.name}", 5000)
        else:
            QMessageBox.critical(
                self,
                "エラー",
                "バックアップの作成に失敗しました"
            )
    
    def _on_refresh(self):
        """表示更新"""
        current_index = self.tab_widget.currentIndex()
        current_widget = self.tab_widget.widget(current_index)
        
        if hasattr(current_widget, 'refresh'):
            current_widget.refresh()
            self.status_bar.showMessage("表示を更新しました", 3000)
        
        logger.info("Display refreshed")
    
    def _on_about(self):
        """バージョン情報"""
        from PySide6.QtWidgets import QMessageBox
        
        QMessageBox.about(
            self,
            "バージョン情報",
            "<h3>アリ類群集・植生データ管理システム</h3>"
            "<p>Version: 1.0.0</p>"
            "<p>© 2025 研究者本人</p>"
            "<p>Python + PySide6 + SQLite3</p>"
        )
    
    def closeEvent(self, event):
        """ウィンドウを閉じる際の処理"""
        from PySide6.QtWidgets import QMessageBox
        
        reply = QMessageBox.question(
            self,
            "確認",
            "アプリケーションを終了しますか？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            logger.info("Application closing")
            event.accept()
        else:
            event.ignore()