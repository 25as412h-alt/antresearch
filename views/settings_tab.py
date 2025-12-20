"""
設定・管理タブ
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                               QGroupBox, QFormLayout, QComboBox, QLabel,
                               QFileDialog, QMessageBox, QTableWidget, QTableWidgetItem,
                               QTabWidget, QTextEdit, QSpinBox, QLineEdit,
                               QListWidget, QListWidgetItem)
from PySide6.QtCore import Qt
import logging
from pathlib import Path
from datetime import datetime

from utils.csv_import import CSVImporter
from models.species import Species
from models.database import Database

logger = logging.getLogger(__name__)


class SettingsTab(QWidget):
    """設定・管理タブ"""
    
    def __init__(self, database, config):
        super().__init__()
        self.database = database
        self.config = config
        self.conn = database.connect()
        
        self._init_ui()
    
    def _init_ui(self):
        """UI初期化"""
        main_layout = QVBoxLayout(self)
        
        # 表示更新ボタン
        button_layout = QHBoxLayout()
        self.refresh_button = QPushButton("表示更新 (F5)")
        self.refresh_button.setObjectName("primaryButton")
        self.refresh_button.clicked.connect(self.refresh)
        button_layout.addWidget(self.refresh_button)
        button_layout.addStretch()
        main_layout.addLayout(button_layout)
        
        # サブタブ
        self.sub_tab_widget = QTabWidget()
        main_layout.addWidget(self.sub_tab_widget)
        
        # 各タブ
        self.sub_tab_widget.addTab(self._create_import_tab(), "CSVインポート")
        self.sub_tab_widget.addTab(self._create_backup_tab(), "バックアップ")
        self.sub_tab_widget.addTab(self._create_integrity_tab(), "データ整合性")
        self.sub_tab_widget.addTab(self._create_species_tab(), "種名マスタ管理")
        self.sub_tab_widget.addTab(self._create_config_tab(), "アプリ設定")
    
    def _create_import_tab(self):
        """CSVインポートタブ"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # テンプレートダウンロード
        template_group = QGroupBox("テンプレートダウンロード")
        template_layout = QFormLayout()
        
        self.template_combo = QComboBox()
        self.template_combo.addItems([
            "親調査地テンプレート",
            "調査地テンプレート",
            "種名マスタテンプレート"
        ])
        template_layout.addRow("テンプレート:", self.template_combo)
        
        self.template_download_button = QPushButton("ダウンロード")
        self.template_download_button.clicked.connect(self._download_template)
        template_layout.addRow("", self.template_download_button)
        
        template_group.setLayout(template_layout)
        layout.addWidget(template_group)
        
        # インポート
        import_group = QGroupBox("CSVインポート")
        import_layout = QFormLayout()
        
        self.import_type_combo = QComboBox()
        self.import_type_combo.addItems([
            "親調査地",
            "調査地",
            "種名マスタ"
        ])
        import_layout.addRow("インポート対象:", self.import_type_combo)
        
        file_layout = QHBoxLayout()
        self.import_file_edit = QLineEdit()
        self.import_file_edit.setReadOnly(True)
        file_layout.addWidget(self.import_file_edit)
        
        self.import_file_button = QPushButton("ファイル選択")
        self.import_file_button.clicked.connect(self._select_import_file)
        file_layout.addWidget(self.import_file_button)
        
        import_layout.addRow("ファイル:", file_layout)
        
        self.import_exec_button = QPushButton("インポート実行")
        self.import_exec_button.setObjectName("primaryButton")
        self.import_exec_button.clicked.connect(self._execute_import)
        import_layout.addRow("", self.import_exec_button)
        
        import_group.setLayout(import_layout)
        layout.addWidget(import_group)
        
        # 結果表示
        result_group = QGroupBox("インポート結果")
        result_layout = QVBoxLayout()
        
        self.import_result_text = QTextEdit()
        self.import_result_text.setReadOnly(True)
        result_layout.addWidget(self.import_result_text)
        
        result_group.setLayout(result_layout)
        layout.addWidget(result_group)
        
        return widget
    
    def _create_backup_tab(self):
        """バックアップタブ"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # バックアップ作成
        backup_group = QGroupBox("バックアップ作成")
        backup_layout = QVBoxLayout()
        
        info_label = QLabel(
            "データベースの完全なバックアップを作成します。\n"
            "バックアップは backups/ ディレクトリに保存されます。"
        )
        backup_layout.addWidget(info_label)
        
        self.backup_create_button = QPushButton("バックアップ作成")
        self.backup_create_button.setObjectName("primaryButton")
        self.backup_create_button.clicked.connect(self._create_backup)
        backup_layout.addWidget(self.backup_create_button)
        
        backup_group.setLayout(backup_layout)
        layout.addWidget(backup_group)
        
        # バックアップ一覧
        list_group = QGroupBox("バックアップ一覧")
        list_layout = QVBoxLayout()
        
        self.backup_list = QListWidget()
        list_layout.addWidget(self.backup_list)
        
        button_layout = QHBoxLayout()
        self.backup_restore_button = QPushButton("復元")
        self.backup_restore_button.clicked.connect(self._restore_backup)
        button_layout.addWidget(self.backup_restore_button)
        
        self.backup_delete_button = QPushButton("削除")
        self.backup_delete_button.setObjectName("dangerButton")
        self.backup_delete_button.clicked.connect(self._delete_backup)
        button_layout.addWidget(self.backup_delete_button)
        
        self.backup_refresh_button = QPushButton("更新")
        self.backup_refresh_button.clicked.connect(self._load_backup_list)
        button_layout.addWidget(self.backup_refresh_button)
        
        button_layout.addStretch()
        list_layout.addLayout(button_layout)
        
        list_group.setLayout(list_layout)
        layout.addWidget(list_group)
        
        return widget
    
    def _create_integrity_tab(self):
        """データ整合性タブ"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 整合性チェック
        check_group = QGroupBox("整合性チェック")
        check_layout = QVBoxLayout()
        
        info_label = QLabel(
            "データベースの整合性をチェックします。\n"
            "- 孤立レコードの検出\n"
            "- 外部キー整合性\n"
            "- 重複データの検出\n"
            "- 異常値の検出"
        )
        check_layout.addWidget(info_label)
        
        self.integrity_check_button = QPushButton("整合性チェック実行")
        self.integrity_check_button.setObjectName("primaryButton")
        self.integrity_check_button.clicked.connect(self._check_integrity)
        check_layout.addWidget(self.integrity_check_button)
        
        check_group.setLayout(check_layout)
        layout.addWidget(check_group)
        
        # 結果表示
        result_group = QGroupBox("チェック結果")
        result_layout = QVBoxLayout()
        
        self.integrity_result_text = QTextEdit()
        self.integrity_result_text.setReadOnly(True)
        result_layout.addWidget(self.integrity_result_text)
        
        result_group.setLayout(result_layout)
        layout.addWidget(result_group)
        
        return widget
    
    def _create_species_tab(self):
        """種名マスタ管理タブ"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 種名追加
        add_group = QGroupBox("種名追加")
        add_layout = QFormLayout()
        
        self.species_name_edit = QLineEdit()
        self.species_name_edit.setPlaceholderText("Genus species")
        add_layout.addRow("学名*:", self.species_name_edit)
        
        self.species_genus_edit = QLineEdit()
        add_layout.addRow("属:", self.species_genus_edit)
        
        self.species_ja_name_edit = QLineEdit()
        add_layout.addRow("和名:", self.species_ja_name_edit)
        
        self.species_add_button = QPushButton("追加")
        self.species_add_button.setObjectName("primaryButton")
        self.species_add_button.clicked.connect(self._add_species)
        add_layout.addRow("", self.species_add_button)
        
        add_group.setLayout(add_layout)
        layout.addWidget(add_group)
        
        # 種名一覧
        list_group = QGroupBox("種名マスタ一覧")
        list_layout = QVBoxLayout()
        
        self.species_table = QTableWidget()
        self.species_table.setColumnCount(5)
        self.species_table.setHorizontalHeaderLabels([
            "ID", "学名", "属", "和名", "登録日"
        ])
        self.species_table.setAlternatingRowColors(True)
        self.species_table.setSelectionBehavior(QTableWidget.SelectRows)
        list_layout.addWidget(self.species_table)
        
        list_group.setLayout(list_layout)
        layout.addWidget(list_group)
        
        return widget
    
    def _create_config_tab(self):
        """アプリ設定タブ"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 表示設定
        display_group = QGroupBox("表示設定")
        display_layout = QFormLayout()
        
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 16)
        self.font_size_spin.setValue(int(self.config.get('UI', 'font_size', fallback=10)))
        display_layout.addRow("フォントサイズ:", self.font_size_spin)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Fusion", "Windows", "WindowsVista"])
        current_theme = self.config.get('UI', 'default_theme', fallback='Fusion')
        index = self.theme_combo.findText(current_theme)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)
        display_layout.addRow("テーマ:", self.theme_combo)
        
        display_group.setLayout(display_layout)
        layout.addWidget(display_group)
        
        # データベース設定
        db_group = QGroupBox("データベース設定")
        db_layout = QFormLayout()
        
        self.max_backups_spin = QSpinBox()
        self.max_backups_spin.setRange(10, 1000)
        self.max_backups_spin.setValue(int(self.config.get('Database', 'max_backups', fallback=100)))
        db_layout.addRow("最大バックアップ数:", self.max_backups_spin)
        
        db_group.setLayout(db_layout)
        layout.addWidget(db_group)
        
        # 保存ボタン
        save_button = QPushButton("設定を保存")
        save_button.setObjectName("primaryButton")
        save_button.clicked.connect(self._save_config)
        layout.addWidget(save_button)
        
        layout.addStretch()
        
        # バージョン情報
        version_label = QLabel(
            "<h3>アリ類群集・植生データ管理システム</h3>"
            "<p>Version: 1.0.0</p>"
            "<p>© 2025</p>"
        )
        version_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(version_label)
        
        return widget
    
    def refresh(self):
        """表示更新"""
        self._load_species_list()
        self._load_backup_list()
        logger.info("Settings tab refreshed")
    
    def _download_template(self):
        """テンプレートをダウンロード"""
        try:
            template_type = self.template_combo.currentText()
            
            type_map = {
                "親調査地テンプレート": "parent_sites",
                "調査地テンプレート": "survey_sites",
                "種名マスタテンプレート": "species"
            }
            
            template_key = type_map[template_type]
            default_name = f"{template_key}_template.csv"
            
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "テンプレート保存",
                default_name,
                "CSV Files (*.csv)"
            )
            
            if not file_path:
                return
            
            importer = CSVImporter(self.database)
            if importer.generate_template(template_key, file_path):
                QMessageBox.information(
                    self,
                    "成功",
                    f"テンプレートを保存しました:\n{file_path}"
                )
            else:
                QMessageBox.critical(self, "エラー", "テンプレート生成に失敗しました")
                
        except Exception as e:
            logger.error(f"Template download failed: {e}")
            QMessageBox.critical(self, "エラー", f"エラー: {str(e)}")
    
    def _select_import_file(self):
        """インポートファイルを選択"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "CSVファイル選択",
            "",
            "CSV Files (*.csv)"
        )
        
        if file_path:
            self.import_file_edit.setText(file_path)
    
    def _execute_import(self):
        """インポート実行"""
        try:
            file_path = self.import_file_edit.text()
            if not file_path:
                QMessageBox.warning(self, "警告", "ファイルを選択してください")
                return
            
            if not Path(file_path).exists():
                QMessageBox.warning(self, "警告", "ファイルが存在しません")
                return
            
            import_type = self.import_type_combo.currentText()
            
            importer = CSVImporter(self.database)
            
            if import_type == "親調査地":
                success, errors = importer.import_parent_sites(file_path)
            elif import_type == "調査地":
                success, errors = importer.import_survey_sites(file_path)
            elif import_type == "種名マスタ":
                success, errors = importer.import_species(file_path)
            else:
                QMessageBox.warning(self, "警告", "不明なインポート対象です")
                return
            
            # 結果表示
            result_html = f"<h3>インポート結果</h3>"
            result_html += f"<p><b>対象:</b> {import_type}</p>"
            result_html += f"<p><b>成功:</b> {success}件</p>"
            result_html += f"<p><b>エラー:</b> {len(errors)}件</p>"
            
            if errors:
                result_html += "<h4>エラー詳細:</h4><ul>"
                for error in errors[:50]:  # 最大50件表示
                    result_html += f"<li>{error}</li>"
                if len(errors) > 50:
                    result_html += f"<li>...他{len(errors)-50}件</li>"
                result_html += "</ul>"
            
            self.import_result_text.setHtml(result_html)
            
            if success > 0:
                QMessageBox.information(
                    self,
                    "完了",
                    f"{success}件のデータをインポートしました"
                )
                self.refresh()
            else:
                QMessageBox.warning(
                    self,
                    "警告",
                    "インポートに失敗しました\nエラー詳細を確認してください"
                )
                
        except Exception as e:
            logger.error(f"Import execution failed: {e}")
            QMessageBox.critical(self, "エラー", f"インポートに失敗しました:\n{str(e)}")
    
    def _create_backup(self):
        """バックアップ作成"""
        try:
            backup_dir = Path(self.config.get('Database', 'backup_dir', fallback='backups'))
            backup_path = self.database.backup(backup_dir)
            
            if backup_path:
                QMessageBox.information(
                    self,
                    "成功",
                    f"バックアップを作成しました:\n{backup_path}"
                )
                self._load_backup_list()
            else:
                QMessageBox.critical(self, "エラー", "バックアップの作成に失敗しました")
                
        except Exception as e:
            logger.error(f"Backup creation failed: {e}")
            QMessageBox.critical(self, "エラー", f"エラー: {str(e)}")
    
    def _load_backup_list(self):
        """バックアップ一覧を読み込み"""
        try:
            self.backup_list.clear()
            
            backup_dir = Path(self.config.get('Database', 'backup_dir', fallback='backups'))
            if not backup_dir.exists():
                return
            
            backups = sorted(backup_dir.glob("ant_database_*.db"), reverse=True)
            
            for backup in backups:
                size_mb = backup.stat().st_size / (1024 * 1024)
                item_text = f"{backup.name} ({size_mb:.2f} MB)"
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, str(backup))
                self.backup_list.addItem(item)
                
        except Exception as e:
            logger.error(f"Backup list loading failed: {e}")
    
    def _restore_backup(self):
        """バックアップから復元"""
        selected = self.backup_list.currentItem()
        if not selected:
            QMessageBox.warning(self, "警告", "復元するバックアップを選択してください")
            return
        
        backup_path = selected.data(Qt.UserRole)
        
        reply = QMessageBox.question(
            self,
            "確認",
            f"このバックアップから復元しますか？\n{Path(backup_path).name}\n\n"
            "現在のデータベースは上書きされます。\n"
            "（復元前に自動バックアップが作成されます）",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # 現在のDBをバックアップ
                self._create_backup()
                
                # 復元
                import shutil
                db_path = Path(self.config.get('Database', 'path', fallback='data/ant_database.db'))
                shutil.copy(backup_path, db_path)
                
                QMessageBox.information(
                    self,
                    "成功",
                    "バックアップから復元しました\nアプリケーションを再起動してください"
                )
                
            except Exception as e:
                logger.error(f"Backup restore failed: {e}")
                QMessageBox.critical(self, "エラー", f"復元に失敗しました:\n{str(e)}")
    
    def _delete_backup(self):
        """バックアップを削除"""
        selected = self.backup_list.currentItem()
        if not selected:
            QMessageBox.warning(self, "警告", "削除するバックアップを選択してください")
            return
        
        backup_path = Path(selected.data(Qt.UserRole))
        
        reply = QMessageBox.question(
            self,
            "確認",
            f"このバックアップを削除しますか？\n{backup_path.name}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                backup_path.unlink()
                QMessageBox.information(self, "成功", "バックアップを削除しました")
                self._load_backup_list()
                
            except Exception as e:
                logger.error(f"Backup deletion failed: {e}")
                QMessageBox.critical(self, "エラー", f"削除に失敗しました:\n{str(e)}")
    
    def _check_integrity(self):
        """整合性チェック"""
        try:
            results = []
            
            # SQLite整合性チェック
            if self.database.integrity_check():
                results.append("✓ データベース構造: OK")
            else:
                results.append("✗ データベース構造: エラー")
            
            cursor = self.conn.cursor()
            
            # 孤立レコードチェック
            cursor.execute("""
                SELECT COUNT(*) FROM survey_sites 
                WHERE parent_site_id NOT IN (SELECT id FROM parent_sites WHERE deleted_at IS NULL)
                AND deleted_at IS NULL
            """)
            orphan_sites = cursor.fetchone()[0]
            if orphan_sites == 0:
                results.append("✓ 孤立調査地: なし")
            else:
                results.append(f"✗ 孤立調査地: {orphan_sites}件")
            
            # 重複チェック
            cursor.execute("""
                SELECT name, COUNT(*) as cnt 
                FROM parent_sites 
                WHERE deleted_at IS NULL 
                GROUP BY name 
                HAVING cnt > 1
            """)
            duplicates = cursor.fetchall()
            if len(duplicates) == 0:
                results.append("✓ 親調査地名重複: なし")
            else:
                results.append(f"✗ 親調査地名重複: {len(duplicates)}件")
            
            # 結果表示
            result_html = "<h3>整合性チェック結果</h3><ul>"
            for result in results:
                if "✓" in result:
                    result_html += f"<li style='color: green;'>{result}</li>"
                else:
                    result_html += f"<li style='color: red;'>{result}</li>"
            result_html += "</ul>"
            
            self.integrity_result_text.setHtml(result_html)
            
            QMessageBox.information(self, "完了", "整合性チェックが完了しました")
            
        except Exception as e:
            logger.error(f"Integrity check failed: {e}")
            QMessageBox.critical(self, "エラー", f"チェックに失敗しました:\n{str(e)}")
    
    def _load_species_list(self):
        """種名一覧を読み込み"""
        try:
            species_model = Species(self.conn)
            species_list = species_model.get_all()
            
            self.species_table.setRowCount(len(species_list))
            for row, species in enumerate(species_list):
                self.species_table.setItem(row, 0, QTableWidgetItem(str(species['id'])))
                self.species_table.setItem(row, 1, QTableWidgetItem(species['scientific_name']))
                self.species_table.setItem(row, 2, QTableWidgetItem(species['genus'] or ''))
                self.species_table.setItem(row, 3, QTableWidgetItem(species['ja_name'] or ''))
                self.species_table.setItem(row, 4, QTableWidgetItem(species['created_at'] or ''))
                
        except Exception as e:
            logger.error(f"Species list loading failed: {e}")
    
    def _add_species(self):
        """種名を追加"""
        try:
            scientific_name = self.species_name_edit.text().strip()
            if not scientific_name:
                QMessageBox.warning(self, "警告", "学名を入力してください")
                return
            
            species_model = Species(self.conn)
            species_id = species_model.create(
                scientific_name=scientific_name,
                genus=self.species_genus_edit.text().strip() or None,
                ja_name=self.species_ja_name_edit.text().strip() or None
            )
            
            if species_id:
                QMessageBox.information(self, "成功", f"種名を追加しました (ID: {species_id})")
                self.species_name_edit.clear()
                self.species_genus_edit.clear()
                self.species_ja_name_edit.clear()
                self._load_species_list()
            else:
                QMessageBox.critical(self, "エラー", "種名の追加に失敗しました\n（学名重複または形式エラー）")
                
        except Exception as e:
            logger.error(f"Species addition failed: {e}")
            QMessageBox.critical(self, "エラー", f"エラー: {str(e)}")
    
    def _save_config(self):
        """設定を保存"""
        try:
            self.config.set('UI', 'font_size', str(self.font_size_spin.value()))
            self.config.set('UI', 'default_theme', self.theme_combo.currentText())
            self.config.set('Database', 'max_backups', str(self.max_backups_spin.value()))
            
            with open('config.ini', 'w', encoding='utf-8') as f:
                self.config.write(f)
            
            QMessageBox.information(
                self,
                "成功",
                "設定を保存しました\n一部の設定はアプリケーション再起動後に反映されます"
            )
            
        except Exception as e:
            logger.error(f"Config save failed: {e}")
            QMessageBox.critical(self, "エラー", f"設定の保存に失敗しました:\n{str(e)}")