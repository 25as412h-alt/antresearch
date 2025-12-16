"""
データ入力タブ
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QTabWidget, QGroupBox, QFormLayout, QLineEdit,
                               QDoubleSpinBox, QTextEdit, QComboBox, QLabel,
                               QTableWidget, QTableWidgetItem, QMessageBox,
                               QHeaderView)
from PySide6.QtCore import Qt
from PySide6.QtGui import QDoubleValidator
import logging

from models.parent_site import ParentSite
from models.survey_site import SurveySite

logger = logging.getLogger(__name__)


class DataInputTab(QWidget):
    """データ入力タブ"""
    
    def __init__(self, database):
        super().__init__()
        self.database = database
        self.conn = database.connect()
        
        # モデルの初期化
        self.parent_site_model = ParentSite(self.conn)
        self.survey_site_model = SurveySite(self.conn)
        
        self._init_ui()
        
        # 初期データ読み込み
        self.refresh()
    
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
        
        # サブタブウィジェット
        self.sub_tab_widget = QTabWidget()
        main_layout.addWidget(self.sub_tab_widget)
        
        # 親調査地タブ
        self.parent_site_tab = self._create_parent_site_tab()
        self.sub_tab_widget.addTab(self.parent_site_tab, "親調査地")
        
        # 調査地タブ
        self.survey_site_tab = self._create_survey_site_tab()
        self.sub_tab_widget.addTab(self.survey_site_tab, "調査地")
        
        # プレースホルダータブ
        self._add_placeholder_subtab("調査イベント")
        self._add_placeholder_subtab("植生データ")
        self._add_placeholder_subtab("アリ類データ")
    
    def _add_placeholder_subtab(self, title: str):
        """プレースホルダーサブタブ"""
        placeholder = QWidget()
        layout = QVBoxLayout(placeholder)
        label = QLabel(f"{title}（未実装）")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        self.sub_tab_widget.addTab(placeholder, title)
    
    def _create_parent_site_tab(self):
        """親調査地タブを作成"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 入力フォーム
        form_group = QGroupBox("親調査地 登録・編集")
        form_layout = QFormLayout()
        
        # 名称（必須）
        name_layout = QHBoxLayout()
        self.ps_name_label = QLabel("名称:")
        self.ps_name_label.setProperty("required", True)
        self.ps_name_edit = QLineEdit()
        self.ps_name_edit.setPlaceholderText("例: 中部_南信")
        self.ps_name_edit.setMaxLength(200)
        name_layout.addWidget(self.ps_name_edit)
        form_layout.addRow(self.ps_name_label, name_layout)
        
        # 緯度（必須）
        lat_layout = QHBoxLayout()
        self.ps_lat_label = QLabel("緯度:")
        self.ps_lat_label.setProperty("required", True)
        self.ps_lat_edit = QDoubleSpinBox()
        self.ps_lat_edit.setRange(20.0, 46.0)
        self.ps_lat_edit.setDecimals(6)
        self.ps_lat_edit.setSingleStep(0.001)
        self.ps_lat_edit.setToolTip("日本国内: 20.0～46.0")
        lat_layout.addWidget(self.ps_lat_edit)
        lat_layout.addWidget(QLabel("°N"))
        lat_layout.addStretch()
        form_layout.addRow(self.ps_lat_label, lat_layout)
        
        # 経度（必須）
        lon_layout = QHBoxLayout()
        self.ps_lon_label = QLabel("経度:")
        self.ps_lon_label.setProperty("required", True)
        self.ps_lon_edit = QDoubleSpinBox()
        self.ps_lon_edit.setRange(122.0, 154.0)
        self.ps_lon_edit.setDecimals(6)
        self.ps_lon_edit.setSingleStep(0.001)
        self.ps_lon_edit.setToolTip("日本国内: 122.0～154.0")
        lon_layout.addWidget(self.ps_lon_edit)
        lon_layout.addWidget(QLabel("°E"))
        lon_layout.addStretch()
        form_layout.addRow(self.ps_lon_label, lon_layout)
        
        # 標高（任意）
        alt_layout = QHBoxLayout()
        self.ps_alt_edit = QDoubleSpinBox()
        self.ps_alt_edit.setRange(-500, 4000)
        self.ps_alt_edit.setDecimals(1)
        self.ps_alt_edit.setSpecialValueText("未設定")
        self.ps_alt_edit.setValue(-500)
        alt_layout.addWidget(self.ps_alt_edit)
        alt_layout.addWidget(QLabel("m"))
        alt_layout.addStretch()
        form_layout.addRow("標高:", alt_layout)
        
        # 面積（任意）
        area_layout = QHBoxLayout()
        self.ps_area_edit = QDoubleSpinBox()
        self.ps_area_edit.setRange(0, 999999999)
        self.ps_area_edit.setDecimals(1)
        self.ps_area_edit.setSpecialValueText("未設定")
        area_layout.addWidget(self.ps_area_edit)
        area_layout.addWidget(QLabel("m²"))
        area_layout.addStretch()
        form_layout.addRow("面積:", area_layout)
        
        # 備考（任意）
        self.ps_remarks_edit = QTextEdit()
        self.ps_remarks_edit.setMaximumHeight(80)
        self.ps_remarks_edit.setPlaceholderText("備考を入力（2000文字以内）")
        form_layout.addRow("備考:", self.ps_remarks_edit)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        # ボタン
        button_layout = QHBoxLayout()
        
        self.ps_add_button = QPushButton("新規登録")
        self.ps_add_button.setObjectName("primaryButton")
        self.ps_add_button.clicked.connect(self._on_add_parent_site)
        button_layout.addWidget(self.ps_add_button)
        
        self.ps_update_button = QPushButton("更新")
        self.ps_update_button.clicked.connect(self._on_update_parent_site)
        self.ps_update_button.setEnabled(False)
        button_layout.addWidget(self.ps_update_button)
        
        self.ps_delete_button = QPushButton("削除")
        self.ps_delete_button.setObjectName("dangerButton")
        self.ps_delete_button.clicked.connect(self._on_delete_parent_site)
        self.ps_delete_button.setEnabled(False)
        button_layout.addWidget(self.ps_delete_button)
        
        self.ps_clear_button = QPushButton("クリア")
        self.ps_clear_button.setObjectName("secondaryButton")
        self.ps_clear_button.clicked.connect(self._clear_parent_site_form)
        button_layout.addWidget(self.ps_clear_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # 一覧テーブル
        list_group = QGroupBox("親調査地 一覧")
        list_layout = QVBoxLayout()
        
        self.ps_table = QTableWidget()
        self.ps_table.setColumnCount(7)
        self.ps_table.setHorizontalHeaderLabels([
            "ID", "名称", "緯度", "経度", "標高(m)", "面積(m²)", "備考"
        ])
        self.ps_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.ps_table.setSelectionMode(QTableWidget.SingleSelection)
        self.ps_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.ps_table.setAlternatingRowColors(True)
        
        # 列幅調整
        header = self.ps_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.Stretch)
        
        self.ps_table.itemSelectionChanged.connect(self._on_parent_site_selected)
        
        list_layout.addWidget(self.ps_table)
        list_group.setLayout(list_layout)
        layout.addWidget(list_group)
        
        return widget
    
    def _create_survey_site_tab(self):
        """調査地タブを作成"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 入力フォーム
        form_group = QGroupBox("調査地 登録・編集")
        form_layout = QFormLayout()
        
        # 親調査地選択（必須）
        ps_layout = QHBoxLayout()
        self.ss_parent_label = QLabel("親調査地:")
        self.ss_parent_label.setProperty("required", True)
        self.ss_parent_combo = QComboBox()
        self.ss_parent_combo.setToolTip("親調査地を選択してください")
        ps_layout.addWidget(self.ss_parent_combo)
        ps_layout.addStretch()
        form_layout.addRow(self.ss_parent_label, ps_layout)
        
        # 名称（必須）
        name_layout = QHBoxLayout()
        self.ss_name_label = QLabel("名称:")
        self.ss_name_label.setProperty("required", True)
        self.ss_name_edit = QLineEdit()
        self.ss_name_edit.setPlaceholderText("例: 上伊那_信州大学農学部キャンパス")
        self.ss_name_edit.setMaxLength(200)
        name_layout.addWidget(self.ss_name_edit)
        form_layout.addRow(self.ss_name_label, name_layout)
        
        # 緯度（必須）
        lat_layout = QHBoxLayout()
        self.ss_lat_label = QLabel("緯度:")
        self.ss_lat_label.setProperty("required", True)
        self.ss_lat_edit = QDoubleSpinBox()
        self.ss_lat_edit.setRange(20.0, 46.0)
        self.ss_lat_edit.setDecimals(6)
        self.ss_lat_edit.setSingleStep(0.001)
        lat_layout.addWidget(self.ss_lat_edit)
        lat_layout.addWidget(QLabel("°N"))
        lat_layout.addStretch()
        form_layout.addRow(self.ss_lat_label, lat_layout)
        
        # 経度（必須）
        lon_layout = QHBoxLayout()
        self.ss_lon_label = QLabel("経度:")
        self.ss_lon_label.setProperty("required", True)
        self.ss_lon_edit = QDoubleSpinBox()
        self.ss_lon_edit.setRange(122.0, 154.0)
        self.ss_lon_edit.setDecimals(6)
        self.ss_lon_edit.setSingleStep(0.001)
        lon_layout.addWidget(self.ss_lon_edit)
        lon_layout.addWidget(QLabel("°E"))
        lon_layout.addStretch()
        form_layout.addRow(self.ss_lon_label, lon_layout)
        
        # 標高（任意）
        alt_layout = QHBoxLayout()
        self.ss_alt_edit = QDoubleSpinBox()
        self.ss_alt_edit.setRange(-500, 4000)
        self.ss_alt_edit.setDecimals(1)
        self.ss_alt_edit.setSpecialValueText("未設定")
        self.ss_alt_edit.setValue(-500)
        alt_layout.addWidget(self.ss_alt_edit)
        alt_layout.addWidget(QLabel("m"))
        alt_layout.addStretch()
        form_layout.addRow("標高:", alt_layout)
        
        # 面積（任意）
        area_layout = QHBoxLayout()
        self.ss_area_edit = QDoubleSpinBox()
        self.ss_area_edit.setRange(0, 999999999)
        self.ss_area_edit.setDecimals(1)
        self.ss_area_edit.setSpecialValueText("未設定")
        area_layout.addWidget(self.ss_area_edit)
        area_layout.addWidget(QLabel("m²"))
        area_layout.addStretch()
        form_layout.addRow("面積:", area_layout)
        
        # 備考（任意）
        self.ss_remarks_edit = QTextEdit()
        self.ss_remarks_edit.setMaximumHeight(80)
        self.ss_remarks_edit.setPlaceholderText("備考を入力（2000文字以内）")
        form_layout.addRow("備考:", self.ss_remarks_edit)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        # ボタン
        button_layout = QHBoxLayout()
        
        self.ss_add_button = QPushButton("新規登録")
        self.ss_add_button.setObjectName("primaryButton")
        self.ss_add_button.clicked.connect(self._on_add_survey_site)
        button_layout.addWidget(self.ss_add_button)
        
        self.ss_update_button = QPushButton("更新")
        self.ss_update_button.clicked.connect(self._on_update_survey_site)
        self.ss_update_button.setEnabled(False)
        button_layout.addWidget(self.ss_update_button)
        
        self.ss_delete_button = QPushButton("削除")
        self.ss_delete_button.setObjectName("dangerButton")
        self.ss_delete_button.clicked.connect(self._on_delete_survey_site)
        self.ss_delete_button.setEnabled(False)
        button_layout.addWidget(self.ss_delete_button)
        
        self.ss_clear_button = QPushButton("クリア")
        self.ss_clear_button.setObjectName("secondaryButton")
        self.ss_clear_button.clicked.connect(self._clear_survey_site_form)
        button_layout.addWidget(self.ss_clear_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # 一覧テーブル
        list_group = QGroupBox("調査地 一覧")
        list_layout = QVBoxLayout()
        
        self.ss_table = QTableWidget()
        self.ss_table.setColumnCount(8)
        self.ss_table.setHorizontalHeaderLabels([
            "ID", "親調査地", "名称", "緯度", "経度", "標高(m)", "面積(m²)", "備考"
        ])
        self.ss_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.ss_table.setSelectionMode(QTableWidget.SingleSelection)
        self.ss_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.ss_table.setAlternatingRowColors(True)
        
        # 列幅調整
        header = self.ss_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.Stretch)
        
        self.ss_table.itemSelectionChanged.connect(self._on_survey_site_selected)
        
        list_layout.addWidget(self.ss_table)
        list_group.setLayout(list_layout)
        layout.addWidget(list_group)
        
        return widget
    
    def refresh(self):
        """表示更新"""
        self._load_parent_sites()
        self._load_survey_sites()
        self._update_parent_site_combo()
        logger.info("Data input tab refreshed")
    
    def _load_parent_sites(self):
        """親調査地一覧を読み込み"""
        sites = self.parent_site_model.get_all()
        
        self.ps_table.setRowCount(len(sites))
        for row, site in enumerate(sites):
            self.ps_table.setItem(row, 0, QTableWidgetItem(str(site['id'])))
            self.ps_table.setItem(row, 1, QTableWidgetItem(site['name'] or ''))
            self.ps_table.setItem(row, 2, QTableWidgetItem(f"{site['latitude']:.6f}" if site['latitude'] else ''))
            self.ps_table.setItem(row, 3, QTableWidgetItem(f"{site['longitude']:.6f}" if site['longitude'] else ''))
            self.ps_table.setItem(row, 4, QTableWidgetItem(f"{site['altitude']:.1f}" if site['altitude'] else ''))
            self.ps_table.setItem(row, 5, QTableWidgetItem(f"{site['area']:.1f}" if site['area'] else ''))
            self.ps_table.setItem(row, 6, QTableWidgetItem(site['remarks'][:50] if site['remarks'] else ''))
    
    def _load_survey_sites(self):
        """調査地一覧を読み込み"""
        sites = self.survey_site_model.get_all()
        
        self.ss_table.setRowCount(len(sites))
        for row, site in enumerate(sites):
            self.ss_table.setItem(row, 0, QTableWidgetItem(str(site['id'])))
            self.ss_table.setItem(row, 1, QTableWidgetItem(site.get('parent_site_name', '') or ''))
            self.ss_table.setItem(row, 2, QTableWidgetItem(site['name'] or ''))
            self.ss_table.setItem(row, 3, QTableWidgetItem(f"{site['latitude']:.6f}" if site['latitude'] else ''))
            self.ss_table.setItem(row, 4, QTableWidgetItem(f"{site['longitude']:.6f}" if site['longitude'] else ''))
            self.ss_table.setItem(row, 5, QTableWidgetItem(f"{site['altitude']:.1f}" if site['altitude'] else ''))
            self.ss_table.setItem(row, 6, QTableWidgetItem(f"{site['area']:.1f}" if site['area'] else ''))
            self.ss_table.setItem(row, 7, QTableWidgetItem(site['remarks'][:50] if site['remarks'] else ''))
    
    def _update_parent_site_combo(self):
        """親調査地コンボボックスを更新"""
        self.ss_parent_combo.clear()
        sites = self.parent_site_model.get_all()
        
        for site in sites:
            self.ss_parent_combo.addItem(site['name'], site['id'])
    
    def _on_add_parent_site(self):
        """親調査地を新規登録"""
        name = self.ps_name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "入力エラー", "名称は必須項目です")
            return
        
        latitude = self.ps_lat_edit.value()
        longitude = self.ps_lon_edit.value()
        altitude = self.ps_alt_edit.value() if self.ps_alt_edit.value() > -500 else None
        area = self.ps_area_edit.value() if self.ps_area_edit.value() > 0 else None
        remarks = self.ps_remarks_edit.toPlainText().strip() or None
        
        site_id = self.parent_site_model.create(
            name=name,
            latitude=latitude,
            longitude=longitude,
            altitude=altitude,
            area=area,
            remarks=remarks
        )
        
        if site_id:
            QMessageBox.information(self, "成功", f"親調査地を登録しました (ID: {site_id})")
            self._clear_parent_site_form()
            self.refresh()
        else:
            QMessageBox.critical(self, "エラー", "親調査地の登録に失敗しました\n同じ名称が既に存在する可能性があります")
    
    def _on_update_parent_site(self):
        """親調査地を更新"""
        selected = self.ps_table.selectedItems()
        if not selected:
            return
        
        site_id = int(self.ps_table.item(selected[0].row(), 0).text())
        
        name = self.ps_name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "入力エラー", "名称は必須項目です")
            return
        
        success = self.parent_site_model.update(
            site_id,
            name=name,
            latitude=self.ps_lat_edit.value(),
            longitude=self.ps_lon_edit.value(),
            altitude=self.ps_alt_edit.value() if self.ps_alt_edit.value() > -500 else None,
            area=self.ps_area_edit.value() if self.ps_area_edit.value() > 0 else None,
            remarks=self.ps_remarks_edit.toPlainText().strip() or None
        )
        
        if success:
            QMessageBox.information(self, "成功", "親調査地を更新しました")
            self._clear_parent_site_form()
            self.refresh()
        else:
            QMessageBox.critical(self, "エラー", "親調査地の更新に失敗しました")
    
    def _on_delete_parent_site(self):
        """親調査地を削除"""
        selected = self.ps_table.selectedItems()
        if not selected:
            return
        
        site_id = int(self.ps_table.item(selected[0].row(), 0).text())
        site_name = self.ps_table.item(selected[0].row(), 1).text()
        
        reply = QMessageBox.question(
            self,
            "確認",
            f"親調査地「{site_name}」を削除しますか？\n（論理削除されます）",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success = self.parent_site_model.delete(site_id)
            
            if success:
                QMessageBox.information(self, "成功", "親調査地を削除しました")
                self._clear_parent_site_form()
                self.refresh()
            else:
                QMessageBox.critical(self, "エラー", "親調査地の削除に失敗しました")
    
    def _clear_parent_site_form(self):
        """親調査地フォームをクリア"""
        self.ps_name_edit.clear()
        self.ps_lat_edit.setValue(35.0)
        self.ps_lon_edit.setValue(138.0)
        self.ps_alt_edit.setValue(-500)
        self.ps_area_edit.setValue(0)
        self.ps_remarks_edit.clear()
        self.ps_update_button.setEnabled(False)
        self.ps_delete_button.setEnabled(False)
        self.ps_table.clearSelection()
    
    def _on_parent_site_selected(self):
        """親調査地が選択された"""
        selected = self.ps_table.selectedItems()
        if not selected:
            return
        
        row = selected[0].row()
        site_id = int(self.ps_table.item(row, 0).text())
        site = self.parent_site_model.get_by_id(site_id)
        
        if site:
            self.ps_name_edit.setText(site['name'] or '')
            self.ps_lat_edit.setValue(site['latitude'] or 35.0)
            self.ps_lon_edit.setValue(site['longitude'] or 138.0)
            self.ps_alt_edit.setValue(site['altitude'] if site['altitude'] is not None else -500)
            self.ps_area_edit.setValue(site['area'] if site['area'] is not None else 0)
            self.ps_remarks_edit.setPlainText(site['remarks'] or '')
            self.ps_update_button.setEnabled(True)
            self.ps_delete_button.setEnabled(True)
    
    def _on_add_survey_site(self):
        """調査地を新規登録"""
        if self.ss_parent_combo.count() == 0:
            QMessageBox.warning(self, "エラー", "親調査地が登録されていません\n先に親調査地を登録してください")
            return
        
        name = self.ss_name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "入力エラー", "名称は必須項目です")
            return
        
        parent_site_id = self.ss_parent_combo.currentData()
        latitude = self.ss_lat_edit.value()
        longitude = self.ss_lon_edit.value()
        altitude = self.ss_alt_edit.value() if self.ss_alt_edit.value() > -500 else None
        area = self.ss_area_edit.value() if self.ss_area_edit.value() > 0 else None
        remarks = self.ss_remarks_edit.toPlainText().strip() or None
        
        site_id = self.survey_site_model.create(
            parent_site_id=parent_site_id,
            name=name,
            latitude=latitude,
            longitude=longitude,
            altitude=altitude,
            area=area,
            remarks=remarks
        )
        
        if site_id:
            QMessageBox.information(self, "成功", f"調査地を登録しました (ID: {site_id})")
            self._clear_survey_site_form()
            self.refresh()
        else:
            QMessageBox.critical(self, "エラー", "調査地の登録に失敗しました\n同じ名称が既に存在する可能性があります")
    
    def _on_update_survey_site(self):
        """調査地を更新"""
        selected = self.ss_table.selectedItems()
        if not selected:
            return
        
        site_id = int(self.ss_table.item(selected[0].row(), 0).text())
        
        name = self.ss_name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "入力エラー", "名称は必須項目です")
            return
        
        success = self.survey_site_model.update(
            site_id,
            parent_site_id=self.ss_parent_combo.currentData(),
            name=name,
            latitude=self.ss_lat_edit.value(),
            longitude=self.ss_lon_edit.value(),
            altitude=self.ss_alt_edit.value() if self.ss_alt_edit.value() > -500 else None,
            area=self.ss_area_edit.value() if self.ss_area_edit.value() > 0 else None,
            remarks=self.ss_remarks_edit.toPlainText().strip() or None
        )
        
        if success:
            QMessageBox.information(self, "成功", "調査地を更新しました")
            self._clear_survey_site_form()
            self.refresh()
        else:
            QMessageBox.critical(self, "エラー", "調査地の更新に失敗しました")
    
    def _on_delete_survey_site(self):
        """調査地を削除"""
        selected = self.ss_table.selectedItems()
        if not selected:
            return
        
        site_id = int(self.ss_table.item(selected[0].row(), 0).text())
        site_name = self.ss_table.item(selected[0].row(), 2).text()
        
        reply = QMessageBox.question(
            self,
            "確認",
            f"調査地「{site_name}」を削除しますか？\n（論理削除されます）",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success = self.survey_site_model.delete(site_id)
            
            if success:
                QMessageBox.information(self, "成功", "調査地を削除しました")
                self._clear_survey_site_form()
                self.refresh()
            else:
                QMessageBox.critical(self, "エラー", "調査地の削除に失敗しました")
    
    def _clear_survey_site_form(self):
        """調査地フォームをクリア"""
        self.ss_name_edit.clear()
        self.ss_lat_edit.setValue(35.0)
        self.ss_lon_edit.setValue(138.0)
        self.ss_alt_edit.setValue(-500)
        self.ss_area_edit.setValue(0)
        self.ss_remarks_edit.clear()
        self.ss_update_button.setEnabled(False)
        self.ss_delete_button.setEnabled(False)
        self.ss_table.clearSelection()
    
    def _on_survey_site_selected(self):
        """調査地が選択された"""
        selected = self.ss_table.selectedItems()
        if not selected:
            return
        
        row = selected[0].row()
        site_id = int(self.ss_table.item(row, 0).text())
        site = self.survey_site_model.get_by_id(site_id)
        
        if site:
            # 親調査地を選択
            index = self.ss_parent_combo.findData(site['parent_site_id'])
            if index >= 0:
                self.ss_parent_combo.setCurrentIndex(index)
            
            self.ss_name_edit.setText(site['name'] or '')
            self.ss_lat_edit.setValue(site['latitude'] or 35.0)
            self.ss_lon_edit.setValue(site['longitude'] or 138.0)
            self.ss_alt_edit.setValue(site['altitude'] if site['altitude'] is not None else -500)
            self.ss_area_edit.setValue(site['area'] if site['area'] is not None else 0)
            self.ss_remarks_edit.setPlainText(site['remarks'] or '')
            self.ss_update_button.setEnabled(True)
            self.ss_delete_button.setEnabled(True)