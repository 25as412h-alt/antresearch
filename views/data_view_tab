"""
データ入力タブ (Phase 2 完全版)
調査イベント、植生データ、アリ類データの入力機能を含む
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QTabWidget, QGroupBox, QFormLayout, QLineEdit,
                               QDoubleSpinBox, QTextEdit, QComboBox, QLabel,
                               QTableWidget, QTableWidgetItem, QMessageBox,
                               QHeaderView, QDateEdit, QSpinBox, QCompleter)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QDoubleValidator
import logging
from datetime import date

from models.parent_site import ParentSite
from models.survey_site import SurveySite
from models.survey_event import SurveyEvent
from models.species import Species
from models.ant_record import AntRecord
from models.vegetation import VegetationData

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
        self.survey_event_model = SurveyEvent(self.conn)
        self.species_model = Species(self.conn)
        self.ant_record_model = AntRecord(self.conn)
        self.vegetation_model = VegetationData(self.conn)
        
        # 選択中のID
        self.selected_parent_site_id = None
        self.selected_survey_site_id = None
        self.selected_event_id = None
        
        self._init_ui()
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
        
        # 各タブを追加
        self.sub_tab_widget.addTab(self._create_parent_site_tab(), "親調査地")
        self.sub_tab_widget.addTab(self._create_survey_site_tab(), "調査地")
        self.sub_tab_widget.addTab(self._create_survey_event_tab(), "調査イベント")
        self.sub_tab_widget.addTab(self._create_vegetation_tab(), "植生データ")
        self.sub_tab_widget.addTab(self._create_ant_data_tab(), "アリ類データ")
    
    def _create_parent_site_tab(self):
        """親調査地タブ - 既存コードと同じ"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 入力フォーム
        form_group = QGroupBox("親調査地 登録・編集")
        form_layout = QFormLayout()
        
        # 名称（必須）
        self.ps_name_label = QLabel("名称:")
        self.ps_name_label.setProperty("required", True)
        self.ps_name_edit = QLineEdit()
        self.ps_name_edit.setPlaceholderText("例: 中部_南信")
        form_layout.addRow(self.ps_name_label, self.ps_name_edit)
        
        # 緯度（必須）
        lat_layout = QHBoxLayout()
        self.ps_lat_label = QLabel("緯度:")
        self.ps_lat_label.setProperty("required", True)
        self.ps_lat_edit = QDoubleSpinBox()
        self.ps_lat_edit.setRange(20.0, 46.0)
        self.ps_lat_edit.setDecimals(6)
        self.ps_lat_edit.setSingleStep(0.001)
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
        lon_layout.addWidget(self.ps_lon_edit)
        lon_layout.addWidget(QLabel("°E"))
        lon_layout.addStretch()
        form_layout.addRow(self.ps_lon_label, lon_layout)
        
        # 標高
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
        
        # 面積
        area_layout = QHBoxLayout()
        self.ps_area_edit = QDoubleSpinBox()
        self.ps_area_edit.setRange(0, 999999999)
        self.ps_area_edit.setDecimals(1)
        self.ps_area_edit.setSpecialValueText("未設定")
        area_layout.addWidget(self.ps_area_edit)
        area_layout.addWidget(QLabel("m²"))
        area_layout.addStretch()
        form_layout.addRow("面積:", area_layout)
        
        # 備考
        self.ps_remarks_edit = QTextEdit()
        self.ps_remarks_edit.setMaximumHeight(80)
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
        self.ps_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.ps_table.setAlternatingRowColors(True)
        self.ps_table.itemSelectionChanged.connect(self._on_parent_site_selected)
        
        list_layout.addWidget(self.ps_table)
        list_group.setLayout(list_layout)
        layout.addWidget(list_group)
        
        return widget
    
    def _create_survey_site_tab(self):
        """調査地タブ - 既存コードと同じ（省略）"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        form_group = QGroupBox("調査地 登録・編集")
        form_layout = QFormLayout()
        
        # 親調査地選択
        self.ss_parent_label = QLabel("親調査地:")
        self.ss_parent_label.setProperty("required", True)
        self.ss_parent_combo = QComboBox()
        form_layout.addRow(self.ss_parent_label, self.ss_parent_combo)
        
        # 名称
        self.ss_name_label = QLabel("名称:")
        self.ss_name_label.setProperty("required", True)
        self.ss_name_edit = QLineEdit()
        form_layout.addRow(self.ss_name_label, self.ss_name_edit)
        
        # 緯度経度（簡略版）
        self.ss_lat_label = QLabel("緯度:")
        self.ss_lat_label.setProperty("required", True)
        self.ss_lat_edit = QDoubleSpinBox()
        self.ss_lat_edit.setRange(20.0, 46.0)
        self.ss_lat_edit.setDecimals(6)
        form_layout.addRow(self.ss_lat_label, self.ss_lat_edit)
        
        self.ss_lon_label = QLabel("経度:")
        self.ss_lon_label.setProperty("required", True)
        self.ss_lon_edit = QDoubleSpinBox()
        self.ss_lon_edit.setRange(122.0, 154.0)
        self.ss_lon_edit.setDecimals(6)
        form_layout.addRow(self.ss_lon_label, self.ss_lon_edit)
        
        self.ss_alt_edit = QDoubleSpinBox()
        self.ss_alt_edit.setRange(-500, 4000)
        self.ss_alt_edit.setSpecialValueText("未設定")
        self.ss_alt_edit.setValue(-500)
        form_layout.addRow("標高:", self.ss_alt_edit)
        
        self.ss_area_edit = QDoubleSpinBox()
        self.ss_area_edit.setRange(0, 999999999)
        self.ss_area_edit.setSpecialValueText("未設定")
        form_layout.addRow("面積:", self.ss_area_edit)
        
        self.ss_remarks_edit = QTextEdit()
        self.ss_remarks_edit.setMaximumHeight(80)
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
            "ID", "親調査地", "名称", "緯度", "経度", "標高", "面積", "備考"
        ])
        self.ss_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.ss_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.ss_table.setAlternatingRowColors(True)
        self.ss_table.itemSelectionChanged.connect(self._on_survey_site_selected)
        
        list_layout.addWidget(self.ss_table)
        list_group.setLayout(list_layout)
        layout.addWidget(list_group)
        
        return widget
    
    def _create_survey_event_tab(self):
        """調査イベントタブ"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        form_group = QGroupBox("調査イベント 登録・編集")
        form_layout = QFormLayout()
        
        # 調査地選択（必須）
        self.se_site_label = QLabel("調査地:")
        self.se_site_label.setProperty("required", True)
        self.se_site_combo = QComboBox()
        form_layout.addRow(self.se_site_label, self.se_site_combo)
        
        # 調査サイト（必須）
        self.se_survey_site_label = QLabel("調査サイト:")
        self.se_survey_site_label.setProperty("required", True)
        self.se_survey_site_edit = QLineEdit()
        self.se_survey_site_edit.setPlaceholderText("例: Plot1, A地点")
        form_layout.addRow(self.se_survey_site_label, self.se_survey_site_edit)
        
        # 調査年月日（必須）
        self.se_date_label = QLabel("調査年月日:")
        self.se_date_label.setProperty("required", True)
        self.se_date_edit = QDateEdit()
        self.se_date_edit.setCalendarPopup(True)
        self.se_date_edit.setDate(QDate.currentDate())
        self.se_date_edit.setDisplayFormat("yyyy-MM-dd")
        form_layout.addRow(self.se_date_label, self.se_date_edit)
        
        # 調査者名
        self.se_surveyor_edit = QLineEdit()
        form_layout.addRow("調査者名:", self.se_surveyor_edit)
        
        # 天候
        self.se_weather_combo = QComboBox()
        self.se_weather_combo.addItems(["", "晴れ", "曇り", "雨", "雪"])
        form_layout.addRow("天候:", self.se_weather_combo)
        
        # 気温
        temp_layout = QHBoxLayout()
        self.se_temperature_spin = QDoubleSpinBox()
        self.se_temperature_spin.setRange(-30, 50)
        self.se_temperature_spin.setDecimals(1)
        self.se_temperature_spin.setSpecialValueText("未測定")
        self.se_temperature_spin.setValue(-30)
        temp_layout.addWidget(self.se_temperature_spin)
        temp_layout.addWidget(QLabel("℃"))
        temp_layout.addStretch()
        form_layout.addRow("気温:", temp_layout)
        
        # 備考
        self.se_remarks_edit = QTextEdit()
        self.se_remarks_edit.setMaximumHeight(80)
        form_layout.addRow("備考:", self.se_remarks_edit)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        # ボタン
        button_layout = QHBoxLayout()
        self.se_add_button = QPushButton("新規登録")
        self.se_add_button.setObjectName("primaryButton")
        self.se_add_button.clicked.connect(self._on_add_survey_event)
        button_layout.addWidget(self.se_add_button)
        
        self.se_update_button = QPushButton("更新")
        self.se_update_button.clicked.connect(self._on_update_survey_event)
        self.se_update_button.setEnabled(False)
        button_layout.addWidget(self.se_update_button)
        
        self.se_delete_button = QPushButton("削除")
        self.se_delete_button.setObjectName("dangerButton")
        self.se_delete_button.clicked.connect(self._on_delete_survey_event)
        self.se_delete_button.setEnabled(False)
        button_layout.addWidget(self.se_delete_button)
        
        self.se_clear_button = QPushButton("クリア")
        self.se_clear_button.setObjectName("secondaryButton")
        self.se_clear_button.clicked.connect(self._clear_survey_event_form)
        button_layout.addWidget(self.se_clear_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # 一覧テーブル
        list_group = QGroupBox("調査イベント 一覧")
        list_layout = QVBoxLayout()
        
        self.se_table = QTableWidget()
        self.se_table.setColumnCount(8)
        self.se_table.setHorizontalHeaderLabels([
            "ID", "調査地", "サイト", "調査日", "調査者", "天候", "気温", "備考"
        ])
        self.se_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.se_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.se_table.setAlternatingRowColors(True)
        self.se_table.itemSelectionChanged.connect(self._on_survey_event_selected)
        
        list_layout.addWidget(self.se_table)
        list_group.setLayout(list_layout)
        layout.addWidget(list_group)
        
        return widget
    
    def _create_vegetation_tab(self):
        """植生データタブ（簡略版）"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 調査イベント選択
        event_group = QGroupBox("調査イベント選択")
        event_layout = QFormLayout()
        
        self.veg_event_label = QLabel("調査イベント:")
        self.veg_event_label.setProperty("required", True)
        self.veg_event_combo = QComboBox()
        event_layout.addRow(self.veg_event_label, self.veg_event_combo)
        
        self.veg_load_button = QPushButton("データ読み込み")
        self.veg_load_button.clicked.connect(self._load_vegetation_data)
        event_layout.addRow("", self.veg_load_button)
        
        event_group.setLayout(event_layout)
        layout.addWidget(event_group)
        
        # 植生データフォーム
        form_group = QGroupBox("植生データ 登録・編集")
        form_layout = QFormLayout()
        
        # 優占種
        self.veg_dominant_tree_edit = QLineEdit()
        form_layout.addRow("優占高木層樹種:", self.veg_dominant_tree_edit)
        
        self.veg_dominant_sasa_edit = QLineEdit()
        form_layout.addRow("優占ササ種:", self.veg_dominant_sasa_edit)
        
        # 被度（主要項目のみ）
        self.veg_canopy_coverage_spin = QDoubleSpinBox()
        self.veg_canopy_coverage_spin.setRange(0, 100)
        self.veg_canopy_coverage_spin.setSuffix(" %")
        form_layout.addRow("高木層樹冠被度:", self.veg_canopy_coverage_spin)
        
        self.veg_sasa_coverage_spin = QDoubleSpinBox()
        self.veg_sasa_coverage_spin.setRange(0, 100)
        self.veg_sasa_coverage_spin.setSuffix(" %")
        form_layout.addRow("ササ被度:", self.veg_sasa_coverage_spin)
        
        # 段階評価
        self.veg_light_spin = QSpinBox()
        self.veg_light_spin.setRange(1, 5)
        form_layout.addRow("光条件(1-5):", self.veg_light_spin)
        
        self.veg_moisture_spin = QSpinBox()
        self.veg_moisture_spin.setRange(1, 5)
        form_layout.addRow("土壌湿潤(1-5):", self.veg_moisture_spin)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        # ボタン
        button_layout = QHBoxLayout()
        self.veg_save_button = QPushButton("保存")
        self.veg_save_button.setObjectName("primaryButton")
        self.veg_save_button.clicked.connect(self._save_vegetation_data)
        button_layout.addWidget(self.veg_save_button)
        
        self.veg_clear_button = QPushButton("クリア")
        self.veg_clear_button.setObjectName("secondaryButton")
        self.veg_clear_button.clicked.connect(self._clear_vegetation_form)
        button_layout.addWidget(self.veg_clear_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        layout.addStretch()
        
        return widget
    
    def _create_ant_data_tab(self):
        """アリ類データタブ"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 調査イベント選択
        event_group = QGroupBox("調査イベント選択")
        event_layout = QFormLayout()
        
        self.ant_event_label = QLabel("調査イベント:")
        self.ant_event_label.setProperty("required", True)
        self.ant_event_combo = QComboBox()
        event_layout.addRow(self.ant_event_label, self.ant_event_combo)
        
        self.ant_load_button = QPushButton("データ読み込み")
        self.ant_load_button.clicked.connect(self._load_ant_records)
        event_layout.addRow("", self.ant_load_button)
        
        event_group.setLayout(event_layout)
        layout.addWidget(event_group)
        
        # アリ類データ入力
        input_group = QGroupBox("アリ類データ 追加")
        input_layout = QFormLayout()
        
        # 種名選択（オートコンプリート付き）
        self.ant_species_label = QLabel("種名:")
        self.ant_species_label.setProperty("required", True)
        self.ant_species_combo = QComboBox()
        self.ant_species_combo.setEditable(True)
        input_layout.addRow(self.ant_species_label, self.ant_species_combo)
        
        # 個体数
        self.ant_count_label = QLabel("個体数:")
        self.ant_count_label.setProperty("required", True)
        self.ant_count_spin = QSpinBox()
        self.ant_count_spin.setRange(0, 999999)
        input_layout.addRow(self.ant_count_label, self.ant_count_spin)
        
        # 備考
        self.ant_remarks_edit = QLineEdit()
        input_layout.addRow("備考:", self.ant_remarks_edit)
        
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)
        
        # ボタン
        button_layout = QHBoxLayout()
        self.ant_add_button = QPushButton("追加")
        self.ant_add_button.setObjectName("primaryButton")
        self.ant_add_button.clicked.connect(self._add_ant_record)
        button_layout.addWidget(self.ant_add_button)
        
        self.ant_update_button = QPushButton("更新")
        self.ant_update_button.clicked.connect(self._update_ant_record)
        self.ant_update_button.setEnabled(False)
        button_layout.addWidget(self.ant_update_button)
        
        self.ant_delete_button = QPushButton("削除")
        self.ant_delete_button.setObjectName("dangerButton")
        self.ant_delete_button.clicked.connect(self._delete_ant_record)
        self.ant_delete_button.setEnabled(False)
        button_layout.addWidget(self.ant_delete_button)
        
        self.ant_clear_button = QPushButton("クリア")
        self.ant_clear_button.setObjectName("secondaryButton")
        self.ant_clear_button.clicked.connect(self._clear_ant_form)
        button_layout.addWidget(self.ant_clear_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # 出現記録一覧
        list_group = QGroupBox("出現記録 一覧")
        list_layout = QVBoxLayout()
        
        self.ant_table = QTableWidget()
        self.ant_table.setColumnCount(5)
        self.ant_table.setHorizontalHeaderLabels([
            "ID", "学名", "和名", "個体数", "備考"
        ])
        self.ant_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.ant_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.ant_table.setAlternatingRowColors(True)
        self.ant_table.itemSelectionChanged.connect(self._on_ant_record_selected)
        
        list_layout.addWidget(self.ant_table)
        list_group.setLayout(list_layout)
        layout.addWidget(list_group)
        
        return widget
    
    def refresh(self):
        """表示更新"""
        self._load_parent_sites()
        self._load_survey_sites()
        self._load_survey_events()
        self._update_parent_site_combo()
        self._update_survey_site_combo()
        self._update_event_combos()
        self._update_species_combo()
        logger.info("Data input tab refreshed")
    
    # 親調査地関連メソッド（既存コードと同じ）
    def _load_parent_sites(self):
        sites = self.parent_site_model.get_all()
        self.ps_table.setRowCount(len(sites))
        for row, site in enumerate(sites):
            self.ps_table.setItem(row, 0, QTableWidgetItem(str(site['id'])))
            self.ps_table.setItem(row, 1, QTableWidgetItem(site['name'] or ''))
            self.ps_table.setItem(row, 2, QTableWidgetItem(f"{site['latitude']:.6f}" if site['latitude'] else ''))
            self.ps_table.setItem(row, 3, QTableWidgetItem(f"{site['longitude']:.6f}" if site['longitude'] else ''))
            self.ps_table.setItem(row, 4, QTableWidgetItem(f"{site['altitude']:.1f}" if site['altitude'] else ''))
            self.ps_table.setItem(row, 5, QTableWidgetItem(f"{site['area']:.1f}" if site['area'] else ''))
            self.ps_table.setItem(row, 6, QTableWidgetItem((site['remarks'] or '')[:50]))
    
    def _on_add_parent_site(self):
        name = self.ps_name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "入力エラー", "名称は必須項目です")
            return
        
        site_id = self.parent_site_model.create(
            name=name,
            latitude=self.ps_lat_edit.value(),
            longitude=self.ps_lon_edit.value(),
            altitude=self.ps_alt_edit.value() if self.ps_alt_edit.value() > -500 else None,
            area=self.ps_area_edit.value() if self.ps_area_edit.value() > 0 else None,
            remarks=self.ps_remarks_edit.toPlainText().strip() or None
        )
        
        if site_id:
            QMessageBox.information(self, "成功", f"親調査地を登録しました (ID: {site_id})")
            self._clear_parent_site_form()
            self.refresh()
        else:
            QMessageBox.critical(self, "エラー", "親調査地の登録に失敗しました")
    
    def _on_update_parent_site(self):
        if not self.selected_parent_site_id:
            return
        
        name = self.ps_name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "入力エラー", "名称は必須項目です")
            return
        
        success = self.parent_site_model.update(
            self.selected_parent_site_id,
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
        if not self.selected_parent_site_id:
            return
        
        reply = QMessageBox.question(self, "確認", "親調査地を削除しますか？",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            if self.parent_site_model.delete(self.selected_parent_site_id):
                QMessageBox.information(self, "成功", "親調査地を削除しました")
                self._clear_parent_site_form()
                self.refresh()
            else:
                QMessageBox.critical(self, "エラー", "親調査地の削除に失敗しました")
    
    def _clear_parent_site_form(self):
        self.ps_name_edit.clear()
        self.ps_lat_edit.setValue(35.0)
        self.ps_lon_edit.setValue(138.0)
        self.ps_alt_edit.setValue(-500)
        self.ps_area_edit.setValue(0)
        self.ps_remarks_edit.clear()
        self.ps_update_button.setEnabled(False)
        self.ps_delete_button.setEnabled(False)
        self.selected_parent_site_id = None
        self.ps_table.clearSelection()
    
    def _on_parent_site_selected(self):
        selected = self.ps_table.selectedItems()
        if not selected:
            return
        
        row = selected[0].row()
        site_id = int(self.ps_table.item(row, 0).text())
        site = self.parent_site_model.get_by_id(site_id)
        
        if site:
            self.selected_parent_site_id = site_id
            self.ps_name_edit.setText(site['name'] or '')
            self.ps_lat_edit.setValue(site['latitude'] or 35.0)
            self.ps_lon_edit.setValue(site['longitude'] or 138.0)
            self.ps_alt_edit.setValue(site['altitude'] if site['altitude'] is not None else -500)
            self.ps_area_edit.setValue(site['area'] if site['area'] is not None else 0)
            self.ps_remarks_edit.setPlainText(site['remarks'] or '')
            self.ps_update_button.setEnabled(True)
            self.ps_delete_button.setEnabled(True)
    
    # 調査地関連メソッド（省略 - 親調査地と同様の実装）
    def _load_survey_sites(self):
        sites = self.survey_site_model.get_all()
        self.ss_table.setRowCount(len(sites))
        for row, site in enumerate(sites):
            self.ss_table.setItem(row, 0, QTableWidgetItem(str(site['id'])))
            self.ss_table.setItem(row, 1, QTableWidgetItem(site.get('parent_site_name', '')))
            self.ss_table.setItem(row, 2, QTableWidgetItem(site['name'] or ''))
            self.ss_table.setItem(row, 3, QTableWidgetItem(f"{site['latitude']:.6f}" if site['latitude'] else ''))
            self.ss_table.setItem(row, 4, QTableWidgetItem(f"{site['longitude']:.6f}" if site['longitude'] else ''))
            self.ss_table.setItem(row, 5, QTableWidgetItem(f"{site['altitude']:.1f}" if site['altitude'] else ''))
            self.ss_table.setItem(row, 6, QTableWidgetItem(f"{site['area']:.1f}" if site['area'] else ''))
            self.ss_table.setItem(row, 7, QTableWidgetItem((site['remarks'] or '')[:50]))
    
    def _update_parent_site_combo(self):
        self.ss_parent_combo.clear()
        sites = self.parent_site_model.get_all()
        for site in sites:
            self.ss_parent_combo.addItem(site['name'], site['id'])
    
    def _update_survey_site_combo(self):
        self.se_site_combo.clear()
        sites = self.survey_site_model.get_all()
        for site in sites:
            display_name = f"{site.get('parent_site_name', '')} - {site['name']}"
            self.se_site_combo.addItem(display_name, site['id'])
    
    def _on_add_survey_site(self):
        if self.ss_parent_combo.count() == 0:
            QMessageBox.warning(self, "エラー", "親調査地が登録されていません")
            return
        
        name = self.ss_name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "入力エラー", "名称は必須項目です")
            return
        
        site_id = self.survey_site_model.create(
            parent_site_id=self.ss_parent_combo.currentData(),
            name=name,
            latitude=self.ss_lat_edit.value(),
            longitude=self.ss_lon_edit.value(),
            altitude=self.ss_alt_edit.value() if self.ss_alt_edit.value() > -500 else None,
            area=self.ss_area_edit.value() if self.ss_area_edit.value() > 0 else None,
            remarks=self.ss_remarks_edit.toPlainText().strip() or None
        )
        
        if site_id:
            QMessageBox.information(self, "成功", f"調査地を登録しました (ID: {site_id})")
            self._clear_survey_site_form()
            self.refresh()
        else:
            QMessageBox.critical(self, "エラー", "調査地の登録に失敗しました")
    
    def _on_update_survey_site(self):
        if not self.selected_survey_site_id:
            return
        
        name = self.ss_name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "入力エラー", "名称は必須項目です")
            return
        
        success = self.survey_site_model.update(
            self.selected_survey_site_id,
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
        if not self.selected_survey_site_id:
            return
        
        reply = QMessageBox.question(self, "確認", "調査地を削除しますか？",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            if self.survey_site_model.delete(self.selected_survey_site_id):
                QMessageBox.information(self, "成功", "調査地を削除しました")
                self._clear_survey_site_form()
                self.refresh()
            else:
                QMessageBox.critical(self, "エラー", "調査地の削除に失敗しました")
    
    def _clear_survey_site_form(self):
        self.ss_name_edit.clear()
        self.ss_lat_edit.setValue(35.0)
        self.ss_lon_edit.setValue(138.0)
        self.ss_alt_edit.setValue(-500)
        self.ss_area_edit.setValue(0)
        self.ss_remarks_edit.clear()
        self.ss_update_button.setEnabled(False)
        self.ss_delete_button.setEnabled(False)
        self.selected_survey_site_id = None
        self.ss_table.clearSelection()
    
    def _on_survey_site_selected(self):
        selected = self.ss_table.selectedItems()
        if not selected:
            return
        
        row = selected[0].row()
        site_id = int(self.ss_table.item(row, 0).text())
        site = self.survey_site_model.get_by_id(site_id)
        
        if site:
            self.selected_survey_site_id = site_id
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
    
    # 調査イベント関連メソッド
    def _load_survey_events(self):
        events = self.survey_event_model.get_all()
        self.se_table.setRowCount(len(events))
        for row, event in enumerate(events):
            self.se_table.setItem(row, 0, QTableWidgetItem(str(event['id'])))
            self.se_table.setItem(row, 1, QTableWidgetItem(event.get('survey_site_name', '')))
            self.se_table.setItem(row, 2, QTableWidgetItem(event['survey_site'] or ''))
            self.se_table.setItem(row, 3, QTableWidgetItem(event['survey_date'] or ''))
            self.se_table.setItem(row, 4, QTableWidgetItem(event['surveyor_name'] or ''))
            self.se_table.setItem(row, 5, QTableWidgetItem(event['weather'] or ''))
            self.se_table.setItem(row, 6, QTableWidgetItem(f"{event['temperature']:.1f}" if event['temperature'] else ''))
            self.se_table.setItem(row, 7, QTableWidgetItem((event['remarks'] or '')[:50]))
    
    def _update_event_combos(self):
        events = self.survey_event_model.get_all()
        
        # 植生データ用
        self.veg_event_combo.clear()
        # アリ類データ用
        self.ant_event_combo.clear()
        
        for event in events:
            display = f"{event.get('survey_site_name', '')} - {event['survey_date']}"
            self.veg_event_combo.addItem(display, event['id'])
            self.ant_event_combo.addItem(display, event['id'])
    
    def _on_add_survey_event(self):
        if self.se_site_combo.count() == 0:
            QMessageBox.warning(self, "エラー", "調査地が登録されていません")
            return
        
        survey_site = self.se_survey_site_edit.text().strip()
        if not survey_site:
            QMessageBox.warning(self, "入力エラー", "調査サイトは必須項目です")
            return
        
        survey_date = self.se_date_edit.date().toPython()
        
        event_id = self.survey_event_model.create(
            survey_site_id=self.se_site_combo.currentData(),
            survey_site=survey_site,
            survey_date=survey_date,
            surveyor_name=self.se_surveyor_edit.text().strip() or None,
            weather=self.se_weather_combo.currentText() or None,
            temperature=self.se_temperature_spin.value() if self.se_temperature_spin.value() > -30 else None,
            remarks=self.se_remarks_edit.toPlainText().strip() or None
        )
        
        if event_id:
            QMessageBox.information(self, "成功", f"調査イベントを登録しました (ID: {event_id})")
            self._clear_survey_event_form()
            self.refresh()
        else:
            QMessageBox.critical(self, "エラー", "調査イベントの登録に失敗しました\n同じ日付の調査が既に存在する可能性があります")
    
    def _on_update_survey_event(self):
        if not self.selected_event_id:
            return
        
        survey_site = self.se_survey_site_edit.text().strip()
        if not survey_site:
            QMessageBox.warning(self, "入力エラー", "調査サイトは必須項目です")
            return
        
        success = self.survey_event_model.update(
            self.selected_event_id,
            survey_site_id=self.se_site_combo.currentData(),
            survey_site=survey_site,
            survey_date=self.se_date_edit.date().toPython(),
            surveyor_name=self.se_surveyor_edit.text().strip() or None,
            weather=self.se_weather_combo.currentText() or None,
            temperature=self.se_temperature_spin.value() if self.se_temperature_spin.value() > -30 else None,
            remarks=self.se_remarks_edit.toPlainText().strip() or None
        )
        
        if success:
            QMessageBox.information(self, "成功", "調査イベントを更新しました")
            self._clear_survey_event_form()
            self.refresh()
        else:
            QMessageBox.critical(self, "エラー", "調査イベントの更新に失敗しました")
    
    def _on_delete_survey_event(self):
        if not self.selected_event_id:
            return
        
        reply = QMessageBox.question(self, "確認", "調査イベントを削除しますか？",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            if self.survey_event_model.delete(self.selected_event_id):
                QMessageBox.information(self, "成功", "調査イベントを削除しました")
                self._clear_survey_event_form()
                self.refresh()
            else:
                QMessageBox.critical(self, "エラー", "調査イベントの削除に失敗しました")
    
    def _clear_survey_event_form(self):
        self.se_survey_site_edit.clear()
        self.se_date_edit.setDate(QDate.currentDate())
        self.se_surveyor_edit.clear()
        self.se_weather_combo.setCurrentIndex(0)
        self.se_temperature_spin.setValue(-30)
        self.se_remarks_edit.clear()
        self.se_update_button.setEnabled(False)
        self.se_delete_button.setEnabled(False)
        self.selected_event_id = None
        self.se_table.clearSelection()
    
    def _on_survey_event_selected(self):
        selected = self.se_table.selectedItems()
        if not selected:
            return
        
        row = selected[0].row()
        event_id = int(self.se_table.item(row, 0).text())
        event = self.survey_event_model.get_by_id(event_id)
        
        if event:
            self.selected_event_id = event_id
            index = self.se_site_combo.findData(event['survey_site_id'])
            if index >= 0:
                self.se_site_combo.setCurrentIndex(index)
            self.se_survey_site_edit.setText(event['survey_site'] or '')
            
            from datetime import datetime
            date_obj = datetime.strptime(event['survey_date'], '%Y-%m-%d').date()
            self.se_date_edit.setDate(QDate(date_obj.year, date_obj.month, date_obj.day))
            
            self.se_surveyor_edit.setText(event['surveyor_name'] or '')
            if event['weather']:
                index = self.se_weather_combo.findText(event['weather'])
                if index >= 0:
                    self.se_weather_combo.setCurrentIndex(index)
            self.se_temperature_spin.setValue(event['temperature'] if event['temperature'] else -30)
            self.se_remarks_edit.setPlainText(event['remarks'] or '')
            self.se_update_button.setEnabled(True)
            self.se_delete_button.setEnabled(True)
    
    # 植生データ関連メソッド
    def _load_vegetation_data(self):
        if self.veg_event_combo.count() == 0:
            QMessageBox.warning(self, "エラー", "調査イベントが選択されていません")
            return
        
        event_id = self.veg_event_combo.currentData()
        veg_data = self.vegetation_model.get_by_event(event_id)
        
        if veg_data:
            self.veg_dominant_tree_edit.setText(veg_data.get('dominant_tree', '') or '')
            self.veg_dominant_sasa_edit.setText(veg_data.get('dominant_sasa', '') or '')
            self.veg_canopy_coverage_spin.setValue(veg_data.get('canopy_coverage', 0) or 0)
            self.veg_sasa_coverage_spin.setValue(veg_data.get('sasa_coverage', 0) or 0)
            self.veg_light_spin.setValue(veg_data.get('light_condition', 3) or 3)
            self.veg_moisture_spin.setValue(veg_data.get('soil_moisture', 3) or 3)
        else:
            self._clear_vegetation_form()
    
    def _save_vegetation_data(self):
        if self.veg_event_combo.count() == 0:
            QMessageBox.warning(self, "エラー", "調査イベントが選択されていません")
            return
        
        event_id = self.veg_event_combo.currentData()
        
        # 既存データがあるかチェック
        existing = self.vegetation_model.get_by_event(event_id)
        
        data = {
            'dominant_tree': self.veg_dominant_tree_edit.text().strip() or None,
            'dominant_sasa': self.veg_dominant_sasa_edit.text().strip() or None,
            'canopy_coverage': self.veg_canopy_coverage_spin.value() if self.veg_canopy_coverage_spin.value() > 0 else None,
            'sasa_coverage': self.veg_sasa_coverage_spin.value() if self.veg_sasa_coverage_spin.value() > 0 else None,
            'light_condition': self.veg_light_spin.value(),
            'soil_moisture': self.veg_moisture_spin.value()
        }
        
        if existing:
            success = self.vegetation_model.update(event_id, **data)
            if success:
                QMessageBox.information(self, "成功", "植生データを更新しました")
            else:
                QMessageBox.critical(self, "エラー", "植生データの更新に失敗しました")
        else:
            veg_id = self.vegetation_model.create(event_id, **data)
            if veg_id:
                QMessageBox.information(self, "成功", "植生データを登録しました")
            else:
                QMessageBox.critical(self, "エラー", "植生データの登録に失敗しました")
    
    def _clear_vegetation_form(self):
        self.veg_dominant_tree_edit.clear()
        self.veg_dominant_sasa_edit.clear()
        self.veg_canopy_coverage_spin.setValue(0)
        self.veg_sasa_coverage_spin.setValue(0)
        self.veg_light_spin.setValue(3)
        self.veg_moisture_spin.setValue(3)
    
    # アリ類データ関連メソッド
    def _update_species_combo(self):
        species_list = self.species_model.get_all()
        self.ant_species_combo.clear()
        
        for species in species_list:
            display = f"{species['scientific_name']}"
            if species['ja_name']:
                display += f" ({species['ja_name']})"
            self.ant_species_combo.addItem(display, species['id'])
    
    def _load_ant_records(self):
        if self.ant_event_combo.count() == 0:
            QMessageBox.warning(self, "エラー", "調査イベントが選択されていません")
            return
        
        event_id = self.ant_event_combo.currentData()
        records = self.ant_record_model.get_by_event(event_id)
        
        self.ant_table.setRowCount(len(records))
        for row, record in enumerate(records):
            self.ant_table.setItem(row, 0, QTableWidgetItem(str(record['id'])))
            self.ant_table.setItem(row, 1, QTableWidgetItem(record.get('scientific_name', '')))
            self.ant_table.setItem(row, 2, QTableWidgetItem(record.get('ja_name', '')))
            self.ant_table.setItem(row, 3, QTableWidgetItem(str(record['count'])))
            self.ant_table.setItem(row, 4, QTableWidgetItem(record['remarks'] or ''))
    
    def _add_ant_record(self):
        if self.ant_event_combo.count() == 0:
            QMessageBox.warning(self, "エラー", "調査イベントが選択されていません")
            return
        
        if self.ant_species_combo.count() == 0:
            QMessageBox.warning(self, "エラー", "種名マスタが登録されていません")
            return
        
        event_id = self.ant_event_combo.currentData()
        species_id = self.ant_species_combo.currentData()
        count = self.ant_count_spin.value()
        remarks = self.ant_remarks_edit.text().strip() or None
        
        record_id = self.ant_record_model.create(event_id, species_id, count, remarks)
        
        if record_id:
            QMessageBox.information(self, "成功", "アリ類記録を追加しました")
            self._clear_ant_form()
            self._load_ant_records()
        else:
            QMessageBox.critical(self, "エラー", "アリ類記録の追加に失敗しました\n同じ種が既に登録されている可能性があります")
    
    def _update_ant_record(self):
        selected = self.ant_table.selectedItems()
        if not selected:
            return
        
        row = selected[0].row()
        record_id = int(self.ant_table.item(row, 0).text())
        
        success = self.ant_record_model.update(
            record_id,
            species_id=self.ant_species_combo.currentData(),
            count=self.ant_count_spin.value(),
            remarks=self.ant_remarks_edit.text().strip() or None
        )
        
        if success:
            QMessageBox.information(self, "成功", "アリ類記録を更新しました")
            self._clear_ant_form()
            self._load_ant_records()
        else:
            QMessageBox.critical(self, "エラー", "アリ類記録の更新に失敗しました")
    
    def _delete_ant_record(self):
        selected = self.ant_table.selectedItems()
        if not selected:
            return
        
        row = selected[0].row()
        record_id = int(self.ant_table.item(row, 0).text())
        
        reply = QMessageBox.question(self, "確認", "このアリ類記録を削除しますか？",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            if self.ant_record_model.delete(record_id):
                QMessageBox.information(self, "成功", "アリ類記録を削除しました")
                self._clear_ant_form()
                self._load_ant_records()
            else:
                QMessageBox.critical(self, "エラー", "アリ類記録の削除に失敗しました")
    
    def _clear_ant_form(self):
        self.ant_count_spin.setValue(0)
        self.ant_remarks_edit.clear()
        self.ant_update_button.setEnabled(False)
        self.ant_delete_button.setEnabled(False)
        self.ant_table.clearSelection()
    
    def _on_ant_record_selected(self):
        selected = self.ant_table.selectedItems()
        if not selected:
            return
        
        row = selected[0].row()
        record_id = int(self.ant_table.item(row, 0).text())
        record = self.ant_record_model.get_by_id(record_id)
        
        if record:
            # 種名を選択
            index = self.ant_species_combo.findData(record['species_id'])
            if index >= 0:
                self.ant_species_combo.setCurrentIndex(index)
            
            self.ant_count_spin.setValue(record['count'])
            self.ant_remarks_edit.setText(record['remarks'] or '')
            self.ant_update_button.setEnabled(True)
            self.ant_delete_button.setEnabled(True)