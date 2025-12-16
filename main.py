"""
アリ類群集・植生データ管理システム メインエントリーポイント
"""
import sys
import logging
from pathlib import Path
import configparser
from datetime import datetime

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QFile, QTextStream, Qt

from models.database import Database
from views.main_window import MainWindow


def setup_logging(config):
    """ロギング設定"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    log_level = config.get('Logging', 'level', fallback='INFO')
    log_file = log_dir / f"app_{datetime.now().strftime('%Y%m%d')}.log"
    
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='[%(asctime)s] [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("="*60)
    logger.info("Application started")
    logger.info(f"Log file: {log_file}")
    return logger


def load_config():
    """設定ファイル読み込み"""
    config = configparser.ConfigParser()
    config_file = Path("config.ini")
    
    if config_file.exists():
        config.read(config_file, encoding='utf-8')
    else:
        logging.warning(f"Config file not found: {config_file}")
    
    return config


def load_stylesheet(app, stylesheet_path):
    """スタイルシート読み込み"""
    qss_file = QFile(stylesheet_path)
    
    if qss_file.exists() and qss_file.open(QFile.ReadOnly | QFile.Text):
        stream = QTextStream(qss_file)
        app.setStyleSheet(stream.readAll())
        qss_file.close()
        logging.info(f"Stylesheet loaded: {stylesheet_path}")
    else:
        logging.warning(f"Stylesheet not found: {stylesheet_path}")


def main():
    """メイン関数"""
    # 設定読み込み
    config = load_config()
    
    # ロギング設定
    logger = setup_logging(config)
    
    try:
        # アプリケーション作成
        app = QApplication(sys.argv)
        app.setApplicationName("アリ類群集・植生データ管理システム")
        app.setApplicationVersion("1.0.0")
        
        # 高DPI対応
        app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        
        # スタイル設定
        theme = config.get('UI', 'default_theme', fallback='Fusion')
        app.setStyle(theme)
        logger.info(f"Qt Style: {theme}")
        
        # フォントサイズ設定
        font = app.font()
        font_size = int(config.get('UI', 'font_size', fallback=10))
        font.setPointSize(font_size)
        app.setFont(font)
        
        # スタイルシート読み込み
        stylesheet_path = config.get('UI', 'style_sheet', 
                                     fallback='resources/styles/default.qss')
        load_stylesheet(app, stylesheet_path)
        
        # データベース初期化
        db_path = config.get('Database', 'path', fallback='data/ant_database.db')
        database = Database(db_path)
        database.initialize_schema()
        
        # 自動バックアップ
        auto_backup = config.getboolean('Database', 'auto_backup_on_startup', 
                                        fallback=True)
        if auto_backup:
            backup_dir = Path(config.get('Database', 'backup_dir', 
                                        fallback='backups'))
            backup_path = database.backup(backup_dir)
            if backup_path:
                logger.info(f"Auto backup created: {backup_path}")
        
        # データベース整合性チェック
        if database.integrity_check():
            logger.info("Database integrity check: OK")
        else:
            logger.warning("Database integrity check: FAILED")
        
        # メインウィンドウ作成
        main_window = MainWindow(database, config)
        main_window.show()
        
        logger.info("Main window displayed")
        
        # アプリケーション実行
        exit_code = app.exec()
        
        # クリーンアップ
        database.close()
        logger.info("Application exited normally")
        
        return exit_code
        
    except Exception as e:
        logger.critical(f"Critical error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())