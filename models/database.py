import sqlite3
import os
import logging
from pathlib import Path
import configparser

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DatabaseManager:
    def __init__(self, config_file='config.ini'):
        self.config = configparser.ConfigParser()
        self.config.read(config_file)
        self.db_path = self._get_db_path()

    def _get_db_path(self):
        # config.iniからパスを取得し、ホームディレクトリを展開
        relative_path = self.config.get('Database', 'path', fallback='ant_data/ant_database.db')
        db_path = Path.home() / relative_path
        
        # ディレクトリが存在しない場合は作成
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return str(db_path)

    def get_connection(self):
        """データベース接続を取得する"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # カラム名でアクセス可能にする
        conn.execute("PRAGMA foreign_keys = ON") # 外部キー制約有効化
        return conn

    def init_db(self):
        """データベースの初期化（テーブル作成）"""
        logging.info(f"Initializing database at {self.db_path}")
        
        conn = self.get_connection()
        cursor = conn.cursor()

        # テーブル作成SQL (要件定義書に基づく)
        schema_sql = """
        -- 1. 親調査地 (Parent Sites)
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
        );
        CREATE INDEX IF NOT EXISTS idx_parent_sites_name ON parent_sites(name);
        CREATE INDEX IF NOT EXISTS idx_parent_sites_deleted ON parent_sites(deleted_at);

        -- 2. 調査地 (Survey Sites)
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
        );
        CREATE INDEX IF NOT EXISTS idx_survey_sites_parent ON survey_sites(parent_site_id);

        -- 3. 調査イベント (Survey Events)
        CREATE TABLE IF NOT EXISTS survey_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            survey_site_id INTEGER NOT NULL,
            survey_site TEXT NOT NULL, -- 表示用キャッシュとしての名称保持
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
        );
        CREATE INDEX IF NOT EXISTS idx_survey_events_site ON survey_events(survey_site_id);
        CREATE INDEX IF NOT EXISTS idx_survey_events_date ON survey_events(survey_date);

        -- 4. 植生データ (Vegetation Data)
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
        );

        -- 5. 種名マスタ (Species Master)
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
        );

        -- 6. アリ類出現記録 (Ant Records)
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
        );

        -- 7. 環境タグマスタ (Environment Tags)
        CREATE TABLE IF NOT EXISTS environment_tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE CHECK(LENGTH(name) <= 100),
            category TEXT CHECK(category IN ('森林', '開放地', '人為地')),
            description TEXT CHECK(LENGTH(description) <= 500),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- 8. 親調査地-環境タグ中間テーブル
        CREATE TABLE IF NOT EXISTS parent_site_environments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            parent_site_id INTEGER NOT NULL,
            environment_tag_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (parent_site_id) REFERENCES parent_sites(id) ON DELETE CASCADE,
            FOREIGN KEY (environment_tag_id) REFERENCES environment_tags(id) ON DELETE RESTRICT,
            UNIQUE(parent_site_id, environment_tag_id)
        );

        -- 9. 変更履歴 (Change Logs)
        CREATE TABLE IF NOT EXISTS change_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            table_name TEXT NOT NULL,
            record_id INTEGER NOT NULL,
            action TEXT NOT NULL CHECK(action IN ('INSERT', 'UPDATE', 'DELETE')),
            changed_fields TEXT,
            user_memo TEXT CHECK(LENGTH(user_memo) <= 500),
            changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        try:
            cursor.executescript(schema_sql)
            
            # 初期タグデータの投入（存在しない場合のみ）
            self._insert_initial_tags(cursor)
            
            conn.commit()
            logging.info("Database initialized successfully.")
        except Exception as e:
            logging.error(f"Error initializing database: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()

    def _insert_initial_tags(self, cursor):
        """初期環境タグの投入"""
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
        
        for name, category, desc in initial_tags:
            try:
                cursor.execute(
                    "INSERT INTO environment_tags (name, category, description) VALUES (?, ?, ?)",
                    (name, category, desc)
                )
            except sqlite3.IntegrityError:
                pass # 既に存在する場合は無視