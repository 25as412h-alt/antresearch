"""
データベース接続管理モジュール
"""
import sqlite3
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class Database:
    """SQLiteデータベース管理クラス"""
    
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.connection: Optional[sqlite3.Connection] = None
        self._ensure_database_directory()
        
    def _ensure_database_directory(self):
        """データベースディレクトリが存在することを確認"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
    def connect(self) -> sqlite3.Connection:
        """データベースに接続"""
        if self.connection is None:
            self.connection = sqlite3.connect(
                str(self.db_path),
                timeout=30.0,
                check_same_thread=False
            )
            self.connection.row_factory = sqlite3.Row
            # 外部キー制約を有効化
            self.connection.execute("PRAGMA foreign_keys = ON")
            logger.info(f"Database connected: {self.db_path}")
        return self.connection
    
    def close(self):
        """データベース接続を閉じる"""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("Database connection closed")
    
    def initialize_schema(self):
        """データベーススキーマを初期化"""
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            # 親調査地テーブル
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS parent_sites (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    latitude REAL NOT NULL CHECK(latitude BETWEEN 20 AND 46),
                    longitude REAL NOT NULL CHECK(longitude BETWEEN 122 AND 154),
                    altitude REAL CHECK(altitude BETWEEN -500 AND 4000),
                    area REAL CHECK(area > 0),
                    remarks TEXT CHECK(LENGTH(remarks) <= 2000),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    deleted_at TIMESTAMP NULL
                )
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_parent_sites_name 
                ON parent_sites(name)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_parent_sites_deleted 
                ON parent_sites(deleted_at)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_parent_sites_location 
                ON parent_sites(latitude, longitude)
            """)
            
            # 調査地テーブル
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS survey_sites (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    parent_site_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    latitude REAL NOT NULL CHECK(latitude BETWEEN 20 AND 46),
                    longitude REAL NOT NULL CHECK(longitude BETWEEN 122 AND 154),
                    altitude REAL CHECK(altitude BETWEEN -500 AND 4000),
                    area REAL CHECK(area > 0),
                    remarks TEXT CHECK(LENGTH(remarks) <= 2000),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    deleted_at TIMESTAMP NULL,
                    FOREIGN KEY (parent_site_id) REFERENCES parent_sites(id) ON DELETE RESTRICT,
                    UNIQUE(parent_site_id, name)
                )
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_survey_sites_parent 
                ON survey_sites(parent_site_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_survey_sites_name 
                ON survey_sites(name)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_survey_sites_deleted 
                ON survey_sites(deleted_at)
            """)
            
            # 調査イベントテーブル
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS survey_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    survey_site_id INTEGER NOT NULL,
                    survey_site TEXT NOT NULL,
                    survey_date DATE NOT NULL,
                    surveyor_name TEXT CHECK(LENGTH(surveyor_name) <= 100),
                    weather TEXT CHECK(weather IN ('晴れ', '曇り', '雨', '雪', NULL)),
                    temperature REAL CHECK(temperature BETWEEN -30 AND 50),
                    remarks TEXT CHECK(LENGTH(remarks) <= 2000),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    deleted_at TIMESTAMP NULL,
                    FOREIGN KEY (survey_site_id) REFERENCES survey_sites(id) ON DELETE CASCADE,
                    UNIQUE(survey_site_id, survey_date)
                )
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_survey_events_site 
                ON survey_events(survey_site_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_survey_events_date 
                ON survey_events(survey_date)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_survey_events_deleted 
                ON survey_events(deleted_at)
            """)
            
            # 植生データテーブル
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vegetation_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    survey_event_id INTEGER NOT NULL,
                    dominant_tree TEXT CHECK(LENGTH(dominant_tree) <= 200),
                    dominant_pretree TEXT CHECK(LENGTH(dominant_pretree) <= 200),
                    dominant_sasa TEXT CHECK(LENGTH(dominant_sasa) <= 200),
                    dominant_herb TEXT CHECK(LENGTH(dominant_herb) <= 200),
                    litter_type TEXT CHECK(LENGTH(litter_type) <= 200),
                    avg_tree_height REAL CHECK(avg_tree_height >= 0),
                    avg_pretree_height REAL CHECK(avg_pretree_height >= 0),
                    avg_sasa_height REAL CHECK(avg_sasa_height >= 0),
                    avg_herb_height REAL CHECK(avg_herb_height >= 0),
                    avg_litter_height REAL CHECK(avg_litter_height >= 0),
                    avg_litterL_height REAL CHECK(avg_litterL_height >= 0),
                    avg_litterF_height REAL CHECK(avg_litterF_height >= 0),
                    avg_litterH_height REAL CHECK(avg_litterH_height >= 0),
                    canopy_coverage REAL CHECK(canopy_coverage BETWEEN 0 AND 100),
                    precanopy_coverage REAL CHECK(precanopy_coverage BETWEEN 0 AND 100),
                    sasa_coverage REAL CHECK(sasa_coverage BETWEEN 0 AND 100),
                    herb_coverage REAL CHECK(herb_coverage BETWEEN 0 AND 100),
                    litter_coverage REAL CHECK(litter_coverage BETWEEN 0 AND 100),
                    vegetation_rate REAL CHECK(vegetation_rate BETWEEN 0 AND 100),
                    light_condition INTEGER CHECK(light_condition BETWEEN 1 AND 5),
                    soil_moisture INTEGER CHECK(soil_moisture BETWEEN 1 AND 5),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    deleted_at TIMESTAMP NULL,
                    FOREIGN KEY (survey_event_id) REFERENCES survey_events(id) ON DELETE CASCADE
                )
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_vegetation_event 
                ON vegetation_data(survey_event_id)
            """)
            
            # 種名マスタテーブル
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS species_master (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scientific_name TEXT NOT NULL UNIQUE CHECK(LENGTH(scientific_name) <= 200),
                    genus TEXT CHECK(LENGTH(genus) <= 100),
                    subfamily TEXT CHECK(LENGTH(subfamily) <= 100),
                    ja_name TEXT CHECK(LENGTH(ja_name) <= 100),
                    ja_genus TEXT CHECK(LENGTH(ja_genus) <= 100),
                    ja_subfamily TEXT CHECK(LENGTH(ja_subfamily) <= 100),
                    remarks TEXT CHECK(LENGTH(remarks) <= 1000),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    deleted_at TIMESTAMP NULL
                )
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_species_scientific_name 
                ON species_master(scientific_name)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_species_ja_name 
                ON species_master(ja_name)
            """)
            
            # アリ類出現記録テーブル
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ant_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    survey_event_id INTEGER NOT NULL,
                    species_id INTEGER NOT NULL,
                    count INTEGER NOT NULL CHECK(count >= 0),
                    remarks TEXT CHECK(LENGTH(remarks) <= 500),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    deleted_at TIMESTAMP NULL,
                    FOREIGN KEY (survey_event_id) REFERENCES survey_events(id) ON DELETE CASCADE,
                    FOREIGN KEY (species_id) REFERENCES species_master(id) ON DELETE RESTRICT,
                    UNIQUE(survey_event_id, species_id)
                )
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_ant_records_event 
                ON ant_records(survey_event_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_ant_records_species 
                ON ant_records(species_id)
            """)
            
            # 環境タグマスタテーブル
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS environment_tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE CHECK(LENGTH(name) <= 100),
                    category TEXT CHECK(category IN ('森林', '開放地', '人為地')),
                    description TEXT CHECK(LENGTH(description) <= 500),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_environment_tags_category 
                ON environment_tags(category)
            """)
            
            # 親調査地-環境タグ中間テーブル
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS parent_site_environments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    parent_site_id INTEGER NOT NULL,
                    environment_tag_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (parent_site_id) REFERENCES parent_sites(id) ON DELETE CASCADE,
                    FOREIGN KEY (environment_tag_id) REFERENCES environment_tags(id) ON DELETE RESTRICT,
                    UNIQUE(parent_site_id, environment_tag_id)
                )
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_pse_parent 
                ON parent_site_environments(parent_site_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_pse_tag 
                ON parent_site_environments(environment_tag_id)
            """)
            
            # 変更履歴テーブル
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS change_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    table_name TEXT NOT NULL,
                    record_id INTEGER NOT NULL,
                    action TEXT NOT NULL CHECK(action IN ('INSERT', 'UPDATE', 'DELETE')),
                    changed_fields TEXT,
                    user_memo TEXT CHECK(LENGTH(user_memo) <= 500),
                    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_change_logs_table 
                ON change_logs(table_name, record_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_change_logs_date 
                ON change_logs(changed_at)
            """)
            
            # スキーママイグレーションテーブル
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version TEXT PRIMARY KEY,
                    description TEXT,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 初期バージョン記録
            cursor.execute("""
                INSERT OR IGNORE INTO schema_migrations (version, description) 
                VALUES ('1.0.0', 'Initial schema')
            """)
            
            # 初期環境タグデータ
            self._insert_initial_environment_tags(cursor)
            
            conn.commit()
            logger.info("Database schema initialized successfully")
            
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"Failed to initialize schema: {e}")
            raise
    
    def _insert_initial_environment_tags(self, cursor):
        """初期環境タグデータを投入"""
        initial_tags = [
            ('落葉広葉樹林', '森林', 'ブナ、ミズナラ等が優占する森林'),
            ('常緑広葉樹林', '森林', 'スダジイ、アラカシ等が優占する森林'),
            ('針葉樹林', '森林', 'スギ、ヒノキ、カラマツ等の植林地'),
            ('混交林', '森林', '広葉樹と針葉樹が混在する森林'),
            ('草地', '開放地', '草本が優占する開放地'),
            ('ササ原', '開放地', 'ササ類が密生する環境'),
            ('河川敷', '開放地', '河川沿いの礫地や草地'),
            ('農耕地', '人為地', '水田、畑地、果樹園等'),
            ('市街地', '人為地', '住宅地、公園等の人為的環境')
        ]
        
        for name, category, description in initial_tags:
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO environment_tags (name, category, description) 
                    VALUES (?, ?, ?)
                """, (name, category, description))
            except sqlite3.Error:
                pass  # 既に存在する場合はスキップ
    
    def backup(self, backup_dir: Path) -> Optional[Path]:
        """データベースをバックアップ"""
        try:
            backup_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = backup_dir / f"ant_database_{timestamp}.db"
            
            # VACUUM INTOでバックアップ作成
            conn = self.connect()
            conn.execute(f"VACUUM INTO '{backup_path}'")
            
            logger.info(f"Database backed up to: {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return None
    
    def integrity_check(self) -> bool:
        """データベースの整合性をチェック"""
        try:
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()
            
            if result and result[0] == "ok":
                logger.info("Database integrity check: OK")
                return True
            else:
                logger.error(f"Database integrity check failed: {result}")
                return False
                
        except Exception as e:
            logger.error(f"Integrity check error: {e}")
            return False