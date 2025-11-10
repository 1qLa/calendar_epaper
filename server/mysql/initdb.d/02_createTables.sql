USE epaperdb;



-- カレンダー情報
CREATE TABLE calendars (
    id INT AUTO_INCREMENT PRIMARY KEY,
    calendar_id VARCHAR(255), -- Googleカレンダーのid
    name VARCHAR(255),
    description TEXT,
    time_zone VARCHAR(50),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- カレンダーとユーザーの紐付け
CREATE TABLE calendar_users (
    calendar_id INT,
    user_email VARCHAR(255), -- Googleアカウントメールに置き換え
    role VARCHAR(50), -- owner, editor, viewerなど
    PRIMARY KEY (calendar_id, user_email),
    FOREIGN KEY (calendar_id) REFERENCES calendars(id)
);

-- カレンダーに紐づくイベント情報
CREATE TABLE events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    google_event_id VARCHAR(255),
    calendar_id INT,
    summary VARCHAR(255),
    description TEXT,
    location VARCHAR(255),
    start_datetime DATETIME,
    end_datetime DATETIME,
    all_day BOOLEAN DEFAULT FALSE,
    recurrence TEXT,
    status VARCHAR(50),
    organizer_email VARCHAR(255),
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY (calendar_id) REFERENCES calendars(id)
);

CREATE TABLE event_attendees (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    event_id INT,
    email VARCHAR(255),
    FOREIGN KEY (event_id) REFERENCES events(id)
);
