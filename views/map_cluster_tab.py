"""
地図・クラスタタブ
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                               QGroupBox, QFormLayout, QComboBox, QLabel,
                               QMessageBox, QTableWidget, QTableWidgetItem,
                               QTabWidget, QTextEdit, QSpinBox, QCheckBox,
                               QFileDialog)
from PySide6.QtCore import Qt
import logging
from pathlib import Path
from datetime import datetime
import webbrowser
import tempfile

from models.parent_site import ParentSite
from models.survey_site import SurveySite
from models.survey_event import SurveyEvent
from models.species import Species
from models.ant_record import AntRecord

logger = logging.getLogger(__name__)


class MapClusterTab(QWidget):
    """地図・クラスタタブ"""
    
    def __init__(self, database):
        super().__init__()
        self.database = database
        self.conn = database.connect()
        
        # モデルの初期化
        self.parent_site_model = ParentSite(self.conn)
        self.survey_site_model = SurveySite(self.conn)
        self.survey_event_model = SurveyEvent(self.conn)
        self.ant_record_model = AntRecord(self.conn)
        
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
        self.sub_tab_widget.addTab(self._create_map_tab(), "地図表示")
        self.sub_tab_widget.addTab(self._create_distance_tab(), "距離行列")
        self.sub_tab_widget.addTab(self._create_cluster_tab(), "クラスタ解析")
    
    def _create_map_tab(self):
        """地図表示タブ"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 設定
        settings_group = QGroupBox("地図設定")
        settings_layout = QFormLayout()
        
        # 表示対象
        self.map_target_combo = QComboBox()
        self.map_target_combo.addItems(["親調査地", "調査地", "調査イベント"])
        settings_layout.addRow("表示対象:", self.map_target_combo)
        
        # 色分け
        self.map_color_combo = QComboBox()
        self.map_color_combo.addItems(["親調査地別", "種数", "個体数"])
        settings_layout.addRow("色分け:", self.map_color_combo)
        
        # ヒートマップ
        self.map_heatmap_check = QCheckBox("ヒートマップ表示")
        settings_layout.addRow("", self.map_heatmap_check)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        # ボタン
        button_layout = QHBoxLayout()
        self.map_create_button = QPushButton("地図を生成")
        self.map_create_button.setObjectName("primaryButton")
        self.map_create_button.clicked.connect(self._create_map)
        button_layout.addWidget(self.map_create_button)
        
        self.map_save_button = QPushButton("HTMLとして保存")
        self.map_save_button.clicked.connect(self._save_map)
        button_layout.addWidget(self.map_save_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # 情報表示
        info_group = QGroupBox("情報")
        info_layout = QVBoxLayout()
        
        self.map_info_text = QTextEdit()
        self.map_info_text.setReadOnly(True)
        self.map_info_text.setMaximumHeight(150)
        self.map_info_text.setPlainText(
            "「地図を生成」ボタンをクリックすると、調査地の位置情報を地図上に表示します。\n"
            "地図はブラウザの新しいウィンドウで開きます。\n\n"
            "注意: インターネット接続が必要です（地図タイルの取得）"
        )
        info_layout.addWidget(self.map_info_text)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        layout.addStretch()
        
        return widget
    
    def _create_distance_tab(self):
        """距離行列タブ"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 設定
        settings_group = QGroupBox("設定")
        settings_layout = QFormLayout()
        
        # 対象
        self.dist_target_combo = QComboBox()
        self.dist_target_combo.addItems(["親調査地", "調査地"])
        settings_layout.addRow("対象:", self.dist_target_combo)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        # ボタン
        button_layout = QHBoxLayout()
        self.dist_calc_button = QPushButton("距離行列を算出")
        self.dist_calc_button.setObjectName("primaryButton")
        self.dist_calc_button.clicked.connect(self._calculate_distance_matrix)
        button_layout.addWidget(self.dist_calc_button)
        
        self.dist_export_button = QPushButton("CSV出力")
        self.dist_export_button.clicked.connect(self._export_distance_matrix)
        self.dist_export_button.setEnabled(False)
        button_layout.addWidget(self.dist_export_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # 結果表示
        result_group = QGroupBox("距離行列（単位: km）")
        result_layout = QVBoxLayout()
        
        self.dist_table = QTableWidget()
        self.dist_table.setAlternatingRowColors(True)
        result_layout.addWidget(self.dist_table)
        
        result_group.setLayout(result_layout)
        layout.addWidget(result_group)
        
        return widget
    
    def _create_cluster_tab(self):
        """クラスタ解析タブ"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 設定
        settings_group = QGroupBox("クラスタ解析設定")
        settings_layout = QFormLayout()
        
        # 対象
        self.cluster_target_combo = QComboBox()
        self.cluster_target_combo.addItems(["調査地（地理的距離）", "調査地（種組成）"])
        settings_layout.addRow("対象:", self.cluster_target_combo)
        
        # 手法
        self.cluster_method_combo = QComboBox()
        self.cluster_method_combo.addItems(["K-Means法", "階層的クラスタリング", "DBSCAN"])
        settings_layout.addRow("手法:", self.cluster_method_combo)
        
        # クラスタ数
        self.cluster_n_spin = QSpinBox()
        self.cluster_n_spin.setRange(2, 10)
        self.cluster_n_spin.setValue(3)
        settings_layout.addRow("クラスタ数:", self.cluster_n_spin)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        # ボタン
        button_layout = QHBoxLayout()
        self.cluster_exec_button = QPushButton("クラスタリング実行")
        self.cluster_exec_button.setObjectName("primaryButton")
        self.cluster_exec_button.clicked.connect(self._perform_clustering)
        button_layout.addWidget(self.cluster_exec_button)
        
        self.cluster_map_button = QPushButton("地図に表示")
        self.cluster_map_button.clicked.connect(self._show_cluster_map)
        self.cluster_map_button.setEnabled(False)
        button_layout.addWidget(self.cluster_map_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # 結果表示
        result_group = QGroupBox("クラスタリング結果")
        result_layout = QVBoxLayout()
        
        self.cluster_result_text = QTextEdit()
        self.cluster_result_text.setReadOnly(True)
        result_layout.addWidget(self.cluster_result_text)
        
        result_group.setLayout(result_layout)
        layout.addWidget(result_group)
        
        return widget
    
    def refresh(self):
        """表示更新"""
        logger.info("Map cluster tab refreshed")
    
    def _create_map(self):
        """地図を生成"""
        try:
            import folium
            from folium import plugins
            
            target = self.map_target_combo.currentText()
            color_by = self.map_color_combo.currentText()
            show_heatmap = self.map_heatmap_check.isChecked()
            
            # データ取得
            if target == "親調査地":
                sites = self.parent_site_model.get_all()
            elif target == "調査地":
                sites = self.survey_site_model.get_all()
            else:  # 調査イベント
                events = self.survey_event_model.get_all()
                # イベントから調査地情報を取得
                sites = []
                for event in events:
                    site = self.survey_site_model.get_by_id(event['survey_site_id'])
                    if site:
                        sites.append({
                            **site,
                            'event_id': event['id'],
                            'survey_date': event['survey_date']
                        })
            
            if not sites:
                QMessageBox.warning(self, "警告", "表示するデータがありません")
                return
            
            # 中心座標を計算
            lats = [s['latitude'] for s in sites if s['latitude']]
            lons = [s['longitude'] for s in sites if s['longitude']]
            
            if not lats or not lons:
                QMessageBox.warning(self, "警告", "座標データがありません")
                return
            
            center_lat = sum(lats) / len(lats)
            center_lon = sum(lons) / len(lons)
            
            # 地図作成
            m = folium.Map(
                location=[center_lat, center_lon],
                zoom_start=10,
                tiles='OpenStreetMap'
            )
            
            # 色分け用の色リスト
            colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 
                     'lightred', 'beige', 'darkblue', 'darkgreen', 'cadetblue', 
                     'darkpurple', 'white', 'pink', 'lightblue', 'lightgreen', 
                     'gray', 'black', 'lightgray']
            
            # 親調査地別の色マッピング
            parent_colors = {}
            if color_by == "親調査地別":
                parent_sites = self.parent_site_model.get_all()
                for idx, ps in enumerate(parent_sites):
                    parent_colors[ps['id']] = colors[idx % len(colors)]
            
            # マーカー追加
            for site in sites:
                lat = site['latitude']
                lon = site['longitude']
                
                if not lat or not lon:
                    continue
                
                # 色決定
                if color_by == "親調査地別":
                    color = parent_colors.get(site.get('parent_site_id'), 'gray')
                elif color_by == "種数":
                    # 種数に応じた色（実装簡略版）
                    color = 'blue'
                elif color_by == "個体数":
                    # 個体数に応じた色（実装簡略版）
                    color = 'red'
                else:
                    color = 'blue'
                
                # ポップアップ作成
                if target == "調査イベント":
                    popup_text = f"""
                    <b>調査地:</b> {site['name']}<br>
                    <b>調査日:</b> {site.get('survey_date', 'N/A')}<br>
                    <b>緯度:</b> {lat:.6f}<br>
                    <b>経度:</b> {lon:.6f}
                    """
                else:
                    popup_text = f"""
                    <b>名称:</b> {site['name']}<br>
                    <b>緯度:</b> {lat:.6f}<br>
                    <b>経度:</b> {lon:.6f}<br>
                    <b>標高:</b> {site.get('altitude', 'N/A')} m
                    """
                
                folium.Marker(
                    location=[lat, lon],
                    popup=folium.Popup(popup_text, max_width=300),
                    tooltip=site['name'],
                    icon=folium.Icon(color=color, icon='info-sign')
                ).add_to(m)
            
            # ヒートマップ
            if show_heatmap:
                heat_data = [[s['latitude'], s['longitude']] for s in sites 
                            if s['latitude'] and s['longitude']]
                plugins.HeatMap(heat_data).add_to(m)
            
            # 一時ファイルに保存
            self.temp_map_path = Path(tempfile.gettempdir()) / f"ant_map_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            m.save(str(self.temp_map_path))
            
            # ブラウザで開く
            webbrowser.open(f'file://{self.temp_map_path}')
            
            self.map_info_text.setPlainText(
                f"地図を生成しました\n"
                f"表示地点数: {len(sites)}\n"
                f"ファイル: {self.temp_map_path}\n\n"
                f"ブラウザで地図が開きます"
            )
            
            logger.info(f"Map created: {len(sites)} points")
            
        except ImportError:
            QMessageBox.critical(
                self,
                "エラー",
                "foliumライブラリがインストールされていません\n"
                "pip install folium でインストールしてください"
            )
        except Exception as e:
            logger.error(f"Map creation failed: {e}")
            QMessageBox.critical(
                self,
                "エラー",
                f"地図の生成に失敗しました:\n{str(e)}"
            )
    
    def _save_map(self):
        """地図をHTMLとして保存"""
        try:
            if not hasattr(self, 'temp_map_path') or not self.temp_map_path.exists():
                QMessageBox.warning(self, "警告", "先に地図を生成してください")
                return
            
            default_name = f"ant_map_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "地図を保存",
                default_name,
                "HTML Files (*.html)"
            )
            
            if not file_path:
                return
            
            # ファイルをコピー
            import shutil
            shutil.copy(self.temp_map_path, file_path)
            
            QMessageBox.information(
                self,
                "成功",
                f"地図を保存しました:\n{file_path}"
            )
            
        except Exception as e:
            logger.error(f"Map save failed: {e}")
            QMessageBox.critical(
                self,
                "エラー",
                f"地図の保存に失敗しました:\n{str(e)}"
            )
    
    def _calculate_distance_matrix(self):
        """距離行列を算出"""
        try:
            from math import radians, sin, cos, sqrt, atan2
            
            target = self.dist_target_combo.currentText()
            
            # データ取得
            if target == "親調査地":
                sites = self.parent_site_model.get_all()
            else:  # 調査地
                sites = self.survey_site_model.get_all()
            
            if len(sites) < 2:
                QMessageBox.warning(self, "警告", "2地点以上のデータが必要です")
                return
            
            if len(sites) > 100:
                reply = QMessageBox.question(
                    self,
                    "確認",
                    f"地点数が{len(sites)}件あります。処理に時間がかかる可能性があります。\n続行しますか？",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return
            
            # Haversine公式で距離計算
            def haversine(lat1, lon1, lat2, lon2):
                R = 6371  # 地球の半径 (km)
                
                lat1_rad = radians(lat1)
                lat2_rad = radians(lat2)
                delta_lat = radians(lat2 - lat1)
                delta_lon = radians(lon2 - lon1)
                
                a = sin(delta_lat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon/2)**2
                c = 2 * atan2(sqrt(a), sqrt(1-a))
                
                return R * c
            
            # 距離行列作成
            n = len(sites)
            distances = [[0.0 for _ in range(n)] for _ in range(n)]
            
            for i in range(n):
                for j in range(i+1, n):
                    dist = haversine(
                        sites[i]['latitude'], sites[i]['longitude'],
                        sites[j]['latitude'], sites[j]['longitude']
                    )
                    distances[i][j] = dist
                    distances[j][i] = dist
            
            # テーブル表示
            self.dist_table.setRowCount(n)
            self.dist_table.setColumnCount(n)
            
            site_names = [s['name'] for s in sites]
            self.dist_table.setHorizontalHeaderLabels(site_names)
            self.dist_table.setVerticalHeaderLabels(site_names)
            
            for i in range(n):
                for j in range(n):
                    item = QTableWidgetItem(f"{distances[i][j]:.2f}")
                    if i == j:
                        item.setBackground(Qt.lightGray)
                    self.dist_table.setItem(i, j, item)
            
            self.dist_export_button.setEnabled(True)
            self.distance_matrix = distances
            self.distance_sites = sites
            
            QMessageBox.information(
                self,
                "完了",
                f"距離行列を算出しました\n地点数: {n}"
            )
            
        except Exception as e:
            logger.error(f"Distance calculation failed: {e}")
            QMessageBox.critical(
                self,
                "エラー",
                f"距離行列の算出に失敗しました:\n{str(e)}"
            )
    
    def _export_distance_matrix(self):
        """距離行列をCSV出力"""
        try:
            if not hasattr(self, 'distance_matrix'):
                QMessageBox.warning(self, "警告", "先に距離行列を算出してください")
                return
            
            default_name = f"distance_matrix_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "CSV出力",
                default_name,
                "CSV Files (*.csv)"
            )
            
            if not file_path:
                return
            
            import pandas as pd
            
            site_names = [s['name'] for s in self.distance_sites]
            df = pd.DataFrame(self.distance_matrix, index=site_names, columns=site_names)
            df.to_csv(file_path, encoding='utf-8-sig')
            
            QMessageBox.information(
                self,
                "成功",
                f"距離行列を出力しました:\n{file_path}"
            )
            
        except Exception as e:
            logger.error(f"Export failed: {e}")
            QMessageBox.critical(
                self,
                "エラー",
                f"CSV出力に失敗しました:\n{str(e)}"
            )
    
    def _perform_clustering(self):
        """クラスタリングを実行"""
        try:
            from sklearn.cluster import KMeans, AgglomerativeClustering, DBSCAN
            import numpy as np
            
            target = self.cluster_target_combo.currentText()
            method = self.cluster_method_combo.currentText()
            n_clusters = self.cluster_n_spin.value()
            
            # データ取得
            if "地理的距離" in target:
                # 距離行列を使用
                if not hasattr(self, 'distance_matrix'):
                    QMessageBox.warning(self, "警告", 
                                      "先に距離タブで距離行列を算出してください")
                    return
                
                X = np.array(self.distance_matrix)
                labels_list = [s['name'] for s in self.distance_sites]
                
            else:  # 種組成
                # アリ類群集行列を使用（簡略版）
                from controllers.analysis_engine import AnalysisEngine
                engine = AnalysisEngine(self.conn)
                df = engine.export_ant_matrix(unit='site', value_type='presence')
                
                if df.empty:
                    QMessageBox.warning(self, "警告", "データがありません")
                    return
                
                X = df.values
                labels_list = df.index.tolist()
            
            # クラスタリング実行
            if method == "K-Means法":
                model = KMeans(n_clusters=n_clusters, random_state=42)
                clusters = model.fit_predict(X)
            elif method == "階層的クラスタリング":
                model = AgglomerativeClustering(n_clusters=n_clusters)
                clusters = model.fit_predict(X)
            elif method == "DBSCAN":
                model = DBSCAN(eps=0.5, min_samples=2)
                clusters = model.fit_predict(X)
            
            # 結果表示
            result_html = f"<h3>クラスタリング結果</h3>"
            result_html += f"<p><b>手法:</b> {method}</p>"
            result_html += f"<p><b>クラスタ数:</b> {len(set(clusters))}</p>"
            result_html += "<table border='1' cellpadding='5'>"
            result_html += "<tr><th>調査地</th><th>クラスタ</th></tr>"
            
            for label, cluster in zip(labels_list, clusters):
                result_html += f"<tr><td>{label}</td><td>クラスタ {cluster}</td></tr>"
            
            result_html += "</table>"
            
            self.cluster_result_text.setHtml(result_html)
            self.cluster_map_button.setEnabled(True)
            self.cluster_labels = clusters
            self.cluster_sites_labels = labels_list
            
            logger.info(f"Clustering completed: {len(set(clusters))} clusters")
            
        except ImportError:
            QMessageBox.critical(
                self,
                "エラー",
                "scikit-learnライブラリがインストールされていません"
            )
        except Exception as e:
            logger.error(f"Clustering failed: {e}")
            QMessageBox.critical(
                self,
                "エラー",
                f"クラスタリングに失敗しました:\n{str(e)}"
            )
    
    def _show_cluster_map(self):
        """クラスタリング結果を地図に表示"""
        try:
            import folium
            
            if not hasattr(self, 'cluster_labels'):
                QMessageBox.warning(self, "警告", "先にクラスタリングを実行してください")
                return
            
            # 調査地データ取得
            sites = self.survey_site_model.get_all()
            
            # 中心座標
            lats = [s['latitude'] for s in sites if s['latitude']]
            lons = [s['longitude'] for s in sites if s['longitude']]
            
            center_lat = sum(lats) / len(lats)
            center_lon = sum(lons) / len(lons)
            
            # 地図作成
            m = folium.Map(location=[center_lat, center_lon], zoom_start=10)
            
            # クラスタ別の色
            colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 
                     'lightred', 'beige', 'darkblue', 'darkgreen']
            
            # マーカー追加
            site_name_to_cluster = dict(zip(self.cluster_sites_labels, self.cluster_labels))
            
            for site in sites:
                if site['name'] in site_name_to_cluster:
                    cluster = site_name_to_cluster[site['name']]
                    color = colors[cluster % len(colors)]
                    
                    folium.Marker(
                        location=[site['latitude'], site['longitude']],
                        popup=f"<b>{site['name']}</b><br>クラスタ {cluster}",
                        tooltip=f"{site['name']} (クラスタ {cluster})",
                        icon=folium.Icon(color=color, icon='info-sign')
                    ).add_to(m)
            
            # 保存して表示
            temp_path = Path(tempfile.gettempdir()) / f"cluster_map_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            m.save(str(temp_path))
            webbrowser.open(f'file://{temp_path}')
            
            QMessageBox.information(
                self,
                "完了",
                "クラスタ地図を生成しました\nブラウザで開きます"
            )
            
        except Exception as e:
            logger.error(f"Cluster map failed: {e}")
            QMessageBox.critical(
                self,
                "エラー",
                f"クラスタ地図の生成に失敗しました:\n{str(e)}"
            )