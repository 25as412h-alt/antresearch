"""
解析エンジン
データ出力、生態学指標算出、統計解析を担当
"""
import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import sqlite3

logger = logging.getLogger(__name__)


class AnalysisEngine:
    """解析エンジンクラス"""
    
    def __init__(self, db_connection: sqlite3.Connection):
        self.conn = db_connection
    
    def export_ant_matrix(self, 
                         unit: str = 'event',  # 'event', 'site', 'parent_site'
                         aggregation: str = 'sum',  # 'sum', 'mean', 'max'
                         value_type: str = 'count',  # 'count', 'presence', 'frequency'
                         missing_value: str = '0',  # '0', '', 'NA'
                         output_path: Optional[str] = None) -> pd.DataFrame:
        """
        アリ類群集行列を出力
        
        Parameters:
        -----------
        unit : str
            集計単位 ('event', 'site', 'parent_site')
        aggregation : str
            集約方法 ('sum', 'mean', 'max')
        value_type : str
            値の種類 ('count', 'presence', 'frequency')
        missing_value : str
            欠損値の表現 ('0', '', 'NA')
        output_path : str, optional
            CSV出力パス
        
        Returns:
        --------
        pd.DataFrame
            群集行列
        """
        try:
            cursor = self.conn.cursor()
            
            # データ取得
            if unit == 'event':
                query = """
                    SELECT 
                        se.id as event_id,
                        ss.name || '_' || se.survey_date as row_name,
                        sm.scientific_name,
                        ar.count
                    FROM survey_events se
                    LEFT JOIN survey_sites ss ON se.survey_site_id = ss.id
                    LEFT JOIN ant_records ar ON se.id = ar.survey_event_id AND ar.deleted_at IS NULL
                    LEFT JOIN species_master sm ON ar.species_id = sm.id
                    WHERE se.deleted_at IS NULL AND ss.deleted_at IS NULL
                    ORDER BY se.survey_date, ss.name
                """
            elif unit == 'site':
                query = """
                    SELECT 
                        ss.id as site_id,
                        ss.name as row_name,
                        sm.scientific_name,
                        ar.count
                    FROM survey_sites ss
                    LEFT JOIN survey_events se ON ss.id = se.survey_site_id AND se.deleted_at IS NULL
                    LEFT JOIN ant_records ar ON se.id = ar.survey_event_id AND ar.deleted_at IS NULL
                    LEFT JOIN species_master sm ON ar.species_id = sm.id
                    WHERE ss.deleted_at IS NULL
                    ORDER BY ss.name
                """
            elif unit == 'parent_site':
                query = """
                    SELECT 
                        ps.id as parent_site_id,
                        ps.name as row_name,
                        sm.scientific_name,
                        ar.count
                    FROM parent_sites ps
                    LEFT JOIN survey_sites ss ON ps.id = ss.parent_site_id AND ss.deleted_at IS NULL
                    LEFT JOIN survey_events se ON ss.id = se.survey_site_id AND se.deleted_at IS NULL
                    LEFT JOIN ant_records ar ON se.id = ar.survey_event_id AND ar.deleted_at IS NULL
                    LEFT JOIN species_master sm ON ar.species_id = sm.id
                    WHERE ps.deleted_at IS NULL
                    ORDER BY ps.name
                """
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            # DataFrameに変換
            df = pd.DataFrame(rows, columns=['id', 'row_name', 'species', 'count'])
            
            # ピボットテーブル作成
            if aggregation == 'sum':
                pivot = df.pivot_table(index='row_name', columns='species', values='count', aggfunc='sum', fill_value=0)
            elif aggregation == 'mean':
                pivot = df.pivot_table(index='row_name', columns='species', values='count', aggfunc='mean', fill_value=0)
            elif aggregation == 'max':
                pivot = df.pivot_table(index='row_name', columns='species', values='count', aggfunc='max', fill_value=0)
            
            # 値の種類に応じて変換
            if value_type == 'presence':
                pivot = (pivot > 0).astype(int)
            elif value_type == 'frequency':
                pivot = (pivot > 0).astype(int) / len(pivot) * 100
            
            # 欠損値の処理
            if missing_value == '':
                pivot = pivot.replace(0, '')
            elif missing_value == 'NA':
                pivot = pivot.replace(0, 'NA')
            
            # CSV出力
            if output_path:
                pivot.to_csv(output_path, encoding='utf-8-sig')
                logger.info(f"Ant matrix exported to: {output_path}")
            
            return pivot
            
        except Exception as e:
            logger.error(f"Failed to export ant matrix: {e}")
            raise
    
    def export_vegetation_matrix(self,
                                unit: str = 'event',
                                missing_value: str = 'NA',
                                output_path: Optional[str] = None) -> pd.DataFrame:
        """
        植生行列を出力
        
        Parameters:
        -----------
        unit : str
            集計単位 ('event', 'site', 'parent_site')
        missing_value : str
            欠損値の表現
        output_path : str, optional
            CSV出力パス
        
        Returns:
        --------
        pd.DataFrame
            植生行列
        """
        try:
            cursor = self.conn.cursor()
            
            if unit == 'event':
                query = """
                    SELECT 
                        se.id,
                        ss.name || '_' || se.survey_date as row_name,
                        vd.dominant_tree, vd.dominant_pretree, vd.dominant_sasa,
                        vd.dominant_herb, vd.litter_type,
                        vd.avg_tree_height, vd.avg_pretree_height, vd.avg_sasa_height,
                        vd.avg_herb_height, vd.avg_litter_height,
                        vd.canopy_coverage, vd.precanopy_coverage, vd.sasa_coverage,
                        vd.herb_coverage, vd.litter_coverage, vd.vegetation_rate,
                        vd.light_condition, vd.soil_moisture
                    FROM survey_events se
                    LEFT JOIN survey_sites ss ON se.survey_site_id = ss.id
                    LEFT JOIN vegetation_data vd ON se.id = vd.survey_event_id AND vd.deleted_at IS NULL
                    WHERE se.deleted_at IS NULL AND ss.deleted_at IS NULL
                    ORDER BY se.survey_date
                """
            elif unit == 'site':
                query = """
                    SELECT 
                        ss.id,
                        ss.name as row_name,
                        AVG(vd.canopy_coverage) as canopy_coverage,
                        AVG(vd.sasa_coverage) as sasa_coverage,
                        AVG(vd.light_condition) as light_condition,
                        AVG(vd.soil_moisture) as soil_moisture
                    FROM survey_sites ss
                    LEFT JOIN survey_events se ON ss.id = se.survey_site_id AND se.deleted_at IS NULL
                    LEFT JOIN vegetation_data vd ON se.id = vd.survey_event_id AND vd.deleted_at IS NULL
                    WHERE ss.deleted_at IS NULL
                    GROUP BY ss.id, ss.name
                    ORDER BY ss.name
                """
            
            cursor.execute(query)
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            df = pd.DataFrame(rows, columns=columns)
            
            # インデックス設定
            if 'row_name' in df.columns:
                df = df.set_index('row_name')
                df = df.drop('id', axis=1)
            
            # 欠損値処理
            df = df.fillna(missing_value)
            
            # CSV出力
            if output_path:
                df.to_csv(output_path, encoding='utf-8-sig')
                logger.info(f"Vegetation matrix exported to: {output_path}")
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to export vegetation matrix: {e}")
            raise
    
    def calculate_diversity_indices(self, unit: str = 'event') -> pd.DataFrame:
        """
        生態学指標を算出
        
        Parameters:
        -----------
        unit : str
            計算単位 ('event', 'site')
        
        Returns:
        --------
        pd.DataFrame
            多様度指標データフレーム
        """
        try:
            # アリ類群集行列を取得
            matrix = self.export_ant_matrix(unit=unit, value_type='count')
            
            results = []
            
            for idx, row in matrix.iterrows():
                counts = row.values
                counts = counts[counts > 0]  # 0を除外
                
                if len(counts) == 0:
                    results.append({
                        'site': idx,
                        'species_richness': 0,
                        'shannon_index': 0.0,
                        'simpson_index': 0.0,
                        'evenness': 0.0,
                        'total_individuals': 0
                    })
                    continue
                
                # 種数
                S = len(counts)
                
                # 総個体数
                N = counts.sum()
                
                # 相対頻度
                pi = counts / N
                
                # Shannon多様度指数 H' = -Σ(pi × ln pi)
                shannon = -np.sum(pi * np.log(pi))
                
                # Simpson多様度指数 D = 1 - Σ(pi²)
                simpson = 1 - np.sum(pi ** 2)
                
                # 均等度 J' = H' / ln S
                evenness = shannon / np.log(S) if S > 1 else 0.0
                
                results.append({
                    'site': idx,
                    'species_richness': S,
                    'shannon_index': round(shannon, 4),
                    'simpson_index': round(simpson, 4),
                    'evenness': round(evenness, 4),
                    'total_individuals': int(N)
                })
            
            df_results = pd.DataFrame(results)
            
            logger.info(f"Calculated diversity indices for {len(df_results)} {unit}s")
            
            return df_results
            
        except Exception as e:
            logger.error(f"Failed to calculate diversity indices: {e}")
            raise
    
    def calculate_correlation(self, 
                            var1_data: List[float], 
                            var2_data: List[float],
                            method: str = 'pearson') -> Dict:
        """
        相関係数を計算
        
        Parameters:
        -----------
        var1_data : List[float]
            変数1のデータ
        var2_data : List[float]
            変数2のデータ
        method : str
            相関係数の種類 ('pearson', 'spearman')
        
        Returns:
        --------
        Dict
            相関係数、p値、サンプル数
        """
        try:
            from scipy import stats
            
            # NaNを除外
            data1 = np.array(var1_data)
            data2 = np.array(var2_data)
            
            mask = ~np.isnan(data1) & ~np.isnan(data2)
            data1 = data1[mask]
            data2 = data2[mask]
            
            if len(data1) < 3:
                return {
                    'correlation': None,
                    'p_value': None,
                    'n': len(data1),
                    'error': 'Insufficient data (n < 3)'
                }
            
            if method == 'pearson':
                corr, p_value = stats.pearsonr(data1, data2)
            elif method == 'spearman':
                corr, p_value = stats.spearmanr(data1, data2)
            else:
                raise ValueError(f"Unknown method: {method}")
            
            return {
                'correlation': round(corr, 4),
                'p_value': round(p_value, 6),
                'n': len(data1),
                'significant': p_value < 0.05
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate correlation: {e}")
            return {
                'correlation': None,
                'p_value': None,
                'n': 0,
                'error': str(e)
            }
    
    def perform_regression(self,
                          x_data: List[float],
                          y_data: List[float],
                          degree: int = 1) -> Dict:
        """
        回帰分析を実行
        
        Parameters:
        -----------
        x_data : List[float]
            説明変数
        y_data : List[float]
            目的変数
        degree : int
            多項式の次数（1=線形、2=2次、3=3次）
        
        Returns:
        --------
        Dict
            回帰係数、決定係数、予測値等
        """
        try:
            from sklearn.preprocessing import PolynomialFeatures
            from sklearn.linear_model import LinearRegression
            from sklearn.metrics import r2_score
            
            # NaNを除外
            x = np.array(x_data).reshape(-1, 1)
            y = np.array(y_data)
            
            mask = ~np.isnan(x.flatten()) & ~np.isnan(y)
            x = x[mask]
            y = y[mask]
            
            if len(x) < 3:
                return {
                    'error': 'Insufficient data (n < 3)',
                    'n': len(x)
                }
            
            # 多項式特徴量生成
            if degree > 1:
                poly = PolynomialFeatures(degree=degree)
                x_poly = poly.fit_transform(x)
            else:
                x_poly = x
            
            # 回帰
            model = LinearRegression()
            model.fit(x_poly, y)
            
            # 予測
            y_pred = model.predict(x_poly)
            
            # 決定係数
            r2 = r2_score(y, y_pred)
            
            # 予測値生成（プロット用）
            x_range = np.linspace(x.min(), x.max(), 100).reshape(-1, 1)
            if degree > 1:
                x_range_poly = poly.transform(x_range)
            else:
                x_range_poly = x_range
            y_range_pred = model.predict(x_range_poly)
            
            return {
                'coefficients': model.coef_.tolist(),
                'intercept': float(model.intercept_),
                'r2': round(r2, 4),
                'n': len(x),
                'x_pred': x_range.flatten().tolist(),
                'y_pred': y_range_pred.tolist(),
                'degree': degree
            }
            
        except Exception as e:
            logger.error(f"Failed to perform regression: {e}")
            return {
                'error': str(e),
                'n': 0
            }