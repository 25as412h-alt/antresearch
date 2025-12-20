"""
データ閲覧タブ
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                               QTableWidget, QTableWidgetItem, QHeaderView,
                               QGroupBox, QLineEdit, QLabel, QCheckBox,
                               QComboBox, QDateEdit, QTextEdit, QSplitter,
                               QTreeWidget, QTreeWidgetItem, QMessageBox)
from PySide6.QtCore import Qt, QDate
import logging
from datetime import datetime

from models.parent_site import ParentSite
from models.survey_site import SurveySite
from models.survey_event import SurveyEvent
from models.species import Species
from models.ant_record import AntRecord
from models.vegetation import VegetationData

logger = logging.getLogger(__name__)


class DataViewTab(QWidget):
    """データ閲覧タブ"""
    
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
        
        # 検索フィルタ
        filter_group = QGroupBox("検索・フィルタ")
        filter_layout = QVBoxLayout()
        
        # 検索バー
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("キーワード:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("調査地名、備考などで検索...")
        self.search_edit.textChanged.connect(self._on_search)
        search_layout.addWidget(self.search_edit)
        
        self.search_button = QPushButton("検索")
        self.search_button.clicked.connect(self._on_search)
        search_layout.addWidget(self.search_button)
        
        self.clear_search_button = QPushButton("クリア")
        self.clear_search_button.setObjectName("secondaryButton")
        self.clear_search_button.clicked.connect(self._clear_search)
        search_layout.addWidget(self.clear_search_button)
        
        filter_layout.addLayout(search_layout)
        
        # 表示オプション
        option_layout = QHBoxLayout()
        self.show_deleted_check = QCheckBox("削除済みを含める")
        self.show_deleted_check.stateChanged.connect(self._on_filter_changed)
        option_layout.addWidget(self.show_deleted_check)
        
        option_layout.addWidget(QLabel("表示:"))
        self.view_type_combo = QComboBox()
        self.view_type_combo.addItems([
            "調査イベント一覧",
            "親調査地一覧",
            "調査地一覧",
            "種別出現記録"
        ])
        self.view_type_combo.currentTextChanged.connect(self._on_view_type_changed)
        option_layout.addWidget(self.view_type_combo)
        
        option_layout.addStretch()
        filter_layout.addLayout(option_layout)
        
        filter_group.setLayout(filter_layout)
        main_layout.addWidget(filter_group)
        
        # スプリッター（一覧と詳細）
        splitter = QSplitter(Qt.Vertical)
        
        # 一覧テーブル
        list_group = QGroupBox("一覧")
        list_layout = QVBoxLayout()
        
        self.data_table = QTableWidget()
        self.data_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.data_table.setSelectionMode(QTableWidget.SingleSelection)
        self.data_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.data_table.setAlternatingRowColors(True)
        self.data_table.itemSelectionChanged.connect(self._on_row_selected)
        
        list_layout.addWidget(self.data_table)
        list_group.setLayout(list_layout)
        splitter.addWidget(list_group)
        
        # 詳細表示パネル
        detail_group = QGroupBox("詳細情報")
        detail_layout = QVBoxLayout()
        
        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        detail_layout.addWidget(self.detail_text)
        
        detail_group.setLayout(detail_layout)
        splitter.addWidget(detail_group)
        
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        
        main_layout.addWidget(splitter)
        
        # 統計サマリー
        stats_group = QGroupBox("統計サマリー")
        stats_layout = QHBoxLayout()
        
        self.stats_label = QLabel("統計情報を読み込み中...")
        stats_layout.addWidget(self.stats_label)
        
        self.show_stats_button = QPushButton("詳細統計を表示")
        self.show_stats_button.clicked.connect(self._show_detailed_stats)
        stats_layout.addWidget(self.show_stats_button)
        
        stats_layout.addStretch()
        stats_group.setLayout(stats_layout)
        main_layout.addWidget(stats_group)
    
    def refresh(self):
        """表示更新"""
        self._on_view_type_changed()
        self._update_statistics()
        logger.info("Data view tab refreshed")
    
    def _on_view_type_changed(self):
        """表示タイプ変更"""
        view_type = self.view_type_combo.currentText()
        
        if view_type == "調査イベント一覧":
            self._load_survey_events()
        elif view_type == "親調査地一覧":
            self._load_parent_sites()
        elif view_type == "調査地一覧":
            self._load_survey_sites()
        elif view_type == "種別出現記録":
            self._load_species_records()
    
    def _load_survey_events(self):
        """調査イベント一覧を読み込み"""
        include_deleted = self.show_deleted_check.isChecked()
        events = self.survey_event_model.get_all(include_deleted)
        
        # 検索フィルタ適用
        keyword = self.search_edit.text().strip().lower()
        if keyword:
            events = [e for e in events if 
                     keyword in (e.get('survey_site_name', '') or '').lower() or
                     keyword in (e.get('survey_site', '') or '').lower() or
                     keyword in (e.get('surveyor_name', '') or '').lower() or
                     keyword in (e.get('remarks', '') or '').lower()]
        
        self.data_table.setColumnCount(9)
        self.data_table.setHorizontalHeaderLabels([
            "ID", "親調査地", "調査地", "サイト", "調査日", "調査者", "天候", "気温", "備考"
        ])
        
        self.data_table.setRowCount(len(events))
        for row, event in enumerate(events):
            self.data_table.setItem(row, 0, QTableWidgetItem(str(event['id'])))
            self.data_table.setItem(row, 1, QTableWidgetItem(event.get('parent_site_name', '')))
            self.data_table.setItem(row, 2, QTableWidgetItem(event.get('survey_site_name', '')))
            self.data_table.setItem(row, 3, QTableWidgetItem(event['survey_site'] or ''))
            self.data_table.setItem(row, 4, QTableWidgetItem(event['survey_date'] or ''))
            self.data_table.setItem(row, 5, QTableWidgetItem(event['surveyor_name'] or ''))
            self.data_table.setItem(row, 6, QTableWidgetItem(event['weather'] or ''))
            self.data_table.setItem(row, 7, QTableWidgetItem(f"{event['temperature']:.1f}℃" if event['temperature'] else ''))
            self.data_table.setItem(row, 8, QTableWidgetItem((event['remarks'] or '')[:50]))
        
        # 列幅調整
        header = self.data_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
    
    def _load_parent_sites(self):
        """親調査地一覧を読み込み"""
        include_deleted = self.show_deleted_check.isChecked()
        sites = self.parent_site_model.get_all(include_deleted)
        
        # 検索フィルタ適用
        keyword = self.search_edit.text().strip().lower()
        if keyword:
            sites = [s for s in sites if 
                    keyword in (s['name'] or '').lower() or
                    keyword in (s['remarks'] or '').lower()]
        
        self.data_table.setColumnCount(7)
        self.data_table.setHorizontalHeaderLabels([
            "ID", "名称", "緯度", "経度", "標高(m)", "面積(m²)", "備考"
        ])
        
        self.data_table.setRowCount(len(sites))
        for row, site in enumerate(sites):
            self.data_table.setItem(row, 0, QTableWidgetItem(str(site['id'])))
            self.data_table.setItem(row, 1, QTableWidgetItem(site['name'] or ''))
            self.data_table.setItem(row, 2, QTableWidgetItem(f"{site['latitude']:.6f}" if site['latitude'] else ''))
            self.data_table.setItem(row, 3, QTableWidgetItem(f"{site['longitude']:.6f}" if site['longitude'] else ''))
            self.data_table.setItem(row, 4, QTableWidgetItem(f"{site['altitude']:.1f}" if site['altitude'] else ''))
            self.data_table.setItem(row, 5, QTableWidgetItem(f"{site['area']:.1f}" if site['area'] else ''))
            self.data_table.setItem(row, 6, QTableWidgetItem((site['remarks'] or '')[:50]))
    
    def _load_survey_sites(self):
        """調査地一覧を読み込み"""
        include_deleted = self.show_deleted_check.isChecked()
        sites = self.survey_site_model.get_all(include_deleted)
        
        # 検索フィルタ適用
        keyword = self.search_edit.text().strip().lower()
        if keyword:
            sites = [s for s in sites if 
                    keyword in (s['name'] or '').lower() or
                    keyword in (s.get('parent_site_name', '') or '').lower() or
                    keyword in (s['remarks'] or '').lower()]
        
        self.data_table.setColumnCount(8)
        self.data_table.setHorizontalHeaderLabels([
            "ID", "親調査地", "名称", "緯度", "経度", "標高(m)", "面積(m²)", "備考"
        ])
        
        self.data_table.setRowCount(len(sites))
        for row, site in enumerate(sites):
            self.data_table.setItem(row, 0, QTableWidgetItem(str(site['id'])))
            self.data_table.setItem(row, 1, QTableWidgetItem(site.get('parent_site_name', '')))
            self.data_table.setItem(row, 2, QTableWidgetItem(site['name'] or ''))
            self.data_table.setItem(row, 3, QTableWidgetItem(f"{site['latitude']:.6f}" if site['latitude'] else ''))
            self.data_table.setItem(row, 4, QTableWidgetItem(f"{site['longitude']:.6f}" if site['longitude'] else ''))
            self.data_table.setItem(row, 5, QTableWidgetItem(f"{site['altitude']:.1f}" if site['altitude'] else ''))
            self.data_table.setItem(row, 6, QTableWidgetItem(f"{site['area']:.1f}" if site['area'] else ''))
            self.data_table.setItem(row, 7, QTableWidgetItem((site['remarks'] or '')[:50]))
    
    def _load_species_records(self):
        """種別出現記録を読み込み"""
        include_deleted = self.show_deleted_check.isChecked()
        species_list = self.species_model.get_all(include_deleted)
        
        # 検索フィルタ適用
        keyword = self.search_edit.text().strip().lower()
        if keyword:
            species_list = [s for s in species_list if 
                           keyword in (s['scientific_name'] or '').lower() or
                           keyword in (s['ja_name'] or '').lower() or
                           keyword in (s['genus'] or '').lower()]
        
        self.data_table.setColumnCount(7)
        self.data_table.setHorizontalHeaderLabels([
            "ID", "学名", "和名", "属", "亜科", "出現回数", "総個体数"
        ])
        
        self.data_table.setRowCount(len(species_list))
        for row, species in enumerate(species_list):
            # 統計情報を取得
            stats = self.ant_record_model.get_statistics_by_species(species['id'])
            
            self.data_table.setItem(row, 0, QTableWidgetItem(str(species['id'])))
            self.data_table.setItem(row, 1, QTableWidgetItem(species['scientific_name'] or ''))
            self.data_table.setItem(row, 2, QTableWidgetItem(species['ja_name'] or ''))
            self.data_table.setItem(row, 3, QTableWidgetItem(species['genus'] or ''))
            self.data_table.setItem(row, 4, QTableWidgetItem(species['subfamily'] or ''))
            self.data_table.setItem(row, 5, QTableWidgetItem(str(stats.get('occurrence_count', 0))))
            
            # 総個体数を計算
            total_count = stats.get('occurrence_count', 0) * stats.get('avg_count', 0)
            self.data_table.setItem(row, 6, QTableWidgetItem(f"{total_count:.0f}"))
    
    def _on_search(self):
        """検索実行"""
        self._on_view_type_changed()
    
    def _clear_search(self):
        """検索クリア"""
        self.search_edit.clear()
        self._on_view_type_changed()
    
    def _on_filter_changed(self):
        """フィルタ変更"""
        self._on_view_type_changed()
    
    def _on_row_selected(self):
        """行選択時の詳細表示"""
        selected = self.data_table.selectedItems()
        if not selected:
            self.detail_text.clear()
            return
        
        row = selected[0].row()
        record_id = int(self.data_table.item(row, 0).text())
        view_type = self.view_type_combo.currentText()
        
        if view_type == "調査イベント一覧":
            self._show_event_detail(record_id)
        elif view_type == "親調査地一覧":
            self._show_parent_site_detail(record_id)
        elif view_type == "調査地一覧":
            self._show_survey_site_detail(record_id)
        elif view_type == "種別出現記録":
            self._show_species_detail(record_id)
    
    def _show_event_detail(self, event_id: int):
        """調査イベント詳細"""
        event = self.survey_event_model.get_by_id(event_id)
        if not event:
            return
        
        # 植生データ取得
        veg_data = self.vegetation_model.get_by_event(event_id)
        
        # アリ類記録取得
        ant_records = self.ant_record_model.get_by_event(event_id)
        
        detail_html = f"""
        <h3>調査イベント詳細</h3>
        <table border="1" cellpadding="5">
        <tr><th>項目</th><th>内容</th></tr>
        <tr><td>ID</td><td>{event['id']}</td></tr>
        <tr><td>親調査地</td><td>{event.get('parent_site_name', '')}</td></tr>
        <tr><td>調査地</td><td>{event.get('survey_site_name', '')}</td></tr>
        <tr><td>調査サイト</td><td>{event['survey_site']}</td></tr>
        <tr><td>調査日</td><td>{event['survey_date']}</td></tr>
        <tr><td>調査者</td><td>{event['surveyor_name'] or '-'}</td></tr>
        <tr><td>天候</td><td>{event['weather'] or '-'}</td></tr>
        <tr><td>気温</td><td>{event['temperature'] if event['temperature'] is not None else '-'}℃</td></tr>
        <tr><td>備考</td><td>{event['remarks'] or '-'}</td></tr>
        </table>
        
        <h4>植生データ</h4>
        """
        
        if veg_data:
            detail_html += f"""
            <table border="1" cellpadding="5">
            <tr><td>優占高木層樹種</td><td>{veg_data.get('dominant_tree') or '-'}</td></tr>
            <tr><td>優占ササ種</td><td>{veg_data.get('dominant_sasa') or '-'}</td></tr>
            <tr><td>高木層樹冠被度</td><td>{veg_data.get('canopy_coverage') if veg_data.get('canopy_coverage') is not None else '-'}%</td></tr>
            <tr><td>ササ被度</td><td>{veg_data.get('sasa_coverage') if veg_data.get('sasa_coverage') is not None else '-'}%</td></tr>
            <tr><td>光条件</td><td>{veg_data.get('light_condition') or '-'}</td></tr>
            <tr><td>土壌湿潤</td><td>{veg_data.get('soil_moisture') or '-'}</td></tr>
            </table>
            """
        else:
            detail_html += "<p>植生データなし</p>"
        
        detail_html += f"""
        <h4>アリ類出現記録（{len(ant_records)}種）</h4>
        """
        
        if ant_records:
            detail_html += """
            <table border="1" cellpadding="5">
            <tr><th>学名</th><th>和名</th><th>個体数</th></tr>
            """
            for record in ant_records:
                detail_html += f"""
                <tr>
                    <td>{record.get('scientific_name', '')}</td>
                    <td>{record.get('ja_name', '')}</td>
                    <td>{record['count']}</td>
                </tr>
                """
            detail_html += "</table>"
        else:
            detail_html += "<p>アリ類記録なし</p>"
        
        self.detail_text.setHtml(detail_html)
    
    def _show_parent_site_detail(self, site_id: int):
        """親調査地詳細"""
        site = self.parent_site_model.get_by_id(site_id)
        if not site:
            return
        
        # 紐づく調査地数を取得
        survey_sites = self.survey_site_model.get_by_parent(site_id)
        
        detail_html = f"""
        <h3>親調査地詳細</h3>
        <table border="1" cellpadding="5">
        <tr><th>項目</th><th>内容</th></tr>
        <tr><td>ID</td><td>{site['id']}</td></tr>
        <tr><td>名称</td><td>{site['name']}</td></tr>
        <tr><td>緯度</td><td>{site['latitude']:.6f}°N</td></tr>
        <tr><td>経度</td><td>{site['longitude']:.6f}°E</td></tr>
        <tr><td>標高</td><td>{'-' if site['altitude'] is None else format(site['altitude'], '.1f')}m</td></tr>
        <tr><td>面積</td><td>{'-' if site['area'] is None else format(site['area'], '.1f')}m²</td></tr>
        <tr><td>備考</td><td>{site['remarks'] or '-'}</td></tr>
        <tr><td>登録日</td><td>{site['created_at']}</td></tr>
        <tr><td>更新日</td><td>{site['updated_at']}</td></tr>
        </table>
        
        <h4>紐づく調査地（{len(survey_sites)}件）</h4>
        """
        
        if survey_sites:
            detail_html += """
            <ul>
            """
            for ss in survey_sites:
                detail_html += f"<li>{ss['name']}</li>"
            detail_html += "</ul>"
        else:
            detail_html += "<p>調査地なし</p>"
        
        self.detail_text.setHtml(detail_html)
    
    def _show_survey_site_detail(self, site_id: int):
        """調査地詳細"""
        site = self.survey_site_model.get_by_id(site_id)
        if not site:
            return
        
        # 調査イベント数を取得
        events = self.survey_event_model.get_by_site(site_id)
        
        detail_html = f"""
        <h3>調査地詳細</h3>
        <table border="1" cellpadding="5">
        <tr><th>項目</th><th>内容</th></tr>
        <tr><td>ID</td><td>{site['id']}</td></tr>
        <tr><td>親調査地</td><td>{site.get('parent_site_name', '')}</td></tr>
        <tr><td>名称</td><td>{site['name']}</td></tr>
        <tr><td>緯度</td><td>{site['latitude']:.6f}°N</td></tr>
        <tr><td>経度</td><td>{site['longitude']:.6f}°E</td></tr>
        <tr><td>標高</td><td>{('-' if site['altitude'] is None else format(site['altitude'], '.1f'))}m</td></tr>
        <tr><td>面積</td><td>{('-' if site['area'] is None else format(site['area'], '.1f'))}m²</td></tr>
        <tr><td>備考</td><td>{site['remarks'] or '-'}</td></tr>
        <tr><td>調査回数</td><td>{len(events)}回</td></tr>
        </table>
        
        <h4>調査履歴</h4>
        """
        
        if events:
            detail_html += """
            <ul>
            """
            for event in events:
                detail_html += f"<li>{event['survey_date']} - {event['survey_site']}</li>"
            detail_html += "</ul>"
        else:
            detail_html += "<p>調査履歴なし</p>"
        
        self.detail_text.setHtml(detail_html)
    
    def _show_species_detail(self, species_id: int):
        """種詳細"""
        species = self.species_model.get_by_id(species_id)
        if not species:
            return
        
        # 統計情報取得
        stats = self.ant_record_model.get_statistics_by_species(species_id)
        
        # 出現記録取得
        records = self.ant_record_model.get_by_species(species_id)
        
        detail_html = f"""
        <h3>種詳細情報</h3>
        <table border="1" cellpadding="5">
        <tr><th>項目</th><th>内容</th></tr>
        <tr><td>ID</td><td>{species['id']}</td></tr>
        <tr><td>学名</td><td><i>{species['scientific_name']}</i></td></tr>
        <tr><td>和名</td><td>{species['ja_name'] or '-'}</td></tr>
        <tr><td>属</td><td>{species['genus'] or '-'}</td></tr>
        <tr><td>和名属</td><td>{species['ja_genus'] or '-'}</td></tr>
        <tr><td>亜科</td><td>{species['subfamily'] or '-'}</td></tr>
        <tr><td>和名亜科</td><td>{species['ja_subfamily'] or '-'}</td></tr>
        <tr><td>備考</td><td>{species['remarks'] or '-'}</td></tr>
        </table>
        
        <h4>統計情報</h4>
        <table border="1" cellpadding="5">
        <tr><td>出現回数</td><td>{stats.get('occurrence_count', 0)}回</td></tr>
        <tr><td>出現頻度</td><td>{stats.get('occurrence_rate', 0):.2f}%</td></tr>
        <tr><td>平均個体数</td><td>{stats.get('avg_count', 0):.2f}個体</td></tr>
        <tr><td>最大個体数</td><td>{stats.get('max_count', 0)}個体</td></tr>
        <tr><td>最小個体数</td><td>{stats.get('min_count', 0)}個体</td></tr>
        </table>
        
        <h4>出現記録（{len(records)}件）</h4>
        """
        
        if records:
            detail_html += """
            <table border="1" cellpadding="5">
            <tr><th>調査日</th><th>調査地</th><th>個体数</th></tr>
            """
            for record in records[:10]:  # 最新10件のみ表示
                detail_html += f"""
                <tr>
                    <td>{record.get('survey_date', '')}</td>
                    <td>{record.get('survey_site_name', '')}</td>
                    <td>{record['count']}</td>
                </tr>
                """
            detail_html += "</table>"
            if len(records) > 10:
                detail_html += f"<p>...他{len(records) - 10}件</p>"
        else:
            detail_html += "<p>出現記録なし</p>"
        
        self.detail_text.setHtml(detail_html)
    
    def _update_statistics(self):
        """統計サマリーを更新"""
        try:
            cursor = self.conn.cursor()
            
            # 親調査地数
            cursor.execute("SELECT COUNT(*) FROM parent_sites WHERE deleted_at IS NULL")
            parent_count = cursor.fetchone()[0]
            
            # 調査地数
            cursor.execute("SELECT COUNT(*) FROM survey_sites WHERE deleted_at IS NULL")
            site_count = cursor.fetchone()[0]
            
            # 調査イベント数
            cursor.execute("SELECT COUNT(*) FROM survey_events WHERE deleted_at IS NULL")
            event_count = cursor.fetchone()[0]
            
            # 種数
            cursor.execute("SELECT COUNT(*) FROM species_master WHERE deleted_at IS NULL")
            species_count = cursor.fetchone()[0]
            
            # アリ類記録数
            cursor.execute("SELECT COUNT(*) FROM ant_records WHERE deleted_at IS NULL")
            record_count = cursor.fetchone()[0]
            
            stats_text = f"親調査地: {parent_count}件 | 調査地: {site_count}件 | 調査イベント: {event_count}件 | 種数: {species_count}種 | アリ類記録: {record_count}件"
            self.stats_label.setText(stats_text)
            
        except Exception as e:
            logger.error(f"Failed to update statistics: {e}")
            self.stats_label.setText("統計情報の取得に失敗しました")
    
    def _show_detailed_stats(self):
        """詳細統計を表示"""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton
        
        dialog = QDialog(self)
        dialog.setWindowTitle("詳細統計情報")
        dialog.resize(800, 600)
        
        layout = QVBoxLayout(dialog)
        
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        
        # 詳細統計情報を生成
        stats_html = self._generate_detailed_stats()
        text_edit.setHtml(stats_html)
        
        layout.addWidget(text_edit)
        
        close_button = QPushButton("閉じる")
        close_button.clicked.connect(dialog.close)
        layout.addWidget(close_button)
        
        dialog.exec()
    
    def _generate_detailed_stats(self) -> str:
        """詳細統計情報HTMLを生成"""
        try:
            cursor = self.conn.cursor()
            
            html = "<h2>詳細統計情報</h2>"
            
            # 調査地ごとの統計
            html += "<h3>調査地ごとの統計</h3>"
            cursor.execute("""
                SELECT 
                    ss.name as site_name,
                    ps.name as parent_name,
                    COUNT(DISTINCT se.id) as event_count,
                    COUNT(DISTINCT ar.species_id) as species_count,
                    SUM(ar.count) as total_individuals
                FROM survey_sites ss
                LEFT JOIN parent_sites ps ON ss.parent_site_id = ps.id
                LEFT JOIN survey_events se ON ss.id = se.survey_site_id AND se.deleted_at IS NULL
                LEFT JOIN ant_records ar ON se.id = ar.survey_event_id AND ar.deleted_at IS NULL
                WHERE ss.deleted_at IS NULL
                GROUP BY ss.id, ss.name, ps.name
                ORDER BY ps.name, ss.name
            """)
            
            rows = cursor.fetchall()
            if rows:
                html += """
                <table border="1" cellpadding="5" style="border-collapse: collapse;">
                <tr style="background-color: #e3f2fd;">
                    <th>親調査地</th><th>調査地</th><th>調査回数</th><th>記録種数</th><th>総個体数</th>
                </tr>
                """
                for row in rows:
                    html += f"""
                    <tr>
                        <td>{row[1] or '-'}</td>
                        <td>{row[0] or '-'}</td>
                        <td>{row[2] or 0}</td>
                        <td>{row[3] or 0}</td>
                        <td>{row[4] or 0}</td>
                    </tr>
                    """
                html += "</table>"
            
            # 種ごとの統計（出現頻度上位10種）
            html += "<h3>出現頻度上位10種</h3>"
            cursor.execute("""
                SELECT 
                    sm.scientific_name,
                    sm.ja_name,
                    COUNT(DISTINCT ar.survey_event_id) as occurrence_count,
                    AVG(ar.count) as avg_count,
                    MAX(ar.count) as max_count
                FROM species_master sm
                LEFT JOIN ant_records ar ON sm.id = ar.species_id AND ar.deleted_at IS NULL
                WHERE sm.deleted_at IS NULL
                GROUP BY sm.id, sm.scientific_name, sm.ja_name
                HAVING occurrence_count > 0
                ORDER BY occurrence_count DESC
                LIMIT 10
            """)
            
            rows = cursor.fetchall()
            if rows:
                html += """
                <table border="1" cellpadding="5" style="border-collapse: collapse;">
                <tr style="background-color: #e3f2fd;">
                    <th>学名</th><th>和名</th><th>出現回数</th><th>平均個体数</th><th>最大個体数</th>
                </tr>
                """
                for row in rows:
                    html += f"""
                    <tr>
                        <td><i>{row[0]}</i></td>
                        <td>{row[1] or '-'}</td>
                        <td>{row[2]}</td>
                        <td>{row[3]:.2f}</td>
                        <td>{row[4]}</td>
                    </tr>
                    """
                html += "</table>"
            
            # 年度別調査回数
            html += "<h3>年度別調査回数</h3>"
            cursor.execute("""
                SELECT 
                    strftime('%Y', survey_date) as year,
                    COUNT(*) as event_count
                FROM survey_events
                WHERE deleted_at IS NULL AND survey_date IS NOT NULL
                GROUP BY year
                ORDER BY year DESC
            """)
            
            rows = cursor.fetchall()
            if rows:
                html += """
                <table border="1" cellpadding="5" style="border-collapse: collapse;">
                <tr style="background-color: #e3f2fd;">
                    <th>年度</th><th>調査回数</th>
                </tr>
                """
                for row in rows:
                    html += f"""
                    <tr>
                        <td>{row[0]}</td>
                        <td>{row[1]}</td>
                    </tr>
                    """
                html += "</table>"
            
            return html
            
        except Exception as e:
            logger.error(f"Failed to generate detailed stats: {e}")
            return "<p>詳細統計情報の生成に失敗しました</p>"