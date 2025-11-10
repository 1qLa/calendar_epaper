-- ユーザー作成(User名：Epaperuser)
DROP USER IF EXISTS epaperuser;
CREATE USER epaperuser IDENTIFIED BY 'epaper';

-- データベースの削除
DROP DATABASE IF EXISTS epaperdb;

-- データベースの作成 
CREATE DATABASE epaperdb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- ユーザにデータベース権限付与
GRANT ALL ON epaperdb.* TO epaperuser;
