"""
解析・出力タブ
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                               QGroupBox, QFormLayout, QComboBox, QLabel,
                               QFileDialog, QMessageBox, QTableWidget, QTableWidgetItem,
                               QTabWidget, QTextEdit, QCheckBox, QSpinBox)
from PySide6.QtCore import Qt
import logging
from pathlib import Path
from datetime import datetime

from controllers.analysis_engine import AnalysisEngine

logger = logging.getLogger(__name__)


class AnalysisTab(QWidget):
    """解析・出力タブ"""
    
    def __init__(self, database):
        super().__init__()
        self.database = database
        self.conn = database.connect()
        
        # 解析エンジン初期化
        self.analysis_engine = AnalysisEngine(self.conn)
        
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
        self.sub_tab_widget.addTab(self._create_export_tab(), "データ出力")
        self.sub_tab_widget.addTab(self._create_diversity_tab(), "生態学指標")
        self.sub_tab_widget.addTab(self._create_graph_tab(), "グラフ作成")
        self.sub_tab_widget.addTab(self._create_stats_tab(), "統計検定")
    
    def _create_export_tab(self):
        """データ出力タブ"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # アリ類群集行列出力
        ant_group = QGroupBox("アリ類群集行列 出力")
        ant_layout = QFormLayout()
        
        # 集計単位
        self.ant_unit_combo = QComboBox()
        self.ant_unit_combo.addItems(["調査イベント単位", "調査地単位", "親調査地単位"])
        ant_layout.addRow("集計単位:", self.ant_unit_combo)
        
        # 集約方法
        self.ant_agg_combo = QComboBox()
        self.ant_agg_combo.addItems(["合算", "平均", "最大値"])
        ant_layout.addRow("集約方法:", self.ant_agg_combo)
        
        # 値の種類
        self.ant_value_combo = QComboBox()
        self.ant_value_combo.addItems(["個体数", "在不在(0/1)", "相対頻度(%)"])
        ant_layout.addRow("値の種類:", self.ant_value_combo)
        
        # 欠損値
        self.ant_missing_combo = QComboBox()
        self.ant_missing_combo.addItems(["0", "空白", "NA"])
        ant_layout.addRow("欠損値:", self.ant_missing_combo)
        
        # 出力ボタン
        ant_button_layout = QHBoxLayout()
        self.ant_export_button = QPushButton("CSV出力")
        self.ant_export_button.setObjectName("primaryButton")
        self.ant_export_button.clicked.connect(self._export_ant_matrix)
        ant_button_layout.addWidget(self.ant_export_button)
        
        self.ant_preview_button = QPushButton("プレビュー")
        self.ant_preview_button.clicked.connect(self._preview_ant_matrix)
        ant_button_layout.addWidget(self.ant_preview_button)
        
        ant_button_layout.addStretch()
        ant_layout.addRow("", ant_button_layout)
        
        ant_group.setLayout(ant_layout)
        layout.addWidget(ant_group)
        
        # 植生行列出力
        veg_group = QGroupBox("植生行列 出力")
        veg_layout = QFormLayout()
        
        # 集計単位
        self.veg_unit_combo = QComboBox()
        self.veg_unit_combo.addItems(["調査イベント単位", "調査地単位"])
        veg_layout.addRow("集計単位:", self.veg_unit_combo)
        
        # 欠損値
        self.veg_missing_combo = QComboBox()
        self.veg_missing_combo.addItems(["NA", "0", "空白"])
        veg_layout.addRow("欠損値:", self.veg_missing_combo)
        
        # 出力ボタン
        veg_button_layout = QHBoxLayout()
        self.veg_export_button = QPushButton("CSV出力")
        self.veg_export_button.setObjectName("primaryButton")
        self.veg_export_button.clicked.connect(self._export_vegetation_matrix)
        veg_button_layout.addWidget(self.veg_export_button)
        
        self.veg_preview_button = QPushButton("プレビュー")
        self.veg_preview_button.clicked.connect(self._preview_vegetation_matrix)
        veg_button_layout.addWidget(self.veg_preview_button)
        
        veg_button_layout.addStretch()
        veg_layout.addRow("", veg_button_layout)
        
        veg_group.setLayout(veg_layout)
        layout.addWidget(veg_group)
        
        layout.addStretch()
        
        return widget
    
    def _create_diversity_tab(self):
        """生態学指標タブ"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 設定
        settings_group = QGroupBox("設定")
        settings_layout = QFormLayout()
        
        # 計算単位
        self.div_unit_combo = QComboBox()
        self.div_unit_combo.addItems(["調査イベント単位", "調査地単位"])
        settings_layout.addRow("計算単位:", self.div_unit_combo)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        # ボタン
        button_layout = QHBoxLayout()
        self.div_calc_button = QPushButton("指標を算出")
        self.div_calc_button.setObjectName("primaryButton")
        self.div_calc_button.clicked.connect(self._calculate_diversity)
        button_layout.addWidget(self.div_calc_button)
        
        self.div_export_button = QPushButton("CSV出力")
        self.div_export_button.clicked.connect(self._export_diversity)
        self.div_export_button.setEnabled(False)
        button_layout.addWidget(self.div_export_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # 結果表示
        result_group = QGroupBox("算出結果")
        result_layout = QVBoxLayout()
        
        self.div_table = QTableWidget()
        self.div_table.setAlternatingRowColors(True)
        result_layout.addWidget(self.div_table)
        
        result_group.setLayout(result_layout)
        layout.addWidget(result_group)
        
        return widget
    
    def _create_graph_tab(self):
        """グラフ作成タブ"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 散布図設定
        scatter_group = QGroupBox("散布図 設定")
        scatter_layout = QFormLayout()
        
        # データソース
        self.graph_source_combo = QComboBox()
        self.graph_source_combo.addItems(["植生データ", "多様度指標"])
        scatter_layout.addRow("データソース:", self.graph_source_combo)
        
        # X軸変数
        self.graph_x_combo = QComboBox()
        scatter_layout.addRow("X軸変数:", self.graph_x_combo)
        
        # Y軸変数
        self.graph_y_combo = QComboBox()
        scatter_layout.addRow("Y軸変数:", self.graph_y_combo)
        
        # 回帰線
        self.graph_regression_check = QCheckBox("回帰線を表示")
        scatter_layout.addRow("", self.graph_regression_check)
        
        # 回帰次数
        self.graph_degree_spin = QSpinBox()
        self.graph_degree_spin.setRange(1, 3)
        self.graph_degree_spin.setValue(1)
        scatter_layout.addRow("多項式次数:", self.graph_degree_spin)
        
        scatter_group.setLayout(scatter_layout)
        layout.addWidget(scatter_group)
        
        # ボタン
        button_layout = QHBoxLayout()
        self.graph_create_button = QPushButton("グラフ作成")
        self.graph_create_button.setObjectName("primaryButton")
        self.graph_create_button.clicked.connect(self._create_scatter_plot)
        button_layout.addWidget(self.graph_create_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # プレースホルダー
        info_label = QLabel("グラフはmatplotlibウィンドウで表示されます")
        info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(info_label)
        
        layout.addStretch()
        
        return widget
    
    def _create_stats_tab(self):
        """統計検定タブ"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 相関検定
        corr_group = QGroupBox("相関検定")
        corr_layout = QFormLayout()
        
        # データソース
        self.corr_source_combo = QComboBox()
        self.corr_source_combo.addItems(["植生データ", "多様度指標"])
        corr_layout.addRow("データソース:", self.corr_source_combo)
        
        # 変数1
        self.corr_var1_combo = QComboBox()
        corr_layout.addRow("変数1:", self.corr_var1_combo)
        
        # 変数2
        self.corr_var2_combo = QComboBox()
        corr_layout.addRow("変数2:", self.corr_var2_combo)
        
        # 検定方法
        self.corr_method_combo = QComboBox()
        self.corr_method_combo.addItems(["Pearson", "Spearman"])
        corr_layout.addRow("検定方法:", self.corr_method_combo)
        
        # 実行ボタン
        self.corr_test_button = QPushButton("検定実行")
        self.corr_test_button.setObjectName("primaryButton")
        self.corr_test_button.clicked.connect(self._perform_correlation_test)
        corr_layout.addRow("", self.corr_test_button)
        
        corr_group.setLayout(corr_layout)
        layout.addWidget(corr_group)
        
        # 結果表示
        result_group = QGroupBox("検定結果")
        result_layout = QVBoxLayout()
        
        self.stats_result_text = QTextEdit()
        self.stats_result_text.setReadOnly(True)
        result_layout.addWidget(self.stats_result_text)
        
        result_group.setLayout(result_layout)
        layout.addWidget(result_group)
        
        return widget
    
    def refresh(self):
        """表示更新"""
        # 変数リストを更新
        self._update_variable_lists()
        logger.info("Analysis tab refreshed")
    
    def _update_variable_lists(self):
        """変数リストを更新"""
        # 植生変数
        veg_vars = [
            "canopy_coverage", "sasa_coverage", "light_condition", "soil_moisture"
        ]
        
        # 多様度指標
        div_vars = [
            "species_richness", "shannon_index", "simpson_index", "evenness", "total_individuals"
        ]
        
        # コンボボックス更新
        self.graph_x_combo.clear()
        self.graph_y_combo.clear()
        self.corr_var1_combo.clear()
        self.corr_var2_combo.clear()
        
        for var in veg_vars + div_vars:
            self.graph_x_combo.addItem(var)
            self.graph_y_combo.addItem(var)
            self.corr_var1_combo.addItem(var)
            self.corr_var2_combo.addItem(var)
    
    def _export_ant_matrix(self):
        """アリ類群集行列をCSV出力"""
        try:
            # 保存先選択
            default_name = f"ant_matrix_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "CSV出力",
                default_name,
                "CSV Files (*.csv)"
            )
            
            if not file_path:
                return
            
            # パラメータ取得
            unit_map = {"調査イベント単位": "event", "調査地単位": "site", "親調査地単位": "parent_site"}
            agg_map = {"合算": "sum", "平均": "mean", "最大値": "max"}
            value_map = {"個体数": "count", "在不在(0/1)": "presence", "相対頻度(%)": "frequency"}
            missing_map = {"0": "0", "空白": "", "NA": "NA"}
            
            unit = unit_map[self.ant_unit_combo.currentText()]
            agg = agg_map[self.ant_agg_combo.currentText()]
            value_type = value_map[self.ant_value_combo.currentText()]
            missing = missing_map[self.ant_missing_combo.currentText()]
            
            # 出力実行
            self.analysis_engine.export_ant_matrix(
                unit=unit,
                aggregation=agg,
                value_type=value_type,
                missing_value=missing,
                output_path=file_path
            )
            
            QMessageBox.information(
                self,
                "成功",
                f"アリ類群集行列を出力しました:\n{file_path}"
            )
            
        except Exception as e:
            logger.error(f"Export failed: {e}")
            QMessageBox.critical(
                self,
                "エラー",
                f"CSV出力に失敗しました:\n{str(e)}"
            )
    
    def _preview_ant_matrix(self):
        """アリ類群集行列をプレビュー"""
        try:
            unit_map = {"調査イベント単位": "event", "調査地単位": "site", "親調査地単位": "parent_site"}
            agg_map = {"合算": "sum", "平均": "mean", "最大値": "max"}
            value_map = {"個体数": "count", "在不在(0/1)": "presence", "相対頻度(%)": "frequency"}
            missing_map = {"0": "0", "空白": "", "NA": "NA"}
            
            unit = unit_map[self.ant_unit_combo.currentText()]
            agg = agg_map[self.ant_agg_combo.currentText()]
            value_type = value_map[self.ant_value_combo.currentText()]
            missing = missing_map[self.ant_missing_combo.currentText()]
            
            df = self.analysis_engine.export_ant_matrix(
                unit=unit,
                aggregation=agg,
                value_type=value_type,
                missing_value=missing
            )
            
            self._show_dataframe_dialog(df, "アリ類群集行列プレビュー")
            
        except Exception as e:
            logger.error(f"Preview failed: {e}")
            QMessageBox.critical(
                self,
                "エラー",
                f"プレビュー表示に失敗しました:\n{str(e)}"
            )
    
    def _export_vegetation_matrix(self):
        """植生行列をCSV出力"""
        try:
            default_name = f"vegetation_matrix_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "CSV出力",
                default_name,
                "CSV Files (*.csv)"
            )
            
            if not file_path:
                return
            
            unit_map = {"調査イベント単位": "event", "調査地単位": "site"}
            missing_map = {"NA": "NA", "0": "0", "空白": ""}
            
            unit = unit_map[self.veg_unit_combo.currentText()]
            missing = missing_map[self.veg_missing_combo.currentText()]
            
            self.analysis_engine.export_vegetation_matrix(
                unit=unit,
                missing_value=missing,
                output_path=file_path
            )
            
            QMessageBox.information(
                self,
                "成功",
                f"植生行列を出力しました:\n{file_path}"
            )
            
        except Exception as e:
            logger.error(f"Export failed: {e}")
            QMessageBox.critical(
                self,
                "エラー",
                f"CSV出力に失敗しました:\n{str(e)}"
            )
    
    def _preview_vegetation_matrix(self):
        """植生行列をプレビュー"""
        try:
            unit_map = {"調査イベント単位": "event", "調査地単位": "site"}
            missing_map = {"NA": "NA", "0": "0", "空白": ""}
            
            unit = unit_map[self.veg_unit_combo.currentText()]
            missing = missing_map[self.veg_missing_combo.currentText()]
            
            df = self.analysis_engine.export_vegetation_matrix(
                unit=unit,
                missing_value=missing
            )
            
            self._show_dataframe_dialog(df, "植生行列プレビュー")
            
        except Exception as e:
            logger.error(f"Preview failed: {e}")
            QMessageBox.critical(
                self,
                "エラー",
                f"プレビュー表示に失敗しました:\n{str(e)}"
            )
    
    def _calculate_diversity(self):
        """生態学指標を算出"""
        try:
            unit_map = {"調査イベント単位": "event", "調査地単位": "site"}
            unit = unit_map[self.div_unit_combo.currentText()]
            
            df = self.analysis_engine.calculate_diversity_indices(unit=unit)
            
            # テーブル表示
            self.div_table.setColumnCount(len(df.columns))
            self.div_table.setHorizontalHeaderLabels(df.columns.tolist())
            self.div_table.setRowCount(len(df))
            
            for row_idx, row in df.iterrows():
                for col_idx, value in enumerate(row):
                    item = QTableWidgetItem(str(value))
                    self.div_table.setItem(row_idx, col_idx, item)
            
            self.div_export_button.setEnabled(True)
            self.div_result_df = df
            
            QMessageBox.information(
                self,
                "完了",
                f"生態学指標を算出しました\n対象: {len(df)}件"
            )
            
        except Exception as e:
            logger.error(f"Calculation failed: {e}")
            QMessageBox.critical(
                self,
                "エラー",
                f"指標算出に失敗しました:\n{str(e)}"
            )
    
    def _export_diversity(self):
        """生態学指標をCSV出力"""
        try:
            if not hasattr(self, 'div_result_df'):
                QMessageBox.warning(self, "警告", "先に指標を算出してください")
                return
            
            default_name = f"diversity_indices_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "CSV出力",
                default_name,
                "CSV Files (*.csv)"
            )
            
            if not file_path:
                return
            
            self.div_result_df.to_csv(file_path, encoding='utf-8-sig', index=False)
            
            QMessageBox.information(
                self,
                "成功",
                f"生態学指標を出力しました:\n{file_path}"
            )
            
        except Exception as e:
            logger.error(f"Export failed: {e}")
            QMessageBox.critical(
                self,
                "エラー",
                f"CSV出力に失敗しました:\n{str(e)}"
            )
    
    def _create_scatter_plot(self):
        """散布図を作成"""
        try:
            import matplotlib.pyplot as plt
            
            # データ取得（簡略版 - 実際は植生データや多様度指標から取得）
            x_var = self.graph_x_combo.currentText()
            y_var = self.graph_y_combo.currentText()
            
            # ダミーデータ（実装時は実データを使用）
            import numpy as np
            np.random.seed(42)
            x_data = np.random.rand(20) * 100
            y_data = 2 * x_data + np.random.randn(20) * 10 + 50
            
            # プロット
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.scatter(x_data, y_data, s=100, alpha=0.6, edgecolors='black')
            
            # 回帰線
            if self.graph_regression_check.isChecked():
                degree = self.graph_degree_spin.value()
                result = self.analysis_engine.perform_regression(
                    x_data.tolist(),
                    y_data.tolist(),
                    degree=degree
                )
                
                if 'x_pred' in result:
                    ax.plot(result['x_pred'], result['y_pred'], 
                           'r-', linewidth=2, label=f'Regression (degree={degree})')
                    ax.text(0.05, 0.95, f"R² = {result['r2']:.4f}", 
                           transform=ax.transAxes, fontsize=12,
                           verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
            
            ax.set_xlabel(x_var, fontsize=12)
            ax.set_ylabel(y_var, fontsize=12)
            ax.set_title(f"{x_var} vs {y_var}", fontsize=14)
            ax.grid(True, alpha=0.3)
            if self.graph_regression_check.isChecked():
                ax.legend()
            
            plt.tight_layout()
            plt.show()
            
        except Exception as e:
            logger.error(f"Graph creation failed: {e}")
            QMessageBox.critical(
                self,
                "エラー",
                f"グラフ作成に失敗しました:\n{str(e)}"
            )
    
    def _perform_correlation_test(self):
        """相関検定を実行"""
        try:
            var1 = self.corr_var1_combo.currentText()
            var2 = self.corr_var2_combo.currentText()
            method = self.corr_method_combo.currentText().lower()
            
            # ダミーデータ（実装時は実データを使用）
            import numpy as np
            np.random.seed(42)
            data1 = np.random.rand(20) * 100
            data2 = 2 * data1 + np.random.randn(20) * 10
            
            result = self.analysis_engine.calculate_correlation(
                data1.tolist(),
                data2.tolist(),
                method=method
            )
            
            # 結果表示
            result_html = f"""
            <h3>相関検定結果</h3>
            <table border="1" cellpadding="5">
            <tr><th>項目</th><th>値</th></tr>
            <tr><td>変数1</td><td>{var1}</td></tr>
            <tr><td>変数2</td><td>{var2}</td></tr>
            <tr><td>検定方法</td><td>{method.capitalize()}</td></tr>
            <tr><td>相関係数</td><td>{result.get('correlation', 'N/A')}</td></tr>
            <tr><td>p値</td><td>{result.get('p_value', 'N/A')}</td></tr>
            <tr><td>サンプル数</td><td>{result.get('n', 0)}</td></tr>
            <tr><td>有意性(α=0.05)</td><td>{'有意' if result.get('significant') else '非有意'}</td></tr>
            </table>
            <p><b>解釈:</b> {'強い相関がある' if abs(result.get('correlation', 0)) > 0.7 else '中程度の相関' if abs(result.get('correlation', 0)) > 0.4 else '弱い相関'}</p>
            """
            
            self.stats_result_text.setHtml(result_html)
            
        except Exception as e:
            logger.error(f"Correlation test failed: {e}")
            QMessageBox.critical(
                self,
                "エラー",
                f"相関検定に失敗しました:\n{str(e)}"
            )
    
    def _show_dataframe_dialog(self, df, title):
        """DataFrameをダイアログで表示"""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QPushButton
        
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.resize(1000, 600)
        
        layout = QVBoxLayout(dialog)
        
        table = QTableWidget()
        table.setColumnCount(len(df.columns))
        table.setHorizontalHeaderLabels(df.columns.tolist())
        table.setRowCount(len(df))
        
        # インデックスを最初の列として表示
        for row_idx, (idx, row) in enumerate(df.iterrows()):
            # インデックス
            table.setVerticalHeaderItem(row_idx, QTableWidgetItem(str(idx)))
            # データ
            for col_idx, value in enumerate(row):
                item = QTableWidgetItem(str(value))
                table.setItem(row_idx, col_idx, item)
        
        table.setAlternatingRowColors(True)
        layout.addWidget(table)
        
        close_button = QPushButton("閉じる")
        close_button.clicked.connect(dialog.close)
        layout.addWidget(close_button)
        
        dialog.exec()